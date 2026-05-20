from typing import List, Optional

from pydantic import BaseModel, Field


class DefaultAlert(BaseModel):
    raw_name: str = Field(..., description="Nombre original en Prometheus (e.g. Default_Service_Status_KO)")
    display_name: str = Field(..., description="Nombre legible para la UI")
    raw_description: Optional[str] = Field(None, description="Mensaje de anotación original del fichero Prometheus")
    display_description: Optional[str] = Field(None, description="Descripción traducida para la UI")
    severity: Optional[str] = Field(None)
    notification_channel: Optional[str] = Field(None)
    excluded_namespaces: List[str] = Field(default_factory=list)
    included_namespaces: List[str] = Field(default_factory=list)
    excluded_jobs: List[str] = Field(default_factory=list)
