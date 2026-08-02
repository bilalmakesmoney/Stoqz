# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class UploadResponse(BaseModel):
    message: str
    rows_imported: int
    products_found: int
    date_range: dict[str, str] | None = None


class ValidationError(BaseModel):
    row: int | None = None
    field: str
    message: str


class UploadErrorResponse(BaseModel):
    message: str
    errors: list[ValidationError]