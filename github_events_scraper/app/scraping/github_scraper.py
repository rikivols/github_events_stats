
import re
import logging
import traceback

from app import config
from app.scraping.github_client import GithubClient
from app.helpers import convert_github_datetime
from app.database.github_event import GithubEvent


class GithubScraper:

    def __init__(self, github_client: GithubClient):
        self.github_client = github_client

    @staticmethod
    def _validate_repository(repository: str):
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
            raise ValueError(f"Repository name {repository} doesn't match schema 'owner/repo_name'")

    def _validate(self):
        if type(config.repositories) != list:
            raise TypeError("Github repositories must be a list")
        if type(config.authentication_tokens) != list:
            raise TypeError("Github authentication_tokens must be a list")
        if len(config.repositories) == 0:
            raise ValueError("Github repositories must contain at least 1 repository")
        if len(config.authentication_tokens) == 0:
            raise ValueError("Github authentication_tokens must contain at least 1 authentication token")
        if len(config.repositories) > config.max_repositories:
            raise ValueError(f"There can't be more than {config.max_repositories} repositories")
        if len(config.repositories) != len(config.authentication_tokens):
            raise ValueError(f"Github repositories must be the same amount of elements as authentication_tokens")

        for repository_name in config.repositories:
            self._validate_repository(repository_name)

    def scrape_events(self) -> list[GithubEvent]:

        github_events = []

        for i, repository in enumerate(config.repositories):
            authentication_token = config.authentication_tokens[i]

            try:
                owner, repository_name = repository.split("/")
                github_events_response = config.github_client.get_github_events(
                    owner, repository_name, authentication_token
                )

                for event in github_events_response:

                    github_event = GithubEvent(
                        id=event["id"],
                        type=event["type"],
                        created_at=convert_github_datetime(event["created_at"]),
                        repository=event["repo"]["name"]
                    )
                    github_events.append(github_event)
            except Exception as e:
                logging.error(f"Error during scraping of repository events for: {repository}"
                              f", ERROR: {e}, traceback: {traceback.format_exc()}")

        return github_events
