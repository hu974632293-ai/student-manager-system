from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.class_service import ClassService
from app.views.schemas.classes import ClassCreate, ClassUpdate


class_router = APIRouter(prefix="/classes", tags=["classes"])


@class_router.post("/")
def create_class(class_in: ClassCreate, db: Session = Depends(get_db)):
    return ClassService.create_class(db, class_in)


@class_router.get("/")
def list_classes(page: int = 1, size: int = 10, keyword: Optional[str] = None, db: Session = Depends(get_db)):
    return ClassService.list_classes(db, page, size, keyword)


@class_router.get("/{class_id}")
def get_class(class_id: int, db: Session = Depends(get_db)):
    return ClassService.get_class(db, class_id)


@class_router.put("/")
def update_class(class_in: ClassUpdate, db: Session = Depends(get_db)):
    return ClassService.update_class(db, class_in)


@class_router.delete("/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    return ClassService.delete_class(db, class_id)
