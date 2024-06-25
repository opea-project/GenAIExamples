# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
""" This code is adapted from BigScience PII detection
https://github.com/bigscience-workshop/data-preparation/blob/main/preprocessing/training/02_pii/bigscience_pii_detect_redact.py

MST BigScience PII Code
Original colab that is a source of this file is located at
    https://colab.research.google.com/drive/1086H3-LGMz3gX0pGy9ECgr8KflosSKso
# License
Copyright 2022 Authors of this Notebook
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import ipaddress
import sys

import regex

year_patterns = [
    regex.compile(
        r"(?:^|[\b\s@?,!;:\'\")(.\p{Han}])([1-2][0-9]{3}[\p{Pd}/][1-2][0-9]{3})(?:$|[\s@,?!;:\'\"(.\p{Han}])"
    ),  # yyyy-yyyy or yyyy/yyyy
    regex.compile(
        r"(?:^|[\b\s@?,!;:\'\")(.\p{Han}])([1-2][0-9]{3}[\p{Pd}/.][0-3][0-9][\p{Pd}/.][0-3][0-9])(?:$|[\s@,?!;:\'\"(.\p{Han}])"
    ),  # yyyy-mm-dd or yyyy-dd-mm or yyyy/mm/dd or yyyy/dd/mm or yyyy.mm.dd or yyyy.dd.mm
    regex.compile(
        r"(?:^|[\b\s@?,!;:\'\")(.\p{Han}])([0-3][0-9][\p{Pd}/.][0-3][0-9][\p{Pd}/.](?:[0-9]{2}|[1-2][0-9]{3}))(?:$|[\s@,?!;:\'\"(.\p{Han}])"
    ),
    # mm-dd-yyyy or dd-mm-yyyy or mm/dd/yyyy or dd/mm/yyyy or mm.dd.yyyy or dd.mm.yyyy or the same but with yy instead of yyyy
    regex.compile(
        r"(?:^|[\b\s@?,!;:\'\")(.\p{Han}])([0-3][0-9][\p{Pd}/](?:[0-9]{2}|[1-2][0-9]{3}))(?:$|[\s@,?!;:\'\"(.\p{Han}])"
    ),  # mm-yyyy or mm/yyyy or the same but with yy
    regex.compile(
        r"(?:^|[\b\s@?,!;:\'\")(.\p{Han}])([1-2][0-9]{3}-[0-3][0-9])(?:$|[\s@,?!;:\'\"(.\p{Han}])"
    ),  # yyyy-mm or yyyy/mm
]

ipv4_pattern = r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}"
ipv6_pattern = r"(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])"
ip_pattern = regex.compile(
    r"(?:^|[\b\s@?,!;:\'\")(.\p{Han}])(" + r"|".join([ipv4_pattern, ipv6_pattern]) + ")(?:$|[\s@,?!;:'\"(.\p{Han}])",
    flags=regex.MULTILINE,
)


def matches_date_pattern(matched_str):
    # Screen out date false positives
    for year_regex in year_patterns:
        if year_regex.match(matched_str):
            return True
    return False


def ip_has_digit(matched_str):
    """Checks to make sure the PII span is not just :: or whatever that may
    accidentally be picked up by making sure there are digits."""
    return any(map(str.isdigit, matched_str))


def filter_versions(matched_str, context):
    """Filter addresses in this format x.x.x.x  and the words dns/server
    don't appear in the neighboring context, usually they are just versions."""
    # count occurrence of dots
    dot_count = matched_str.count(".")
    exclude = dot_count == 3 and len(matched_str) == 7
    if exclude:
        if "dns" in context.lower() or "server" in context.lower():
            return False
    return exclude


def not_ip_address(matched_str):
    """make sure the string has a valid IP address format
    e.g: 33.01.33.33 is not a valid IP address because of the 0 in front of 1
    TODO: fix this directly in the regex"""
    try:
        ipaddress.ip_address(matched_str)
        return False
    except ValueError:
        return True


def detect_ip(content):
    """Detects ip addresses in a string using regex matching
    Args:
      content (str): A string containing the text to be analyzed.
    Returns:
        A list of dicts containing the tag type, the matched string, and the start and
        end indices of the match.
    """

    matches = []

    # regex matching
    matches_tmp = ip_pattern.finditer(content)
    for match in matches_tmp:
        if match.groups():
            if len(match.groups()) > 1 and match.groups()[1]:
                sys.stderr.write("Warning: Found substring matches in the main match.")
            # setup outputs
            value = match.group(1)
            start, end = match.span(1)
            if value:
                # Filter out false positive IPs
                if not ip_has_digit(value):
                    continue
                if matches_date_pattern(value):
                    continue
                if filter_versions(value, content[start - 100 : end + 100]) or not_ip_address(value):
                    continue
                # combine if conditions in one

                matches.append(
                    {
                        "tag": "IP_ADDRESS",
                        "value": value,
                        "start": start,
                        "end": end,
                    }
                )
            else:
                raise ValueError("No match found inside groups")
    return matches
