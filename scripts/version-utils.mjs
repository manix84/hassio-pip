import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

export const ROOT_PACKAGE_PATH = "package.json";
export const ROOT_LOCK_PATH = "package-lock.json";
export const ANDROID_PACKAGE_PATH = "android-tv-app/package.json";
export const ANDROID_BUILD_PATH = "android-tv-app/app/build.gradle.kts";
export const HA_PACKAGE_PATH = "ha-integration/package.json";
export const HA_MANIFEST_PATH = "ha-integration/custom_components/ha_tv_pip/manifest.json";
export const WEBSITE_PACKAGE_PATH = "website/package.json";
export const WEBSITE_LOCK_PATH = "website/package-lock.json";

const VERSION_FILE_PATTERNS = [
  /^package\.json$/,
  /^package-lock\.json$/,
  /^android-tv-app\/package\.json$/,
  /^ha-integration\/package\.json$/,
  /^website\/package\.json$/,
  /^website\/package-lock\.json$/,
  /^android-tv-app\/.*build\.gradle(?:\.kts)?$/,
  /^ha-integration\/custom_components\/ha_tv_pip\/manifest\.json$/
];

const PATCH_PATH_PATTERNS = [
  /^android-tv-app\/app\/src\//,
  /^android-tv-app\/src\//,
  /^android-tv-app\/build\.gradle\.kts$/,
  /^android-tv-app\/settings\.gradle\.kts$/,
  /^ha-integration\/custom_components\/ha_tv_pip\//
];

const MINOR_FILE_PATTERNS = [
  /^ha-integration\/custom_components\/ha_tv_pip\/services\.yaml$/,
  /^ha-integration\/custom_components\/ha_tv_pip\/config_flow\.py$/,
  /^ha-integration\/custom_components\/ha_tv_pip\/manifest\.json$/,
  /^ha-integration\/custom_components\/ha_tv_pip\/const\.py$/,
  /^android-tv-app\/app\/src\/.*\/models\//,
  /^android-tv-app\/app\/src\/.*\/receiver\//,
  /^android-tv-app\/app\/src\/.*\/pairing\//,
  /^android-tv-app\/app\/src\/.*\/discovery\//,
  /^android-tv-app\/app\/src\/.*\/api\//
];

const SUPPORT_ONLY_PATTERNS = [
  /^docs\//,
  /^examples\//,
  /^scripts\//,
  /^\.github\//,
  /^README\.md$/,
  /^LICENSE$/,
  /^\.gitignore$/,
  /^PRIVACY\.md$/,
  /^WHATSNEW\.md$/,
  /^CODE_OF_CONDUCT\.md$/,
  /^CONTRIBUTING\.md$/,
  /^SECURITY\.md$/,
  /^SUPPORT\.md$/,
  /^package\.json$/,
  /^package-lock\.json$/,
  /^android-tv-app\/package\.json$/,
  /^ha-integration\/package\.json$/,
  /^website\//
];

const MINOR_MARKERS = [
  "[minor]",
  "[api]",
  "[breaking]",
  "[protocol]",
  "[service-schema]",
  "[pairing]",
  "[discovery]",
  "[compatibility]"
];

const MINOR_TERMS = [
  "command payload",
  "service schema",
  "pairing token",
  "discovery metadata",
  "api version",
  "protocol version",
  "streamType",
  "durationSeconds",
  "enterPip",
  "deviceId",
  "pairingRequired",
  "/show",
  "/close",
  "/status",
  "/pair"
];

export function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

export function writeJson(path, value) {
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
}

export function readRootVersion() {
  return readJson(ROOT_PACKAGE_PATH).version;
}

export function parseSemver(version) {
  const match = /^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$/.exec(version ?? "");
  if (!match) {
    throw new Error(`Invalid semantic version: ${version}`);
  }
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3])
  };
}

export function bumpSemver(version, bumpType) {
  const parsed = parseSemver(version);
  if (bumpType === "major") {
    return `${parsed.major + 1}.0.0`;
  }
  if (bumpType === "minor") {
    return `${parsed.major}.${parsed.minor + 1}.0`;
  }
  if (bumpType === "patch") {
    return `${parsed.major}.${parsed.minor}.${parsed.patch + 1}`;
  }
  throw new Error(`Unsupported version bump: ${bumpType}`);
}

export function runGit(args, options = {}) {
  const result = spawnSync("git", args, {
    encoding: "utf8",
    ...options
  });

  if (result.error) {
    throw result.error;
  }

  if (result.status !== 0) {
    throw new Error(`git ${args.join(" ")} failed: ${result.stderr.trim()}`);
  }

  return result.stdout;
}

export function getStagedFiles() {
  return runGit(["diff", "--cached", "--name-only"])
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

export function getStagedDiff(paths = []) {
  const args = ["diff", "--cached"];
  if (paths.length > 0) {
    args.push("--", ...paths);
  }
  return runGit(args);
}

export function getHeadFile(path) {
  const result = spawnSync("git", ["show", `HEAD:${path}`], {
    encoding: "utf8"
  });
  if (result.status !== 0) {
    return null;
  }
  return result.stdout;
}

export function getStagedFile(path) {
  const result = spawnSync("git", ["show", `:${path}`], {
    encoding: "utf8"
  });
  if (result.status !== 0) {
    return null;
  }
  return result.stdout;
}

export function isVersionFile(path) {
  return VERSION_FILE_PATTERNS.some((pattern) => pattern.test(path));
}

export function isSupportOnlyFile(path) {
  return SUPPORT_ONLY_PATTERNS.some((pattern) => pattern.test(path));
}

export function isPatchRuntimeFile(path) {
  return PATCH_PATH_PATTERNS.some((pattern) => pattern.test(path));
}

export function isMinorCandidateFile(path) {
  return MINOR_FILE_PATTERNS.some((pattern) => pattern.test(path));
}

function changedContentLines(diff) {
  return diff
    .split("\n")
    .filter((line) => /^[+-]/.test(line))
    .filter((line) => !line.startsWith("+++") && !line.startsWith("---"));
}

function isVersionOnlyDiff(path) {
  const diff = getStagedDiff([path]);
  const contentLines = changedContentLines(diff);

  if (contentLines.length === 0) {
    return true;
  }

  return contentLines.every((line) => {
    const content = line.slice(1).trim();
    if (content === "{" || content === "}" || content === "," || content === "") {
      return true;
    }
    return /"version"\s*:/.test(content) ||
      /"lockfileVersion"\s*:/.test(content) ||
      /"versionName"\s*=/.test(content) ||
      /versionName\s*=/.test(content) ||
      /version\s*=/.test(content) ||
      /versionCode\s*=/.test(content);
  });
}

function syncPackageLockVersion(path, nextVersion) {
  if (!existsSync(path)) {
    return false;
  }

  const lock = readJson(path);
  let changed = false;

  if (lock.version !== nextVersion) {
    lock.version = nextVersion;
    changed = true;
  }

  if (lock.packages?.[""] && lock.packages[""].version !== nextVersion) {
    lock.packages[""].version = nextVersion;
    changed = true;
  }

  if (changed) {
    writeJson(path, lock);
  }

  return changed;
}

export function areOnlyVersionFiles(stagedFiles) {
  return stagedFiles.length > 0 && stagedFiles.every((path) => isVersionFile(path));
}

export function areOnlyVersionChanges(stagedFiles) {
  return stagedFiles.length > 0 &&
    stagedFiles.every((path) => isVersionFile(path) && isVersionOnlyDiff(path));
}

export function areSupportOnlyChanges(stagedFiles) {
  return stagedFiles.length > 0 && stagedFiles.every((path) => isSupportOnlyFile(path));
}

export function hasRuntimeChanges(stagedFiles) {
  return stagedFiles.some((path) => {
    if (!isPatchRuntimeFile(path)) {
      return false;
    }
    if (isVersionFile(path)) {
      return !isVersionOnlyDiff(path);
    }
    return true;
  });
}

export function detectMinorReason(stagedFiles, diff) {
  const lowerDiff = diff.toLowerCase();
  const marker = MINOR_MARKERS.find((value) => lowerDiff.includes(value));
  if (marker) {
    return `minor marker found in staged diff: ${marker}`;
  }

  const minorFile = stagedFiles.find((path) => isMinorCandidateFile(path));
  if (minorFile) {
    return `staged API/protocol candidate changed: ${minorFile}`;
  }

  const term = MINOR_TERMS.find((value) => lowerDiff.includes(value.toLowerCase()));
  if (term) {
    return `staged diff contains API/protocol term: ${term}`;
  }

  return null;
}

export function getStagedRootVersion() {
  const stagedPackage = getStagedFile(ROOT_PACKAGE_PATH);
  if (!stagedPackage) {
    return null;
  }
  return JSON.parse(stagedPackage).version;
}

export function getHeadRootVersion() {
  const headPackage = getHeadFile(ROOT_PACKAGE_PATH);
  if (!headPackage) {
    return null;
  }
  return JSON.parse(headPackage).version;
}

export function hasAlreadyStagedVersionBump() {
  const stagedVersion = getStagedRootVersion();
  const headVersion = getHeadRootVersion();
  return Boolean(stagedVersion && headVersion && stagedVersion !== headVersion);
}

export function syncVersionFiles(nextVersion) {
  const updated = [];

  const rootPackage = readJson(ROOT_PACKAGE_PATH);
  if (rootPackage.version !== nextVersion) {
    rootPackage.version = nextVersion;
    writeJson(ROOT_PACKAGE_PATH, rootPackage);
    updated.push(ROOT_PACKAGE_PATH);
  }

  if (syncPackageLockVersion(ROOT_LOCK_PATH, nextVersion)) {
    updated.push(ROOT_LOCK_PATH);
  }

  if (existsSync(ANDROID_PACKAGE_PATH)) {
    const androidPackage = readJson(ANDROID_PACKAGE_PATH);
    if (androidPackage.version !== nextVersion) {
      androidPackage.version = nextVersion;
      writeJson(ANDROID_PACKAGE_PATH, androidPackage);
      updated.push(ANDROID_PACKAGE_PATH);
    }
  }

  if (existsSync(WEBSITE_PACKAGE_PATH)) {
    const websitePackage = readJson(WEBSITE_PACKAGE_PATH);
    if (websitePackage.version !== nextVersion) {
      websitePackage.version = nextVersion;
      writeJson(WEBSITE_PACKAGE_PATH, websitePackage);
      updated.push(WEBSITE_PACKAGE_PATH);
    }
  }

  if (syncPackageLockVersion(WEBSITE_LOCK_PATH, nextVersion)) {
    updated.push(WEBSITE_LOCK_PATH);
  }

  if (existsSync(HA_PACKAGE_PATH)) {
    const haPackage = readJson(HA_PACKAGE_PATH);
    if (haPackage.version !== nextVersion) {
      haPackage.version = nextVersion;
      writeJson(HA_PACKAGE_PATH, haPackage);
      updated.push(HA_PACKAGE_PATH);
    }
  }

  if (existsSync(ANDROID_BUILD_PATH)) {
    const current = readFileSync(ANDROID_BUILD_PATH, "utf8");
    const next = current.replace(/versionName\s*=\s*"[^"]+"/, `versionName = "${nextVersion}"`);
    if (next !== current) {
      writeFileSync(ANDROID_BUILD_PATH, next);
      updated.push(ANDROID_BUILD_PATH);
    }
  }

  if (existsSync(HA_MANIFEST_PATH)) {
    const manifest = readJson(HA_MANIFEST_PATH);
    if (manifest.version !== nextVersion) {
      manifest.version = nextVersion;
      writeJson(HA_MANIFEST_PATH, manifest);
      updated.push(HA_MANIFEST_PATH);
    }
  }

  return updated;
}

export function applyVersionBump(bumpType) {
  const oldVersion = readRootVersion();
  const newVersion = bumpSemver(oldVersion, bumpType);
  const updatedFiles = syncVersionFiles(newVersion);
  return {
    oldVersion,
    newVersion,
    updatedFiles
  };
}

export function stageFiles(files) {
  const existingFiles = files.filter((path) => existsSync(path));
  if (existingFiles.length > 0) {
    runGit(["add", ...existingFiles], { stdio: "inherit" });
  }
}

export function validateBumpType(value) {
  const bumpType = value || "auto";
  const allowed = new Set(["auto", "none", "patch", "minor", "major"]);
  if (!allowed.has(bumpType)) {
    throw new Error(`Unsupported VERSION_BUMP '${bumpType}'. Use auto, none, patch, minor, or major.`);
  }
  return bumpType;
}

export function decideAutomaticBump(stagedFiles) {
  if (stagedFiles.length === 0) {
    return { bump: "none", reason: "no staged files" };
  }

  if (areOnlyVersionChanges(stagedFiles)) {
    return { bump: "none", reason: "only version files are staged" };
  }

  if (areSupportOnlyChanges(stagedFiles)) {
    return { bump: "none", reason: "docs/support-only changes" };
  }

  const diff = getStagedDiff();
  const minorReason = detectMinorReason(stagedFiles, diff);
  if (minorReason) {
    return { bump: "minor", reason: minorReason };
  }

  const runtimeFile = stagedFiles.find((path) => isPatchRuntimeFile(path));
  if (hasRuntimeChanges(stagedFiles)) {
    return {
      bump: "patch",
      reason: `runtime implementation changed: ${runtimeFile}`
    };
  }

  return { bump: "none", reason: "no runtime-impacting staged changes" };
}
