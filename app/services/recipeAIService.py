from PIL import Image
import numpy as np
import ai_edge_litert.interpreter as tflite
import io
from google import genai
from google.genai import types
import json
from sqlmodel import Session, select
import base64
from app.core.config import GOOGLE_AI_STUDIO_KEY, GOOGLE_ANALIZE_IMG_MODEL, GOOGLE_IMG_GEN_MODEL, GOOGLE_GEN_CONTENT_MODEL
from app.core.exceptions import NotFoundException
from app.enums.errorCodeEnum import ErrorCodeEnum
from app.models.recipeModel import MasTagModel, TrnRecipeModel, MasIngredientModel, DtlRecipeIngredientModel, DtlRecipeStepModel, MapRecipeTagModel
from app.models.unitModel import UnitModel
from app.schemas.recipeDTO import ScanIngredientResponseDTO, AnalyzeFoodResponseDTO
from app.services import recipeService

import time

# CLASS_NAMES = ["food", "non_food"]
CLASS_NAMES = [
    'ข้าวผัด', 'ผัดกะเพรา', 'ผัดไท',
    'ผัดผงกะหรี่', 'ผัดซีอิ๊ว', 'ข้าวไข่เจียว',
    'ส้มตำ', 'สุกี้', 'ทอดกระเทียม',
    'ต้มยำ', 'non_food'
]

print("กำลังโหลดโมเดล TF Lite ทั้ง 2 ตัว...")
# --- 1. โหลดโมเดลทายชื่อ 11 คลาส ---
classifier_interpreter = tflite.Interpreter(model_path="app/ai/model_11class_new.tflite")
classifier_interpreter.allocate_tensors()
class_input_details = classifier_interpreter.get_input_details()
class_output_details = classifier_interpreter.get_output_details()
# --- 2. โหลดโมเดลสกัดลายนิ้วมือภาพ (ตัวใหม่) ---
feature_interpreter = tflite.Interpreter(model_path="app/ai/feature_extractor.tflite")
feature_interpreter.allocate_tensors()
feat_input_details = feature_interpreter.get_input_details()
feat_output_details = feature_interpreter.get_output_details()
print("กำลังวอร์มอัปโมเดล...")
dummy_class_input = np.zeros(class_input_details[0]['shape'], dtype=np.float32)
classifier_interpreter.set_tensor(class_input_details[0]['index'], dummy_class_input)
classifier_interpreter.invoke()

dummy_feat_input = np.zeros(feat_input_details[0]['shape'], dtype=np.float32)
feature_interpreter.set_tensor(feat_input_details[0]['index'], dummy_feat_input)
feature_interpreter.invoke()
print("วอร์มอัปโมเดล TF Lite พร้อมใช้งาน!")


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
            "description": "ตอบ true ถ้ารูปนี้คืออาหาร, ตอบ false ถ้ารูปนี้ไม่ใช่อาหาร"
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

ingredient_schema = {
    "type": "OBJECT",
    "properties": {
        "has_ingredients": {
            "type": "BOOLEAN",
            "description": "ตอบ true ถ้าในภาพมี 'วัตถุดิบสด' ที่ยังไม่ปรุงสุก ตอบ false ถ้าเป็น 'อาหารที่ปรุงเสร็จแล้ว' หรือรูปอื่นๆ ที่ไม่ใช่วัตถุดิบ"
        },
        "ingredients": {
            "type": "ARRAY",
            "items": {
                "type": "STRING"
            },
            "description": "รายชื่อวัตถุดิบสดสำหรับทำอาหารที่พบ (ถ้าเป็นอาหารปรุงสุกแล้วให้ตอบเป็น [] ทันที)"
        }
    },
    "required": ["has_ingredients","ingredients"]
}

recipe_list_schema = {
    "type": "OBJECT",
    "properties": {
        "recipes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "recipe_name": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "cooking_time_min": {"type": "INTEGER", "description": "เวลาทำอาหาร (นาที)"},
                    "ingredients": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "ingredient_name": {"type": "STRING", "description": "ชื่อวัตถุดิบมาตรฐาน (ให้ตอบเฉพาะคำนามหลัก เช่น 'เนื้อหมู', 'กระเทียม' ห้ามใส่คำขยายเช่น 'สับละเอียด' หรือ 'หั่นเต๋า' เด็ดขาด)"},
                                "quantity": {"type": "NUMBER", "description": "ปริมาณ"},
                                "unit_id": {"type": "INTEGER", "description": "รหัสหน่วยตวง"},
                                "is_main_ingredient": {"type": "BOOLEAN"},
                                "ingredient_group": {
                                    "type": "STRING", 
                                    "nullable": True, 
                                    "description": "ระบุเฉพาะประเภทของเนื้อสัตว์หลักเท่านั้น (เช่น 'เนื้อหมู', 'เนื้อไก่', 'เนื้อวัว', 'เนื้อปลา') หากวัตถุดิบนั้นไม่ใช่เนื้อสัตว์ประเภทดังกล่าว ให้ตอบเป็น null เด็ดขาด"
                                },
                                "pantry_days": {"type": "INTEGER", "description": "อายุเก็บรักษาอุณหภูมิห้อง (วัน) ถ้าเก็บไม่ได้ให้ใส่ 0"},
                                "fridge_days": {"type": "INTEGER", "description": "อายุเก็บรักษาในตู้เย็นช่องธรรมดา (วัน)"},
                                "freezer_days": {"type": "INTEGER", "description": "อายุเก็บรักษาในช่องแช่แข็ง (วัน)"}
                            },
                            "required": ["ingredient_name", "quantity", "unit_id", "is_main_ingredient"]
                        }
                    },
                    "steps": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "step_no": {"type": "INTEGER"},
                                "instruction": {"type": "STRING"}
                            },
                            "required": ["step_no", "instruction"]
                        }
                    },
                    "tags": {
                        "type": "ARRAY",
                        "description": "เลือก tag_id ที่เกี่ยวข้องกับเมนูนี้จากรายการที่ให้ไป (เลือกได้หลายอัน)",
                        "items": {"type": "INTEGER"}
                    }
                },
                "required": ["recipe_name", "description", "cooking_time_min", "ingredients", "steps", "tags"]
            }
        }
    },
    "required": ["recipes"]
}

def predict_food_image(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((224, 224))
    image_array = np.array(image).astype("float32")
    image_batch = np.expand_dims(image_array, axis=0)


    classifier_interpreter.set_tensor(class_input_details[0]['index'], image_batch)
    classifier_interpreter.invoke()
    predictions = classifier_interpreter.get_tensor(class_output_details[0]['index'])
    scores = predictions[0]
    # predictions = model.predict(image_batch)  
        
    predicted_index = np.argmax(scores)
    confidence = scores[predicted_index]
    result_class = CLASS_NAMES[predicted_index]

    is_food = (result_class != "non_food")
        
    return {
        "is_food": is_food,
        "class_name": result_class,
        "confidence": round(float(confidence) * 100, 2)
    }

def get_image_vector(image_bytes: bytes) -> list[float]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((224, 224))
    
    image_array = np.array(image).astype("float32")
    image_batch = np.expand_dims(image_array, axis=0)
    
    feature_interpreter.set_tensor(feat_input_details[0]['index'], image_batch)
    feature_interpreter.invoke()
    features = feature_interpreter.get_tensor(feat_output_details[0]['index'])
    return features[0].tolist()
    
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
    
def analyze_food_image(user_id: int, image_bytes: bytes, force_search: bool, db: Session):
    try:
        total_time = time.perf_counter()

        t1_start = time.perf_counter()
        prediction_result = predict_food_image(image_bytes)
        t1_end = time.perf_counter()
        print(f"MobileNetV2 ใช้เวลา: {t1_end - t1_start:.2f} วินาที")

        if not prediction_result["is_food"] and not force_search:
            print("ไม่ใช่อาหาร by MobileNetV2")
            # raise NotFoundException("รูปภาพนี้ไม่ใช่อาหาร กรุณาเลือกรูปภาพอาหาร")
            return AnalyzeFoodResponseDTO(
                is_food=False,
                recipes=[]
            )

        t2_start = time.perf_counter()
        ai_result = scan_food_image(image_bytes)
        t2_end = time.perf_counter()
        print(f"AI ใช้เวลา: {t2_end - t2_start:.2f} วินาที")

        if not ai_result or "predictions" not in ai_result or "is_food" not in ai_result:
            print("AI ส่งข้อมูลกลับมาไม่ครบถ้วน")
            raise
            
        if ai_result["is_food"] == False:
            print("ไม่ใช่อาหาร by AI")
                # return None, ErrorCodeEnum.NOT_FOUND
            raise NotFoundException("รูปภาพนี้ไม่ใช่อาหาร กรุณาเลือกรูปภาพอาหาร")

        if not ai_result["predictions"]:
                # return None
            raise NotFoundException("รูปภาพนี้ไม่ใช่อาหาร กรุณาเลือกรูปภาพอาหาร")
        
        predicted_names = [recipe["name"] for recipe in ai_result["predictions"]]
        print(f"AI คาดเดาว่าเป็น: {predicted_names}")

        t_vec_start = time.perf_counter()
        uploaded_img_vector = get_image_vector(image_bytes)
        print(f"สกัด Image Vector ใช้เวลา: {time.perf_counter() - t_vec_start:.2f} วินาที")

        t3_start = time.perf_counter()
        recipe_result = recipeService.get_recipe_by_ai_recipe_name(
            user_id, prediction_result["class_name"], predicted_names, uploaded_img_vector, db
        )
        # recipe_result = recipeService.get_recipe_by_image_only(
        #     user_id, uploaded_img_vector, db
        # )
        t3_end = time.perf_counter()
        print(f"DB ใช้เวลา: {t3_end - t3_start:.2f} วินาที")

        print(f"Total ใช้เวลา: {time.perf_counter() - total_time:.2f} วินาที")

        return AnalyzeFoodResponseDTO(
            is_food=True,
            predicted_name=predicted_names,
            recipes=recipe_result
        )
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        raise
    
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
            }

        else:
            print("ไม่สามารถสร้างรูปและแปลงเป็น Base64 ได้!")
            print(f"Total ใช้เวลา: {time.perf_counter() - total_time:.2f} วินาที")
            raise

    except Exception as ex:
        print(f"error: {ex}")
        raise
    
def scan_ingredient_image(image_bytes: bytes):
    img = Image.open(io.BytesIO(image_bytes))

    response = client.models.generate_content(
        model=GOOGLE_ANALIZE_IMG_MODEL,
        contents=[img, "วิเคราะห์ภาพนี้ตามกฎที่กำหนดอย่างเคร่งครัด"],
        config=types.GenerateContentConfig(
            system_instruction="""
                คุณคือผู้เชี่ยวชาญด้านวัตถุดิบอาหาร

                **กฎเหล็กที่ต้องปฏิบัติตามอย่างเคร่งครัด:**
                1. หากภาพที่เห็นคือ "อาหารที่ปรุงสำเร็จแล้ว" (เช่น อาหารในจาน, แกงในชาม, ขนมที่ทำเสร็จแล้ว) ห้ามแกะส่วนผสมเด็ดขาด! ให้ตอบ has_ingredients = false และ ingredients = [] ทันที
                2. จะระบุชื่อวัตถุดิบได้ก็ต่อเมื่อ ภาพนั้นเป็น "วัตถุดิบสด" หรือของที่ยังไม่ประกอบร่างเป็นเมนูเท่านั้น
                3. ให้ระบุเฉพาะวัตถุดิบที่มองเห็นได้ชัดเจนในภาพเท่านั้น ห้ามคาดเดา
                4. ห้ามใส่ชื่อเมนูสำเร็จรูป
                5. ห้ามใส่คำซ้ำ
                6. ห้ามใส่หมวดหมู่กว้าง ๆ
                
                ตอบเป็น JSON ตาม schema เท่านั้น
                """,
            response_mime_type="application/json",
            response_schema=ingredient_schema,
        ),
    )
    return json.loads(response.text)
    
def analize_ingredient_image(user_id: int, image_bytes: bytes, db: Session):
    try:
        total_time = time.perf_counter()

        t1_start = time.perf_counter()
        ai_result = scan_ingredient_image(image_bytes)
        t1_end = time.perf_counter()
        print(f"AI ใช้เวลา: {t1_end - t1_start:.2f} วินาที")

        if not ai_result or "ingredients" not in ai_result or "has_ingredients" not in ai_result:
            print("AI ส่งข้อมูลกลับมาไม่ครบถ้วน")
            raise
            
        if ai_result["has_ingredients"] == False:
            print("ไม่มีวัตถุดิบ by AI")
            raise NotFoundException("ไม่พบรูปวัตถุดิบในภาพ กรุณาเลือกรูปภาพใหม่อีกครั้ง")

        if not ai_result["ingredients"]:
            raise NotFoundException("ไม่พบรูปวัตถุดิบในภาพ กรุณาเลือกรูปภาพใหม่อีกครั้ง")
            
        print(f"AI คาดเดาว่าเป็น: {ai_result['ingredients']}")

        t2_start = time.perf_counter()
        tags = db.exec(select(MasTagModel.tag_id, MasTagModel.tag_name).where(MasTagModel.tag_type == "method")).all()
        t2_end = time.perf_counter()
        print(f"DB Tag ใช้เวลา: {t2_end - t2_start:.2f} วินาที")

        t3_start = time.perf_counter()
        recipe_result = recipeService.get_recipe_by_ai_ingredient_name(user_id, ai_result["ingredients"], db)
        t3_end = time.perf_counter()
        print(f"DB Recipe ใช้เวลา: {t3_end - t3_start:.2f} วินาที")

        print(f"Total ใช้เวลา: {time.perf_counter() - total_time:.2f} วินาที")
        return ScanIngredientResponseDTO(
            ingredients=ai_result["ingredients"],
            tags= [{"tag_id": tag_id, "tag_name": tag_name} for tag_id, tag_name in tags],
            recipes=recipe_result
        )
    except Exception as ex:
        print(f"error: {ex}")
        raise

def generate_new_recipe_by_ai_process(user_id: int, recipe_name: str, prompt: str | None, db: Session):
    total_time = time.perf_counter()
    units = db.exec(select(UnitModel)).all()
    unit_options = ", ".join([f"{unit.unit_id}:{unit.unit_name}" for unit in units])

    tags = db.exec(select(MasTagModel)).all()
    tag_options = ", ".join([f"{tag.tag_id}:{tag.tag_name}" for tag in tags])

    system_instruction = f"""คุณคือเชฟระดับโลก หน้าที่ของคุณคือสร้างสูตรอาหาร 1 สูตร
    โดยหน่วยตวง (unit_id) ที่อนุญาตให้ใช้คือ: {unit_options}
    รหัสแท็กหมวดหมู่ (tag_id) ที่อนุญาตให้ใช้: {tag_options}
    (เลือก unit_id และ tag_id ที่เหมาะสมที่สุด)"""
    
    user_prompt = f"ขอสูตรอาหารสำหรับเมนู '{recipe_name}' เงื่อนไขเพิ่มเติม: '{prompt if prompt else 'ไม่มี'}'"
    print("⏳ กำลังให้ AI คิดสูตรอาหาร...")
    t1_start = time.perf_counter()
    try:
        response = client.models.generate_content(
            model=GOOGLE_GEN_CONTENT_MODEL,
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=recipe_list_schema, # 🟢 บังคับโครงสร้างแบบ 100%
                temperature=0.7,
            ),
        )
        
        response_dict = json.loads(response.text)
        recipes_data = response_dict.get("recipes", [])
        t1_end = time.perf_counter()
        print(f"AI ใช้เวลา: {t1_end - t1_start:.2f} วินาที")
        
    except Exception as ex:
        print(f"❌ Error calling Gemini API: {ex}")
        raise Exception("AI ประมวลผลผิดพลาด กรุณาลองใหม่อีกครั้ง")
    
    generated_recipes = []

    try:
        for data in recipes_data:
            new_recipe = TrnRecipeModel(
                user_id=user_id,
                recipe_name=data["recipe_name"],
                description=data["description"],
                cooking_time_min=data.get("cooking_time_min", 0),
                is_created_by_ai=True,
                is_public=False,
                is_active=False,

            )
            db.add(new_recipe)
            db.flush()

            # 3.2 บันทึก Ingredients
            for ing in data.get("ingredients", []):
                ing_name = ing["ingredient_name"]
                
                # เช็คว่ามีวัตถุดิบนี้หรือยัง
                db_ingredient = db.exec(
                    select(MasIngredientModel).where(MasIngredientModel.ingredient_name == ing_name)
                ).first()
                
                if db_ingredient:
                    final_ingredient_id = db_ingredient.ingredient_id
                else:
                    new_mst_ing = MasIngredientModel(
                        ingredient_name=ing_name,
                        ingredient_group=ing.get("ingredient_group"), 
                        pantry_days=ing.get("pantry_days"),
                        fridge_days=ing.get("fridge_days"),
                        freezer_days=ing.get("freezer_days")
                    )
                    db.add(new_mst_ing)
                    db.flush() 
                    final_ingredient_id = new_mst_ing.ingredient_id

                new_ing = DtlRecipeIngredientModel(
                    recipe_id=new_recipe.recipe_id,
                    ingredient_id=final_ingredient_id,
                    quantity=ing["quantity"],
                    unit_id=ing["unit_id"],
                    is_main_ingredient=ing.get("is_main_ingredient", False)
                )
                db.add(new_ing)

            # 3.3 บันทึก Steps
            for step in data.get("steps", []):
                new_step = DtlRecipeStepModel(
                    recipe_id=new_recipe.recipe_id,
                    step_no=step["step_no"],
                    instruction=step["instruction"]
                )
                db.add(new_step)

            for tag_id in data.get("tags", []):
                new_map_tag = MapRecipeTagModel(
                    recipe_id=new_recipe.recipe_id,
                    tag_id=tag_id
                )
                db.add(new_map_tag)

            generated_recipes.append(new_recipe)

        db.commit()

    except Exception as ex:
        db.rollback()
        raise ex
    
    # created_recipe_ids = [r.recipe_id for r in generated_recipes]
    # complete_recipes = db.exec(
    #     select(TrnRecipeModel).where(TrnRecipeModel.recipe_id.in_(created_recipe_ids))
    # ).all()

    print("✅ AI ประมวลผลสูตรอาหารเรียบร้อยแล้ว")
    print(f"เวลาที่ใช้ทั้งหมด: {time.perf_counter() - total_time:.2f} วินาที")
    return True