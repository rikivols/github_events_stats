
import logging
import traceback

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import Config
from app.decorators import track_response


class GithubClient:
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self._mount_session()

    def _mount_session(self):
        """
        Adds a retry mechanism on failed requests, such as timeouts or connection failed. Also retries on the common
        responses when the server is overloaded e.g. (502, 503, 504)
        """

        retries = Retry(
            total=self.config.github_max_retry,
            backoff_factor=self.config.github_backoff_factor,
            status_forcelist=self.config.github_status_forcelist,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    @track_response
    def _get_github_events(self, url: str, authorization_token: str) -> requests.Response:
        return self.session.get(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {authorization_token}",
                "X-GitHub-Api-Version": "2022-11-28"
            },
            timeout=self.config.github_timeout
        )

    def get_github_events(self, owner: str, repository_name: str, authorization_token: str) -> list[dict]:

        self.session.cookies.clear()
        events_response = self._get_github_events(
            f"https://api.github.com/repos/{owner}/{repository_name}/events",
            authorization_token
        )

        return events_response.json() if events_response.ok else []
