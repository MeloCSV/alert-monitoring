from typing import Optional, List
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON

class DefaultAlertRuleDB(SQLModel, table=True):
    __tablename__ = "default_alert_catalog"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    cluster: str = Field(index=True)
    name: str = Field(index=True)
    display_name: str
    description: str
    severity: str
    condition: str
    environments: List[str] = Field(default=[], sa_column=Column(JSON))
    notification_channel: Optional[str] = None
    solution: Optional[str] = None
