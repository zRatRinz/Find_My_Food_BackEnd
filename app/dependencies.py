from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from sqlmodel import Session
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import SECRET_KEY, ALGORITHM
from app.db import database
from app.schemas.userDTO import TokenData
from app.services import userService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

async def get_current_user(token:Annotated[str, Depends(oauth2_scheme)], db:Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "ไม่มีสิทธิ์เข้าใช้งาน",
        headers = {"WWW-Authenticate": "Bearer"}
    )

    try:
        print(f"DEBUG TOKEN: >>>{token}<<<")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            print("123")
            raise credentials_exception
        
        token_data = TokenData(user_id=int(user_id))
    except Exception as ex:
        print(str(ex))
        raise credentials_exception
    
    try:
        user = userService.get_user_by_user_id(token_data.user_id, db)
        if user is None:
            raise credentials_exception
        return user
    except Exception as ex:
        print(str(ex))