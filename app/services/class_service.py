from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.dao.classes import class_dao
from app.views.schemas.classes import ClassCreate, ClassUpdate


class ClassService:
    @staticmethod
    def create_class(db: Session, class_in: ClassCreate):
        return success(class_dao.create_class(db, class_in.model_dump()), "class created")

    @staticmethod
    def list_classes(db: Session, page: int = 1, size: int = 10, keyword: str = None):
        page = max(1, page)
        size = min(100, max(1, size))
        total, items = class_dao.get_classes(db, page, size, keyword)
        return success({"items": items, "total": total, "page": page, "size": size}, "classes found")

    @staticmethod
    def get_class(db: Session, class_id: int):
        class_info = class_dao.get_class_by_id(db, class_id)
        if not class_info:
            return fail("class not found")
        return success(class_info, "class found")

    @staticmethod
    def update_class(db: Session, class_in: ClassUpdate):
        updated = class_dao.update_class(db, class_in.id, class_in.model_dump(exclude_unset=True))
        if not updated:
            return fail("class not found")
        return success(updated, "class updated")

    @staticmethod
    def delete_class(db: Session, class_id: int):
        if not class_dao.delete_class(db, class_id):
            return fail("class not found")
        return success(None, "class deleted")
