"""Wyszukiwanie w internecie: DuckDuckGo HTML (bez klucza) albo Brave Search API (klucz w BRAVE_API_KEY)."""

from __future__ import annotations

import json
import os
import time
from urllib.parse import parse_qs, quote_plus, urlsplit

from selectolax.lexbor import LexborHTMLParser

from .net import Siec

DDG = "https://html.duckduckgo.com/html/"
BRAVE = "https://api.search.brave.com/res/v1/web/search"
MAX_WYNIKOW = 50
# ponytail: stałe dobrane testem (blokada po ~6 zapytaniach co 1 s, mija po ~20 s); strojenie wg zgłoszeń
ODSTEP_DDG = 4.0  # sekundy między zapytaniami do DDG
PRZERWA_PO_BLOKADZIE = 20.0
_ostatnie_ddg = 0.0


def _pobierz_ddg(siec: Siec, url: str, post: list[tuple[str, str]] | None = None):
    """Pobranie z DDG z dłuższym odstępem niż zwykły limit 1 żądanie/s."""
    global _ostatnie_ddg
    czekaj = ODSTEP_DDG - (time.monotonic() - _ostatnie_ddg)
    if czekaj > 0:
        time.sleep(czekaj)
    try:
        return siec.pobierz(url, post)
    finally:
        _ostatnie_ddg = time.monotonic()


def _cel_ddg(href: str) -> str | None:
    """Prawdziwy adres z przekierowania DDG (//duckduckgo.com/l/?uddg=…); None dla reklam."""
    if "duckduckgo.com/l/" not in href:
        return href if href.startswith("http") else None
    cel = parse_qs(urlsplit(href).query).get("uddg", [""])[0]
    # Reklamy prowadzą przez duckduckgo.com/y.js
    return None if not cel or "duckduckgo.com/y.js" in cel else cel


def wyniki_ddg(html: str) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]] | None]:
    """Wyniki (tytuł, adres, opis) i pola formularza następnej strony (None = brak)."""
    doc = LexborHTMLParser(html)
    wyniki = []
    for blok in doc.css(".result"):
        a = blok.css_first("a.result__a")
        if a is None:
            continue
        cel = _cel_ddg(a.attributes.get("href") or "")
        if cel is None:
            continue
        opis = blok.css_first(".result__snippet")
        wyniki.append((" ".join(a.text().split()), cel, " ".join(opis.text().split()) if opis else ""))
    form = doc.css_first(".nav-link form")
    dalej = None
    if form is not None:
        dalej = [(i.attributes.get("name") or "", i.attributes.get("value") or "")
                 for i in form.css("input[type=hidden]") if i.attributes.get("name")]
    return wyniki, dalej


def _ddg(siec: Siec, zapytanie: str, region: str, ile: int) -> list[tuple[str, str, str]]:
    # Region DDG, np. uk-en, pl-pl, us-en; wt-wt = bez regionu
    adres = f"{DDG}?q={quote_plus(zapytanie)}&kl={quote_plus(region)}"
    wyniki, dalej = [], None
    # Przy zbyt częstych zapytaniach DDG pokazuje CAPTCHA (HTTP 202) na ok. 20 s – nie omijamy jej, czekamy raz
    for proba in range(2):
        if proba:
            time.sleep(PRZERWA_PO_BLOKADZIE)
        strona = _pobierz_ddg(siec, adres)
        wyniki, dalej = wyniki_ddg(strona.html)
        if wyniki or "anomaly" not in strona.html.lower():
            break
    else:
        raise RuntimeError("DuckDuckGo tymczasowo blokuje zapytania (CAPTCHA); spróbuj za minutę "
                           "albo ustaw BRAVE_API_KEY")
    while len(wyniki) < ile and dalej:
        nowe, dalej = wyniki_ddg(_pobierz_ddg(siec, DDG, dalej + [("kl", region)]).html)
        if not nowe:
            break
        wyniki += nowe
    return wyniki


def _brave(siec: Siec, klucz: str, zapytanie: str, region: str, ile: int) -> list[tuple[str, str, str]]:
    kraj = region.split("-")[0].upper()  # uk-en -> UK; Brave używa GB
    kraj = "GB" if kraj == "UK" else kraj
    wyniki: list[tuple[str, str, str]] = []
    for strona in range(0, 5):  # Brave: do 20 wyników na stronę, offset w stronach
        siec.czekaj(BRAVE)
        odp = siec.klient.get(BRAVE, params={"q": zapytanie, "count": 20, "offset": strona,
                                              **({"country": kraj} if kraj != "WT" else {})},
                              headers={"X-Subscription-Token": klucz, "Accept": "application/json"})
        if odp.status_code != 200:
            raise RuntimeError(f"Brave Search API: HTTP {odp.status_code}")
        dane = json.loads(odp.text).get("web", {}).get("results", [])
        wyniki += [(w.get("title", ""), w.get("url", ""), w.get("description", "")) for w in dane]
        if len(wyniki) >= ile or len(dane) < 20:
            break
    return wyniki


def szukaj(siec: Siec, zapytanie: str, region: str = "wt-wt", ile: int = 10) -> str:
    """Wyniki wyszukiwania jako zwięzła lista; Brave gdy jest klucz, inaczej DuckDuckGo."""
    ile = max(1, min(ile, MAX_WYNIKOW))
    klucz = os.environ.get("BRAVE_API_KEY")
    wyniki = _brave(siec, klucz, zapytanie, region, ile) if klucz else _ddg(siec, zapytanie, region, ile)
    # Bez duplikatów adresów
    unikalne = list({w[1]: w for w in wyniki}.values())[:ile]
    if not unikalne:
        return "(brak wyników)"
    return "\n".join(f"{n}. {t}\n   {u}\n   {o}" for n, (t, u, o) in enumerate(unikalne, 1))
