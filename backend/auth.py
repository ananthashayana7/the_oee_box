from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from backend.models import TokenData, User, UserInDB
from backend.database import db_manager
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkeywhichshouldbechanged")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Key Management (Mock for Demo)
# In real app, keys generated on client device or secure enclave
KEY_FILE = "admin_key.pem"

if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as f:
        admin_private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )
else:
    admin_private_key = ec.generate_private_key(ec.SECP256R1())
    with open(KEY_FILE, "wb") as f:
        f.write(admin_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

admin_public_key = admin_private_key.public_key()

def get_admin_public_key_pem():
    return admin_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

async def get_user(username: str):
    if not db_manager.db: return None
    try:
        async with db_manager.db.execute("SELECT username, password_hash, role FROM users WHERE username = ?", (username,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return UserInDB(username=row[0], hashed_password=row[1], role=row[2])
    except Exception as e:
        print(f"Auth DB Error: {e}")
    return None

async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

async def get_authorized_user(current_user: Annotated[User, Depends(get_current_active_user)], required_roles: list[str] = ["engineer", "admin"]):
    if current_user.role not in required_roles:
        raise HTTPException(status_code=403, detail=f"Insufficient permissions. Role '{current_user.role}' required.")
    return current_user
