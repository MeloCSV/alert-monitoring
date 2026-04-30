from pydantic import BaseModel

class AlertUploadRequest(BaseModel):
    yaml_content: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "yaml_content": "spec:\n  groups:\n  - name: example\n    rules:\n    - alert: ExampleAlert\n      expr: up == 0"
                }
            ]
        }
    }
    
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