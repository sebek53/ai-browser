"""Tryb awaryjny: renderowanie stron wymagających JavaScriptu w Chromium (Playwright, opcjonalny dodatek [js])."""

from __future__ import annotations

from urllib.parse import urlsplit

from .net import Siec, Strona

# Jak włączyć tryb JS – pokazywane agentowi, gdy dodatek nie jest zainstalowany
JAK_WLACZYC = (
    'install the optional JS mode: run the server with `uvx --from "ai-browser[js] @ git+https://github.com/sebek53/ai-browser#subdirectory=python" ai-browser` '
    'and once `uvx --from "ai-browser[js] @ git+https://github.com/sebek53/ai-browser#subdirectory=python" playwright install chromium`'
)

# Zasoby niepotrzebne do odczytu treści – nie pobieramy ich (szybciej, mniej transferu)
POMIJANE_ZASOBY = {"image", "media", "font"}
LIMIT_MS = 20_000


class Renderer:
    """Jedna przeglądarka Chromium bez okna, uruchamiana dopiero przy pierwszej stronie wymagającej JS."""

    def __init__(self, siec: Siec) -> None:
        self.siec = siec
        self._pw = None
        self._kontekst = None

    def _uruchom(self) -> None:
        from playwright.sync_api import sync_playwright  # import tutaj: dodatek [js] jest opcjonalny

        self._pw = sync_playwright().start()
        przegladarka = self._pw.chromium.launch(headless=True)
        # Ten sam uczciwy User-Agent co w trybie bez JS
        self._kontekst = przegladarka.new_context(user_agent=self.siec.ua)
        self._kontekst.route("**/*", self._filtr)

    def _filtr(self, route) -> None:
        """Każde żądanie Chromium przechodzi przez blokadę SSRF; obrazy, media i fonty są pomijane."""
        zadanie = route.request
        if urlsplit(zadanie.url).scheme in ("data", "blob"):
            route.continue_()
            return
        if zadanie.resource_type in POMIJANE_ZASOBY:
            route.abort()
            return
        try:
            self.siec.sprawdz_adres(zadanie.url)
        except RuntimeError:
            route.abort()
            return
        route.continue_()

    def renderuj(self, url: str) -> Strona:
        """Otwiera stronę z JavaScriptem i zwraca wyrenderowany HTML."""
        from playwright.sync_api import TimeoutError as PlaywrightTimeout

        if self._kontekst is None:
            self._uruchom()
        self.siec.czekaj(url)  # ten sam limit tempa co w trybie bez JS
        strona = self._kontekst.new_page()
        try:
            try:
                strona.goto(url, wait_until="networkidle", timeout=LIMIT_MS)
            except PlaywrightTimeout:
                pass  # strony z ciągłym ruchem sieciowym: bierzemy to, co zdążyło się wyrenderować
            return Strona(url=strona.url, html=strona.content(), js=True)
        finally:
            strona.close()

    def zamknij(self) -> None:
        if self._pw is not None:
            self._pw.stop()
            self._pw = self._kontekst = None
