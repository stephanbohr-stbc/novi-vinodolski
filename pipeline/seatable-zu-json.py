#!/usr/bin/env python3
"""Macht aus einer Zeile der SeaTable-Tabelle „Seiten“ eine fertige Empfehlungsseite.

Aufruf:
    SEATABLE_TOKEN=… python3 pipeline/seatable-zu-json.py <slug> [--ziel ~/git/referral-novi.github.io/seiten] [--ohne-upload]

Ablauf:
1. Zeile mit dem Slug aus SeaTable laden (Formular-Eingang).
2. Ort-Vorlage laden (pipeline/vorlagen/<ort>.json): alles, was alle Besitzer am gleichen Ort teilen.
3. Persönliches aus der Zeile einsetzen (Besitzer, Kontakt, Objekt, Fotos, Notizen) → seite.json nach docs/schema/seite.schema.json.
4. Bilder aus SeaTable herunterladen, auf 1800 px verkleinern, Resort-Bilder aus dem Novi-Repo übernehmen.
5. Generator aufrufen → <ziel>/<slug>/index.html.
6. seite.json zurück in die Spalte „Seite JSON“ schreiben, Status auf „vorschau“ setzen (außer --ohne-upload).

Braucht nur Python 3 + sips (macOS) zum Verkleinern; Übersetzungen fehlender Sprachen fallen auf die Standardsprache zurück.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import date

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
SERVER = os.environ.get("SEATABLE_SERVER", "https://cloud.seatable.io").rstrip("/")
TOKEN = os.environ.get("SEATABLE_TOKEN")
NOVI_BILDER = os.path.join(REPO, "bilder")

ORT_VORLAGEN = {"Mövenpick – Novi Vinodolski": "moevenpick-novi-vinodolski"}


def api(methode, url, token, daten=None, schema="Bearer"):
    req = urllib.request.Request(url, method=methode, headers={"Authorization": f"{schema} {token}", "Accept": "application/json", "Content-Type": "application/json"})
    if daten is not None:
        req.data = json.dumps(daten).encode()
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def slugify(s):
    s = s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:40] or "seite"


def t(de, en=None):
    """Mehrsprachiger Text; Englisch optional."""
    return {"de": de, "en": en or de}


def absaetze(text):
    teile = [p.strip() for p in re.split(r"\n\s*\n|\n", text or "") if p.strip()]
    return teile[:6]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    slug_gesucht = args[0]
    ziel_basis = os.path.expanduser(sys.argv[sys.argv.index("--ziel") + 1]) if "--ziel" in sys.argv else os.path.expanduser("~/git/referral-novi.github.io/seiten")
    ohne_upload = "--ohne-upload" in sys.argv
    if not TOKEN:
        sys.exit("SEATABLE_TOKEN fehlt (set -a; . ~/.claude/.env; set +a).")

    # 1. Zeile laden
    z = api("GET", f"{SERVER}/api/v2.1/dtable/app-access-token/", TOKEN, schema="Token")
    basis, acc = f"{SERVER}/api-gateway/api/v2/dtables/{z['dtable_uuid']}", z["access_token"]
    zeilen = api("GET", f"{basis}/rows/?table_name=Seiten&convert_keys=true", acc)["rows"]
    zeile = next((r for r in zeilen if r.get("Slug") == slug_gesucht), None)
    if not zeile:
        sys.exit(f"Keine Zeile mit Slug {slug_gesucht!r}. Vorhanden: {[r.get('Slug') for r in zeilen]}")
    slug = slugify(zeile["Slug"])

    # 2. Ort-Vorlage
    ort = zeile.get("Ort") or "Mövenpick – Novi Vinodolski"
    vorlage_name = ORT_VORLAGEN.get(ort)
    if not vorlage_name:
        sys.exit(f"Keine Ort-Vorlage für {ort!r}. Vorhanden: {list(ORT_VORLAGEN)}")
    V = json.load(open(os.path.join(HIER, "vorlagen", vorlage_name + ".json"), encoding="utf-8"))

    # 3. Persönliches
    besitzer = (zeile.get("Besitzer") or "").strip()
    vornamen = [p.strip() for p in re.split(r"\s*(?:&|und|\+|,)\s*", besitzer) if p.strip()]
    anzeigename = " & ".join(v.split()[0] for v in vornamen) if len(vornamen) > 1 else (vornamen[0].split()[0] if vornamen else besitzer)
    anrede = "ihr"
    sprachen = zeile.get("Sprachen") or ["de"]
    std = zeile.get("Standardsprache") or sprachen[0]
    heute = date.today().isoformat()
    notizen = zeile.get("Notizen") or ""
    objekt_text = (zeile.get("Objekt") or "").strip()

    ziel = os.path.join(ziel_basis, slug)
    os.makedirs(os.path.join(ziel, "bilder", "privat"), exist_ok=True)

    # 4. Bilder: eigene aus SeaTable, Resort-Bilder aus dem Novi-Repo
    eigene = []
    for i, url in enumerate(zeile.get("Bilder") or [], 1):
        pfad = urllib.parse.unquote(urllib.parse.urlparse(url).path)
        rel = pfad.split("/asset/", 1)[1].split("/", 1)[1] if "/asset/" in pfad else None
        if not rel:
            continue
        link = api("GET", f"{SERVER}/api/v2.1/dtable/app-download-link/?path=" + urllib.parse.quote("/" + rel), TOKEN, schema="Token")["download_link"]
        roh = os.path.join(ziel, "bilder", "privat", f"roh-{i}")
        urllib.request.urlretrieve(link, roh)
        datei = f"bilder/privat/foto-{i}.jpg"
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82", "-Z", "1800", roh, "--out", os.path.join(ziel, datei)], check=True, capture_output=True)
        os.remove(roh)
        eigene.append(datei)
        print("Bild übernommen:", datei)
    for ordner in ("", "umgebung"):
        q = os.path.join(NOVI_BILDER, ordner)
        if os.path.isdir(q):
            os.makedirs(os.path.join(ziel, "bilder", ordner), exist_ok=True)
            for f in os.listdir(q):
                if f.lower().endswith(".jpg"):
                    shutil.copy2(os.path.join(q, f), os.path.join(ziel, "bilder", ordner, f))

    # Fotos-Galerie aus den eigenen Bildern; Größen rotierend
    groessen = ["breit", "schmal", "drittel", "drittel", "drittel", "schmal", "breit"]
    fotos = [{"datei": d, "titel": t(f"Foto {i}", f"Photo {i}"), "groesse": groessen[(i - 1) % len(groessen)]} for i, d in enumerate(eigene, 1)]
    if not fotos:  # ohne eigene Fotos wenigstens eine Kachel mit Resort-Bild
        fotos = [{"datei": "bilder/strandweg.jpg", "titel": t("Der Weg zum Strand", "The path to the beach"), "groesse": "breit"}]

    seite = {
        "meta": {"slug": slug, "sprachen": sprachen, "standardsprache": std, "erstellt_am": heute, "stand": heute, "status": "entwurf", "suchmaschinen": False},
        "gastgeber": {"anzeigename": anzeigename or besitzer, "anrede": anrede,
                      "kontakt": {k: v for k, v in {"email": zeile.get("E-Mail Besitzer"), "telefon": zeile.get("Telefon Besitzer"),
                                                     "mail_betreff": t(f"{V['objekt']['ort']} – erzählt uns mehr", f"{V['objekt']['ort']} – tell us more"),
                                                     "mail_text": t(f"Hallo {anzeigename},\n\nwir sind neugierig geworden. Schickt uns gern die Unterlagen.\n\nViele Grüße", f"Hi {anzeigename},\n\nwe are curious. Please send us the documents.\n\nBest wishes")}.items() if v},
                      **({"foto": {"datei": eigene[0], "quelle": "eigen"}} if eigene else {})},
        "objekt": {**V["objekt"], "praemie_offenlegen": True},
        "hero": {"titel": t("Wir haben unseren Platz am Meer gefunden.", "We have found our place by the sea."),
                 "untertitel": t(f"In {V['objekt']['ort']} an der Kvarner-Bucht – anderthalb Flugstunden von Frankfurt. Und wir fänden es großartig, wenn ihr dort unsere Nachbarn würdet.",
                                 f"In {V['objekt']['ort']} on Croatia's Kvarner Bay – an hour and a half by plane from Frankfurt. And we would love it if you became our neighbours there."),
                 "bild": V["hero_bild"]},
        "brief": {"anrede": t("Liebe Freunde,", "Dear friends,"),
                  "absaetze": [t(a) for a in absaetze(notizen)] or [t(f"wir haben uns für ein Apartment in {V['objekt']['ort']} entschieden – und würden uns freuen, wenn ihr dort unsere Nachbarn werdet.",
                                                                         f"we have decided on an apartment in {V['objekt']['ort']} – and would love for you to become our neighbours there.")],
                  "unterschrift": anzeigename or besitzer},
        "gruende": V["gruende_standard"],
        "umgebung": V["umgebung"],
        "fotos": {"einleitung": t(f"Keine Visualisierung, kein Prospekt: eigene Bilder, Stand {heute}.", f"No renderings, no brochure: our own pictures, as of {heute}."), "bilder": fotos},
        "projektstand": V["projektstand"],
        "ueberblick": V["ueberblick"],
        "nutzung": V["nutzung"],
        "anreise": V["anreise"],
        "offen": V["offen_standard"],
        "kontakt": {"schritte": V["kontakt_schritte"], "bild": V["kontakt_bild"], "formular": False},
        "fuss": {"disclaimer": [t(d["de"].replace("Manu und Stephan", besitzer or "den Besitzern"), d["en"].replace("Manu and Stephan", besitzer or "the owners")) for d in V["fuss_disclaimer"]],
                 "bildnachweis": V["bildnachweis"]},
    }
    if objekt_text:
        seite["eigenes_objekt"] = {"einleitung": t(f"Wir haben uns für {objekt_text} entschieden.", f"We chose {objekt_text}."),
                                   "merkmale": [{"titel": t("Unser Apartment", "Our apartment"), "text": t(objekt_text)}]}
    if zeile.get("Gültig bis"):
        seite["meta"]["gueltig_bis"] = zeile["Gültig bis"][:10]

    json_pfad = os.path.join(ziel, "seite.json")
    json.dump(seite, open(json_pfad, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 5. Generator
    subprocess.run([sys.executable, os.path.join(REPO, "generator", "erzeuge-seite.py"), json_pfad, ziel], check=True)

    # 6. Rückschreiben
    if not ohne_upload:
        api("PUT", f"{basis}/rows/", acc, {"table_name": "Seiten", "updates": [{"row_id": zeile["_id"], "row": {"Seite JSON": json.dumps(seite, ensure_ascii=False), "Status": "vorschau", "Vorschau-URL": f"https://referral-novi.eu/vorschau/{slug}/"}}]})
        print("SeaTable aktualisiert: Status vorschau, Seite JSON gespeichert.")
    print(f"Fertig: {ziel}/index.html ({len(eigene)} eigene Bilder, Vorlage {vorlage_name})")


if __name__ == "__main__":
    main()
