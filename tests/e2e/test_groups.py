import pytest
from httpx import AsyncClient
from infrastructure.models import Group


class TestGroupsAPI:
    """Test cases for Groups API endpoints."""

    @pytest.mark.asyncio
    async def test_create_group_success(self, async_client: AsyncClient, sample_group_data: dict):
        """Test successful group creation."""
        response = await async_client.post("/api/groups", json=sample_group_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_group_data["name"]
        assert data["type"] == sample_group_data["type"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_group_with_child_success(
        self, async_client: AsyncClient, sample_group_data: dict, sample_group: Group
    ):
        """Test successful group creation."""
        sample_group_data["child_groups"] = [sample_group.id]
        response = await async_client.post("/api/groups", json=sample_group_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_group_data["name"]
        assert data["type"] == sample_group_data["type"]
        assert "id" in data
        assert data["child_groups"][0]["id"] == sample_group.id

    @pytest.mark.asyncio
    async def test_get_group_success(self, async_client: AsyncClient, sample_group):
        """Test successful group retrieval."""
        response = await async_client.get(f"/api/groups/{sample_group.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_group.id
        assert data["name"] == sample_group.name

    @pytest.mark.asyncio
    async def test_get_group_not_found(self, async_client: AsyncClient):
        """Test group retrieval with non-existent ID."""
        response = await async_client.get("/api/groups/999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_groups_success(self, async_client: AsyncClient, multiple_groups):
        """Test successful groups listing."""
        response = await async_client.get("/api/groups")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("id" in group for group in data)

    @pytest.mark.asyncio
    async def test_list_groups_with_filters(self, async_client: AsyncClient, multiple_groups):
        """Test groups listing with filters."""
        # Filter by type
        response = await async_client.get("/api/groups?group_type=group1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(group["type"] == "group1" for group in data)

        # Filter by name
        response = await async_client.get("/api/groups?name=Group A")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Group A"

    @pytest.mark.asyncio
    async def test_list_groups_with_sorting(self, async_client: AsyncClient, multiple_groups):
        """Test groups listing with sorting."""
        # Sort by name ascending
        response = await async_client.get("/api/groups?sort=name")
        assert response.status_code == 200
        data = response.json()
        names = [group["name"] for group in data]
        assert names == sorted(names)

        # Sort by name descending
        response = await async_client.get("/api/groups?sort=-name")
        assert response.status_code == 200
        data = response.json()
        names = [group["name"] for group in data]
        assert names == sorted(names, reverse=True)

        # Sort by id
        response = await async_client.get("/api/groups?sort=id")
        assert response.status_code == 200
        data = response.json()
        ids = [group["id"] for group in data]
        assert ids == sorted(ids)

    @pytest.mark.asyncio
    async def test_update_group_success(self, async_client: AsyncClient, sample_group):
        """Test successful group update."""
        update_data = {"name": "Updated Group Name"}
        response = await async_client.patch(f"/api/groups/{sample_group.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Group Name"
        assert data["id"] == sample_group.id

    @pytest.mark.asyncio
    async def test_update_group_not_found(self, async_client: AsyncClient):
        """Test group update with non-existent ID."""
        update_data = {"name": "Updated Name"}
        response = await async_client.patch("/api/groups/999", json=update_data)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_group_success(self, async_client: AsyncClient, sample_group):
        """Test successful group deletion."""
        response = await async_client.delete(f"/api/groups/{sample_group.id}")
        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Verify group is deleted
        get_response = await async_client.get(f"/api/groups/{sample_group.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_group_not_found(self, async_client: AsyncClient):
        """Test group deletion with non-existent ID."""
        response = await async_client.delete("/api/groups/999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_group_missing_required_fields(self, async_client: AsyncClient):
        """Test group creation with missing required fields."""
        incomplete_data = {
            "name": "Test Group"
            # Missing type
        }
        response = await async_client.post("/api/groups", json=incomplete_data)
        assert response.status_code == 422  # Validation error
