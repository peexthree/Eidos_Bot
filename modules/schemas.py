from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any

class User(BaseModel):
    uid: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    path: str = "general"
    xp: int = Field(default=0, ge=0)
    biocoin: int = Field(default=0, ge=0)
    level: int = Field(default=1, ge=1)
    streak: int = Field(default=1, ge=1)
    last_active: Any = None  # Using Any for datetime/timezone complexities from psycopg2
    total_spent: int = Field(default=0, ge=0)
    max_depth: int = Field(default=0, ge=0)
    is_admin: bool = False
    is_active: bool = True
    raid_count_today: int = Field(default=0, ge=0)
    ref_count: int = Field(default=0, ge=0)
    shadow_broker_expiry: int = 0
    anomaly_buff_expiry: int = 0
    encrypted_cache_unlock_time: int = 0
    proxy_expiry: int = 0
    cryo: int = 0
    accel: int = 0
    decoder: int = 0

    # Catch-all for extra fields (legacy compatibility)
    class Config:
        extra = "allow"

class InventoryItem(BaseModel):
    id: Optional[int] = None
    uid: int
    item_id: str
    quantity: int = Field(default=1, ge=0)
    durability: int = Field(default=100, ge=0)
    custom_data: Optional[str] = None

class EquipmentSlot(BaseModel):
    uid: int
    slot: str
    item_id: str
    durability: int = Field(default=100, ge=0)
    custom_data: Optional[str] = None
