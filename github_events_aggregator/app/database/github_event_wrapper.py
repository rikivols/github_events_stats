
import datetime

from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from app.config import Config
from app.database.github_event import GithubEvent
from app.decorators import postgre_session


class GithubEventWrapper:

    def __init__(self, config: Config, db_engine: Engine):
        self.config = config
        self.db_engine = db_engine
        self.cached_github_event_ids = set()

    @postgre_session
    def delete_expired_events(self, session: Session):
        delete_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=self.config.aggregator_rolling_days)
        session.query(GithubEvent).filter(GithubEvent.created_at < delete_time).delete()
        session.commit()


