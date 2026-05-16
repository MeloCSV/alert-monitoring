from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ClusterConfig:
    name: str
    host: str
    token: str
    namespace: str = "prometheus"
    ca_cert: Optional[str] = None
    verify_ssl: bool = True