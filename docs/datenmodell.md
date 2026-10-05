# Datenmodell einer Empfehlungsseite (Issue #3, Punkt 1)

Stand: 05.10.2026. Das Modell beschreibt, welche Daten eine Empfehlungsseite braucht, damit sie aus einem Formular (Issue #3) erzeugt werden kann statt von Hand. Es ist aus der Novi-Vinodolski-Seite abgeleitet: jedes Feld entspricht einem Element, das dort tatsächlich vorkommt.

- Formale Definition: [`schema/seite.schema.json`](schema/seite.schema.json) (JSON Schema, Draft 2020-12)
- Ausgefülltes Beispiel: [`schema/novi.beispiel.json`](schema/novi.beispiel.json) (die Novi-Seite, gekürzt, validiert gegen das Schema)

## Grundsätze

1. **Eine Seite = ein JSON-Dokument.** Bilder liegen daneben im Ordner `bilder/`; das JSON verweist nur auf Dateinamen.
2. **Alle sichtbaren Texte sind mehrsprachig.** Ein Textfeld ist ein Objekt mit Sprachcodes als Schlüssel (`{"de": "…", "en": "…"}`). Die Standardsprache ist Pflicht; fehlende Übersetzungen fallen darauf zurück. Neue Sprachen (Issue #1: `hr`, `sl`, `hu`) brauchen keine Strukturänderung.
3. **Abschnitte sind optional, wo es inhaltlich passt.** Pflicht sind nur Kopf, Brief, Gründe, eigene Fotos, Kontakt und Fußzeile. Projektstand, Nutzung/Vermietung, Umgebung und Anreise entfallen, wenn sie nicht zutreffen.
4. **Jedes Bild kennt seine Herkunft** (`eigen`, `anbieter`, `commons`). Daraus folgen automatisch die Kennzeichnung „Visualisierung" und der Bildnachweis im Fuß.
5. **Jeder Link hat eine Beschriftung und eine Art** (`offiziell`, `quelle`, `bericht`) – so werden Buttons statt nackter Adressen erzeugt und Belege bleiben als solche erkennbar.
6. **Pflichtsätze bleiben im Modell verankert:** Hinweis „Einnahmen nicht garantiert" (`nutzung.hinweis`), Disclaimer (`fuss.disclaimer`), Offenlegung der Prämie (`objekt.praemie_offenlegen` + `offen.zitat`).

## Die Blöcke im Überblick

| Block | Zweck | Pflicht |
|---|---|---|
| `meta` | Kennung, Sprachen, Stand, Status, **Laufzeit** (`gueltig_bis`, Issue #4), Suchmaschinen ja/nein | ja |
| `gastgeber` | Anzeigename, Anrede (du/ihr/sie), Kontakt (Mail, Telefon, Mail-Vorlage je Sprache), Foto | ja |
| `objekt` | Projekt, Ort, Anbieter, Marke, Material-Genehmigung, Prämie offenlegen, Kurzbeschreibung | ja |
| `hero` | Titel, Untertitel, Bild, zwei Buttons | ja |
| `brief` | Anrede, 1–6 Absätze, Unterschrift | ja |
| `gruende` | 3–8 Karten, eine davon hervorhebbar | ja |
| `eigenes_objekt` | Einleitung, Merkmale, Bild, Modell/Lageplan, Hinweis | nein |
| `umgebung` | Ausflüge mit bis zu 3 Bildern, Links, Layout | nein |
| `fotos` | Eigene Fotos mit Titel, Text, Kachelgröße, Bildausschnitt | ja |
| `projektstand` | Zeitleiste (fertig/bald/offen), Fazit | nein |
| `ueberblick` | Anbieter-Galerie, Ausstattungsliste | nein |
| `nutzung` | Saisons, Fazit, gewähltes Paket, Pflichthinweis | nein |
| `anreise` | Wege, Hinweis, Links, Region mit Quellen | nein |
| `offen` | Prämien-Offenlegung und eigentliches Motiv | empfohlen |
| `kontakt` | Titel, Text, 2–4 Schritte, Bild, **Formular statt Mail** (Anbindung Issue #2) | ja |
| `fuss` | Disclaimer, Bildnachweis | ja |
| `vereinbarung` | **Konditionen für Seiten Dritter** (Issue #5): Version, Beträge, Laufzeit, Bestätigung mit Zeitstempel | nur bei Fremdseiten |

## Was das Modell bewusst nicht enthält

- **Preise des Objekts** – gehören nicht auf die Seite.
- **Daten der Interessenten** – das ist die Kontaktverwaltung (Issue #2, eigenes Konzept in `konzept-kontaktverwaltung.md`). Die Seite kennt nur ihre eigene Kennung (`meta.slug`), über die Anfragen zugeordnet werden.
- **Gestaltung** – Farben, Schriften und Raster bleiben in der Vorlage. Das Formular ändert Inhalt, nicht Design.

## Nächste Schritte in Issue #3

1. Generator: `erzeuge-seite.py <seite.json> <ausgabeordner>` baut aus den Daten die `index.html` nach der Vorlage (Platzhalter in der Vorlage ↔ Felder im Schema).
2. Formular, das genau dieses JSON befüllt und Bilder hochlädt.
3. Bearbeitungs-Link mit Zugangscode, Veröffentlichung je Seite.
