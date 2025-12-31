from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
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

    try:
        data = await run_agent(schema_dict, files)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "data": None, "errors": [{"type": "ValueError", "message": str(e)}]},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "data": None, "errors": [{"type": type(e).__name__, "message": str(e)}]},
        )

    return JSONResponse(status_code=200, content={"status": "success", "data": data, "errors": []})