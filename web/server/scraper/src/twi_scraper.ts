import { readdir } from "node:fs/promises";
import { getConfigs } from "../configs/twi-scraper";
import { extractContent, extractLinks, reduceToText } from "./extractors";
import {
  appendToFileWithBackup,
  fileExists,
  pathInDataDirectory,
  readFile,
  saveFile,
} from "./utils/file_util";

async function scrapeStartpage(
  configs: ReturnType<typeof getConfigs>,
  mock = false,
) {
  if (mock)
    return [await readFile(configs.dataDirectory, configs.startPage.saveTo)];
  else return await extractContent([configs.startPage]);
}

async function extractNewLinks(
  html: string,
  configs: ReturnType<typeof getConfigs>,
) {
  console.log("Extracting new links.");

  const previousLinks = await readFile(
    configs.dataDirectory,
    configs.links.saveTo,
  );

  const newLinks = (await extractLinks(html, configs.links.selector)).filter(
    (link) => link.startsWith(configs.siteUrl) && !previousLinks.includes(link),
  );
  return newLinks;
}

async function createSubPageConfigs(
  newLinks: string[],
  configs: ReturnType<typeof getConfigs>,
) {
  const { siteUrl, dataDirectory, savedPages: files } = configs;
  return newLinks
    .map((link) => ({
      url: link,
      endsWithSlash: link.endsWith("/"),
      saveTo: link.substring(siteUrl.length).replaceAll("/", "."),
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
  files: string[],
  configs: ReturnType<typeof getConfigs>,
) {
  if (files.length < 1) throw Error("Empty array");

  for (const file of files) {
    console.log("Cleaning up file", file);
    const html = await readFile(
      configs.dataDirectory,
      configs.savedPages.raw,
      file,
    );

    const cleanedPage = await reduceToText(html, configs.textNodes);
    if (configs.filters.some((filter) => cleanedPage.includes(filter)))
      continue;
    else
      await saveFile(
        cleanedPage,
        configs.dataDirectory,
        configs.savedPages.cleaned,
        file,
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
 * 1. Scrape the start page.
 * 2. Extract all links from this page. Keep only the new ones.
 * 3. Scrape pages referenced by those links.
 */
async function main() {
  const mock = true;
  const configs = getConfigs();
  const pagesHtml = await scrapeStartpage(configs, mock);
  const newLinks: string[] = [];

  for (const html of pagesHtml) {
    newLinks.push(...(await extractNewLinks(html, configs)));
  }
  const newPagesConfigs = await createSubPageConfigs(newLinks, configs);
  const rawPages: string[] = [];

  if (!mock) rawPages.push(...(await extractContent(newPagesConfigs)));
  else
    rawPages.push(
      ...(await readdir(
        pathInDataDirectory(configs.dataDirectory, configs.savedPages.raw),
      )),
    );
  cleanUpPages(
    rawPages.sort((a, b) => a.localeCompare(b)),
    configs,
  );
  saveNewLinks(newPagesConfigs, configs);
}

main();
