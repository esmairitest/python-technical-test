from typing import ClassVar

from infrastructure.db import Base
from sqlalchemy import Column, Date, Enum, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from .enums import GroupType

group_group_association = Table(
    "group_group_association",
    Base.metadata,
    Column("parent_group_id", Integer, ForeignKey("groups.id"), primary_key=True),
    Column("child_group_id", Integer, ForeignKey("groups.id"), primary_key=True),
)
# Association table for many-to-many between sites and groups
site_group_association = Table(
    "site_group_association",
    Base.metadata,
    Column("site_id", Integer, ForeignKey("sites.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id"), primary_key=True),
)


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(GroupType), nullable=False)

    sites = relationship("Site", secondary=site_group_association, back_populates="groups")
    child_groups = relationship(
        "Group",
        secondary=group_group_association,
        primaryjoin=id == group_group_association.c.parent_group_id,
        secondaryjoin=id == group_group_association.c.child_group_id,
        lazy="selectin",
        cascade="all",
    )


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    installation_date = Column(Date, nullable=False)
    max_power_megawatt = Column(Float, nullable=False)
    min_power_megawatt = Column(Float, nullable=False)
    country = Column(String, nullable=False)

    __mapper_args__: ClassVar[dict] = {
        "polymorphic_on": "country",
        "polymorphic_identity": "generic",
    }

    groups = relationship(
        Group, secondary=site_group_association, back_populates="sites", lazy="selectin"
    )


class FrenchSite(Site):
    __tablename__ = "french_sites"
    id = Column(Integer, ForeignKey("sites.id"), primary_key=True)
    useful_energy_at_1_megawatt = Column(Float)

    __mapper_args__: ClassVar[dict] = {"polymorphic_identity": "fr"}


class ItalianSite(Site):
    __tablename__ = "italian_sites"

    id = Column(Integer, ForeignKey("sites.id"), primary_key=True)
    efficiency = Column(Float, nullable=False)

    __mapper_args__: ClassVar[dict] = {"polymorphic_identity": "it"}
