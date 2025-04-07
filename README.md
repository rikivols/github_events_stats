# Github events aggregator pipeline
This pipeline scrapes Github events and provides statistics through an API endpoint.

The statistics include consecutive time between events and their amount. The stastics are calculated
as a rolling window of 7 days or 500 events (configurable) per repo, depends on which condition is met first.

The project consists of 2 parts:
* **github_event_scraper** - App that scrapes github events and stores them to (Postgre) database
* **github_events_api** - Aggregates the statistics and provides them as an API endpoint.

You can read more about these 2 apps in their respective README's

## Running the pipeline
The apps are supposed to be ran through docker compose. Both the apps and database will be created in the docker.

To successfully run docker-compose, you need to fill the .env file in the pipeline's root directory containing 
database information. Please copy the `.env.example` file to `.env` file and fill it with your credentials.

Next you need to copy the `.env.example` to `.env` file for both the apps in their root directory. The .env contains
config for both apps. The config is more explained in their individual README's.

Once you filled your `.env` files, all you need to do is run `docker-compose up --build`

The project uses poetry for project dependencies, but their installation is internally handled in the Dockerfile.

After you successfully start both dockers for the first time, it may take some time to see first stats appear. 
That is because the containers start at the same time, and the api app will fetch the database before scraper app had
the chance to populate it. This will be solved on the second refresh of the database. That is one of the reasons why
there's less refresh time in the api app than scraper app.

## Local development
For local development of the apps, please create your python virtual environment `python3 -m venv .venv`, and download
all dependencies with `poetry install` for each app.

## Code Formatting

The project uses black to format source codes.
    1. `pip install black`
    2. `black .`
