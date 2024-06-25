# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from .utils import PIIEntityType


def detect_name_password(content, pipeline, entity_types=None):
    """Detects name and password in a string using bigcode/starpii model
    Args:
      entity_types: detection types
      pipeline: a transformer model
      content (str): A string containing the text to be analyzed.
    Returns:
        A list of dicts containing the tag type, the matched string, and the start and
        end indices of the match.
    """
    if entity_types is None:
        entity_types = [PIIEntityType.NAME, PIIEntityType.PASSWORD]
    matches = []
    if pipeline is None:
        return matches
    try:
        for entity in pipeline(content):
            entity_group = entity["entity_group"]
            if ("NAME" == entity_group and PIIEntityType.NAME in entity_types) or (
                "PASSWORD" == entity_group and PIIEntityType.PASSWORD in entity_types
            ):
                matches.append(
                    {
                        "tag": entity_group,
                        "value": entity["word"],
                        "start": entity["start"],
                        "end": entity["end"],
                    }
                )
    except:
        pass

    return matches
