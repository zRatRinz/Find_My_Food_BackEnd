from PIL import Image
import numpy as np
import ai_edge_litert.interpreter as tflite
import io
from google import genai
from google.genai import types
import json
from sqlmodel import Session
import base64
from app.core.config import GOOGLE_AI_STUDIO_KEY, GOOGLE_ANALIZE_IMG_MODEL, GOOGLE_IMG_GEN_MODEL
from app.enums.errorCodeEnum import ErrorCodeEnum
from app.services import recipeService

import time

print("📦 กำลังโหลดโมเดล TF Lite...")
interpreter = tflite.Interpreter(model_path="app/ai/model.tflite")
interpreter.allocate_tensors()

# ดึงสเปคทางเข้า (Input) และทางออก (Output) ของโมเดล
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

CLASS_NAMES = ["food", "non_food"]

# (Optional) โค้ด Dummy วอร์มอัปเครื่องแก้ Cold Start
dummy_input = np.zeros(input_details[0]['shape'], dtype=np.float32)
interpreter.set_tensor(input_details[0]['index'], dummy_input)
interpreter.invoke()
print("วอร์มอัปโมเดล TF Lite พร้อมใช้งาน!")

# model = tf.keras.models.load_model("app/ai/MNV2_Project_2.keras") 

# print("กำลังวอร์มอัป MobileNetV2 (Cold Start)...")
# dummy_input = np.zeros((1, 224, 224, 3), dtype=np.float32)
# model.predict(dummy_input)
# print("วอร์มอัปเสร็จสิ้น!")

client = genai.Client(api_key=GOOGLE_AI_STUDIO_KEY)

# food_schema = {
#     "type": "OBJECT",
#     "properties": {
#         "is_food": {
#             "type": "BOOLEAN", 
#             "description": "True if the image contains food or beverage, False otherwise."
#         },
#         "predictions": {
#             "type": "ARRAY",
#             "description": "Top 3 predicted food names in Thai language. Empty array if not food.",
#             "items": {
#                 "type": "OBJECT",
#                 "properties": {
#                     "name": {"type": "STRING", "description": "Exact food name in Thai language"}
#                 },
#                 "required": ["name"]
#             }
#         }
#     },
#     "required": ["is_food","predictions"]
# }

food_schema = {
    "type": "OBJECT",
    "properties": {
        "is_food": {
            "type": "BOOLEAN", 
            "description": "ตอบ true ถ้ารูปนี้คืออาหารหรือเครื่องดื่ม, ตอบ false ถ้ารูปนี้ไม่ใช่อาหาร"
        },
        "predictions": {
            "type": "ARRAY",
            "description": "รายชื่ออาหารที่คาดเดา 3 อันดับแรก (ถ้ารูปนี้ไม่ใช่อาหาร ให้ตอบเป็น Array ว่าง [])",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING", "description": "ชื่ออาหารเป็นภาษาไทย"}
                },
                "required": ["name"]
            }
        }
    },
    "required": ["is_food", "predictions"]
}

def predict_food_image(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((224, 224))
    image_array = np.array(image).astype("float32")
    image_batch = np.expand_dims(image_array, axis=0)


    interpreter.set_tensor(input_details[0]['index'], image_batch)
    interpreter.invoke()
    # predictions = model.predict(image_batch)
    predictions = interpreter.get_tensor(output_details[0]['index'])
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
    # response = client.models.generate_content(
    #     model="models/",
    #     contents=[img],
    #     config=types.GenerateContentConfig(
    #         system_instruction="You are a food expert. Analyze the provided image. If it is food or beverage, set 'is_food' to true and provide the top 3 likely food names in Thai. If not, set 'is_food' to false and return an empty array for predictions.",
    #         response_mime_type="application/json",
    #         response_schema=food_schema,
    #     ),
    # )
    response = client.models.generate_content(
        model=GOOGLE_ANALIZE_IMG_MODEL,
        contents=[img, "รูปนี้ใช่อาหารหรือไม่? ถ้าใช่ให้บอกชื่ออาหารที่น่าจะเป็นไปได้ 3 อันดับแรก ถ้าไม่ใช่ให้ตอบว่าไม่ใช่"],
        config=types.GenerateContentConfig(
            system_instruction="คุณคือผู้เชี่ยวชาญด้านอาหาร วิเคราะห์รูปภาพและตอบกลับในรูปแบบ JSON. หากเป็นอาหารให้ระบุ is_food เป็น true พร้อมรายชื่อ หากไม่ใช่ให้ระบุ is_food เป็น false และไม่ต้องใส่รายชื่ออาหาร",
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
    
def generate_recipe_image(recipe_name: str, ingredients: list[str]):
    try:
        total_time = time.perf_counter()
        ingredients_str = ", ".join(ingredients)
        prompt_text = (
            f"Professional and appetizing food photography of a Thai dish called '{recipe_name}'. "
            f"This dish highlights the following key ingredients: {ingredients_str}. "
            f"Focus on the final cooked dish with clear visibility of the solid ingredients like meat and herbs. "
            f"Do NOT show any raw seasoning powders, salt, sugar, or sauce bottles. "
            f"Soft natural window light, cozy homemade food style, appetizing, realistic and approachable."
        )

        print(f"กำลังสั่ง Nano Banana 4 วาดรูป: {prompt_text}")
        t_start = time.perf_counter()
        response = client.models.generate_content(
            model=GOOGLE_IMG_GEN_MODEL,
            contents=[prompt_text],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="1:1"
                )
            )
        )
        t_end = time.perf_counter()
        print(f"Nano Banana 4 ใช้เวลา: {t_end - t_start:.2f} วินาที")

        image_bytes = None
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(f"AI ส่งข้อความมาด้วย: {part.text}")
                elif part.inline_data is not None:
                    image_bytes = part.inline_data.data
                    break

        if image_bytes:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85, optimize=True)
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            print("สร้างรูปและแปลงเป็น Base64 สำเร็จ!")
            print(f"Total ใช้เวลา: {time.perf_counter() - total_time:.2f} วินาที")
            return {
                "recipe_name": recipe_name,
                "image_base64": img_base64
            }, None

        else:
            print("ไม่สามารถสร้างรูปและแปลงเป็น Base64 ได้!")
            print(f"Total ใช้เวลา: {time.perf_counter() - total_time:.2f} วินาที")
            return None, ErrorCodeEnum.INTERNAL_ERROR

    except Exception as ex:
        print(f"error: {ex}")
        return None, ErrorCodeEnum.INTERNAL_ERROR

# def generate_recipe_image(recipe_name: str, ingredients: list[str]):
#     try:
#         total_time = time.perf_counter()
#         ingredients_str = ", ".join(ingredients)
#         prompt_text = (
#             f"Professional and appetizing food photography of a Thai dish called '{recipe_name}'. "
#             f"This dish highlights the following key ingredients: {ingredients_str}. "
#             f"Focus on the final cooked dish with clear visibility of the solid ingredients like meat and herbs. "
#             f"Do NOT show any raw seasoning powders, salt, sugar, or sauce bottles. "
#             f"Soft natural window light, cozy homemade food style, appetizing, realistic and approachable."
#         )

#         print(f"กำลังสั่ง Imagen 4 วาดรูป: {prompt_text}")
#         t_start = time.perf_counter()
#         response = client.models.generate_images(
#             model=GOOGLE_IMG_GEN_MODEL,
#             prompt=prompt_text,
#             config={
#                 "number_of_images": 1,
#                 "aspect_ratio": "1:1"
#             }
#         )
#         t_end = time.perf_counter()
#         print(f"Imagen 4 ใช้เวลา: {t_end - t_start:.2f} วินาที")

#         if response.generated_images:
#             image_bytes = response.generated_images[0].image.image_bytes
#             img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

#             buffered = io.BytesIO()
#             img.save(buffered, format="JPEG", quality=85, optimize=True)

#             img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
#             print("สร้างรูปและแปลงเป็น Base64 สำเร็จ!")
#             print(f"Total ใช้เวลา: {time.perf_counter() - total_time:.2f} วินาที")
#             return {
#                 "recipe_name": recipe_name,
#                 "image_base64": img_base64
#             }, None

#         else:
#             print("ไม่สามารถสร้างรูปและแปลงเป็น Base64 ได้!")
#             print(f"Total ใช้เวลา: {time.perf_counter() - total_time:.2f} วินาที")
#             return None, ErrorCodeEnum.INTERNAL_ERROR

#     except Exception as ex:
#         print(f"error: {ex}")
#         return None, ErrorCodeEnum.INTERNAL_ERROR

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
