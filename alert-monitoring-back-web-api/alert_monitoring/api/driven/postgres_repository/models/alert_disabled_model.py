from typing import List, Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class AlertDisabledDB(SQLModel, table=True):
    __tablename__ = "alert_disabled"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    alert_name: str = Field(index=True)
    solution: str = Field(index=True)
    is_disabled: bool = Field(default=False)
    is_partial: bool = Field(default=False)
    excluded_items: List[str] = Field(default=[], sa_column=Column(JSON))
