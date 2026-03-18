from app.models.recipeModel import TrnRecipeModel

def build_recipe_document(recipe: TrnRecipeModel):
    title = recipe.recipe_name

    method_tags = []

    # 2. วนลูปเช็ค Tag ทุกตัวที่ผูกกับเมนูนี้
    if recipe.recipe_tags:
        for map_tag in recipe.recipe_tags:
            # สมมติว่าตาราง Tag ของคุณมี Column ชื่อ tag_type (หรือ category)
            # ให้เช็คว่ามันคือกลุ่ม "วิธีทำ" หรือไม่ 
            # 🚨 (แก้ "method" ให้ตรงกับค่าที่บันทึกใน DB ของคุณ เช่น "METHOD", "cooking_method")
            if map_tag.tag and map_tag.tag.tag_type == "method": 
                method_tags.append(map_tag.tag.tag_name)

    # 3. เอาเฉพาะ Tag ที่เป็น Method มาต่อกัน
    method_str = " ".join(method_tags)
    

    # tags = " ".join(recipe.tags) if recipe.tags else ""
    # tag_type = recipe.tags_type if recipe.tags_type else ""

    return f"{title} {method_str}".strip()
