import pytest
import datetime

from unittest.mock import MagicMock, patch
from collections import defaultdict

from app.stats_aggregator import StatsAggregator
from app.config import Config
from shared_resources.github_event import GithubEvent


def test_get_event_cutoff_datetime(stats_aggregator: StatsAggregator):
    cutoff = stats_aggregator.get_event_cutoff_datetime()
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    assert isinstance(cutoff, datetime.datetime)
    assert (now - cutoff).days == stats_aggregator._config.AGGREGATOR_ROLLING_DAYS


@pytest.mark.asyncio
async def test_refresh_stats_aggregates_data(stats_aggregator: StatsAggregator) -> None:
    mock_data = defaultdict(dict)
    mock_data["repo"] = {
        "all": [4.0, 6.0],
        "PushEvent": [5.0, 5.0],
        "ForkEvent": [5.0],
        "WatchEvent": [],
    }

    with patch.object(
        stats_aggregator, "_fetch_consecutive_event_times", return_value=mock_data
    ):
        await stats_aggregator._refresh_stats()

        assert "repo" in stats_aggregator.cached_stats
        stats = stats_aggregator.cached_stats["repo"]
        assert stats["all"]["consecutive_events_average_s"] == 5.0
        assert stats["all"]["total_events"] == 3
        assert stats["PushEvent"]["consecutive_events_average_s"] == 5.0
        assert stats["PushEvent"]["total_events"] == 3
        assert stats["ForkEvent"]["consecutive_events_average_s"] == 5.0
        assert stats["ForkEvent"]["total_events"] == 2
        assert stats["WatchEvent"]["consecutive_events_average_s"] == 0.0
        assert stats["WatchEvent"]["total_events"] == 1
        assert isinstance(await stats_aggregator.get_last_updated(), str)


def make_event(seconds_offset: int) -> GithubEvent:
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    return GithubEvent(
        id=str(seconds_offset),
        type="PushEvent",
        created_at=now + datetime.timedelta(seconds=seconds_offset),
        repository="repo",
    )


def get_mock_session(return_value: list) -> MagicMock:
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_order = MagicMock()

    mock_order.yield_per.return_value = return_value
    mock_filter.order_by.return_value = mock_order
    mock_query.filter.return_value = mock_filter
    mock_session.query.return_value = mock_query

    return mock_session


@pytest.mark.asyncio
def test_fetch_consecutive_sums() -> None:
    aggregator = StatsAggregator(config=Config(), db_engine=MagicMock())
    mock_session = get_mock_session([make_event(i * 5) for i in range(3)])
    result = aggregator._fetch_consecutive_sums(session=mock_session)

    assert isinstance(result, defaultdict)
    assert "repo" in result
    assert "PushEvent" in result["repo"]
    assert len(result["repo"]["PushEvent"]) == 2
    assert round(result["repo"]["PushEvent"][0], 2) == 5.0
    assert round(result["repo"]["PushEvent"][1], 2) == 5.0


@pytest.mark.asyncio
def test_fetch_consecutive_sums_skip_old() -> None:
    aggregator = StatsAggregator(config=Config(), db_engine=MagicMock())
    mock_session = get_mock_session([make_event(-(i * 10**8)) for i in range(3)])
    result = aggregator._fetch_consecutive_sums(session=mock_session)

    assert isinstance(result, defaultdict)
    assert "repo" in result
    assert "PushEvent" in result["repo"]
    assert len(result["repo"]["PushEvent"]) == 0


@pytest.mark.asyncio
def test_fetch_consecutive_sums_skip_many_events() -> None:
    config = Config()
    aggregator = StatsAggregator(config=config, db_engine=MagicMock())
    mock_session = get_mock_session(
        [make_event(i) for i in range(config.AGGREGATOR_ROLLING_EVENTS + 100)]
    )
    result = aggregator._fetch_consecutive_sums(session=mock_session)

    assert isinstance(result, defaultdict)
    assert "repo" in result
    assert "PushEvent" in result["repo"]
    assert len(result["repo"]["PushEvent"]) == config.AGGREGATOR_ROLLING_EVENTS - 1
    assert round(result["repo"]["PushEvent"][0], 2) == 1.0
