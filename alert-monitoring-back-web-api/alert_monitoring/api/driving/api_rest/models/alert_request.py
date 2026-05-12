from pydantic import BaseModel
    
class ElasticUploadRequest(BaseModel):
    json_content: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "json_content": "{\"page\": 1, \"per_page\": 10, \"total\": 1, \"data\": []}"
                }
            ]
        }
    }