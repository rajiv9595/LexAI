"""Public user schemas. Never exposes password hashes."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Safe public representation of a user account."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
