"""Query optimization utilities to prevent N+1 queries and optimize database access."""

from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database.base import Base
from app.database.query import Page, PageParams, apply_filters, apply_sorting


class QueryOptimizer:
    """Prevents N+1 queries by providing eager-loading strategies per model."""

    EAGER_STRATEGIES: dict[str, list[str]] = {
        "Patient": [
            "reports",
            "medicines",
            "appointments",
            "doctor_assignments",
            "doctor_assignments.doctor",
            "adherence_logs",
            "emergency_alerts",
            "chat_messages",
        ],
        "Doctor": [
            "appointments",
            "patient_assignments",
            "patient_assignments.patient",
            "acknowledged_alerts",
        ],
        "Appointment": ["patient", "doctor"],
        "Report": ["patient", "medicines"],
        "Medicine": ["patient", "report", "adherence_logs"],
        "AdherenceLog": ["medicine", "patient"],
        "EmergencyAlert": ["patient", "acknowledged_by_doctor"],
        "ChatHistory": ["patient"],
        "PatientDoctor": ["patient", "doctor"],
    }

    @classmethod
    def get_eager_options(cls, model_name: str, load_paths: Optional[list[str]] = None) -> list:
        """Return selectinload options for the given model and optional custom paths."""
        paths = load_paths or cls.EAGER_STRATEGIES.get(model_name, [])
        options = []
        for path in paths:
            parts = path.split(".")
            opt = None
            for part in parts:
                if opt is None:
                    opt = selectinload(getattr(__import__("app.models", fromlist=[part]), part, None) if False else joinedload(part))
                else:
                    opt = opt.selectinload(part)
            options.append(opt)
        return options

    @classmethod
    def apply_eager_loading(cls, query: Select, model_name: str, load_paths: Optional[list[str]] = None) -> Select:
        options = cls.get_eager_options(model_name, load_paths)
        for opt in options:
            query = query.options(opt)
        return query


def paginate_with_optimization(
    db: Session,
    model: type,
    page_params: PageParams,
    model_name: str,
    filters: Optional[list] = None,
    sort_rules: Optional[list] = None,
    eager_load: Optional[list[str]] = None,
) -> Page:
    """Paginate with automatic eager loading to prevent N+1 queries."""
    query = select(model)
    query = apply_filters(query, model, filters or [])
    query = apply_sorting(query, model, sort_rules or [])

    load_paths = eager_load or QueryOptimizer.EAGER_STRATEGIES.get(model_name, [])
    for path in load_paths:
        attr = getattr(model, path.split(".")[0], None)
        if attr is not None:
            query = query.options(selectinload(attr))

    count_query = select(model)
    count_query = apply_filters(count_query, model, filters or [])
    total = len(db.execute(count_query).scalars().all())

    query = query.offset(page_params.skip).limit(page_params.limit)
    items = list(db.execute(query).scalars().all())

    pages = max(1, (total + page_params.per_page - 1) // page_params.per_page)

    return Page(
        items=items,
        total=total,
        page=page_params.page,
        per_page=page_params.per_page,
        pages=pages,
    )
