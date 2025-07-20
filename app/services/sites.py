from datetime import date
from typing import List

from fastapi import HTTPException
from infrastructure.models import FrenchSite, Group, GroupType, ItalianSite, Site
from pydantic import BaseModel
from schemas import SiteCreate, SiteOut, SiteUpdate
from schemas.site import FrenchSiteOut, ItalianSiteOut
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, with_polymorphic

from .base import BaseService

# A mapping between country → model class
COUNTRY_MODEL_MAP = {"fr": FrenchSite, "it": ItalianSite}
SITE_SCHEME_OUT: dict[str, type[BaseModel]] = {"fr": FrenchSiteOut, "it": ItalianSiteOut}


class SiteService(BaseService[Site, FrenchSite | ItalianSite]):
    """Service for managing site-related operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the services with a DB session."""
        site_entity = with_polymorphic(Site, [FrenchSite, ItalianSite])
        super().__init__(db, site_entity, ["groups"])

    async def validate_group_ids_not_group3(self, group_ids: list[int]):
        """Ensure no group in the list is of type 'group3'."""
        groups = await self.get_groups_by_ids(group_ids)
        for group in groups:
            if group.type == GroupType.group3:
                raise HTTPException(400, f"Group {group.id} is of type group3 — not allowed.")
        return groups

    async def get_groups_by_ids(self, group_ids: List[int]) -> List[Group]:
        stmt = select(Group).where(Group.id.in_(group_ids))
        result = await self.db.execute(stmt)
        groups = list(result.scalars().all())
        if len(groups) != len(set(group_ids)):
            raise HTTPException(status_code=404, detail="One or more groups not found.")
        return groups

    async def validate_installation_constraints(
        self, installation_date: date, country: str, side_id=None
    ) -> None:
        """Apply business rules for French and Italian site installation dates."""
        if country == "fr":
            q = await self.db.execute(
                select(Site).where(
                    Site.country == "fr", Site.installation_date == installation_date
                )
            )
            result = q.scalars().first()
            if result and side_id != result.id:
                raise HTTPException(
                    status_code=400, detail="Only one French site can be installed per day."
                )
        if country == "it":
            weekday = installation_date.weekday()
            if weekday not in (5, 6):
                raise HTTPException(
                    status_code=400, detail="Italian sites must be installed on weekends."
                )

    async def create_site(self, site_data: SiteCreate) -> SiteOut:
        """Create a new site with validation logic applied."""
        await self.validate_installation_constraints(site_data.installation_date, site_data.country)
        await self.validate_group_ids_not_group3(site_data.groups or [])
        model_cls = COUNTRY_MODEL_MAP.get(site_data.country)
        if not model_cls:
            raise HTTPException(400, detail=f"Unsupported country: {site_data.country}")
        site = model_cls(**site_data.model_dump(exclude_unset=True, exclude={"groups"}))
        if site_data.groups:
            site.groups = await self.get_groups_by_ids(site_data.groups)
        self.db.add(site)
        await self.db.commit()
        await self.db.refresh(site, attribute_names=["groups"])
        schema = SITE_SCHEME_OUT[site.country]
        return schema.model_validate(site)

    async def get_site(self, site_id: int) -> SiteOut:
        """Retrieve a site by ID or raise 404 if not found."""
        site_entity = with_polymorphic(Site, [FrenchSite, ItalianSite])
        stmt = (
            select(site_entity).options(selectinload(site_entity.groups)).where(Site.id == site_id)
        )
        result = await self.db.execute(stmt)
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        return site

    async def update_site(self, site_id: int, site_data: SiteUpdate) -> SiteOut:
        """Update an existing site with validations."""
        await self.validate_group_ids_not_group3(site_data.groups or [])
        site = await self.get_site(site_id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        update_data = site_data.model_dump(exclude_unset=True, exclude={"groups"})
        installation_date = update_data.get("installation_date", site.installation_date)
        country = update_data.get("country", site.country)
        await self.validate_installation_constraints(installation_date, country, site.id)
        for field, value in update_data.items():
            setattr(site, field, value)
        if site_data.groups:
            site.groups = await self.get_groups_by_ids(site_data.groups)
        await self.db.commit()
        await self.db.refresh(site)
        return site

    async def delete_site(self, site_id: int):
        """Delete a site by ID."""
        site = await self.db.get(Site, site_id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        await self.db.delete(site)
        await self.db.commit()
        return {"ok": True}

    async def list_sites(
        self, filters: dict | None = None, sort: str | None = None
    ) -> list[SiteOut]:
        """List all sites with optional filtering and sorting."""
        res = await self.list_with_filters(filters, sort)
        return res
