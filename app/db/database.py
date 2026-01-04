from sqlmodel import create_engine, Session
from app.core.config import DBURL

engine = create_engine(DBURL, echo=True)

def get_db():
    with Session(engine) as db:
        yield db