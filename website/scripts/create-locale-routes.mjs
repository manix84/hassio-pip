import { copyFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const locales = ["de", "nl", "fr", "es", "it", "pt-br", "pl"];
const distDir = new URL("../dist/", import.meta.url);
const sourceIndex = new URL("index.html", distDir);

await Promise.all(
  locales.map(async (locale) => {
    const targetDir = new URL(`${locale}/`, distDir);
    await mkdir(targetDir, { recursive: true });
    await copyFile(sourceIndex, fileURLToPath(new URL("index.html", targetDir)));
  })
);

console.log(`Created static locale routes: ${locales.join(", ")}`);
