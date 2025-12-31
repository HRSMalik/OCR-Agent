from pydantic import ValidationError

def validate(model, data: dict):
    parsed = model.model_validate(data)
    return parsed.model_dump(
        mode="json",
        exclude_none=False,
        exclude_unset=False
    )
