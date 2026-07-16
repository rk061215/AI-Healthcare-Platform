from app.database.query import (
    FilterRule,
    Page,
    PageParams,
    SortRule,
    exists,
    parse_filter_string,
    parse_page_params,
    parse_sort_string,
)


class TestPageParams:
    def test_defaults(self):
        p = PageParams()
        assert p.page == 1
        assert p.per_page == 20
        assert p.skip == 0
        assert p.limit == 20

    def test_custom_values(self):
        p = PageParams(page=3, per_page=10)
        assert p.skip == 20
        assert p.limit == 10


class TestPage:
    def test_has_next(self):
        p = Page(items=[1, 2], total=20, page=1, per_page=10, pages=2)
        assert p.has_next is True
        assert p.has_prev is False

    def test_no_next(self):
        p = Page(items=[], total=10, page=2, per_page=10, pages=1)
        assert p.has_next is False
        assert p.has_prev is True

    def test_to_dict(self):
        p = Page(items=[1], total=1, page=1, per_page=10, pages=1)
        d = p.to_dict()
        assert d["total"] == 1
        assert d["has_next"] is False


class TestParsePageParams:
    def test_default(self):
        p = parse_page_params()
        assert p.page == 1
        assert p.per_page == 20

    def test_clamps_values(self):
        p = parse_page_params(page=0, per_page=999)
        assert p.page == 1
        assert p.per_page == 100


class TestParseSortString:
    def test_empty(self):
        assert parse_sort_string("") == []
        assert parse_sort_string(None) == []

    def test_asc(self):
        rules = parse_sort_string("name")
        assert len(rules) == 1
        assert rules[0].field == "name"
        assert rules[0].direction == "asc"

    def test_desc(self):
        rules = parse_sort_string("-created_at")
        assert len(rules) == 1
        assert rules[0].field == "created_at"
        assert rules[0].direction == "desc"

    def test_multiple(self):
        rules = parse_sort_string("name,-created_at")
        assert len(rules) == 2


class TestParseFilterString:
    def test_empty(self):
        assert parse_filter_string("") == []
        assert parse_filter_string(None) == []

    def test_eq(self):
        rules = parse_filter_string("email:test@test.com")
        assert len(rules) == 1
        assert rules[0].field == "email"
        assert rules[0].operator == "eq"
        assert rules[0].value == "test@test.com"

    def test_operator_syntax(self):
        rules = parse_filter_string("age__gte:18")
        assert len(rules) == 1
        assert rules[0].field == "age"
        assert rules[0].operator == "gte"
        assert rules[0].value == "18"


class TestFilterRule:
    def test_creation(self):
        rule = FilterRule(field="name", value="John", operator="eq")
        assert rule.field == "name"
        assert rule.value == "John"
        assert rule.operator == "eq"


class TestSortRule:
    def test_creation(self):
        rule = SortRule(field="name", direction="desc")
        assert rule.field == "name"
        assert rule.direction == "desc"


class TestExists:
    def test_returns_false_for_empty_table(self, db_session):
        from app.models.doctor import Doctor
        assert exists(db_session, Doctor, email="nonexistent") is False
