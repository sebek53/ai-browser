"""Testy ekstrakcji i sieci na wspólnej stronie testowej (ta sama co w wersji Rust)."""

import ipaddress
from pathlib import Path

import pytest

from ai_browser import extract
from ai_browser.net import prywatny

STRONA = (Path(__file__).parents[2] / "tests" / "fixtures" / "strona.html").read_text(encoding="utf-8")
BAZA = "https://example.com/katalog/"


def _nr(migawka: str, fraza: str) -> int:
    linia = next(l for l in migawka.splitlines() if fraza in l)
    return int(linia[1:linia.index("]")])


def test_czytaj_bierze_article_bez_szumu():
    t = extract.czytaj(STRONA, BAZA)
    assert "# Zażółć gęślą jaźń" in t
    assert "- punkt pierwszy" in t
    assert "Menu główne" not in t and "alert" not in t and "ukryte" not in t


def test_czytaj_z_linkami():
    assert "więcej -> https://example.com/katalog/dalej" in extract.czytaj(STRONA, BAZA, linki=True)


def test_migawka_i_tabele():
    m = extract.migawka(STRONA)
    assert "Tytuł: Test" in m
    assert '[1] link "Start"' in m
    assert 'input[text] name=q "Szukaj"' in m
    t = extract.tabele(STRONA)
    assert "Nazwa | Cena" in t and "Śruba | 2 zł" in t


def test_wyciagnij_atrybut():
    assert extract.wyciagnij(STRONA, "article a", "href") == "dalej"
    with pytest.raises(ValueError):
        extract.wyciagnij(STRONA, "[[[")


def test_formularze_get_i_post():
    m = extract.migawka(STRONA)
    w = {_nr(m, "name=q"): "śruby M8"}
    a = extract.wyslij(STRONA, BAZA, _nr(m, "name=q"), w)
    assert (a.url, a.post) == ("https://example.com/szukaj?q=%C5%9Bruby+M8&lang=pl", None)

    nr_sel = _nr(m, "select name=kolor")
    w[nr_sel] = extract.wartosc_opcji(STRONA, nr_sel, "Zielony")
    a = extract.kliknij(STRONA, BAZA, _nr(m, "button name=ok"), w)
    assert a.url == "https://example.com/zamow"
    assert a.post == [("kolor", "g"), ("zgoda", "tak"), ("ok", "1")]

    assert extract.kliknij(STRONA, BAZA, 1, w).url == "https://example.com/"


def test_prawie_pusta_strona():
    from ai_browser.server import prawie_pusta

    antybot = '<html><head><script src="/_Incapsula_Resource"></script></head><body><iframe></iframe></body></html>'
    assert prawie_pusta(antybot, BAZA)
    assert not prawie_pusta(STRONA.replace("Pierwszy", "Pierwszy " * 50), BAZA)


def test_adresy_prywatne():
    for a in ["127.0.0.1", "10.1.2.3", "172.16.0.1", "192.168.1.1", "169.254.169.254", "100.64.0.1", "::1", "fd00::1", "::ffff:10.0.0.1"]:
        assert prywatny(ipaddress.ip_address(a)), a
    assert not prywatny(ipaddress.ip_address("93.184.216.34"))
