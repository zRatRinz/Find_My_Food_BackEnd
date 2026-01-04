from pwdlib import PasswordHash
import jwt
from datetime import datetime, timedelta, timezone

from app.core.config import SECRET_KEY, ALGORITHM

password_hash = PasswordHash.recommended()

def create_hash_password(plain_password:str):
    return password_hash.hash(plain_password)

def verify_password(plain_password:str, password:str):
    return password_hash.verify(plain_password,password)

def create_access_token(data:dict, expires_delta: timedelta | None = None):
    prepare_encode_data = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    prepare_encode_data.update({"exp":expire})
    encoded_jwt = jwt.encode(prepare_encode_data, SECRET_KEY, ALGORITHM)
    return encoded_jwt
