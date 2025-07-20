import asyncio
from collections.abc import AsyncGenerator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from infrastructure.db import Base, engine
from infrastructure.models import FrenchSite, Group, GroupType, ItalianSite, Site
from main import app
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(autouse=True, scope="function")
async def setup_database(db_session):
    """Create tables once, and delete all data after each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with db_session as session:
        # Clean all tables in reverse dependency order
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f"DELETE FROM {table.name}"))
        await session.commit()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Get an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_fr_site_data():
    """Sample site data for testing."""
    return {
        "name": "Test Solar Farm",
        "installation_date": "2025-06-23",
        "max_power_megawatt": 50.0,
        "min_power_megawatt": 10.0,
        "country": "fr",
        "useful_energy_at_1_megawatt": 0.85,
    }


@pytest.fixture
def sample_italian_site_data():
    """Sample Italian site data for testing."""
    return {
        "name": "Test Italian Farm",
        "installation_date": "2023-06-17",  # Saturday
        "max_power_megawatt": 30.0,
        "min_power_megawatt": 5.0,
        "country": "it",
        "efficiency": 0.92,
    }


@pytest.fixture
def sample_group_data():
    """Sample group data for testing."""
    return {"name": "Test Group", "type": "group1"}


@pytest.fixture
async def sample_fr_site(db_session: AsyncSession, sample_fr_site_data: dict) -> FrenchSite:
    """Create a sample site in the database."""
    sample_fr_site_data["installation_date"] = date(2025, 6, 23)
    site = FrenchSite(**sample_fr_site_data)
    db_session.add(site)
    await db_session.commit()
    await db_session.refresh(site, attribute_names=["groups"])
    return site


@pytest.fixture
async def sample_group(db_session: AsyncSession, sample_group_data: dict) -> Group:
    """Create a sample group in the database."""
    child_group = Group(name="G1", type=GroupType.group1)
    group = Group(**sample_group_data)
    group.child_groups.extend([child_group])
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)
    return group


@pytest.fixture
async def multiple_sites(db_session: AsyncSession) -> list[Site]:
    """Create multiple sample sites for testing."""
    sites_data = [
        FrenchSite(
            **{
                "name": "Solar",
                "installation_date": date(2025, 6, 22),
                "max_power_megawatt": 50.0,
                "min_power_megawatt": 10.0,
                "country": "fr",
                "useful_energy_at_1_megawatt": 0.85,
            }
        ),
        FrenchSite(
            **{
                "name": "Solar",
                "installation_date": date(2025, 6, 21),
                "max_power_megawatt": 75.0,
                "min_power_megawatt": 15.0,
                "country": "fr",
                "useful_energy_at_1_megawatt": 0.88,
            }
        ),
        ItalianSite(
            **{
                "name": "Italian Farm 1",
                "installation_date": date(2025, 7, 19),  # Saturday
                "max_power_megawatt": 30.0,
                "min_power_megawatt": 5.0,
                "country": "it",
                "efficiency": 0.92,
            }
        ),
    ]

    sites = []
    for site in sites_data:
        db_session.add(site)
        sites.append(site)

    await db_session.commit()
    for site in sites:
        await db_session.refresh(site)

    return sites


@pytest.fixture
async def multiple_groups(db_session: AsyncSession) -> list[Group]:
    """Create multiple sample groups for testing."""
    groups_data = [
        {"name": "Group A", "type": "group1"},
        {"name": "Group B", "type": "group2"},
        {"name": "Group C", "type": "group1"},
    ]

    groups = []
    for group_data in groups_data:
        group = Group(**group_data)
        db_session.add(group)
        groups.append(group)

    await db_session.commit()
    for group in groups:
        await db_session.refresh(group)

    return groups
