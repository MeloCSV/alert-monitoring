from typing import Optional
from sqlmodel import SQLModel, Field


class CatalogAppDB(SQLModel, table=True):
    __tablename__ = "catalog_apps"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    object_id: str = Field(unique=True)
    name: str = Field(index=True)
    csw_code: Optional[str] = Field(default=None)
