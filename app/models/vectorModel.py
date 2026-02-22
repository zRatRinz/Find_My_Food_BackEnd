from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB

class MapRecipeVectorModel(SQLModel, table=True):
    __tablename__ = "map_recipe_vector"
    recipe_id: int = Field(primary_key=True, foreign_key="trn_recipe.recipe_id")
    vector_data: list[float] = Field(sa_column=Column(JSONB))

class MapUserVectorModel(SQLModel, table=True):
    __tablename__ = "map_user_vector"
    user_id: int = Field(primary_key=True, foreign_key="mas_user.user_id")
    vector_data: list[float] = Field(sa_column=Column(JSONB))

class SysModelVocabularyModel(SQLModel, table=True):
    __tablename__ = "sys_model_vocabulary"
    name: str = Field(primary_key=True)
    vocabulary: dict = Field(sa_column=Column(JSONB))

class SysCacheVersionModel(SQLModel, table=True):
    __tablename__ = "sys_cache_version"
    cache_name: str = Field(primary_key=True)
    version_number: int = Field(default=1)