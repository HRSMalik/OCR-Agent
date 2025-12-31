from schema_engine import json_schema_to_pydantic
from ocr import upload_file, extract, delete_file
from schema_guard import validate_schema
from validator import validate

async def run_agent(schema: dict, files: list):
    validate_schema(schema)

    Model = json_schema_to_pydantic(schema)
    uploaded_files = []
    try:
        for file in files:
            uploaded = await upload_file(file)
            uploaded_files.append(uploaded)

        ai_output = await extract(Model, uploaded_files)

        return validate(Model, ai_output)

    finally:
        for f in uploaded_files:
            delete_file(f["file_id"])
