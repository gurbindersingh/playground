import { readdir } from "node:fs/promises";
import { getConfigs } from "../configs/twi-scraper";
import { scrapePages, extractLinks, reduceToText } from "./extractors";
import {
  appendToFileWithBackup,
  fileExists,
  pathInDataDirectory,
  readFile,
  saveFile,
} from "./utils/file_util";

interface ScrapedPage {
  url: string;
  lastScraped: Date;
  rawFile: string;
  cleanedFile?: string;
}

/**
 * Extracts the URLs from all anchor tags on this page. The results only
 * contain URLs that match the current site.
 *
 * @param html HTML page from which to extract the links.
 * @param configs Scraper configs.
 * @returns A list of URLs that have not already been scraped.  */
async function extractNewLinks(
  html: string,
  configs: ReturnType<typeof getConfigs>,
) {
  console.log("Extracting new links.");

  const scrapedLinks = await readFile(
    configs.dataDirectory,
    configs.links.saveTo,
  );
  // Filter out all outgoing links (those that point to other sites) and links
  // that have already been scraped.
  const newLinks = extractLinks(html, configs.links.selector).filter(
    (link) => link.startsWith(configs.siteUrl) && !scrapedLinks.includes(link),
  );
  return newLinks;
}

/**
 * Creates the necessary page configs for scraping.
 *
 * @param urls The links for which to create the configs.
 * @param scraperConfigs Scraper configs.
 * @returns A list of page configs.
 */
async function createSubPageConfigs(
  urls: string[],
  scraperConfigs: ReturnType<typeof getConfigs>,
) {
  const { siteUrl, dataDirectory, savedPages: files } = scraperConfigs;
  return urls
    .map((url) => ({
      url: url,
      saveTo: url.substring(siteUrl.length).replaceAll("/", "."),
      endsWithSlash: url.endsWith("/"),
    }))
    .map((pageConfig) => ({
      url: pageConfig.url,
      saveTo: pageConfig.endsWithSlash
        ? pageConfig.saveTo.substring(0, pageConfig.saveTo.length - 1)
        : pageConfig.saveTo,
    }))
    .map((config) => ({
      ...config,
      saveTo: `${dataDirectory}/${files.raw}/${config.saveTo}.html`,
    }));
}

async function cleanUpPages(
  filePaths: string[],
  configs: ReturnType<typeof getConfigs>,
) {
  if (filePaths.length < 1) throw Error("Empty array");

  for (const path of filePaths) {
    console.log("Cleaning up file", path);
    const html = await readFile(
      configs.dataDirectory,
      configs.savedPages.raw,
      path,
    );

    const cleanedPage = reduceToText(html, configs.textNodes);
    if (configs.filters.some((filter) => cleanedPage.includes(filter)))
      continue;
    else
      await saveFile(
        cleanedPage,
        configs.dataDirectory,
        configs.savedPages.cleaned,
        path,
      );
  }
}

async function saveNewLinks(
  links: { url: string; saveTo: string }[],
  configs: ReturnType<typeof getConfigs>,
) {
  console.log("Saving new links.");
  for (const link of links) {
    if (
      await fileExists(
        configs.dataDirectory,
        configs.savedPages.cleaned,
        link.saveTo,
      )
    ) {
      console.log(`Adding link ${link.url} to scraped pages.`);
      appendToFileWithBackup(
        "\n" + link.url,
        configs.dataDirectory,
        configs.links.saveTo,
      );
    }
  }
}

/**
 * Entry point for the scraper.
 * Workflow:
 * 1. Scrape the start page(s).
 * 2. Extract all links (href attributes) from them.
 * 3. Keep only those that have not been scraped yet and remove those pointing
 *    to different sites.
 * 4. Scrape pages referenced by those links.
 * 5. Clean up pages.
 */
async function main() {
  const isMock = true;
  const configs = getConfigs();

  const startPagesHtml: string[] = isMock
    ? await Promise.all(
        configs.startPages.map((page) =>
          readFile(configs.dataDirectory, page.saveTo),
        ),
      )
    : await scrapePages(configs.startPages);
  // Use a Set here to filter out duplicate URLs.
  const newLinks: string[] = (
    await Promise.all(
      startPagesHtml.map((page) => extractNewLinks(page, configs)),
    )
  ).flatMap((links) => links);

  const newPagesConfigs = await createSubPageConfigs(newLinks, configs);
  isMock
    ? await Promise.all(newPagesConfigs.map((conf) => readFile(conf.saveTo)))
    : await scrapePages(newPagesConfigs);

  cleanUpPages(
    newPagesConfigs
      // FIXME: the clean up function expects the file name, not full path
      .map((conf) => conf.saveTo)
      .sort((a, b) => a.localeCompare(b)),
    configs,
  );
  saveNewLinks(newPagesConfigs, configs);
}

main();
