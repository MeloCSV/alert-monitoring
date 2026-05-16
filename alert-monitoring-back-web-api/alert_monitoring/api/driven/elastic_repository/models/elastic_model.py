from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ElasticRule:
    id: str
    name: str
    enabled: bool
    schedule_interval: str
    condition: str
    rule_type: Optional[str] = None
    canals: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    environments: List[str] = field(default_factory=list)
