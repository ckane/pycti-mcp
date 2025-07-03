import random
import sys
import json
import logging
from dateutil.parser import parse as dateparse
from typing import Annotated
from pycti import OpenCTIApiClient

desired_obj_fields = ["value", "name", "pattern", "pattern_type", "observable_value"]


def filter_object(o):
    if "relationship_type" in o:
        return False

    for f in desired_obj_fields:
        if f in o:
            return True

    return False


def translate_object(o):
    new_o = {
        "entity_type": o["entity_type"],
        "opencti_id": o["id"],
        "stix_id": o["standard_id"],
    }

    for f in desired_obj_fields:
        if f in o:
            new_o[f] = o[f]

    return new_o


def parse_rpt(rpt: dict) -> dict:
    parsed_rpt = {
        "stix_id": rpt["standard_id"],
        "opencti_id": rpt["id"],
        "labels": [l["value"] for l in rpt["objectLabel"]],
        "data_type": rpt["entity_type"],
        "description": rpt["description"],
        "name": rpt["name"],
        "created": rpt["created"],
        "modified": rpt["modified"],
        "published": rpt["published"],
        "report_types": rpt["report_types"],
        "external_urls": [e["url"] for e in rpt["externalReferences"]],
        "objects": [translate_object(o) for o in filter(filter_object, rpt["objects"])],
    }

    return parsed_rpt


report_projection = """
id
standard_id
entity_type
objectLabel {
  value
}
externalReferences {
  edges {
    node {
      source_name
      description
      url
    }
  }
}
created
modified
published
name
description
report_types
objects(all: true) {
  edges {
    node {
      ... on BasicObject {
        id
        entity_type
        parent_types
      }
      ... on BasicRelationship {
        id
        entity_type
        parent_types
      }
      ... on StixObject {
        standard_id
        spec_version
        created_at
        updated_at
      }
      ... on AttackPattern {
        name
      }
      ... on Campaign {
        name
      }
      ... on CourseOfAction {
        name
      }
      ... on Individual {
        name
      }
      ... on Organization {
        name
      }
      ... on Sector {
        name
      }
      ... on System {
        name
      }
      ... on Indicator {
        name
        pattern
        pattern_type
      }
      ... on Infrastructure {
        name
      }
      ... on IntrusionSet {
        name
      }
      ... on Position {
        name
      }
      ... on City {
        name
      }
      ... on Country {
        name
      }
      ... on Region {
        name
      }
      ... on Malware {
        name
      }
      ... on ThreatActor {
        name
      }
      ... on Tool {
        name
      }
      ... on Vulnerability {
        name
      }
      ... on Incident {
        name
      }
      ... on Event {
        name
      }
      ... on Channel {
        name
      }
      ... on Narrative {
        name
      }
      ... on Language {
        name
      }
      ... on DataComponent {
        name
      }
      ... on DataSource {
        name
      }
      ... on Case {
        name
      }
      ... on StixCyberObservable {
        observable_value
      }                        
      ... on StixCoreRelationship {
        standard_id
        spec_version
        created_at
        updated_at
        relationship_type
      }
     ... on StixSightingRelationship {
        standard_id
        spec_version
        created_at
        updated_at
      }
    }
  }
}
"""


# Look up any reports in the system that match the criteria
# TODO: Look across reports, cases, malware analyses, and groupings
def opencti_reports_lookup(
    earliest: Annotated[str | None, "The earliest date of a report"] = None,
    latest: Annotated[str | None, "The latest date of a report"] = None,
    search: Annotated[str | None, "Search terms to filter"] = None,
) -> Annotated[list | None, "Data structure listing the discovered reports"]:
    """Given a date range (start and end date) and some search terms, find all reports in the system
    matching the given criteria"""
    log = logging.getLogger(name=__name__)

    if not ToolSpec.opencti_url:
        log.error("OpenCTI URL was not set. Tool will not work")
        return None

    octi = OpenCTIApiClient(
        url=ToolSpec.opencti_url, token=ToolSpec.opencti_key, ssl_verify=True
    )

    log.info(
        f'Searching for reports between {earliest} and {latest} via search term "{search}"'
    )

    rpts_list = []

    try:
        fargs = {
            "orderMode": "desc",
            "orderBy": "published",
            "customAttributes": report_projection,
            "filters": {},
        }

        if search:
            fargs["search"] = search

        # If earliest or latest are provided, then build a filter for them
        if earliest or latest:
            daterange_filter = {
                "mode": "and",
                "filters": [],
                "filterGroups": [],
            }

            if earliest:
                earliest_dt = dateparse(earliest)
                daterange_filter["filters"].append(
                    {
                        "key": "published",
                        "values": [earliest_dt.isoformat()],
                        "operator": "gte",
                        "mode": "and",
                    }
                )

            if latest:
                latest_dt = dateparse(latest)
                daterange_filter["filters"].append(
                    {
                        "key": "published",
                        "values": [latest_dt.isoformat()],
                        "operator": "lte",
                        "mode": "and",
                    }
                )

            fargs["filters"] = daterange_filter

        log.debug(f"Query: {fargs}")
        r = octi.report.list(**fargs)

        log.debug(f"{len(r)} Reports found")

        for rpt in r:
            parsed_rpt = parse_rpt(rpt)
            rpts_list.append(parsed_rpt)
            log.debug(f"Report result: {json.dumps(parsed_rpt)}")
    except Exception as e:
        log.error(f"There was an error {e}")

    return rpts_list


class ToolSpec:
    fn = opencti_reports_lookup
    opencti_url = ""
    opencti_key = ""
