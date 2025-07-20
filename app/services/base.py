from typing import Any, Generic, TypeVar

from sqlalchemy import and_, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.util import AliasedClass

T = TypeVar("T")
OutSchema = TypeVar("OutSchema")


class QueryBuilder:
    def __init__(self, model_class, load_rel=None):
        self.model_class = model_class
        self.stmt = select(model_class)
        self.conditions = []
        self.sort_field = None
        self.sort_order = asc
        self.load_rel = load_rel

    def filter(self, field: str, value: Any):
        """Add a filter condition"""
        if value is None:
            return self

        column = getattr(self.model_class, field, None)
        if column is None:
            return self
        condition = column == value
        self.conditions.append(condition)
        return self

    def sort(self, field: str, order: str = "asc"):
        """Add sorting"""
        column = getattr(self.model_class, field, None)
        if column is None:
            return self

        self.sort_field = column
        self.sort_order = desc if order.lower() == "desc" else asc
        return self

    def build(self):
        """Build the final query"""
        if self.conditions:
            self.stmt = self.stmt.where(and_(*self.conditions))

        if self.sort_field:
            self.stmt = self.stmt.order_by(self.sort_order(self.sort_field))

        if self.load_rel:
            relationship_options = [
                selectinload(getattr(self.model_class, rel)) for rel in self.load_rel
            ]

            return self.stmt.options(*relationship_options)
        return self.stmt


class BaseService(Generic[T, OutSchema]):
    def __init__(self, db: AsyncSession, model_class: type[T | AliasedClass[T]], relations=None):
        self.db = db
        self.model_class = model_class
        self.relations = relations

    def query_builder(self) -> QueryBuilder:
        """Get a query builder that eagerly loads all relationships."""
        return QueryBuilder(self.model_class, self.relations)

    async def list_with_filters(
        self,
        filters: dict[str, Any] | None = None,
        sort: str | None = None,
        output_schema: type[OutSchema] | None = None,
    ) -> list[OutSchema]:
        """List records with dynamic filtering and sorting"""
        builder = self.query_builder()

        # Apply filters
        if filters:
            for field, value in filters.items():
                builder.filter(field, value)
        # Apply sorting
        if sort:
            if sort.startswith("-"):
                field = sort[1:]
                order = "desc"
            else:
                field = sort
                order = "asc"
            builder.sort(field, order)

        # Execute query
        stmt = builder.build()
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        # Convert to output schema if provided
        if output_schema:
            return [output_schema.model_validate(record) for record in records]
        return records
