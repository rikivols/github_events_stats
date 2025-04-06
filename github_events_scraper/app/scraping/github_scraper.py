
import re
import logging
import traceback
import math
import time

from app.config import Config
from app.scraping.github_client import GithubClient
from app.database.github_event_wrapper import GithubEventWrapper
from shared_resources.helpers import convert_github_datetime
from shared_resources.github_event import GithubEvent


class GithubScraper:

    def __init__(self, config: Config, github_client: GithubClient, github_event_wrapper: GithubEventWrapper):
        self.config = config
        self.github_client = github_client
        self.github_event_wrapper = github_event_wrapper
        self._validate()

    @staticmethod
    def _validate_repository(repository: str):
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
            raise ValueError(f"Repository name {repository} doesn't match schema 'owner/repo_name'")

    def _validate(self):
        if type(self.config.GITHUB_REPOSITORIES) != list:
            raise TypeError("Github repositories must be a list")
        if type(self.config.GITHUB_AUTHENTICATION_TOKENS) != list:
            raise TypeError("Github authentication_tokens must be a list")
        if len(self.config.GITHUB_REPOSITORIES) == 0:
            raise ValueError("Github repositories must contain at least 1 repository")
        if len(self.config.GITHUB_AUTHENTICATION_TOKENS) == 0:
            raise ValueError("Github authentication_tokens must contain at least 1 authentication token")
        if len(self.config.GITHUB_REPOSITORIES) > self.config.GITHUB_MAX_REPOSITORIES:
            raise ValueError(f"There can't be more than {self.config.GITHUB_MAX_REPOSITORIES} repositories")
        if len(self.config.GITHUB_REPOSITORIES) != len(self.config.GITHUB_AUTHENTICATION_TOKENS):
            raise ValueError(f"Github repositories must be the same amount of elements as authentication_tokens")

        for repository_name in self.config.GITHUB_REPOSITORIES:
            self._validate_repository(repository_name)

    def scrape_repository(self, repository: str, authentication_token: str) -> list[GithubEvent]:
        """
        Scrape repository events page for page, until the rolling events limit is reached.

        We stop scraping a new page if we find an event that we already scraped (old data),
        or we find that the event is older than configured rolling days limit.

        :param repository: Github repository name in format {owner}/{repo_name}
        :param authentication_token: Authentication token for scraping that repository, can be any for public repos.
        :return:
        """

        repository_events = []

        owner, repository_name = repository.split("/")

        github_per_page = 100
        dont_continue = False

        for page_num in range(1, math.ceil(self.config.AGGREGATOR_ROLLING_EVENTS // github_per_page) + 1):
            github_events_response = self.github_client.get_github_events(
                owner, repository_name, authentication_token, github_per_page, page_num
            )
            page_events = []

            for event in github_events_response:
                created_event_datetime = convert_github_datetime(event["created_at"])
                if (created_event_datetime < self.github_event_wrapper.get_event_cutoff_datetime() or
                        self.github_event_wrapper.is_event_id_in_db(event["id"])):
                    dont_continue = True
                    break

                github_event = GithubEvent(
                    id=event["id"],
                    type=event["type"],
                    created_at=convert_github_datetime(event["created_at"]),
                    repository=event["repo"]["name"]
                )
                page_events.append(github_event)

            logging.info(f"Repo: {repository}, page: {page_num}, scraped {len(page_events)} events.")
            repository_events.extend(page_events)

            time.sleep(0.2)

            if dont_continue or len(github_events_response) < github_per_page:
                break


        return repository_events

    def scrape_events(self) -> list[GithubEvent]:
        """
        Scrape events from all configured repositories
        """

        github_events = []

        for i, repository in enumerate(self.config.GITHUB_REPOSITORIES):
            authentication_token = self.config.GITHUB_AUTHENTICATION_TOKENS[i]

            try:
                events = self.scrape_repository(repository, authentication_token)
                logging.info(f"Repo: {repository}, scraped {len(events)} events.")
                github_events.extend(events)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.error(f"Error during scraping of repository events for: {repository}"
                              f", ERROR: {e}, traceback: {traceback.format_exc()}")

        return github_events
