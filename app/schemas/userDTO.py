from pydantic import BaseModel, Field, ConfigDict
from datetime import date

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
    gender: str | None = None
    birth_date: date | None = None

class UserAccountDTO(BaseModel):
    email: str
    username: str
    gender: str | None = None
    birth_date: date | None = None
    image_url: str | None = None
    
class GoogleRegisterDTO(BaseModel):
    temp_token: str
    username: str
    gender: str
    birth_date: date

class GoogleLoginDTO(BaseModel):
    id_token: str

class VerifyPasswordDTO(BaseModel):
    password: str

class ChangePasswordDTO(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
    
class UpdateUsernameDTO(BaseModel):
    username: str

class SimpleUserInfoDTO(BaseModel):
    user_id: int
    email: str
    username: str
    image_url: str | None = None

class UserLikeRecipeDTO(BaseModel):
    recipe_id: int
    recipe_name: str
    description: str | None = None
    cooking_time_min: int | None = None
    image_url: str | None = None
    username: str | None = None
    like_count: int = Field(default=0)
    is_liked: bool = False

    model_config = ConfigDict(from_attributes=True)