// Initial JavaScript of the Mini App, gzip, against the TZ 13 budget (250 KB).
// Counts what index.html loads at start: the entry script and its modulepreload chunks.
// Run after `npm run build`: node scripts/check-size.mjs

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const BUDGET = 250 * 1024;
const dist = fileURLToPath(new URL("../dist/", import.meta.url));

const html = readFileSync(join(dist, "index.html"), "utf8");
const files = [...html.matchAll(/(?:src|href)="(\/assets\/[^"]+\.js)"/g)].map((m) => m[1]);

let total = 0;
for (const file of files) {
  const size = gzipSync(readFileSync(join(dist, file)), { level: 9 }).length;
  total += size;
  console.log(`${(size / 1024).toFixed(1).padStart(7)} KB  ${file}`);
}
console.log(`${(total / 1024).toFixed(1).padStart(7)} KB  initial JS (gzip), budget ${BUDGET / 1024} KB`);
if (total > BUDGET) {
  console.error("Initial JavaScript is over the TZ 13 budget.");
  process.exit(1);
}
