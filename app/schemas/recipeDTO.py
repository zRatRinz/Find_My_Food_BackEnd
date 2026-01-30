from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class CreateNewRecipeIngredientDTO(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0, description="จำนวนต้องมากกว่า 0")
    unit_id: int

class CreateNewRecipeStepDTO(BaseModel):
    step_no: int
    instruction: str

class CreateNewRecipeDTO(BaseModel):
    recipe_name: str
    description: str | None = None
    cooking_time_min: int | None = Field(default=None, gt=0)
    image_url: str | None = None
    is_public: bool
    ingredients: list[CreateNewRecipeIngredientDTO]
    steps: list[CreateNewRecipeStepDTO]

class UpdateRecipeIngredientDTO(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0, description="จำนวนต้องมากกว่า 0")
    unit_id: int

class UpdateRecipeIngredientListDTO(BaseModel):
    ingredients: list[UpdateRecipeIngredientDTO]

class UpdateRecipeStepDTO(BaseModel):
    step_no: int
    instruction: str

class UpdateRecipeStepListDTO(BaseModel):
    steps: list[UpdateRecipeStepDTO]

class UpdateRecipeHeaderDTO(BaseModel):
    recipe_name: str
    description: str | None = None
    cooking_time_min: int | None = None
    is_public: bool
    is_active: bool

class RecipeResponseDTO(BaseModel):
    recipe_id: int
    recipe_name: str
    description: str | None = None
    cooking_time_min: int | None = None
    image_url: str | None = None
    username: str | None = None
    create_date: datetime | None = None
    update_date: datetime | None = None
    is_public: bool
    is_active: bool
    like_count: int = Field(default=0)

    model_config = ConfigDict(from_attributes=True)

class RecipeIngredientResponseDTO(BaseModel):
    ingredient_id: int
    ingredient_name: str
    quantity: float
    unit_id: int
    unit_name: str
    
    model_config = ConfigDict(from_attributes=True)

class RecipeStepResponseDTO(BaseModel):
    step_no: int
    instruction: str

    model_config = ConfigDict(from_attributes=True)

class RecipeDetailResponseDTO(BaseModel):
    recipe: RecipeResponseDTO
    ingredients: list[RecipeIngredientResponseDTO]
    steps: list[RecipeStepResponseDTO]
    is_liked: bool

class IngredientResponseDTO(BaseModel):
    ingredient_id: int
    ingredient_name: str

class LikeRecipeResponseDTO(BaseModel):
    like_count: int = Field(default=0)
    is_liked: bool