
import datetime

from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from app.config import Config
from shared_resources.github_event import GithubEvent
from shared_resources.database_utils import postgre_session
from shared_resources.helpers import calculate_days_ago


class GithubEventWrapper:

    def __init__(self, config: Config, db_engine: Engine):
        self.config = config
        self.db_engine = db_engine
        self._cached_github_event_ids = set()

    def is_event_id_in_db(self, event_id: str):
        return event_id in self._cached_github_event_ids

    def get_event_cutoff_datetime(self):
        return datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=self.config.AGGREGATOR_ROLLING_DAYS)

    @postgre_session
    def load_event_ids(self, session: Session):
        event_ids = session.query(GithubEvent.id).filter(GithubEvent.created_at >= self.get_event_cutoff_datetime())
        self._cached_github_event_ids = set([event_id[0] for event_id in event_ids])

    @postgre_session
    def delete_expired_events(self, session: Session):
        session.query(GithubEvent).filter(GithubEvent.created_at < self.get_event_cutoff_datetime()).delete()
        session.commit()

    @postgre_session
    def insert_multiple_events(self, session: Session, github_events: list[GithubEvent]) -> list[str]:
        """
        Filter out old events and events already in database and insert them.
        """

        filtered_events: list[GithubEvent] = []

        for event in github_events:
            if not self.is_event_id_in_db(event.id) and calculate_days_ago(event.created_at) < self.config.AGGREGATOR_ROLLING_DAYS:
                filtered_events.append(event)

        # TODO - make insert safe
        session.bulk_save_objects(filtered_events)
        session.commit()
        filtered_event_ids = [filtered_event.id for filtered_event in filtered_events]
        self._cached_github_event_ids.update(filtered_event_ids)

        return filtered_event_ids
