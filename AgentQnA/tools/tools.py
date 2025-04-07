# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import requests
from comps.cores.telemetry.opea_telemetry import opea_telemetry, tracer
from tools.pycragapi import CRAG


@opea_telemetry
def search_web_base(query: str) -> str:
    import os

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


@opea_telemetry
def search_knowledge_base(query: str) -> str:
    """Search a knowledge base about music and singers for a given query.

    Returns text related to the query.
    """
    url = os.environ.get("WORKER_AGENT_URL")
    print(url)
    proxies = {"http": ""}
    payload = {
        "messages": query,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    return response.json()["text"]


@opea_telemetry
def search_sql_database(query: str) -> str:
    """Search a SQL database on artists and their music with a natural language query.

    Returns text related to the query.
    """
    url = os.environ.get("SQL_AGENT_URL")
    print(url)
    proxies = {"http": ""}
    payload = {
        "messages": query,
    }
    response = requests.post(url, json=payload, proxies=proxies)
    return response.json()["text"]


@opea_telemetry
def get_grammy_best_artist_by_year(year: int) -> dict:
    """Get the Grammy Best New Artist for a specific year."""
    api = CRAG()
    year = int(year)
    return api.music_grammy_get_best_artist_by_year(year)


@opea_telemetry
def get_members(band_name: str) -> dict:
    """Get the member list of a band."""
    api = CRAG()
    return api.music_get_members(band_name)


@opea_telemetry
def get_artist_birth_place(artist_name: str) -> dict:
    """Get the birthplace of an artist."""
    api = CRAG()
    return api.music_get_artist_birth_place(artist_name)


@opea_telemetry
def get_billboard_rank_date(rank: int, date: str = None) -> dict:
    """Get Billboard ranking for a specific rank and date."""
    api = CRAG()
    rank = int(rank)
    return api.music_get_billboard_rank_date(rank, date)


@opea_telemetry
def get_song_release_date(song_name: str) -> dict:
    """Get the release date of a song."""
    api = CRAG()
    return api.music_get_song_release_date(song_name)
