import random
import sys
import json
import logging
from typing import Annotated
from pycti import OpenCTIApiClient
from .local_settings import api_url, api_token

# Parse a "Threat Adversary" when fetched from the system
def parse_adv(ta):
    parsed_ta = {
        'stix_id': ta['standard_id'],
        'opencti_id': ta['id'],
        'name': ta['name'],
        'data_type': ta['entity_type'],
        'description': ta['description'],
        'created': ta['created_at'],
        'last_updated': ta['updated_at'],
        'labels': [l['value'] for l in ta['objectLabel']],
        'first_seen': ta['first_seen'],
        'last_seen': ta['last_seen'],
        #'external_reports': [
        #    {'name': r['name'], 'urls': [e['url'] for e in r['externalReferences']]} for r in ta['reports']
        #] + [
        #    {'name': 'Self', 'urls': [e['url'] for e in ta['externalReferences']]}
        #],
       # 'notes': [note['content'] for note in ta['notes']],
       # 'opinions': [{'sentiment': op['opinion'], 'explanation': op['explanation']} for op in ta['opinions']]
    }

    # Safely populate optional keys if they exist in the source object
    for optkey in [
            'aliases', 'goals', 'roles', 'sophistication', 'primary_motivation', 'secondary_motivations', 'objective', 'resource_level'
    ]:
        if optkey in ta:
            parsed_ta[optkey] = ta[optkey]

    return parsed_ta

ta_projection="""
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

# Should look up campaign, intrusion_set, threat_actor_group, and threat_actor_individual
def opencti_adversary_lookup(
    name: Annotated[str, "The adversary or threat name or alias to look up in OpenCTI"],
) -> Annotated[dict, "Data structure representing the adversary"] | None:
    """Given a name or alias of a threat adversary, look it up in OpenCTI. If it is stored in OpenCTI return a JSON
       data structure with information about it. Can be used to look up Threat Actors, Threat Actor Groups, Campaigns, Individuals,
       and Intrusion Sets. If it isn't found, None will be returned."""
    log = logging.getLogger(name="octimcp")
    octi = OpenCTIApiClient(url=api_url, token=api_token, ssl_verify=True)

    adversary_types = [octi.campaign, octi.intrusion_set, octi.threat_actor_group, octi.threat_actor_individual]

    ta_list = []

    for adv_type in adversary_types:
        try:
            ta = adv_type.read(filters={
                "mode": "or",
                "filters": [{"key": "name", "values": [name]}, {"key": "aliases", "values": [name]}],
                "filterGroups": [],
            }, customAttributes=ta_projection)
            log.info(f"Got {ta}")

            if ta == None:
                log.info(f"Result from OpenCTI for {adv_type}={name} was None")
                continue

            parsed_ta = parse_adv(ta)
            log.info(f"Made {parsed_ta}")

            ta_list.append(parsed_ta)
        except Exception as e:
            log.error("Failed: {e}\n".format(e=e))
            raise e

    return ta_list if ta_list else None

class ToolSpec:
    name = "opencti_adversary_lookup"
    description = """Given a name or alias of a threat adversary, look it up in OpenCTI. If it is stored in OpenCTI return a JSON
       data structure with information about it. Can be used to look up Threat Actors, Threat Actor Groups, Campaigns, Individuals,
       and Intrusion Sets. If it isn't found, None will be returned."""
    fn = opencti_adversary_lookup
