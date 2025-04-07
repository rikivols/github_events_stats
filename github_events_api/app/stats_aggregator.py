
import datetime
import traceback
import logging
import time
from collections import defaultdict

import asyncio
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from shared_resources.github_event import GithubEvent
from shared_resources.database_utils import postgre_session
from shared_resources.helpers import time_response
from app.config import Config


class StatsAggregator:

    def __init__(self, config: Config, db_engine: Engine):
        self._task_started = False
        self.config = config
        self.db_engine = db_engine
        self.cached_stats = defaultdict(dict)
        self.lock = asyncio.Lock()
        self._last_updated: datetime.datetime | None = None

    def get_event_cutoff_datetime(self) -> datetime.datetime:
        return datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
            days=self.config.AGGREGATOR_ROLLING_DAYS)

    async def get_last_updated(self) -> str:
        async with self.lock:
            return self._last_updated.isoformat(timespec='seconds') + "Z" if self._last_updated else None

    @postgre_session
    def _fetch_consecutive_sums(self, session: Session) -> defaultdict[str, dict[str, list[float]]]:
        event_query = (
            session.query(GithubEvent)
            .filter(GithubEvent.created_at >= self.get_event_cutoff_datetime())
            .order_by(GithubEvent.created_at)
        )

        last_datetimes = defaultdict(dict)
        sums_for_avg = defaultdict(dict)

        # avoid memory issues in case events contained a lot of info
        for event in event_query.yield_per(100):
            repository = event.repository
            created_at: datetime.datetime = event.created_at.replace(tzinfo=datetime.timezone.utc)
            event_type = event.type

            # already past 7 days
            if created_at < self.get_event_cutoff_datetime():
                break

            for stats_key in "all", event_type:
                # we already did 500 events
                if (stats_key in sums_for_avg[repository] and
                        len(sums_for_avg[repository][stats_key]) + 1 >= self.config.AGGREGATOR_ROLLING_EVENTS):
                    continue

                if stats_key in last_datetimes[repository]:
                    consecutive_action_time = last_datetimes[repository][stats_key] - created_at
                    sums_for_avg[repository][stats_key].append(consecutive_action_time.total_seconds())
                    last_datetimes[repository][stats_key] = created_at
                else:
                    last_datetimes[repository] = {stats_key: created_at}

        return sums_for_avg

    async def _refresh_stats(self):
        consecutive_sums = self._fetch_consecutive_sums()

        async with self.lock:
            for repository in consecutive_sums:
                for stats_key in consecutive_sums[repository]:
                    consecutive_average = sum(consecutive_sums[repository]) / len(consecutive_sums[repository])
                    self.cached_stats[repository] = {
                        stats_key: {
                            "consecutive_events_average_s": round(consecutive_average, self.config.AGGREGATOR_STATS_PRECISION),
                            "total_events": len(consecutive_sums[repository])
                        }
                    }
            self.last_updated = datetime.datetime.now(tz=datetime.timezone.utc)
            logging.info(f"Successfully refreshed statistics, repositories: {len(self.cached_stats[repository])}")

    async def start_refresh(self):
        if self._task_started:
            logging.warning("Statistics refresh task already running, skipping second start.")
            return

        self._task_started = True
        logging.info(f"Statistics refresh task started.")
        while True:
            loop_start = time.time()

            try:
                await self._refresh_stats()
            except Exception as e:
                logging.error(f"There was an error in the main loop, ERROR: {e}, traceback: {traceback.format_exc()}")

            loop_took = time_response(loop_start)

            if loop_took < self.config.GITHUB_REFRESH_RATE:
                await asyncio.sleep(self.config.GITHUB_REFRESH_RATE - loop_took + 0.01)