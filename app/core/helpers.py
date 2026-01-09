import jwt
import datetime
from passlib.context import CryptContext
from app.core.settings import SECRET_KEY, TOKEN_EXPIRATION_DAYS

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)

def generate_access_token(client: dict) -> str:
    secret_key = SECRET_KEY
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=TOKEN_EXPIRATION_DAYS)
    to_encode = {
        "sub": client["username"],
        "sub_id": client["id"],
        "exp": expiration
    }
    token = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return token
