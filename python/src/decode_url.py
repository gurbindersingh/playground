import sys
import html
from urllib.parse import unquote


def main():
    if len(sys.argv) <= 1:
        print("Missing URL argument.")
        print("Usage: decode-url 'URL'...")
        print(
            "> NOTE: Do not forget to quote the URL! The '&' character is a bash control operator."
        )
        sys.exit(1)

    for arg in sys.argv[1:]:
        url = html.unescape(arg)
        url = unquote(url)
        print(url)


if __name__ == "__main__":
    main()
