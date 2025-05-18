An [MCP](https://modelcontextprotocol.io/) server front-end for [`pycti`](https://github.com/OpenCTI-Platform/client-python).

To use:

1. Copy `local_settings.py.sample` to `local_settings.py`, and edit the new file to your needs
2. Run `uv run mcp run -t sse mcp_server_octi.py`

# Implemented Functions

## OpenCTI Observable Lookup

**Name**: `opencti_observable_lookup`
**Inputs**: `observable` (`str`): An Observable

Given an observable, queries for it in OpenCTI and, if it exists, returns JSON object representing
the findings from OpenCTI for the observable, with the following fields:
* `observable_value`: The observable value, as it is recorded in OpenCTI
* `stix_id`: The STIX Id of the observable object
* `opencti_id`: The entity Id of the observable object in OpenCTI
* `data_type`: The STIX Observable type
* `descriotion`: A short description of the observable, from OpenCTI
* `created`: Creation data within OpenCTI
* `last_updated`: The last time an update was written to the observable object in OpenCTI
* `labels`: A list of labels (as strings) attached to the observable
* `external_reports`: A list of external reports containing the observable
  * `name`: The title of the report
  * `urls`: List of URLs to fetch the report (or parts of it)
* `notes`: Notes in OpenCTI written about the observable
* `opinions`: Opinions in OpenCTI about the observable
