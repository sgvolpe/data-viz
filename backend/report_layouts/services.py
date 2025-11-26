from sqlalchemy.orm import Session
from typing import List

from backend.report_layouts.models import ReportLayout


def fetch_report_layouts_by_user(db: Session, user_id: str) -> List[ReportLayout]:
    return db.query(ReportLayout).filter(ReportLayout.user_id == user_id).all()
