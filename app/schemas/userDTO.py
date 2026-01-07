from pydantic import BaseModel

class UserLoginDTO(BaseModel):
    username: str
    password: str

class PasswordHashDTO(UserLoginDTO):
    password_hash: str

class TokenData(BaseModel):
    user_id: int | None = None

class UserRegisterDTO(BaseModel):
    email: str
    password: str
    username: str
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    age: int | None = None

class UserAccountDTO(BaseModel):
    email: str
    username: str
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    age: int | None = None
    image_url: str | None = None
    
class GoogleRegisterModel(BaseModel):
    temp_token: str
    username: str
    gender: str
    age: int
    