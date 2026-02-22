# import pickle
from cachetools import LRUCache
from threading import Lock
from sqlmodel import Session, select
import numpy as np
from app.models.systemModel import MapRecipeVectorModel, MapUserVectorModel, SysCacheVersionModel

_recipe_cache_version = 0
_user_cache_version = 0
_recipe_vectors_cache = None
_user_vectors_cache = LRUCache(maxsize=50)

_recipe_lock = Lock()
_user_lock = Lock()

def get_recipe_vectors(db: Session):
    global _recipe_vectors_cache, _recipe_cache_version

    db_version_record = db.get(SysCacheVersionModel, "recipe_vector_version")
    db_version = db_version_record.version_number if db_version_record else 0

    if _recipe_cache_version != db_version or _recipe_vectors_cache is None:
        with _recipe_lock:
            if _recipe_cache_version != db_version or _recipe_vectors_cache is None:
                rows = db.exec(select(MapRecipeVectorModel)).all()
                _recipe_vectors_cache = {row.recipe_id: np.array(row.vector_data) for row in rows}

                with _user_lock:
                    _user_vectors_cache.clear()

                _recipe_cache_version = db_version
    return _recipe_vectors_cache

def get_user_vector(db:Session, user_id: int):
    global _user_cache_version

    db_version_record = db.get(SysCacheVersionModel, "user_vector_version")
    db_version = db_version_record.version_number if db_version_record else 0

    with _user_lock:
        if _user_cache_version != db_version:
            _user_vectors_cache.clear()
            _user_cache_version = db_version

        if user_id not in _user_vectors_cache:
            record = db.get(MapUserVectorModel, user_id)
            if record:
                _user_vectors_cache[user_id] = np.array(record.vector_data)
            else:
                return None
    return _user_vectors_cache.get(user_id)
