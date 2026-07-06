from __future__ import annotations

import base64
import json
import os
import shutil
import time
import uuid
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Iterable, List

import img2pdf
from fastapi import UploadFile
from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image, ImageChops

from enhancer import enhance_image
from schemas import EnhancementParams


BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = Path(os.getenv("PDF_PLAN_ENHANCER_WORKSPACE", BASE_DIR / ".workspace"))
DOCUMENTS_DIR = WORKSPACE_DIR / "documents"
EXPORTS_DIR = WORKSPACE_DIR / "exports"
MAX_SESSION_AGE_SECONDS = 24 * 60 * 60
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def ensure_workspace() -> None:
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _poppler_path() -> str | None:
    value = os.getenv("POPPLER_PATH") or os.getenv("PDF_PLAN_ENHANCER_POPPLER_PATH")
    return value or None


def cleanup_old_sessions(max_age_seconds: int = MAX_SESSION_AGE_SECONDS) -> None:
    ensure_workspace()
    cutoff = time.time() - max_age_seconds
    for root in (DOCUMENTS_DIR, EXPORTS_DIR):
        for item in root.iterdir():
            try:
                if item.stat().st_mtime < cutoff:
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink(missing_ok=True)
            except OSError:
                continue


def _extension(filename: str) -> str:
    return Path(filename or "").suffix.lower()


def _kind_for_filename(filename: str) -> str:
    ext = _extension(filename)
    if ext in PDF_EXTENSIONS:
        return "pdf"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    raise ValueError("Bitte eine PDF- oder Bilddatei hochladen.")


def validate_upload(file: UploadFile) -> str:
    filename = file.filename or ""
    return _kind_for_filename(filename)


def _safe_filename(filename: str) -> str:
    keep = [c for c in filename if c.isalnum() or c in (" ", ".", "-", "_")]
    cleaned = "".join(keep).strip()
    return cleaned or "scan.pdf"


def save_upload(file: UploadFile, batch_id: str | None = None) -> dict:
    kind = validate_upload(file)
    ensure_workspace()
    cleanup_old_sessions()

    file_id = str(uuid.uuid4())
    doc_dir = DOCUMENTS_DIR / file_id
    doc_dir.mkdir(parents=True, exist_ok=False)
    ext = _extension(file.filename or "")
    source_path = doc_dir / f"original{ext}"

    with source_path.open("wb") as target:
        shutil.copyfileobj(file.file, target)

    page_count = count_pages(source_path) if kind == "pdf" else 1
    metadata = {
        "file_id": file_id,
        "filename": _safe_filename(file.filename or "scan.pdf"),
        "kind": kind,
        "extension": ext,
        "export_extension": "pdf" if kind == "pdf" else "png",
        "page_count": page_count,
        "batch_id": batch_id,
        "created_at": time.time(),
    }
    (doc_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    metadata["path"] = source_path
    metadata["dir"] = doc_dir
    return metadata


def get_document(file_id: str) -> dict:
    doc_dir = DOCUMENTS_DIR / file_id
    metadata_path = doc_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError("Die Datei wurde nicht gefunden. Bitte erneut hochladen.")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    source_path = doc_dir / f"original{metadata.get('extension', '.pdf')}"
    if not source_path.exists():
        raise FileNotFoundError("Die Datei wurde nicht gefunden. Bitte erneut hochladen.")
    metadata["path"] = source_path
    metadata["dir"] = doc_dir
    return metadata


def count_pages(pdf_path: Path) -> int:
    info = pdfinfo_from_path(str(pdf_path), poppler_path=_poppler_path())
    return int(info.get("Pages", 1))


def render_page(pdf_path: Path, page: int, dpi: int) -> Image.Image:
    if pdf_path.suffix.lower() in IMAGE_EXTENSIONS:
        with Image.open(pdf_path) as image:
            return image.convert("RGB").copy()

    images = convert_from_path(
        str(pdf_path),
        dpi=dpi,
        first_page=page,
        last_page=page,
        fmt="ppm",
        poppler_path=_poppler_path(),
    )
    if not images:
        raise ValueError("Die PDF-Seite konnte nicht gerendert werden.")
    return images[0]


def render_all_pages(pdf_path: Path, dpi: int) -> List[Image.Image]:
    if pdf_path.suffix.lower() in IMAGE_EXTENSIONS:
        return [render_page(pdf_path, 1, dpi)]

    images = convert_from_path(str(pdf_path), dpi=dpi, fmt="ppm", poppler_path=_poppler_path())
    if not images:
        raise ValueError("Die PDF-Datei enthält keine renderbaren Seiten.")
    return images


def image_to_data_url(image: Image.Image, format_name: str = "JPEG") -> str:
    buffer = BytesIO()
    image.save(buffer, format=format_name, quality=88)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    mime = "image/jpeg" if format_name.upper() == "JPEG" else "image/png"
    return f"data:{mime};base64,{encoded}"


def _rotate_image(image: Image.Image, rotation: int) -> Image.Image:
    normalized = rotation % 360
    if normalized == 90:
        return image.transpose(Image.Transpose.ROTATE_270)
    if normalized == 180:
        return image.transpose(Image.Transpose.ROTATE_180)
    if normalized == 270:
        return image.transpose(Image.Transpose.ROTATE_90)
    return image


def _auto_crop_white_margin(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, (255, 255, 255))
    diff = ImageChops.difference(rgb, background).convert("L")
    mask = diff.point(lambda pixel: 255 if pixel > 12 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return image

    left, top, right, bottom = bbox
    pad = max(8, int(min(rgb.size) * 0.01))
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(rgb.width, right + pad)
    bottom = min(rgb.height, bottom + pad)

    if right - left < 20 or bottom - top < 20:
        return image
    return image.crop((left, top, right, bottom))


def _manual_crop(image: Image.Image, params: EnhancementParams) -> Image.Image:
    if not params.crop_enabled or not params.crop_box:
        return image

    box = params.crop_box
    left = int(image.width * box.x)
    top = int(image.height * box.y)
    right = int(image.width * min(1.0, box.x + box.width))
    bottom = int(image.height * min(1.0, box.y + box.height))

    if right - left < 20 or bottom - top < 20:
        return image
    return image.crop((left, top, right, bottom))


def prepare_image(image: Image.Image, params: EnhancementParams) -> Image.Image:
    prepared = _rotate_image(image.convert("RGB"), params.rotation)
    prepared = _manual_crop(prepared, params)
    if params.auto_crop:
        prepared = _auto_crop_white_margin(prepared)
    return prepared


def preview_pair(file_id: str, page: int, params: EnhancementParams) -> dict:
    doc = get_document(file_id)
    page = min(page, int(doc["page_count"]))
    original = prepare_image(render_page(doc["path"], page, params.preview_dpi), params)
    enhanced = enhance_image(original, params)
    return {
        "file_id": file_id,
        "filename": doc["filename"],
        "kind": doc.get("kind", "pdf"),
        "export_extension": doc.get("export_extension", "pdf"),
        "page": page,
        "page_count": doc["page_count"],
        "original_preview": image_to_data_url(original),
        "enhanced_preview": image_to_data_url(enhanced),
    }


def export_enhanced_document(file_id: str, params: EnhancementParams) -> Path:
    doc = get_document(file_id)
    output_dir = EXPORTS_DIR / file_id
    output_dir.mkdir(parents=True, exist_ok=True)

    if doc.get("kind") == "image":
        output_image = output_dir / f"{Path(doc['filename']).stem}_enhanced.png"
        source = prepare_image(render_page(doc["path"], 1, params.export_dpi), params)
        enhance_image(source, params).save(output_image, "PNG", optimize=True)
        return output_image

    output_pdf = output_dir / f"{Path(doc['filename']).stem}_enhanced.pdf"
    page_dir = output_dir / f"pages_{uuid.uuid4().hex}"
    page_dir.mkdir(parents=True, exist_ok=True)
    page_paths: list[Path] = []

    try:
        for index, page in enumerate(render_all_pages(doc["path"], params.export_dpi), start=1):
            processed = enhance_image(prepare_image(page, params), params)
            page_path = page_dir / f"page_{index:04d}.png"
            processed.save(page_path, "PNG", optimize=True)
            page_paths.append(page_path)

        with output_pdf.open("wb") as target:
            target.write(img2pdf.convert([str(path) for path in page_paths]))
    finally:
        shutil.rmtree(page_dir, ignore_errors=True)

    return output_pdf


def export_enhanced_pdf(file_id: str, params: EnhancementParams) -> Path:
    return export_enhanced_document(file_id, params)


def export_batch_zip(file_ids: Iterable[str], params: EnhancementParams) -> Path:
    ensure_workspace()
    batch_export_id = str(uuid.uuid4())
    zip_path = EXPORTS_DIR / f"pdf_plan_enhancer_batch_{batch_export_id}.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_id in file_ids:
            doc = get_document(file_id)
            output_path = export_enhanced_document(file_id, params)
            archive.write(output_path, arcname=output_path.name)

    return zip_path
