from ocr.schema_engine import json_schema_to_pydantic
from ocr.agent import upload_file, extract, delete_file
from ocr.schema_guard import validate_schema
from ocr.validator import validate
from ocr.utils import semantic_map
import asyncio


async def run_agent(schema: dict, files: list):
    validate_schema(schema)

    Model = json_schema_to_pydantic(schema)
    uploaded_files = []
    try:
        async def _upload_with_context(f):
            try:
                return await upload_file(f)
            except Exception as e:
                name = getattr(f, "filename", "<unknown>")
                raise ValueError(f"Failed to upload {name}: {e}") from e

        tasks = [asyncio.create_task(_upload_with_context(f)) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                raise r
            uploaded_files.append(r)

        ai_output = await extract(Model, uploaded_files)

        mapped = semantic_map(ai_output, Model)

        return validate(Model, mapped)

    finally:
        for f in uploaded_files:
            delete_file(f["file_id"])
