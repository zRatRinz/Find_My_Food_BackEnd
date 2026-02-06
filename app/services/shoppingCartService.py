from sqlmodel import Session, select
from sqlalchemy.orm import selectinload, joinedload
from uuid import UUID
from collections import defaultdict
from app.core import datetimezone
from app.models.shoppingCartModel import ShoppingListModel, ShoppingItemModel
from app.models.recipeModel import TrnRecipeModel
from app.models.userStockModel import TrnUserStockModel
from app.schemas.shoppingCartDTO import (
    CreateNewShoppingListDTO, AddShoppingItemToShoppingListDTO, UpdateShoppingItemStatusDTO, UpdateShoppingItemQuantityDTO,
    UpdateShoppingItemUnitDTO, ShoppingPreviewDTO, AddRecipeIngredientToShoppingListDTO
)
from app.schemas.userStockDTO import StockInfoDTO
from app.enums.types import ShoppingTypeEnum
from app.enums.errorCodeEnum import ErrorCodeEnum

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
    
def add_item_to_shopping_list_by_recipe_id(db:Session, request_body: AddRecipeIngredientToShoppingListDTO, user_id: int | None = None, guest_token: UUID | None = None):
    try:
        recipe = db.get(TrnRecipeModel, request_body.recipe_id)
        if not recipe:
            print(f"Error: Recipe ID {request_body.recipe_id} not found.")
            return False, ErrorCodeEnum.NOT_FOUND

        existing_shopping_list_sql = select(ShoppingListModel).where(ShoppingListModel.list_name == recipe.recipe_name)
        if user_id:
            existing_shopping_list_sql = existing_shopping_list_sql.where(ShoppingListModel.user_id == user_id)
        elif guest_token:
            existing_shopping_list_sql = existing_shopping_list_sql.where(ShoppingListModel.guest_token == guest_token)

        existing_shopping_list = db.exec(existing_shopping_list_sql).first()
        shopping_list = None
        if existing_shopping_list:
            shopping_list = existing_shopping_list
            shopping_list.update_date = datetimezone.get_thai_now()
        else:
            shopping_list = ShoppingListModel(
                user_id = user_id,
                guest_token = guest_token,
                shopping_type = ShoppingTypeEnum.RECIPE,
                list_name = recipe.recipe_name,
                status = "pending",
            )
            db.add(shopping_list)
            db.flush()
            db.refresh(shopping_list)

        if request_body.items: 
            current_items = db.exec(select(ShoppingItemModel).where(
                ShoppingItemModel.shopping_list_id == shopping_list.shopping_list_id
            )).all()

            existing_item_map = {
                item.ingredient_id: item
                for item in current_items
                if item.ingredient_id is not None
            }
            request_ingredient_id = { item.ingredient_id for item in request_body.items}
            for exsiting_ingredient_id, existing_item_obj in existing_item_map.items():
                if exsiting_ingredient_id not in request_ingredient_id:
                    db.delete(existing_item_obj)

            new_items_to_add = []
            for new_item in request_body.items:
                item_key_id = new_item.ingredient_id
                if item_key_id in existing_item_map:
                    existing_item = existing_item_map[item_key_id]
                    existing_item.item_name = new_item.item_name
                    existing_item.quantity = new_item.quantity
                    existing_item.unit_id = new_item.unit_id
                    existing_item.is_check = False
                    existing_item.update_date = datetimezone.get_thai_now()

                    db.add(existing_item)
                else:
                    new_item_obj = ShoppingItemModel(
                        shopping_list_id = shopping_list.shopping_list_id,
                        item_name = new_item.item_name,
                        ingredient_id = new_item.ingredient_id,
                        quantity = new_item.quantity,
                        unit_id = new_item.unit_id,
                        is_check = False
                    )
                    new_items_to_add.append(new_item_obj)

            if new_items_to_add:
                db.add_all(new_items_to_add)

        db.commit()
        db.refresh(shopping_list)
        return shopping_list, None
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, ErrorCodeEnum.INTERNAL_ERROR
    
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

def get_shopping_ingredient_preview(db: Session, recipe_id: int, user_id: int | None = None, guest_token: UUID | None = None):
    try:
        recipe = db.get(TrnRecipeModel, recipe_id)
        if not recipe:
            print(f"Error: Recipe ID {recipe_id} not found.")
            return None, ErrorCodeEnum.NOT_FOUND

        ingredients = recipe.ingredients
        stock_group = defaultdict(list)
        if user_id:
            recipe_ingredients = [ingredient.ingredient_id for ingredient in ingredients]
            user_stock = db.exec(select(TrnUserStockModel).where(
                TrnUserStockModel.user_id == user_id,
                TrnUserStockModel.ingredient_id.in_(recipe_ingredients)
            ).options(
                joinedload(TrnUserStockModel.unit)
            )).all()

            for stock in user_stock:
                stock_group[stock.ingredient_id].append(stock)

        preview_list = []
        for ingredient in ingredients:
            # related_stocks = stock_group.get(ingredient.ingredient_id, [])
            related_stocks: list[TrnUserStockModel] = stock_group.get(ingredient.ingredient_id, [])
            select_stock_dto = None
            if related_stocks:
                related_stocks.sort(key=lambda x: (
                    x.expire_date is None,
                    x.expire_date,
                    x.create_date
                ))

                best_stock = related_stocks[0]
                # stock_unit_name = best_stock.unit.unit_name if best_stock.unit else "หน่วย"
                select_stock_dto =  StockInfoDTO(
                    # item_name = best_stock.item_name,
                    quantity = best_stock.quantity,
                    unit_name = best_stock.unit.unit_name
                )
            # recipe_unit_name = ingredient.unit.unit_name if ingredient.unit else "หน่วย"
            response_dto = ShoppingPreviewDTO(
                ingredient_id = ingredient.ingredient_id,
                item_name = ingredient.ingredient_name,
                recipe_quantity = ingredient.quantity,
                recipe_unit_name = ingredient.unit_name,
                user_stock = select_stock_dto
            )
            preview_list.append(response_dto)

        return preview_list, None

    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, ErrorCodeEnum.INTERNAL_ERROR