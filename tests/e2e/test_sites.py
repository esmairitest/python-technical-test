import pytest
from httpx import AsyncClient
from infrastructure.models import FrenchSite


class TestSitesAPI:
    """Test cases for Sites API endpoints."""

    @pytest.mark.asyncio
    async def test_create_fr_site_success(
        self, async_client: AsyncClient, sample_fr_site_data: dict
    ):
        """Test successful site creation."""
        response = await async_client.post("/api/sites", json=sample_fr_site_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_fr_site_data["name"]
        assert data["country"] == sample_fr_site_data["country"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_italian_site_weekend_success(
        self, async_client: AsyncClient, sample_italian_site_data: dict
    ):
        """Test successful Italian site creation on weekend."""
        response = await async_client.post("/api/sites", json=sample_italian_site_data)
        assert response.status_code == 200
        data = response.json()
        assert data["country"] == "it"
        assert data["efficiency"] == sample_italian_site_data["efficiency"]

    @pytest.mark.asyncio
    async def test_create_italian_site_weekday_failure(self, async_client: AsyncClient):
        """Test Italian site creation on weekday should fail."""
        site_data = {
            "name": "Test Italian Farm",
            "installation_date": "2023-06-16",  # Friday
            "max_power_megawatt": 30.0,
            "min_power_megawatt": 5.0,
            "country": "it",
            "efficiency": 0.92,
        }
        response = await async_client.post("/api/sites", json=site_data)
        assert response.status_code == 400
        assert "weekends" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_french_site_duplicate_date_failure(
        self, async_client: AsyncClient, sample_fr_site_data: dict
    ):
        """Test creating two French sites on the same day should fail."""
        # Create first site
        response1 = await async_client.post("/api/sites", json=sample_fr_site_data)
        assert response1.status_code == 200

        # Try to create second site on same date
        site_data2 = sample_fr_site_data.copy()
        site_data2["name"] = "Another French Site"
        response2 = await async_client.post("/api/sites", json=site_data2)
        assert response2.status_code == 400
        assert "one French site" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_site_success(self, async_client: AsyncClient, sample_fr_site: FrenchSite):
        """Test successful site retrieval."""
        response = await async_client.get(f"/api/sites/{sample_fr_site.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_fr_site.id
        assert data["name"] == sample_fr_site.name

    @pytest.mark.asyncio
    async def test_get_site_not_found(self, async_client: AsyncClient):
        """Test site retrieval with non-existent ID."""
        response = await async_client.get("/api/sites/999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_sites_success(self, async_client: AsyncClient, multiple_sites: list):
        """Test successful sites listing."""
        response = await async_client.get("/api/sites")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("id" in site for site in data)

    @pytest.mark.asyncio
    async def test_list_sites_with_filters(self, async_client: AsyncClient, multiple_sites: list):
        """Test sites listing with filters."""
        # Filter by country
        response = await async_client.get("/api/sites?country=fr")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(site["country"] == "fr" for site in data)

        # Filter by name
        response = await async_client.get("/api/sites?name=Solar")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("Solar" in site["name"] for site in data)

    @pytest.mark.asyncio
    async def test_list_sites_with_sorting(self, async_client: AsyncClient, multiple_sites: list):
        """Test sites listing with sorting."""
        # Sort by name ascending
        response = await async_client.get("/api/sites?sort=name")
        assert response.status_code == 200
        data = response.json()
        names = [site["name"] for site in data]
        assert names == sorted(names)

        # Sort by name descending
        response = await async_client.get("/api/sites?sort=-name")
        assert response.status_code == 200
        data = response.json()
        names = [site["name"] for site in data]
        assert names == sorted(names, reverse=True)

    @pytest.mark.asyncio
    async def test_update_site_success(self, async_client: AsyncClient, sample_fr_site: FrenchSite):
        """Test successful site update."""
        update_data = {"name": "Updated Site Name"}
        response = await async_client.patch(f"/api/sites/{sample_fr_site.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Site Name"
        assert data["id"] == sample_fr_site.id

    @pytest.mark.asyncio
    async def test_update_site_not_found(self, async_client: AsyncClient):
        """Test site update with non-existent ID."""
        update_data = {"name": "Updated Name"}
        response = await async_client.patch("/api/sites/999", json=update_data)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_site_success(self, async_client: AsyncClient, sample_fr_site: FrenchSite):
        """Test successful site deletion."""
        response = await async_client.delete(f"/api/sites/{sample_fr_site.id}")
        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Verify site is deleted
        get_response = await async_client.get(f"/api/sites/{sample_fr_site.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_site_not_found(self, async_client: AsyncClient):
        """Test site deletion with non-existent ID."""
        response = await async_client.delete("/api/sites/999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_site_missing_required_fields(self, async_client: AsyncClient):
        """Test site creation with missing required fields."""
        incomplete_data = {
            "name": "Test Site",
            "installation_date": "2023-06-15",
            # Missing other required fields
        }
        response = await async_client.post("/api/sites", json=incomplete_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_french_site_missing_useful_energy(self, async_client: AsyncClient):
        """Test French site creation without useful_energy_at_1_megawatt should fail."""
        site_data = {
            "name": "French Site",
            "installation_date": "2023-06-15",
            "max_power_megawatt": 50.0,
            "min_power_megawatt": 10.0,
            "country": "fr",
            # Missing useful_energy_at_1_megawatt
        }
        response = await async_client.post("/api/sites", json=site_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_italian_site_missing_efficiency(self, async_client: AsyncClient):
        """Test Italian site creation without efficiency should fail."""
        site_data = {
            "name": "Italian Site",
            "installation_date": "2023-06-17",
            "max_power_megawatt": 30.0,
            "min_power_megawatt": 5.0,
            "country": "it",
            # Missing efficiency
        }
        response = await async_client.post("/api/sites", json=site_data)
        assert response.status_code == 422
