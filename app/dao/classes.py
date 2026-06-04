from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.classes import Class
from app.models.teacher import Teacher


class ClassDao:
    def get_classes(self, db: Session, page: int, size: int, keyword: Optional[str], class_ids: Optional[list[int]] = None) -> Tuple[int, List[Class]]:
        query = db.query(Class).options(joinedload(Class.teachers)).filter(Class.is_deleted == False)
        if class_ids is not None:
            if not class_ids:
                return 0, []
            query = query.filter(Class.id.in_(class_ids))
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(or_(Class.class_id.like(like), Class.head_teacher.like(like), Class.description.like(like)))
        total = query.count()
        items = query.order_by(Class.id.asc()).offset((page - 1) * size).limit(size).all()
        return total, items

    def get_class_by_id(self, db: Session, class_id: int, class_ids: Optional[list[int]] = None):
        query = db.query(Class).options(joinedload(Class.teachers)).filter(Class.id == class_id, Class.is_deleted == False)
        if class_ids is not None:
            if not class_ids:
                return None
            query = query.filter(Class.id.in_(class_ids))
        return query.first()

    def create_class(self, db: Session, class_data: dict):
        data = dict(class_data)
        teacher_ids = data.pop("teacher_ids", [])
        class_obj = Class(**data)
        if teacher_ids:
            class_obj.teachers = db.query(Teacher).filter(Teacher.id.in_(teacher_ids), Teacher.is_deleted == False).all()
        db.add(class_obj)
        db.commit()
        db.refresh(class_obj)
        return class_obj

    def update_class(self, db: Session, class_id: int, class_data: dict):
        class_obj = self.get_class_by_id(db, class_id)
        if not class_obj:
            return None
        data = dict(class_data)
        teacher_ids = data.pop("teacher_ids", None)
        data.pop("id", None)
        for key, value in data.items():
            setattr(class_obj, key, value)
        if teacher_ids is not None:
            class_obj.teachers = db.query(Teacher).filter(Teacher.id.in_(teacher_ids), Teacher.is_deleted == False).all()
        db.commit()
        db.refresh(class_obj)
        return class_obj

    def delete_class(self, db: Session, class_id: int) -> bool:
        class_obj = self.get_class_by_id(db, class_id)
        if not class_obj:
            return False
        class_obj.is_deleted = True
        db.commit()
        return True


class_dao = ClassDao()
