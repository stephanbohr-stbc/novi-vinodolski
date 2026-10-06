# Novi Vinodolski – unser Platz am Meer

Private Empfehlungsseite von Manu und Stephan für Freunde: warum wir uns für ein Apartment in den Mövenpick Residences Kvarner Bay in Novi Vinodolski entschieden haben – und warum wir uns freuen würden, wenn Freunde dort Nachbarn werden.

**Seite:** https://stephanbohr-stbc.github.io/novi-vinodolski/
**Englisch:** https://stephanbohr-stbc.github.io/novi-vinodolski/?lang=en

## Was die Seite ist

- Eine einzelne statische HTML-Seite ohne Framework, ohne Build-Schritt, ohne externe Abhängigkeiten.
- Zweisprachig (Deutsch/Englisch) über einen Umschalter in der festen Kopfleiste.
- Gehostet kostenlos über GitHub Pages direkt aus dem Branch `main`.
- Keine Preise, kein Angebot, keine Anlageberatung – nur persönliche Einladung plus Fakten aus den Unterlagen des Entwicklers.
- Die Provision, die wir bei einer Vermittlung erhalten, wird offen genannt (ohne Betrag).

## Aufbau

```
index.html          die komplette Seite (HTML, CSS und JavaScript in einer Datei)
bilder/             Visualisierungen des Entwicklers (mit Genehmigung des Vertriebs)
bilder/privat/      eigene Fotos
bilder/umgebung/    frei lizenzierte Fotos von Wikimedia Commons (Bildnachweis im Seitenfuß)
deploy.sh           veröffentlicht den aktuellen Stand aus der Quelle (Google Drive)
generator/          erzeugt aus einer seite.json eine fertige Seite (siehe generator/README.md)
docs/schema/        Datenmodell (JSON Schema) und Beispiel
docs/PROZESS.md     wie die Seite entstanden ist und wie sie gepflegt wird
docs/AENDERUNGEN.md Änderungsprotokoll
```

## Pflege

Die Quelle liegt in Google Drive (`04 - Haus Wohnen/35 - Mövenpick Accor/06 - Webseite Empfehlung`). Änderungen werden dort gemacht und mit

```
./deploy.sh "Kurzbeschreibung der Änderung"
```

veröffentlicht. Das Skript kopiert Seite und Bilder, entfernt Entwurfs-Markierungen, committet und pusht. Nach ein bis zwei Minuten ist der neue Stand online.

Wünsche und Ideen werden als [Issues](https://github.com/stephanbohr-stbc/novi-vinodolski/issues) erfasst.

## Nachnutzung

**Stand 06.10.2026:** Die Weiterentwicklung zur Plattform (Formular, Pipeline, eigene Domain referral-novi.eu) ist bis Phase 2 gebaut und dann **pausiert**; Details in `docs/konzept-selbstbedienung.md` und den Issues.


Der Aufbau eignet sich als Vorlage für ähnliche Empfehlungsseiten anderer Eigentümer. Der Prozess ist in `docs/PROZESS.md` beschrieben.
