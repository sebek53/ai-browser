"""Test na żywo: extract() kontra niezależny parser (BeautifulSoup/soupsieve) dla różnych selektorów CSS.

Uruchomienie: uv run --with beautifulsoup4 python tests/porownaj_selektory.py
"""

import httpx
from bs4 import BeautifulSoup

from ai_browser.extract import przytnij, wyciagnij
from ai_browser.net import Siec

# (strona, selektor, atrybut) – różne rodzaje selektorów
PRZYPADKI = [
    ("https://books.toscrape.com/", "article.product_pod h3 a", "title"),            # klasa + potomek + atrybut
    ("https://books.toscrape.com/", ".price_color", None),                           # sama klasa
    ("https://books.toscrape.com/", "p.star-rating.Three", "class"),                 # kilka klas naraz
    ("https://books.toscrape.com/", "ol.row > li:nth-child(2n+1) h3 a", "href"),     # dziecko + nth-child
    ("https://books.toscrape.com/", "a[href*='catalogue/category/books/']", None),   # atrybut zawiera
    ("https://books.toscrape.com/", "img[alt^='A ']", "src"),                        # atrybut zaczyna się od
    ("https://quotes.toscrape.com/", ".quote:first-child .author", None),            # :first-child
    ("https://quotes.toscrape.com/", ".quote .tags a.tag:not([href*='love'])", None),# :not
    ("https://quotes.toscrape.com/", "small.author, span.text", None),               # kilka selektorów
    ("https://quotes.toscrape.com/", "div.quote span:last-of-type a", "href"),        # :last-of-type
    ("https://www.scrapethissite.com/pages/simple/", "#countries .country-name", None),  # id + klasa
    ("https://www.scrapethissite.com/pages/simple/", ".country-capital", None),
    ("https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)", "table.wikitable tr td:first-child a", "title"),
    ("https://en.wikipedia.org/wiki/List_of_largest_cities", "#toc a, .mw-heading h2", None),
]

# Ten sam User-Agent co przeglądarka (z kontaktem – wymaga go np. Wikipedia)
KLIENT = httpx.Client(headers={"User-Agent": Siec().ua}, follow_redirects=True, timeout=30)


def wzorzec(html: str, selektor: str, atrybut: str | None) -> list[str]:
    """Wynik referencyjny z BeautifulSoup w tym samym formacie co extract()."""
    wynik = []
    for e in BeautifulSoup(html, "html.parser").select(selektor):
        if atrybut:
            v = e.get(atrybut)
            if v is not None:
                wynik.append(" ".join(v) if isinstance(v, list) else v)
        else:
            wynik.append(przytnij(e.get_text(), 500))
    return wynik


def main() -> None:
    cache: dict[str, str] = {}
    bledy = 0
    for url, selektor, atrybut in PRZYPADKI:
        if url not in cache:
            odp = KLIENT.get(url)
            odp.raise_for_status()  # strona błędu dałaby fałszywe 0/0
            cache[url] = odp.text
        html = cache[url]
        nasze = wyciagnij(html, selektor, atrybut)
        nasze = [] if nasze == "(brak dopasowań)" else nasze.split("\n")
        ref = wzorzec(html, selektor, atrybut)
        ok = nasze == ref
        bledy += not ok
        print(f"{'OK ' if ok else 'ZLE'} {len(nasze):4} / {len(ref):4}  {selektor}" + (f" @{atrybut}" if atrybut else ""))
        if not ok:
            for i, (a, b) in enumerate(zip(nasze, ref)):
                if a != b:
                    print(f"      pierwsza różnica [{i}]: nasze={a[:70]!r} ref={b[:70]!r}")
                    break
    print(f"\nWynik: {len(PRZYPADKI) - bledy}/{len(PRZYPADKI)} zgodnych")


if __name__ == "__main__":
    main()
