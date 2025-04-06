FROM python:3.10-slim-buster

RUN apt-get update

RUN mkdir /myapp

WORKDIR /myapp
ENV PYTHONPATH=/myapp/github_events_api:/myapp

COPY github_events_api ./github_events_api
COPY shared_resources ./shared_resources

RUN pip3 install poetry

# change workdir so we run script from within github_events_scraper
WORKDIR /myapp/github_events_api

RUN poetry config virtualenvs.create false
RUN poetry install

CMD ["poetry", "run", "python", "app/main.py"]
