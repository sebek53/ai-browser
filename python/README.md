# ai-browser

**Polski** | [English](README.en.md)

Lekka przeglądarka dla agentów AI (serwer MCP). Zamiast zrzutów ekranu i surowego HTML zwraca zwięzły tekst,
więc agent zużywa dużo mniej tokenów.

## Korzyści

- **Taniej przy wyciąganiu danych:** `extract` (ceny, tytuły, tabele) zużywa od kilku do ponad 1000 razy mniej
  tokenów niż czytanie całej strony (Wikipedia: 121 znaków zamiast 180 tys.). To główna oszczędność.
- **Czytanie całej strony** (`read`) zwraca mniej więcej tyle tekstu, co zwykła przeglądarka – ale ok. 7 razy mniej
  niż surowy HTML i bez zrzutów ekranu. Domyślny limit 8000 znaków chroni przed wciągnięciem ogromnej strony naraz.
- **Szybciej:** strona otwiera się w ułamku sekundy, bez uruchamiania pełnej przeglądarki.
- **Lżej:** ok. 20 MB pamięci (pełna przeglądarka zajmuje setki MB).
- **Dokładniej:** agent dostaje czysty tekst bez menu, reklam i stopek, więc rzadziej się myli.
- **Scraping jednym poleceniem:** „wypisz wszystkie ceny z tej strony” – agent sam dobiera selektor.
- **Wyszukiwanie bez klucza:** `search` szuka w internecie (DuckDuckGo) z wyborem kraju, np. `region=pl-pl`, `uk-en`.
- **Kontakty hurtowo:** `contacts` zbiera e-maile i telefony z wielu stron naraz (także z podstrony „Kontakt”).
- **Formularze:** wyszukiwarki, filtry, listy wyboru – bez JavaScriptu.
- **Bezpiecznie:** blokada adresów sieci wewnętrznej, oznaczanie treści stron jako niezaufanej (ochrona przed
  prompt injection), respektowanie `robots.txt`.

Narzędzia: `navigate`, `read`, `tables`, `snapshot`, `extract`, `click`, `type`, `select`, `back`, `crawl`, `search`, `contacts`.

## Instalacja

> **Wklej komendy sam w terminalu** (PowerShell / cmd / Terminal). Nie proś Claude'a, żeby to zainstalował:
> Claude z zasady nie uruchamia kodu z zewnętrznych repozytoriów i odmówi. To zabezpieczenie, nie błąd.

1. Zainstaluj [uv](https://docs.astral.sh/uv/) (jednorazowo). Windows:

```
winget install astral-sh.uv
```

macOS / Linux:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Zamknij i otwórz ponownie terminal, potem podepnij przeglądarkę do Claude Code:

```
claude mcp add --scope user ai-browser -- uvx --from git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python ai-browser
```

3. Sprawdzenie: `claude mcp get ai-browser` powinno pokazać `Connected`.

### Claude Desktop i inni klienci MCP

1. W Claude Desktop otwórz **Ustawienia → Developer → Edit Config**. Otworzy się plik `claude_desktop_config.json`
   (Windows: `%APPDATA%\Claude\`, macOS: `~/Library/Application Support/Claude/`).
2. Wklej (jeśli plik ma już `mcpServers`, dopisz tylko wpis `ai-browser`):

```json
{
  "mcpServers": {
    "ai-browser": { "command": "uvx", "args": ["--from", "git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python", "ai-browser"] }
  }
}
```

3. Zamknij Claude Desktop całkowicie (także z zasobnika systemowego) i uruchom ponownie.
4. W nowej rozmowie, w menu narzędzi, powinien być widoczny serwer `ai-browser`.

### Codex (OpenAI)

W terminalu:

```
codex mcp add ai-browser -- uvx --from git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python ai-browser
```

albo dopisz do `~/.codex/config.toml` (Windows: `%USERPROFILE%\.codex\config.toml`):

```toml
[mcp_servers.ai-browser]
command = "uvx"
args = ["--from", "git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python", "ai-browser"]
```

Sprawdzenie: `codex mcp list` powinno pokazać `ai-browser` ze statusem `enabled`. Narzędzia do czytania stron
są oznaczone jako tylko do odczytu, więc Codex może je uruchamiać bez pytania o zgodę; `click` i `type`
(wysyłanie formularzy) wymagają zgody.

Codex domyślnie sięga po swoją wbudowaną przeglądarkę. Żeby sam wybierał ai-browser, dopisz do
`~/.codex/AGENTS.md`:

```
Do czytania stron internetowych i wyciągania z nich danych używaj narzędzi MCP serwera ai-browser
(navigate, read, extract, tables, snapshot), a nie wbudowanej przeglądarki.
```

Jeśli Codex mówi, że nie widzi narzędzi ai-browser (niektóre wersje ukrywają narzędzia zewnętrznych serwerów MCP),
dopisz do `config.toml`:

```toml
[features]
tool_search_always_defer_mcp_tools = false
```

Pierwsze uruchomienie trwa kilka sekund (uv pobiera paczkę), kolejne są natychmiastowe.

## Czy to bezpieczne? Co robi ten kod

- Komenda instaluje **konkretną, przypiętą wersję** (`@v0.1.4`). Kod nie zmieni się sam – aktualizujesz go
  świadomie, podmieniając numer wersji.
- Kod jest krótki i otwarty: 5 plików w [`python/src/ai_browser`](src/ai_browser) (ok. 600 linii). Można go
  przejrzeć przed instalacją.
- Program **łączy się tylko ze stronami, które agent otwiera na Twoją prośbę**. Nie ma telemetrii, nie wysyła
  danych nigdzie indziej, nie czyta plików na dysku.
- Blokuje adresy sieci wewnętrznej (localhost, 192.168…, 10…, adresy metadanych chmury), więc strona nie może
  go użyć do zajrzenia do Twojej sieci firmowej.
- Nie omija CAPTCHA ani zabezpieczeń stron, przedstawia się uczciwie i respektuje `robots.txt`.
- Na komputerze służbowym sprawdź zasady firmy dotyczące instalowania narzędzi – w razie wątpliwości zapytaj dział IT.

## Jak używać

Wystarczy poprosić agenta zwykłym językiem, np.:

- „Otwórz https://books.toscrape.com i wypisz tytuły i ceny książek.”
- „Przeczytaj ten artykuł i streść go w 5 punktach: <adres>.”
- „Wyszukaj na <stronie> frazę X i podaj pierwsze 3 wyniki.”
- „Znajdź drukarnie wielkoformatowe w Glasgow i Edynburgu i zrób tabelę z e-mailem i telefonem.” (`search` + `contacts`)
- „Przejdź po 30 stronach https://books.toscrape.com i wypisz tytuły wszystkich książek.” (`crawl` – po wielu
  podstronach jednej domeny, 1 strona na sekundę, z `robots.txt`; limit domyślnie 20, maksymalnie 200)

Agent sam wybiera narzędzia: `navigate` otwiera stronę, `read` czyta tekst, `extract` wyciąga dane selektorem,
`type`/`click` wypełniają formularze.

### Czy Claude użyje jej automatycznie?

Zwykle tak: serwer przekazuje agentowi instrukcję, żeby wybierał go do czytania i scrapowania stron. Agent
decyduje jednak sam i czasem może sięgnąć po wbudowane pobieranie stron. Żeby zawsze używał ai-browser:

- napisz w prośbie: „użyj ai-browser, żeby …”, albo
- dodaj jedną linię do `CLAUDE.md` (Claude Code) lub instrukcji projektu (Claude Desktop):
  `Do czytania stron internetowych zawsze używaj narzędzi ai-browser.`

Przy pierwszym użyciu Claude pyta o zgodę na uruchomienie narzędzi. Żeby nie pytał w Claude Code, wybierz
„zawsze zezwalaj” albo dopisz `mcp__ai-browser` do listy `allow` w `~/.claude/settings.json`.

### Opcjonalny tryb JavaScript (strony wymagające JS)

Domyślnie ai-browser nie uruchamia JavaScriptu, więc strony zbudowane w całości w JS (aplikacje SPA) wyglądają
na puste. Opcjonalny tryb JS to naprawia: gdy strona okaże się pusta, ai-browser otwiera ją w Chromium bez
okna, czeka na wyrenderowanie i zwraca ten sam zwięzły tekst. Zwykłe strony nadal idą lekkim trybem.

1. Jednorazowo zainstaluj Chromium (ok. 150 MB):

```
uvx --from "ai-browser[js] @ git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python" playwright install chromium
```

2. Podepnij wersję z trybem JS (zamiast podstawowej):

```
claude mcp add --scope user ai-browser -- uvx --from "ai-browser[js] @ git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python" ai-browser
```

Claude Desktop: `"command": "uvx", "args": ["--from", "ai-browser[js] @ git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python", "ai-browser"]`.

Agent może też wymusić tryb JS przez `navigate(url, js=true)`. Wyłączenie: `AI_BROWSER_JS=0`.
Chromium używa tego samego uczciwego User-Agenta, `robots.txt`, limitu tempa i blokady SSRF (sprawdzane jest
każde jego żądanie). Zużycie pamięci rośnie do 150–300 MB tylko wtedy, gdy Chromium działa.

## Aktualizacja i odinstalowanie

- Aktualizacja: w komendzie instalacji podmień `@v0.1.4` na nowszą wersję z
  [listy wydań](https://github.com/sebek53/ai-browser/releases), potem `claude mcp remove ai-browser -s user`
  i ponownie `claude mcp add …`.
- Odinstalowanie: `claude mcp remove ai-browser -s user` lub usunięcie wpisu z `claude_desktop_config.json`.

## Problemy

- **`uvx` nie jest rozpoznawane** – po instalacji uv uruchom ponownie terminal / Claude Desktop.
- **Claude odmawia instalacji** – wklej komendę sam w terminalu (patrz „Instalacja”).
- **„robots.txt tej strony zabrania…”** – strona nie zgadza się na automaty; poszukaj jej oficjalnego API.
- **Pusta treść** – strona działa tylko z JavaScriptem: włącz opcjonalny tryb JS (opis wyżej).

## Ustawienia (zmienne środowiskowe)

- `AI_BROWSER_CONTACT` – kontakt dopisywany do User-Agent (domyślnie adres tego repozytorium).
- `AI_BROWSER_ALLOW_PRIVATE=1` – zezwala na adresy prywatne (localhost, 192.168…); domyślnie blokowane.
- `AI_BROWSER_JS=0` – wyłącza tryb JS.
- `BRAVE_API_KEY` – opcjonalny klucz [Brave Search API](https://brave.com/search/api/) (darmowy limit); `search` używa go zamiast DuckDuckGo – stabilniej przy bardzo wielu zapytaniach.

## Wsparcie autora

Projekt jest darmowy. Jeśli oszczędza Ci tokeny, możesz postawić autorowi piwo 🍺

[buycoffee.to/sebastian.garstka](https://buycoffee.to/sebastian.garstka) (BLIK, przelew) · [ko-fi.com/sebastiangarstka](https://ko-fi.com/sebastiangarstka)
