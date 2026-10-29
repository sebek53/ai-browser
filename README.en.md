# ai-browser

[Polski](README.md) | **English**

A lightweight browser for AI agents (MCP server). Instead of screenshots or raw HTML
it returns compact text, so the agent uses far fewer tokens.

Tools: `navigate`, `read`, `tables`, `snapshot`, `extract`, `click`, `type`, `select`, `back`.

## Installation

User guide (install with `uvx`, connect to Claude Code / Claude Desktop / Codex, usage, troubleshooting):
**[python/README.en.md](python/README.en.md)**.

## Results (24 test pages)

| | raw HTML | screenshots (est.) | `read` | `extract` |
|---|---|---|---|---|
| total tokens | 2 121 553 | 666 120 | 297 072 | 11 609 |

- `read`: about 7x fewer tokens than raw HTML and about 2x fewer than screenshots
  (in practice even less – the default limit is 8000 characters, the rest is fetched with `offset`).
- `extract` (CSS selector): about 180x fewer tokens than raw HTML and about 57x fewer than screenshots.
- To be fair: compared with plain page text from a browser (innerText), `read` returns a similar amount
  (Wikipedia "Poland": 185k vs 181k characters). The real saving is `extract` – here 121 characters
  instead of 181k – and no screenshots.
- Memory: about 20 MB.

Tokens estimated as characters/4. Test script: [tests/bench/sprawdz.ps1](tests/bench/sprawdz.ps1)
(tokens + correctness: click, forms, back, robots.txt, SSRF, 404, redirects, JSON). Code is in [python/](python/).

## Settings (environment variables)

- `AI_BROWSER_CONTACT` – contact appended to the User-Agent (default: this repository's URL).
- `AI_BROWSER_ALLOW_PRIVATE=1` – allows private addresses (localhost, 192.168…); blocked by default.

## Rules and security

- Honest User-Agent `ai-browser/<version>`, respects `robots.txt`, at most 1 request per second per host,
  `429` responses passed to the agent. No CAPTCHA or anti-bot circumvention.
- SSRF protection: private addresses checked after DNS resolution and on every redirect.
- Every response is marked as untrusted page content (prompt injection protection).

## Limitations

- JavaScript only in the optional JS mode (Chromium); without it, pages rendered only by JS (SPAs) return little content.
- On some pages `read` starts with noise (e.g. Wikipedia's language list) – use `extract` there.
- No tabs, scrolling or screenshots.

## Support the author

The project is free. If it saves you tokens, you can buy the author a beer 🍺

[ko-fi.com/sebastiangarstka](https://ko-fi.com/sebastiangarstka) · [buycoffee.to/sebastian.garstka](https://buycoffee.to/sebastian.garstka) (Poland, BLIK)
