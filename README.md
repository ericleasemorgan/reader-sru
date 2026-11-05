# reader-sru

This is an [MCP](https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro) (Model Context Protocol) server used to search the [Distant Reader catalog](http://catalog.distantreader.org) via the [SRU (Search/Retrieve via URL)](https://www.loc.gov/standards/sru/) protocol.

With this server and your favorite agent software (ollmcp, Claude, ChatGPT, etc.) you can use natural langauge commands to query the Reader's catalog of 1.4 million items, and have the results interpreted by the agent. Once you identify items of interest, you can then save a CSV (comma-separated values) file which includes rudimentary bibliographics and URLs pointing to where the items can be downloaded. The CSV file is useful because you will probably want to curate the file (normalize names, remove duplicates, add dates, etc.) before actually downloading items.

There is also a [Web-based interface to the SRU interface](http://index.distantreader.org), but in the long run, this MCP server is more functional.


## Install

Download the distribution, change directories to the distribution's root, and install the requirements:

```bash
pip install -r requirements.txt
```

You then ought to be able to run the server:

```bash
python server.py
```

If zero errors are output, then it is probably working. Ironicaly, if zero errors are output, then nothing else will be output either because the server is waiting for MCP commands. Just press ^C and assume all is well.


## Using the server

To use the server you need to integrate it with your agent software. I use [ollmcp](https://github.com/jonigl/mcp-client-for-ollama) as my agent, and I can use the server by running the following command:

```bash
ollmcp -s /path/to/reader-sru/server.py
```

Many people use Claude as their agent. If you do too, then open your Claude desktop config file (claude_desktop_config.json), and add an MCP server record. For example:

```json
{
  "mcpServers": {
    "reader-sru": {
      "command": "python",
      "args": ["/path/to/reader-sru/server.py"]
    }
  }
}
```

(There has got to be an easier way!)


## Example Commands

After you have integrated the server into your agent you ought to be able to submit commands. Here are six:

1. Throughly explain the Reader Index, and use the word "astrology" as an example. - This will load bunches o' configurations, query the remote server for functionality, and search for records on the topic of astrology.

2. Find items about Lancaster. Get a single record. Evaluate the facets. - This will do just what the command states. Pay attention to the facet evaluation beause it will give you hints on how to improve your searches. Very useful.

3. Get the first twelve items from the search results. - This will retrieve the bibliographics of the first twelve items and do some analysis against them. It would be nice if traditional library catalogs would do the same.

4. Get the first twelve items from the search results, and save them as a CSV file. - Again, this will do exactly what the command states, and the resulting CSV file will be a rudimentary bibliography, plus URLs, that you can use for any number of things.

5. From the twelve records, create a rudimentary bibliography in the Chicago style. - This command ought to output a more formal bibliography.

6. Get the full text of item #12 and summarize it. - This will download item #12, feed it to the LLM, and you ought to get back some sort of analysis. 


