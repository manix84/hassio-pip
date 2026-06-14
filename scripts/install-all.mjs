import { spawnSync } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const isWindows = process.platform === "win32";
const npmCommand = isWindows ? "npm.cmd" : "npm";
const androidLocalPropertiesPath = join("android-tv-app", "local.properties");
const androidSdkCandidates = [
  process.env.ANDROID_HOME,
  process.env.ANDROID_SDK_ROOT,
  join(homedir(), "Library", "Android", "sdk"),
  join(homedir(), "Android", "Sdk"),
  "/opt/android-sdk",
  "/usr/local/share/android-sdk",
  "/opt/homebrew/share/android-sdk",
].filter(Boolean);
const integrationDir = "ha-integration";
const integrationVenvDir = join(integrationDir, ".venv");
const integrationVenvPython = join(
  integrationVenvDir,
  isWindows ? "Scripts/python.exe" : "bin/python",
);

function run(label, command, args, options = {}) {
  console.log(`\n==> ${label}`);

  const result = spawnSync(command, args, {
    cwd: options.cwd ?? process.cwd(),
    shell: false,
    stdio: "inherit",
  });

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function escapePropertiesValue(value) {
  return value.replaceAll("\\", "\\\\").replaceAll(":", "\\:");
}

function findAndroidSdk() {
  return androidSdkCandidates.find((candidate) => existsSync(candidate));
}

function configureAndroidSdk() {
  if (existsSync(androidLocalPropertiesPath)) {
    console.log("\n==> Android SDK already configured");
    return;
  }

  const androidSdkPath = findAndroidSdk();

  if (!androidSdkPath) {
    console.error("\nAndroid SDK location not found.");
    console.error("Install the Android SDK with Android Studio, then rerun `npm run install:all`.");
    console.error("Alternatively set ANDROID_HOME or create android-tv-app/local.properties:");
    console.error("  sdk.dir=/absolute/path/to/android/sdk");
    process.exit(1);
  }

  writeFileSync(
    androidLocalPropertiesPath,
    `sdk.dir=${escapePropertiesValue(androidSdkPath)}\n`,
  );

  console.log(`\n==> Wrote Android SDK path to ${androidLocalPropertiesPath}`);
}

run("Installing root npm dependencies", npmCommand, ["install"]);
run("Checking Android app npm metadata", npmCommand, [
  "--prefix",
  "android-tv-app",
  "install",
  "--package-lock=false",
]);
configureAndroidSdk();
run("Installing website npm dependencies", npmCommand, ["--prefix", "website", "install"]);

if (existsSync("ha-integration/requirements-dev.txt")) {
  if (!existsSync(integrationVenvPython)) {
    run("Creating Home Assistant integration Python virtualenv", "python3", [
      "-m",
      "venv",
      integrationVenvDir,
    ]);
  }

  run("Updating Home Assistant integration virtualenv pip", integrationVenvPython, [
    "-m",
    "pip",
    "install",
    "--upgrade",
    "pip",
  ]);

  run("Installing Home Assistant integration Python dev tools", integrationVenvPython, [
    "-m",
    "pip",
    "install",
    "-r",
    "ha-integration/requirements-dev.txt",
  ]);
}

console.log("\nInstall complete.");
console.log("Android Gradle dependencies are resolved by Android Studio or Gradle during builds.");
console.log("Home Assistant Python tools are installed in ha-integration/.venv.");
