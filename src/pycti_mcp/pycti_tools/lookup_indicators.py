import json
from typing import Annotated, List, Literal
from pycti import OpenCTIApiClient
from fastmcp import Context


class OpenCTIConfig:
    opencti_url = ""
    opencti_key = ""


def parse_indicator(i):
    parsed_i = {
        "signature": i["pattern"],
        "stix_id": i["standard_id"],
        "opencti_id": i["id"],
        "signature_type": i["pattern_type"],
        "description": i["description"],
        "created": i["created_at"],
        "last_updated": i["updated_at"],
        "labels": [label["value"] for label in i["objectLabel"]],
        "external_reports": [
            {"name": "Self", "urls": [e["url"] for e in i["externalReferences"]]}
        ],
        "confidence": i["confidence"],
        "score": i["x_opencti_score"],
        "revoked": i["revoked"],
        "deploy": i["x_opencti_detection"],
        "mitre_platforms": i["x_mitre_platforms"],
        "observables": [
            {"value": x["value"], "type": x["type"]}
            for x in i["x_opencti_observable_values"]
        ],
        # TODO: Walk through the list of "killChainPhases" and extract the MITRE TTPs
    }
    return parsed_i


ind_projection = """
    id
    standard_id
    pattern
    pattern_type
    pattern_version
    entity_type
    confidence
    revoked
    name
    x_opencti_main_observable_type
    x_opencti_observable_values {
      type
      value
    }
    description
    x_opencti_detection
    x_opencti_score
    x_mitre_platforms
    created_at
    updated_at
    externalReferences {
      edges {
        node {
          url
        }
      }
    }
    objectLabel {
      id
      value
    }
    killChainPhases {
      id
      standard_id
      entity_type
      kill_chain_name
      phase_name
    }
"""


async def opencti_indicator_lookup(
    pattern_search_strings: Annotated[
        List[str], "Strings to search for in indicator patterns in OpenCTI"
    ],
    ctx: Context,
    pattern_types: Annotated[
        List[
            str
            | Literal[
                "eql",
                "kql",
                "linq",
                "pcre",
                "shodan",
                "sigma",
                "snort",
                "spl",
                "stix",
                "suricata",
                "tanium-signal",
                "yara",
            ],
        ],
        "One or more strings in a list specifying the pattern types in OpenCTI we want to limit search to",
    ] = [],
    indicator_id: Annotated[
        str | None,
        "Id of the indicator to look up. If specified, pattern_types and pattern_search_strings will be ignored. Can be a STIX or OpenCTI Id value.",
    ] = None,
) -> Annotated[list[dict], "Data structure representing the observable"] | None:
    """This tool can be used to search for one or more indicators (also called a signature or IOC) given a list of strings,
    which will be used to perform a search within the indicator's pattern field (also known as the signature content or body).
    It will search for any indicators in OpenCTI that contain all of the strings in pattern_search_strings, where the pattern
    type (also called "signature type" or "indicator type" or "IOC type") are exactly any of the values specified in
    pattern_types. If pattern_types is empty list ([]), then this tool will interpret that as an instruction to search across
    all pattern types, even patterns that aren't specifically defined in the pattern_types definition.

    If indicator_id is not None, then it must contain either a STIX Id or an OpenCTI Id to fetch an indicator, IOC,
    signature, by Id rather than by searching. When used with indicator_id, this function will ignore the values of
    pattern_search_strings and pattern_types, and return the indicator specified by the Id even if it doesn't match either of those
    input parameters. The name of the indicator, such as its filename or signature name, can also be provided as the indicator_id.

    This tool will return a list of the indicators (also known as signatures, IOCs, or patterns) that match the provided input.
    """
    if not OpenCTIConfig.opencti_url:
        await ctx.error("OpenCTI URL was not set. Tool will not work")
        return None

    octi = OpenCTIApiClient(
        url=OpenCTIConfig.opencti_url, token=OpenCTIConfig.opencti_key, ssl_verify=True
    )

    found_indicators = []

    try:
        filter_block = {}
        if indicator_id:
            # If indicator_id is specified, then do a lookup for the Id value as either an OpenCTI
            # or STIX Id. Fetch the requested Id regardless of any pattern_types filter provided.
            filter_block = {
                "mode": "or",
                "filters": [
                    {
                        "key": "id",
                        "values": [indicator_id],
                        "operator": "eq",
                        "mode": "and",
                    },
                    {
                        "key": "standard_id",
                        "values": [indicator_id],
                        "operator": "eq",
                        "mode": "and",
                    },
                    {
                        "key": "name",
                        "values": [indicator_id],
                        "operator": "eq",
                        "mode": "and",
                    },
                ],
                "filterGroups": {},
            }
        else:
            filter_block = {
                "mode": "and",
                "filters": [
                    {
                        "key": "pattern",
                        "values": pattern_search_strings,
                        "mode": "and",
                        "operator": "contains",
                    },
                ],
                "filterGroups": {},
            }

            if pattern_types:
                # If pattern_types is provided, then add a pattern_type filter to the filter block. Otherwise,
                # don't filter by pattern_type at all. This will optimize search and also ensures that this
                # code will return patterns that aren't present in the hard-coded pattern_types list here.
                filter_block["filters"].append(
                    {
                        "key": "pattern_type",
                        "values": pattern_types,
                        "mode": "or",
                        "operator": "eq",
                    }
                )

        ind = octi.indicator.read(
            filters=filter_block,
            customAttributes=ind_projection,
        )
        await ctx.debug(f"Got {json.dumps(ind)}")

        if ind is None:
            await ctx.info("Result from OpenCTI was None")
            return None

        for i in ind:
            parsed_ind = parse_indicator(ind)
            await ctx.debug(f"Made {json.dumps(parsed_ind)}")

            found_indicators.append(parsed_ind)

        return found_indicators
    except Exception as e:
        await ctx.error("Failed: {e}\n".format(e=e))
        raise e


def tool_init(url, key):
    OpenCTIConfig.opencti_url = url
    OpenCTIConfig.opencti_key = key
    return opencti_indicator_lookup
