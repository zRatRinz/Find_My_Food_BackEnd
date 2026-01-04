from pydantic import BaseModel

class UserLoginDTO(BaseModel):
    username: str
    password: str

class PasswordHashDTO(UserLoginDTO):
    password_hash: str

class TokenData(BaseModel):
    user_id: int | None = None

class UserRegisterDTO(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    age: int
    gender: str
    email: str

class UserProfileDTO(BaseModel):
    username: str
    first_name: str
    last_name: str
    age: int
    gender: str
    email: str
    image_url: str | None = None

class UserLoginResponseDTO(BaseModel):
    user_info: UserProfileDTO
    