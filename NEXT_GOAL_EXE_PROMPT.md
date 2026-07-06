# Nächstes Ziel: pdf-plan-enhancer als Windows-EXE/Installer

Ziel ist, aus der aktuellen lokalen Download-Version eine nutzerfreundliche Windows-Anwendung zu machen.

## Ausgangspunkt

- Aktuelle lokale App liegt unter `pdf-plan-enhancer-local-download/`.
- React ist bereits statisch gebaut und wird vom FastAPI-Backend ausgeliefert.
- Start funktioniert aktuell über `start-pdf-plan-enhancer.bat`.
- Die App öffnet lokal im Browser unter einem freien Port, bevorzugt `http://127.0.0.1:8765`.

## Gewünschter nächster Stand

1. Eine portable Windows-EXE erstellen:
   - Datei z.B. `pdf-plan-enhancer.exe`.
   - Doppelklick startet das lokale Backend.
   - Browser öffnet automatisch die lokale App.
   - Nutzer muss keine `.bat` mehr starten.

2. Möglichst wenig Voraussetzungen beim Nutzer:
   - Python möglichst bündeln oder klar prüfen.
   - Poppler entweder mitliefern oder verständlich melden, wenn es fehlt.
   - Fehlermeldungen nutzerfreundlich anzeigen.

3. Optional danach echter Installer:
   - `pdf-plan-enhancer-setup.exe`.
   - Desktop-Verknüpfung.
   - Startmenü-Eintrag.
   - Installation nach `%LOCALAPPDATA%\pdf-plan-enhancer`.

## Technische Richtung

- Aktuelle Architektur beibehalten:
  - FastAPI Backend
  - statisches React Frontend in `app/backend/static`
  - lokale PDF-Verarbeitung mit Pillow, OpenCV, pdf2image, img2pdf

- Zuerst portable EXE testen, z.B. mit PyInstaller:
  - Launcher-Python-Skript erstellen.
  - Backend-Prozess starten.
  - Browser öffnen.
  - App-Dateien und Backend mit in die Distribution packen.

## Wichtig

- Keine Online-PDF-Verarbeitung.
- PDFs bleiben lokal.
- Die Downloadseite soll später nur die EXE/ZIP anbieten.
- Aktuelle ZIP-Variante darf als Fallback bestehen bleiben.

---

# Änderungswünsche für die nächste UI-/Funktionsrunde

Stand der Oberfläche laut Screenshot:

- Aktuell helles technisches UI mit linker Upload-/Parameter-Spalte und rechter Vorschau.
- Rechts ist bei normalem Browserzoom noch vertikales Scrollen nötig.
- Die Parameterliste ist zu lang für komfortables Arbeiten ohne Scrollen.
- Manuelle Vorschauaktualisierung ist aktuell noch ein Button.

Gewünschte Designrichtung:

- Farbschema an das Laabmayr-Logo anlehnen, aber ohne Logo in der App.
- Primärfarben:
  - helles bis mittleres Grau/Blaugrau für Typografie und Flächen
  - dunkles Anthrazit/Grüngrau für Kontraste
  - tiefes Rot als Akzentfarbe
  - sehr heller, fast weißer Hintergrund
- Das Tool soll weiterhin technisch, ruhig und arbeitsorientiert wirken.

## Gewünschte Funktionsänderungen

1. Zuschnitt
   - Manuelle Zuschnittfunktion für Seiten/Bilder.
   - Optional automatische Funktion zum Entfernen weißer Ränder.
   - Zuschnitt soll beim Export optional angewendet werden.

2. Bild- und Orthofoto-Unterstützung
   - Neben PDFs sollen auch Bilder verarbeitet werden können.
   - Ziel: Luftbilder, Orthofotos, GIS-Exporte und normale Bilddateien.
   - Verarbeitung grundsätzlich ähnlich wie PDF-Seiten.
   - Eigene Presets für Bilder/Orthofotos prüfen.

3. Rotation
   - PDF-Seiten und Bilder sollen gedreht werden können.
   - 90-Grad-Schritte reichen.
   - Rotation soll in Vorschau und Export berücksichtigt werden.

4. Drag & Drop
   - Drag & Drop muss erhalten bleiben bzw. sauber für PDFs und Bilder funktionieren.

5. Infobox
   - Kleine Info-Schaltfläche mit `i` links oben neben dem Titel.
   - Bei Klick öffnet sich eine kompakte Erklärung:
     - Bedienung
     - Buttons
     - Vorschau
     - Export
     - Presets

6. Exportziel und Überschreiben
   - Wunsch: Beim Export Zielordner wählen.
   - Optional Ausgangsdatei überschreiben.
   - Mehrere Dateien bzw. ganzer Ordner mit gleichen Enhancements schnell verarbeiten.
   - Hinweis: In einer Browser-Web-App ist freies Schreiben in beliebige lokale Ordner eingeschränkt. Für die spätere EXE-/Desktop-Version ist das deutlich realistischer.

7. CAD-artiger Zoom
   - Zoom nicht über Slider.
   - Mausradzoom in der Vorschau.
   - Zoom soll auf Mausposition zentriert sein.
   - Pan/verschieben der Ansicht sollte wahrscheinlich ergänzt werden.

8. Automatische Vorschauaktualisierung
   - Kein manueller Button ganz unten.
   - Parameteränderungen sollen automatisch eine Vorschau auslösen.
   - Bei kurzer Verarbeitung direkt aktualisieren.
   - Bei längerer Verarbeitung Ladebalken/Statushinweis zeigen.
   - Debounce/Abbruch alter Vorschauanfragen einplanen, damit Sliderbewegungen nicht zu viele Requests erzeugen.

9. Layout ohne vertikales Scrollen bei 100 Prozent Zoom
   - Oberfläche soll auf üblichen PC-Bildschirmen bei 100 Prozent Browserzoom in ein Fenster passen.
   - Kein Scrollen nach unten für wichtige Bedienung.
   - Wenn Platz knapp ist:
     - Reiter/Tabs für Parametergruppen
     - einklappbare Bereiche
     - kompaktere Controls
     - Export/Dateiaktionen als feste Toolbar

## Einschätzung zur Umsetzung

Diese Änderungsrunde ist größer als reines Styling. Sie betrifft:

- Frontend-Layout und Interaktion
- Backend-Schema für neue Parameter
- Bildverarbeitungspipeline
- Exportlogik
- spätere Desktop-/EXE-Fähigkeiten

Sinnvolle Reihenfolge:

1. UI-Layout und Farbschema umbauen.
2. Automatische Vorschau mit Ladezustand einbauen.
3. Zoom/Pan wie CAD umsetzen.
4. Rotation ergänzen.
5. Bild-Upload ergänzen.
6. Zuschnitt und Auto-Randentfernung ergänzen.
7. Batch-/Ordner-/Zielpfadfunktionen für Desktop-EXE planen und danach umsetzen.
