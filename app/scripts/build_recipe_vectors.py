from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sklearn.feature_extraction.text import TfidfVectorizer
from pythainlp.tokenize import word_tokenize
import traceback
from app.core import aiConfig
from app.core.utils.feature_builder import build_recipe_document
from app.db.database import engine
from app.models.recipeModel import TrnRecipeModel, MapRecipeTagModel
from app.models.userModel import MasUserModel
from app.models.systemModel import MapRecipeVectorModel, SysModelVocabularyModel, SysCacheVersionModel

def thai_tokenizer(text):
    return word_tokenize(text, engine="newmm")

# def run():
#     with Session(engine) as db:
#         try:
#             recipes = db.exec(
#                 select(TrnRecipeModel)
#                 .where(TrnRecipeModel.is_active == True)
#                 .options(selectinload(TrnRecipeModel.recipe_tags).selectinload(MapRecipeTagModel.tag))
#                 .order_by(TrnRecipeModel.recipe_id)
#             ).all()

#             docs = [build_recipe_document(recipe) for recipe in recipes]

#             vectorizer = TfidfVectorizer(
#                 tokenizer=thai_tokenizer,
#                 token_pattern=None,
#                 lowercase=False,
#             )
#             matrix = vectorizer.fit_transform(docs)

#             has_change = False

#             idf_list = vectorizer.idf_.tolist()
#             vocab_record = db.get(SysModelVocabularyModel, "recipe_vocab")

#             if not vocab_record:
#                 vocab_record = SysModelVocabularyModel(name="recipe_vocab", vocabulary=vectorizer.vocabulary_, idf=idf_list)
#                 db.add(vocab_record)
#                 has_change = True
#             else:
#                 if vocab_record.vocabulary != vectorizer.vocabulary_ or vocab_record.idf != idf_list:
#                     vocab_record.vocabulary = vectorizer.vocabulary_
#                     vocab_record.idf = idf_list
#                     has_change = True
#                     print("Debug: Vocabulary has changed!")

#             existing_vectors = db.exec(select(MapRecipeVectorModel)).all()
#             vector_dict = {v.recipe_id: v for v in existing_vectors}

#             for i, recipe in enumerate(recipes):
#                 # vec_list = matrix[i].toarray()[0].tolist()
#                 vec_list = matrix.getrow(i).toarray()[0].tolist()
#                 record = vector_dict.get(recipe.recipe_id)

#                 # record = db.get(MapRecipeVectorModel, recipe.recipe_id)
#                 if not record:
#                     record = MapRecipeVectorModel(recipe_id=recipe.recipe_id, vector_data=vec_list)
#                     db.add(record)
#                     has_change = True
#                 else:
#                     if record.vector_data != vec_list:
#                         record.vector_data = vec_list
#                         has_change = True
#                     # if len(record.vector_data) != len(vec_list) or not np.allclose(record.vector_data, vec_list, atol=1e-5):
#                     #     record.vector_data = vec_list
#                     #     has_change = True

#             if has_change:
#                 config_record = db.get(SysCacheVersionModel, "recipe_vector_version")
#                 if not config_record:
#                     config_record = SysCacheVersionModel(cache_name="recipe_vector_version", version_number=1)
#                     db.add(config_record)
#                 else:
#                     config_record.version_number += 1
#                 db.commit()
#                 print("Recipe vectors built and saved to DB:", len(recipes))
#             else:
#                 print("No changes in recipe vectors. Cache version skipped.")

#         except Exception as ex:
#             print(f"error: {ex}")
#             db.rollback()
#             traceback.print_exc()

def run():
    with Session(engine) as db:
        try:
            recipes = db.exec(
                select(TrnRecipeModel)
                .where(TrnRecipeModel.is_active == True)
                .options(selectinload(TrnRecipeModel.recipe_tags).selectinload(MapRecipeTagModel.tag))
                .order_by(TrnRecipeModel.recipe_id)
            ).all()

            if not recipes:
                print("ไม่มีข้อมูลสูตรอาหาร")
                return

            docs = [build_recipe_document(recipe) for recipe in recipes]

            print(f"กำลังแปลง Vector สำหรับ {len(docs)} สูตร...")
            matrix = aiConfig.embed_model.encode(docs)

            has_change = False

            existing_vectors = db.exec(select(MapRecipeVectorModel)).all()
            vector_dict = {v.recipe_id: v for v in existing_vectors}

            for i, recipe in enumerate(recipes):
                vec_list = matrix[i].tolist()
                
                record = vector_dict.get(recipe.recipe_id)

                if not record:
                    record = MapRecipeVectorModel(recipe_id=recipe.recipe_id, vector_data=vec_list)
                    db.add(record)
                    has_change = True
                else:
                    if record.vector_data != vec_list:
                        record.vector_data = vec_list
                        has_change = True

            if has_change:
                config_record = db.get(SysCacheVersionModel, "recipe_vector_version")
                if not config_record:
                    config_record = SysCacheVersionModel(cache_name="recipe_vector_version", version_number=1)
                    db.add(config_record)
                else:
                    config_record.version_number += 1
                db.commit()
                print(f"Recipe vectors built and saved to DB: {len(recipes)}")
            else:
                print("No changes in recipe vectors. Cache version skipped.")

        except Exception as ex:
            print(f"error: {ex}")
            db.rollback()
            traceback.print_exc()

if __name__ == "__main__":
    run()