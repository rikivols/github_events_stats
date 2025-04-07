
import copy
import datetime
import math
from datetime import timedelta

from app.config import Config
from app.scraping.github_scraper import GithubScraper
from shared_resources.github_event import GithubEvent
from shared_resources.helpers import convert_to_github_datetime


REPO_NAME = "test_owner/test_repo"
EVENT_ID = "1"

TEST_EVENT = {
    "id": EVENT_ID,
    "type": "PushEvent",
    "created_at": "2099-01-01T12:00:00Z",
    "repo": {"name": REPO_NAME},
}


def test_scrape_repository_returns_events(
    github_scraper: GithubScraper, mock_github_client
):
    mock_github_client.get_github_events.return_value = [TEST_EVENT] * 2

    events = github_scraper.scrape_events()

    assert len(events) == 2
    assert all(isinstance(event, GithubEvent) for event in events)
    assert events[0].id == EVENT_ID
    mock_github_client.get_github_events.assert_called_once()


def test_scrape_repository_skips_old_events(
    github_scraper: GithubScraper, mock_github_client, mock_github_event_wrapper
):
    test_event_old = copy.deepcopy(TEST_EVENT)
    config = Config()
    test_event_old["created_at"] = convert_to_github_datetime(
        datetime.datetime.now(tz=datetime.timezone.utc)
        - timedelta(days=config.AGGREGATOR_ROLLING_DAYS + 1)
    )
    test_event_new = copy.deepcopy(TEST_EVENT)
    test_event_new["created_at"] = convert_to_github_datetime(
        datetime.datetime.now(tz=datetime.timezone.utc)
        - timedelta(days=config.AGGREGATOR_ROLLING_DAYS - 1)
    )

    mock_github_client.get_github_events.return_value = [
        TEST_EVENT,
        test_event_new,
        test_event_old,
    ]

    events = github_scraper.scrape_events()

    assert len(events) == 2
    assert all(isinstance(event, GithubEvent) for event in events)
    mock_github_client.get_github_events.assert_called_once()


def test_scrape_repository_skips_existing_events(
    github_scraper: GithubScraper, mock_github_client, mock_github_event_wrapper
):
    mock_github_client.get_github_events.return_value = [TEST_EVENT]
    mock_github_event_wrapper.is_event_id_in_db.return_value = True
    events = github_scraper.scrape_events()

    assert events == []


def test_scrape_repository_cut_rolling_events(
    github_scraper: GithubScraper, mock_github_client, mock_github_event_wrapper
):
    config = Config()
    mock_github_client.get_github_events.return_value = [
        TEST_EVENT
    ] * github_scraper.GITHUB_PER_PAGE

    events = github_scraper.scrape_events()

    assert len(events) == config.AGGREGATOR_ROLLING_EVENTS
    assert all(isinstance(event, GithubEvent) for event in events)
    mock_github_client.get_github_events.call_count = (
        math.ceil(config.AGGREGATOR_ROLLING_EVENTS / github_scraper.GITHUB_PER_PAGE) + 1
    )


def test_scrape_repository_handles_exception(
    github_scraper: GithubScraper, mock_github_client
):
    mock_github_client.get_github_events.side_effect = Exception("GitHub API down!")

    events = github_scraper.scrape_events()

    assert events == []
