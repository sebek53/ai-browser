# ai-browser

[English](README.md) | **Polski**

Lekka przeglądarka dla agentów AI (serwer MCP). Zamiast zrzutów ekranu i surowego HTML
zwraca zwięzły tekst: około 7 razy mniej tokenów przy czytaniu i około 180 razy mniej przy wyciąganiu danych selektorem CSS.

Narzędzia: `navigate`, `read`, `tables`, `snapshot`, `extract`, `click`, `type`, `select`, `back`.

## Instalacja

Wymaga [uv](https://docs.astral.sh/uv/). Windows:

```
winget install astral-sh.uv
```

macOS / Linux:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Claude Code

```
claude mcp add --scope user ai-browser -- uvx ai-browser
```

Sprawdzenie: `claude mcp get ai-browser` powinno pokazać `Connected`.

### Claude Desktop i inni klienci MCP

1. W Claude Desktop otwórz **Ustawienia → Developer → Edit Config**. Otworzy się plik `claude_desktop_config.json`
   (Windows: `%APPDATA%\Claude\`, macOS: `~/Library/Application Support/Claude/`).
2. Wklej (jeśli plik ma już `mcpServers`, dopisz tylko wpis `ai-browser`):

```json
{
  "mcpServers": {
    "ai-browser": { "command": "uvx", "args": ["ai-browser"] }
  }
}
```

3. Zamknij Claude Desktop całkowicie (także z zasobnika systemowego) i uruchom ponownie.
4. W nowej rozmowie, w menu narzędzi, powinien być widoczny serwer `ai-browser`.

Pierwsze uruchomienie trwa kilka sekund (uv pobiera paczkę), kolejne są natychmiastowe.

## Jak używać

Wystarczy poprosić agenta zwykłym językiem, np.:

- „Otwórz https://books.toscrape.com i wypisz tytuły i ceny książek.”
- „Przeczytaj ten artykuł i streść go w 5 punktach: <adres>.”
- „Wyszukaj na <stronie> frazę X i podaj pierwsze 3 wyniki.”

Agent sam wybiera narzędzia: `navigate` otwiera stronę, `read` czyta tekst, `extract` wyciąga dane selektorem,
`type`/`click` wypełniają formularze.

### Opcjonalny tryb JavaScript (strony wymagające JS)

Domyślnie ai-browser nie uruchamia JavaScriptu, więc strony zbudowane w całości w JS (aplikacje SPA) wyglądają
na puste. Opcjonalny tryb JS to naprawia: gdy strona okaże się pusta, ai-browser otwiera ją w Chromium bez
okna, czeka na wyrenderowanie i zwraca ten sam zwięzły tekst. Zwykłe strony nadal idą lekkim trybem.

1. Jednorazowo zainstaluj Chromium (ok. 150 MB):

```
uvx --from "ai-browser[js]" playwright install chromium
```

2. Zamiast `uvx ai-browser` używaj `uvx --from "ai-browser[js]" ai-browser`:

```
claude mcp add --scope user ai-browser -- uvx --from "ai-browser[js]" ai-browser
```

Claude Desktop: `"command": "uvx", "args": ["--from", "ai-browser[js]", "ai-browser"]`.

Agent może też wymusić tryb JS przez `navigate(url, js=true)`. Wyłączenie: `AI_BROWSER_JS=0`.
Chromium używa tego samego uczciwego User-Agenta, `robots.txt`, limitu tempa i blokady SSRF (sprawdzane jest
każde jego żądanie). Zużycie pamięci rośnie do 150–300 MB tylko wtedy, gdy Chromium działa.

### Czy Claude użyje jej automatycznie?

Zwykle tak: serwer przekazuje agentowi instrukcję (MCP server instructions), żeby wybierał go do czytania
i scrapowania stron. Agent decyduje jednak sam i czasem może sięgnąć po wbudowane pobieranie stron albo
przeglądarkę. Żeby zawsze używał ai-browser:

- napisz w prośbie: „użyj ai-browser, żeby …”, albo
- dodaj jedną linię do `CLAUDE.md` (Claude Code) lub instrukcji projektu (Claude Desktop):
  `Do czytania stron internetowych zawsze używaj narzędzi ai-browser.`

Przy pierwszym użyciu Claude pyta o zgodę na uruchomienie narzędzi. Żeby nie pytał w Claude Code, wybierz
„zawsze zezwalaj” albo dopisz `mcp__ai-browser` do listy `allow` w `~/.claude/settings.json`.

## Aktualizacja i odinstalowanie

- Aktualizacja: `uvx ai-browser@latest` (albo `uv cache clean ai-browser`).
- Odinstalowanie: `claude mcp remove ai-browser -s user` lub usunięcie wpisu z `claude_desktop_config.json`.

## Problemy

- **`uvx` nie jest rozpoznawane** – po instalacji uv uruchom ponownie terminal / Claude Desktop.
- **„robots.txt tej strony zabrania…”** – strona nie zgadza się na automaty; poszukaj jej oficjalnego API.
- **Pusta treść** – strona działa tylko z JavaScriptem: włącz opcjonalny tryb JS (opis wyżej).

## Ustawienia (zmienne środowiskowe)

- `AI_BROWSER_CONTACT` – kontakt dopisywany do User-Agent (np. `mailto:ja@example.com`).
- `AI_BROWSER_ALLOW_PRIVATE=1` – zezwala na adresy prywatne (localhost, 192.168…); domyślnie blokowane.

## Zasady

Program przedstawia się uczciwie (User-Agent `ai-browser/<wersja>`), respektuje `robots.txt`, wysyła najwyżej
jedno żądanie na sekundę do jednego hosta i nie omija CAPTCHA ani zabezpieczeń antybotowych.
Każda odpowiedź jest oznaczona jako niezaufane dane ze strony.

Strony renderowane wyłącznie JavaScriptem (SPA) wymagają opcjonalnego trybu JS.

## Wsparcie autora

Projekt jest darmowy. Jeśli oszczędza Ci tokeny, możesz postawić autorowi piwo 🍺

[buycoffee.to/sebastian.garstka](https://buycoffee.to/sebastian.garstka) (BLIK, przelew) · [ko-fi.com/sebastiangarstka](https://ko-fi.com/sebastiangarstka)
