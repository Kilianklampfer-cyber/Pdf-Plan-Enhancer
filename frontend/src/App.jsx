import { Download, FileText, FolderOpen, Info, RefreshCcw, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { exportBatch, exportPdf, requestPreview, uploadBatch, uploadPdf } from "./api";
import Dropzone from "./components/Dropzone";
import ModeTabs from "./components/ModeTabs";
import ParameterPanel from "./components/ParameterPanel";
import PreviewPane from "./components/PreviewPane";
import { defaultParams, presets } from "./presets";

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

async function writeBlobToDirectory(directoryHandle, filename, blob) {
  const handle = await directoryHandle.getFileHandle(filename, { create: true });
  const writable = await handle.createWritable();
  await writable.write(blob);
  await writable.close();
}

export default function App() {
  const [params, setParams] = useState(defaultParams);
  const [activeMode, setActiveMode] = useState("readability");
  const [fileId, setFileId] = useState("");
  const [filename, setFilename] = useState("");
  const [documents, setDocuments] = useState([]);
  const [page, setPage] = useState(1);
  const [pageCount, setPageCount] = useState(0);
  const [originalPreview, setOriginalPreview] = useState("");
  const [enhancedPreview, setEnhancedPreview] = useState("");
  const [viewMode, setViewMode] = useState("split");
  const [split, setSplit] = useState(50);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");
  const [infoOpen, setInfoOpen] = useState(false);
  const [directoryHandle, setDirectoryHandle] = useState(null);
  const [overwriteNames, setOverwriteNames] = useState(false);
  const requestId = useRef(0);

  function exportName(document) {
    const extension = document.export_extension || (document.kind === "image" ? "png" : "pdf");
    const stem = document.filename.replace(/\.[^.]+$/i, "") || "plan";
    return overwriteNames ? `${stem}.${extension}` : `${stem}_enhanced.${extension}`;
  }

  function applyMode(mode) {
    setActiveMode(mode);
    if (mode === "cad") {
      setParams((current) => ({ ...current, ...presets["Schwarz-Weiß CAD-Vorlage"], mode: "cad" }));
    } else if (mode === "detail") {
      setParams((current) => ({ ...current, mode: "detail", contrast: 1.55, gamma: 0.88, sharpen: 1.5, edge_boost: 1.2 }));
      setZoom(1.55);
    } else if (mode === "image") {
      setParams((current) => ({ ...current, ...presets["Orthofoto klarer"], mode: "image" }));
    } else if (mode === "readability") {
      setParams((current) => ({ ...current, mode: "readability" }));
    }
  }

  async function handleFiles(files) {
    setError("");
    setLoading(true);
    setPage(1);
    setPan({ x: 0, y: 0 });
    setZoom(1);

    try {
      if (activeMode === "batch" || files.length > 1) {
        const result = await uploadBatch(files);
        const first = result.documents[0];
        setDocuments(result.documents);
        setFileId(first.file_id);
        setFilename(first.filename);
        setPageCount(first.page_count);
        setOriginalPreview(result.original_preview || "");
        setEnhancedPreview(result.enhanced_preview || "");
      } else {
        const result = await uploadPdf(files[0]);
        setDocuments([
          {
            file_id: result.file_id,
            filename: result.filename,
            page_count: result.page_count,
            kind: result.kind,
            export_extension: result.export_extension,
          },
        ]);
        setFileId(result.file_id);
        setFilename(result.filename);
        setPageCount(result.page_count);
        setOriginalPreview(result.original_preview);
        setEnhancedPreview(result.enhanced_preview);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function updatePreview(targetFileId = fileId, targetPage = page) {
    if (!targetFileId) return;
    const id = requestId.current + 1;
    requestId.current = id;
    setError("");
    setLoading(true);

    try {
      const result = await requestPreview(targetFileId, targetPage, params);
      if (requestId.current !== id) return;
      setFileId(result.file_id);
      setFilename(result.filename);
      setPage(result.page);
      setPageCount(result.page_count);
      setOriginalPreview(result.original_preview);
      setEnhancedPreview(result.enhanced_preview);
      setDocuments((current) =>
        current.map((document) =>
          document.file_id === result.file_id
            ? { ...document, kind: result.kind, export_extension: result.export_extension, page_count: result.page_count }
            : document,
        ),
      );
    } catch (err) {
      if (requestId.current === id) setError(err.message);
    } finally {
      if (requestId.current === id) setLoading(false);
    }
  }

  async function chooseDirectory() {
    if (!window.showDirectoryPicker) {
      setError("Zielordnerwahl wird in diesem Browser nicht unterstützt. In Chrome/Edge auf localhost funktioniert sie normalerweise.");
      return;
    }
    const handle = await window.showDirectoryPicker({ mode: "readwrite" });
    setDirectoryHandle(handle);
  }

  async function handleExport() {
    if (!fileId) return;
    setError("");
    setExporting(true);

    try {
      if (directoryHandle) {
        const targets = activeMode === "batch" && documents.length > 1 ? documents : documents.filter((document) => document.file_id === fileId);
        for (const document of targets) {
          const blob = await exportPdf(document.file_id, params);
          await writeBlobToDirectory(directoryHandle, exportName(document), blob);
        }
        return;
      }

      if (activeMode === "batch" && documents.length > 1) {
        const blob = await exportBatch(
          documents.map((document) => document.file_id),
          params,
        );
        downloadBlob(blob, "pdf_plan_enhancer_batch.zip");
      } else {
        const current = documents.find((document) => document.file_id === fileId) || { filename, kind: "pdf", export_extension: "pdf" };
        const blob = await exportPdf(fileId, params);
        downloadBlob(blob, exportName(current));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setExporting(false);
    }
  }

  useEffect(() => {
    if (!fileId) return;
    const timer = window.setTimeout(() => updatePreview(fileId, page), 420);
    return () => window.clearTimeout(timer);
  }, [fileId, page, JSON.stringify(params)]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="title-row">
          <button type="button" className="info-button" onClick={() => setInfoOpen(true)} title="Bedienhinweise">
            <Info size={18} />
          </button>
          <div>
            <span className="product-label">pdf-plan-enhancer</span>
            <h1>Planaufbereitung</h1>
          </div>
        </div>
        <ModeTabs activeMode={activeMode} onChange={applyMode} />
      </header>

      <div className="workspace-grid">
        <aside className="left-column">
          <section className="panel upload-panel">
            <Dropzone disabled={loading || exporting} multiple={activeMode === "batch"} onFiles={handleFiles} />
            {documents.length > 0 && (
              <div className="file-list">
                {documents.map((document) => (
                  <button
                    key={document.file_id}
                    type="button"
                    className={document.file_id === fileId ? "active" : ""}
                    onClick={() => {
                      setFileId(document.file_id);
                      setFilename(document.filename);
                      setPageCount(document.page_count);
                      setPage(1);
                      setPan({ x: 0, y: 0 });
                      updatePreview(document.file_id, 1);
                    }}
                  >
                    <FileText size={16} />
                    <span>{document.filename}</span>
                    <small>{document.kind === "image" ? "Bild" : `${document.page_count} S.`}</small>
                  </button>
                ))}
              </div>
            )}
            <div className="export-options">
              <button type="button" className="secondary-button" onClick={chooseDirectory}>
                <FolderOpen size={17} />
                {directoryHandle ? directoryHandle.name : "Zielordner"}
              </button>
              <label className="toggle inline">
                <input type="checkbox" checked={overwriteNames} onChange={(event) => setOverwriteNames(event.target.checked)} />
                <span>Namen überschreiben</span>
              </label>
            </div>
            <div className="export-row">
              <button type="button" className="primary-button" disabled={!fileId || loading || exporting} onClick={handleExport}>
                {exporting ? <RefreshCcw size={17} className="spin" /> : <Download size={17} />}
                Exportieren
              </button>
            </div>
            {error && <div className="error-box">{error}</div>}
          </section>

          <ParameterPanel params={params} setParams={setParams} loading={loading} />
        </aside>

        <PreviewPane
          originalPreview={originalPreview}
          enhancedPreview={enhancedPreview}
          filename={filename}
          page={page}
          pageCount={pageCount}
          setPage={setPage}
          viewMode={viewMode}
          setViewMode={setViewMode}
          split={split}
          setSplit={setSplit}
          zoom={zoom}
          setZoom={setZoom}
          pan={pan}
          setPan={setPan}
          params={params}
          setParams={setParams}
          loading={loading}
        />
      </div>

      {infoOpen && (
        <div className="modal-backdrop" onClick={() => setInfoOpen(false)}>
          <section className="info-modal" onClick={(event) => event.stopPropagation()}>
            <button type="button" className="modal-close" onClick={() => setInfoOpen(false)} title="Schließen">
              <X size={18} />
            </button>
            <h2>Bedienung</h2>
            <div className="help-grid">
              <article>
                <h3>Dateien</h3>
                <p>PDFs, gescannte Pläne, JPG/PNG/TIFF/WebP, Luftbilder und GIS-Exporte per Drag & Drop ablegen. Im Batchmodus können mehrere Dateien mit denselben Einstellungen verarbeitet werden.</p>
              </article>
              <article>
                <h3>Modi</h3>
                <p>Lesbarkeit verbessert blasse Pläne farbschonend. CAD-Hinterlegung ist für klare schwarz-weiße Vorlagen. Detail ist für starkes Nachschärfen. Bild/Orthofoto hält Farbe bewusst erhalten. Batch verarbeitet mehrere Dateien.</p>
              </article>
              <article>
                <h3>Presets und Parameter</h3>
                <p>Presets setzen Startwerte. Parameter aktualisieren die Vorschau automatisch. Farbe bleibt erhalten, solange Graustufen, Schwarz-Weiß oder CAD-Vorlage nicht aktiv sind.</p>
              </article>
              <article>
                <h3>Vorschau</h3>
                <p>Split zeigt Vorher/Nachher. Nachher zeigt nur das Ergebnis. Drehen rotiert in 90-Grad-Schritten. Einpassen zentriert die Ansicht und setzt den Zoom zurück.</p>
              </article>
              <article>
                <h3>Zoom und Zuschnitt</h3>
                <p>Mausrad zoomt auf die Mausposition. Ziehen verschiebt die Ansicht. Für manuellen Zuschnitt Zuschnitt aktivieren und mit gedrückter Shift-Taste einen Rahmen aufziehen.</p>
              </article>
              <article>
                <h3>Export</h3>
                <p>Ohne Zielordner landet die Ausgabe im Browser-Download. Mit Zielordner kann Chrome/Edge auf localhost direkt in einen Ordner schreiben. Namen überschreiben nutzt den Originalnamen statt _enhanced.</p>
              </article>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
