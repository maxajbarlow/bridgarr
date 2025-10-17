"""
Authentication API Endpoints
User registration, login, and Real-Debrid token management
"""

from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User, DebridProvider
from app.services.debrid import get_debrid_client

# Router setup
router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Pydantic schemas
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    has_rd_token: bool  # Legacy field for backwards compatibility
    has_debrid_token: bool = False
    debrid_provider: str = "real-debrid"
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class RDTokenRequest(BaseModel):
    rd_api_token: str  # Legacy field


class DebridTokenRequest(BaseModel):
    provider: DebridProvider
    api_token: str


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


# API Endpoints
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user

    - Creates user account with hashed password
    - Returns user info (password not included)
    """
    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Add computed properties
    new_user.has_rd_token = new_user.rd_api_token is not None or new_user.debrid_api_token is not None
    new_user.has_debrid_token = new_user.debrid_api_token is not None

    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """
    Login with username and password

    - Returns JWT access token
    - Token expires based on ACCESS_TOKEN_EXPIRE_MINUTES setting
    """
    # Find user
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Create access token
    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information

    - Requires valid JWT token
    - Returns user details
    """
    # Add computed properties
    current_user.has_rd_token = current_user.rd_api_token is not None or current_user.debrid_api_token is not None
    current_user.has_debrid_token = current_user.debrid_api_token is not None
    return current_user


@router.post("/rd-token", response_model=UserResponse)
async def store_rd_token(
    rd_token_data: RDTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Store Real-Debrid API token for user

    - Updates user's RD token
    - Sets expiration to 90 days from now
    - Returns updated user info
    """
    # Update user's RD token
    current_user.rd_api_token = rd_token_data.rd_api_token
    current_user.rd_token_expires_at = datetime.utcnow() + timedelta(days=90)

    db.commit()
    db.refresh(current_user)

    # Add computed properties
    current_user.has_rd_token = current_user.rd_api_token is not None or current_user.debrid_api_token is not None
    current_user.has_debrid_token = current_user.debrid_api_token is not None

    return current_user


@router.post("/debrid-token", response_model=UserResponse)
async def store_debrid_token(
    token_data: DebridTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Store debrid service API token for user

    - Updates user's debrid provider and token
    - Validates token with provider API
    - Sets expiration to 90 days from now
    - Returns updated user info
    """
    # Validate token with provider
    try:
        debrid_client = get_debrid_client(token_data.provider, token_data.api_token)
        if not debrid_client.validate_token():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {token_data.provider} API token"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to validate token: {str(e)}"
        )

    # Update user's debrid configuration
    current_user.debrid_provider = token_data.provider
    current_user.debrid_api_token = token_data.api_token
    current_user.debrid_token_expires_at = datetime.utcnow() + timedelta(days=90)

    # Also update legacy rd_api_token if provider is Real-Debrid
    if token_data.provider == DebridProvider.REAL_DEBRID:
        current_user.rd_api_token = token_data.api_token
        current_user.rd_token_expires_at = current_user.debrid_token_expires_at

    db.commit()
    db.refresh(current_user)

    # Add computed properties
    current_user.has_rd_token = current_user.rd_api_token is not None or current_user.debrid_api_token is not None
    current_user.has_debrid_token = current_user.debrid_api_token is not None

    return current_user


@router.get("/debrid-token/test")
async def test_debrid_token(current_user: User = Depends(get_current_user)):
    """
    Test if debrid service token is valid

    - Checks if user has debrid token configured
    - Validates token with provider API
    - Returns validation status and provider info
    """
    if not current_user.debrid_api_token:
        # Check legacy RD token
        if current_user.rd_api_token:
            return {
                "valid": True,
                "provider": "real-debrid",
                "message": "Using legacy Real-Debrid token",
                "username": current_user.username
            }
        return {
            "valid": False,
            "message": "No debrid service token configured"
        }

    # Validate with provider API
    try:
        debrid_client = get_debrid_client(current_user.debrid_provider, current_user.debrid_api_token)
        is_valid = debrid_client.validate_token()

        if is_valid:
            user_info = debrid_client.get_user_info()
            return {
                "valid": True,
                "provider": current_user.debrid_provider.value,
                "message": f"{current_user.debrid_provider.value} token is valid",
                "username": current_user.username,
                "provider_username": user_info.get("username") or user_info.get("email")
            }
        else:
            return {
                "valid": False,
                "provider": current_user.debrid_provider.value,
                "message": f"{current_user.debrid_provider.value} token is invalid or expired"
            }
    except Exception as e:
        return {
            "valid": False,
            "provider": current_user.debrid_provider.value if current_user.debrid_provider else "unknown",
            "message": f"Failed to validate token: {str(e)}"
        }


@router.delete("/debrid-token", status_code=status.HTTP_204_NO_CONTENT)
async def remove_debrid_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove debrid service API token from user account

    - Clears debrid token and expiration
    - Also clears legacy RD token
    - Returns 204 No Content
    """
    current_user.debrid_api_token = None
    current_user.debrid_token_expires_at = None
    current_user.rd_api_token = None
    current_user.rd_token_expires_at = None

    db.commit()

    return None


@router.get("/rd-token/test")
async def test_rd_token(current_user: User = Depends(get_current_user)):
    """
    Test if Real-Debrid token is valid

    - Checks if user has RD token configured
    - Returns validation status
    """
    if not current_user.rd_api_token:
        return {"valid": False, "message": "No Real-Debrid token configured"}

    # For now, just check if token exists
    # In future, could make actual API call to Real-Debrid to validate
    return {
        "valid": True,
        "message": "Real-Debrid token is configured",
        "username": current_user.username
    }


@router.delete("/rd-token", status_code=status.HTTP_204_NO_CONTENT)
async def remove_rd_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove Real-Debrid API token from user account

    - Clears RD token and expiration
    - Returns 204 No Content
    """
    current_user.rd_api_token = None
    current_user.rd_token_expires_at = None

    db.commit()

    return None
