from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str
    picture: Optional[str] = None

class UserCreate(UserBase):
    google_id: str

class UserDB(UserBase):
    id: str
    google_id: str
    created_at: datetime
    updated_at: datetime
    subscription_tier: str = "free"   # free | pro_50 | pro_100 | pro_200 | pro_400 | pro_500
    credits_used: int = 0
    credits_limit: int = 3            # free = 3/month; pro tiers set by payments webhook
    is_active: bool = True

class UserPublic(UserBase):
    id: str
    subscription_tier: str
    credits_used: int
    credits_limit: int
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic
