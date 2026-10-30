# ai-browser

[Polski](README.md) | **English**

A lightweight browser for AI agents (MCP server). Instead of screenshots or raw HTML it returns compact text,
so the agent uses far fewer tokens.

## Benefits

- **Cheaper data extraction:** `extract` (prices, titles, tables) uses from a few to over 1000x fewer tokens than
  reading the whole page (Wikipedia: 121 characters instead of 180k). This is the main saving.
- **Reading a whole page** (`read`) returns about as much text as a regular browser – but about 7x less than raw
  HTML and no screenshots. The default 8000-character limit keeps huge pages from being pulled in at once.
- **Faster:** pages open in a fraction of a second, without starting a full browser.
- **Lighter:** about 20 MB of memory (a full browser takes hundreds of MB).
- **More accurate:** the agent gets clean text without menus, ads and footers, so it makes fewer mistakes.
- **Scraping in one request:** "list all prices on this page" – the agent picks the selector itself.
- **Search without an API key:** `search` searches the web (DuckDuckGo) with a country, e.g. `region=uk-en`, `pl-pl`.
- **Bulk contacts:** `contacts` collects emails and phone numbers from many sites at once (including their contact page).
- **Forms:** search boxes, filters, drop-downs – without JavaScript.
- **Safe:** blocks internal network addresses, marks page content as untrusted (prompt injection protection),
  respects `robots.txt`.

Tools: `navigate`, `read`, `tables`, `snapshot`, `extract`, `click`, `type`, `select`, `back`, `crawl`, `search`, `contacts`.

## Installation

> **Paste the commands into your terminal yourself** (PowerShell / cmd / Terminal). Do not ask Claude to install it:
> by design Claude does not run code from external repositories and will refuse. That is a safeguard, not a bug.

1. Install [uv](https://docs.astral.sh/uv/) (once). Windows:

```
winget install astral-sh.uv
```

macOS / Linux:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Close and reopen the terminal, then connect the browser to Claude Code:

```
claude mcp add --scope user ai-browser -- uvx --from git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python ai-browser
```

3. Check: `claude mcp get ai-browser` should show `Connected`.

### Claude Desktop and other MCP clients

1. In Claude Desktop open **Settings → Developer → Edit Config**. This opens `claude_desktop_config.json`
   (Windows: `%APPDATA%\Claude\`, macOS: `~/Library/Application Support/Claude/`).
2. Paste the following (if the file already has `mcpServers`, add only the `ai-browser` entry):

```json
{
  "mcpServers": {
    "ai-browser": { "command": "uvx", "args": ["--from", "git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python", "ai-browser"] }
  }
}
```

3. Quit Claude Desktop completely (including the system tray) and start it again.
4. In a new chat the `ai-browser` server should appear in the tools menu.

### Codex (OpenAI)

In a terminal:

```
codex mcp add ai-browser -- uvx --from git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python ai-browser
```

or add to `~/.codex/config.toml` (Windows: `%USERPROFILE%\.codex\config.toml`):

```toml
[mcp_servers.ai-browser]
command = "uvx"
args = ["--from", "git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python", "ai-browser"]
```

Check: `codex mcp list` should show `ai-browser` as `enabled`. Page-reading tools are marked read-only, so Codex
can run them without asking for approval; `click` and `type` (form submission) require approval.

By default Codex reaches for its built-in browser. To make it pick ai-browser on its own, add to
`~/.codex/AGENTS.md`:

```
For reading web pages and extracting data from them use the ai-browser MCP tools
(navigate, read, extract, tables, snapshot), not the built-in browser.
```

If Codex says it cannot see the ai-browser tools (some versions hide tools of external MCP servers), add to
`config.toml`:

```toml
[features]
tool_search_always_defer_mcp_tools = false
```

The first start takes a few seconds (uv downloads the package); later starts are instant.

## Is it safe? What this code does

- The command installs a **specific, pinned version** (`@v0.1.4`). The code never changes by itself – you update
  deliberately by changing the version number.
- The code is short and open: 5 files in [`python/src/ai_browser`](src/ai_browser) (about 600 lines). You can
  review it before installing.
- It **only connects to the pages the agent opens at your request**. No telemetry, no data sent anywhere else,
  no reading of files on your disk.
- It blocks internal network addresses (localhost, 192.168…, 10…, cloud metadata addresses), so a web page cannot
  use it to look into your company network.
- It does not bypass CAPTCHAs or site protection, identifies itself honestly and respects `robots.txt`.
- On a work computer, check your company's rules for installing tools – if in doubt, ask your IT department.

## Usage

Just ask the agent in plain language, e.g.:

- "Open https://books.toscrape.com and list the book titles and prices."
- "Read this article and summarize it in 5 bullet points: <url>."
- "Search <site> for X and give me the first 3 results."
- "Find large format printers in Glasgow and Edinburgh and make a table with email and phone." (`search` + `contacts`)
- "Go through 30 pages of https://books.toscrape.com and list all book titles." (`crawl` – many pages of one
  site, 1 page per second, respecting `robots.txt`; default limit 20, max 200)

The agent picks the tools itself: `navigate` opens a page, `read` reads the text, `extract` pulls data
with a selector, `type`/`click` fill in forms.

### Will Claude use it automatically?

Usually yes: the server tells the agent to prefer it for reading and scraping pages. The agent still decides on
its own and may sometimes pick its built-in web fetch. To make it always use ai-browser:

- say it in the request: "use ai-browser to …", or
- add one line to your `CLAUDE.md` (Claude Code) or project instructions (Claude Desktop):
  `For reading web pages always use the ai-browser tools.`

On first use Claude asks for permission to run the tools. To stop the prompts in Claude Code, choose
"always allow" or add `mcp__ai-browser` to the `allow` list in `~/.claude/settings.json`.

### Optional JavaScript mode (pages that need JS)

By default ai-browser does not run JavaScript, so pages built entirely in JS (single-page apps) look empty.
The optional JS mode fixes that: when a page turns out empty, ai-browser opens it in a headless Chromium,
waits for it to render and returns the same compact text. Normal pages keep using the light mode.

1. Install Chromium once (about 150 MB):

```
uvx --from "ai-browser[js] @ git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python" playwright install chromium
```

2. Connect the JS-enabled version (instead of the basic one):

```
claude mcp add --scope user ai-browser -- uvx --from "ai-browser[js] @ git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python" ai-browser
```

Claude Desktop: `"command": "uvx", "args": ["--from", "ai-browser[js] @ git+https://github.com/sebek53/ai-browser@v0.1.4#subdirectory=python", "ai-browser"]`.

The agent can also force it with `navigate(url, js=true)`. Disable with `AI_BROWSER_JS=0`.
Chromium uses the same honest User-Agent, `robots.txt`, rate limit and SSRF protection (every request it makes
is checked). Memory use grows to 150–300 MB only while Chromium is running.

## Update and uninstall

- Update: in the install command replace `@v0.1.4` with a newer version from the
  [releases list](https://github.com/sebek53/ai-browser/releases), then `claude mcp remove ai-browser -s user`
  and run `claude mcp add …` again.
- Uninstall: `claude mcp remove ai-browser -s user` or remove the entry from `claude_desktop_config.json`.

## Troubleshooting

- **`uvx` is not recognized** – after installing uv, restart the terminal / Claude Desktop.
- **Claude refuses to install it** – paste the command into your terminal yourself (see "Installation").
- **"robots.txt tej strony zabrania…"** (robots.txt disallows this page) – the site does not allow bots; look for its official API.
- **Empty content** – the page works only with JavaScript: enable the optional JS mode (see above).

## Settings (environment variables)

- `AI_BROWSER_CONTACT` – contact appended to the User-Agent (default: this repository's URL).
- `AI_BROWSER_ALLOW_PRIVATE=1` – allows private addresses (localhost, 192.168…); blocked by default.
- `AI_BROWSER_JS=0` – disables JS mode.
- `BRAVE_API_KEY` – optional [Brave Search API](https://brave.com/search/api/) key (free tier); `search` uses it instead of DuckDuckGo – more reliable for very many queries.

## Support the author

The project is free. If it saves you tokens, you can buy the author a beer 🍺

[ko-fi.com/sebastiangarstka](https://ko-fi.com/sebastiangarstka) · [buycoffee.to/sebastian.garstka](https://buycoffee.to/sebastian.garstka) (Poland, BLIK)
