#!/usr/bin/env python

# server.py - an MCP server used to query the Distant Reader Catalog via SRU
# forked from https://github.com/codefzer/sru-mcp; Thanks Sam Codefzer!

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# July  9, 2026 - first documentation but been hacking on it for couple of weeks
# July 14, 2026 - added facets (cool!), save html or json, and cache file; at the cabin


# require
from json               import dump, load
from mcp.server.fastmcp import FastMCP
from pandas             import DataFrame
from pathlib            import Path
from pydantic           import Field, BaseModel
from requests           import get
from typing             import Annotated
import sru


#class Item( BaseModel ) :
#	author : str
#	title : str
#	date : str
#	url : str


# Build a compact server list string for tool descriptions
_SERVER_HINT      = ", ".join( f"{s['id']} ({s['name']})" for s in sru.SERVERS )
_SERVER_URL_FIELD = Field( description=( "URL or ID of the SRU server. " f"Known IDs: {', '.join(sru.KNOWN_SERVERS)}. " "Use sru_list_servers to see full details, or pass any SRU server URL." ) )
mcp = FastMCP( "sru_mcp", instructions=(  "Search library catalogs using the SRU (Search/Retrieve via URL) protocol. " "Use sru_list_servers to discover available servers, sru_explain to inspect " "a server's capabilities, sru_search_books for simple field-based searches, " f"or sru_search for raw CQL queries. Available servers: {_SERVER_HINT}." ), )
HTML    = 'sru-results.html'
#JSON    = 'sru-results.json'
CACHE   = 'cache'
METADATA = 'metadata.csv'
COLUMNS  = [ 'author', 'title', 'date', 'url', 'file' ]

def _resolve_url(id_or_url: str) -> str :
    """Resolve a server ID to its URL, or return the input unchanged if it's already a URL."""
    server = sru.get_server(id_or_url)    
    return server["url"] if server else id_or_url

def main() -> None : mcp.run( transport="stdio" )


############## save to file ##############

@mcp.tool()
def save_HTML( content: str ) -> str:
    '''Save the given HTML to a file'''
    
    # try to do the work
    html = Path.cwd()/HTML
    try:
        with open( html, "w", encoding="utf-8") as handle : handle.write( content )
        return f"Successfully wrote {len(content)} characters to file://{html}"
    
    # alas
    except Exception as error : return f"Error: {error}"


#@mcp.tool()
#def save_JSON( content: str ) -> str:
#    '''Save the given JSON to a file'''
#    
#    # try to do the work
#    try:
#        with open( JSON, "w", encoding="utf-8") as handle : dump( content, handle )
#        return f"Successfully wrote {len(content)} characters to file://{JSON}"
#    
#    # alas
#    except Exception as error : return f"Error: {error}"


# get url
@mcp.tool()
def get_URL( url:str ) -> dict:
	'''Given a URL pointing to an item in the Distant Reader stacks, get a cautionary note and the plain text of an item from the Distant Reader stacks. Pay attention to any cautionary notes returned by this operation. Be forewarned. Having an LLM evaluate a set of plain text without a great deal of context ma produce dubious results.'''

	return( { 'caution': 'Requesting an LLM to evaluate a plain text document sans any context often results in dubious results. Be forwared.', "text": get( url ).text } )


# list servers
@mcp.tool(annotations={"readOnlyHint": True})
def list_servers() -> dict:
    '''Return a list of all the SRU servers available from this system. There ought to be only one, the Distant Reader Index at http://catalog.distantreader.org:2100/biblios'''
    
    return ( sru.SERVERS )


# explain
@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
async def explain( server: Annotated[ str, _SERVER_URL_FIELD ] ) -> dict :
    '''Given the name of a server, request the server's explain operation and return the explain response. This is useful for understanding the basic functionality of the server.'''

    try :
    
        explanation = await sru.explain( _resolve_url( server ) )
        return ( sru.parse_explain( explanation ) )
 
    except sru.SRUError as exc : return f"**Error:** {exc}"


# list indexes
@mcp.tool( annotations={ "readOnlyHint": True, "openWorldHint": True } )
async def list_indexes( server: Annotated[ str, _SERVER_URL_FIELD ] ) -> dict:
    '''Given the name of a server, extract the indexes the server supports in order to how CQL queries can be applied to it.'''

    try :
    
        explanation = await sru.explain(_resolve_url( server ) )
        return( sru.parse_explain( explanation )[ 'indexes' ] )

    except sru.SRUError as exc : return f"**Error:** {exc}"


# search via CQL
@mcp.tool(annotations={ "readOnlyHint": True, "openWorldHint": True } )
async def search_CQL(
    server: Annotated[str, _SERVER_URL_FIELD ],
    cql_query: Annotated[
        str,
        Field(
            description=(
                "CQL (Contextual Query Language) query string. "
                'Examples: \'dc.title = "Moby Dick"\', '
                '\'dc.creator = "Melville" AND dc.date = "1851"\', '
                '\'bath.isbn = "9780142437247"\'. '
                "Use sru_list_indexes to discover available index names."
            )
        ),
    ],
    max_records: Annotated[
        int,
        Field(description="Maximum number of records to return (1–128)", ge=1, le=128),
    ] = 128,
    start_record: Annotated[
        int,
        Field(description="1-based index of the first record to return (for pagination)", ge=1),
    ] = 1,
    record_schema: Annotated[
        str | None,
        Field(description="Record schema to request (e.g., 'dc', 'marcxml', 'mods'). "
                          "Defaults to 'marcxml'. Use sru_explain to see supported schemas."),
    ] = "marcxml",
) -> dict:
    """Execute a raw CQL query against an SRU server and return matching records.

    Returns a markdown summary of results including title, author, publisher,
    year, ISBN, subjects, and language for each record.

    For pagination, increment start_record by max_records on each call.
    The response includes the total number of matching records.
    """
    try:
        results = await sru.search_retrieve( _resolve_url( server ), cql_query, max_records, start_record, record_schema )
        return ( sru.parse_search_results( results ) )

    except sru.SRUError as exc: return f"**Error:** {exc}"


# search via CQL
#@mcp.tool(annotations={ "readOnlyHint": True, "openWorldHint": True } )
#async def search_CQL_to_JSON(
#    server: Annotated[str, _SERVER_URL_FIELD ],
#    cql_query: Annotated[
#        str,
#        Field(
#            description=(
#                "CQL (Contextual Query Language) query string. "
#                'Examples: \'dc.title = "Moby Dick"\', '
#                '\'dc.creator = "Melville" AND dc.date = "1851"\', '
#                '\'bath.isbn = "9780142437247"\'. '
#                "Use sru_list_indexes to discover available index names."
#            )
#        ),
#    ],
#    max_records: Annotated[
#        int,
#        Field(description="Maximum number of records to return (1–128)", ge=1, le=128),
#    ] = 128,
#    start_record: Annotated[
#        int,
#        Field(description="1-based index of the first record to return (for pagination)", ge=1),
#    ] = 1,
#    record_schema: Annotated[
#        str | None,
#        Field(description="Record schema to request (e.g., 'dc', 'marcxml', 'mods'). "
#                          "Defaults to 'marcxml'. Use sru_explain to see supported schemas."),
#    ] = "marcxml",
#) -> str :
#    """Execute a raw CQL query against an SRU server and return matching records.
#
#    Returns a markdown summary of results including title, author, publisher,
#    year, ISBN, subjects, and language for each record.
#
#    For pagination, increment start_record by max_records on each call.
#    The response includes the total number of matching records.
#    """
#    try:
#        results = await sru.search_retrieve( _resolve_url( server ), cql_query, max_records, start_record, record_schema )
#        records =  sru.parse_search_results( results )[ 'records' ]
#        results = []
#        for record in records :
#          author = ''
#          url = ''
#          if (authors := record.get( "author", [] ) ) : author = authors[0]
#          title = record.get( 'title', '')
#          date = record.get( 'year', '')
#          if (urls := record.get( "urls", [] ) ) : url = urls[1]
#          #results.append( Item(author=author,title=title, date=date, url=url) )
#          results.append( { 'author':author,'title':title, 'date':date, 'url':url } )
#        with open( JSON, "w", encoding="utf-8") as handle : dump( results, handle )
#        return f"Successfully wrote {len(results)} characters to file://{JSON}"
#    except sru.SRUError as exc: return f"**Error:** {exc}"


# search via CQL
@mcp.tool(annotations={ "readOnlyHint": True, "openWorldHint": True } )
async def search_CQL_to_CACHE(
    server: Annotated[str, _SERVER_URL_FIELD ],
    cql_query: Annotated[
        str,
        Field(
            description=(
                "CQL (Contextual Query Language) query string. "
                'Examples: \'dc.title = "Moby Dick"\', '
                '\'dc.creator = "Melville" AND dc.date = "1851"\', '
                '\'bath.isbn = "9780142437247"\'. '
                "Use sru_list_indexes to discover available index names."
            )
        ),
    ],
    max_records: Annotated[
        int,
        Field(description="Maximum number of records to return (1–128)", ge=1, le=128),
    ] = 128,
    start_record: Annotated[
        int,
        Field(description="1-based index of the first record to return (for pagination)", ge=1),
    ] = 1,
    record_schema: Annotated[
        str | None,
        Field(description="Record schema to request (e.g., 'dc', 'marcxml', 'mods'). "
                          "Defaults to 'marcxml'. Use sru_explain to see supported schemas."),
    ] = "marcxml",
) -> str :
    """Execute a raw CQL query against an SRU server and return matching records.

    Returns a markdown summary of results including title, author, publisher,
    year, ISBN, subjects, and language for each record.

    For pagination, increment start_record by max_records on each call.
    The response includes the total number of matching records.
    """
    try:
        results = await sru.search_retrieve( _resolve_url( server ), cql_query, max_records, start_record, record_schema )
        records =  sru.parse_search_results( results )[ 'records' ]
        results = []
        for record in records :
          author = ''
          url = ''
          if (authors := record.get( "author", [] ) ) : author = authors[0]
          title = record.get( 'title', '')
          date = record.get( 'year', '')
          if (urls := record.get( "urls", [] ) ) : url = urls[1]
          #results.append( Item(author=author,title=title, date=date, url=url) )
          results.append( { 'author':author,'title':title, 'date':date, 'url':url } )

        # initialize
        cache = Path.cwd()/CACHE
        cache.mkdir( exist_ok=True )

        metadata = []
        for record in results :

          # parse
          author = record[ 'author' ]
          title  = record[ 'title' ]
          date   = record[ 'date' ]
          url    = record[ 'url' ]
          file   = url.split( '/' )[ -1 ]

          # get the given item; could use error-checking
          response = get( url )
          with open( cache/file, 'wb' ) as handle : handle.write( response.content )

          # update
          metadata.append( [ author, title, date, url, file ] )

        # create a dataframe, output, and done
        metadata = DataFrame( metadata, columns=COLUMNS )
        with open( cache/METADATA, 'w' ) as handle : handle.write( metadata.to_csv( index=False ) )
        return f"Successfully cache {len(records)} to file://{cache}"
    except sru.SRUError as exc: return f"**Error:** {exc}"


# ---------------------------------------------------------------------------
# Tool: sru_search_books
# ---------------------------------------------------------------------------

@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
async def search_keywords(
    server: Annotated[str, _SERVER_URL_FIELD],
    title: Annotated[str | None, Field(description="Book title or partial title")] = None,
    author: Annotated[str | None, Field(description="Author name")] = None,
    isbn: Annotated[str | None, Field(description="ISBN (10 or 13 digits)")] = None,
    subject: Annotated[str | None, Field(description="Subject or topic keyword")] = None,
    publisher: Annotated[str | None, Field(description="Publisher name")] = None,
    year: Annotated[str | None, Field(description="Publication year (e.g., '2001')")] = None,
    keyword: Annotated[str | None, Field(description="General keyword search across all fields")] = None,
    max_records: Annotated[
        int,
        Field(description="Maximum number of records to return (1–100)", ge=1, le=100),
    ] = 10,
    start_record: Annotated[
        int,
        Field(description="1-based index of the first record to return (for pagination)", ge=1),
    ] = 1,
    record_schema: Annotated[
        str | None,
        Field(description="Record schema to request (e.g., 'dc', 'marcxml'). "
                          "Defaults to 'marcxml'."),
    ] = "marcxml",
) -> dict:
    """Search an SRU library catalog by common bibliographic fields.

    Provide any combination of title, author, isbn, subject, publisher, year,
    or keyword. Multiple fields are AND-combined. At least one field is required.

    Returns a markdown summary of matching records.

    Example using the Library of Congress:
      server = "loc"
      title = "Moby Dick"
      author = "Melville"
    """
    try:
        cql = sru.build_cql(
            title=title,
            author=author,
            isbn=isbn,
            subject=subject,
            publisher=publisher,
            year=year,
            keyword=keyword,
        )
    except ValueError as exc:
        return f"**Error:** {exc}"

    try:
        root = await sru.search_retrieve(
            _resolve_url(server), cql, max_records, start_record, record_schema,
        )
        results = sru.parse_search_results(root)
        #md = sru.format_search_results_markdown(results)
        return results
    except sru.SRUError as exc:
       return f"**Error:** {exc}"


# scan an index, but the Reader does not support the scan operation
#@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
#async def sru_scan(
#    server: Annotated[str, _SERVER_URL_FIELD],
#    scan_clause: Annotated[str, Field(description="CQL index and term to scan, e.g. 'dc.title = moby'")],
#    max_terms: Annotated[
#        int,
#        Field(description="Maximum number of index terms to return (1–100)", ge=1, le=100),
#    ] = 20,
#    response_position: Annotated[
#        int,
#        Field(description="Position of the scan clause term within the returned list (1-based)", ge=1),
#    ] = 1,
#) -> str:
#    """Browse index terms near a given term on an SRU server (scan operation).
#
#    Returns a list of index terms and their record counts, which is useful
#    for exploring available values before running a full search.
#
#    Example: scan dc.title = "moby" to see title terms alphabetically near "moby".
#    """
#    try:
#        root = await sru.scan(_resolve_url(server), scan_clause, max_terms, response_position )
#        terms = sru.parse_scan_results(root)
#        if not terms:
#            return "No terms found."
#        lines = ["| Term | Count |", "|------|-------|"]
#        for t in terms:
#            count = t.get("count", "")
#            lines.append(f"| {t['term']} | {count} |")
#        return "\n".join(lines)
#    except sru.SRUError as exc:
#        return f"**Error:** {exc}"


# on our mark, get set, go!
if __name__ == "__main__" : main()
