# pdf-plan-enhancer Windows-EXE

Diese Variante startet die komplette Anwendung lokal auf dem eigenen Rechner.
Die Verarbeitung bleibt lokal; PDFs und Bilder werden nicht in eine Cloud hochgeladen.

## Start

1. ZIP entpacken.
2. Den entpackten Ordner zusammenlassen. Der Ordner `_internal` muss neben der EXE bleiben.
3. `pdf-plan-enhancer.exe` doppelklicken.
4. Der Browser oeffnet sich automatisch.

Falls der Standard-Port bereits belegt ist, nimmt die App automatisch den naechsten freien lokalen Port.

## An Taskleiste anheften

Am einfachsten:

1. `pdf-plan-enhancer.exe` starten.
2. Unten in der Windows-Taskleiste mit Rechtsklick auf das Programmsymbol klicken.
3. `An Taskleiste anheften` waehlen.

Alternativ kann auch direkt im entpackten Ordner per Rechtsklick auf die EXE angeheftet werden, falls Windows diese Option anzeigt.

## Voraussetzungen

- Windows
- Fuer Bilddateien: keine weitere Installation noetig.
- Fuer PDF-Rendering: Poppler muss vorhanden sein.

Die App sucht Poppler zuerst neben der Anwendung und danach unter:

```text
C:\Program Files\poppler\Library\bin
```

Falls Poppler mitgeliefert werden soll, kann dieser Ordner neben die EXE gelegt werden:

```text
pdf-plan-enhancer-windows/
|-- pdf-plan-enhancer.exe
|-- _internal/
`-- poppler/
    `-- Library/
        `-- bin/
```

## Hinweise

- Die Originaldateien werden nicht ueberschrieben.
- Exportierte Dateien werden lokal gespeichert.
- Das kleine Starterfenster darf offen bleiben. Mit `Beenden` wird auch der lokale Server geschlossen.
