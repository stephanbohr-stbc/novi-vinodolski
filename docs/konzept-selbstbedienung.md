# Konzept: Selbstbedienungs-Formular und automatische Veröffentlichung (Issue #3, Punkte 3–6)

Stand: 05.10.2026. Plan für die verbleibenden Punkte von #3: Formular mit Upload, Bearbeitungs-Link, automatische Veröffentlichung, Konditionen im Formular (#5). Baut auf Datenmodell und Generator auf, berücksichtigt Laufzeit (#4) und Kontaktverwaltung (#2).

## 1. Ziel

Ein Eigentümerpaar füllt ohne Hilfe ein Formular aus, lädt Fotos hoch, bestätigt die Konditionen – und bekommt innerhalb weniger Minuten eine fertige, mehrsprachige Empfehlungsseite unter einer eigenen Adresse. Später können sie Texte und Fotos selbst ändern. Stephan sieht jede neue Seite vor der Freischaltung.

## 2. Nutzerreise der Gastgeber

1. Stephan schickt den Formular-Link (persönlich, nicht öffentlich beworben).
2. Formular in 6 Schritten, ca. 30–45 Minuten: Gastgeber → Objekt → Gründe → Eigene Fotos → Umgebung/Projektstand (optional) → Kontakt & Konditionen.
3. Absenden → Bestätigungsmail mit **Bearbeitungs-Link** (enthält Zugangscode) und dem Hinweis „Stephan prüft und schaltet frei".
4. Stephan prüft Vorschau (Screenshot-Streifen wie bei Novi), gibt frei → Seite ist unter `…/seiten/<slug>/` erreichbar. Rechnung über die Erstellungsgebühr (#5).
5. Änderungen: Bearbeitungs-Link öffnen, Felder ändern, absenden → neue Version, wieder mit Freigabe (oder ohne, wenn Stephan das für diese Seite erlaubt).
6. Laufzeitende (#4): vier Wochen vorher Mail an Gastgeber und Stephan; Verlängerung per Klick, sonst Ablaufseite.

## 3. Drei Architektur-Optionen

### A – SeaTable als Formular, Speicher und Verwaltung (Empfehlung für den Start)
- **Formular:** SeaTable-Webformular (kann Datei-/Bild-Upload, Pflichtfelder, Mehrfachauswahl, Bedingungen). Pro Seite eine Zeile in der Tabelle „Seiten", Bilder als Anhänge.
- **Pipeline:** Ein Skript (`seatable-zu-json.py`) holt per SeaTable-API die Zeile und Anhänge, baut daraus die `seite.json` und den `bilder/`-Ordner (Verkleinern auf 1800 px), ruft den Generator auf und legt das Ergebnis in ein Veröffentlichungs-Repo. Läuft per GitHub Action auf Zuruf (Button „Freigeben" = Statuswechsel in SeaTable → Webhook → Action) oder stündlich.
- **Bearbeiten:** SeaTable bietet keinen Bearbeitungs-Link für fremde Nutzer ohne Konto. Lösung: eigener Bearbeitungs-Link = vorausgefülltes Formular (SeaTable unterstützt URL-Parameter zum Vorbelegen) plus Zugangscode-Feld; der Pipeline-Schritt ersetzt die alte Zeile, wenn der Code stimmt.
- **Kontaktverwaltung (#2)** liegt in derselben Base – ein Werkzeug für alles.
- **Kosten:** 0 € (SeaTable-Free reicht für Dutzende Seiten; Anhänge sind der Engpass, ca. 2 GB).
- **Aufwand:** 2–3 Tage. Kein eigener Server.

### B – Eigener kleiner Dienst (Cloudflare Pages + Worker + R2)
- Formular als statische Seite, Worker nimmt Uploads entgegen (R2), speichert JSON (KV/D1), erzeugt Bearbeitungs-Links mit signiertem Token, ruft den Generator (als JS-Port oder per GitHub-Action-Trigger) auf.
- Volle Kontrolle, sauberes Bearbeiten, sehr gute Laufzeit-/Ablauf-Logik serverseitig (#4).
- **Kosten:** 0–5 €/Monat. **Aufwand:** 1–2 Wochen inkl. Generator-Port und Sicherheit (Upload-Limits, Missbrauch).
- Sinnvoll ab etwa 20 Seiten oder wenn Dritte ohne Stephans Beteiligung ändern sollen.

### C – n8n-Workflow als Klebstoff
- n8n-Formular-Trigger → Validierung → SeaTable/GitHub → Generator per SSH/Script → Mail.
- Flexibel, aber ein weiteres System, das laufen muss (Stephans n8n-Instanz). Gut als Automatisierungsschicht über A, nicht als Ersatz.

**Empfehlung:** Mit **A** starten, weil sofort nutzbar, kostenlos und ohne Betrieb; Upgrade auf **B** nur, wenn das Modell mit Dritten tatsächlich anläuft. Die `seite.json` ist in beiden Fällen die Schnittstelle, der Generator bleibt gleich.

## 4. Formularfelder → Datenmodell

Ein Webformular kann keine verschachtelten Listen. Deshalb feste Wiederholungen:

| Formularblock | Felder | → Schema |
|---|---|---|
| Gastgeber | Anzeigename, Vornamen, Anrede (ihr/du/Sie), E-Mail, Telefon, Foto | `gastgeber` |
| Objekt | Name, Ort, Region, Land, Anbieter, Marke, Material genehmigt (ja/nein), Prämie offenlegen (ja/nein), Kurzbeschreibung | `objekt` |
| Sprachen | Mehrfachauswahl de/en/hr/sl/hu, Standardsprache | `meta.sprachen` |
| Hero | Titel, Untertitel, Hero-Bild | `hero` |
| Brief | Anrede, Absatz 1–4 | `brief` |
| Gründe | 3–7 × (Titel, Text), eines als „wichtigster Punkt" | `gruende` |
| Eigenes Objekt | Einleitung, 1–4 Merkmale, Bild, Modellbild + Unterschrift, Hinweis | `eigenes_objekt` |
| Umgebung | 0–3 × (Titel, Text, bis 3 Bilder, bis 2 Links mit Beschriftung) | `umgebung` |
| Eigene Fotos | 3–9 × (Bild, Titel, Text) – Größe wird automatisch verteilt | `fotos` |
| Projektstand | 0–4 × (Wann, Titel, Text, Status), Fazit | `projektstand` |
| Nutzung | Saisons 0–3 × (Name, Nutzung, Zeiträume), Paket-Text; Pflichthinweis wird automatisch gesetzt | `nutzung` |
| Anreise | 1–3 × (Dauer, Text), Region-Absätze, Quellen-Links | `anreise` |
| Kontakt | Mail-Betreff/-Text, 3 Schritte | `kontakt` |
| Konditionen (#5) | Anzeige des Konditionen-Textes, Checkbox „gelesen und akzeptiert", Name, Laufzeit-Auswahl (12/24 Monate) | `vereinbarung`, `meta.gueltig_bis` |

Übersetzungen: Im Formular wird nur die Standardsprache eingegeben. Weitere Sprachen entstehen in einem zweiten Schritt (Übersetzung durch Stephan/Claude, Gegenlesen durch Muttersprachler) und werden in die `seite.json` ergänzt – siehe #1. Das Formular zeigt das transparent an.

Automatisch gesetzt, nicht abgefragt: Disclaimer (`fuss.disclaimer`, Anbieter eingesetzt), Pflichthinweis Vermietung, `noindex`, Bildnachweis für Commons-Bilder (werden im Formular nicht angeboten – nur eigene Fotos und freigegebenes Anbieter-Material).

## 5. Veröffentlichung

- **Ein Repo für alle Seiten:** `stephanbohr-stbc/empfehlungsseiten`, Struktur `seiten/<slug>/index.html + bilder/`. URL: `https://stephanbohr-stbc.github.io/empfehlungsseiten/<slug>/`. Vorteil: ein Pages-Deployment, ein Workflow, keine Repo-Flut; Novi bleibt als eigenes Repo bestehen.
- **GitHub Action** `veroeffentlichen.yml`: Eingabe `slug`, holt Daten aus SeaTable, erzeugt, committet. Ausgelöst durch Freigabe-Status in SeaTable (Webhook) oder manuell.
- **Freigabe:** Standard = Stephan gibt frei (Status `freigegeben`); Gastgeber mit Vertrauensstatus dürfen direkt veröffentlichen.
- **Vorschau vor Freigabe:** Action erzeugt zusätzlich `vorschau/<slug>/` mit `noindex` und Zufallssuffix im Pfad; Link geht an Stephan und Gastgeber.
- **Ablauf (#4):** Action läuft täglich, vergleicht `gueltig_bis`, ersetzt abgelaufene Seiten durch die Ablaufseite (serverseitig, zusätzlich zur clientseitigen Logik des Generators) und setzt den Status in SeaTable.

## 6. Bearbeitungs-Link und Sicherheit

- Zugangscode: 12 Zeichen, zufällig, in SeaTable gespeichert (gehasht), nur in der Bestätigungsmail im Klartext.
- Bearbeitungs-Link = Formular-URL mit `?slug=…&code=…`; das Formular zeigt die aktuellen Werte, die Pipeline akzeptiert die Änderung nur bei passendem Code.
- Uploads: nur JPEG/PNG/HEIC, max. 15 MB je Datei, max. 25 Dateien; Pipeline verkleinert und entfernt Metadaten (Standort!).
- Kein Login, keine Passwörter – der Link ist der Schlüssel. Bei Verlust: Stephan erzeugt einen neuen Code.

## 7. Datenschutz

- Gastgeber-Daten: Vertragsdaten (#5), Aufbewahrung bis Laufzeitende + Rechnungsfristen.
- Fotos der Gastgeber und Dritter: Gastgeber bestätigt im Formular, dass er die Rechte hat und abgebildete Personen einverstanden sind.
- Datenschutzhinweis im Formular und auf jeder erzeugten Seite (Fußzeile, automatisch).
- Verarbeitung durch Stephan für Gastgeber = Auftragsverarbeitung → AV-Vertrag als Teil der Konditionen (#5).

## 7a. Stand der Umsetzung (06.10.2026)

- SeaTable-Base **Empfehlungsseiten** angelegt (Konto stephan.bohr@bohr-advise.de, Workspace 104380), Struktur per `pipeline/seatable-base-anlegen.py`.
- Webformular **„Eure Empfehlungsseite“** auf der Tabelle Seiten: Felder Gastgeber, E-Mail Gastgeber, Telefon Gastgeber, Objekt, Ort, Sprachen, Standardsprache, Bilder, Notizen. Benachrichtigung an Stephan bei jedem Eingang. Zugriff: jeder mit Link.
  Link: https://cloud.seatable.io/dtable/forms/9937bb6e-8225-489c-92ce-9bb09b1cbc26/
- Bewusst nicht im Formular: Slug, Status, Zugangscode, Seite JSON, URLs, Freigabefelder – die setzt die Pipeline bzw. Stephan.
- Noch offen in Phase 1: Pflichtfelder markieren, Hinweistexte (Konditionen, Datenschutz) im Formular, Übersetzungs-Hinweis.

## 8. Phasen

| Phase | Inhalt | Ergebnis |
|---|---|---|
| 1 | SeaTable-Base anlegen (Tabellen Seiten, Interessenten aus #2), Webformular bauen, Konditionen-Text und Datenschutzhinweis einsetzen | Formular-Link testbar |
| 2 | `seatable-zu-json.py` + Bildverarbeitung + Generator-Aufruf, lokal | Aus einer Formular-Zeile entsteht eine Seite |
| 3 | Repo `empfehlungsseiten` + GitHub Action (Vorschau, Freigabe, täglicher Ablauf-Lauf) | Veröffentlichung auf Knopfdruck |
| 4 | Bearbeitungs-Link mit Code, Bestätigungs- und Erinnerungsmails | Gastgeber ändern selbst |
| 5 | Probelauf mit einem echten Paar (ohne Rechnung), Nachbesserung | Freigabe des Modells |

Aufwand gesamt: etwa 3 Arbeitstage, verteilt. Kosten: 0 €.

## 9. Entscheidungen vor Phase 1

1. **SeaTable (A) als Start akzeptiert?** Alternative B kostet deutlich mehr Zeit.
2. **Ein Sammel-Repo `empfehlungsseiten`** oder je Seite ein Repo?
3. **Freigabe immer durch Stephan**, oder dürfen Gastgeber nach der ersten Freigabe direkt veröffentlichen?
4. **Laufzeiten im Angebot** (12 oder 24 Monate, Verlängerungspreis?) – hängt an #5.
5. **Konditionen- und Datenschutztext** müssen vor dem ersten Probelauf stehen (#5, #2).
