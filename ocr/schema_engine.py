from pydantic import BaseModel, create_model
from typing import Any, Dict, List, Optional

def map_json_type(schema: dict, nullable: bool):
    t = schema.get("type")

    if t == "array":
        item_schema = schema["items"]
        item_type = map_json_type(item_schema, nullable=False)
        return Optional[List[item_type]] if nullable else List[item_type]

    if t == "object":
        return json_schema_to_pydantic(schema)

    if t == "string":
        return Optional[str] if nullable else str

    if t == "number":
        return Optional[float] if nullable else float

    if t == "integer":
        return Optional[int] if nullable else int

    if t == "boolean":
        return Optional[bool] if nullable else bool

    return Optional[str]


def json_schema_to_pydantic(schema: Dict[str, Any]) -> type[BaseModel]:
    fields = {}
    required = set(schema.get("required", []))
    properties = schema.get("properties", {})

    for field_name, field_schema in properties.items():
        is_required = field_name in required
        python_type = map_json_type(field_schema, nullable=not is_required)
        default = ... if is_required else None
        fields[field_name] = (python_type, default)

    return create_model(schema.get("title", "DynamicModel"), **fields)
