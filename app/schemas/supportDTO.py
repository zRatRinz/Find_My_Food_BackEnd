from pydantic import BaseModel

class FeedBackDTO(BaseModel):
    title: str
    detail: str