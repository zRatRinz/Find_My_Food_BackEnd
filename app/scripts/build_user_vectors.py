from sqlmodel import Session, select
import numpy as np
import traceback
from app.db.database import engine
from app.models.recipeModel import MapRecipeLikeModel
from app.models.userModel import MasUserModel
from app.models.systemModel import MapRecipeVectorModel, MapUserVectorModel, SysCacheVersionModel

def run():
    with Session(engine) as db:
        try:
            recipe_records = db.exec(select(MapRecipeVectorModel)).all()
            recipe_vectors = {record.recipe_id: record.vector_data for record in recipe_records}

            likes = db.exec(select(MapRecipeLikeModel).order_by(MapRecipeLikeModel.user_id, MapRecipeLikeModel.recipe_id)).all()

            if not likes:
                print("No likes found. Skipping user vector build.")
                return

            user_like_map = {}
            for like in likes:
                user_like_map.setdefault(like.user_id, []).append(like.recipe_id)

            existing_user_records = db.exec(select(MapUserVectorModel)).all()
            user_vector_dict = {record.user_id: record for record in existing_user_records}

            has_change = False

            for user_id, recipe_ids in user_like_map.items():
                vecs = [recipe_vectors[recipe_id] for recipe_id in recipe_ids if recipe_id in recipe_vectors]
                if not vecs:
                    continue

                user_vector = np.mean(vecs, axis=0).tolist()
                # record = db.get(MapUserVectorModel, user_id)
                record = user_vector_dict.get(user_id)
                if not record:
                    record = MapUserVectorModel(user_id=user_id, vector_data=user_vector)
                    db.add(record)
                    has_change = True
                else:
                    if record.vector_data != user_vector:
                        record.vector_data = user_vector
                        has_change = True

            if has_change:
                config_record = db.get(SysCacheVersionModel, "user_vector_version")
                if not config_record:
                    config_record = SysCacheVersionModel(cache_name="user_vector_version", version_number=1)
                    db.add(config_record)
                else:
                    config_record.version_number += 1

                db.commit()
                print("User vectors built and saved to DB")
            else:
                print("No changes detected. User vectors not updated.")

        except Exception as ex:
            print(f"error: {str(ex)}")
            db.rollback()
            traceback.print_exc()

if __name__ == "__main__":
    run()