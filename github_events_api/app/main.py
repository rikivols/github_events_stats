
import logging

import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from sqlalchemy import create_engine

from app.stats_aggregator import StatsAggregator
from app.config import Config
from shared_resources.helpers import set_logger
from shared_resources.database_utils import get_connection_string


config = Config()

db_engine = create_engine(get_connection_string())
stats_aggregator = StatsAggregator(config=config, db_engine=db_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(stats_aggregator.start_refresh())

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logging.info("Stats aggregator refresh task cancelled.")


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def get_health():
    return JSONResponse(
        {"status": "ok", "last_refresh": await stats_aggregator.get_last_updated()}
    )


async def get_consecutive_result(repository_to_return: str = None) -> dict:
    result = {
        "last_refresh": await stats_aggregator.get_last_updated(),
        "repositories": {},
    }

    async with stats_aggregator.lock:
        for repository in stats_aggregator.cached_stats:
            if repository_to_return and repository != repository_to_return:
                continue

            for event_type in stats_aggregator.cached_stats[repository]:
                if repository not in result["repositories"]:
                    result["repositories"][repository] = {
                        "all_actions": {},
                        "event_type": {},
                    }

                if event_type == "all":
                    result["repositories"][repository]["all_actions"] = (
                        stats_aggregator.cached_stats[repository]["all"]
                    )
                else:
                    result["repositories"][repository]["event_type"][event_type] = (
                        stats_aggregator.cached_stats[repository][event_type]
                    )

    return result


ok_response_example = {
    "description": "Stats retrieved successfully",
    "content": {
        "application/json": {
            "example": {
                "last_refresh": "2025-04-07T14:14:10+00:00Z",
                "repositories": {
                    "user/repo_name": {
                        "all_actions": {
                            "consecutive_events_average_s": 123.45,
                            "total_events": 50,
                        },
                        "event_type": {
                            "PushEvent": {
                                "consecutive_events_average_s": 60.0,
                                "total_events": 20,
                            },
                            "WatchEvent": {
                                "consecutive_events_average_s": 180.0,
                                "total_events": 30,
                            },
                        },
                    }
                },
            }
        }
    },
}

response_structure = """
**Structure of response:**\n
    - `last_refresh`: Timestamp of last stats update (UTC, ISO format)\n
    - `repositories`: A dictionary keyed by repository name (e.g. `owner/repo`), each containing:\n
        - `all_actions`: Stats across all event types\n
        - `event_type`: Dictionary of stats grouped by event type (e.g. `PushEvent`, `WatchEvent`, etc.)\n\n
        Each stat entry includes:\n
            - `consecutive_events_average_s`: Average time (in seconds) between consecutive events of that type\n
            - `total_events`: Total number of events used to compute the average
"""


@app.get(
    "/github_events/all/consecutive_stats",
    summary="Get average consecutive event stats for all repositories",
    description=(
        "Returns statistics for the average time between consecutive GitHub events and their amount. "
        "The stats contain all repositories configured, grouped by event type and also across all event types. "
        "They are grouped by a specific repo over a rolling window (7 days or 500 events).\n"
        + response_structure
    ),
    tags=["GitHub Stats"],
    response_description="A dictionary of consecutive event time by repository and event type",
    responses={200: ok_response_example},
)
async def get_all_consecutive_stats():
    result = await get_consecutive_result()
    return JSONResponse(result)


@app.get(
    "/github_events/repo/{repo_owner}/{repo_name}/consecutive_stats",
    summary="Get average consecutive event stats for a specific repository",
    description=(
        "Returns statistics about consecutive GitHub events for a single repository, "
        "grouped by event type and across all types. Useful for tracking activity trends "
        "in a specific repo over a rolling window (7 days or 500 events).\n"
        + response_structure
    ),
    tags=["GitHub Stats"],
    response_description="A dictionary of stats for the given repository and event type",
    responses={
        200: ok_response_example,
        404: {
            "description": "Repository not found or has no events in the aggregation window",
            "content": {
                "application/json": {"example": {"detail": "Repository ... not found"}}
            },
        },
    },
)
async def get_all_stats_repo(repo_owner: str, repo_name: str):
    result = await get_consecutive_result(f"{repo_owner}/{repo_name}")
    if not result["repositories"]:
        raise HTTPException(
            status_code=404,
            detail=f"Repository with owner: '{repo_owner}' and name: {repo_name} not found",
        )

    return JSONResponse(result)


if __name__ == "__main__":
    set_logger(config)
    logging.info("Starting app...")
    uvicorn.run("app.main:app", host=config.API_HOST, port=config.API_PORT)
