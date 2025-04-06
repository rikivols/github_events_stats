from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


@app.get("/health")
def get_health():
    ...


@app.get("/github_events_stats")
def get_stats():
    ...
