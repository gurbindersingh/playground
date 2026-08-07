"""Typed models for TV Time and TMDB JSON data."""

from collections.abc import Mapping, Sequence
from typing import Literal, NotRequired, TypedDict

type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | Mapping[str, JSONValue] | Sequence[JSONValue]
type CSVRow = dict[str | None, str | list[str] | None]
type MediaKind = Literal["shows", "movies"]


class TMDBGenre(TypedDict):
    id: int
    name: str


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


class AggregatedWatchedEpisode(TypedDict):
    season: int
    episode: int
    updated_at: str


class EnrichedWatchedEpisode(AggregatedWatchedEpisode):
    name: str | None
    overview: str | None
    air_date: str | None
    runtime: int | None
    still_path: str | None
    vote_average: float | None
    vote_count: int | None


class WatchData(TypedDict):
    name: str
    created_at: str
    updated_at: str


class AggregatedShowWatchData(WatchData):
    is_archived: bool
    episodes_watched: list[AggregatedWatchedEpisode]


class AggregatedMovieWatchData(WatchData):
    watched: bool


class EnrichedShowWatchData(WatchData):
    is_archived: bool
    episodes_watched: list[EnrichedWatchedEpisode]
    first_air_date: str | None
    last_air_date: str | None
    homepage: str | None
    id: int | None
    in_production: bool | None
    next_episode_to_air: TMDBEpisodeDetail | None
    original_name: str | None
    backdrop_path: str | None
    poster_path: str | None
    number_of_episodes: int | None
    number_of_seasons: int | None
    overview: str | None
    popularity: float | None
    status: str | None
    type: str | None
    vote_average: float | None
    vote_count: int | None
    genres: list[TMDBGenre]
    languages: list[str]
    seasons: list[TMDBSeason]


class EnrichedMovieWatchData(WatchData):
    watched: bool
    release_date: str | None
    homepage: str | None
    id: int | None
    original_language: str | None
    original_title: str | None
    title: str | None
    backdrop_path: str | None
    poster_path: str | None
    overview: str | None
    popularity: float | None
    runtime: int | None
    status: str | None
    vote_average: float | None
    vote_count: int | None
    genres: list[TMDBGenre]
    spoken_languages: list[TMDBSpokenLanguage]


type ShowIndex = dict[str, AggregatedShowWatchData]
type MovieIndex = dict[str, AggregatedMovieWatchData]


class IndexedWatchData(TypedDict):
    shows: ShowIndex
    movies: MovieIndex


class AggregatedWatchData(TypedDict):
    shows: list[AggregatedShowWatchData]
    movies: list[AggregatedMovieWatchData]


class EnrichedWatchData(TypedDict):
    shows: list[EnrichedShowWatchData]
    movies: list[EnrichedMovieWatchData]


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
    shows: dict[str, list[TMDBSearchCandidate]]
    movies: dict[str, list[TMDBSearchCandidate]]


class TMDBSearchPage(TypedDict):
    page: NotRequired[int]
    results: list[TMDBSearchCandidate]
    total_pages: int
    total_results: NotRequired[int]


class TMDBSelectionCache(TypedDict):
    shows: dict[str, int | None]
    movies: dict[str, int | None]


class TMDBShowDetail(TypedDict):
    first_air_date: NotRequired[str | None]
    last_air_date: NotRequired[str | None]
    homepage: NotRequired[str | None]
    id: int
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
    id: int
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
    shows: dict[str, TMDBShowDetail]
    movies: dict[str, TMDBMovieDetail]


type JSONDocument = (
    JSONValue
    | IndexedWatchData
    | AggregatedWatchData
    | EnrichedWatchData
    | TMDBSearchData
    | TMDBSelectionCache
    | TMDBDetailsData
)
