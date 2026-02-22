from app.models.recipeModel import TrnRecipeModel

def build_recipe_document(recipe: TrnRecipeModel):
    title = recipe.recipe_name
    tags = " ".join(recipe.tags) if recipe.tags else ""
    # tag_type = recipe.tags_type if recipe.tags_type else ""

    return f"{title} {tags}"
