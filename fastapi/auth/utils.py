from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def check_password(password: str, hashed_password: str) -> bool:
    if not bcrypt_context.verify(password, hashed_password):
        return False
    return True


def hash_password(password: str) -> str:
    return bcrypt_context.hash(password)
