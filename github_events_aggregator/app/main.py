

from app.config import Config
from app.database.github_event_wrapper import GithubEventWrapper
from sqlalchemy import create_engine


config = Config(path="../config.toml", spec_path="../../config.spec.toml")

db_engine = create_engine(
    f"postgresql://{config.database_user}:{config.database_password}@"
    f"{config.database_host}:{config.database_port}/{config.database_name}"
)
github_event_wrapper = GithubEventWrapper(config=config, db_engine=db_engine)


if __name__ == "__main__":
    pass