from PIL import Image
import numpy as np
import tensorflow as tf
import io
from app.ai.class_map import CLASS_MAP

model = tf.keras.models.load_model("app/ai/MNV2_Project.keras") 

def predict_food_image(image_bytes: bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize((224, 224))
        image_array = np.array(image).astype("float32")
        image_batch = np.expand_dims(image_array, axis=0)
        predictions = model.predict(image_batch)
        scores = predictions[0]

        # class_index = int(np.argmax(scores))
        # confidence = float(scores[class_index])
        # return {
        #     "class_index": class_index,
        #     "class_name": CLASS_MAP.get(class_index, "Unknown"),
        #     "confidence": round(confidence, 4)
        # }

        top_indices = scores.argsort()[::-1][:3]

        top_3 = [
            {
                "class_name": CLASS_MAP.get(i, "Unknown"),
                "confidence": round(float(scores[i]), 4)
            }
            for i in top_indices
        ]

        return {
            "top_3": top_3
        }

    except Exception as ex:
        raise Exception(f"Error: {str(ex)}")