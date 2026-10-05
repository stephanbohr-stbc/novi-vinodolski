# Generator

`erzeuge-seite.py` baut aus einer `seite.json` (Schema: `../docs/schema/seite.schema.json`) die fertige `index.html` im Design der Novi-Vinodolski-Seite.

```
# mit Schemaprüfung
uv run --quiet --with jsonschema python generator/erzeuge-seite.py docs/schema/novi.beispiel.json /pfad/ausgabe --pruefen

# ohne Prüfung (nur Python 3, keine Pakete)
python3 generator/erzeuge-seite.py meine-seite.json /pfad/ausgabe
```

- Der Ausgabeordner braucht daneben den Ordner `bilder/` mit allen im JSON genannten Dateien; fehlende Bilder meldet das Skript.
- `vorlage.css` ist das Design (aus der Novi-Seite übernommen). Änderungen am Aussehen passieren dort, nicht im JSON.
- Sprachen: alle aus `meta.sprachen` (de, en, hr, sl, hu). Die Oberflächentexte (Buttons, Abschnittslabels) liegen im Skript (`UI`), die Inhalte im JSON. Fehlende Übersetzungen fallen auf die Standardsprache zurück.
- Laufzeit: Ist `meta.gueltig_bis` überschritten, zeigt die Seite nur den Ablauf-Hinweis (`meta.ablauf_hinweis` oder Standardtext).
- Mehrsprachige Texte dürfen `**fett**` und Zeilenumbrüche enthalten; sonst wird HTML maskiert.

Prüfen nach dem Erzeugen: `~/.claude/skills/freunde-empfehlungsseite/scripts/seite-pruefen.sh <ausgabe>/index.html <screenshot-ordner>`.
