from typing import List, Optional

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class DefaultAlertApiDB(SQLModel, table=True):
    __tablename__ = "default_alert_api"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    raw_name: str = Field(unique=True)
    display_name: str
    raw_description: Optional[str] = Field(default=None)
    display_description: Optional[str] = Field(default=None)
    severity: Optional[str] = Field(default=None)
    notification_channel: Optional[str] = Field(default=None)
    excluded_apis: List[str] = Field(default=[], sa_column=Column(JSON))
