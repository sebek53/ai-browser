"""Sieć: pobieranie stron, ochrona SSRF, robots.txt, limit tempa i cookies."""

from __future__ import annotations

import ipaddress
import os
import socket
import ssl
import time
from dataclasses import dataclass
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx
import truststore

from . import __version__

NAZWA_UA = "ai-browser"
MAX_PRZEKIEROWAN = 10
ODSTEP_NA_HOST = 1.0  # sekundy


@dataclass
class Strona:
    url: str
    html: str
    js: bool = False  # True = wyrenderowana w Chromium


def prywatny(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Każdy adres niepubliczny: loopback, sieci prywatne, link-local (metadane chmury), CGNAT, ULA."""
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        return prywatny(ip.ipv4_mapped)
    return not ip.is_global


class Siec:
    def __init__(self) -> None:
        # Uczciwy User-Agent; adres kontaktowy z AI_BROWSER_CONTACT
        kontakt = os.environ.get("AI_BROWSER_CONTACT", "https://github.com/sebek53/ai-browser")
        self.ua = f"{NAZWA_UA}/{__version__} (+{kontakt})"
        self.klient = httpx.Client(
            headers={"User-Agent": self.ua},
            follow_redirects=False,  # przekierowania ręcznie, żeby sprawdzić SSRF na każdym kroku
            timeout=30,
            # Magazyn certyfikatów systemu (Windows/macOS/Linux) – działa też w sieciach firmowych
            verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        )
        self.robots: dict[str, RobotFileParser] = {}
        self.ostatnie: dict[str, float] = {}
        self.prywatne_dozwolone = os.environ.get("AI_BROWSER_ALLOW_PRIVATE") == "1"

    def pobierz(self, url: str, post: list[tuple[str, str]] | None = None) -> Strona:
        """Pobiera stronę (GET albo POST z polami formularza), idąc za przekierowaniami."""
        for _ in range(MAX_PRZEKIEROWAN + 1):
            self.sprawdz_adres(url)
            self._sprawdz_robots(url)
            self.czekaj(url)
            try:
                if post is not None:
                    # urlencode zachowuje kolejność i powtórzone nazwy pól
                    odp = self.klient.post(url, content=urlencode(post).encode(),
                                           headers={"Content-Type": "application/x-www-form-urlencoded"})
                else:
                    odp = self.klient.get(url)
            except httpx.HTTPError as e:
                raise RuntimeError(f"nie udało się pobrać {url}: {e}") from e
            if odp.is_redirect:
                cel = odp.headers.get("location")
                if not cel:
                    raise RuntimeError("przekierowanie bez Location")
                url = urljoin(url, cel)
                if odp.status_code not in (307, 308):
                    post = None
                continue
            if odp.status_code == 429:
                raise RuntimeError(f"HTTP 429: serwer prosi o przerwę (Retry-After: {odp.headers.get('retry-after', '?')})")
            if not odp.is_success:
                raise RuntimeError(f"HTTP {odp.status_code} dla {url}")
            typ = odp.headers.get("content-type", "text/html")
            if not any(t in typ for t in ("html", "text", "xml", "json")):
                raise RuntimeError(f"to nie jest strona tekstowa ({typ})")
            return Strona(url=str(odp.url), html=odp.text)
        raise RuntimeError("za dużo przekierowań")

    # ponytail: DNS sprawdzany przed żądaniem, httpx rozwiązuje ponownie (DNS rebinding); własny transport gdy to istotne
    def sprawdz_adres(self, url: str) -> None:
        """Blokada SSRF: tylko http(s) i bez adresów prywatnych (także po DNS)."""
        czesci = urlsplit(url)
        if czesci.scheme not in ("http", "https"):
            raise RuntimeError("dozwolone tylko http i https")
        if self.prywatne_dozwolone:
            return
        if not czesci.hostname:
            raise RuntimeError("brak hosta")
        try:
            adresy = {ipaddress.ip_address(a[4][0].split("%")[0]) for a in socket.getaddrinfo(czesci.hostname, czesci.port or 443)}
        except socket.gaierror as e:
            raise RuntimeError(f"nie można rozwiązać {czesci.hostname}") from e
        for ip in adresy:
            if prywatny(ip):
                raise RuntimeError(f"zablokowano adres sieci prywatnej {ip} (AI_BROWSER_ALLOW_PRIVATE=1 zezwala)")

    def _sprawdz_robots(self, url: str) -> None:
        czesci = urlsplit(url)
        zrodlo = f"{czesci.scheme}://{czesci.netloc}"
        if zrodlo not in self.robots:
            parser = RobotFileParser()
            try:
                odp = self.klient.get(f"{zrodlo}/robots.txt")
                parser.parse(odp.text.splitlines() if odp.is_success else [])
            except httpx.HTTPError:
                parser.parse([])
            self.robots[zrodlo] = parser
        if not self.robots[zrodlo].can_fetch(NAZWA_UA, url):
            raise RuntimeError(f"robots.txt tej strony zabrania pobrania {url}; poszukaj oficjalnego API")

    def czekaj(self, url: str) -> None:
        """Limit tempa: najwyżej jedno żądanie na sekundę na host."""
        host = urlsplit(url).hostname or ""
        minelo = time.monotonic() - self.ostatnie.get(host, 0.0)
        if minelo < ODSTEP_NA_HOST:
            time.sleep(ODSTEP_NA_HOST - minelo)
        self.ostatnie[host] = time.monotonic()
