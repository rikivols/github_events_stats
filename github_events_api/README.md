# Github events api
This app fetches Github events from database (Postgre). It aggregates these data and makes stats
available through an API endpoint `/github_events/all/consecutive_stats`.

The stats contain the average time between consecutive events that are grouped by repository and event type.
You can also find stats for all event types together there.

The stats are from the last 500 events or 7 days (configurable), for which condition is met first.

This app uses Fastapi for providing endpoint.

## Endpoints
* `/github_events/all/consecutive_stats` - get events for all the configured repos in GITHUB_REPOSITORIES
* `/github_events/repo/{owner}/{repo_name}/consecutive_stats` - get events for given repository
* `/health` - returns last time the database was fetched
You can find documentation for the endpoint in 
* `/docs` endpoint - Swagger UI, interactive docs.
* `/redoc` endpoint - ReDoc UI, minimalistic docs.
* `/openapi.json` endpoint - OpenAPI schema.

The host will be `http://localhost:8000` if you used default config.

The Github API endpoint limits how many pages of events you can see, so often you won't get all the events in
the past 7 days at start.

## Configuration
You have a `.env.example` file that you're supposed to copy to `.env` file and fill with your own values.

### Environmental variables:
* **GITHUB_REPOSITORIES**: list[str] = Repository owner + name in a list format, fow which we'll do stats, e.g *["coleam00/Archon"]*
* **GITHUB_MAX_REPOSITORIES**: list[str] = Maximum repositories. Will throw error if GITHUB_REPOSITORIES list is longer, default=`5`
* **AGGREGATOR_ROLLING_DAYS**: int = From how many days to do stats, default=`7`
* **AGGREGATOR_ROLLING_EVENTS**: int = Maximum amount of data used for stats per repo, default=`500`
* **AGGREGATOR_BACKGROUND_REFRESH**: int = How often to fetch the database and refresh stats in seconds, default=`100`
* **AGGREGATOR_STATS_PRECISION**: int = How many decimal places of stat averages, default=`100`
* **API_HOST**: str = Host of the API, default=`"0.0.0.0"`
* **API_PORT**: int = Port of the API, default=`8000`
* **LOGGING_LEVEL**: str = 'debug', 'info', 'warning', 'error', default=`warning`


## Run tests with pytest
Run all tests or for the specific file:
```bash
pytest tests/
```
```bash
pytest tests/test_stats_aggregator.py
```
You can also run them through Pycharm or other IDEs.

## Code Formatting

The project uses black to format source codes.
    1. `pip install black`
    2. `black .`
