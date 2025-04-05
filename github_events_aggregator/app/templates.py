
from pydantic import BaseModel


class GithubEvent(BaseModel):
    id: str
    type: str
    created_at: str
    repository: str
