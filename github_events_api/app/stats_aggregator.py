
from sqlalchemy.orm import Session

from shared_resources.github_event import GithubEvent
from shared_resources.database_utils import postgre_session

class StatsAggregator:

    def __init__(self, github_event: GithubEvent):
        self.github_event = github_event

    @postgre_session
    def get_github_events(self, session: Session):
        ...


    def calculate_stats(self):
        ...

