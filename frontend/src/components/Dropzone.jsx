import { UploadCloud } from "lucide-react";
import { useRef, useState } from "react";

const ACCEPTED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"];

export default function Dropzone({ disabled, multiple, onFiles }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  function handleFiles(fileList) {
    const files = Array.from(fileList || []).filter((file) =>
      ACCEPTED_EXTENSIONS.some((extension) => file.name.toLowerCase().endsWith(extension)),
    );
    if (files.length) onFiles(files);
  }

  return (
    <div
      className={`dropzone ${isDragging ? "is-dragging" : ""} ${disabled ? "is-disabled" : ""}`}
      onDragEnter={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setIsDragging(false);
        if (!disabled) handleFiles(event.dataTransfer.files);
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if ((event.key === "Enter" || event.key === " ") && !disabled) inputRef.current?.click();
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,image/*,.pdf,.jpg,.jpeg,.png,.tif,.tiff,.bmp,.webp"
        multiple={multiple}
        disabled={disabled}
        onChange={(event) => handleFiles(event.target.files)}
      />
      <UploadCloud size={28} />
      <div>
        <strong>{multiple ? "Dateien ablegen" : "PDF oder Bild ablegen"}</strong>
        <span>{multiple ? "PDFs, Pläne, Luftbilder" : "Scan, Orthofoto oder GIS-Export"}</span>
      </div>
    </div>
  );
}
