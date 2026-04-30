from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class ElasticRule:
    id: str
    name: str
    enabled: bool
    schedule_interval: str
    condition: str
    canal: Optional[str] = None
    severity: Optional[str] = None
    namespace: Optional[str] = None
    description: Optional[str] = None
    microservice: Optional[str] = None
    environment: Optional[str] = None
    rule_type: Optional[str] = None