# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json_repair
from mini_deep_search.logging_utils import format_terminal_str, log_status


def postproc_query(response_text, state):
    """
    load query for retrieval and rerank from a predefined JSON:
    {
        "keywords": "keywords for retrieval",
        "query": "query for rerank"
    }
    """
    # Default use the raw response text as the query for both retrieval and rerank
    try:
        # Attempt to parse the response text as JSON
        parsed_json = json_repair.loads(response_text)
        keywords_str = parsed_json.get("keywords", "")
        query_str = parsed_json.get("query", "")
        log_status(
            "🧲",
            f"{format_terminal_str('Keywords for retrieval:', color='magenta')} {format_terminal_str(keywords_str, italic=True)}",
        )
        log_status(
            "🔮",
            f"{format_terminal_str('Query for reranking:', color='magenta')} {format_terminal_str(query_str, italic=True)}",
        )
    except Exception as e:
        # If parsing fails, return the original response text
        print("Failed to parse JSON, returning original response text.")
        print(e)
        return response_text, response_text
    # return keywords_str, query_str
    return f"{state.question}\n{state.step}\n{keywords_str}", f"{query_str}"
