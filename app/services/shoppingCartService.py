from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.core import datetimezone
from app.models.shoppingCartModel import ShoppingListModel, ShoppingItemModel
from app.models.recipeModel import TrnRecipeModel
from app.schemas.shoppingCartDTO import (
    CreateNewShoppingListDTO, AddShoppingItemToShoppingListDTO, UpdateShoppingItemStatusDTO, UpdateShoppingItemQuantityDTO,
    UpdateShoppingItemUnitDTO
)

def create_new_shopping_list(db:Session, request_body: CreateNewShoppingListDTO, user_id: int | None, guest_token: UUID | None = None):
    try:
        new_shopping_list = ShoppingListModel(
            user_id = user_id, 
            guest_token = guest_token,
            shopping_type = request_body.shopping_type,
            list_name = request_body.list_name,
            status = "pending",
        )
        db.add(new_shopping_list)
        db.flush()

        if request_body.items: 
            items = [
                ShoppingItemModel(
                    shopping_list_id = new_shopping_list.shopping_list_id,
                    item_name = item.item_name,
                    quantity = item.quantity,
                    unit_id = item.unit_id,
                    note = item.note
                )
                for item in request_body.items
            ]
            db.add_all(items)

        db.commit()
        db.refresh(new_shopping_list)
        
        return new_shopping_list, None
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, str(ex)

def add_item_to_shopping_list(db:Session, request_body: AddShoppingItemToShoppingListDTO, user_id: int | None = None, guest_token: UUID | None = None):
    try:
        shopping_list = db.get(ShoppingListModel, request_body.shopping_list_id)
        if not shopping_list:
            print(f"Error: Shopping list ID {request_body.shopping_list_id} not found.")
            return False, "ไม่พบรายการสั่งซื้อที่ต้องการ"
        
        if shopping_list.user_id != user_id or guest_token != shopping_list.guest_token:
            return None, "คุณไม่มีสิทธิ์เพิ่มรายการในตะกร้านี้"
        
        new_item = ShoppingItemModel(**request_body.model_dump())
        db.add(new_item)
        db.commit()
        return "success", None
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, "เกิดข้อผิดพลาดในการเพิ่มรายการสั่งซื้อ"
    
# def add_item_to_shopping_list_by_recipe_id(db:Session, recipe_id: int, user_id: int | None = None, guest_token: UUID | None = None):
#     try:
#         recipe = db.get(TrnRecipeModel, recipe_id)
#         if not recipe:
#             print(f"Error: Recipe ID {recipe_id} not found.")
#             return False, "ไม่พบรายการอาหารที่ต้องการ"
        
#         new_shopping_list = 
        

#     except Exception as ex:
#         db.rollback()
#         print(f"error: {ex}")
#         return None
    
def update_shopping_item_status_by_shopping_item_id(db: Session, shopping_item_id: int, request_body: UpdateShoppingItemStatusDTO, user_id: int | None, guest_token: UUID | None = None):
    try:
        item = db.get(ShoppingItemModel, shopping_item_id)
        if not item:
            print(f"Error: Shopping item ID {shopping_item_id} not found.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการแก้ไข"
        
        if item.shopping_list.user_id != user_id or guest_token != item.shopping_list.guest_token:
            print(f"Error: Not authorized to update shopping item.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการแก้ไข"
        
        item.is_check = request_body.is_check
        item.update_date = datetimezone.get_thai_now()
        
        db.commit()
        db.refresh(item)
        return item, None
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        return None, "เกิดข้อผิดพลาดในการแก้ไขรายการสั่งซื้อ"
    
def update_shopping_item_quantity_by_item_id(db: Session, item_id: int, request_body: UpdateShoppingItemQuantityDTO, user_id: int | None = None, guest_token: UUID | None = None):
    try:
        item = db.get(ShoppingItemModel, item_id)
        if not item:
            print(f"Error: Shopping item ID {item_id} not found.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการแก้ไข"
        
        if item.shopping_list.user_id != user_id or guest_token != item.shopping_list.guest_token:
            print(f"Error: Not authorized to update shopping item.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการแก้ไข"
        
        item.quantity = request_body.quantity
        item.update_date = datetimezone.get_thai_now()
        
        db.commit()
        db.refresh(item)
        return item, None
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, "เกิดข้อผิดพลาดในการแก้ไขจํานวน"

def update_shopping_item_unit_by_item_id(db: Session, item_id: int, request_body: UpdateShoppingItemUnitDTO, user_id: int | None = None, guest_token: UUID | None = None):
    try:
        item = db.get(ShoppingItemModel, item_id)
        if not item:
            print(f"Error: Shopping item ID {item_id} not found.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการแก้ไข"
        
        if item.shopping_list.user_id != user_id or guest_token != item.shopping_list.guest_token:
            print(f"Error: Not authorized to update shopping item.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการแก้ไข"
        
        item.unit_id = request_body.unit_id
        item.update_date = datetimezone.get_thai_now()
        
        db.commit()
        db.refresh(item)
        return item, None
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, "เกิดข้อผิดพลาดในการแก้ไขหน่วย"
    
def delete_shopping_list_by_shopping_list_id(db: Session, list_id: int, user_id: int | None = None, guest_token: UUID | None = None):
    try:
        list = db.get(ShoppingListModel, list_id)
        if not list:
            print(f"Error: Shopping list ID {list_id} not found.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการลบ"
        
        if list.user_id != user_id or guest_token != list.guest_token:
            print(f"Error: Not authorized to delete shopping list.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการลบ"
        
        db.delete(list)
        db.commit()
        return True, None
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, "เกิดข้อผิดพลาดในการลบรายการสั่งซื้อ"
    
def delete_shopping_item_by_item_id(db: Session, item_id: int, user_id: int | None = None, guest_token: UUID | None = None):
    try:
        item = db.get(ShoppingItemModel, item_id)
        if not item:
            print(f"Error: Shopping item ID {item_id} not found.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการลบ"
        
        if item.shopping_list.user_id != user_id or guest_token != item.shopping_list.guest_token:
            print(f"Error: Not authorized to delete shopping item.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการลบ"
        
        db.delete(item)
        db.commit()
        return True, None
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, "เกิดข้อผิดพลาดในการลบรายการสั่งซื้อ"
    
def get_shopping_list_by_user_id_or_guest_token(db:Session, shopping_type: str, user_id: int | None = None, guest_token: UUID | None = None):
    if user_id:
        sql = select(ShoppingListModel).where(ShoppingListModel.user_id == user_id, ShoppingListModel.shopping_type == shopping_type)

    elif guest_token:
        sql = select(ShoppingListModel).where(ShoppingListModel.guest_token == guest_token, ShoppingListModel.shopping_type == shopping_type)

    else:
        raise ValueError("ต้องมี user_id หรือ guest_token")

    sql = sql.options(
        selectinload(ShoppingListModel.items).options(
            selectinload(ShoppingItemModel.unit)
        )
    )
    result = db.exec(sql).all()
    return result