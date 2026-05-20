from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class PrometheusRule:
    alert: str
    expr: str
    labels: Dict[str, Any] = field(default_factory=dict)
    annotations: Dict[str, Any] = field(default_factory=dict)
    group_name: str = ""
    cluster_name: str = ""
    rule_file: str = ""