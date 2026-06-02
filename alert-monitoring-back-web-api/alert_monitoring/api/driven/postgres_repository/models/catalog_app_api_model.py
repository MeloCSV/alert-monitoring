from typing import List, Optional

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class CatalogAppApiDB(SQLModel, table=True):
    __tablename__ = "catalog_app_api"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    app: str = Field(index=True)
    microservice: str = Field(unique=True)
    apis: List[str] = Field(default=[], sa_column=Column(JSON))
