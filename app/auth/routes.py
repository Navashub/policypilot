import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.schemas import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyOut,
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserOut,
)
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models import ApiKey, Org, User, UserRole
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with that email already exists.")

    org = Org(name=payload.org_name)
    db.add(org)
    db.flush()  # get org.id before creating the user

    user = User(
        org_id=org.id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=UserRole.owner,  # first user in a new org is always the owner
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user.id, org.id),
        refresh_token=create_refresh_token(user.id, org.id),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated.")

    return TokenResponse(
        access_token=create_access_token(user.id, user.org_id),
        refresh_token=create_refresh_token(user.id, user.org_id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

    user = db.get(User, data.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive.")

    return TokenResponse(
        access_token=create_access_token(user.id, user.org_id),
        refresh_token=create_refresh_token(user.id, user.org_id),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# --- API keys (for programmatic / integration access) ---

def _generate_api_key() -> tuple[str, str, str]:
    """Returns (full_key, key_hash, key_prefix). Only the hash is stored."""
    full_key = f"pp_live_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:12]
    return full_key, key_hash, key_prefix


@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    full_key, key_hash, key_prefix = _generate_api_key()
    api_key = ApiKey(org_id=current_user.org_id, name=payload.name, key_hash=key_hash, key_prefix=key_prefix)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return ApiKeyCreateResponse(id=api_key.id, name=api_key.name, key=full_key, key_prefix=key_prefix)


@router.get("/api-keys", response_model=list[ApiKeyOut])
def list_api_keys(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(ApiKey).filter(ApiKey.org_id == current_user.org_id).all()


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(key_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.org_id == current_user.org_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found.")
    api_key.revoked = True
    db.commit()
