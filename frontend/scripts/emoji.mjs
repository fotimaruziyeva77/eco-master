// Emoji pictures that look the same on every phone: Microsoft Fluent Emoji, flat style
// (MIT, https://github.com/microsoft/fluentui-emoji), from the @iconify-json package.
// Writes public/emoji/<code points>.svg, e.g. 1f525.svg for 🔥 (no FE0F selectors), which
// src/components/Emoji.tsx shows. Runs before `dev` and `build`; skin-tone variants are left out.
//   node scripts/emoji.mjs

import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const pkg = require("@iconify-json/fluent-emoji-flat/package.json");
const set = require("@iconify-json/fluent-emoji-flat/icons.json");
const chars = require("@iconify-json/fluent-emoji-flat/chars.json");
const info = require("@iconify-json/fluent-emoji-flat/info.json");

const out = fileURLToPath(new URL("../public/emoji/", import.meta.url));
const stamp = `${out}VERSION`;
const version = `${pkg.name}@${pkg.version}`;

if (existsSync(stamp) && readFileSync(stamp, "utf8").trim() === version) process.exit(0);

rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });

const SKIN_TONE = /-(light|medium-light|medium|medium-dark|dark)(-skin-tone)?$|skin-tone/;
let count = 0;
for (const [code, name] of Object.entries(chars)) {
  if (SKIN_TONE.test(name)) continue;
  const icon = set.icons[name] ?? set.icons[set.aliases?.[name]?.parent];
  if (!icon) continue;
  const width = icon.width ?? set.width ?? 16;
  const height = icon.height ?? set.height ?? 16;
  const box = `${icon.left ?? 0} ${icon.top ?? 0} ${width} ${height}`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${box}" width="${width}" height="${height}">${icon.body}</svg>`;
  writeFileSync(`${out}${code.replace(/-fe0f/g, "")}.svg`, svg);
  count += 1;
}

writeFileSync(
  `${out}LICENSE.txt`,
  `Fluent Emoji by ${info.author.name} (${info.author.url}), ${info.license.title} license:\n${info.license.url}\n`,
);
writeFileSync(stamp, `${version}\n`);
console.log(`emoji: ${count} pictures in public/emoji (${version})`);
