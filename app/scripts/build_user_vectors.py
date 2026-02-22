from sqlmodel import Session, select
import numpy as np
from app.db.database import engine
from app.models.recipeModel import MapRecipeLikeModel
from app.models.userModel import MasUserModel
from app.models.systemModel import MapRecipeVectorModel, MapUserVectorModel, SysCacheVersionModel

def run():
    with Session(engine) as db:
        recipe_records = db.exec(select(MapRecipeVectorModel)).all()
        recipe_vectors = {record.recipe_id: record.vector_data for record in recipe_records}

        likes = db.exec(select(MapRecipeLikeModel)).all()

        user_like_map = {}
        for like in likes:
            user_like_map.setdefault(like.user_id, []).append(like.recipe_id)

        for user_id, recipe_ids in user_like_map.items():
            vecs = [recipe_vectors[recipe_id] for recipe_id in recipe_ids if recipe_id in recipe_vectors]
            if not vecs:
                continue
            user_vector = np.mean(vecs, axis=0).tolist()
            record = db.get(MapUserVectorModel, user_id)
            if not record:
                record = MapUserVectorModel(user_id=user_id, vector_data=user_vector)
                db.add(record)
            else:
                record.vector_data = user_vector

        config_record = db.get(SysCacheVersionModel, "user_vector_version")
        if not config_record:
            config_record = SysCacheVersionModel(cache_name="user_vector_version", version_number=1)
            db.add(config_record)
        else:
            config_record.version_number += 1
        db.commit()
        print("User vectors built and saved to DB")

if __name__ == "__main__":
    run()