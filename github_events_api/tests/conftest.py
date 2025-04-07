import os

import pytest
from unittest.mock import MagicMock

os.environ["GITHUB_REPOSITORIES"] = '["test_owner/test_repo"]'
os.environ["GITHUB_AUTHENTICATION_TOKENS"] = '["test_token"]'
os.environ["GITHUB_MAX_REPOSITORIES"] = "5"
os.environ["AGGREGATOR_ROLLING_EVENTS"] = "500"
os.environ["AGGREGATOR_ROLLING_DAYS"] = "7"
os.environ["DATABASE_NAME"] = "test_name"

from app.stats_aggregator import StatsAggregator
from app.config import Config
from sqlalchemy.engine import Engine


@pytest.fixture
def mock_engine() -> Engine:
    return MagicMock(spec=Engine)


@pytest.fixture
def stats_aggregator(mock_engine: Engine) -> StatsAggregator:
    StatsAggregator._instance = None
    return StatsAggregator(config=Config(), db_engine=mock_engine)
