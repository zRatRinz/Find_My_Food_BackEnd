from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sklearn.feature_extraction.text import TfidfVectorizer
from pythainlp.tokenize import word_tokenize
from app.core.utils.feature_builder import build_recipe_document
from app.db.database import engine
from app.models.recipeModel import TrnRecipeModel, MapRecipeTagModel
from app.models.userModel import MasUserModel
from app.models.systemModel import MapRecipeVectorModel, SysModelVocabularyModel, SysCacheVersionModel

def thai_tokenizer(text):
    return word_tokenize(text, engine="newmm")

def run():
    with Session(engine) as db:
        recipes = db.exec(
            select(TrnRecipeModel)
            .where(TrnRecipeModel.is_active == True)
            .options(selectinload(TrnRecipeModel.recipe_tags).selectinload(MapRecipeTagModel.tag))
        ).all()

        docs = [build_recipe_document(recipe) for recipe in recipes]

        vectorizer = TfidfVectorizer(
            tokenizer=thai_tokenizer,
            token_pattern=None,
            lowercase=False,
        )
        matrix = vectorizer.fit_transform(docs)

        vocab_record = db.get(SysModelVocabularyModel, "recipe_vocab")
        if not vocab_record:
            vocab_record = SysModelVocabularyModel(name="recipe_vocab", vocabulary=vectorizer.vocabulary_)
            db.add(vocab_record)
        else:
            vocab_record.vocabulary = vectorizer.vocabulary_

        for i, recipe in enumerate(recipes):
            vec_list = matrix[i].toarray()[0].tolist()

            record = db.get(MapRecipeVectorModel, recipe.recipe_id)
            if not record:
                record = MapRecipeVectorModel(recipe_id=recipe.recipe_id, vector_data=vec_list)
                db.add(record)
            else:
                record.vector_data = vec_list

        config_record = db.get(SysCacheVersionModel, "recipe_vector_version")
        if not config_record:
            config_record = SysCacheVersionModel(cache_name="recipe_vector_version", version_number=1)
            db.add(config_record)
        else:
            config_record.version_number += 1
        db.commit()
        print("Recipe vectors built and saved to DB:", len(recipes))

if __name__ == "__main__":
    run()