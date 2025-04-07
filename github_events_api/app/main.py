
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
set_logger(config)

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
    return JSONResponse({
        "status": "ok",
        "last_refresh": await stats_aggregator.get_last_updated()
    })


async def get_consecutive_result(repository_to_return: str=None) -> dict:
    result = {
        "last_refresh": await stats_aggregator.get_last_updated(),
        "repositories": {}
    }

    async with stats_aggregator.lock:
        for repository in stats_aggregator.cached_stats:
            if repository_to_return and repository != repository_to_return:
                continue

            for event_type in stats_aggregator.cached_stats[repository]:
                if repository not in result["repositories"]:
                    result["repositories"][repository] = {}

                if event_type == "all":
                    result["repositories"][repository]["all_actions"] = stats_aggregator.cached_stats[repository]["all"]
                else:
                    result["repositories"][repository]["event_type"] = {
                        event_type: stats_aggregator.cached_stats[repository][event_type]
                    }

    return result


@app.get("/github_events/all/consecutive_stats")
async def get_all_consecutive_stats():
    result = await get_consecutive_result()
    return JSONResponse(result)


@app.get("/github_events/repo/{repo_owner}/{repo_name}/consecutive_stats")
async def get_all_stats_repo(repo_owner: str, repo_name: str):
    result = await get_consecutive_result(f"{repo_owner}/{repo_name}")
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Repository with owner: '{repo_owner}' and name: {repo_name} not found"
        )

    return JSONResponse(result)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=config.API_HOST, port=config.API_PORT)
