from enum import Enum

class ShoppingTypeEnum(str, Enum):
    RECIPE = "recipe"
    MARKET = "market"

class StorageTypeEnum(str, Enum):
    PANTRY = "pantry"
    FRIDGE = "fridge"
    FREEZER = "freezer"