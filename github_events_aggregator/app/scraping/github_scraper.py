
import re
import logging
import traceback

from app.config import Config
from app.scraping.github_client import GithubClient
from app.helpers import calculate_days_ago
from app.database.github_event import GithubEvent


class GithubScraper:

    def __init__(self, github_client: GithubClient, config: Config):
        self.github_client = github_client
        self.config = config
        self.repositories = config.github_repositories
        self.authentication_tokens = config.github_authentication_tokens
        self.max_repositories = config.github_max_repositories
        self.max_days_ago = config.aggregator_rolling_days

    @staticmethod
    def _validate_repository(repository: str):
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
            raise ValueError(f"Repository name {repository} doesn't match schema 'owner/repo_name'")

    def _validate(self):
        if type(self.repositories) != list:
            raise TypeError("Github repositories must be a list")
        if type(self.authentication_tokens) != list:
            raise TypeError("Github authentication_tokens must be a list")
        if len(self.repositories) == 0:
            raise ValueError("Github repositories must contain at least 1 repository")
        if len(self.authentication_tokens) == 0:
            raise ValueError("Github authentication_tokens must contain at least 1 authentication token")
        if len(self.repositories) > self.max_repositories:
            raise ValueError(f"There can't be more than {self.max_repositories} repositories")
        if len(self.repositories) != len(self.authentication_tokens):
            raise ValueError(f"Github repositories must be the same amount of elements as authentication_tokens")

        for repository_name in self.repositories:
            self._validate_repository(repository_name)

    def scrape_events(self) -> list[GithubEvent]:

        github_events = []

        for i, repository in enumerate(self.repositories):
            authentication_token = self.authentication_tokens[i]

            try:
                owner, repository_name = repository.split("/")
                github_events_response = self.github_client.get_github_events(
                    owner, repository_name, authentication_token
                )

                for event in github_events_response:
                    if calculate_days_ago(event["created_at"]) > self.config.aggregator_rolling_days:
                        continue

                    github_event = GithubEvent(
                        id=event["id"],
                        type=event["type"],
                        created_at=event["created_at"],
                        repository=event["repo"]["name"]
                    )
                    github_events.append(github_event)
            except Exception as e:
                logging.error(f"Error during scraping of repository events for: {repository}"
                              f", ERROR: {e}, traceback: {traceback.format_exc()}")

        return github_events
