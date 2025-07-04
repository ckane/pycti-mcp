# `pycti-mcp`: An MCP Server for OpenCTI

An [MCP](https://modelcontextprotocol.io/) server front-end for [`pycti`](https://github.com/OpenCTI-Platform/client-python).

Inspired by [Spathodea-Network/opencti-mcp](https://github.com/Spathodea-Network/opencti-mcp), but rather than trying to reflect
OpenCTI content back to the caller, the aim here is to condense, normalize, and consolidate data from OpenCTI into JSON for
the LLM to consume in order to acheive the following improvements:

- More verbosity in field naming so the LLM can better intuit what a field represents
- Resolve parts of GraphQL-linked entities into the response so more context is available in a single MCP response
- Reduce the inclusion of non-informative metadata to reduce context window usage

To use:

1. Set `$OPENCTI_URL` and `$OPENCTI_KEY` to your OpenCTI URL and API Key, respectively. Or, you can provide these on the command-line.
2. Run `uvx pycti-mcp@latest [ ... any CLI args ... ]`

Usage details:

```plaintext
usage: pycti-mcp [-h] [-p PORT] [-s] [-v] [-u URL] [-k KEY]

Execute the OpenCTI MCP Server

options:
  -h, --help       show this help message and exit
  -p, --port PORT  TCP port to listen on (default 8002 - only used if -s/--sse is provided)
  -s, --sse        Start an SSE server (default: off)
  -v, --verbose    Run in VERBOSE mode (INFO level logging). Default: off (WARN level logging)
  -u, --url URL    OpenCTI URL - Can also be provided in OPENCTI_URL environment variable
  -k, --key KEY    OpenCTI API Key - Can also be provided in OPENCTI_KEY environment variable
```

## Usage with [mcp-hub](https://github.com/ravitemer/mcp-hub)

The packaging of this MCP server has been designed to work well with the [mcp-hub](https://github.com/ravitemer/mcp-hub) project. For more
details about it, you can visit its project page. MCP-Hub is popular for providing multi-MCP-server management to various
tools, such as NeoVim. To add this project to MCP-Hub, simply extend your `mcpServers` section in `~/.config/mcphub/servers.json`
with the following configuration, adjusting as necessary for your particular server/environment:

```json
{
  "mcpServers": {
    "OpenCTI": {
      "command": "uvx",
      "args": [
        "pycti-mcp@latest",
        "--url",
        "https://my.opencti.server",
        "--key",
        "${cmd: kwallet-query -r my-opencti-apikey -l kdewallet}"
      ]
    }
  }
}
```

Note that, in the above example, `mcp-hub` supports various types of variable/shell expansion in the JSON configuration file. In
the above example, [KWalletManager](https://apps.kde.org/kwalletmanager5/) (or similar) would have been used to manually populate
a password named `my-opencti-apikey` in the `kdewallet` wallet. The above code would trigger any required system-side authentication
prompts for secret retrieval, and keep the secret out of the JSON file. If, however, storing the API Key in your JSON file is acceptable
or preferable, you can simply make the API key the value of that field in the JSON.

If preferred, the `--url` and `--key` arguments can be left off, and an `env` section can be added to the configuration to
populate the `OPENCTI_URL` and `OPENCTI_KEY` environment vars, instead. Read the `mcp-hub` documentation for more details.

## Usage with VSCode

Similar to above, [VSCode Supports MCP Servers](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) as well. You
can add `pycti-mcp` using a config similar to this:

```json
{
  // Inputs are prompted on first server start, then stored securely by VS Code.
  "inputs": [
    {
      "type": "promptString",
      "id": "opencti-key",
      "description": "OpenCTI API Key",
      "password": true
    }
  ],
  "servers": {
    "OpenCTI": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "pycti-mcp@latest",
        "-u",
        "https://my.opencti.server",
        "-k",
        "${input:opencti-key"
      ]
    }
  }
}
```

If preferred, the `--url` and `--key` arguments can be left off, and an `env` section can be added to the configuration to
populate the `OPENCTI_URL` and `OPENCTI_KEY` environment vars, instead. See the above VSCode documentation for more details.

# Adding New Tools

New tools may be added by creating a new Python module under [`src/pycti_mcp/pycti_tools/`](./src/pycti_mcp/pycti_tools/), then adding it
to the `__all__` list in [`./src/pycti_mcp/pycti_tools/__init__.py`](./src/pycti_mcp/pycti_tools/__init__.py) and to the
appropriate place in [`./tests/tools_list.txt`](./tests/tools_list.txt) so that the test suite can discover it during
code validation.

The only requirement is that your code
must implement exactly **one tool per module**, and the module must contain a `def tool_init(url, key)` function that takes the
OpenCTI url and API key as input (to save them internally for run-time use) and returns the function which is the entrypoint for the tool.
The entrypoint must implement the [Python Type Annotations](https://typing.python.org/en/latest/spec/annotations.html), which will be used
to provide an English-language description of how to call your tool, what it returns, and what its purpose is.

Example `generic_tool.py` below:

```python
from typing import Annotated
from pycti import OpenCTIApiClient

# Useful convention is to make a class implementation which holds the credentials provided to the tool
# from the call to tool_init(url, key)
class OpenCTIConfig:
    opencti_url = ""
    opencti_key = ""

def opencti_generic_tool(
    earliest: Annotated[str | None, "The earliest date of my search range"] = None,
    latest: Annotated[str | None, "The latest date of my search range"] = None,
    search: Annotated[str | None, "Search terms to filter on"] = None,
) -> Annotated[list | None, "Data structure listing the matching objects in the range"]:
    """Given a date range (start and end date) and some search terms, find all generic objects in the system
    matching the given criteria"""
    log = logging.getLogger(name=__name__)

    if not OpenCTIConfig.opencti_url:
        log.error("OpenCTI URL was not set. Tool will not work")
        return None

    # The credentials can be referenced by OpenCTIConfig.* as below
    octi = OpenCTIApiClient(
        url=OpenCTIConfig.opencti_url, token=OpenCTIConfig.opencti_key, ssl_verify=True
    )

    found_objs = []

    # TODO: Your implementation would go here, using the OpenCTI client to perform desired work
    ...

    ...

# Implement the tool_init that will be called by the MCP server to discover the available tool
def tool_init(url, key):
    # Note that it overwrites the default values in OpenCTIConfig.* with what was provided
    OpenCTIConfig.opencti_url = url
    OpenCTIConfig.opencti_key = key
    return opencti_reports_lookup
```

New tools need to be added to the following files in the project:

- [`./src/pycti_mcp/pycti_tools/__init__.py`](./src/pycti_mcp/pycti_tools/__init__.py) - Needs to be in the `__all__` list here to be auto-loaded
- [`./tests/tools_list.txt`](./tests/tools_list.txt) - Needs to be added to the list of tools, in alphabetical order, for the test suite to succeed

# Implemented Tools

<details>
<summary>OpenCTI Observable Lookup</summary>

**Name**: `opencti_observable_lookup`

**Inputs**: `observable` (`str`): An Observable

This tool will perform an exact-match lookup in OpenCTI for the observable value provided as `observable`.

Given an observable, queries for it in OpenCTI and, if it exists, returns JSON object representing
the findings from OpenCTI for the observable, with the following fields:

- `observable_value`: The observable value, as it is recorded in OpenCTI
- `stix_id`: The STIX Id of the observable object
- `opencti_id`: The entity Id of the observable object in OpenCTI
- `data_type`: The STIX Observable type
- `descriotion`: A short description of the observable, from OpenCTI
- `created`: Creation data within OpenCTI
- `last_updated`: The last time an update was written to the observable object in OpenCTI
- `labels`: A list of labels (as strings) attached to the observable
- `external_reports`: A list of external reports containing the observable
  - `name`: The title of the report
  - `urls`: List of URLs to fetch the report (or parts of it)
- `notes`: Notes in OpenCTI written about the observable
- `opinions`: Opinions in OpenCTI about the observable
  - `sentiment`: The sentiment expressed in the opinion.
  - `explanation`: An explanation of the opinion.

</details>

<details>
<summary>OpenCTI Adversary Lookup</summary>

**Name**: `opencti_adversary_lookup`

**Inputs**: `name` (`str`): A name or alias of an adversary, intrusion set, threat actor, threat group, or campaign

This tool will search across all "adversary" type entities: Intrusion Sets, Actors, and Campaigns for the adversary
matching `name` either in its formal name or one of its aliases.

- `stix_id`: The STIX ID of the adversary object.
- `opencti_id`: The entity ID of the adversary object in OpenCTI.
- `name`: The name of the adversary.
- `data_type`: The type of the entity (e.g., "Threat Actor").
- `description`: A brief description of the adversary.
- `created`: The creation date of the adversary in OpenCTI.
- `last_updated`: The last time the adversary was updated in OpenCTI.
- `labels`: A list of labels (as strings) attached to the adversary.
- `first_seen`: The first date the adversary was observed.
- `last_seen`: The last date the adversary was observed.
- `external_reports`: A list of external reports related to the adversary, each containing:
  - `name`: The title of the report.
  - `urls`: List of URLs to access the report or its parts.
- `notes`: A collection of notes associated with the adversary.
- `opinions`: A list of opinions about the adversary, where each opinion includes:
  - `sentiment`: The sentiment expressed in the opinion.
  - `explanation`: An explanation of the opinion.
  </details>

<details>
<summary>OpenCTI Report Lookup</summary>

**Name**: `opencti_report_lookup`

**Inputs**:

- `search` (`str`): An optional search term to use to filter to reports matching a string term
- `earliest` (`str`): Optional timestamp that sets the _earliest_ date to search for reports
- `latest` (`str`): Optional timestamp that sets the _latest_ date to search for reports

This tool will perform a lookup in OpenCTI of all of the threat reports matching a search term provided as `search`,
between the creation timestamps `earliest` and `latest`. Any of the inputs can be omitted (specified as None).

- `stix_id`: The STIX ID of the report.
- `opencti_id`: The entity ID of the report in OpenCTI.
- `name`: The name of the report.
- `data_type`: The type of the entity (e.g., "Report").
- `description`: A brief description of the contents of the report.
- `created`: The creation date of the report.
- `modified`: The most recent modification date of the report.
- `published`: The report's publication date.
- `labels`: A list of labels (as strings) attached to the report.
- `external_urls`: A list of external URLs referencing sourcing of the report.
- `report_types`: The type label(s) of the analysis report.
- `objects`: The STIX objects (Entities and Cyber observables) contained within the report.

</details>
