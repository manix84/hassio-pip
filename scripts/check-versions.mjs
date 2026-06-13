import { readFileSync } from "node:fs";

const rootPackage = JSON.parse(readFileSync("package.json", "utf8"));
const androidPackage = JSON.parse(readFileSync("android-tv-app/package.json", "utf8"));
const androidBuild = readFileSync("android-tv-app/app/build.gradle.kts", "utf8");
const whatsNew = readFileSync("WHATSNEW.md", "utf8");

const expectedVersion = rootPackage.version;
const versionNameMatch = androidBuild.match(/versionName\s*=\s*"([^"]+)"/);

const failures = [];

if (androidPackage.version !== expectedVersion) {
  failures.push(
    `android-tv-app/package.json version ${androidPackage.version} does not match root ${expectedVersion}`
  );
}

if (!versionNameMatch) {
  failures.push("Could not find Android versionName in android-tv-app/app/build.gradle.kts");
} else if (versionNameMatch[1] !== expectedVersion) {
  failures.push(
    `Android versionName ${versionNameMatch[1]} does not match root ${expectedVersion}`
  );
}

if (!whatsNew.includes(`## ${expectedVersion} `)) {
  failures.push(`WHATSNEW.md does not contain an entry for ${expectedVersion}`);
}

if (failures.length > 0) {
  console.error("Version check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log(`Version check passed for ${expectedVersion}`);
