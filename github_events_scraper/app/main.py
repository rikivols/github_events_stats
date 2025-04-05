
import time
import logging
import traceback

from app import config
from app.database.github_event_wrapper import GithubEventWrapper
from app.database.github_event import GithubEvent
from app.helpers import time_response, get_postgre_url
from app.scraping.github_client import GithubClient
from app.scraping.github_scraper import GithubScraper
from sqlalchemy import create_engine


db_engine = create_engine(get_postgre_url())
GithubEvent.metadata.create_all(db_engine)

github_event_wrapper = GithubEventWrapper(db_engine=db_engine)

github_client = GithubClient()
github_scraper = GithubScraper(github_client=github_client)


if __name__ == "__main__":

    github_event_wrapper.load_event_ids()

    while True:
        loop_start = time.time()

        try:
            github_events = github_scraper.scrape_events()
            logging.info(f"Scraped {len(github_events)} events.")
            inserted_events = github_event_wrapper.insert_multiple_events(github_events=github_events)
            logging.info(f"Inserted {len(inserted_events)} new events.")

        except Exception as e:
            logging.error(f"There was an error in the main loop, ERROR: {e}, traceback: {traceback.format_exc()}")

        loop_took = time_response(loop_start)

        if loop_took < config.github_refresh_rate:
            time.sleep(config.github_refresh_rate - loop_took + 0.01)