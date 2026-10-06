#!/usr/bin/env python3
"""Legt die Tabellenstruktur der SeaTable-Base „Empfehlungsseiten“ an (Konzept: docs/konzept-kontaktverwaltung.md).

Voraussetzung: eine (leere) Base in SeaTable und deren API-Token (Base → Erweitert → API-Token, Berechtigung „Lesen und Schreiben“).

Aufruf:
    SEATABLE_TOKEN=... python3 pipeline/seatable-base-anlegen.py
    # optional: SEATABLE_SERVER=https://cloud.seatable.io (Standard)

Idempotent: vorhandene Tabellen und Spalten werden übersprungen, fehlende ergänzt.
Nur Standardbibliothek, keine Pakete nötig.
"""
import json
import os
import sys
import urllib.error
import urllib.request

SERVER = os.environ.get("SEATABLE_SERVER", "https://cloud.seatable.io").rstrip("/")
TOKEN = os.environ.get("SEATABLE_TOKEN")

# Spalten: (Name, Typ, column_data oder None)
def auswahl(*optionen):
    farben = ["#9860E5", "#59CB74", "#FFC94E", "#F27B59", "#5BB4FD", "#FF8000", "#ADDF84", "#E1D7E3"]
    return {"options": [{"id": f"{i+1:06d}", "name": o, "color": farben[i % len(farben)], "textColor": "#FFFFFF"} for i, o in enumerate(optionen)]}

TABELLEN = {
    "Seiten": [
        ("Slug", "text", None),  # erste Spalte = Name-Spalte
        ("Gastgeber", "text", None),
        ("E-Mail Gastgeber", "email", None),
        ("Telefon Gastgeber", "text", None),
        ("Objekt", "text", None),
        ("Ort", "text", None),
        ("Status", "single-select", auswahl("entwurf", "vorschau", "freigegeben", "veroeffentlicht", "abgelaufen", "abgeschaltet")),
        ("Sprachen", "multiple-select", auswahl("de", "en", "hr", "sl", "hu")),
        ("Standardsprache", "single-select", auswahl("de", "en", "hr", "sl", "hu")),
        ("Gültig bis", "date", {"format": "YYYY-MM-DD"}),
        ("Zugangscode (Hash)", "text", None),
        ("Seite JSON", "long-text", None),
        ("Bilder", "image", None),
        ("Live-URL", "url", None),
        ("Vorschau-URL", "url", None),
        ("Freigegeben am", "date", {"format": "YYYY-MM-DD"}),
        ("Freigegeben von", "text", None),
        ("Notizen", "long-text", None),
        ("Erstellt", "ctime", None),
        ("Geändert", "mtime", None),
    ],
    "Interessenten": [
        ("Name", "text", None),
        ("E-Mail", "email", None),
        ("Telefon", "text", None),
        ("Sprache", "single-select", auswahl("de", "en", "hr", "sl", "hu")),
        ("Land", "text", None),
        ("Seite", "text", None),  # Slug; wird unten in eine Link-Spalte umgewandelt, wenn möglich
        ("Weg", "single-select", auswahl("Mail-Button", "Formular", "Anruf", "persönlich", "Weiterempfehlung")),
        ("Beziehung", "single-select", auswahl("Freund", "Familie", "Bekannter", "Weiterempfehlung")),
        ("Status", "single-select", auswahl("neu", "unterlagen gesendet", "gespräch geführt", "besichtigung", "an vertrieb weitergeleitet", "reserviert", "gekauft", "abgesagt", "inaktiv")),
        ("Erstkontakt", "date", {"format": "YYYY-MM-DD"}),
        ("Einwilligung Speicherung", "checkbox", None),
        ("Einwilligung Weitergabe Vertrieb", "checkbox", None),
        ("Einwilligung am", "date", {"format": "YYYY-MM-DD"}),
        ("Einwilligungstext Version", "text", None),
        ("Notizen", "long-text", None),
        ("Erstellt", "ctime", None),
        ("Geändert", "mtime", None),
    ],
    "Ereignisse": [
        ("Betreff", "text", None),
        ("Datum", "date", {"format": "YYYY-MM-DD"}),
        ("Art", "single-select", auswahl("Mail", "Anruf", "Gespräch", "Unterlagen gesendet", "Besichtigung", "Weiterleitung an Vertrieb", "Statuswechsel", "Sonstiges")),
        ("Text", "long-text", None),
        ("Eingetragen von", "creator", None),
        ("Erstellt", "ctime", None),
    ],
    "Vermittlungen": [
        ("Bezeichnung", "text", None),
        ("Datum Reservierung/Kauf", "date", {"format": "YYYY-MM-DD"}),
        ("Einheit", "text", None),
        ("Bestätigung Vertrieb am", "date", {"format": "YYYY-MM-DD"}),
        ("Beleg Vertrieb", "file", None),
        ("Prämie Anbieter erhalten am", "date", {"format": "YYYY-MM-DD"}),
        ("Erfolgsprämie Status", "single-select", auswahl("offen", "fällig", "gestellt", "bezahlt", "entfällt")),
        ("Erfolgsprämie EUR", "number", {"format": "euro", "decimal": "comma", "thousands": "dot"}),
        ("Rechnung gestellt am", "date", {"format": "YYYY-MM-DD"}),
        ("Notizen", "long-text", None),
    ],
    "Vereinbarungen": [
        ("Bezeichnung", "text", None),
        ("Version Konditionen", "text", None),
        ("Erstellung netto EUR", "number", {"format": "euro", "decimal": "comma", "thousands": "dot"}),
        ("Erfolgsprämie EUR", "number", {"format": "euro", "decimal": "comma", "thousands": "dot"}),
        ("Laufzeit Monate", "number", {"format": "number", "decimal": "comma", "thousands": "no"}),
        ("Akzeptiert am", "date", {"format": "YYYY-MM-DD HH:mm"}),
        ("Akzeptiert von", "text", None),
        ("Rechnung Erstellung gestellt am", "date", {"format": "YYYY-MM-DD"}),
        ("Rechnung Erstellung bezahlt am", "date", {"format": "YYYY-MM-DD"}),
        ("AV-Vertrag", "file", None),
        ("Notizen", "long-text", None),
    ],
}

# Verknüpfungen (Link-Spalten): (Tabelle, Spaltenname, Zieltabelle)
LINKS = [
    ("Interessenten", "Seite (Link)", "Seiten"),
    ("Ereignisse", "Interessent", "Interessenten"),
    ("Vermittlungen", "Interessent", "Interessenten"),
    ("Vermittlungen", "Seite", "Seiten"),
    ("Vereinbarungen", "Seite", "Seiten"),
]


def anfrage(methode, url, token, daten=None):
    req = urllib.request.Request(url, method=methode, headers={"Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"})
    if daten is not None:
        req.data = json.dumps(daten).encode()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        raise SystemExit(f"HTTP {e.code} bei {methode} {url}: {text[:300]}")


def main():
    if not TOKEN:
        sys.exit("SEATABLE_TOKEN fehlt. Base → Erweitert → API-Token anlegen und als Umgebungsvariable setzen.")
    # Base-Zugriffstoken holen
    req = urllib.request.Request(f"{SERVER}/api/v2.1/dtable/app-access-token/", headers={"Authorization": f"Token {TOKEN}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        zugang = json.loads(r.read())
    uuid, access = zugang["dtable_uuid"], zugang["access_token"]
    basis = f"{SERVER}/api-gateway/api/v2/dtables/{uuid}"
    print(f"Base: {zugang.get('dtable_name')} ({uuid}) auf {SERVER}")

    meta = anfrage("GET", f"{basis}/metadata/", access)["metadata"]
    vorhanden = {t["name"]: {c["name"] for c in t["columns"]} for t in meta["tables"]}

    for tabelle, spalten in TABELLEN.items():
        if tabelle not in vorhanden:
            erste = spalten[0]
            anfrage("POST", f"{basis}/tables/", access, {"table_name": tabelle, "columns": [{"column_name": erste[0], "column_type": erste[1]}]})
            vorhanden[tabelle] = {erste[0]}
            print(f"Tabelle angelegt: {tabelle}")
            rest = spalten[1:]
        else:
            rest = [s for s in spalten if s[0] not in vorhanden[tabelle]]
        for name, typ, daten in rest:
            body = {"table_name": tabelle, "column_name": name, "column_type": typ}
            if daten:
                body["column_data"] = daten
            anfrage("POST", f"{basis}/columns/", access, body)
            vorhanden[tabelle].add(name)
            print(f"  Spalte: {tabelle}.{name} ({typ})")

    for tabelle, name, ziel in LINKS:
        if name in vorhanden.get(tabelle, set()):
            continue
        anfrage("POST", f"{basis}/columns/", access, {"table_name": tabelle, "column_name": name, "column_type": "link", "column_data": {"table": tabelle, "other_table": ziel}})
        vorhanden[tabelle].add(name)
        print(f"  Verknüpfung: {tabelle}.{name} → {ziel}")

    # Leere Standardtabelle entfernen, falls die Base frisch ist
    for t in meta["tables"]:
        if t["name"] in ("Table1", "Tabelle1") and not t.get("rows"):
            try:
                anfrage("DELETE", f"{basis}/tables/", access, {"table_name": t["name"]})
                print(f"Leere Standardtabelle entfernt: {t['name']}")
            except SystemExit as e:
                print(f"Hinweis: {e}")
    print("Fertig. Nächster Schritt: Webformular auf der Tabelle „Seiten“ anlegen (siehe docs/konzept-selbstbedienung.md, Abschnitt 4).")


if __name__ == "__main__":
    main()
