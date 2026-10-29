"""Pomiar: jaki odsetek popularnych stron wymaga JavaScriptu (tryb bez JS).

Uruchomienie: uv run python tests/odsetek_js.py
"""

from collections import Counter

from ai_browser.extract import czytaj
from ai_browser.net import Siec
from ai_browser.server import prawie_pusta

STRONY = [
    # newsy PL
    "https://www.onet.pl/", "https://www.wp.pl/", "https://www.interia.pl/", "https://wyborcza.pl/",
    "https://www.money.pl/", "https://www.rp.pl/", "https://www.bankier.pl/", "https://www.pap.pl/",
    # sklepy PL
    "https://allegro.pl/", "https://www.olx.pl/", "https://www.ceneo.pl/", "https://www.x-kom.pl/",
    "https://www.mediaexpert.pl/", "https://www.morele.net/", "https://www.empik.com/",
    # urzędy / usługi PL
    "https://www.gov.pl/", "https://www.biznes.gov.pl/", "https://pkp.pl/", "https://www.mbank.pl/",
    # świat – newsy i wiedza
    "https://www.bbc.com/news", "https://www.theguardian.com/international", "https://www.reuters.com/",
    "https://en.wikipedia.org/wiki/Poland", "https://stackoverflow.com/questions", "https://medium.com/",
    # świat – sklepy i serwisy
    "https://www.amazon.com/", "https://www.ebay.com/", "https://www.imdb.com/", "https://www.booking.com/",
    "https://www.airbnb.com/", "https://github.com/trending", "https://www.youtube.com/",
    # aplikacje webowe
    "https://x.com/", "https://www.linkedin.com/", "https://open.spotify.com/", "https://www.figma.com/",
]


def main() -> None:
    siec = Siec()
    wyniki = Counter()
    for url in STRONY:
        try:
            s = siec.pobierz(url)
            if prawie_pusta(s.html, s.url):
                kat = "WYMAGA JS"
            else:
                kat = "OK bez JS"
            opis = f"{len(czytaj(s.html, s.url))} zn. tekstu"
        except RuntimeError as e:
            tekst = str(e)
            kat = "ZABLOKOWANA (robots.txt)" if "robots" in tekst else "ZABLOKOWANA (antybot/błąd)"
            opis = tekst[:70]
        wyniki[kat] += 1
        print(f"{kat:28} {url:50} {opis}")
    print()
    for kat, n in wyniki.most_common():
        print(f"{kat:28} {n:3}  ({n * 100 // len(STRONY)}%)")


if __name__ == "__main__":
    main()
