from typing import List

from fastapi import HTTPException
from infrastructure.models import Group, Site
from schemas import GroupCreate, GroupOut, GroupUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only, selectinload

from .base import BaseService


class GroupService(BaseService[Group, GroupOut]):
    """Service for managing group-related operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the services with a DB session."""
        super().__init__(db, Group, ["child_groups", "sites"])

    async def get_groups_by_ids(self, ids: list[int]) -> list[Group]:
        stmt = select(Group).options(load_only(Group.id)).where(Group.id.in_(ids))
        result = await self.db.execute(stmt)
        groups = list(result.scalars().all())

        if len(groups) != len(set(ids)):
            raise HTTPException(status_code=404, detail="One or more groups not found.")

        return groups

    async def get_sites_by_ids(self, site_ids: List[int]) -> List[Site]:
        q = await self.db.execute(select(Site).where(Site.id.in_(site_ids)))
        sites = list(q.scalars().all())

        if len(sites) != len(set(site_ids)):
            raise HTTPException(status_code=404, detail="One or more sites not found.")

        return sites

    async def create_group(self, group_data: GroupCreate) -> GroupOut:
        """Create a new group."""
        group = Group(**group_data.model_dump(exclude={"child_groups", "sites"}))
        if group_data.child_groups:
            group.child_groups = await self.get_groups_by_ids(group_data.child_groups)
        if group_data.sites:
            group.sites = await self.get_sites_by_ids(group_data.sites)
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group, attribute_names=["child_groups", "sites"])
        return GroupOut.model_validate(group)

    async def get_group(self, group_id: int) -> GroupOut:
        """Retrieve a group by ID or raise 404 if not found."""
        stmt = (
            select(Group)
            .options(selectinload(Group.child_groups), selectinload(Group.sites))
            .where(Group.id == group_id)
        )
        result = await self.db.execute(stmt)
        group = result.scalar_one_or_none()

        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return GroupOut.model_validate(group)

    async def update_group(self, group_id: int, group_data: GroupUpdate) -> GroupOut:
        """Update an existing group."""
        stmt = (
            select(Group)
            .options(selectinload(Group.child_groups), selectinload(Group.sites))
            .where(Group.id == group_id)
        )

        result = await self.db.execute(stmt)
        group = result.scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        for field, value in group_data.model_dump(
            exclude_unset=True, exclude={"child_groups", "sites"}
        ).items():
            setattr(group, field, value)
        if group_data.child_groups:
            groups = await self.get_groups_by_ids(group_data.child_groups)
            group.child_groups = groups
        if group_data.sites:
            sites = await self.get_sites_by_ids(group_data.sites)
            group.sites = sites
        await self.db.commit()
        await self.db.refresh(group, attribute_names=["child_groups", "sites"])
        return GroupOut.model_validate(group)

    async def delete_group(self, group_id: int):
        """Delete a group if it has no sites or subgroups."""
        group = await self.db.get(Group, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        # Check if the group contains sites
        has_sites = await self.db.scalar(select(Group.sites.any()).where(Group.id == group_id))
        if has_sites:
            raise HTTPException(status_code=400, detail="Cannot delete group linked to sites.")

        await self.db.delete(group)
        await self.db.commit()
        return {"ok": True}

    async def list_groups(
        self, filters: dict | None = None, sort: str | None = None
    ) -> list[GroupOut]:
        """List all groups with optional filtering and sorting."""
        return await self.list_with_filters(filters, sort, GroupOut)
