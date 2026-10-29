"""Test zgodności: oficjalny klient MCP (pakiet `mcp`) łączy się z ai-browser po stdio.

Uruchomienie: uv run --with mcp python tests/klient_mcp.py
Ten sam protokół używają Claude Code, Claude Desktop, Codex i inni klienci MCP.
"""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERWER = StdioServerParameters(command=sys.executable, args=["-m", "ai_browser.server"])


async def main() -> None:
    async with stdio_client(SERWER) as (odczyt, zapis), ClientSession(odczyt, zapis) as sesja:
        init = await sesja.initialize()
        print("initialize:", init.server_info.name, init.server_info.version, "| instrukcje:", bool(init.instructions))

        narzedzia = [t.name for t in (await sesja.list_tools()).tools]
        print("tools/list:", ", ".join(narzedzia))
        assert len(narzedzia) == 9

        wynik = await sesja.call_tool("navigate", {"url": "https://books.toscrape.com/"})
        assert not wynik.is_error and "Books to Scrape" in wynik.content[0].text
        wynik = await sesja.call_tool("extract", {"selector": "article.product_pod h3 a", "attr": "title"})
        tytuly = wynik.content[0].text.splitlines()[1:]
        print(f"extract: {len(tytuly)} tytułów, np. {tytuly[0]!r}")
        assert len(tytuly) == 20

        wynik = await sesja.call_tool("navigate", {"url": "http://localhost/"})
        assert wynik.is_error
        print("błąd narzędzia (SSRF) zwrócony jako isError: OK")
    print("WYNIK: zgodny z MCP")


if __name__ == "__main__":
    asyncio.run(main())
