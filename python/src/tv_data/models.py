"""Typed models for TV Time and TMDB JSON data."""

from typing import NotRequired, Required, TypedDict

type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | list[JSONValue] | dict[str, JSONValue]


class TMDBGenre(TypedDict):
    id: Required[int]
    name: Required[str]


class TMDBSpokenLanguage(TypedDict):
    english_name: NotRequired[str | None]
    iso_639_1: NotRequired[str | None]
    name: NotRequired[str | None]


class TMDBSeason(TypedDict):
    air_date: NotRequired[str | None]
    episode_count: NotRequired[int | None]
    id: NotRequired[int | None]
    name: NotRequired[str | None]
    overview: NotRequired[str | None]
    poster_path: NotRequired[str | None]
    season_number: NotRequired[int | None]
    vote_average: NotRequired[float | None]


class TMDBEpisodeDetail(TypedDict):
    air_date: NotRequired[str | None]
    episode_number: NotRequired[int | None]
    id: NotRequired[int | None]
    name: NotRequired[str | None]
    overview: NotRequired[str | None]
    runtime: NotRequired[int | None]
    season_number: NotRequired[int | None]
    show_id: NotRequired[int | None]
    still_path: NotRequired[str | None]
    vote_average: NotRequired[float | None]
    vote_count: NotRequired[int | None]


class WatchedEpisode(TypedDict):
    season: Required[int]
    episode: Required[int]
    updated_at: Required[str]
    name: NotRequired[str | None]
    overview: NotRequired[str | None]
    air_date: NotRequired[str | None]
    runtime: NotRequired[int | None]
    still_path: NotRequired[str | None]
    vote_average: NotRequired[float | None]
    vote_count: NotRequired[int | None]


class WatchData(TypedDict):
    name: Required[str]
    created_at: Required[str]
    updated_at: Required[str]


class ShowWatchData(WatchData):
    is_archived: Required[bool]
    total_episodes_watched: Required[int]
    episodes_watched: Required[list[WatchedEpisode]]
    first_air_date: NotRequired[str | None]
    last_air_date: NotRequired[str | None]
    homepage: NotRequired[str | None]
    id: NotRequired[int | None]
    in_production: NotRequired[bool | None]
    next_episode_to_air: NotRequired[TMDBEpisodeDetail | None]
    original_name: NotRequired[str | None]
    backdrop_path: NotRequired[str | None]
    poster_path: NotRequired[str | None]
    number_of_episodes: NotRequired[int | None]
    number_of_seasons: NotRequired[int | None]
    overview: NotRequired[str | None]
    popularity: NotRequired[float | None]
    status: NotRequired[str | None]
    type: NotRequired[str | None]
    vote_average: NotRequired[float | None]
    vote_count: NotRequired[int | None]
    genres: NotRequired[list[TMDBGenre]]
    languages: NotRequired[list[str]]
    seasons: NotRequired[list[TMDBSeason]]


class MovieWatchData(WatchData):
    watched: Required[bool]
    release_date: NotRequired[str | None]
    homepage: NotRequired[str | None]
    id: NotRequired[int | None]
    original_language: NotRequired[str | None]
    original_title: NotRequired[str | None]
    title: NotRequired[str | None]
    backdrop_path: NotRequired[str | None]
    poster_path: NotRequired[str | None]
    overview: NotRequired[str | None]
    popularity: NotRequired[float | None]
    runtime: NotRequired[int | None]
    status: NotRequired[str | None]
    vote_average: NotRequired[float | None]
    vote_count: NotRequired[int | None]
    genres: NotRequired[list[TMDBGenre]]
    spoken_languages: NotRequired[list[TMDBSpokenLanguage]]


type WatchRecord = ShowWatchData | MovieWatchData
type ShowIndex = dict[str, ShowWatchData]
type MovieIndex = dict[str, MovieWatchData]


class IndexedWatchData(TypedDict):
    shows: Required[ShowIndex]
    movies: Required[MovieIndex]


class AggregatedWatchData(TypedDict):
    shows: Required[list[ShowWatchData]]
    movies: Required[list[MovieWatchData]]


class TMDBSearchCandidate(TypedDict):
    adult: NotRequired[bool]
    backdrop_path: NotRequired[str | None]
    first_air_date: NotRequired[str | None]
    genre_ids: NotRequired[list[int]]
    id: NotRequired[int]
    name: NotRequired[str]
    original_language: NotRequired[str]
    original_name: NotRequired[str]
    original_title: NotRequired[str]
    origin_country: NotRequired[list[str]]
    overview: NotRequired[str | None]
    popularity: NotRequired[float]
    poster_path: NotRequired[str | None]
    release_date: NotRequired[str | None]
    title: NotRequired[str]
    vote_average: NotRequired[float]
    vote_count: NotRequired[int]


class TMDBSearchData(TypedDict):
    shows: Required[dict[str, list[TMDBSearchCandidate]]]
    movies: Required[dict[str, list[TMDBSearchCandidate]]]


class TMDBSearchPage(TypedDict):
    page: NotRequired[int]
    results: Required[list[TMDBSearchCandidate]]
    total_pages: Required[int]
    total_results: NotRequired[int]


class TMDBSelectionCache(TypedDict):
    shows: Required[dict[str, int]]
    movies: Required[dict[str, int]]


class TMDBShowDetail(TypedDict):
    first_air_date: NotRequired[str | None]
    last_air_date: NotRequired[str | None]
    homepage: NotRequired[str | None]
    id: Required[int]
    in_production: NotRequired[bool | None]
    next_episode_to_air: NotRequired[TMDBEpisodeDetail | None]
    original_name: NotRequired[str | None]
    backdrop_path: NotRequired[str | None]
    poster_path: NotRequired[str | None]
    number_of_episodes: NotRequired[int | None]
    number_of_seasons: NotRequired[int | None]
    overview: NotRequired[str | None]
    popularity: NotRequired[float | None]
    status: NotRequired[str | None]
    type: NotRequired[str | None]
    vote_average: NotRequired[float | None]
    vote_count: NotRequired[int | None]
    name: NotRequired[str]
    genres: NotRequired[list[TMDBGenre]]
    languages: NotRequired[list[str]]
    seasons: NotRequired[list[TMDBSeason]]


class TMDBMovieDetail(TypedDict):
    release_date: NotRequired[str | None]
    homepage: NotRequired[str | None]
    id: Required[int]
    original_language: NotRequired[str | None]
    original_title: NotRequired[str | None]
    title: NotRequired[str]
    backdrop_path: NotRequired[str | None]
    poster_path: NotRequired[str | None]
    overview: NotRequired[str | None]
    popularity: NotRequired[float | None]
    runtime: NotRequired[int | None]
    status: NotRequired[str | None]
    vote_average: NotRequired[float | None]
    vote_count: NotRequired[int | None]
    genres: NotRequired[list[TMDBGenre]]
    spoken_languages: NotRequired[list[TMDBSpokenLanguage]]


class TMDBDetailsData(TypedDict):
    shows: Required[dict[str, TMDBShowDetail]]
    movies: Required[dict[str, TMDBMovieDetail]]
