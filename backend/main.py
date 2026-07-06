from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from enhancer import enhance_image
from pdf_utils import export_batch_zip, export_enhanced_pdf, image_to_data_url, preview_pair, render_page, save_upload
from schemas import (
    BatchExportRequest,
    BatchUploadResponse,
    EnhancementParams,
    ExportRequest,
    PreviewRequest,
    UploadResponse,
    UploadedDocument,
)


app = FastAPI(title="pdf-plan-enhancer", version="1.0.0")
STATIC_DIR = Path(__file__).resolve().parent / "static"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PRESETS: dict[str, EnhancementParams] = {
    "Blasser Bestandsplan": EnhancementParams(contrast=1.65, brightness=1.06, gamma=0.86, sharpen=0.8, denoise=0.5, edge_boost=0.8),
    "Maßketten lesbarer": EnhancementParams(contrast=1.75, brightness=1.0, gamma=0.82, sharpen=1.2, grayscale=False, edge_boost=1.2, line_thicken=1),
    "Dünne Linien verstärken": EnhancementParams(contrast=1.5, brightness=1.0, gamma=0.92, sharpen=1.0, grayscale=False, edge_boost=1.0, line_thicken=2, morph_close=1),
    "Schwarz-Weiß CAD-Vorlage": EnhancementParams(mode="cad", contrast=1.9, brightness=1.04, gamma=0.95, sharpen=0.7, grayscale=True, adaptive_threshold=True, denoise=0.7, line_thicken=1, morph_close=1),
    "Schonende Verbesserung": EnhancementParams(contrast=1.25, brightness=1.02, gamma=0.95, sharpen=0.4, grayscale=False, denoise=0.3, edge_boost=0.3),
}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"app": "pdf-plan-enhancer", "frontend": "http://127.0.0.1:5173", "health": "http://127.0.0.1:8000/api/health"}


@app.get("/api/presets")
def presets() -> dict:
    return {name: params.dict() for name, params in PRESETS.items()}


@app.post("/api/upload", response_model=UploadResponse)
def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    try:
        metadata = save_upload(file)
        params = EnhancementParams()
        original = render_page(metadata["path"], page=1, dpi=params.preview_dpi)
        enhanced = enhance_image(original, params)
        return UploadResponse(
            file_id=metadata["file_id"],
            filename=metadata["filename"],
            kind=metadata["kind"],
            export_extension=metadata["export_extension"],
            page_count=metadata["page_count"],
            original_preview=image_to_data_url(original),
            enhanced_preview=image_to_data_url(enhanced),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload oder PDF-Rendering fehlgeschlagen: {exc}") from exc


@app.post("/api/batch-upload", response_model=BatchUploadResponse)
def upload_batch(files: list[UploadFile] = File(...)) -> BatchUploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Bitte mindestens eine PDF-Datei auswählen.")

    batch_id = str(uuid.uuid4())
    documents: list[UploadedDocument] = []
    first_metadata = None

    try:
        for file in files:
            metadata = save_upload(file, batch_id=batch_id)
            first_metadata = first_metadata or metadata
            documents.append(
                UploadedDocument(
                    file_id=metadata["file_id"],
                    filename=metadata["filename"],
                    kind=metadata["kind"],
                    export_extension=metadata["export_extension"],
                    page_count=metadata["page_count"],
                )
            )

        original_preview = None
        enhanced_preview = None
        if first_metadata:
            params = EnhancementParams()
            original = render_page(first_metadata["path"], page=1, dpi=params.preview_dpi)
            enhanced = enhance_image(original, params)
            original_preview = image_to_data_url(original)
            enhanced_preview = image_to_data_url(enhanced)

        return BatchUploadResponse(
            batch_id=batch_id,
            documents=documents,
            original_preview=original_preview,
            enhanced_preview=enhanced_preview,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Batch-Upload fehlgeschlagen: {exc}") from exc


@app.post("/api/preview")
def preview(request: PreviewRequest) -> dict:
    try:
        return preview_pair(request.file_id, request.page, request.params)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vorschau konnte nicht erzeugt werden: {exc}") from exc


@app.post("/api/export")
def export_pdf(request: ExportRequest) -> FileResponse:
    try:
        output_path = export_enhanced_pdf(request.file_id, request.params)
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=output_path.name,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF-Export fehlgeschlagen: {exc}") from exc


@app.post("/api/batch-export")
def export_batch(request: BatchExportRequest) -> FileResponse:
    try:
        output_path = export_batch_zip(request.file_ids, request.params)
        return FileResponse(
            output_path,
            media_type="application/zip",
            filename=output_path.name,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Batch-Export fehlgeschlagen: {exc}") from exc


if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
