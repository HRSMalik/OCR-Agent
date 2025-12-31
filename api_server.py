from fastapi import FastAPI, UploadFile, File, Form
import json
from orchestrator import run_agent

app = FastAPI()

@app.post("/ai/parse")
async def parse(
    schema: UploadFile = File(...),
    files: list[UploadFile] = File(...)
):
    schema_content = await schema.read()
    schema_dict = json.loads(schema_content)

    data = await run_agent(schema_dict, files)

    return {
        "status": "success",
        "data": data,
        "errors": []
    }