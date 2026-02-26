from PIL import Image
import numpy as np
import tensorflow as tf
import io
from google import genai
from google.genai import types
import json
from sqlmodel import Session
from app.core.config import GOOGLE_AI_STUDIO_KEY
from app.ai.class_map import CLASS_MAP
from app.enums.errorCodeEnum import ErrorCodeEnum
from app.services import recipeService

import time

model = tf.keras.models.load_model("app/ai/MNV2_Project_2.keras") 
CLASS_NAMES = ["food", "non_food"] 

print("กำลังวอร์มอัป MobileNetV2 (Cold Start)...")
dummy_input = np.zeros((1, 224, 224, 3), dtype=np.float32)
model.predict(dummy_input)
print("✅ วอร์มอัปเสร็จสิ้น!")

client = genai.Client(api_key=GOOGLE_AI_STUDIO_KEY)

food_schema = {
    "type": "OBJECT",
    "properties": {
        "is_food": {
            "type": "BOOLEAN", 
            "description": "True if the image contains food or beverage, False otherwise."
        },
        "predictions": {
            "type": "ARRAY",
            "description": "Top 3 predicted food names in Thai language. Empty array if not food.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING", "description": "Exact food name in Thai language"}
                },
                "required": ["name"]
            }
        }
    },
    "required": ["is_food","predictions"]
}

def predict_food_image(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((224, 224))
    image_array = np.array(image).astype("float32")
    image_batch = np.expand_dims(image_array, axis=0)

    predictions = model.predict(image_batch)
    scores = predictions[0]
        
    predicted_index = np.argmax(scores)
    confidence = scores[predicted_index]
    result_class = CLASS_NAMES[predicted_index]

    is_food = (result_class == "food")
        
    return {
        "is_food": is_food,
        "class_name": result_class,
        "confidence": round(float(confidence) * 100, 2)
    }
    
def scan_food_image(image_bytes: bytes):
    img = Image.open(io.BytesIO(image_bytes))
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[img],
        config=types.GenerateContentConfig(
            system_instruction="You are a food expert. Analyze the provided image. If it is food or beverage, set 'is_food' to true and provide the top 3 likely food names in Thai. If not, set 'is_food' to false and return an empty array for predictions.",
            response_mime_type="application/json",
            response_schema=food_schema,
        ),
    )
    return json.loads(response.text)
    
def analyze_food_image(user_id: int, image_bytes: bytes, db: Session):
    try:
        total_time = time.perf_counter()

        t1_start = time.perf_counter()
        prediction_result = predict_food_image(image_bytes)
        t1_end = time.perf_counter()
        print(f"MobileNetV2 ใช้เวลา: {t1_end - t1_start:.2f} วินาที")

        if not prediction_result["is_food"]:
            print("ไม่ใช่อาหาร by MobileNetV2")
            return None, ErrorCodeEnum.NOT_FOUND

        t2_start = time.perf_counter()
        ai_result = scan_food_image(image_bytes)
        t2_end = time.perf_counter()
        print(f"AI ใช้เวลา: {t2_end - t2_start:.2f} วินาที")

        if not ai_result or "predictions" not in ai_result:
            raise ValueError("AI ส่งข้อมูลกลับมาไม่ครบถ้วน")
        
        if ai_result["is_food"] == False:
            print("ไม่ใช่อาหาร by AI")
            return None, ErrorCodeEnum.NOT_FOUND

        if not ai_result["predictions"]:
            return None, None
        
        predicted_names = [recipe["name"] for recipe in ai_result["predictions"]]
        print(f"AI คาดเดาว่าเป็น: {predicted_names}")

        t3_start = time.perf_counter()
        recipe_result = recipeService.get_recipe_by_ai_name(user_id, predicted_names, db)
        t3_end = time.perf_counter()
        print(f"DB ใช้เวลา: {t3_end - t3_start:.2f} วินาที")

        print(f"Total ใช้เวลา: {time.perf_counter() - total_time:.2f} วินาที")

        return recipe_result, None
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, ErrorCodeEnum.INTERNAL_ERROR

# def predict_food_image(image_bytes: bytes):
#     try:
#         image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#         image = image.resize((224, 224))
#         image_array = np.array(image).astype("float32")
#         image_batch = np.expand_dims(image_array, axis=0)
#         predictions = model.predict(image_batch)
#         scores = predictions[0]

#         # class_index = int(np.argmax(scores))
#         # confidence = float(scores[class_index])
#         # return {
#         #     "class_index": class_index,
#         #     "class_name": CLASS_MAP.get(class_index, "Unknown"),
#         #     "confidence": round(confidence, 4)
#         # }

#         top_indices = scores.argsort()[::-1][:3]

#         top_3 = [
#             {
#                 "class_name": CLASS_MAP.get(i, "Unknown"),
#                 "confidence": round(float(scores[i]), 4)
#             }
#             for i in top_indices
#         ]

#         return {
#             "top_3": top_3
#         }

#     except Exception as ex:
#         raise Exception(f"Error: {str(ex)}")
