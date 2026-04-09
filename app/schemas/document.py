from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict


class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}