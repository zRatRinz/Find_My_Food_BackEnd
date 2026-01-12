from sqlmodel import Session, select
from app.models.unitModel import UnitModel

def get_all_unit(db: Session):
    sql = select(UnitModel)
    result = db.exec(sql).all()
    return result
        