from pydantic import BaseModel, Field
from typing import List, Optional


class KibanaRule(BaseModel):
    rule_id: str = Field(..., description="ID de la regla en Kibana")
    name: str = Field(..., description="Nombre de la regla")
    enabled: bool = Field(default=False, description="Si la regla está habilitada en Kibana")
    tags: List[str] = Field(default_factory=list, description="Tags de la regla")
    schedule_interval: Optional[str] = Field(None, description="Intervalo de ejecución (e.g. 1m, 2m)")
    severity: Optional[str] = Field(None, description="Severidad inferida de las acciones")
    notification_channels: List[str] = Field(default_factory=list, description="Canales de notificación inferidos de las acciones")
    apis: List[str] = Field(default_factory=list, description="APIs a las que aplica la regla (extraídas del KQL o termField)")
    is_global: bool = Field(default=False, description="True si la regla no aplica a una API concreta")
    last_execution_date: Optional[str] = Field(None, description="Última fecha de ejecución reportada por Kibana")
    last_execution_status: Optional[str] = Field(None, description="Estado de la última ejecución")
    kibana_url: Optional[str] = Field(None, description="Enlace directo a la regla en Kibana")
    kibana_name: Optional[str] = Field(None, description="Nombre del Kibana del que proviene la regla")
