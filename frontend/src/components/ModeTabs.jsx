import { Image, Layers, Maximize, Rows3, ScanLine } from "lucide-react";
import { modes } from "../presets";

const icons = {
  readability: ScanLine,
  cad: Layers,
  detail: Maximize,
  image: Image,
  batch: Rows3,
};

export default function ModeTabs({ activeMode, onChange }) {
  return (
    <div className="mode-tabs" aria-label="Modus">
      {modes.map((mode) => {
        const Icon = icons[mode.id];
        return (
          <button
            key={mode.id}
            type="button"
            className={activeMode === mode.id ? "active" : ""}
            onClick={() => onChange(mode.id)}
            title={mode.label}
          >
            <Icon size={17} />
            <span>{mode.label}</span>
          </button>
        );
      })}
    </div>
  );
}
