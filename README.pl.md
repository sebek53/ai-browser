# ai-browser

[English](README.md) | **Polski**

Lekka przeglądarka dla agentów AI (serwer MCP). Zamiast zrzutów ekranu i surowego HTML
zwraca zwięzły tekst, więc agent zużywa dużo mniej tokenów.

Narzędzia: `navigate`, `read`, `tables`, `snapshot`, `extract`, `click`, `type`, `select`, `back`.

## Instalacja

Instrukcja dla użytkowników (instalacja przez `uvx`, podpięcie do Claude Code i Claude Desktop, użycie,
rozwiązywanie problemów): **[python/README.pl.md](python/README.pl.md)**.

## Wyniki (24 strony testowe)

| | surowy HTML | zrzuty ekranu (szac.) | `read` | `extract` |
|---|---|---|---|---|
| tokeny łącznie | 2 121 553 | 666 120 | 297 072 | 11 609 |

- `read`: ok. 7 razy mniej tokenów niż surowy HTML, ok. 2 razy mniej niż zrzuty ekranu
  (w praktyce jeszcze mniej – domyślny limit to 8000 znaków, resztę pobiera się przez `offset`).
- `extract` (selektor CSS): ok. 180 razy mniej niż surowy HTML i ok. 57 razy mniej niż zrzuty ekranu.
- Pamięć: ok. 20 MB.

Tokeny szacowane jako znaki/4. Skrypt testowy: [tests/bench/sprawdz.ps1](tests/bench/sprawdz.ps1)
(tokeny + poprawność: klik, formularze, back, robots.txt, SSRF, 404, przekierowania, JSON). Kod jest w [python/](python/).

## Ustawienia (zmienne środowiskowe)

- `AI_BROWSER_CONTACT` – opcjonalny kontakt dopisywany do User-Agent (np. `mailto:ja@example.com`).
- `AI_BROWSER_ALLOW_PRIVATE=1` – zezwala na adresy prywatne (localhost, 192.168…); domyślnie blokowane.

## Zasady i bezpieczeństwo

- Uczciwy User-Agent `ai-browser/<wersja>`, respektowanie `robots.txt`, najwyżej 1 żądanie na sekundę na host,
  odpowiedź `429` przekazywana agentowi. Bez omijania CAPTCHA i zabezpieczeń antybotowych.
- Blokada SSRF: adresy prywatne sprawdzane po DNS i przy każdym przekierowaniu.
- Każda odpowiedź oznaczona jako niezaufane dane ze strony (ochrona przed prompt injection).

## Ograniczenia

- JavaScript tylko w opcjonalnym trybie JS (Chromium); bez niego strony renderowane wyłącznie w JS (SPA) zwracają niewiele treści.
- Na niektórych stronach `read` zaczyna się od szumu (np. lista języków na Wikipedii) – wtedy lepiej użyć `extract`.
- Brak kart, przewijania i zrzutów ekranu.

## Wsparcie autora

Projekt jest darmowy. Jeśli oszczędza Ci tokeny, możesz postawić autorowi piwo 🍺

[buycoffee.to/sebastian.garstka](https://buycoffee.to/sebastian.garstka) (BLIK, przelew) · [ko-fi.com/sebastiangarstka](https://ko-fi.com/sebastiangarstka)
