from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from sqlalchemy import Column, Boolean, and_
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    # 单主键查询
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model) \
            .filter(self.model.id == id, self.model.is_deleted == False) \
            .first()

    # 分页查询
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model) \
            .filter(self.model.is_deleted == False) \
            .offset(skip).limit(limit).all()

    # 创建记录
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_data = obj_in.model_dump() if not isinstance(obj_in, dict) else obj_in
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    # 更新记录
    def update(self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        update_data = obj_in.model_dump(exclude_unset=True) if not isinstance(obj_in, dict) else obj_in
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        try:
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            raise e
    # 单主键软删除
    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = self.get(db, id)
        if not obj:
            raise ValueError(f"ID为 {id} 的记录不存在或已删除")
        obj.is_deleted = True
        db.add(obj)
        try:
            db.commit()
            return obj
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    # 按字段查询
    def get_by_column(self, db: Session, *, column_name: str, value: Any) -> Optional[ModelType]:
        if not hasattr(self.model, column_name):
            return None
        column = getattr(self.model, column_name)
        return (db.query(self.model)
                .filter(column == value, self.model.is_deleted == False).first())