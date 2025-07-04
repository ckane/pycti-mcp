import json
from typing import Annotated
from pycti import OpenCTIApiClient
from fastmcp import Context


class OpenCTIConfig:
    opencti_url = ""
    opencti_key = ""


def parse_obs(o):
    parsed_o = {
        "observable_value": o["observable_value"],
        "stix_id": o["standard_id"],
        "opencti_id": o["id"],
        "data_type": o["entity_type"],
        "description": o["x_opencti_description"],
        "created": o["created_at"],
        "last_updated": o["updated_at"],
        "labels": [label["value"] for label in o["objectLabel"]],
        "external_reports": [
            {"name": r["name"], "urls": [e["url"] for e in r["externalReferences"]]}
            for r in o["reports"]
        ]
        + [{"name": "Self", "urls": [e["url"] for e in o["externalReferences"]]}],
        "notes": [note["content"] for note in o["notes"]],
        "opinions": [
            {"sentiment": op["opinion"], "explanation": op["explanation"]}
            for op in o["opinions"]
        ],
    }
    return parsed_o


obs_projection = """
    id
    standard_id
    observable_value
    entity_type
    x_opencti_description
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
    reports {
      edges {
        node {
          id
          name
          externalReferences {
            edges {
              node {
                url
              }
            }
          }
        }
      }
    }
    cases {
      edges {
        node {
          id
          name
          externalReferences {
            edges {
              node {
                url
              }
            }
          }
        }
      }
    }
    groupings {
      edges {
        node {
          id
          name
          externalReferences {
            edges {
              node {
                url
              }
            }
          }
        }
      }
    }
    notes {
      edges {
        node {
          id
          content
        }
      }
    }
    opinions {
      edges {
        node {
          id
          explanation
          opinion
        }
      }
    }
"""


async def opencti_observable_lookup(
    observable: Annotated[str, "The value of the observable to look up in OpenCTI"],
    ctx: Context,
) -> Annotated[dict, "Data structure representing the observable"] | None:
    """Given obervable, look it up in OpenCTI. If it is stored in OpenCTI return a JSON
    data structure with information about it. Otherwise, if it doesn't exist, None will
    be returned. The observable parameter can also be a STIX id or OpenCTI UUID, and the
    tool will return the observable with that Id, if it exists in the platform."""
    if not OpenCTIConfig.opencti_url:
        await ctx.error("OpenCTI URL was not set. Tool will not work")
        return None

    octi = OpenCTIApiClient(
        url=OpenCTIConfig.opencti_url, token=OpenCTIConfig.opencti_key, ssl_verify=True
    )

    try:
        o = octi.stix_cyber_observable.read(
            filters={
                "mode": "or",
                # Search for a matching value across the id and standard_id fields, too, so
                # so that this function can return an observable by either Id or Value
                "filters": [
                    {"key": "value", "values": [observable]},
                    {"key": "id", "values": [observable]},
                    {"key": "standard_id", "values": [observable]},
                ],
                "filterGroups": [],
            },
            customAttributes=obs_projection,
        )
        await ctx.debug(f"Got {json.dumps(o)}")

        if o is None:
            await ctx.info("Result from OpenCTI was None")
            return None

        parsed_o = parse_obs(o)
        await ctx.debug(f"Made {json.dumps(parsed_o)}")

        return parsed_o
    except Exception as e:
        await ctx.error("Failed: {e}\n".format(e=e))
        raise e


def tool_init(url, key):
    OpenCTIConfig.opencti_url = url
    OpenCTIConfig.opencti_key = key
    return opencti_observable_lookup
