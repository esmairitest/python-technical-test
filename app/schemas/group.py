from typing import List, Optional

from infrastructure.models import GroupType
from pydantic import BaseModel, Field, constr
from schemas.site import SiteSummary


class GroupBase(BaseModel):
    name: constr(min_length=1)
    type: GroupType


class GroupCreate(GroupBase):
    child_groups: Optional[List[int]] = Field(default_factory=list)
    sites: Optional[List[int]] = Field(default_factory=list)


class GroupUpdate(BaseModel):
    name: str | None = None
    type: GroupType | None = None
    child_groups: Optional[List[int]] = Field(default_factory=list)
    sites: Optional[List[int]] = Field(default_factory=list)

    @classmethod
    def validate_one_field(cls, values):
        if not any(
            [
                values.get("name"),
                values.get("type"),
                values.get("child_groups"),
                values.get("sites"),
            ]
        ):
            raise ValueError("At least one field must be provided to update the group.")
        return values


class GroupSummary(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class GroupOut(GroupBase):
    id: int
    child_groups: List[GroupSummary] | None = None
    sites: List[SiteSummary] | None = None

    model_config = {"from_attributes": True}


GroupOut.model_rebuild()
