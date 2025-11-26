# models.py
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from uuid import uuid4
from datetime import datetime

from sqlalchemy.orm import relationship

from database import Base

class ReportLayout(Base):
    __tablename__ = "report_layout"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    uid = Column(String, unique=True, nullable=False, index=True)

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    # user = relationship("User", back_populates="report_layouts")

    config = Column(JSON, nullable=False)  # store JSON configuration