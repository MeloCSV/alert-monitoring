from typing import Optional
from sqlmodel import SQLModel, Field


class AlertOverrideDB(SQLModel, table=True):
    __tablename__ = "alert_overrides"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    alert_name: str = Field(index=True)
    solution: str = Field(index=True)
    is_disabled: bool = Field(default=False)
    is_partial: bool = Field(default=False)
