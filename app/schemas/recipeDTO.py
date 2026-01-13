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
    username: str 
    create_date: datetime | None = None
    update_date: datetime | None = None
    is_public: bool
    is_active: bool

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

class RecipeDetailResponseDTO(RecipeResponseDTO):
    ingredients: list[RecipeIngredientResponseDTO]
    steps: list[RecipeStepResponseDTO]

class IngredientResponseDTO(BaseModel):
    ingredient_id: int
    ingredient_name: str