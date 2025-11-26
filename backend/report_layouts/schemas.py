from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

# Base schema for input
class ReportLayoutBase(BaseModel):
    uid: str
    config: Dict  # JSON config

# Schema for creating
class ReportLayoutCreate(ReportLayoutBase):
    user_id: str  # link to a user

# Schema for updating
class ReportLayoutUpdate(BaseModel):
    config: Optional[Dict] = None

# Schema for reading / output
class ReportLayoutRead(ReportLayoutBase):
    id: str
    timestamp: datetime
    user_id: str

    class Config:
        orm_mode = True
