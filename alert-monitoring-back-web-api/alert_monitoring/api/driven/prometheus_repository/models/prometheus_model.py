from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class PrometheusRule:
    alert: str
    expr: str
    labels: Dict[str, Any] = field(default_factory = dict)
    annotations: Dict[str, Any] = field(default_factory = dict)
    group_name: str = ""