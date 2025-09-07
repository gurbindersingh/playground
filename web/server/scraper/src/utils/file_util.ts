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
