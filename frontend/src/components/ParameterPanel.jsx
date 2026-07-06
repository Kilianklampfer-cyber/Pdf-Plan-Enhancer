import { Crop, RotateCcw, RotateCw, SlidersHorizontal } from "lucide-react";
import { useState } from "react";
import { defaultParams, presets } from "../presets";

function RangeControl({ label, value, min, max, step, onChange }) {
  return (
    <label className="range-control">
      <span>
        {label}
        <b>{Number(value).toFixed(step < 1 ? 2 : 0)}</b>
      </span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="toggle">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

const tabs = [
  { id: "presets", label: "Presets" },
  { id: "image", label: "Bild" },
  { id: "output", label: "Ausgabe" },
  { id: "crop", label: "Zuschnitt" },
];

export default function ParameterPanel({ params, setParams, loading }) {
  const [activeTab, setActiveTab] = useState("presets");
  const update = (key, value) => setParams((current) => ({ ...current, [key]: value }));
  const applyPreset = (name) => setParams((current) => ({ ...current, ...presets[name] }));
  const rotateRight = () => update("rotation", (params.rotation + 90) % 360);

  return (
    <section className="panel controls-panel">
      <div className="panel-title">
        <SlidersHorizontal size={18} />
        <h2>Parameter</h2>
        {loading && <span className="mini-status">Vorschau</span>}
      </div>

      <div className="parameter-tabs" role="tablist">
        {tabs.map((tab) => (
          <button key={tab.id} type="button" className={activeTab === tab.id ? "active" : ""} onClick={() => setActiveTab(tab.id)}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "presets" && (
        <div className="preset-grid compact">
          {Object.keys(presets).map((name) => (
            <button key={name} type="button" className="preset-button" onClick={() => applyPreset(name)}>
              {name}
            </button>
          ))}
        </div>
      )}

      {activeTab === "image" && (
        <div className="control-stack compact">
          <RangeControl label="Kontrast" value={params.contrast} min={0.5} max={3} step={0.05} onChange={(value) => update("contrast", value)} />
          <RangeControl label="Helligkeit" value={params.brightness} min={0.5} max={1.8} step={0.02} onChange={(value) => update("brightness", value)} />
          <RangeControl label="Gamma" value={params.gamma} min={0.4} max={2.5} step={0.02} onChange={(value) => update("gamma", value)} />
          <RangeControl label="Schärfen" value={params.sharpen} min={0} max={3} step={0.05} onChange={(value) => update("sharpen", value)} />
          <RangeControl label="Rauschen" value={params.denoise} min={0} max={3} step={0.05} onChange={(value) => update("denoise", value)} />
          <RangeControl label="Kanten" value={params.edge_boost} min={0} max={3} step={0.05} onChange={(value) => update("edge_boost", value)} />
        </div>
      )}

      {activeTab === "output" && (
        <>
          <div className="control-stack compact">
            <RangeControl label="Linien" value={params.line_thicken} min={0} max={4} step={1} onChange={(value) => update("line_thicken", value)} />
            <RangeControl label="Lücken" value={params.morph_close} min={0} max={4} step={1} onChange={(value) => update("morph_close", value)} />
            <RangeControl label="SW-Schwelle" value={params.threshold_value} min={0} max={255} step={1} onChange={(value) => update("threshold_value", value)} />
            <RangeControl label="Export-DPI" value={params.export_dpi} min={150} max={600} step={25} onChange={(value) => update("export_dpi", value)} />
          </div>
          <div className="toggle-grid compact">
            <Toggle label="Graustufen" checked={params.grayscale} onChange={(value) => update("grayscale", value)} />
            <Toggle label="Schwarz-Weiß" checked={params.threshold_enabled} onChange={(value) => update("threshold_enabled", value)} />
            <Toggle label="Adaptive Schwelle" checked={params.adaptive_threshold} onChange={(value) => update("adaptive_threshold", value)} />
            <Toggle label="Invertieren" checked={params.invert} onChange={(value) => update("invert", value)} />
          </div>
        </>
      )}

      {activeTab === "crop" && (
        <div className="crop-tools">
          <button type="button" className="secondary-button" onClick={rotateRight}>
            <RotateCw size={17} />
            90° drehen
          </button>
          <button type="button" className="secondary-button" onClick={() => update("crop_box", null)}>
            <Crop size={17} />
            Rahmen löschen
          </button>
          <Toggle label="Manuellen Zuschnitt anwenden" checked={params.crop_enabled} onChange={(value) => update("crop_enabled", value)} />
          <Toggle label="Weiße Ränder automatisch schneiden" checked={params.auto_crop} onChange={(value) => update("auto_crop", value)} />
          <p className="hint-text">Für manuellen Zuschnitt im Vorschaufenster einen Rahmen aufziehen. Rotation und Zuschnitt werden beim Export angewendet.</p>
        </div>
      )}

      <div className="panel-actions single">
        <button type="button" className="secondary-button" onClick={() => setParams(defaultParams)}>
          <RotateCcw size={17} />
          Zurücksetzen
        </button>
      </div>
    </section>
  );
}
