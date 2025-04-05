FROM python:3.10-slim-buster

RUN apt-get update && apt-get install -y gcc g++

RUN mkdir /myapp
COPY pyproject.toml /myapp
COPY poetry.lock /myapp
WORKDIR /myapp
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install

COPY . /myapp

CMD ["python3", "main.py"]
