from pydantic import BaseModel


class AtlassianAssetsConfig(BaseModel):
    workspace_id: str
    base_url: str
    email: str
    token: str
    object_type_id: str
    page_size: int = 100
    verify_ssl: bool = True
