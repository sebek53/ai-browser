"""Dane kontaktowe z listy stron: nazwa, e-maile, telefony (z podstrony kontaktowej, gdy trzeba)."""

from __future__ import annotations

import re
from urllib.parse import unquote, urljoin, urlsplit

from selectolax.lexbor import LexborHTMLParser

from .net import Siec

MAX_STRON = 50
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Odrzucamy „e-maile” będące nazwami plików, np. logo@2x.png
NIE_EMAIL = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", "example.com", "sentry.io", "wixpress.com")
SLOWA_KONTAKT = ("contact", "kontakt", "get-in-touch", "about")


def _nazwa(doc: LexborHTMLParser) -> str:
    meta = doc.css_first('meta[property="og:site_name"]')
    if meta and meta.attributes.get("content"):
        return meta.attributes["content"].strip()
    tytul = doc.css_first("title")
    return " ".join(tytul.text().split())[:80] if tytul else "(bez nazwy)"


def dane(html: str) -> tuple[str, list[str], list[str]]:
    """Nazwa, e-maile i telefony ze strony (linki mailto/tel oraz e-maile w tekście)."""
    doc = LexborHTMLParser(html)
    maile, telefony = [], []
    for a in doc.css('a[href^="mailto:"], a[href^="tel:"]'):
        href = unquote(a.attributes.get("href") or "")
        wartosc = href.split(":", 1)[1].split("?")[0].strip()
        (maile if href.lower().startswith("mailto:") else telefony).append(wartosc)
    tekst = doc.body.text(separator=" ") if doc.body else ""
    maile += EMAIL.findall(tekst)
    maile = [m for m in dict.fromkeys(m.lower() for m in maile) if not m.endswith(NIE_EMAIL) and "@" in m]
    # Telefony porównujemy po samych cyfrach, żeby „0141 352 6800” i „01413526800” były jednym
    unikalne: dict[str, str] = {}
    for t in telefony:
        unikalne.setdefault(re.sub(r"\D", "", t), t)
    return _nazwa(doc), maile[:5], list(unikalne.values())[:5]


def strona_kontaktowa(html: str, baza: str) -> str | None:
    """Link do podstrony kontaktowej w tej samej domenie."""
    host = urlsplit(baza).hostname
    for a in LexborHTMLParser(html).css("a[href]"):
        href = a.attributes.get("href") or ""
        opis = (href + " " + a.text()).lower()
        url = urljoin(baza, href)
        if any(s in opis for s in SLOWA_KONTAKT[:3]) and urlsplit(url).hostname == host:
            return url
    return None


def kontakty(siec: Siec, adresy: list[str]) -> str:
    """Jedna linia na stronę: nazwa | e-mail | telefon | adres."""
    linie = []
    for adres in list(dict.fromkeys(adresy))[:MAX_STRON]:
        adres = adres if "://" in adres else f"https://{adres}"
        try:
            s = siec.pobierz(adres)
            nazwa, maile, telefony = dane(s.html)
            if not maile or not telefony:
                kontakt = strona_kontaktowa(s.html, s.url)
                if kontakt and kontakt != s.url:
                    _, m2, t2 = dane(siec.pobierz(kontakt).html)
                    maile = list(dict.fromkeys(maile + m2))[:5]
                    telefony = list(dict.fromkeys(telefony + t2))[:5]
            linie.append(f"{nazwa} | {', '.join(maile) or '–'} | {', '.join(telefony) or '–'} | {s.url}")
        except RuntimeError as e:
            linie.append(f"(błąd) | – | – | {adres} ({e})")
    return "\n".join(linie) or "(brak adresów)"
