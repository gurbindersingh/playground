from pathlib import Path
from typing import Iterable

_ROOT_MARKERS: tuple[str, ...] = (
    "pyproject.toml",
    "setup.py",
    "requirements.txt",
    ".git",
)


def _contains_marker(path: Path, markers: Iterable[str] = _ROOT_MARKERS) -> bool:
    return any((path / marker).exists() for marker in markers)


def _find_project_root(
    start: Path | None = None, markers: Iterable[str] = _ROOT_MARKERS
) -> Path:
    """
    Walk up the directory tree from *start* until a marker is found.

    Args:
        start:  Where to begin the search.
                Defaults to the directory that contains *this* file.

        markers: Iterable of marker names that identify the root.

    Returns:
        The *Path* object of the detected project root. If no marker is
        found, a error is thrown.
    """
    current = (start or Path(__file__)).resolve()

    # The *parents* sequence does *not* include the path itself, so we
    # prepend *current* explicitly to also check the starting directory.
    for directory in (current, *current.parents):
        if _contains_marker(directory, markers):
            return directory

    raise FileNotFoundError(
        f"Could not determine the root directory. None of the markers {markers} were found."
    )


PROJECT_ROOT = _find_project_root()

if __name__ == "__main__":
    print(_find_project_root())
