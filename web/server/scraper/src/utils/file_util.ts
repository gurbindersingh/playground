import { appendFileSync, copyFileSync } from "node:fs";
import { readdir } from "node:fs/promises";
import { join } from "node:path";
import { getLogger } from "./logger.ts";

const logger = getLogger("file_util");

export function getProjectRoot() {
  return new URL("../..", import.meta.url).pathname;
}

export function pathFromRoot(...paths: string[]) {
  return join(getProjectRoot(), ...paths);
}

export function pathInDataDirectory(...paths: string[]) {
  return pathFromRoot("data", ...paths);
}

export function appendToFileWithBackup(content: string, ...paths: string[]) {
  const fullPath = pathInDataDirectory(...paths);
  logger.debug(`Backing up ${fullPath}.`);
  copyFileSync(fullPath, fullPath + ".bak");
  appendToFile(content, ...paths);
}

export function appendToFile(content: string, ...paths: string[]) {
  const filePath = pathInDataDirectory(...paths);
  logger.debug(`Appending ${content.length} char(s) to ${filePath}.`);
  appendFileSync(filePath, content);
}

export async function saveFile(content: string, ...paths: string[]) {
  const filePath = pathInDataDirectory(...paths);
  await Deno.writeTextFile(filePath, content);
  logger.debug(`Saved file ${filePath}.`);
}

export async function readFile(...paths: string[]) {
  const filePath = pathInDataDirectory(...paths);
  try {
    await Deno.stat(filePath);
  } catch {
    logger.error(`File not found: ${filePath}`);
    throw Error(`File ${filePath} does not exist.`);
  }
  logger.debug(`Retrieving file ${filePath}.`);
  return Deno.readTextFile(filePath);
}

export async function fileExists(...paths: string[]) {
  const filePath = pathInDataDirectory(...paths);
  let exists: boolean;
  try {
    await Deno.stat(filePath);
    exists = true;
  } catch {
    exists = false;
  }
  logger.debug(`File ${filePath} ${exists ? "exist" : "does not exist"}.`);
  return exists;
}

export async function ls(...paths: string[]) {
  return await readdir(pathInDataDirectory(...paths));
}
