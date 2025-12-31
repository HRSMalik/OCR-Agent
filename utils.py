from fastapi import UploadFile
from typing import Literal, TypedDict
from rapidfuzz import process, fuzz
from typing import Any, Dict, Iterable, List


class OpenAIFileMeta(TypedDict):
    purpose: Literal["vision", "user_data"]
    input_type: Literal["input_image", "input_file"]


def resolve_openai_file_meta(file: UploadFile) -> OpenAIFileMeta:
    """
    Decide OpenAI upload purpose AND GPT input type
    based on FastAPI UploadFile metadata.
    """
    allowed_image_exts = {"png", "jpg", "jpeg", "webp"}
    allowed_doc_exts = {"pdf", "xls", "xlsx"}
    allowed_exts = allowed_image_exts | allowed_doc_exts
    excel_mimes = {
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    if file.content_type:
        if file.content_type.startswith("image/"):
            return {"purpose": "vision", "input_type": "input_image"}
        if file.content_type == "application/pdf":
            return {"purpose": "user_data", "input_type": "input_file"}
        if file.content_type in excel_mimes:
            return {"purpose": "user_data", "input_type": "input_file"}

    if file.filename:
        parts = file.filename.lower().rsplit(".", 1)
        if len(parts) == 2 and parts[1] in allowed_exts:
            ext = parts[1]
            if ext in allowed_image_exts:
                return {"purpose": "vision", "input_type": "input_image"}
            return {"purpose": "user_data", "input_type": "input_file"}

    # If we reach here, reject unsupported types explicitly
    raise ValueError("Unsupported file type. Allowed: png, jpg, jpeg, webp, pdf, xls, xlsx")


def semantic_map(data: Any, model_class: Any, threshold: int = 70) -> Any:
    """
    Map keys in `data` (which may be nested) to the closest matching
    field names in `model_class` using rapidfuzz. Returns a new data
    structure containing only the model's fields (unmatched fields set to None).
    This attempts to recurse when nested pydantic models are detected.
    """

    def _get_field_names(cls: Any) -> List[str]:
        try:
            return list(getattr(cls, "model_fields", {}).keys())
        except Exception:
            return []

    def _get_nested_model_for_field(cls: Any, field_name: str):
        try:
            field_info = getattr(cls, "model_fields", {}).get(field_name)
            ann = None
            if field_info is None:
                return None
            # FieldInfo object may be a mapping or object; handle both
            ann = getattr(field_info, "annotation", None)
            if ann is None and isinstance(field_info, dict):
                ann = field_info.get("annotation")
            if ann and hasattr(ann, "model_fields"):
                return ann
        except Exception:
            return None

    def _map_obj(obj: Any, cls: Any):
        if obj is None:
            return None
        if not isinstance(obj, dict):
            return obj

        target_fields = _get_field_names(cls)
        if not target_fields:
            return obj

        result: Dict[str, Any] = {f: None for f in target_fields}

        for k, v in obj.items():
            best = process.extractOne(k, target_fields, scorer=fuzz.token_sort_ratio)
            if best is None:
                continue
            match, score, idx = best
            if score >= threshold:
                # attempt recursion if nested model exists for this field
                nested_model = _get_nested_model_for_field(cls, match)
                if isinstance(v, dict) and nested_model is not None:
                    result[match] = _map_obj(v, nested_model)
                elif isinstance(v, list) and nested_model is not None:
                    # map each element if it's a list of objects
                    result[match] = [_map_obj(x, nested_model) if isinstance(x, dict) else x for x in v]
                else:
                    result[match] = v

        return result

    # Start mapping at root
    return _map_obj(data, model_class)