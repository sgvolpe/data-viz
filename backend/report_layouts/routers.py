from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from report_layouts.schemas import ReportLayoutCreate, ReportLayoutRead, ReportLayoutUpdate
from users.models import User
from users.routers import get_db
from report_layouts.models import ReportLayout

router = APIRouter(prefix="/report-layouts", tags=["Report Layouts"])


# Create
@router.post("/", response_model=ReportLayoutRead)
def create_report_layout(layout: ReportLayoutCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == layout.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_layout = ReportLayout(uid=layout.uid, config=layout.config, user_id=layout.user_id)
    db.add(db_layout)
    db.commit()
    db.refresh(db_layout)
    return db_layout


# Read all
@router.get("/", response_model=List[ReportLayoutRead])
def get_report_layouts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    layouts = db.query(ReportLayout).offset(skip).limit(limit).all()
    return layouts


# Read by ID
@router.get("/{layout_id}", response_model=ReportLayoutRead)
def get_report_layout(layout_id: str, db: Session = Depends(get_db)):
    layout = db.query(ReportLayout).filter(ReportLayout.id == layout_id).first()
    if not layout:
        raise HTTPException(status_code=404, detail="Report layout not found")
    return layout


# Update
@router.put("/{layout_id}", response_model=ReportLayoutRead)
def update_report_layout(layout_id: str, layout_update: ReportLayoutUpdate, db: Session = Depends(get_db)):
    layout = db.query(ReportLayout).filter(ReportLayout.id == layout_id).first()
    if not layout:
        raise HTTPException(status_code=404, detail="Report layout not found")

    if layout_update.config is not None:
        layout.config = layout_update.config

    db.commit()
    db.refresh(layout)
    return layout


# Delete
@router.delete("/{layout_id}", response_model=dict)
def delete_report_layout(layout_id: str, db: Session = Depends(get_db)):
    layout = db.query(ReportLayout).filter(ReportLayout.id == layout_id).first()
    if not layout:
        raise HTTPException(status_code=404, detail="Report layout not found")

    db.delete(layout)
    db.commit()
    return {"detail": "Report layout deleted"}
