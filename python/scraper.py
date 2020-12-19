from pathlib import Path
from random import randint
from time import sleep

import requests
from bs4 import BeautifulSoup

import utils.configs_reader as configs_reader
import utils.logger_factory as logger_factory
import utils.path_util as path_util

LOGGER = logger_factory.get_logger("twi-scraper", with_log_file=True)


def readFile(filePath):
    LOGGER.debug(f"Reading {filePath}.")
    with open(filePath, "r") as file:
        return file.readlines()


def writeFile(filePath, content: str):
    LOGGER.debug(f"Writing to {filePath}.")
    with open(filePath, mode="w", encoding="utf-8") as file:
        file.write(content)


def extractContent(htmlString: str, contentClass: str, splitPoint: str):
    # TODO: Remove images
    LOGGER.debug("Extracting content")
    html = BeautifulSoup(htmlString, features="html.parser")
    # print(html.prettify())
    images = [element.extract() for element in html.find_all("img")]
    LOGGER.debug(f"Removed {len(images)} images.")

    title = [str(element) for element in html.find_all("h1")]
    content = [str(element) for element in html.find_all(class_=contentClass)]

    entryContentRoot = BeautifulSoup(
        "\n".join(content).split(splitPoint)[0], features="html.parser"
    )

    pageContent = "".join([*title, str(entryContentRoot)])
    return pageContent


def scrapePage(url: str, filters: str):
    LOGGER.debug(f"Scraping url {url}")

    htmlPage = fetchPage(url)
    # Keep filter simple for now
    if htmlPage.split("<h1 ")[1].split("</h1>")[0].find(filters) >= 0:
        LOGGER.debug(f"Page '{url}' matches filter '{filters}', skipping.")
        return ""

    return htmlPage


def fetchPage(url: str, minWait=5, maxWait=30):
    # So that we don't accidentally DOS their website
    sleepSeconds = randint(minWait, maxWait)
    LOGGER.debug(f"Wait for {sleepSeconds} seconds before downloading {url}")
    sleep(sleepSeconds)

    response = requests.get(url, timeout=15)
    return response.content.decode()


def getFilenameFromUrl(url: str, prefix: str):
    return url.removeprefix(prefix).removesuffix("/").replace("/", "-") + ".html"


def fetchTableOfContents(url: str):
    LOGGER.debug("Fetching tables of content")

    htmlString = fetchPage(url, minWait=0, maxWait=1)
    html = BeautifulSoup(htmlString, features="html.parser")
    tocElements = [str(element) for element in html.find_all(id="table-of-contents")]

    return tocElements


def extractUrlsFromToc(tableOfContents: list[str], urlsFileWritePath: str):
    LOGGER.debug("Extracting urls from table of contents")

    urls = extractUrls("".join(tableOfContents))
    return urls


def extractUrls(htmlString: str):
    html = BeautifulSoup(htmlString, features="html.parser")
    # print(html.prettify())
    urls = [str(tag["href"]) for tag in html.find_all("a")]
    urls = [tag for tag in urls if tag.find("book") < 0]
    return urls


def main():
    configs = configs_reader.read_configs(
        f"{path_util.get_project_root()}/configs/scraper-config.json"
    )

    baseDirectory = configs["base-directory"]
    tocFilePath = f"{baseDirectory}/{configs['toc-file-path']}"
    urlsFilePath = f"{baseDirectory}/{configs['urls-file-path']}"
    rawPagesDirectory = f"{baseDirectory}/{configs['raw-pages-directory']}"
    cleanedPagesDirectory = f"{baseDirectory}/{configs['cleaned-pages-directory']}"

    tableOfContents = fetchTableOfContents(url=configs["toc-url"])
    writeFile(filePath=tocFilePath, content="".join(tableOfContents))

    tableOfContents = readFile(tocFilePath)
    urls = extractUrlsFromToc(tableOfContents=tableOfContents)
    writeFile(filePath=urlsFilePath, content="\n".join(urls))
    # urls = [url.removesuffix("\n") for url in readFile(urlsFilePath)]

    for url in urls:
        fileName = getFilenameFromUrl(url=url, prefix=configs["site-url"])
        rawPageFile = f"{rawPagesDirectory}/{fileName}"
        cleanedPageFile = f"{cleanedPagesDirectory}/{fileName}"

        if Path(cleanedPageFile).exists():
            LOGGER.debug(f"Cleaned page file '{fileName}' already exists, skipping.")
            continue

        if Path(rawPageFile).exists():
            LOGGER.debug(f"Reading raw page from {rawPageFile}")
            rawPage = readFile(rawPageFile)
        else:
            LOGGER.debug(f"Reading raw page from {url}")
            rawPage = scrapePage(url=url, filters=configs["filters"])
            if rawPage == "":
                LOGGER.debug(f"No content for page '{url}', skipping.")
                continue
            writeFile(filePath=rawPageFile, content=rawPage)

        cleanedPage = extractContent(
            htmlString="".join(rawPage),
            contentClass=configs["content-class"],
            splitPoint=configs["split-point"],
        )
        writeFile(filePath=cleanedPageFile, content=cleanedPage)

    LOGGER.debug("DONE")


if __name__ == "__main__":
    main()
