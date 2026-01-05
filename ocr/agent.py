from openai import OpenAI
from fastapi import UploadFile
from ocr.utils import resolve_openai_file_meta
import json
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()

async def upload_file(file: UploadFile) -> dict:
    meta = resolve_openai_file_meta(file)
    file_bytes = await file.read()

    uploaded = client.files.create(
        file=(file.filename, file_bytes),
        purpose=meta["purpose"] 
    )

    return {
        "file_id": uploaded.id,
        "input_type": meta["input_type"]
    }

SYSTEM_PROMPT = """
You are a document intelligence agent.
Extract only information present in the document.
Follow the schema strictly.
Return JSON only.
"""

USER_PROMPT = """Return ONLY valid JSON matching the given model exactly.

STRICT RULES:
- Use ONLY the fields defined in the model.
- Do NOT invent new fields.
- If a document key is semantically equivalent to a model field,
- You MUST map it to the closest matching field.
- If a field is similar add the same value to it example if the field is "date" and the document has "document date" use that value for "date"
  

SEMANTIC MAPPING RULES:
- Map "date", "document date", or "invoice date" → DocumentDate
- Map "invoice no", "inv no", or "document no" → VendorInvoiceNo
- Map "vendor no", "supplier id" → BuyFromVendorNo
- Map "no" or "number" → No
- Map address-like fields to the closest matching address field
- Prefer populated fields over leaving values null

If a value exists in the document but the exact field name does not,
you MUST place it in the closest semantic field.

If no reasonable semantic match exists, set the field to null.

If a field is missing, return null.
"""

async def extract(schema_model, uploaded_files: list[dict]) -> dict:
    """
    uploaded_files = [
      { "file_id": "...", "input_type": "input_image" | "input_file" }
    ]
    """
    file = uploaded_files[0]

    response = client.responses.parse(
        model="gpt-4o",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": file["input_type"], "file_id": file["file_id"]},
                    {
                        "type": "input_text",
                        "text": (
                            USER_PROMPT
                        )
                    }
                ]
            }
        ],
        text_format=schema_model,
    )

    return json.loads(response.output_text)


def delete_file(file_id: str):
    delete_status = client.files.delete(file_id)
    print(f"File deleted: {delete_status.deleted}")

