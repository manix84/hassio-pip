import { readFileSync, writeFileSync } from "node:fs";
import { parseSemver, readRootVersion } from "./version-utils.mjs";

const args = process.argv.slice(2);

function argValue(name) {
  const index = args.indexOf(name);
  if (index === -1) {
    return null;
  }
  return args[index + 1] ?? null;
}

function normalizeVersion(value) {
  return String(value ?? "").trim().replace(/^v/i, "");
}

function compareVersions(left, right) {
  const parsedLeft = parseSemver(left);
  const parsedRight = parseSemver(right);
  if (parsedLeft.major !== parsedRight.major) {
    return parsedLeft.major - parsedRight.major;
  }
  if (parsedLeft.minor !== parsedRight.minor) {
    return parsedLeft.minor - parsedRight.minor;
  }
  return parsedLeft.patch - parsedRight.patch;
}

function parseWhatsNew(markdown) {
  const headingPattern = /^##\s+(\d+\.\d+\.\d+)\b[^\n]*\n/gm;
  const headings = [...markdown.matchAll(headingPattern)];

  return headings.map((heading, index) => {
    const start = heading.index ?? 0;
    const end = headings[index + 1]?.index ?? markdown.length;
    return {
      version: heading[1],
      markdown: markdown.slice(start, end).trim(),
    };
  });
}

const targetVersion = normalizeVersion(argValue("--version") ?? readRootVersion());
const sinceVersion = normalizeVersion(argValue("--since"));
const outputPath = argValue("--output") ?? "dist/release-notes.md";

parseSemver(targetVersion);
if (sinceVersion) {
  parseSemver(sinceVersion);
}

const entries = parseWhatsNew(readFileSync("WHATSNEW.md", "utf8"));
const selected = entries.filter((entry) => {
  const currentOrOlder = compareVersions(entry.version, targetVersion) <= 0;
  const newerThanPrevious = sinceVersion
    ? compareVersions(entry.version, sinceVersion) > 0
    : entry.version === targetVersion;
  return currentOrOlder && newerThanPrevious;
});

const releaseNotes =
  selected.length > 0
    ? selected.map((entry) => entry.markdown).join("\n\n")
    : [
        `## ${targetVersion}`,
        "",
        "No WHATSNEW.md entry was found for this release.",
      ].join("\n");

writeFileSync(outputPath, `${releaseNotes}\n`);
console.log(
  `Generated release notes for ${targetVersion}${
    sinceVersion ? ` since ${sinceVersion}` : ""
  }: ${outputPath}`
);
