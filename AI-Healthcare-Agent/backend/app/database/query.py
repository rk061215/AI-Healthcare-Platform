from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable, Generic, Optional, TypeVar, Union

from sqlalchemy import Select, UnaryExpression, asc, desc, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


@dataclass
class PageParams:
    page: int = 1
    per_page: int = 20

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        return self.per_page


@dataclass
class Page(Generic[ModelType]):
    items: list[ModelType]
    total: int
    page: int
    per_page: int
    pages: int

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "per_page": self.per_page,
            "pages": self.pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
        }


@dataclass
class FilterRule:
    field: str
    value: Any
    operator: str = "eq"


@dataclass
class SortRule:
    field: str
    direction: str = "asc"


def parse_page_params(page: Optional[int] = 1, per_page: Optional[int] = 20) -> PageParams:
    p = max(1, page or 1)
    pp = max(1, min(100, per_page or 20))
    return PageParams(page=p, per_page=pp)


def parse_sort_string(sort: Optional[str]) -> list[SortRule]:
    if not sort:
        return []
    rules: list[SortRule] = []
    for part in sort.split(","):
        part = part.strip()
        if part.startswith("-"):
            rules.append(SortRule(field=part[1:], direction="desc"))
        elif part.startswith("+"):
            rules.append(SortRule(field=part[1:], direction="asc"))
        else:
            rules.append(SortRule(field=part, direction="asc"))
    return rules


def parse_filter_string(filters: Optional[str]) -> list[FilterRule]:
    if not filters:
        return []
    rules: list[FilterRule] = []
    for part in filters.split(","):
        part = part.strip()
        for op in ("__gte", "__lte", "__gt", "__lt", "__ne", "__like", "__ilike"):
            if op in part:
                field, value = part.split(op, 1)
                operator = op.lstrip("_")
                value = value.lstrip(":")
                rules.append(FilterRule(field=field, value=value, operator=operator))
                break
        else:
            if ":" in part:
                field, value = part.split(":", 1)
                rules.append(FilterRule(field=field, value=value, operator="eq"))
    return rules


def apply_filters(query: Select, model: type[ModelType], filters: list[FilterRule]) -> Select:
    for rule in filters:
        column = getattr(model, rule.field, None)
        if column is None:
            continue
        value = rule.value
        if isinstance(column.type, (date.__class__, datetime.__class__)):
            try:
                value = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                pass
        op_map = {
            "eq": lambda c, v: c == v,
            "ne": lambda c, v: c != v,
            "gt": lambda c, v: c > v,
            "gte": lambda c, v: c >= v,
            "lt": lambda c, v: c < v,
            "lte": lambda c, v: c <= v,
            "like": lambda c, v: c.like(v),
            "ilike": lambda c, v: c.ilike(v),
        }
        op_fn = op_map.get(rule.operator)
        if op_fn:
            query = query.where(op_fn(column, value))
    return query


def apply_sorting(query: Select, model: type[ModelType], sort_rules: list[SortRule]) -> Select:
    for rule in sort_rules:
        column = getattr(model, rule.field, None)
        if column is None:
            continue
        order_fn: Callable[[Any], UnaryExpression] = desc if rule.direction == "desc" else asc
        query = query.order_by(order_fn(column))
    return query


def apply_eager_loading(
    query: Select,
    model: type[ModelType],
    relationships: Optional[list[str]] = None,
) -> Select:
    if relationships:
        for rel_name in relationships:
            rel = getattr(model, rel_name, None)
            if rel is not None:
                query = query.options(selectinload(rel))
    return query


def paginate_query(
    db: Session,
    model: type[ModelType],
    page_params: PageParams,
    filters: Optional[list[FilterRule]] = None,
    sort_rules: Optional[list[SortRule]] = None,
    eager_load: Optional[list[str]] = None,
) -> Page[ModelType]:
    base_query = select(model)
    base_query = apply_filters(base_query, model, filters or [])
    base_query = apply_sorting(base_query, model, sort_rules or [])
    base_query = apply_eager_loading(base_query, model, eager_load)

    count_query = select(model)
    count_query = apply_filters(count_query, model, filters or [])
    total = len(db.execute(count_query).scalars().all())

    query = base_query.offset(page_params.skip).limit(page_params.limit)
    items = list(db.execute(query).scalars().all())

    pages = max(1, (total + page_params.per_page - 1) // page_params.per_page)

    return Page(
        items=items,
        total=total,
        page=page_params.page,
        per_page=page_params.per_page,
        pages=pages,
    )


def exists(db: Session, model: type[ModelType], **filters: Any) -> bool:
    query = select(model).filter_by(**filters).limit(1)
    return db.execute(query).first() is not None


FILTER_OPERATOR_PATTERN = re.compile(r"^(?P<field>\w+)(?:__(?P<op>gte|lte|gt|lt|ne|like|ilike))?$")
