import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import AuthSessionRecord, UserRecord, UserRole

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


class AuthenticationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    token: str
    user: UserRecord
    expires_at: datetime


def hash_password(password: str) -> str:
    if len(password) < 10:
        raise AuthenticationError("password must contain at least 10 characters")
    salt = secrets.token_bytes(16)
    digest = _scrypt(password, salt)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$")
        if algorithm != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=64,
        )
        return hmac.compare_digest(digest, bytes.fromhex(expected))
    except (TypeError, ValueError):
        return False


def create_user(
    session: Session,
    *,
    username: str,
    password: str,
    role: UserRole,
) -> UserRecord:
    normalized = username.strip().lower()
    if not normalized:
        raise AuthenticationError("username is required")
    if session.scalar(select(UserRecord.id).where(UserRecord.username == normalized)):
        raise AuthenticationError("username already exists")
    user = UserRecord(
        username=normalized,
        password_hash=hash_password(password),
        role=role,
        created_at=datetime.now(UTC),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def login(session: Session, *, username: str, password: str) -> AuthenticatedSession:
    normalized = username.strip().lower()
    user = session.scalar(select(UserRecord).where(UserRecord.username == normalized))
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("invalid username or password")
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    expires_at = now + timedelta(hours=settings.session_lifetime_hours)
    session.add(
        AuthSessionRecord(
            token_hash=token_hash(token),
            user_id=user.id,
            created_at=now,
            expires_at=expires_at,
        )
    )
    session.commit()
    return AuthenticatedSession(token=token, user=user, expires_at=expires_at)


def user_for_token(session: Session, token: str) -> UserRecord | None:
    auth_session = session.get(AuthSessionRecord, token_hash(token))
    if auth_session is None:
        return None
    expires_at = auth_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        session.delete(auth_session)
        session.commit()
        return None
    return session.get(UserRecord, auth_session.user_id)


def logout(session: Session, token: str) -> None:
    auth_session = session.get(AuthSessionRecord, token_hash(token))
    if auth_session is not None:
        session.delete(auth_session)
        session.commit()


def change_password(
    session: Session,
    *,
    user_id: str,
    current_password: str,
    new_password: str,
) -> None:
    user = session.get(UserRecord, user_id)
    if user is None or not verify_password(current_password, user.password_hash):
        raise AuthenticationError("current password is incorrect")
    user.password_hash = hash_password(new_password)
    session.query(AuthSessionRecord).filter(AuthSessionRecord.user_id == user.id).delete()
    session.commit()


def _scrypt(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=64
    )


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
