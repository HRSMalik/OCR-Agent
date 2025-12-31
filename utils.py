from fastapi import UploadFile
from typing import Literal, TypedDict


class OpenAIFileMeta(TypedDict):
    purpose: Literal["vision", "user_data"]
    input_type: Literal["input_image", "input_file"]


def resolve_openai_file_meta(file: UploadFile) -> OpenAIFileMeta:
    """
    Decide OpenAI upload purpose AND GPT input type
    based on FastAPI UploadFile metadata.
    """

    if file.content_type and file.content_type.startswith("image/"):
        return {
            "purpose": "vision",
            "input_type": "input_image"
        }

    if file.filename:
        ext = file.filename.lower().rsplit(".", 1)
        if len(ext) == 2 and ext[1] in {"png", "jpg", "jpeg", "webp"}:
            return {
                "purpose": "vision",
                "input_type": "input_image"
            }
    return {
        "purpose": "user_data",
        "input_type": "input_file"
    }