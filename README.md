An [MCP](https://modelcontextprotocol.io/) server front-end for [`pycti`](https://github.com/OpenCTI-Platform/client-python).

Inspired by [Spathodea-Network/opencti-mcp](https://github.com/Spathodea-Network/opencti-mcp), but rather than trying to reflect
OpenCTI content back to the caller, the aim here is to condense, normalize, and consolidate data from OpenCTI into JSON for
the LLM to consume in order to acheive the following improvements:
* More verbosity in field naming so the LLM can better intuit what a field represents
* Resolve parts of GraphQL-linked entities into the response so more context is available in a single MCP response
* Reduce the inclusion of non-informative metadata to reduce context window usage

To use:

1. Copy `pycti_tools/local_settings.py.sample` to `pycti_tools/local_settings.py`, and edit the new file to your needs
2. Run `uv run mcp_server_octi.py`

# Implemented Functions

## OpenCTI Observable Lookup

**Name**: `opencti_observable_lookup`

**Inputs**: `observable` (`str`): An Observable

This tool will perform an exact-match lookup in OpenCTI for the observable value provided as `observable`.

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
  - `sentiment`: The sentiment expressed in the opinion.
  - `explanation`: An explanation of the opinion.

## OpenCTI Adversary Lookup

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

## OpenCTI Report Lookup

**Name**: `opencti_report_lookup`

**Inputs**:
 * `search` (`str`): An optional search term to use to filter to reports matching a string term
 * `earliest` (`str`): Optional timestamp that sets the *earliest* date to search for reports
 * `latest` (`str`): Optional timestamp that sets the *latest* date to search for reports

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
