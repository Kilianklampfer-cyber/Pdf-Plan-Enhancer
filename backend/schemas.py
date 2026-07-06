from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class ProcessingMode(str, Enum):
    readability = "readability"
    cad = "cad"
    detail = "detail"
    image = "image"


class DocumentKind(str, Enum):
    pdf = "pdf"
    image = "image"


class CropBox(BaseModel):
    x: float = Field(default=0.0, ge=0.0, le=1.0)
    y: float = Field(default=0.0, ge=0.0, le=1.0)
    width: float = Field(default=1.0, gt=0.0, le=1.0)
    height: float = Field(default=1.0, gt=0.0, le=1.0)


class EnhancementParams(BaseModel):
    mode: ProcessingMode = ProcessingMode.readability
    contrast: float = Field(default=1.25, ge=0.5, le=3.0)
    brightness: float = Field(default=1.0, ge=0.5, le=1.8)
    gamma: float = Field(default=1.0, ge=0.4, le=2.5)
    sharpen: float = Field(default=0.6, ge=0.0, le=3.0)
    grayscale: bool = False
    threshold_enabled: bool = False
    threshold_value: int = Field(default=168, ge=0, le=255)
    adaptive_threshold: bool = False
    denoise: float = Field(default=0.4, ge=0.0, le=3.0)
    edge_boost: float = Field(default=0.5, ge=0.0, le=3.0)
    line_thicken: int = Field(default=0, ge=0, le=4)
    morph_close: int = Field(default=0, ge=0, le=4)
    invert: bool = False
    rotation: int = Field(default=0, ge=0, le=270)
    crop_enabled: bool = False
    auto_crop: bool = False
    crop_box: CropBox | None = None
    preview_dpi: int = Field(default=150, ge=72, le=250)
    export_dpi: int = Field(default=300, ge=150, le=600)


class PreviewRequest(BaseModel):
    file_id: str = Field(min_length=8)
    page: int = Field(default=1, ge=1)
    params: EnhancementParams = Field(default_factory=EnhancementParams)


class ExportRequest(BaseModel):
    file_id: str = Field(min_length=8)
    params: EnhancementParams = Field(default_factory=EnhancementParams)


class BatchExportRequest(BaseModel):
    file_ids: List[str] = Field(min_length=1)
    params: EnhancementParams = Field(default_factory=EnhancementParams)


class UploadedDocument(BaseModel):
    file_id: str
    filename: str
    page_count: int
    kind: DocumentKind = DocumentKind.pdf
    export_extension: str = "pdf"


class UploadResponse(UploadedDocument):
    original_preview: str
    enhanced_preview: str


class BatchUploadResponse(BaseModel):
    batch_id: str
    documents: List[UploadedDocument]
    original_preview: str | None = None
    enhanced_preview: str | None = None
