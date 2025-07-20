from typing import Annotated, List

from fastapi import APIRouter, Body, Depends, Query
from infrastructure.db import get_session
from schemas import SiteCreate, SiteOut, SiteUpdate
from services.sites import SiteService
from sqlalchemy.ext.asyncio import AsyncSession

site_router = APIRouter(prefix="/sites", tags=["sites"])


@site_router.post("")
async def create_site(
    db: Annotated[AsyncSession, Depends(get_session)],
    site_data: SiteCreate = Body(
        example={
            "name": "s1",
            "installation_date": "2025-07-20",
            "max_power_megawatt": 1,
            "min_power_megawatt": 2,
            "country": "fr",
            "groups": [1],
            "useful_energy_at_1_megawatt": 0,
        }
    ),
) -> SiteOut:
    service = SiteService(db)
    return await service.create_site(site_data)


@site_router.get("")
async def list_sites(
    db: Annotated[AsyncSession, Depends(get_session)],
    name: str | None = Query(None, description="Filter by name"),
    country: str | None = Query(None, description="Filter by country"),
    installation_date: str | None = Query(None, description="Filter by installation date"),
    sort: str | None = Query(None, description="Sort parameter (e.g., 'name', '-name')"),
) -> List[SiteOut]:
    service = SiteService(db)
    filters = {}
    if name:
        filters["name"] = name
    if country:
        filters["country"] = country
    if installation_date:
        filters["installation_date"] = installation_date
    return await service.list_sites(filters=filters if filters else None, sort=sort)


@site_router.get("/{site_id}")
async def get_site(site_id: int, db: Annotated[AsyncSession, Depends(get_session)]) -> SiteOut:
    service = SiteService(db)
    return await service.get_site(site_id)


@site_router.patch("/{site_id}")
async def update_site(
    site_id: int,
    db: Annotated[AsyncSession, Depends(get_session)],
    site_data: SiteUpdate = Body(
        example={
            "name": "s2",
            "installation_date": "2025-07-01",
            "max_power_megawatt": 1,
            "min_power_megawatt": 2,
            "country": "fr",
            "groups": [1],
            "useful_energy_at_1_megawatt": 0,
        }
    ),
) -> SiteOut:
    service = SiteService(db)
    return await service.update_site(site_id, site_data)


@site_router.delete("/{site_id}")
async def delete_site(site_id: int, db: Annotated[AsyncSession, Depends(get_session)]):
    service = SiteService(db)
    return await service.delete_site(site_id)
