import { ConsoleHandler, Logger } from "@std/log";
import type { LevelName } from "@std/log";

const level = (Deno.env.get("LOG_LEVEL")?.toUpperCase() || "INFO") as LevelName;

const handler = new ConsoleHandler("DEBUG", {
  formatter: (record) => {
    const t = record.datetime;
    const date = [t.getFullYear(), t.getMonth() + 1, t.getDate()]
      .map((n) => String(n).padStart(2, "0"))
      .join("-");
    const time = [t.getHours(), t.getMinutes(), t.getSeconds()]
      .map((n) => String(n).padStart(2, "0"))
      .join(":");
    return `[${date} ${time}] ${record.levelName.padEnd(8)} ${record.loggerName.padEnd(15)} ${record.msg}`;
  },
});

export function getLogger(name: string) {
  return new Logger(name, level, { handlers: [handler] });
}
