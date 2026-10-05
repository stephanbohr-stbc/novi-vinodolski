# Konzept: Kontaktverwaltung für Interessenten (Issue #2)

Stand: 05.10.2026. Plan, noch keine Umsetzung. Berücksichtigt das Selbstbedienungs-Formular (#3), die begrenzte Laufzeit (#4) und die Konditionen für Seiten Dritter (#5).

## 1. Worum es geht

Heute landen Anfragen von Freunden per E-Mail und Telefon bei Manu und Stephan. Das reicht für eine Seite. Sobald weitere Eigentümer eigene Seiten bekommen (#3) und dafür eine Erfolgsprämie fällig wird (#5), muss belastbar nachvollziehbar sein: **Wer hat sich über welche Seite gemeldet, was ist daraus geworden, und wann wurde vermittelt?** Genau das leistet die Kontaktverwaltung.

## 2. Rollen

| Rolle | Wer | Was sie braucht |
|---|---|---|
| **Betreiber** | Stephan (später ggf. eine Gesellschaft) | Überblick über alle Seiten und Interessenten, Nachweis für Prämien, Rechnungsstellung |
| **Gastgeber** | Eigentümer, die eine Seite haben (Manu & Stephan; Dritte über #3) | Sehen nur die Interessenten ihrer eigenen Seite, pflegen Status und Notizen |
| **Interessent** | Freund/Bekannter, der sich meldet | Meldet sich mit minimalem Aufwand, weiß, was mit seinen Daten passiert |
| **Vertrieb des Anbieters** | z. B. Sales Kvarner Bay | Erhält nur weitergeleitete Kontakte mit Einwilligung; bestätigt Vermittlungen |

## 3. Datenobjekte

```
Seite ──1:n── Interessent ──1:n── Kontaktereignis
  │                │
  │                └── Vermittlung (0..1)
  └── Vereinbarung (0..1, nur Fremdseiten, #5)
```

**Seite** (aus dem Datenmodell #3): `slug`, Gastgeber, Objekt, `status`, `gueltig_bis` (#4), Vereinbarung (#5).

**Interessent**
- Stammdaten: Name, E-Mail, Telefon, Sprache, Land
- Herkunft: `seite.slug`, Weg (Mail-Button / Formular / Anruf / persönlich), Datum des Erstkontakts
- Beziehung zum Gastgeber (Freund, Familie, Bekannter, Weiterempfehlung durch …)
- Status (Pipeline, siehe 4.)
- Einwilligungen: Speicherung (Pflicht), Weitergabe an den Vertrieb (optional, einzeln), Zeitstempel und Version des Einwilligungstextes
- Notizen (frei)

**Kontaktereignis**: Datum, Art (Mail, Anruf, Gespräch, Unterlagen gesendet, Besichtigung, Weiterleitung an Vertrieb), Kurztext, wer eingetragen hat.

**Vermittlung**: Datum der Reservierung/des Kaufs, Objekt-Einheit, Bestätigung durch den Vertrieb (Datum, Beleg), Prämie des Anbieters erhalten (Datum), Erfolgsprämie nach #5 fällig/gestellt/bezahlt.

**Vereinbarung** (#5): Version des Konditionen-Textes, 250 € netto Erstellung, 500 € Erfolgsprämie, Laufzeit, bestätigt am/von, Rechnung Erstellung gestellt/bezahlt.

## 4. Status-Pipeline

`neu` → `unterlagen gesendet` → `gespräch geführt` → `besichtigung` → `an vertrieb weitergeleitet` → `reserviert` → `gekauft` | `abgesagt` | `inaktiv`

- Jeder Statuswechsel erzeugt ein Kontaktereignis (automatisch).
- `reserviert`/`gekauft` setzen eine Vermittlung an und lösen die Prüfung der Erfolgsprämie aus (#5).
- `inaktiv` wird automatisch gesetzt, wenn 6 Monate nichts passiert ist (Erinnerung an den Gastgeber vorher).

## 5. Zusammenspiel mit den anderen Issues

**#3 Selbstbedienungs-Formular**
- Jede erzeugte Seite bekommt beim Anlegen ihren Datensatz „Seite" in der Verwaltung; der Gastgeber bekommt einen Zugang (Bearbeitungs-Link + Zugangscode, derselbe wie für die Seite).
- Der Kontakt-Button der Seite kann wahlweise ein kleines Formular öffnen (`kontakt.formular = true`): Name, E-Mail, optional Telefon und Nachricht, Einwilligungs-Checkbox. Das Formular trägt den Interessenten direkt mit `seite.slug` ein und schickt dem Gastgeber eine Mail. Der Mail-Button bleibt als Alternative (dann trägt der Gastgeber den Kontakt von Hand nach).

**#4 Begrenzte Laufzeit**
- Läuft `gueltig_bis` ab, schließt die Seite die Kontaktaufnahme; bestehende Interessenten bleiben in der Pipeline, bis sie abgeschlossen sind.
- Löschfristen hängen an der Laufzeit: Interessenten ohne Vermittlung werden 12 Monate nach Ablauf der Seite gelöscht, mit Vermittlung erst nach Abschluss aller Prämienzahlungen plus gesetzlicher Aufbewahrung der Rechnungen (10 Jahre, nur die Rechnungsdaten).
- Verlängerung der Laufzeit setzt alle Fristen neu.

**#5 Konditionen**
- Die Erfolgsprämie (500 €) wird aus der Verwaltung heraus ausgelöst: Vermittlung mit Bestätigung des Vertriebs → Rechnung an den Gastgeber. Ohne vollständigen Nachweis (Interessent mit Herkunft = Seite, Ereigniskette, Bestätigung) keine Rechnung.
- Die Erstellungsgebühr (250 € zzgl. Steuern) wird beim Anlegen der Seite fällig und im Datensatz „Vereinbarung" verfolgt.
- Beide Beträge und ihre Versionierung stehen im Datenmodell (`vereinbarung`), nicht im Code.

## 6. Datenschutz (DSGVO)

- **Rechtsgrundlage:** Einwilligung des Interessenten (Art. 6 Abs. 1 a) beim Formular; bei Mail/Anruf berechtigtes Interesse des Gastgebers, Kontakt dokumentiert zu halten (Art. 6 Abs. 1 f) – im Zweifel Einwilligung nachholen.
- **Weitergabe an den Vertrieb** nur mit gesonderter, protokollierter Einwilligung.
- **Zugriff:** Gastgeber sehen nur ihre Seite; der Betreiber alles. Zugänge personengebunden.
- **Speicherort:** EU. Keine Daten im öffentlichen Git-Repo – die Verwaltung lebt vollständig außerhalb der Seite.
- **Informationspflicht:** kurzer Datenschutzhinweis auf der Seite (wer speichert was, wie lange, Widerruf per Mail).
- **Betroffenenrechte:** Auskunft und Löschung müssen aus der Verwaltung heraus einfach möglich sein (Export je Interessent, Löschen-Knopf).
- **Auftragsverarbeitung:** Wenn der Betreiber die Daten für Gastgeber (Dritte) verwaltet, braucht es einen AV-Vertrag als Teil der Vereinbarung (#5).

## 7. Werkzeug in drei Stufen

**Stufe 1 – jetzt, für die Novi-Seite (Aufwand: ein Nachmittag)**
SeaTable-Base „Empfehlungsseiten" (Stephan nutzt SeaTable bereits) mit den Tabellen Seiten, Interessenten, Ereignisse, Vermittlungen. Pflege von Hand nach jeder Mail/jedem Anruf. Ansichten: „Offene Interessenten", „Vermittlungen offen". Keine Automatisierung.

**Stufe 2 – mit dem Formular (#3)**
Kontaktformular auf der Seite schreibt per Webhook/API in SeaTable (oder einen kleinen Dienst davor, der die Einwilligung protokolliert und die Mail an den Gastgeber schickt). Gastgeber bekommen eine SeaTable-Freigabeansicht gefiltert auf ihre Seite. Automatische Erinnerungen (inaktiv, Laufzeit endet).

**Stufe 3 – eigene Oberfläche (nur wenn es viele Seiten werden)**
Kleine Web-App (Login je Gastgeber, Pipeline-Ansicht, Export, Lösch-Knopf, Rechnungsauslösung). Datenbank bleibt SeaTable oder wandert in Postgres. Erst sinnvoll ab etwa zehn aktiven Seiten.

## 8. Entscheidungen, die vorher fallen müssen

1. Wer ist Betreiber und Rechnungssteller (Stephan privat, STB, AI Performance Academy, neue Gesellschaft)? Daran hängen Steuer, AV-Vertrag und Impressum.
2. Rechtliche Einordnung der Vermittlung gegen Prämie (Maklerrecht, Gewerbeanmeldung) – vor der ersten Fremdseite klären.
3. Soll der Vertrieb des Anbieters Vermittlungen formal bestätigen? Ohne Bestätigung fehlt der Nachweis für #5.
4. Datenschutzhinweis und Einwilligungstexte (DE/EN) formulieren.

## 9. Umsetzungsschritte (Vorschlag)

- [ ] Entscheidungen aus Abschnitt 8 treffen
- [ ] SeaTable-Base anlegen (Stufe 1), Novi-Interessenten eintragen
- [ ] Datenschutzhinweis und Einwilligungstext schreiben; Hinweis auf die Seite setzen
- [ ] Datenmodell (#3) um `kontakt.formular` nutzen: Formular bauen, an SeaTable anbinden (Stufe 2)
- [ ] Laufzeit-Logik (#4) mit Löschfristen verknüpfen
- [ ] Rechnungsablauf für #5 aus den Vermittlungsdaten ableiten
