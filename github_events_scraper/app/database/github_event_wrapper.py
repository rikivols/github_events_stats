
import datetime

from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from app import config
from app.database.github_event import GithubEvent
from app.decorators import postgre_session
from app.helpers import calculate_days_ago


class GithubEventWrapper:

    def __init__(self, db_engine: Engine):
        self.db_engine = db_engine
        self.cached_github_event_ids = set()

    @staticmethod
    def _get_event_cutoff_datetime():
        return datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=config.aggregator_rolling_days)

    @postgre_session
    def load_event_ids(self, session: Session):
        event_ids = session.query(GithubEvent.id).filter(GithubEvent.created_at >= self._get_event_cutoff_datetime())
        self.cached_github_event_ids = set([event_id[0] for event_id in event_ids])

    @postgre_session
    def delete_expired_events(self, session: Session):
        session.query(GithubEvent).filter(GithubEvent.created_at < self._get_event_cutoff_datetime()).delete()
        session.commit()

    @postgre_session
    def insert_multiple_events(self, session: Session, github_events: list[GithubEvent]) -> list[str]:
        """
        Filter out old events and events already in database and insert them.
        """

        filtered_events: list[GithubEvent] = []

        for event in github_events:
            if event.id not in self.cached_github_event_ids and \
                calculate_days_ago(event.created_at) < config.aggregator_rolling_days:
                filtered_events.append(event)

        session.bulk_save_objects(filtered_events)
        session.commit()

        return [filtered_event.id for filtered_event in filtered_events]
