import { chromium } from "@playwright/test";
import * as cheerio from "cheerio";
import { getLogger } from "./utils/logger.ts";
import { saveFile } from "./utils/file_util.ts";

const logger = getLogger("extractors");

/**
 * Adds a delay.
 *
 * @param min Minimum delay in milliseconds.
 * @param max Maximum delay in milliseconds.
 * @returns A random delay.
 */
function randomDelay(min = 1000, max = 10000) {
  const delay = Math.round(Math.max(min, Math.random() * max));
  logger.debug(`Delay ${delay} ms`);
  return delay;
}

/**
 * This function extract the content of multiple pages and saves them the file
 * system. All pages will be extracted using the same browser session for
 * efficiency.
 *
 * @param pages Array of pages to extract.
 * @returns Content of the pages.
 */
export async function scrapePages(
  pages: {
    url: string;
    saveTo: string;
  }[],
) {
  logger.info(`Scraping ${pages.length} page(s).`);
  const browser = await chromium.launch();
  logger.debug("Browser launched.");
  const pagesContent: string[] = [];

  for (const pageConfig of pages) {
    logger.info(`Extracting page ${pageConfig.url}.`);
    const browserPage = await browser.newPage();
    const t0 = Date.now();
    try {
      await browserPage.goto(pageConfig.url);
    } catch (err) {
      logger.error(`Failed to load ${pageConfig.url}: ${err}`);
      continue;
    }
    logger.debug(`Page loaded in ${Date.now() - t0} ms.`);

    const content = await browserPage.content();
    logger.debug(`Page content: ${content.length} chars.`);
    await saveFile(content, pageConfig.saveTo);
    pagesContent.push(content);
    await new Promise((res) => setTimeout(res, randomDelay()));
  }
  browser.close();
  logger.debug("Browser closed.");
  return pagesContent;
}

/**
 *
 * @param html A string containing HTML.
 * @param restrictToElement HTML element in which to search for links.
 * @returns List of URLs.
 */
export function extractLinks(html: string, restrictToElement = "body") {
  const $ = cheerio.load(html);
  const links = $(restrictToElement)
    .find("a")
    .toArray()
    .map((link) =>
      link.attribs["href"] !== undefined ? link.attribs["href"] : "",
    )
    // Filter out all blank links
    .filter((l) => l);
  logger.debug(`Extracted ${links.length} link(s) from "${restrictToElement}".`);
  return links;
}

export function reduceToText(
  html: string,
  keep = "p, h1, h2, h3, h4, h5, h6",
  remove = "script, iframe, img",
) {
  let $ = cheerio.load(html);
  $(remove).remove();
  let elements = $(keep);

  let content = elements
    .map((_, elem) => $.html(elem))
    .get()
    .join("\n");
  content = `<html>${content}</html>`;
  return content;
}
