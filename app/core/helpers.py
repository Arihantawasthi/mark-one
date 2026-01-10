import jwt
import datetime
from passlib.context import CryptContext
from app.core.settings import SECRET_KEY, TOKEN_EXPIRATION_DAYS
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class TokenException(Exception):
    pass


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


def verify_token(req: Request) -> dict:
    token = req.headers.get("Authorization")
    if not token:
        logger.error(
            "Authorization Failed! Token is missing",
            extra={"error": "Token is missing"},
            exc_info=True
        )
        return {}
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload

    except jwt.ExpiredSignatureError:
        logger.error(
            "Authorization Failed! Token is expired",
            extra={"error": "Token is expired"},
            exc_info=True
        )
        return {}

    except jwt.InvalidTokenError:
        logger.error(
            "Authorization Failed! Invalid Token",
            extra={"error": "Invalid token"},
            exc_info=True
        )
        return {}
