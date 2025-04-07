import datetime
import os

import pytest
from unittest.mock import MagicMock
from sqlalchemy.engine import Engine

os.environ["GITHUB_REPOSITORIES"] = '["test_owner/test_repo"]'
os.environ["GITHUB_AUTHENTICATION_TOKENS"] = '["test_token"]'
os.environ["GITHUB_MAX_REPOSITORIES"] = "5"
os.environ["AGGREGATOR_ROLLING_EVENTS"] = "500"
os.environ["AGGREGATOR_ROLLING_DAYS"] = "7"
os.environ["DATABASE_NAME"] = "test_name"

from app.scraping.github_scraper import GithubScraper
from app.config import Config
from app.scraping.github_client import GithubClient
from app.database.github_event_wrapper import GithubEventWrapper


@pytest.fixture
def mock_github_client():
    return MagicMock(spec=GithubClient)


@pytest.fixture
def mock_github_event_wrapper():
    mock = MagicMock(spec=GithubEventWrapper)
    config = Config()
    mock.get_event_cutoff_datetime.return_value = datetime.datetime.now(
        tz=datetime.timezone.utc
    ) - datetime.timedelta(days=config.AGGREGATOR_ROLLING_DAYS)
    mock.is_event_id_in_db.return_value = False
    return mock


@pytest.fixture
def mock_engine() -> Engine:
    return MagicMock(spec=Engine)


@pytest.fixture
def github_scraper(mock_github_client, mock_github_event_wrapper):
    return GithubScraper(
        config=Config(),
        github_client=mock_github_client,
        github_event_wrapper=mock_github_event_wrapper,
    )
