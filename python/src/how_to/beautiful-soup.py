from bs4 import BeautifulSoup


def remove_tags(markup: str) -> dict:
    html = BeautifulSoup(markup, features="html.parser")
    [element.decompose() for element in html.find_all("i")]
    print(html)


if __name__ == "__main__":
    markup = """
        <a href="http://example.com/">
            I linked to <i>example.com</i> and <i>foo.bar</i>.
        </a>
    """
    remove_tags(markup)
