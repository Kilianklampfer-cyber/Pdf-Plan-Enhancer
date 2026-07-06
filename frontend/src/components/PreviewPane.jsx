import { Columns2, Crop, Expand, Image as ImageIcon, Move, RotateCw } from "lucide-react";
import { useRef, useState } from "react";

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export default function PreviewPane({
  originalPreview,
  enhancedPreview,
  filename,
  page,
  pageCount,
  setPage,
  viewMode,
  setViewMode,
  split,
  setSplit,
  zoom,
  setZoom,
  pan,
  setPan,
  params,
  setParams,
  loading,
}) {
  const hasPreview = originalPreview && enhancedPreview;
  const stageRef = useRef(null);
  const imageRef = useRef(null);
  const dragRef = useRef(null);
  const [draftCrop, setDraftCrop] = useState(null);

  function updateCropFromEvent(event, commit = false) {
    const rect = imageRef.current?.getBoundingClientRect();
    if (!rect || !dragRef.current) return;

    const x = clamp((event.clientX - rect.left) / rect.width, 0, 1);
    const y = clamp((event.clientY - rect.top) / rect.height, 0, 1);
    const start = dragRef.current;
    const left = Math.min(start.x, x);
    const top = Math.min(start.y, y);
    const width = Math.abs(x - start.x);
    const height = Math.abs(y - start.y);
    const crop = { x: left, y: top, width, height };
    setDraftCrop(crop);

    if (commit && width > 0.02 && height > 0.02) {
      setParams((current) => ({ ...current, crop_enabled: true, crop_box: crop }));
    }
  }

  function handleWheel(event) {
    if (!hasPreview) return;
    event.preventDefault();
    const stage = stageRef.current?.getBoundingClientRect();
    if (!stage) return;

    const oldZoom = zoom;
    const nextZoom = clamp(oldZoom * (event.deltaY > 0 ? 0.9 : 1.1), 0.45, 5);
    const pointerX = event.clientX - stage.left - stage.width / 2;
    const pointerY = event.clientY - stage.top - stage.height / 2;
    const ratio = nextZoom / oldZoom;

    setPan({
      x: pointerX - (pointerX - pan.x) * ratio,
      y: pointerY - (pointerY - pan.y) * ratio,
    });
    setZoom(nextZoom);
  }

  function handlePointerDown(event) {
    if (!hasPreview) return;
    const rect = imageRef.current?.getBoundingClientRect();
    if (!rect) return;

    if (params.crop_enabled && event.shiftKey) {
      dragRef.current = {
        mode: "crop",
        x: clamp((event.clientX - rect.left) / rect.width, 0, 1),
        y: clamp((event.clientY - rect.top) / rect.height, 0, 1),
      };
      setDraftCrop(null);
      event.currentTarget.setPointerCapture(event.pointerId);
      return;
    }

    dragRef.current = { mode: "pan", x: event.clientX, y: event.clientY, pan: { ...pan } };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function handlePointerMove(event) {
    if (!dragRef.current) return;
    if (dragRef.current.mode === "crop") {
      updateCropFromEvent(event);
      return;
    }

    setPan({
      x: dragRef.current.pan.x + event.clientX - dragRef.current.x,
      y: dragRef.current.pan.y + event.clientY - dragRef.current.y,
    });
  }

  function handlePointerUp(event) {
    if (dragRef.current?.mode === "crop") {
      updateCropFromEvent(event, true);
    }
    dragRef.current = null;
  }

  const crop = draftCrop || params.crop_box;

  return (
    <section className="panel preview-panel">
      <div className="preview-header">
        <div>
          <span className="eyebrow">Aktuelle Datei</span>
          <h2>{filename || "Keine Datei geladen"}</h2>
        </div>
        {pageCount > 0 && (
          <div className="page-control">
            <button type="button" onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1 || loading}>
              -
            </button>
            <span>
              {page}/{pageCount}
            </span>
            <button type="button" onClick={() => setPage(Math.min(pageCount, page + 1))} disabled={page >= pageCount || loading}>
              +
            </button>
          </div>
        )}
      </div>

      <div className="preview-toolbar">
        <button type="button" className={viewMode === "split" ? "active" : ""} onClick={() => setViewMode("split")} title="Split-View">
          <Columns2 size={17} />
          Split
        </button>
        <button type="button" className={viewMode === "enhanced" ? "active" : ""} onClick={() => setViewMode("enhanced")} title="Nachher">
          <ImageIcon size={17} />
          Nachher
        </button>
        <button type="button" onClick={() => setParams((current) => ({ ...current, rotation: (current.rotation + 90) % 360 }))} title="90 Grad drehen">
          <RotateCw size={17} />
          Drehen
        </button>
        <button type="button" className={params.crop_enabled ? "active" : ""} onClick={() => setParams((current) => ({ ...current, crop_enabled: !current.crop_enabled }))} title="Manueller Zuschnitt">
          <Crop size={17} />
          Zuschnitt
        </button>
        <button
          type="button"
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
          title="Vorschau zentrieren"
        >
          <Expand size={17} />
          Einpassen
        </button>
        <span className="zoom-readout">
          <Move size={16} />
          Mausrad {Math.round(zoom * 100)}%
        </span>
      </div>

      <div
        ref={stageRef}
        className={`preview-stage ${loading ? "is-loading" : ""}`}
        onWheel={handleWheel}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        {!hasPreview && <div className="empty-preview">PDF oder Bild laden</div>}
        {hasPreview && (
          <div className="image-shell" style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}>
            {viewMode === "split" ? (
              <>
                <img ref={imageRef} src={originalPreview} alt="Originale Vorschau" draggable="false" />
                <img className="after-image" src={enhancedPreview} alt="Verbesserte Vorschau" draggable="false" style={{ clipPath: `inset(0 0 0 ${split}%)` }} />
                <div className="split-line" style={{ left: `${split}%` }} />
              </>
            ) : (
              <img ref={imageRef} src={viewMode === "original" ? originalPreview : enhancedPreview} alt="Vorschau" draggable="false" />
            )}
            {params.crop_enabled && crop && (
              <div
                className="crop-rect"
                style={{
                  left: `${crop.x * 100}%`,
                  top: `${crop.y * 100}%`,
                  width: `${crop.width * 100}%`,
                  height: `${crop.height * 100}%`,
                }}
              />
            )}
          </div>
        )}
        {loading && (
          <div className="loading-shade">
            <span>Vorschau wird aktualisiert</span>
            <i />
          </div>
        )}
      </div>

      {hasPreview && viewMode === "split" && (
        <label className="split-control">
          <span>Vorher</span>
          <input type="range" min={5} max={95} step={1} value={split} onChange={(event) => setSplit(Number(event.target.value))} />
          <span>Nachher</span>
        </label>
      )}
    </section>
  );
}
