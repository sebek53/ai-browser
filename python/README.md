# ai-browser

**English** | [Polski](https://github.com/sebek53/ai-browser/blob/main/python/README.pl.md)

A lightweight browser for AI agents (MCP server). Instead of screenshots or raw HTML
it returns compact text: about 7x fewer tokens when reading and about 180x fewer when extracting data
with a CSS selector.

Tools: `navigate`, `read`, `tables`, `snapshot`, `extract`, `click`, `type`, `select`, `back`.

## Installation

Requires [uv](https://docs.astral.sh/uv/). Windows:

```
winget install astral-sh.uv
```

macOS / Linux:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Claude Code

```
claude mcp add --scope user ai-browser -- uvx --from git+https://github.com/sebek53/ai-browser#subdirectory=python ai-browser
```

Check: `claude mcp get ai-browser` should show `Connected`.

### Claude Desktop and other MCP clients

1. In Claude Desktop open **Settings → Developer → Edit Config**. This opens `claude_desktop_config.json`
   (Windows: `%APPDATA%\Claude\`, macOS: `~/Library/Application Support/Claude/`).
2. Paste the following (if the file already has `mcpServers`, add only the `ai-browser` entry):

```json
{
  "mcpServers": {
    "ai-browser": { "command": "uvx", "args": ["--from", "git+https://github.com/sebek53/ai-browser#subdirectory=python", "ai-browser"] }
  }
}
```

3. Quit Claude Desktop completely (including the system tray) and start it again.
4. In a new chat the `ai-browser` server should appear in the tools menu.

The first start takes a few seconds (uv downloads the package); later starts are instant.

## Usage

Just ask the agent in plain language, e.g.:

- "Open https://books.toscrape.com and list the book titles and prices."
- "Read this article and summarize it in 5 bullet points: <url>."
- "Search <site> for X and give me the first 3 results."

The agent picks the tools itself: `navigate` opens a page, `read` reads the text, `extract` pulls data
with a selector, `type`/`click` fill in forms.

### Optional JavaScript mode (pages that need JS)

By default ai-browser does not run JavaScript, so pages built entirely in JS (single-page apps) look empty.
The optional JS mode fixes that: when a page turns out empty, ai-browser opens it in a headless Chromium,
waits for it to render and returns the same compact text. Normal pages keep using the light mode.

1. Install Chromium once (about 150 MB):

```
uvx --from "ai-browser[js] @ git+https://github.com/sebek53/ai-browser#subdirectory=python" playwright install chromium
```

2. Use `uvx --from "ai-browser[js] @ git+https://github.com/sebek53/ai-browser#subdirectory=python" ai-browser` instead of the basic command:

```
claude mcp add --scope user ai-browser -- uvx --from "ai-browser[js] @ git+https://github.com/sebek53/ai-browser#subdirectory=python" ai-browser
```

Claude Desktop: `"command": "uvx", "args": ["--from", "ai-browser[js] @ git+https://github.com/sebek53/ai-browser#subdirectory=python", "ai-browser"]`.

The agent can also force it with `navigate(url, js=true)`. Disable with `AI_BROWSER_JS=0`.
Chromium uses the same honest User-Agent, `robots.txt`, rate limit and SSRF protection (every request it makes
is checked). Memory use grows to 150–300 MB only while Chromium is running.

### Will Claude use it automatically?

Usually yes: the server tells the agent (MCP server instructions) to prefer it for reading and scraping pages.
The agent still decides on its own and may sometimes pick its built-in web fetch or browser instead. To make
it always use ai-browser:

- say it in the request: "use ai-browser to …", or
- add one line to your `CLAUDE.md` (Claude Code) or project instructions (Claude Desktop):
  `For reading web pages always use the ai-browser tools.`

On first use Claude asks for permission to run the tools. To stop the prompts in Claude Code, choose
"always allow" or add `mcp__ai-browser` to the `allow` list in `~/.claude/settings.json`.

## Update and uninstall

- Update: `uv cache clean ai-browser`, then restart Claude (the newest version from GitHub is downloaded).
- Uninstall: `claude mcp remove ai-browser -s user` or remove the entry from `claude_desktop_config.json`.

## Settings (environment variables)

- `AI_BROWSER_CONTACT` – contact appended to the User-Agent (e.g. `mailto:me@example.com`).
- `AI_BROWSER_ALLOW_PRIVATE=1` – allows private addresses (localhost, 192.168…); blocked by default.

## Rules

The program identifies itself honestly (User-Agent `ai-browser/<version>`), respects `robots.txt`, sends at most
one request per second to a single host and does not bypass CAPTCHAs or anti-bot protection.
Every response is marked as untrusted page content.

## Troubleshooting

- **`uvx` is not recognized** – after installing uv, restart the terminal / Claude Desktop.
- **"robots.txt tej strony zabrania…"** (robots.txt disallows this page) – the site does not allow bots; look for its official API.
- **Empty content** – the page works only with JavaScript: enable the optional JS mode (see above).

## Support the author

The project is free. If it saves you tokens, you can buy the author a beer 🍺

[ko-fi.com/sebastiangarstka](https://ko-fi.com/sebastiangarstka) · [buycoffee.to/sebastian.garstka](https://buycoffee.to/sebastian.garstka) (Poland, BLIK)
