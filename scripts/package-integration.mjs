import { cpSync, existsSync, mkdirSync, readFileSync, rmSync } from "node:fs";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve, join } from "node:path";
import { spawnSync } from "node:child_process";

const rootPackage = JSON.parse(readFileSync("package.json", "utf8"));
const version = rootPackage.version;

if (!version || typeof version !== "string") {
  throw new Error("Root package.json must contain a version string");
}

const sourceDir = resolve("custom_components/ha_tv_pip");
const distDir = resolve("dist");
const outputPath = join(distDir, `ha-tv-pip-integration-v${version}.zip`);
const hacsOutputPath = join(distDir, "ha-tv-pip-integration.zip");

if (!existsSync(sourceDir)) {
  throw new Error(`Integration source directory does not exist: ${sourceDir}`);
}

mkdirSync(distDir, { recursive: true });
rmSync(outputPath, { force: true });
rmSync(hacsOutputPath, { force: true });

const tempRoot = await mkdtemp(join(tmpdir(), "ha-tv-pip-integration-"));
const manualRoot = join(tempRoot, "manual");
const manualTargetDir = join(manualRoot, "custom_components/ha_tv_pip");
const hacsRoot = join(tempRoot, "hacs");

try {
  const copyOptions = {
    recursive: true,
    filter: (source) => {
      const ignored = [".git", "node_modules", "dist", "__pycache__", ".DS_Store"];
      return !ignored.some((segment) => source.split(/[\\/]/).includes(segment));
    }
  };

  mkdirSync(join(manualRoot, "custom_components"), { recursive: true });
  cpSync(sourceDir, manualTargetDir, copyOptions);
  mkdirSync(hacsRoot, { recursive: true });
  cpSync(sourceDir, hacsRoot, copyOptions);

  const zip = spawnSync("zip", ["-r", outputPath, "custom_components/ha_tv_pip"], {
    cwd: manualRoot,
    stdio: "inherit"
  });

  if (zip.error) {
    throw new Error(`Failed to run zip: ${zip.error.message}`);
  }

  if (zip.status !== 0) {
    throw new Error(`zip exited with status ${zip.status}`);
  }

  const hacsZip = spawnSync("zip", ["-r", hacsOutputPath, "."], {
    cwd: hacsRoot,
    stdio: "inherit"
  });

  if (hacsZip.error) {
    throw new Error(`Failed to run zip: ${hacsZip.error.message}`);
  }

  if (hacsZip.status !== 0) {
    throw new Error(`zip exited with status ${hacsZip.status}`);
  }

  console.log(`Created ${outputPath}`);
  console.log(`Created ${hacsOutputPath}`);
} finally {
  await rm(tempRoot, { recursive: true, force: true });
}
