import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url
import uuid

from app.core.config import CLOUD_NAME, API_KEY, API_SECRET, CLOUD_USER_IMG, CLOUD_FOOD_IMG

cloudinary.config(
    cloud_name = CLOUD_NAME,
    api_key = API_KEY,
    api_secret = API_SECRET,
    secure = True
)

def upload_temp_image_to_cloudinary(file):
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder = "temp-img",
            public_id = str(uuid.uuid4()),
        )
        return result.get("secure_url")
        # return {"url": result.get("secure_url"), "public_id": result.get("public_id")}
    except Exception as ex:
        print(f"Cloudinary Error: {str(ex)}")
        return None
    
# def move_temp_image_to_food_folder(recipe_id: int, temp_public_id: str):
#     new_public_id = f"{CLOUD_FOOD_IMG}/food_img_{recipe_id}"

#     response = cloudinary.uploader.rename(
#         temp_public_id,
#         new_public_id,
#         overwrite=True
#     )
#     print(response)

#     return response["secure_url"]

def move_temp_image_to_food_folder(recipe_id: int, image_url: str):
        if "/upload/" not in image_url:
            return None
        path_after_upload = image_url.split("/upload/")[1]
        parts = path_after_upload.split("/")
        if parts[0].startswith("v") and parts[0][1:].isdigit():
            parts = parts[1:]

        full_path = "/".join(parts)
        current_public_id = full_path.rsplit(".", 1)[0]
        new_public_id = f"{CLOUD_FOOD_IMG}/food_img_{recipe_id}"
        response = cloudinary.uploader.rename(
            from_public_id= current_public_id,
            to_public_id= new_public_id,
            overwrite = True,
        )
        cloudinary.api.update(
            new_public_id,
            asset_folder = CLOUD_FOOD_IMG,
            display_name=f"food_img_{recipe_id}"
        )
        return response.get("secure_url")

def upload_user_image_to_cloudinary(user_id: int, file):
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder = CLOUD_USER_IMG,
            public_id = f"user_img_{user_id}",
            overwrite = True,
            unique_filename = False
        )
        return result.get("secure_url")
    except Exception as ex:
        print(f"Cloudinary Error: {str(ex)}")
        return None
    
def upload_food_image_to_cloudinary(food_id: int, file):
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder = CLOUD_FOOD_IMG,
            public_id = f"food_img_{food_id}",
            overwrite = True,
            unique_filename = False
        )
        return result.get("secure_url")
    except Exception as ex:
        print(f"Cloudinary Error: {str(ex)}")
        return None