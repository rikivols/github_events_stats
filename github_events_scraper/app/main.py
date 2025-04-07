import time
import logging
import traceback

from sqlalchemy import create_engine

from app.config import Config
from app.database.github_event_wrapper import GithubEventWrapper
from shared_resources.github_event import GithubEvent
from shared_resources.helpers import time_response, set_logger
from shared_resources.database_utils import get_connection_string
from app.scraping.github_client import GithubClient
from app.scraping.github_scraper import GithubScraper


config = Config()
set_logger(config)

db_engine = create_engine(get_connection_string())
GithubEvent.metadata.create_all(db_engine)

github_event_wrapper = GithubEventWrapper(config=config, db_engine=db_engine)

github_client = GithubClient(config=config)
github_scraper = GithubScraper(
    config=config,
    github_client=github_client,
    github_event_wrapper=github_event_wrapper,
)


if __name__ == "__main__":

    github_event_wrapper.load_event_ids()

    while True:
        loop_start = time.time()

        try:
            github_events = github_scraper.scrape_events()
            logging.info(f"Scraped {len(github_events)} new events.")
            inserted_events = github_event_wrapper.insert_multiple_events(
                github_events=github_events
            )
            logging.info(f"Inserted {len(inserted_events)} new events.")
            deleted_count = github_event_wrapper.delete_expired_events()
            logging.info(f"Deleted {deleted_count} old events.")

        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(
                f"There was an error in the main loop, ERROR: {e}, traceback: {traceback.format_exc()}"
            )

        loop_took = time_response(loop_start)

        if loop_took < config.GITHUB_REFRESH_RATE:
            time.sleep(config.GITHUB_REFRESH_RATE - loop_took + 0.01)
