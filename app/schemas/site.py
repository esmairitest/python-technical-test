from datetime import date
from typing import Annotated, List, Literal, Optional

from pydantic import BaseModel, Field, constr, model_validator


class BaseSite(BaseModel):
    name: constr(min_length=1)
    installation_date: date
    max_power_megawatt: float
    min_power_megawatt: float
    country: constr(min_length=1)
    groups: Optional[List[int]] = Field(default_factory=list)


class SiteCreate(BaseSite):
    useful_energy_at_1_megawatt: Optional[float] = None
    efficiency: Optional[float] = None

    @model_validator(mode="after")
    def validate_country_fields(self) -> "SiteCreate":
        if self.country == "fr":
            if self.efficiency is not None:
                raise ValueError("Field 'efficiency' is not allowed when country is 'fr'")
            if self.useful_energy_at_1_megawatt is None:
                raise ValueError(
                    "Field 'useful_energy_at_1_megawatt' is required when country is 'fr'"
                )
        elif self.country == "it":
            if self.useful_energy_at_1_megawatt is not None:
                raise ValueError(
                    "Field 'useful_energy_at_1_megawatt' is not allowed when country is 'it'"
                )
            if self.efficiency is None:
                raise ValueError("Field 'efficiency' is required when country is 'it'")
        return self


class SiteUpdate(BaseModel):
    name: str | None = None
    installation_date: date | None = None
    max_power_megawatt: float | None = None
    min_power_megawatt: float | None = None
    country: str | None = None
    useful_energy_at_1_megawatt: float | None = None
    efficiency: float | None = None
    groups: list[int] | None = None


class SiteSummary(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class FrenchSiteOut(BaseSite):
    id: int
    groups: list[SiteSummary] | None = None
    country: Literal["fr"] = "fr"
    useful_energy_at_1_megawatt: float
    model_config = {"from_attributes": True}


class ItalianSiteOut(BaseSite):
    id: int
    groups: list[SiteSummary] | None = None
    efficiency: float
    country: Literal["it"] = "it"

    model_config = {"from_attributes": True}


SiteOut = Annotated[FrenchSiteOut | ItalianSiteOut, Field(discriminator="country")]
