import { chromium } from "@playwright/test";
import * as cheerio from "cheerio";
import { pathInDataDirectory } from "./utils/file_util";

/**
 * Adds a delay.
 *
 * @param min Minimum delay in milliseconds.
 * @param max Maximum delay in milliseconds.
 * @returns A promise that will be fulfilled after the delay.
 */
async function delay(min = 1000, max = 10000) {
  return new Promise((resolve) => {
    console.log("Delay");
    setTimeout(resolve, Math.max(min, Math.random() * max));
  });
}

/**
 * This function extract the content of multiple pages and saves them the file
 * system. All pages will be extracted using the same browser session for
 * efficiency.
 *
 * @param pages Array of pages to extract.
 * @returns Content of the pages.
 */
export async function extractContent(
  pages: {
    url: string;
    saveTo: string;
  }[],
) {
  const browser = await chromium.launch();
  const extractedContent: string[] = [];

  for (const pageConfig of pages) {
    console.log(`Extracting page ${pageConfig.url}.`);
    const browserPage = await browser.newPage();
    await browserPage.goto(pageConfig.url);

    const content = await browserPage.content();
    Bun.write(pathInDataDirectory(pageConfig.saveTo), content);
    extractedContent.push(content);
    await delay();
  }
  browser.close();
  return extractedContent;
}

/**
 *
 * @param filePaths HTML file to read from the file system.
 * @param restrictToElement HTML element in which to search for links.
 * @returns List of URLs.
 */
export async function extractLinksFromHtmlFile(
  filePaths: string,
  restrictToElement = "body",
) {
  console.log(`Reading file: ${filePaths}.`);

  const file = Bun.file(pathInDataDirectory(filePaths));
  if (!file.exists()) return [];
  const content = await file.text();

  const links = await extractLinks(content, restrictToElement);
  return links;
}

/**
 *
 * @param html A string containing HTML.
 * @param restrictToElement HTML element in which to search for links.
 * @returns List of URLs.
 */
export async function extractLinks(html: string, restrictToElement = "body") {
  const $ = cheerio.load(html);

  return (
    $(restrictToElement)
      .find("a")
      .toArray()
      .map((link) =>
        link.attribs["href"] !== undefined ? link.attribs["href"] : "",
      )
      // Filter out all blank links
      .filter((l) => l)
  );
}
