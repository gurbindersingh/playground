import { appendFileSync, copyFileSync } from "fs";
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
