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

import sys

import regex

# Note: to reduce false positives, a number of technically-valid-but-rarely-used
# email address patterns (e.g. with parenthesis or slashes) will not match
email_pattern = regex.compile(
    r"""
    (?<= ^ | [[({<\b\s@,?!;'"\p{Han}¿¡:.] | \\['"] )  # left delimiter
    (
      (?:                                             # local part
        [^][(){}<>\b\s@,?!;'":#/\\=.\-]               # arbitrary character
        |
        (?: [=.\-] (?! [.@]) )                        # ".=-" not before ".@"
      )+
      @
      (?:
        (?:
             \w                                       # single-letter subdomain
           |
             [^.\b\s@?!;,/()>\-:]                     # subdomain (>=2 letter)
             [^.\b\s@?!;,/()>]{0,62}
             [^.\b\s@?!;,/()>\-:'"]
        )
        \.
      ){1,10}
      (?: [\p{L}\p{M}]{2,63} | xn-- \w+ )             # TLD, including IDN
    )
    (?= $ | [])}>\b\s@,?!;'"\p{Han}] | \\['"] | : (?! \d) | \. (?! \S))   # right delim
""",
    flags=regex.MULTILINE | regex.VERBOSE,
)


def detect_email(content):
    """Detects email addresses in a string using regex matching
    Args:
      content (str): A string containing the text to be analyzed.
    Returns:
        A list of dicts containing the tag type, the matched string, and the start and
        end indices of the match.
    """

    matches = []

    # regex matching
    matches_tmp = email_pattern.finditer(content)
    for match in matches_tmp:
        if match.groups():
            if len(match.groups()) > 1 and match.groups()[1]:
                sys.stderr.write("Warning: Found substring matches in the main match.")
            # setup outputs
            value = match.group(1)
            start, end = match.span(1)
            if value:
                matches.append(
                    {
                        "tag": "EMAIL",
                        "value": value,
                        "start": start,
                        "end": end,
                    }
                )
            else:
                raise ValueError("No match found inside groups")
    return matches
