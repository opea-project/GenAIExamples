# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


def search_web(query: str) -> str:
    """Search the web for information not contained in databases."""
    from langchain_core.tools import Tool
    from langchain_google_community import GoogleSearchAPIWrapper

    search = GoogleSearchAPIWrapper()

    tool = Tool(
        name="google_search",
        description="Search Google for recent results.",
        func=search.run,
    )

    response = tool.run(query)
    return response
