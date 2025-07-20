from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query
from infrastructure.db import get_session
from schemas import GroupCreate, GroupOut, GroupUpdate
from services.groups import GroupService
from sqlalchemy.ext.asyncio import AsyncSession

group_router = APIRouter(prefix="/groups", tags=["groups"])


@group_router.post("")
async def create_group(
    db: Annotated[AsyncSession, Depends(get_session)],
    group_data: GroupCreate = Body(
        example={"name": "g1", "type": "group1", "child_groups": [], "sites": []}
    ),
) -> GroupOut:
    service = GroupService(db)
    return await service.create_group(group_data)


@group_router.get("")
async def list_groups(
    db: Annotated[AsyncSession, Depends(get_session)],
    name: str | None = Query(None, description="Filter by name"),
    group_type: str | None = Query(None, description="Filter by type"),
    sort: str | None = Query(None, description="Sort parameter (e.g., 'name', '-name')"),
) -> list[GroupOut]:
    service = GroupService(db)
    filters = {}
    if name:
        filters["name"] = name
    if group_type:
        filters["type"] = group_type
    return await service.list_groups(filters=filters if filters else None, sort=sort)


@group_router.get("/{group_id}")
async def get_group(group_id: int, db: Annotated[AsyncSession, Depends(get_session)]) -> GroupOut:
    service = GroupService(db)
    return await service.get_group(group_id)


@group_router.patch("/{group_id}")
async def update_group(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    group_data: GroupUpdate = Body(
        example={"name": "g1", "type": "group1", "child_groups": [], "sites": []}
    ),
) -> GroupOut:
    service = GroupService(db)
    return await service.update_group(group_id, group_data)


@group_router.delete("/{group_id}")
async def delete_group(group_id: int, db: Annotated[AsyncSession, Depends(get_session)]):
    service = GroupService(db)
    return await service.delete_group(group_id)
