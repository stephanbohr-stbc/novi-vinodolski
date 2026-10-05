#!/usr/bin/env python3
"""Erzeugt aus einer seite.json (Schema: docs/schema/seite.schema.json) die fertige index.html.

Aufruf:
    python3 generator/erzeuge-seite.py <seite.json> <ausgabeordner> [--pruefen]

- Schreibt <ausgabeordner>/index.html. Bilder werden nicht kopiert; der Ordner
  bilder/ muss daneben liegen (die Pfade im JSON sind relativ zur Seite).
- --pruefen validiert das JSON vorher gegen das Schema (braucht das Paket
  jsonschema, z. B. `uv run --with jsonschema python generator/erzeuge-seite.py …`).
- Sprachen: alle in meta.sprachen; die Standardsprache steht im HTML, alle
  Sprachen zusätzlich als data-<code>-Attribute. Fehlende Übersetzungen fallen
  auf die Standardsprache zurück.
- Laufzeit (meta.gueltig_bis): nach Ablauf zeigt die Seite nur den Ablauf-Hinweis.

Design und Verhalten entsprechen der Novi-Vinodolski-Seite (generator/vorlage.css).
"""
import html
import json
import os
import re
import sys
from datetime import date
from urllib.parse import quote

HIER = os.path.dirname(os.path.abspath(__file__))

SPRACHNAMEN = {"de": "DE", "en": "EN", "hr": "HR", "sl": "SL", "hu": "HU"}
UI = {  # feste Oberflächentexte je Sprache
    "de": {"kontakt": "Meldet euch", "kontakt_sie": "Melden Sie sich", "wer": "Eine Einladung an unsere Freunde",
           "brief": "Ein paar Zeilen von uns", "gruende": "Was uns überzeugt hat", "gruende_h": "Was wir besonders schätzen",
           "wahl": "Unsere Wahl", "umgebung": "Bei unseren ersten Besuchen", "umgebung_h": "Was wir rundherum entdeckt haben",
           "fotos": "Unsere eigenen Fotos", "fotos_h": "So sieht es dort wirklich aus", "stand": "Stand", "stand_h": "Wo das Projekt heute steht",
           "resort": "Das Objekt im Überblick", "nutzung": "So funktioniert es", "anreise": "Anreise", "anreise_h": "Näher, als man denkt",
           "offen": "Ganz offen gesagt", "neugierig": "Neugierig geworden?", "mail": "E-Mail an", "oder": "oder ruft an:",
           "oder_sie": "oder rufen Sie an:", "bildnachweis": "Bildnachweis:", "abgelaufen": "Diese Seite ist nicht mehr aktiv.",
           "schreibt": "Schreibt uns", "schreibt_sie": "Schreiben Sie uns", "warum": "Warum wir das erzählen"},
    "en": {"kontakt": "Get in touch", "kontakt_sie": "Get in touch", "wer": "An invitation to our friends",
           "brief": "A few lines from us", "gruende": "What convinced us", "gruende_h": "What we really value",
           "wahl": "Our choice", "umgebung": "On our first visits", "umgebung_h": "What we discovered nearby",
           "fotos": "Our own photos", "fotos_h": "What it actually looks like", "stand": "As of", "stand_h": "Where the project stands today",
           "resort": "The property at a glance", "nutzung": "How it works", "anreise": "Getting there", "anreise_h": "Closer than you think",
           "offen": "To be completely open", "neugierig": "Curious?", "mail": "Email", "oder": "or call us:",
           "oder_sie": "or call us:", "bildnachweis": "Photo credits:", "abgelaufen": "This page is no longer active.",
           "schreibt": "Write to us", "schreibt_sie": "Write to us", "warum": "Why we are telling you this"},
    "hr": {"kontakt": "Javite nam se", "kontakt_sie": "Javite nam se", "wer": "Poziv našim prijateljima",
           "brief": "Nekoliko riječi od nas", "gruende": "Što nas je uvjerilo", "gruende_h": "Što posebno cijenimo",
           "wahl": "Naš izbor", "umgebung": "Pri našim prvim posjetima", "umgebung_h": "Što smo otkrili u okolici",
           "fotos": "Naše fotografije", "fotos_h": "Kako zaista izgleda", "stand": "Stanje", "stand_h": "Gdje je projekt danas",
           "resort": "Pregled objekta", "nutzung": "Kako funkcionira", "anreise": "Dolazak", "anreise_h": "Bliže nego što mislite",
           "offen": "Posve otvoreno", "neugierig": "Zainteresirani?", "mail": "E-mail za", "oder": "ili nazovite:",
           "oder_sie": "ili nazovite:", "bildnachweis": "Izvori fotografija:", "abgelaufen": "Ova stranica više nije aktivna.",
           "schreibt": "Pišite nam", "schreibt_sie": "Pišite nam", "warum": "Zašto vam ovo pričamo"},
    "sl": {"kontakt": "Oglasite se", "kontakt_sie": "Oglasite se", "wer": "Vabilo našim prijateljem",
           "brief": "Nekaj besed od naju", "gruende": "Kaj naju je prepričalo", "gruende_h": "Kaj še posebej ceniva",
           "wahl": "Najina izbira", "umgebung": "Ob najinih prvih obiskih", "umgebung_h": "Kaj sva odkrila v okolici",
           "fotos": "Najine fotografije", "fotos_h": "Kako v resnici izgleda", "stand": "Stanje", "stand_h": "Kje je projekt danes",
           "resort": "Objekt na kratko", "nutzung": "Kako deluje", "anreise": "Prihod", "anreise_h": "Bližje, kot mislite",
           "offen": "Povsem odkrito", "neugierig": "Radovedni?", "mail": "E-pošta za", "oder": "ali pokličite:",
           "oder_sie": "ali pokličite:", "bildnachweis": "Viri fotografij:", "abgelaufen": "Ta stran ni več aktivna.",
           "schreibt": "Pišite nama", "schreibt_sie": "Pišite nam", "warum": "Zakaj vam to pripovedujeva"},
    "hu": {"kontakt": "Jelentkezzetek", "kontakt_sie": "Jelentkezzen", "wer": "Meghívó a barátainknak",
           "brief": "Néhány sor tőlünk", "gruende": "Ami meggyőzött minket", "gruende_h": "Amit különösen értékelünk",
           "wahl": "A mi választásunk", "umgebung": "Az első látogatásainkon", "umgebung_h": "Amit a környéken felfedeztünk",
           "fotos": "Saját fotóink", "fotos_h": "Így néz ki valójában", "stand": "Állapot", "stand_h": "Hol tart ma a projekt",
           "resort": "Az ingatlan röviden", "nutzung": "Így működik", "anreise": "Megközelítés", "anreise_h": "Közelebb, mint gondolnád",
           "offen": "Őszintén szólva", "neugierig": "Kíváncsi lettél?", "mail": "E-mail", "oder": "vagy hívjatok:",
           "oder_sie": "vagy hívjon:", "bildnachweis": "Képek forrása:", "abgelaufen": "Ez az oldal már nem aktív.",
           "schreibt": "Írjatok nekünk", "schreibt_sie": "Írjon nekünk", "warum": "Miért meséljük el"},
}


MONATE = {
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "hr": ["siječnja", "veljače", "ožujka", "travnja", "svibnja", "lipnja", "srpnja", "kolovoza", "rujna", "listopada", "studenoga", "prosinca"],
    "sl": ["januar", "februar", "marec", "april", "maj", "junij", "julij", "avgust", "september", "oktober", "november", "december"],
    "hu": ["január", "február", "március", "április", "május", "június", "július", "augusztus", "szeptember", "október", "november", "december"],
}


def datum(iso, sprache):
    """ISO-Datum sprachgerecht ausschreiben (1. Oktober 2026 / 1 October 2026)."""
    d = date.fromisoformat(iso)
    m = MONATE.get(sprache, MONATE["en"])[d.month - 1]
    if sprache == "de":
        return f"{d.day}. {m} {d.year}"
    if sprache == "hr":
        return f"{d.day}. {m} {d.year}."
    if sprache == "sl":
        return f"{d.day}. {m} {d.year}"
    if sprache == "hu":
        return f"{d.year}. {m} {d.day}."
    return f"{d.day} {m} {d.year}"


class Seite:
    def __init__(self, daten):
        self.d = daten
        self.sprachen = daten["meta"]["sprachen"]
        self.std = daten["meta"]["standardsprache"]
        self.sie = daten["gastgeber"]["anrede"] == "sie"

    # ---------- Textbausteine ----------
    def txt(self, t, sprache=None):
        """Text in einer Sprache, mit Rückfall auf die Standardsprache."""
        if t is None:
            return ""
        if isinstance(t, str):
            return t
        return t.get(sprache or self.std) or t.get(self.std) or next(iter(t.values()), "")

    @staticmethod
    def inline(s):
        """HTML-escapen, **fett** und Zeilenumbrüche erlauben."""
        s = html.escape(s, quote=True)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        return s.replace("\n", "<br>")

    def ui(self, schluessel, sprache=None):
        sp = sprache or self.std
        return UI.get(sp, UI["de"]).get(schluessel, UI["de"][schluessel])

    def el(self, tag, t, klasse="", extra=""):
        """Mehrsprachiges Element: Standardsprache als Inhalt, alle Sprachen als data-Attribute."""
        if t is None:
            return ""
        attrs = ' data-i18n'
        for sp in self.sprachen:
            attrs += f' data-{sp}="{self.inline(self.txt(t, sp))}"'
        if klasse:
            attrs += f' class="{klasse}"'
        if extra:
            attrs += " " + extra
        return f"<{tag}{attrs}>{self.inline(self.txt(t))}</{tag}>"

    def ui_el(self, tag, schluessel, klasse="", extra=""):
        return self.el(tag, {sp: self.ui(schluessel, sp) for sp in self.sprachen}, klasse, extra)

    def bild(self, b, extra_style=""):
        if not b:
            return ""
        style = ""
        pos = b.get("bildausschnitt")
        if pos or extra_style:
            style = f' style="{("object-position: " + pos + ";") if pos else ""}{extra_style}"'
        alt = self.inline(self.txt(b.get("alt"))) if b.get("alt") else ""
        return f'<img src="{html.escape(b["datei"])}" alt="{alt}"{style}>'

    def links(self, liste, klasse="links"):
        if not liste:
            return ""
        items = "".join(
            f'<li><a href="{html.escape(l["url"])}" target="_blank" rel="noopener"' +
            "".join(f' data-{sp}="{self.inline(self.txt(l["label"], sp))}"' for sp in self.sprachen) +
            f' data-i18n>{self.inline(self.txt(l["label"]))}</a></li>'
            for l in liste)
        return f'<ul class="{klasse}">{items}</ul>'

    def mailto(self, sprache):
        k = self.d["gastgeber"]["kontakt"]
        betreff = self.txt(k.get("mail_betreff"), sprache)
        text = self.txt(k.get("mail_text"), sprache)
        q = []
        if betreff:
            q.append("subject=" + quote(betreff, safe=""))
        if text:
            q.append("body=" + quote(text, safe=""))
        return "mailto:" + k["email"] + ("?" + "&".join(q) if q else "")

    # ---------- Abschnitte ----------
    def kopf(self):
        d = self.d
        titel = self.txt(d["hero"]["titel"])
        beschreibung = self.txt(d["objekt"].get("kurzbeschreibung"))
        robots = "index, follow" if d["meta"].get("suchmaschinen") else "noindex, nofollow"
        css = open(os.path.join(HIER, "vorlage.css"), encoding="utf-8").read()
        return f"""<!DOCTYPE html>
<html lang="{self.std}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="{robots}">
<title>{html.escape(titel)}</title>
<meta name="description" content="{html.escape(beschreibung)}">
<meta name="generator" content="erzeuge-seite.py (novi-vinodolski)">
<style>
{css}</style>
</head>
<body>
"""

    def nav(self):
        g = self.d["gastgeber"]
        knoepfe = "".join(
            f'<button type="button" data-lang="{sp}" aria-pressed="{"true" if sp == self.std else "false"}">{SPRACHNAMEN.get(sp, sp.upper())}</button>'
            for sp in self.sprachen)
        sprache = f'<div class="sprache" role="group" aria-label="Sprache / Language">{knoepfe}</div>' if len(self.sprachen) > 1 else ""
        return f"""<nav>
  <span class="marke">{html.escape(g["anzeigename"])} · {html.escape(self.d["objekt"]["ort"])}</span>
  <div class="rechts">{sprache}{self.ui_el("a", "kontakt_sie" if self.sie else "kontakt", "knopf-klein", 'href="#kontakt"')}</div>
</nav>
"""

    def hero(self):
        h = self.d["hero"]
        label = h.get("label") or {sp: self.ui("wer", sp) for sp in self.sprachen}
        b1 = h.get("button_kontakt") or {sp: self.ui("schreibt_sie" if self.sie else "schreibt", sp) for sp in self.sprachen}
        b2 = h.get("button_warum") or {sp: self.ui("warum", sp) for sp in self.sprachen}
        return f"""<header class="hero">
  {self.bild(h["bild"])}
  <div class="wrap">
    {self.el("span", label, "label")}
    {self.el("h1", h["titel"])}
    {self.el("p", h["untertitel"])}
    {self.el("a", b1, "knopf", 'href="#kontakt"')}
    {self.el("a", b2, "knopf hell", 'href="#brief"')}
  </div>
</header>
"""

    def brief(self):
        b = self.d["brief"]
        g = self.d["gastgeber"]
        absaetze = "\n      ".join(self.el("p", a) for a in b["absaetze"])
        foto = f'<figure><div class="privat quer">{self.bild(g["foto"])}</div></figure>' if g.get("foto") else ""
        unterschrift = f'<p class="unterschrift">{html.escape(b.get("unterschrift") or g["anzeigename"])}</p>'
        return f"""<section class="brief" id="brief">
  <div class="wrap zwei">
    <div>
      {self.el("span", b.get("label") or {sp: self.ui("brief", sp) for sp in self.sprachen}, "label")}
      {self.el("h2", b["anrede"])}
      {absaetze}
      {unterschrift}
    </div>
    {foto}
  </div>
</section>
"""

    def gruende(self):
        karten = "\n      ".join(
            f'<div class="grund{" wichtig" if g.get("hervorgehoben") else ""}">{self.el("h3", g["titel"])}{self.el("p", g["text"])}</div>'
            for g in self.d["gruende"])
        return f"""<section id="gruende">
  <div class="wrap">
    {self.ui_el("span", "gruende", "label")}
    {self.ui_el("h2", "gruende_h")}
    <div class="gruende">
      {karten}
    </div>
  </div>
</section>
"""

    def eigenes_objekt(self):
        e = self.d.get("eigenes_objekt")
        if not e:
            return ""
        merkmale = "".join(f'<li>{self.el("strong", m["titel"])}{self.el("span", m["text"])}</li>' for m in e["merkmale"])
        bild = ""
        if e.get("bild"):
            cap = f'<p class="hinweis">{self.el("span", e["bild"]["bildunterschrift"])}</p>' if e["bild"].get("bildunterschrift") else ""
            bild = f'<figure><div class="privat quer">{self.bild(e["bild"])}</div>{cap}</figure>'
        modell = ""
        if e.get("modell"):
            cap = self.el("figcaption", e["modell"].get("bildunterschrift")) if e["modell"].get("bildunterschrift") else ""
            modell = f'<figure class="modell">{self.bild(e["modell"])}{cap}</figure>'
        hinweis = self.el("p", e.get("hinweis"), "reihen") if e.get("hinweis") else ""
        return f"""<section class="unseres" id="unseres">
  <div class="wrap zwei">
    {bild}
    <div>
      {self.ui_el("span", "wahl", "label")}
      {self.el("h2", e.get("titel") or e["einleitung"])}
      {self.el("p", e["einleitung"]) if e.get("titel") else ""}
      <ul class="merkmale">{merkmale}</ul>
    </div>
  </div>
  <div class="wrap">
    {modell}
    {hinweis}
  </div>
</section>
"""

    def umgebung(self):
        u = self.d.get("umgebung")
        if not u:
            return ""
        bloecke = []
        for i, a in enumerate(u):
            bilder = a.get("bilder") or []
            layout = a.get("layout") or ("drei-bilder" if len(bilder) >= 3 else "zwei-bilder" if len(bilder) == 2 else "ein-bild" if bilder else "nur-text")
            text = f'{self.el("h3", a["titel"])}{self.el("p", a["text"])}{self.links(a.get("links"))}'
            if layout == "drei-bilder":
                figs = "".join(f"<figure>{self.bild(b)}</figure>" for b in bilder[:3])
                bloecke.append(f'<div class="plitvice"><div class="bilder">{figs}</div><div>{text}</div></div>')
            elif layout == "nur-text":
                bloecke.append(f'<div class="ortszeile">{text}</div>')
            else:
                figs = "".join(f"<figure>{self.bild(b)}</figure>" for b in bilder[:2])
                einzeln = " einzeln" if layout == "ein-bild" else ""
                gespiegelt = " gespiegelt" if i % 2 == 1 else ""
                bloecke.append(f'<div class="ausflug{gespiegelt}"><div class="bilder{einzeln}">{figs}</div><div class="text">{text}</div></div>')
        return f"""<section id="entdeckt">
  <div class="wrap">
    {self.ui_el("span", "umgebung", "label")}
    {self.ui_el("h2", "umgebung_h")}
    {chr(10).join(bloecke)}
  </div>
</section>
"""

    def fotos(self):
        f = self.d["fotos"]
        groessen = {"breit": "f-breit", "schmal": "f-schmal", "drittel": "f-drittel"}
        figs = []
        for b in f["bilder"]:
            cls = groessen.get(b.get("groesse"), "f-drittel")
            text = self.el("span", b["text"]) if b.get("text") else ""
            figs.append(f'<figure class="{cls}">{self.bild(b)}<figcaption>{self.el("b", b["titel"])}{text}</figcaption></figure>')
        einleitung = self.el("p", f.get("einleitung"), "schmal") if f.get("einleitung") else ""
        return f"""<section class="erlebt" id="erlebt">
  <div class="wrap">
    {self.ui_el("span", "fotos", "label")}
    {self.ui_el("h2", "fotos_h")}
    {einleitung}
    <div class="fotos">
      {chr(10).join(figs)}
    </div>
  </div>
</section>
"""

    def projektstand(self):
        p = self.d.get("projektstand")
        if not p:
            return ""
        stand = self.d["meta"].get("stand")
        label = {sp: self.ui("stand", sp) + (" " + datum(stand, sp) if stand else "") for sp in self.sprachen}
        klassen = {"fertig": " fertig", "bald": " bald", "offen": ""}
        items = "".join(
            f'<li class="{klassen[z["status"]].strip()}">{self.el("span", z["wann"], "wann")}{self.el("h3", z["titel"])}{self.el("p", z["text"])}</li>'
            for z in p["zeitleiste"])
        return f"""<section class="stand" id="stand">
  <div class="wrap">
    {self.el("span", label, "label")}
    {self.ui_el("h2", "stand_h")}
    {self.el("p", p.get("einleitung"), "schmal") if p.get("einleitung") else ""}
    <ul class="zeitleiste">{items}</ul>
    {self.el("p", p.get("fazit"), "gelegenheit") if p.get("fazit") else ""}
  </div>
</section>
"""

    def ueberblick(self):
        u = self.d.get("ueberblick")
        if not u:
            return ""
        galerie = ""
        if u.get("galerie"):
            figs = []
            for i, b in enumerate(u["galerie"]):
                cls = "breit" if i == 0 else "halb" if i in (2, 3) else ""
                cap = self.el("figcaption", b.get("bildunterschrift")) if b.get("bildunterschrift") else ""
                figs.append(f'<figure class="{cls}">{self.bild(b)}{cap}</figure>')
            galerie = f'<div class="galerie">{"".join(figs)}</div>'
        hinweis = self.el("p", u.get("galerie_hinweis"), "hinweis") if u.get("galerie_hinweis") else ""
        ausstattung = f'<ul class="ausstattung">{"".join(self.el("li", a) for a in u.get("ausstattung", []))}</ul>' if u.get("ausstattung") else ""
        text = self.el("p", u.get("text") or self.d["objekt"].get("kurzbeschreibung"), "schmal")
        return f"""<section class="resort" id="resort">
  <div class="wrap">
    {self.ui_el("span", "resort", "label")}
    <h2>{html.escape(self.d["objekt"]["name"])}</h2>
    {text}
    {galerie}
    {hinweis}
    {ausstattung}
  </div>
</section>
"""

    def nutzung(self):
        n = self.d.get("nutzung")
        if not n:
            return ""
        saisons = "".join(
            f'<div class="saison">{self.el("span", s["name"], "name")}{self.el("div", s["nutzung"], "zahl")}'
            f'<p class="zeit">{"<br>".join(self.el("span", z) for z in s["zeitraeume"])}</p></div>'
            for s in n.get("saisons", []))
        paket = ""
        if n.get("paket"):
            paket = f'<div class="paket">{self.el("h3", n["paket"].get("titel"))}{self.el("p", n["paket"].get("text"))}</div>'
        return f"""<section class="nutzung" id="nutzung">
  <div class="wrap">
    {self.ui_el("span", "nutzung", "label")}
    {self.el("h2", n.get("titel")) if n.get("titel") else ""}
    {self.el("p", n.get("einleitung"), "einleitung") if n.get("einleitung") else ""}
    {f'<div class="saisons">{saisons}</div>' if saisons else ""}
    {self.el("p", n.get("fazit"), "fazit") if n.get("fazit") else ""}
    {paket}
    {self.el("p", n.get("hinweis"), "hinweis") if n.get("hinweis") else ""}
  </div>
</section>
"""

    def anreise(self):
        a = self.d.get("anreise")
        if not a:
            return ""
        wege = "".join(f'<li>{self.el("span", w["dauer"], "dauer")}{self.el("span", w["text"])}</li>' for w in a.get("wege", []))
        region = ""
        if a.get("region"):
            r = a["region"]
            region = f'<div class="kasten">{self.el("h3", r.get("titel"))}{"".join(self.el("p", p) for p in r.get("absaetze", []))}{self.links(r.get("links"))}</div>'
        return f"""<section class="anreise" id="anreise">
  <div class="wrap raster">
    <div>
      {self.ui_el("span", "anreise", "label")}
      {self.ui_el("h2", "anreise_h")}
      <ul class="wege">{wege}</ul>
      {self.el("p", a.get("hinweis"), "quelle") if a.get("hinweis") else ""}
      {self.links(a.get("links"))}
    </div>
    {region}
  </div>
</section>
"""

    def offen(self):
        o = self.d.get("offen")
        if not o or not self.d["objekt"].get("praemie_offenlegen", True):
            return ""
        return f"""<section class="offen" id="offen">
  <div class="wrap schmal">
    {self.ui_el("span", "offen", "label")}
    {self.el("blockquote", o["zitat"])}
    {self.el("p", o.get("text"), "nach") if o.get("text") else ""}
  </div>
</section>
"""

    def kontakt(self):
        k = self.d["kontakt"]
        g = self.d["gastgeber"]
        schritte = "".join(
            f'<div class="schritt"><span class="nr">{i + 1}</span>{self.el("p", s)}</div>' for i, s in enumerate(k["schritte"]))
        hrefs = "".join(f' data-href-{sp}="{html.escape(self.mailto(sp))}"' for sp in self.sprachen)
        mail_label = {sp: f'{self.ui("mail", sp)} {g["anzeigename"]}' for sp in self.sprachen}
        telefon = ""
        if g["kontakt"].get("telefon"):
            tel = g["kontakt"]["telefon"]
            telefon = f'<p class="telefon">{self.ui_el("span", "oder_sie" if self.sie else "oder")} <a href="tel:{html.escape(re.sub(r"[^+0-9]", "", tel))}">{html.escape(tel)}</a></p>'
        bild = self.bild(k["bild"]) if k.get("bild") else ""
        return f"""<section class="kontakt" id="kontakt">
  {bild}
  <div class="wrap">
    {self.ui_el("span", "neugierig", "label")}
    {self.el("h2", k.get("titel") or {sp: self.ui("kontakt_sie" if self.sie else "kontakt", sp) for sp in self.sprachen})}
    {self.el("p", k.get("text")) if k.get("text") else ""}
    <div class="schritte">{schritte}</div>
    {self.el("a", mail_label, "knopf", f'id="mail" href="{html.escape(self.mailto(self.std))}"{hrefs}')}
    {telefon}
  </div>
</section>
"""

    def fuss(self):
        f = self.d["fuss"]
        disclaimer = "".join(self.el("p", t) for t in f["disclaimer"])
        nachweis = ""
        if f.get("bildnachweis"):
            teile = []
            for b in f["bildnachweis"]:
                lizenz = f'<a href="{html.escape(b["lizenz_url"])}" target="_blank" rel="noopener">{html.escape(b["lizenz"])}</a>' if b.get("lizenz_url") else html.escape(b["lizenz"])
                teile.append(f'{html.escape(os.path.splitext(os.path.basename(b["bild"]))[0])} – {html.escape(b["urheber"])}, {lizenz}')
            nachweis = f'<p class="bildnachweis">{self.ui_el("span", "bildnachweis")} {" · ".join(teile)}</p>'
        return f"""<footer>
  <div class="wrap">
    {disclaimer}
    {nachweis}
  </div>
</footer>
"""

    def skript(self):
        m = self.d["meta"]
        titel = {sp: self.txt(self.d["hero"]["titel"], sp) for sp in self.sprachen}
        ablauf = m.get("gueltig_bis", "")
        ablauf_text = {sp: self.txt(m.get("ablauf_hinweis"), sp) or self.ui("abgelaufen", sp) for sp in self.sprachen}
        return f"""<script>
(function () {{
  var sprachen = {json.dumps(self.sprachen)};
  var standard = {json.dumps(self.std)};
  var titel = {json.dumps(titel, ensure_ascii=False)};
  var gueltigBis = {json.dumps(ablauf)};
  var ablaufText = {json.dumps(ablauf_text, ensure_ascii=False)};
  var texte = document.querySelectorAll('[data-i18n]');
  var mail = document.getElementById('mail');
  var knoepfe = document.querySelectorAll('.sprache button');

  function setze(sprache) {{
    if (sprachen.indexOf(sprache) < 0) sprache = standard;
    texte.forEach(function (el) {{
      var t = el.getAttribute('data-' + sprache) || el.getAttribute('data-' + standard);
      if (t !== null) el.innerHTML = t;
    }});
    if (mail) mail.setAttribute('href', mail.getAttribute('data-href-' + sprache) || mail.getAttribute('data-href-' + standard));
    document.documentElement.lang = sprache;
    document.title = titel[sprache] || titel[standard];
    knoepfe.forEach(function (k) {{ k.setAttribute('aria-pressed', String(k.getAttribute('data-lang') === sprache)); }});
    try {{ localStorage.setItem('sprache', sprache); }} catch (e) {{}}
    return sprache;
  }}

  knoepfe.forEach(function (k) {{ k.addEventListener('click', function () {{ setze(k.getAttribute('data-lang')); }}); }});

  var leiste = document.querySelector('nav');
  function leisteAnpassen() {{ if (leiste) leiste.classList.toggle('fest', window.scrollY > 80); }}
  window.addEventListener('scroll', leisteAnpassen, {{ passive: true }});
  leisteAnpassen();

  // Startsprache: ?lang= im Link > gespeicherte Wahl > Browsersprache
  var start = (location.search.match(/[?&]lang=([a-z]{{2}})/) || [])[1];
  if (!start) {{ try {{ start = localStorage.getItem('sprache'); }} catch (e) {{}} }}
  if (!start) {{ var b = (navigator.language || standard).slice(0, 2).toLowerCase(); start = sprachen.indexOf(b) >= 0 ? b : standard; }}
  var aktiv = setze(start);

  // Laufzeit: nach Ablauf nur noch den Hinweis zeigen
  if (gueltigBis && new Date() > new Date(gueltigBis + 'T23:59:59')) {{
    document.body.innerHTML = '<div class="abgelaufen"><div><h1>' + (ablaufText[aktiv] || ablaufText[standard]) + '</h1></div></div>';
  }}
}})();
</script>
</body>
</html>
"""

    def render(self):
        teile = [self.kopf(), self.nav(), self.hero(), self.brief(), self.gruende(), self.eigenes_objekt(),
                 self.umgebung(), self.fotos(), self.projektstand(), self.ueberblick(), self.nutzung(),
                 self.anreise(), self.offen(), self.kontakt(), self.fuss(), self.skript()]
        return "".join(teile)


def pruefen(daten):
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        sys.exit("Für --pruefen wird das Paket jsonschema benötigt (z. B. uv run --with jsonschema …).")
    schema = json.load(open(os.path.join(HIER, "..", "docs", "schema", "seite.schema.json"), encoding="utf-8"))
    fehler = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(daten))
    if fehler:
        for e in fehler:
            print("FEHLER", "/".join(str(p) for p in e.path) or "(Wurzel)", "–", e.message, file=sys.stderr)
        sys.exit(f"{len(fehler)} Fehler im JSON – nichts erzeugt.")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    quelle, ziel = args
    daten = json.load(open(quelle, encoding="utf-8"))
    if "--pruefen" in sys.argv:
        pruefen(daten)
    m = daten["meta"]
    if m.get("gueltig_bis") and date.fromisoformat(m["gueltig_bis"]) < date.today():
        print(f"Hinweis: gueltig_bis {m['gueltig_bis']} liegt in der Vergangenheit – die Seite zeigt nur den Ablauf-Hinweis.")
    os.makedirs(ziel, exist_ok=True)
    pfad = os.path.join(ziel, "index.html")
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(Seite(daten).render())
    fehlend = []
    for b in re.findall(r'src="(bilder/[^"]+)"', open(pfad, encoding="utf-8").read()):
        if not os.path.exists(os.path.join(ziel, b)):
            fehlend.append(b)
    print(f"{pfad} geschrieben ({len(daten['meta']['sprachen'])} Sprachen).")
    if fehlend:
        print("Fehlende Bilder im Ausgabeordner:", ", ".join(sorted(set(fehlend))))


if __name__ == "__main__":
    main()
