from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

# class LoginAccountModel(SQLModel, table=True):
#     __tablename__ = "mas_user_login"
#     user_id: int = Field(primary_key=True)
#     username: str
#     password: str
#     last_login: datetime | None = None

#     user_info: "UserInfoModel" = Relationship(back_populates="login_account")

# class UserInfoModel(SQLModel, table=True):
#     __tablename__ = "mas_user"
#     user_id: int = Field(primary_key=True, foreign_key="mas_user_login.user_id")
#     first_name: str | None = None
#     last_name: str | None = None
#     age: int | None = None
#     gender: str | None = None
#     email: str
#     image_url: str | None = None
#     create_date: datetime = Field(default_factory=datetime.now)
#     update_date: datetime = Field(default_factory=datetime.now)

#     login_account: "LoginAccountModel" = Relationship(back_populates="user_info")

class UserAccountModel(SQLModel, table=True):
    __tablename__ = "mas_user"
    user_id: int = Field(primary_key=True)
    email: str = Field(unique=True)
    username: str | None = Field(unique=True)
    password: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    age: int | None = None
    image_url: str | None = None
    provider: str = Field(default="local")
    create_date: datetime = Field(default_factory=datetime.now)
    update_date: datetime | None = None
    last_login: datetime | None = None
    is_active: bool = True
