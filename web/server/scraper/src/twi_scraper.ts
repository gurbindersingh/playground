import path from "node:path";
import { getConfigs } from "../configs/twi-scraper.ts";
import { extractLinks, reduceToText, scrapePages } from "./extractors.ts";
import {
  appendToFileWithBackup,
  fileExists,
  readFile,
  saveFile,
} from "./utils/file_util.ts";
import { getLogger } from "./utils/logger.ts";

const logger = getLogger("twi_scraper");

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
  logger.info("Extracting new links.");

  const scrapedLinks = await readFile(
    configs.dataDirectory,
    configs.links.saveTo,
  );
  // Filter out all outgoing links (those that point to other sites) and links
  // that have already been scraped.
  const allLinks = extractLinks(html, configs.links.selector);
  logger.debug(`Found ${allLinks.length} total link(s) in page.`);
  const newLinks = allLinks.filter(
    (link) => link.startsWith(configs.siteUrl) && !scrapedLinks.includes(link),
  );
  logger.debug(`${newLinks.length} new link(s) after filtering external and already-scraped URLs.`);
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
  if (filePaths.length < 1) {
    logger.error("cleanUpPages called with empty array.");
    throw Error("Empty array");
  }
  logger.info(`Cleaning up ${filePaths.length} file(s).`);

  for (const filePath of filePaths) {
    logger.debug(`Cleaning up file ${filePath}`);
    const html = await readFile(
      configs.dataDirectory,
      configs.savedPages.raw,
      path.basename(filePath),
    );

    const cleanedPage = reduceToText(html, configs.textNodes);
    if (configs.filters.some((filter) => cleanedPage.includes(filter))) {
      logger.warn(`Skipping ${filePath} (matches exclusion filter).`);
      continue;
    } else
      await saveFile(
        cleanedPage,
        configs.dataDirectory,
        configs.savedPages.cleaned,
        filePath,
      );
  }
}

async function saveNewLinks(
  links: { url: string; saveTo: string }[],
  configs: ReturnType<typeof getConfigs>,
) {
  logger.info(`Saving new links (${links.length} candidate(s)).`);
  for (const link of links) {
    if (
      await fileExists(
        configs.dataDirectory,
        configs.savedPages.cleaned,
        link.saveTo,
      )
    ) {
      logger.info(`Adding link ${link.url} to scraped pages.`);
      appendToFileWithBackup(
        "\n" + link.url,
        configs.dataDirectory,
        configs.links.saveTo,
      );
    } else {
      logger.warn(`Skipping ${link.url} (cleaned file not found).`);
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
  logger.info(`Starting scraper in ${isMock ? "mock" : "live"} mode.`);
  logger.debug(`Fetching ${configs.startPages.length} start page(s).`);

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
  logger.info(`Found ${newLinks.length} new link(s) to scrape.`);

  const newPagesConfigs = await createSubPageConfigs(newLinks, configs);
  logger.debug(`Scraping ${newPagesConfigs.length} page(s).`);
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

main().then(() => logger.info("Done."));
