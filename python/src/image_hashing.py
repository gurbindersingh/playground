import sys
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import imagehash


def hash_image(path: Path) -> str | None:
    try:
        with Image.open(path) as img:
            return str(imagehash.phash(img))
    except UnidentifiedImageError:
        return None
    except Exception as e:
        print(f"Error hashing '{path}': {e}", file=sys.stderr)
        return None


def main():
    if len(sys.argv) <= 1:
        print("Error: Missing argument. \n" + "Usage: image-hashing.py FILE [FILE ...]")
        sys.exit(1)

    for arg in sys.argv[1:]:
        path = Path(arg)

        if not path.is_file():
            print(f"Error: '{arg}' is not a valid file", file=sys.stderr)
            continue

        hash_value = hash_image(path)
        if hash_value is not None:
            print(f"{hash_value} {path}")


if __name__ == "__main__":
    main()
