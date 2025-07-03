import random
import sys
import json
import logging
from typing import Annotated
from pycti import OpenCTIApiClient


# Parse a "Threat Adversary" when fetched from the system
def parse_adv(ta):
    parsed_ta = {
        "stix_id": ta["standard_id"],
        "opencti_id": ta["id"],
        "name": ta["name"],
        "data_type": ta["entity_type"],
        "description": ta["description"],
        "created": ta["created_at"],
        "last_updated": ta["updated_at"],
        "labels": [l["value"] for l in ta["objectLabel"]],
        "first_seen": ta["first_seen"],
        "last_seen": ta["last_seen"],
        "external_reports": [
            {"name": r["name"], "urls": [e["url"] for e in r["externalReferences"]]}
            for r in ta["reports"]
        ]
        + [{"name": "Self", "urls": [e["url"] for e in ta["externalReferences"]]}],
        "notes": [note["content"] for note in ta["notes"]],
        "opinions": [
            {"sentiment": op["opinion"], "explanation": op["explanation"]}
            for op in ta["opinions"]
        ],
    }

    # Safely populate optional keys if they exist in the source object
    for optkey in [
        "aliases",
        "goals",
        "roles",
        "sophistication",
        "primary_motivation",
        "secondary_motivations",
        "objective",
        "resource_level",
    ]:
        if optkey in ta:
            parsed_ta[optkey] = ta[optkey]

    return parsed_ta


notes_projection = """
    id
    content
    authors
"""

opinions_projection = """
    id
    opinion
    explanation
    authors
"""

reports_projection = """
    id
    standard_id
    name
    published
    entity_type
    created_at
    updated_at
    created
    modified
    description
    report_types
    objectLabel {
      id
      value
    }
    externalReferences {
      edges {
        node {
          url
        }
      }
    }
"""

ta_projection = """
    id
    standard_id
    name
    aliases
    entity_type
    description
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
"""


# Should look up campaign, intrusion_set, threat_actor_group, and threat_actor_individual
def opencti_adversary_lookup(
    name: Annotated[str, "The adversary or threat name or alias to look up in OpenCTI"],
) -> (
    Annotated[list[dict], "List of Data structures representing matching adversaries"]
    | None
):
    """Given a name or alias of a threat adversary, look it up in OpenCTI. If it is stored in OpenCTI return a JSON
    data structure with information about it. Can be used to look up Threat Actors, Threat Actor Groups, Campaigns, Individuals,
    and Intrusion Sets. If it isn't found, None will be returned."""
    log = logging.getLogger(name=__name__)

    if not ToolSpec.opencti_url:
        log.error("OpenCTI URL was not set. Tool will not work")
        return None

    octi = OpenCTIApiClient(
        url=ToolSpec.opencti_url, token=ToolSpec.opencti_key, ssl_verify=True
    )

    adversary_types = [
        octi.campaign,
        octi.intrusion_set,
        octi.threat_actor_group,
        octi.threat_actor_individual,
    ]

    ta_list = []

    for adv_type in adversary_types:
        try:
            ta = adv_type.read(
                filters={
                    "mode": "or",
                    "filters": [
                        {"key": "name", "values": [name]},
                        {"key": "aliases", "values": [name]},
                    ],
                    "filterGroups": [],
                },
                customAttributes=ta_projection,
            )
            log.debug(f"Got {json.dumps(ta)}")

            if ta == None:
                log.info(f"Result from OpenCTI for {adv_type}={name} was None")
                continue

            # Look up the reports associated with the Adversary
            ta_rpts = octi.report.list(
                filters={
                    "mode": "and",
                    "filters": [{"key": "objects", "values": [ta["id"]]}],
                    "filterGroups": [],
                },
                orderBy="published",
                orderMode="asc",
                customAttributes=reports_projection,
            )

            # Add reports to the Threat Adversary data structure, if any relate
            if not ta_rpts:
                ta["reports"] = []
            else:
                ta["reports"] = ta_rpts

            # Look up the notes associated with the Adversary
            ta_notes = octi.note.list(
                filters={
                    "mode": "and",
                    "filters": [{"key": "objects", "values": [ta["id"]]}],
                    "filterGroups": [],
                },
                customAttributes=notes_projection,
            )

            # Add reports to the Threat Adversary data structure, if any relate
            if not ta_notes:
                ta["notes"] = []
            else:
                ta["notes"] = ta_notes

            # Look up the opinions associated with the Adversary
            ta_opinions = octi.opinion.list(
                filters={
                    "mode": "and",
                    "filters": [{"key": "objects", "values": [ta["id"]]}],
                    "filterGroups": [],
                },
                customAttributes=opinions_projection,
            )

            # Add reports to the Threat Adversary data structure, if any relate
            if not ta_opinions:
                ta["opinions"] = []
            else:
                ta["opinions"] = ta_opinions

            parsed_ta = parse_adv(ta)
            log.debug(f"Made {json.dumps(parsed_ta)}")

            ta_list.append(parsed_ta)
        except Exception as e:
            log.error("Failed: {e}\n".format(e=e))
            raise e

    return ta_list if ta_list else None


class ToolSpec:
    fn = opencti_adversary_lookup
    opencti_url = ""
    opencti_key = ""
