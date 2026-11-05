# reader-sru

This is an MCP (Model Context Protocol) server used to search the Distant Reader catalog via the [SRU (Search/Retrieve via URL)](https://www.loc.gov/standards/sru/) protocol. With this server and your favorite agent software (ollmcp, Claude, ChatGPT, etc.) you can use natural langauge commands to query the Reader's catalog, and have the results interpreted by the agent. Once you identify items of interest, you can then save a CSV (comma-separated values) file which includes rudimentary bibliographics and URLs pointing to where the items can be downloaded. The CSV file is useful because you will probably want to curate the file (normalizing names, removing duplicates, adding dates, etc.) before actually downloading items.

There is a Web-based interface to the Reader's catalog ([http://index.distantreader.org](http://index.distantreader.org)), but in the long run, this MCP server is more functional than the Web-based interface.

## Features

- **5 tools** for LLM-driven bibliographic search
- **7 pre-configured servers** including Library of Congress, BnF, DNB, and more
- Parses **MARCXML** and **Dublin Core** record formats
- Supports any SRU-compliant server — pass a URL or use a built-in server ID
- Raw CQL queries or high-level field-based search (title, author, ISBN, subject, etc.)

## Quick Start

### Install

```bash
pip install mcp[cli] httpx xmltodict
```

### Run

```bash
python server.py
```

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sru": {
      "command": "python",
      "args": ["/path/to/sru-mcp/server.py"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `sru_list_servers` | List all pre-configured library catalog servers |
| `sru_explain` | Get a server's capabilities, supported schemas, and indexes |
| `sru_list_indexes` | List available search indexes on a server |
| `sru_search` | Execute a raw CQL query |
| `sru_search_books` | Search by title, author, ISBN, subject, publisher, year, or keyword |

### Example Usage

Search the Library of Congress for books by Melville:

```
sru_search_books(server="loc", author="Melville", title="Moby Dick")
```

Search the French national library with a raw CQL query:

```
sru_search(server="bnf", cql_query='dc.title = "Les Misérables"')
```

## Pre-configured Servers

| ID | Name | Notes |
|----|------|-------|
| `loc` | Library of Congress | US national catalog |
| `loc-names` | LC Name Authority | Personal and corporate names |
| `loc-subjects` | LC Subject Authority | Subject headings and genre terms |
| `bnf` | Bibliothèque nationale de France | French national library |
| `dnb` | Deutsche Nationalbibliothek | German national library |
| `kb` | Koninklijke Bibliotheek | Netherlands national library |
| `bibsys` | BIBSYS | Norwegian academic libraries |

To add a server, edit `servers.json`.

## Development

```bash
# Install dev dependencies
pip install pytest pytest-asyncio respx

# Run tests
python3 -m pytest test_sru.py test_server.py -v

# Test with MCP Inspector
npx @modelcontextprotocol/inspector python server.py
```

## Project Structure

```
server.py       FastMCP server — tool definitions
sru.py          SRU protocol client — HTTP, parsing, formatting
servers.json    Server registry
test_sru.py     Tests for sru.py (92 tests total)
test_server.py  Tests for server.py
```

## License

MIT
