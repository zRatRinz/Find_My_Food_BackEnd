from typing import Generic,  TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class TokenResponse(BaseModel, Generic[T]):
    access_token: str
    token_type: str
    data: T | None = None

class StandardResponse(BaseModel, Generic[T]):
    status: str
    message: str | None = None
    data: T | None = None

    @classmethod
    def success(cls, data: T = None):
        return cls(
            status = "success",
            message = None,
            data = data
        )
    
    @classmethod
    def fail(cls, message: str):
        return cls(
            status = "fail",
            message = message,
            data = None
        )