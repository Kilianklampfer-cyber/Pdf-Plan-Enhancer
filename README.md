# pdf-plan-enhancer

Lokales Web-Tool zur Verbesserung eingescannter Bestandspläne. Die App ist für alte, blasse Papierpläne gedacht, die anschließend in CAD/Civil 3D nachgezeichnet oder als klare Planvorlage hinterlegt werden.

## Funktionen

- React + Vite Frontend mit Drag-&-Drop Upload
- FastAPI Backend mit modularer Bild- und PDF-Verarbeitung
- Vorschau der ersten oder ausgewählten PDF-Seite
- Vorher/Nachher-Vergleich als Split-View
- Export der kompletten verbesserten PDF
- Batchmodus für mehrere PDFs als ZIP-Export
- Presets für typische Scan-Probleme
- Lokaler Betrieb ohne Cloud-Abhängigkeit

## Projektstruktur

```text
pdf_contrast_flask/
├── backend/
│   ├── main.py
│   ├── enhancer.py
│   ├── pdf_utils.py
│   ├── schemas.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       ├── presets.js
│       ├── styles.css
│       └── components/
└── README.md
```

## Voraussetzungen

- Python 3.10 oder neuer
- Node.js 18 oder neuer
- Poppler für `pdf2image`

Unter Windows Poppler installieren und den `bin`-Ordner als Umgebungsvariable setzen, zum Beispiel:

```powershell
$env:POPPLER_PATH="C:\Program Files\poppler\Library\bin"
```

Alternativ kann der Poppler-Ordner dauerhaft in den Windows-`PATH` aufgenommen werden.

## Backend starten

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Die API läuft dann unter `http://127.0.0.1:8000`.

## Frontend starten

In einem zweiten Terminal:

```powershell
cd frontend
npm install
npm run dev
```

Das Frontend läuft standardmäßig unter `http://127.0.0.1:5173`.

Alternativ mit `pnpm`:

```powershell
cd frontend
pnpm install
pnpm run dev
```

Falls das Backend auf einem anderen Port läuft:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000/api"
npm run dev
```

## Verarbeitung

Die Original-PDF wird im lokalen Backend-Arbeitsordner gespeichert und nicht überschrieben. Für die Vorschau rendert das Backend nur die angeforderte Seite. Beim Export werden alle Seiten mit denselben Parametern verarbeitet und als neue PDF ausgegeben.

Wichtige Schritte in `backend/enhancer.py`:

- Kontrast, Helligkeit und Gamma für blasse Scans
- Rauschreduzierung gegen Papier- und Scannerartefakte
- Schärfen und Kantenverstärkung für Maßzahlen und Konturen
- Globale oder adaptive Schwarz-Weiß-Schwelle für CAD-Hinterlegung
- Linienverdickung und morphologisches Schließen für dünne oder unterbrochene Linien

Temporäre Arbeitsdaten liegen unter `backend/.workspace/` und werden beim Upload automatisch nach Alter bereinigt.

## API-Endpunkte

- `POST /api/upload`: eine PDF hochladen
- `POST /api/batch-upload`: mehrere PDFs hochladen
- `POST /api/preview`: einzelne Vorschauseite mit Parametern rendern
- `POST /api/export`: komplette verbesserte PDF exportieren
- `POST /api/batch-export`: mehrere verbesserte PDFs als ZIP exportieren
- `GET /api/health`: einfacher Statuscheck

## Presets

- Blasser Bestandsplan
- Maßketten lesbarer
- Dünne Linien verstärken
- Schwarz-Weiß CAD-Vorlage
- Schonende Verbesserung

Die Presets sind Startwerte. Für schwierige Altpläne lohnt sich meist ein vorsichtiges Zusammenspiel aus Kontrast, Gamma, Kantenverstärkung und geringer Linienverdickung.
