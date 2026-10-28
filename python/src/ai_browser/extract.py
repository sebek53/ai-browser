"""Ekstrakcja treści: tekst główny, migawka [ref], tabele, selektory CSS i formularze."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit

from selectolax.lexbor import LexborHTMLParser, LexborNode

# Elementy pomijane przy wyciąganiu tekstu (szum)
POMIJANE = {"script", "style", "noscript", "template", "svg", "nav", "footer", "aside", "iframe", "head"}

# Role ARIA oznaczające szum (menu, nawigacja, stopka)
ROLE_SZUMU = {"navigation", "menu", "menubar", "banner", "contentinfo", "search"}

# Elementy blokowe – rozdzielane nową linią
BLOKOWE = {
    "p", "div", "section", "article", "main", "header", "br", "li", "tr", "ul", "ol", "table",
    "blockquote", "pre", "form", "dd", "dt", "figure", "figcaption", "h1", "h2", "h3", "h4", "h5", "h6",
}

# Elementy, które dostają numer [ref] w migawce
INTERAKTYWNE = "a[href], button, input:not([type=hidden]), select, textarea"


@dataclass
class Akcja:
    """Wynik kliknięcia / wysłania: url do pobrania (z polami POST) albo komunikat."""

    url: str | None = None
    post: list[tuple[str, str]] | None = None
    komunikat: str | None = None


def _attr(n: LexborNode, nazwa: str) -> str | None:
    return n.attributes.get(nazwa)


def _ma(n: LexborNode, nazwa: str) -> bool:
    return nazwa in n.attributes


def _ukryty(n: LexborNode) -> bool:
    styl = (_attr(n, "style") or "").replace(" ", "")
    return _ma(n, "hidden") or _attr(n, "aria-hidden") == "true" or "display:none" in styl


def porzadkuj(s: str) -> str:
    """Zwija białe znaki w liniach i usuwa puste linie."""
    linie = (" ".join(l.split()) for l in s.splitlines())
    return "\n".join(l for l in linie if l)


def przytnij(s: str, maks: int) -> str:
    s = porzadkuj(s).replace("\n", " ")
    return s if len(s) <= maks else s[:maks] + "…"


def _tekst_wezla(n: LexborNode) -> str:
    return n.text(deep=True, separator="")


# ponytail: tylko main/article/body, heurystyka "największy blok tekstu" gdy to za mało
def _glowny_blok(doc: LexborHTMLParser) -> LexborNode:
    for s in ("main", "[role=main]"):
        if (e := doc.css_first(s)) is not None:
            return e
    # Wiele <article> = lista (np. produkty), wtedy cała strona
    artykuly = doc.css("article")
    if len(artykuly) == 1:
        return artykuly[0]
    return doc.body or doc.root


def _tekst(el: LexborNode, baza: str | None, out: list[str]) -> None:
    for d in el.iter(include_text=True):
        if d.tag == "-text":
            out.append(d.text_content or "")
            continue
        nazwa = d.tag
        if nazwa.startswith(("-", "_", "!")):
            continue  # komentarze, doctype
        if nazwa in POMIJANE or _attr(d, "role") in ROLE_SZUMU or _ukryty(d):
            continue
        blok = nazwa in BLOKOWE
        if blok:
            out.append("\n")
        if nazwa in ("h1", "h2", "h3", "h4", "h5", "h6"):
            out.append("#" * int(nazwa[1]) + " ")
        elif nazwa == "li":
            out.append("- ")
        _tekst(d, baza, out)
        if nazwa in ("td", "th"):
            out.append(" | ")
        elif nazwa == "a" and baza is not None and (href := _attr(d, "href")) is not None:
            out.append(f" -> {urljoin(baza, href)}")
        if blok:
            out.append("\n")


def czytaj(html: str, url: str, linki: bool = False) -> str:
    """Główny tekst strony; linki jako `tekst -> href` tylko gdy `linki`."""
    doc = LexborHTMLParser(html)
    out: list[str] = []
    _tekst(_glowny_blok(doc), url if linki else None, out)
    return porzadkuj("".join(out))


def tabele(html: str, max_tabel: int = 5, max_wierszy: int = 50) -> str:
    """Tabele jako `a | b | c`."""
    doc = LexborHTMLParser(html)
    out: list[str] = []
    for i, t in enumerate(doc.css("table")[:max_tabel], start=1):
        out.append(f"## Tabela {i}")
        for w in t.css("tr")[:max_wierszy]:
            out.append(" | ".join(przytnij(_tekst_wezla(k), 200) for k in w.css("th, td")))
    return "\n".join(out) or "(brak tabel)"


def _elementy(doc: LexborHTMLParser) -> list[LexborNode]:
    """Wszystkie elementy interaktywne w kolejności dokumentu; [ref] = indeks + 1."""
    return doc.css(INTERAKTYWNE)


def _etykieta(e: LexborNode) -> str:
    tekst = przytnij(_tekst_wezla(e), 60)
    opis = next((przytnij(v, 60) for k in ("aria-label", "placeholder", "title", "value")
                 if (v := _attr(e, k)) and v.strip()), "")
    nazwa = f" name={n}" if (n := _attr(e, "name")) else ""
    tekst_lub_opis = tekst or opis
    if e.tag == "a":
        return f'link "{tekst_lub_opis}"'
    if e.tag == "input":
        return f'input[{_attr(e, "type") or "text"}]{nazwa} "{tekst_lub_opis}"'
    if e.tag == "select":
        opcje = ", ".join(przytnij(_tekst_wezla(o), 30) for o in e.css("option")[:8])
        return f"select{nazwa} [{opcje}]"
    return f'{e.tag}{nazwa} "{tekst_lub_opis}"'


def migawka(html: str, maks: int = 120) -> str:
    """Migawka: nagłówki i elementy interaktywne z numerami [ref]."""
    doc = LexborHTMLParser(html)
    interaktywne = {e.mem_id for e in _elementy(doc)}
    tytul = przytnij(_tekst_wezla(t), 120) if (t := doc.css_first("title")) else ""
    out = [f"Tytuł: {tytul}"]
    nr = pokazane = 0
    for e in doc.css(f"h1, h2, h3, {INTERAKTYWNE}"):
        interaktywny = e.mem_id in interaktywne
        if interaktywny:
            nr += 1
        if _ukryty(e):
            continue
        if pokazane >= maks:
            out.append(f"[ucięto: pokazano {maks} pozycji, zwiększ max_items]")
            break
        pokazane += 1
        if interaktywny:
            out.append(f"[{nr}] {_etykieta(e)}")
        else:
            out.append(f"{'#' * int(e.tag[1])} {przytnij(_tekst_wezla(e), 100)}")
    return "\n".join(out)


def wyciagnij(html: str, selektor: str, atrybut: str | None = None) -> str:
    """Dane po selektorze CSS: tekst albo wskazany atrybut, jedna linia na element."""
    doc = LexborHTMLParser(html)
    try:
        wezly = doc.css(selektor)
    except Exception as e:  # selectolax rzuca różne wyjątki dla złych selektorów
        raise ValueError(f"zły selektor CSS: {e}") from e
    if atrybut:
        linie = [v for e in wezly if (v := _attr(e, atrybut)) is not None]
    else:
        linie = [przytnij(_tekst_wezla(e), 500) for e in wezly]
    return "\n".join(linie) or "(brak dopasowań)"


def _element(doc: LexborHTMLParser, nr: int) -> LexborNode:
    elementy = _elementy(doc)
    if not 1 <= nr <= len(elementy):
        raise ValueError(f"brak elementu [{nr}] – zrób snapshot")
    return elementy[nr - 1]


def wartosc_opcji(html: str, nr: int, opcja: str) -> str:
    """Wartość opcji <select> pasująca do `opcja` (po value albo tekście)."""
    el = _element(LexborHTMLParser(html), nr)
    if el.tag != "select":
        raise ValueError(f"[{nr}] to nie jest select")
    for o in el.css("option"):
        tekst = przytnij(_tekst_wezla(o), 1000)
        wartosc = _attr(o, "value")
        wartosc = tekst if wartosc is None else wartosc
        if opcja in (wartosc, tekst):
            return wartosc
    raise ValueError(f'brak opcji "{opcja}" w [{nr}]')


def kliknij(html: str, baza: str, nr: int, wartosci: dict[int, str]) -> Akcja:
    """Kliknięcie elementu [nr]."""
    doc = LexborHTMLParser(html)
    el = _element(doc, nr)
    typ = (_attr(el, "type") or "").lower()
    if el.tag == "a":
        return Akcja(url=urljoin(baza, _attr(el, "href") or ""))
    if (el.tag == "button" and typ not in ("button", "reset")) or (el.tag == "input" and typ in ("submit", "image")):
        return _wyslij_z(doc, baza, el, wartosci, klikniety=el)
    if el.tag == "input" and typ in ("checkbox", "radio"):
        return Akcja(komunikat=f'Pole wyboru: użyj type(ref={nr}, text="on") albo "off".')
    return Akcja(komunikat=f"[{nr}] nie ma akcji bez JavaScriptu (tryb bez JS).")


def wyslij(html: str, baza: str, nr: int, wartosci: dict[int, str]) -> Akcja:
    """Wysłanie formularza, w którym jest element [nr] (np. po wpisaniu tekstu)."""
    doc = LexborHTMLParser(html)
    return _wyslij_z(doc, baza, _element(doc, nr), wartosci, klikniety=None)


def _wyslij_z(doc: LexborHTMLParser, baza: str, el: LexborNode, wartosci: dict[int, str],
              klikniety: LexborNode | None) -> Akcja:
    form = el.parent
    while form is not None and form.tag != "form":
        form = form.parent
    if form is None:
        raise ValueError("element nie jest w formularzu")
    numery = {e.mem_id: i for i, e in enumerate(_elementy(doc), start=1)}
    pola: list[tuple[str, str]] = []
    for pole in form.css("input, select, textarea"):
        nazwa = _attr(pole, "name")
        if not nazwa or _ma(pole, "disabled"):
            continue
        nadpis = wartosci.get(numery.get(pole.mem_id, 0))
        if pole.tag == "textarea":
            wartosc = nadpis if nadpis is not None else _tekst_wezla(pole)
        elif pole.tag == "select":
            if nadpis is not None:
                wartosc = nadpis
            else:
                opcje = pole.css("option")
                o = next((o for o in opcje if _ma(o, "selected")), opcje[0] if opcje else None)
                if o is None:
                    continue
                v = _attr(o, "value")
                wartosc = _tekst_wezla(o).strip() if v is None else v
        else:
            typ = (_attr(pole, "type") or "text").lower()
            if typ in ("submit", "button", "image", "reset", "file"):
                continue
            if typ in ("checkbox", "radio"):
                zaznaczone = _ma(pole, "checked") if nadpis is None else nadpis not in ("", "off", "false", "0")
                if not zaznaczone:
                    continue
                wartosc = _attr(pole, "value") or "on"
            else:
                wartosc = nadpis if nadpis is not None else (_attr(pole, "value") or "")
        pola.append((nazwa, wartosc))
    if klikniety is not None and (n := _attr(klikniety, "name")):
        pola.append((n, _attr(klikniety, "value") or ""))
    url = urljoin(baza, _attr(form, "action") or "")
    if (_attr(form, "method") or "").lower() == "post":
        return Akcja(url=url, post=pola)
    czesci = urlsplit(url)
    return Akcja(url=urlunsplit(czesci._replace(query=urlencode(pola))))
