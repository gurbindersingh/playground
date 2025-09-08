import { appendFileSync, copyFileSync } from "fs";
import { readdir } from "fs/promises";
import { join } from "path";

export function getProjectRoot() {
  return join(import.meta.dir, "/../..");
}

export function pathFromRoot(...paths: string[]) {
  return join(getProjectRoot(), ...paths);
}

export function pathInDataDirectory(...paths: string[]) {
  return pathFromRoot("data", ...paths);
}

export function appendToFileWithBackup(content: string, ...paths: string[]) {
  const fullPath = pathInDataDirectory(...paths);
  copyFileSync(fullPath, fullPath + ".bak");
  appendToFile(content, ...paths);
}

export function appendToFile(content: string, ...paths: string[]) {
  appendFileSync(pathInDataDirectory(...paths), content);
}

export async function saveFile(content: string, ...paths: string[]) {
  const filePath = pathInDataDirectory(...paths);
  const bytesWritten = await Bun.write(filePath, content);

  if (bytesWritten >= content.length) {
    console.log(`Saved file ${filePath}.`);
  } else {
    throw Error(
      `File ${filePath} could not be written to properly. Content might be missing.`,
    );
  }
}

export async function readFile(...paths: string[]) {
  const filePath = pathInDataDirectory(...paths);
  const file = Bun.file(filePath);

  if (await file.exists()) {
    console.log(`Retrieving file ${filePath}.`);
    return file.text();
  } else {
    throw Error(`File ${filePath} does not exist.`);
  }
}

export async function fileExists(...paths: string[]) {
  const filePath = pathInDataDirectory(...paths);
  const exists = await Bun.file(filePath).exists();

  if (exists) {
    console.log(`File ${filePath} exist.`);
  } else {
    console.log(`File ${filePath} does not exist.`);
  }
  return exists;
}

export async function ls(...paths: string[]) {
  return await readdir(pathInDataDirectory(...paths));
}
