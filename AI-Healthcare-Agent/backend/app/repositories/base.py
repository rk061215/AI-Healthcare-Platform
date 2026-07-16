from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.base import Base
from app.database.query import (
    FilterRule,
    Page,
    PageParams,
    SortRule,
    paginate_query,
)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: type[ModelType]):
        self.db = db
        self.model = model

    def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def get(self, id: Any, eager_load: Optional[list[str]] = None) -> Optional[ModelType]:
        if isinstance(id, str):
            try:
                import uuid
                id = uuid.UUID(id)
            except (ValueError, AttributeError):
                pass
        query = select(self.model)
        if eager_load:
            for rel_name in eager_load:
                rel = getattr(self.model, rel_name, None)
                if rel is not None:
                    query = query.options(selectinload(rel))
        query = query.where(self.model.id == id)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None,
        order_by: Optional[str] = None,
        eager_load: Optional[list[str]] = None,
    ) -> list[ModelType]:
        query = select(self.model)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        if eager_load:
            for rel_name in eager_load:
                rel = getattr(self.model, rel_name, None)
                if rel is not None:
                    query = query.options(selectinload(rel))
        if order_by:
            query = query.order_by(order_by)
        query = query.offset(skip).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def paginate(
        self,
        page_params: PageParams,
        filters: Optional[list[FilterRule]] = None,
        sort_rules: Optional[list[SortRule]] = None,
        eager_load: Optional[list[str]] = None,
    ) -> Page[ModelType]:
        return paginate_query(self.db, self.model, page_params, filters, sort_rules, eager_load)

    def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        instance = self.get(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key) and value is not None:
                setattr(instance, key, value)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, id: Any) -> bool:
        instance = self.get(id)
        if not instance:
            return False
        self.db.delete(instance)
        self.db.commit()
        return True

    def count(self, filters: Optional[dict] = None) -> int:
        query = select(self.model)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        result = self.db.execute(query)
        return len(result.scalars().all())
