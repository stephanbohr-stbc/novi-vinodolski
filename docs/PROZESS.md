# Prozess: So ist die Seite entstanden

Stand: 05.10.2026. Dieses Dokument beschreibt, wie die Empfehlungsseite gebaut wurde, welche Entscheidungen dahinterstecken und wie sie gepflegt wird – so, dass eine ähnliche Seite für jemand anderen in wenigen Stunden entstehen kann.

## 1. Ausgangslage

- Manu und Stephan haben im April 2026 ein Apartment in den Mövenpick Residences Kvarner Bay (Novi Vinodolski, Kroatien) reserviert.
- Der Vertrieb bietet eine Prämie je vermitteltem Käufer und erlaubt die Nutzung des Materials der Projekt-Webseite.
- Ziel der Seite: Freunden die Vorzüge zeigen, zum Gespräch einladen – und dabei offen sagen, dass es eine Prämie gibt.

## 2. Material sammeln

| Quelle | Verwendung |
|---|---|
| Factsheet des Entwicklers (PDF) | Fakten zu Resort, Ausstattung, Eigennutzungszeiten; Bilder per `pdfimages` extrahiert |
| FAQ des Entwicklers (PDF) | Vermietungsprogramm, Servicegebühr, Eigentümervorteile |
| Angebots-E-Mail des Vertriebs | Lage der Wohnung, Entfernungen, Parken |
| Eigene Fotos (Apple Fotos, iPhone) | Glaubwürdigkeit: „So sieht es dort wirklich aus" |
| Wikimedia Commons | Lizenzfreie Fotos für Orte, von denen keine eigenen Bilder da waren (Lizenz und Urheber im Seitenfuß nennen) |
| Web-Recherche | Infrastrukturpläne (Autobahn A7, Krk-Brücke), Direktflug, Ausflugsziele – immer mit Quelle verlinkt |

Technischer Fallstrick: Die PDF-Bilder waren CMYK-JPEGs mit invertierten Kanälen. Lösung: mit Pillow `ImageChops.invert()` auf dem CMYK-Bild, dann nach RGB konvertieren.

## 3. Inhalt und Dramaturgie

Reihenfolge der Abschnitte (bewährt):

1. **Hero** – ein Satz, der die Einladung trägt, plus zwei Buttons (Kontakt, Warum).
2. **Brief** – persönlich, in der Du-/Ihr-Form, mit Foto der Gastgeber.
3. **Gründe** – sechs bis sieben kurze Karten mit dem, was die Gastgeber selbst schätzen.
4. **Unsere Wahl** – das eigene Apartment, Modell der Anlage, Hinweis auf Alternativen.
5. **Umgebung** – Ausflüge mit eigenen Fotos und Buttons zu offiziellen Seiten.
6. **Eigene Fotos** – Galerie mit Datum („Stand …").
7. **Projektstand** – ehrlich: was fertig ist, was nicht, mit Terminen.
8. **Resort im Überblick** – Visualisierungen und Ausstattungsliste.
9. **Nutzung und Vermietung** – Eigennutzungszeiten, das gewählte Paket, Hinweis „Einnahmen nicht garantiert".
10. **Anreise und Region** – Zeiten, Infrastrukturpläne mit Quellen.
11. **Ganz offen gesagt** – Provision benennen, eigentliches Motiv nennen.
12. **Kontakt** – drei Schritte, Mail-Button mit vorausgefülltem Text, Telefon.
13. **Fußzeile** – Disclaimer (kein Angebot, keine Anlageberatung), Markenhinweis, Bildnachweis.

Regeln:
- Keine Preise auf der Seite.
- Hörensagen als solches kennzeichnen („haben wir gehört", „Pläne, keine Zusagen").
- Fakten aus Unterlagen nicht aufrunden; Abweichungen zwischen Dokumenten klären.
- Alle externen Links als Buttons mit sprechender Beschriftung.

## 4. Technik

- **Eine Datei:** `index.html` mit CSS und JavaScript inline. Keine Fonts oder Skripte von außen, damit die Seite auch lokal ohne Netz funktioniert.
- **Design:** Sandtöne, Meerblau, Terrakotta als Akzent; Serifenschrift für Überschriften (Systemschriften).
- **Mehrsprachigkeit:** Jedes übersetzbare Element trägt `data-en="…"` mit dem englischen Text. Ein kleines Skript tauscht `innerHTML` beim Umschalten, merkt die Wahl in `localStorage` und liest `?lang=en` aus dem Link. Erweiterbar auf weitere Sprachen (`data-hr`, `data-sl`, `data-hu`).
- **Feste Kopfleiste:** `position: fixed`, bekommt ab 80 px Scrollweg einen festen Hintergrund, damit der Kontakt-Button immer sichtbar ist.
- **Entwurfsmodus:** `<body class="entwurf">` blendet gelbe „Noch prüfen"-Hinweise (`<i class="pruefen">`) und eine Fußleiste ein. `deploy.sh` entfernt beides beim Veröffentlichen.
- **Fotos:** auf max. 1800 px Kante und JPEG-Qualität 80–82 verkleinert (`sips`), damit die Seite schnell lädt.
- **noindex:** Meta-Tag, damit Suchmaschinen die Seite nicht listen (sie ist für Freunde gedacht, nicht für die Öffentlichkeit).

## 5. Qualitätssicherung

- Screenshots mit Chrome headless (`--headless=new --screenshot --window-size=1280,…`), in Streifen geschnitten und geprüft: Desktop deutsch, Desktop englisch (`?lang=en`), Mobil (500 px).
- Nach jedem Deploy: Live-URL und Stichproben-Bilder per `curl` abfragen (HTTP 200), neuen Text im HTML suchen.

## 6. Hosting

- Öffentliches GitHub-Repo, GitHub Pages aus `main` (Wurzelverzeichnis). Kostenlos, kein Build.
- Anlegen: `gh repo create <konto>/<name> --public --source=. --push`, dann `gh api -X POST repos/<konto>/<name>/pages -f "source[branch]=main" -f "source[path]=/"`.
- Bewusst öffentlich: Fotos, E-Mail und Telefonnummer sind im Repo sichtbar. Wer das nicht will, braucht ein privates Repo mit Pages (kostenpflichtiger Plan) oder einen anderen Host.

## 7. Pflege

- Quelle bleibt der Drive-Ordner; das Repo ist nur die Veröffentlichungskopie.
- `deploy.sh "Beschreibung"` veröffentlicht; Änderungen in `docs/AENDERUNGEN.md` eintragen.
- Wünsche als GitHub-Issues erfassen, damit nichts verloren geht und Entscheidungen nachvollziehbar bleiben.

## 8. Für die nächste Seite

Der Skill `freunde-empfehlungsseite` in Stephans Claude-Umgebung führt durch genau diesen Ablauf: Material einsammeln, Inhalt nach obiger Dramaturgie schreiben, Seite aus diesem Repo als Vorlage ableiten, prüfen, veröffentlichen.
