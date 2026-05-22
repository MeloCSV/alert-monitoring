from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class KibanaRuleDB(SQLModel, table=True):
    __tablename__ = "kibana_rules"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: str = Field(index=True)
    name: str
    enabled: bool = Field(default=False)
    tags: List[str] = Field(default=[], sa_column=Column(JSON))
    schedule_interval: Optional[str] = None
    severity: Optional[str] = None
    notification_channels: List[str] = Field(default=[], sa_column=Column(JSON))
    apis: List[str] = Field(default=[], sa_column=Column(JSON))
    is_global: bool = Field(default=False, index=True)
    last_execution_date: Optional[datetime] = None
    last_execution_status: Optional[str] = None
    kibana_url: Optional[str] = None
    kibana_name: Optional[str] = None
    message: Optional[str] = None
