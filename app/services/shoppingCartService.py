from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.core import datetimezone
from app.models.shoppingCartModel import ShoppingListModel, ShoppingItemModel
from app.schemas.shoppingCartDTO import (
    CreateNewShoppingListDTO, AddShoppingItemToShoppingListDTO, UpdateShoppingItemStatusDTO, UpdateShoppingItemQuantityDTO,
    UpdateShoppingItemUnitDTO
)


def create_new_shopping_list(db:Session, request: CreateNewShoppingListDTO, user_id: int):
    try:
        new_shopping_list = ShoppingListModel(
            user_id = user_id, 
            list_name = request.list_name,
            status = "pending",
        )
        db.add(new_shopping_list)
        db.flush()

        if not request.items:
            return (None, "กรุณาเพิ่มรายการสินค้า")
        
        items = [
            ShoppingItemModel(
                shopping_list_id = new_shopping_list.shopping_list_id,
                item_name = item.item_name,
                quantity = item.quantity,
                unit_id = item.unit_id,
                note = item.note
            )
            for item in request.items
        ]
        db.add_all(items)
        # create_new_shopping_item(db, request.items, new_shopping_list.shopping_list_id)
        db.commit()
        return "success"
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None

def add_item_to_shopping_list(db:Session, user_id: int, request_body: AddShoppingItemToShoppingListDTO):
    try:
        shopping_list = db.get(ShoppingListModel, request_body.shopping_list_id)
        if not shopping_list:
            print(f"Error: Shopping list ID {request_body.shopping_list_id} not found.")
            return False, "ไม่พบรายการสั่งซื้อที่ต้องการ"
        
        if shopping_list.user_id != user_id:
            return None, "คุณไม่มีสิทธิ์เพิ่มรายการในตะกร้านี้"
        
        new_item = ShoppingItemModel(**request_body.model_dump())
        db.add(new_item)
        db.commit()
        return "success", None
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, "เกิดข้อผิดพลาดในการเพิ่มรายการสั่งซื้อ"
    
def update_shopping_item_status_by_shopping_item_id(db: Session, user_id: int, shopping_item_id: int, request_body: UpdateShoppingItemStatusDTO):
    try:
        item = db.get(ShoppingItemModel, shopping_item_id)
        if not item:
            print(f"Error: Shopping item ID {shopping_item_id} not found.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการแก้ไข"
        
        if item.shopping_list.user_id != user_id:
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
    
def update_shopping_item_quantity_by_item_id(db: Session, user_id: int, item_id: int, request_body: UpdateShoppingItemQuantityDTO):
    try:
        item = db.get(ShoppingItemModel, item_id)
        if not item:
            print(f"Error: Shopping item ID {item_id} not found.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการแก้ไข"
        
        if item.shopping_list.user_id != user_id:
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

def update_shopping_item_unit_by_item_id(db: Session, user_id: int, item_id: int, request_body: UpdateShoppingItemUnitDTO):
    try:
        item = db.get(ShoppingItemModel, item_id)
        if not item:
            print(f"Error: Shopping item ID {item_id} not found.")
            return None, "ไม่พบรายการสั่งซื้อที่ต้องการแก้ไข"
        
        if item.shopping_list.user_id != user_id:
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
    
def get_shopping_list_by_user_id(db:Session, user_id: int):
    sql = select(ShoppingListModel).where(ShoppingListModel.user_id == user_id).options(
            selectinload(ShoppingListModel.items).options(
                selectinload(ShoppingItemModel.unit)
            )
        )
    result = db.exec(sql).all()
    return result