# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import json
import os
from typing import List

import requests


class CRAG(object):
    """A client for interacting with the CRAG server, offering methods to query various domains such as Open, Movie, Finance, Music, and Sports. Each method corresponds to an API endpoint on the CRAG server.

    Attributes:
        server (str): The base URL of the CRAG server. Defaults to "http://127.0.0.1:8080".

    Methods:
        open_search_entity_by_name(query: str) -> dict: Search for entities by name in the Open domain.
        open_get_entity(entity: str) -> dict: Retrieve detailed information about an entity in the Open domain.
        movie_get_person_info(person_name: str) -> dict: Get information about a person related to movies.
        movie_get_movie_info(movie_name: str) -> dict: Get information about a movie.
        movie_get_year_info(year: str) -> dict: Get information about movies released in a specific year.
        movie_get_movie_info_by_id(movie_id: int) -> dict: Get movie information by its unique ID.
        movie_get_person_info_by_id(person_id: int) -> dict: Get person information by their unique ID.
        finance_get_company_name(query: str) -> dict: Search for company names in the finance domain.
        finance_get_ticker_by_name(query: str) -> dict: Retrieve the ticker symbol for a given company name.
        finance_get_price_history(ticker_name: str) -> dict: Get the price history for a given ticker symbol.
        finance_get_detailed_price_history(ticker_name: str) -> dict: Get detailed price history for a ticker symbol.
        finance_get_dividends_history(ticker_name: str) -> dict: Get dividend history for a ticker symbol.
        finance_get_market_capitalization(ticker_name: str) -> dict: Retrieve market capitalization for a ticker symbol.
        finance_get_eps(ticker_name: str) -> dict: Get earnings per share (EPS) for a ticker symbol.
        finance_get_pe_ratio(ticker_name: str) -> dict: Get the price-to-earnings (PE) ratio for a ticker symbol.
        finance_get_info(ticker_name: str) -> dict: Get financial information for a ticker symbol.
        music_search_artist_entity_by_name(artist_name: str) -> dict: Search for music artists by name.
        music_search_song_entity_by_name(song_name: str) -> dict: Search for songs by name.
        music_get_billboard_rank_date(rank: int, date: str = None) -> dict: Get Billboard ranking for a specific rank and date.
        music_get_billboard_attributes(date: str, attribute: str, song_name: str) -> dict: Get attributes of a song from Billboard rankings.
        music_grammy_get_best_artist_by_year(year: int) -> dict: Get the Grammy Best New Artist for a specific year.
        music_grammy_get_award_count_by_artist(artist_name: str) -> dict: Get the total Grammy awards won by an artist.
        music_grammy_get_award_count_by_song(song_name: str) -> dict: Get the total Grammy awards won by a song.
        music_grammy_get_best_song_by_year(year: int) -> dict: Get the Grammy Song of the Year for a specific year.
        music_grammy_get_award_date_by_artist(artist_name: str) -> dict: Get the years an artist won a Grammy award.
        music_grammy_get_best_album_by_year(year: int) -> dict: Get the Grammy Album of the Year for a specific year.
        music_grammy_get_all_awarded_artists() -> dict: Get all artists awarded the Grammy Best New Artist.
        music_get_artist_birth_place(artist_name: str) -> dict: Get the birthplace of an artist.
        music_get_artist_birth_date(artist_name: str) -> dict: Get the birth date of an artist.
        music_get_members(band_name: str) -> dict: Get the member list of a band.
        music_get_lifespan(artist_name: str) -> dict: Get the lifespan of an artist.
        music_get_song_author(song_name: str) -> dict: Get the author of a song.
        music_get_song_release_country(song_name: str) -> dict: Get the release country of a song.
        music_get_song_release_date(song_name: str) -> dict: Get the release date of a song.
        music_get_artist_all_works(artist_name: str) -> dict: Get all works by an artist.
        sports_soccer_get_games_on_date(team_name: str, date: str) -> dict: Get soccer games on a specific date.
        sports_nba_get_games_on_date(team_name: str, date: str) -> dict: Get NBA games on a specific date.
        sports_nba_get_play_by_play_data_by_game_ids(game_ids: List[str]) -> dict: Get NBA play by play data for a set of game ids.

    Note:
        Each method performs a POST request to the corresponding API endpoint and returns the response as a JSON dictionary.
    """

    def __init__(self):
        self.server = os.environ.get("CRAG_SERVER", "http://127.0.0.1:8080")

    def open_search_entity_by_name(self, query: str):
        url = self.server + "/open/search_entity_by_name"
        headers = {"accept": "application/json"}
        data = {"query": query}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def open_get_entity(self, entity: str):
        url = self.server + "/open/get_entity"
        headers = {"accept": "application/json"}
        data = {"query": entity}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def movie_get_person_info(self, person_name: str):
        url = self.server + "/movie/get_person_info"
        headers = {"accept": "application/json"}
        data = {"query": person_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def movie_get_movie_info(self, movie_name: str):
        url = self.server + "/movie/get_movie_info"
        headers = {"accept": "application/json"}
        data = {"query": movie_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def movie_get_year_info(self, year: str):
        url = self.server + "/movie/get_year_info"
        headers = {"accept": "application/json"}
        data = {"query": year}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def movie_get_movie_info_by_id(self, movid_id: int):
        url = self.server + "/movie/get_movie_info_by_id"
        headers = {"accept": "application/json"}
        data = {"query": movid_id}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def movie_get_person_info_by_id(self, person_id: int):
        url = self.server + "/movie/get_person_info_by_id"
        headers = {"accept": "application/json"}
        data = {"query": person_id}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def finance_get_company_name(self, query: str):
        url = self.server + "/finance/get_company_name"
        headers = {"accept": "application/json"}
        data = {"query": query}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def finance_get_ticker_by_name(self, query: str):
        url = self.server + "/finance/get_ticker_by_name"
        headers = {"accept": "application/json"}
        data = {"query": query}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def finance_get_price_history(self, ticker_name: str):
        url = self.server + "/finance/get_price_history"
        headers = {"accept": "application/json"}
        data = {"query": ticker_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def finance_get_detailed_price_history(self, ticker_name: str):
        url = self.server + "/finance/get_detailed_price_history"
        headers = {"accept": "application/json"}
        data = {"query": ticker_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def finance_get_dividends_history(self, ticker_name: str):
        url = self.server + "/finance/get_dividends_history"
        headers = {"accept": "application/json"}
        data = {"query": ticker_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def finance_get_market_capitalization(self, ticker_name: str):
        url = self.server + "/finance/get_market_capitalization"
        headers = {"accept": "application/json"}
        data = {"query": ticker_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def finance_get_eps(self, ticker_name: str):
        url = self.server + "/finance/get_eps"
        headers = {"accept": "application/json"}
        data = {"query": ticker_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def finance_get_pe_ratio(self, ticker_name: str):
        url = self.server + "/finance/get_pe_ratio"
        headers = {"accept": "application/json"}
        data = {"query": ticker_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def finance_get_info(self, ticker_name: str):
        url = self.server + "/finance/get_info"
        headers = {"accept": "application/json"}
        data = {"query": ticker_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_search_artist_entity_by_name(self, artist_name: str):
        url = self.server + "/music/search_artist_entity_by_name"
        headers = {"accept": "application/json"}
        data = {"query": artist_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_search_song_entity_by_name(self, song_name: str):
        url = self.server + "/music/search_song_entity_by_name"
        headers = {"accept": "application/json"}
        data = {"query": song_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_get_billboard_rank_date(self, rank: int, date: str = None):
        url = self.server + "/music/get_billboard_rank_date"
        headers = {"accept": "application/json"}
        data = {"rank": rank, "date": date}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_get_billboard_attributes(self, date: str, attribute: str, song_name: str):
        url = self.server + "/music/get_billboard_attributes"
        headers = {"accept": "application/json"}
        data = {"date": date, "attribute": attribute, "song_name": song_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_grammy_get_best_artist_by_year(self, year: int):
        url = self.server + "/music/grammy_get_best_artist_by_year"
        headers = {"accept": "application/json"}
        data = {"query": year}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_grammy_get_award_count_by_artist(self, artist_name: str):
        url = self.server + "/music/grammy_get_award_count_by_artist"
        headers = {"accept": "application/json"}
        data = {"query": artist_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_grammy_get_award_count_by_song(self, song_name: str):
        url = self.server + "/music/grammy_get_award_count_by_song"
        headers = {"accept": "application/json"}
        data = {"query": song_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_grammy_get_best_song_by_year(self, year: int):
        url = self.server + "/music/grammy_get_best_song_by_year"
        headers = {"accept": "application/json"}
        data = {"query": year}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_grammy_get_award_date_by_artist(self, artist_name: str):
        url = self.server + "/music/grammy_get_award_date_by_artist"
        headers = {"accept": "application/json"}
        data = {"query": artist_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_grammy_get_best_album_by_year(self, year: int):
        url = self.server + "/music/grammy_get_best_album_by_year"
        headers = {"accept": "application/json"}
        data = {"query": year}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_grammy_get_all_awarded_artists(self):
        url = self.server + "/music/grammy_get_all_awarded_artists"
        headers = {"accept": "application/json"}
        result = requests.post(url, headers=headers)
        return json.loads(result.text)

    def music_get_artist_birth_place(self, artist_name: str):
        url = self.server + "/music/get_artist_birth_place"
        headers = {"accept": "application/json"}
        data = {"query": artist_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_get_artist_birth_date(self, artist_name: str):
        url = self.server + "/music/get_artist_birth_date"
        headers = {"accept": "application/json"}
        data = {"query": artist_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_get_members(self, band_name: str):
        url = self.server + "/music/get_members"
        headers = {"accept": "application/json"}
        data = {"query": band_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_get_lifespan(self, artist_name: str):
        url = self.server + "/music/get_lifespan"
        headers = {"accept": "application/json"}
        data = {"query": artist_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_get_song_author(self, song_name: str):
        url = self.server + "/music/get_song_author"
        headers = {"accept": "application/json"}
        data = {"query": song_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_get_song_release_country(self, song_name: str):
        url = self.server + "/music/get_song_release_country"
        headers = {"accept": "application/json"}
        data = {"query": song_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_get_song_release_date(self, song_name: str):
        url = self.server + "/music/get_song_release_date"
        headers = {"accept": "application/json"}
        data = {"query": song_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def music_get_artist_all_works(self, song_name: str):
        url = self.server + "/music/get_artist_all_works"
        headers = {"accept": "application/json"}
        data = {"query": song_name}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def sports_soccer_get_games_on_date(self, date: str, team_name: str = None):
        url = self.server + "/sports/soccer/get_games_on_date"
        headers = {"accept": "application/json"}
        data = {"team_name": team_name, "date": date}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def sports_nba_get_games_on_date(self, date: str, team_name: str = None):
        url = self.server + "/sports/nba/get_games_on_date"
        headers = {"accept": "application/json"}
        data = {"team_name": team_name, "date": date}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)

    def sports_nba_get_play_by_play_data_by_game_ids(self, game_ids: List[str]):
        url = self.server + "/sports/nba/get_play_by_play_data_by_game_ids"
        headers = {"accept": "application/json"}
        data = {"game_ids": game_ids}
        result = requests.post(url, json=data, headers=headers)
        return json.loads(result.text)
