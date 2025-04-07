# Github events scraper
This app scrapes Github events API and stores them to a database (Postgre). The events are not lost upon restart,
and are instead ingested to not be scraped again.

The events are periodically deleted if they're more than 7 days old (configurable). We keep track of the scraped
ids to not insert them twice. Database table is indexed by event creation for fast order and deletion.

We also don't scrape more than 500 events from a single repo (configurable). The additional events are not deleted,
as their management is outsourced to the aggregator app.

The repositories that we scrape are configurable.

## Configuration
You have a `.env.example` file that you're supposed to copy to `.env` file and fill with your own values.

### Environmental variables:
* **GITHUB_REPOSITORIES**: list[str] = Repository owner + name in a list format, e.g *["coleam00/Archon"]*
* **GITHUB_AUTHENTICATION_TOKENS**: list[str] = API key for Github events API. It's in a list format and must be the same length as
GITHUB_REPOSITORIES. Authentication token is used for scraping private repository, but it also reduces API limits for public
repositories. You can create them through this link: https://github.com/settings/personal-access-tokens. Github advises to
have metadata read permission on the token. If you don't want to use tokens, put "" for each event in list
* **GITHUB_MAX_REPOSITORIES**: int - Maximum repositories. Will throw error if GITHUB_REPOSITORIES list is longer, default=`5`
* **GITHUB_REFRESH_RATE**: int = How often to re-scrape all the repositories in seconds, default=`3600`
* **REQUEST_TIMEOUT**: int = Timeout for the Github API call, default=`60`
* **REQUEST_MAX_RETRY**: int = How many times to retry request if it fails (under given statuses), default=`3`
* **REQUEST_BACKOFF_FACTOR**: int = How long to wait between retries of requests (time increases with more retries), default=`1`
* **REQUEST_STATUS_FORCELIST**: list[int] = On which statuses we want to retry (5XX are recommended, as they mean issue on Github's side), default=`[501, 502, 503, 504]`
* **AGGREGATOR_ROLLING_DAYS**: int = After how many days we'll delete events from database, default=`7`
* **AGGREGATOR_ROLLING_EVENTS**: int = Maximum amount of events we scrape per repo, default=`500`
* **LOGGING_LEVEL**: str = 'debug', 'info', 'warning', 'error', default=`warning`


## Run tests with pytest
Run all tests or for the specific file:
```bash
pytest tests/
```
```bash
pytest tests/test_github_scraper.py
```
You can also run them through Pycharm or other IDEs.

## Code Formatting

The project uses black to format source codes.
    1. `pip install black`
    2. `black .`
