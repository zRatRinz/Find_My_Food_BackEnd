import io
import time
import requests
import numpy as np
import tensorflow as tf
from PIL import Image
from sqlmodel import Session, select
from app.db.database import engine 
from app.models.recipeModel import TrnRecipeModel, MapRecipeImageVectorModel 
from app.models.userModel import MasUserModel

print("⏳ กำลังโหลด MobileNetV2 Feature Extractor...")
base_model = tf.keras.applications.MobileNetV2(weights='imagenet', include_top=False, pooling='avg')
print("✅ โหลด MobileNetV2 สำเร็จ!")

def get_image_vector_from_bytes(image_bytes: bytes) -> list[float]:
    """แปลงรูปภาพเป็น Array 1280 มิติ"""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((224, 224))
    
    image_array = np.array(image).astype("float32")
    image_batch = np.expand_dims(image_array, axis=0)
    
    features = base_model.predict(image_batch, verbose=0)
    return features[0].tolist()

def process_all_recipe_images(db: Session):
    recipes = db.exec(
        select(TrnRecipeModel)
        .where(TrnRecipeModel.is_active == True)
        .where(TrnRecipeModel.image_url != None)
        .where(TrnRecipeModel.image_url != "")
    ).all()

    if not recipes:
        print("📭 ไม่พบสูตรอาหารที่มีรูปภาพในระบบ")
        return

    print(f"🔍 พบสูตรอาหารที่มีรูปภาพจำนวน {len(recipes)} รายการ... เริ่มกระบวนการ!")

    success_count = 0
    fail_count = 0
    skip_count = 0

    for recipe in recipes:
        existing_vec = db.get(MapRecipeImageVectorModel, recipe.recipe_id)
        if existing_vec:
            skip_count += 1
            print(f"⏩ [ID: {recipe.recipe_id}] ข้าม - มีข้อมูลใน DB แล้ว")
            continue 

        try:
            print(f"⏳ [ID: {recipe.recipe_id}] กำลังดาวน์โหลดรูปภาพ...")
            response = requests.get(recipe.image_url, timeout=10)
            
            if response.status_code == 200:
                image_bytes = response.content
                
                vector_data = get_image_vector_from_bytes(image_bytes)
                
                new_image_vec = MapRecipeImageVectorModel(
                    recipe_id=recipe.recipe_id,
                    image_vector=vector_data
                )
                db.add(new_image_vec)
                db.commit()
                
                success_count += 1
                print(f"[ID: {recipe.recipe_id}] สกัด Vector และบันทึกสำเร็จ!")
            else:
                fail_count += 1
                print(f"[ID: {recipe.recipe_id}] โหลดรูปไม่สำเร็จ (HTTP Status: {response.status_code})")

        except Exception as e:
            db.rollback()
            fail_count += 1
            print(f"[ID: {recipe.recipe_id}] เกิดข้อผิดพลาด: {str(e)}")
            
        time.sleep(0.1) 

    print("\n" + "="*40)
    print(f"🎉 สรุปผลการทำงาน:")
    print(f"✅ สำเร็จ: {success_count} รายการ")
    print(f"⏩ ข้าม (มีอยู่แล้ว): {skip_count} รายการ")
    print(f"❌ ล้มเหลว: {fail_count} รายการ")
    print("="*40)

if __name__ == "__main__":
    with Session(engine) as db:
        process_all_recipe_images(db)