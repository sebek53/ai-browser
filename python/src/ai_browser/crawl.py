"""Crawling serwisu: przejście po podstronach jednej domeny (BFS) z wyciąganiem danych selektorem."""

from __future__ import annotations

from collections import deque
from urllib.parse import urljoin, urlsplit, urlunsplit

from selectolax.lexbor import LexborHTMLParser

from . import extract
from .net import Siec

MAX_STRON = 200
# Pliki, których nie warto pobierać jako stron
POMIJANE_ROZSZERZENIA = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf", ".zip", ".mp4", ".mp3",
                         ".css", ".js", ".ico", ".xml", ".rss")


def normalizuj(url: str) -> str:
    """Adres bez fragmentu (#…), żeby ta sama strona nie była odwiedzana dwa razy."""
    c = urlsplit(url)
    return urlunsplit((c.scheme, c.netloc, c.path or "/", c.query, ""))


def linki(html: str, baza: str, prefiks: str) -> list[str]:
    """Linki strony zaczynające się od prefiksu (ta sama domena), bez plików i duplikatów."""
    wynik: list[str] = []
    for a in LexborHTMLParser(html).css("a[href]"):
        href = (a.attributes.get("href") or "").strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        url = normalizuj(urljoin(baza, href))
        if url.startswith(prefiks) and not urlsplit(url).path.lower().endswith(POMIJANE_ROZSZERZENIA):
            wynik.append(url)
    return list(dict.fromkeys(wynik))


def _tytul(html: str) -> str:
    doc = LexborHTMLParser(html)
    wezel = doc.css_first("title") or doc.css_first("h1")
    return " ".join(wezel.text().split()) if wezel else "(bez tytułu)"


def crawl(siec: Siec, start: str, selektor: str | None = None, atrybut: str | None = None,
          limit: int = 20, prefiks: str | None = None) -> str:
    """Odwiedza do `limit` stron od `start`; z każdej tytuł albo dane po selektorze."""
    limit = max(1, min(limit, MAX_STRON))
    start = normalizuj(start)
    c = urlsplit(start)
    # Domyślnie cała domena startowa; prefiks zawęża np. do /blog/
    prefiks = prefiks or f"{c.scheme}://{c.netloc}/"
    kolejka, widziane = deque([start]), {start}
    wyniki: list[str] = []
    tresci: set[int] = set()  # skróty treści – ta sama strona pod innym adresem (np. / i /index.html)
    odwiedzone = 0
    while kolejka and odwiedzone < limit:
        url = kolejka.popleft()
        odwiedzone += 1
        try:
            # robots.txt, SSRF i limit tempa sprawdza Siec przy każdym pobraniu
            strona = siec.pobierz(url)
        except RuntimeError as e:
            wyniki.append(f"## {url}\n(błąd: {e})")
            continue
        if hash(strona.html) in tresci:
            continue
        tresci.add(hash(strona.html))
        if selektor:
            dane = extract.wyciagnij(strona.html, selektor, atrybut)
            if dane != "(brak dopasowań)":
                wyniki.append(f"## {strona.url}\n{dane}")
        else:
            wyniki.append(f"{strona.url} – {_tytul(strona.html)}")
        for nowy in linki(strona.html, strona.url, prefiks):
            if nowy not in widziane:
                widziane.add(nowy)
                kolejka.append(nowy)
    stopka = f"\n[odwiedzono {odwiedzone} stron; w kolejce zostało {len(kolejka)}"
    stopka += "; zwiększ limit, żeby iść dalej]" if kolejka else "]"
    return ("\n".join(wyniki) or "(brak dopasowań na odwiedzonych stronach)") + stopka
