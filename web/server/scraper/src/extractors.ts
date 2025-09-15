import { chromium } from "@playwright/test";
import * as cheerio from "cheerio";
import { saveFile } from "./utils/file_util";
import { sleep } from "bun";

/**
 * Adds a delay.
 *
 * @param min Minimum delay in milliseconds.
 * @param max Maximum delay in milliseconds.
 * @returns A random delay.
 */
function randomDelay(min = 1000, max = 10000) {
  const delay = Math.round(Math.max(min, Math.random() * max));
  console.log(`Delay ${delay} ms`);
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
  const browser = await chromium.launch();
  const pagesContent: string[] = [];

  for (const pageConfig of pages) {
    console.log(`Extracting page ${pageConfig.url}.`);
    const browserPage = await browser.newPage();
    await browserPage.goto(pageConfig.url);

    const content = await browserPage.content();
    await saveFile(content, pageConfig.saveTo);
    pagesContent.push(content);
    await sleep(randomDelay());
  }
  browser.close();
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
