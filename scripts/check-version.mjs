import { existsSync, readFileSync } from "node:fs";
import {
  ANDROID_BUILD_PATH,
  ANDROID_PACKAGE_PATH,
  HA_MANIFEST_PATH,
  ROOT_PACKAGE_PATH,
  WEBSITE_PACKAGE_PATH,
  parseSemver,
  readJson
} from "./version-utils.mjs";

const rootPackage = readJson(ROOT_PACKAGE_PATH);
const expectedVersion = rootPackage.version;

const failures = [];
const warnings = [];

try {
  parseSemver(expectedVersion);
} catch (error) {
  failures.push(`Root package.json version is invalid: ${error.message}`);
}

if (existsSync(ANDROID_PACKAGE_PATH)) {
  const androidPackage = readJson(ANDROID_PACKAGE_PATH);
  if (androidPackage.version !== expectedVersion) {
    failures.push(
      `${ANDROID_PACKAGE_PATH} version ${androidPackage.version} does not match root ${expectedVersion}`
    );
  }
} else {
  warnings.push(`TODO: ${ANDROID_PACKAGE_PATH} does not exist yet`);
}

if (existsSync(WEBSITE_PACKAGE_PATH)) {
  const websitePackage = readJson(WEBSITE_PACKAGE_PATH);
  if (websitePackage.version !== expectedVersion) {
    failures.push(
      `${WEBSITE_PACKAGE_PATH} version ${websitePackage.version} does not match root ${expectedVersion}`
    );
  }
} else {
  warnings.push(`TODO: ${WEBSITE_PACKAGE_PATH} does not exist yet`);
}

if (existsSync(ANDROID_BUILD_PATH)) {
  const androidBuild = readFileSync(ANDROID_BUILD_PATH, "utf8");
  const versionNameMatch = androidBuild.match(/versionName\s*=\s*"([^"]+)"/);
  if (!versionNameMatch) {
    failures.push(`Could not find Android versionName in ${ANDROID_BUILD_PATH}`);
  } else if (versionNameMatch[1] !== expectedVersion) {
    failures.push(
      `Android versionName ${versionNameMatch[1]} does not match root ${expectedVersion}`
    );
  }
} else {
  warnings.push(`TODO: ${ANDROID_BUILD_PATH} does not exist yet`);
}

if (existsSync("WHATSNEW.md")) {
  const whatsNew = readFileSync("WHATSNEW.md", "utf8");
  if (!whatsNew.includes(`## ${expectedVersion} `)) {
    warnings.push(`WHATSNEW.md does not contain an entry for ${expectedVersion}`);
  }
}

if (existsSync(HA_MANIFEST_PATH)) {
  const haManifest = readJson(HA_MANIFEST_PATH);
  if (haManifest.version !== expectedVersion) {
    failures.push(
      `${HA_MANIFEST_PATH} version ${haManifest.version ?? "<missing>"} does not match root ${expectedVersion}`
    );
  }
} else {
  warnings.push(
    `TODO: ${HA_MANIFEST_PATH} does not exist yet; Home Assistant integration version sync will be enforced once the integration is implemented`
  );
}

if (failures.length > 0) {
  console.error("Version check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

for (const warning of warnings) {
  console.warn(`Warning: ${warning}`);
}

console.log(`Version check passed for ${expectedVersion}`);
