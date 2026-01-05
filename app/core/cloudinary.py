import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

from app.core.config import CLOUD_NAME, API_KEY, API_SECRET, CLOUD_USER_IMG, CLOUD_FOOD_IMG

cloudinary.config(
    cloud_name = CLOUD_NAME,
    api_key = API_KEY,
    api_secret = API_SECRET,
    secure = True
)

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