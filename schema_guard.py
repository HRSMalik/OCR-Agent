ALLOWED_SCHEMA_TYPES = {"string", "number", "integer", "boolean", "object", "array", "null"}

def validate_schema(schema: dict):
    if schema.get("type") != "object":
        raise ValueError("Root schema must be an object")

    def walk(node):
        if "type" in node:
            types = node["type"] if isinstance(node["type"], list) else [node["type"]]
            for t in types:
                if t not in ALLOWED_SCHEMA_TYPES:
                    raise ValueError(f"Unsupported type: {t}")
        for key in ("oneOf", "anyOf", "allOf"):
            if key in node:
                raise ValueError(f"{key} is not supported")

        if "type" in node and "object" in (node["type"] if isinstance(node["type"], list) else [node["type"]]):
            for v in node.get("properties", {}).values():
                walk(v)

        if "type" in node and "array" in (node["type"] if isinstance(node["type"], list) else [node["type"]]):
            walk(node["items"])

    walk(schema)
