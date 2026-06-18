"""Tests for Home Assistant integration release packaging."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

REPO_ROOT = Path(__file__).parents[2]


def test_integration_release_archives_have_expected_install_layout(
    tmp_path: Path,
) -> None:
    """Protect the HACS and manual install zip path contracts."""

    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required to run the integration packaging script")
    if shutil.which("zip") is None:
        pytest.skip("zip is required to run the integration packaging script")

    package_root = tmp_path / "repo"
    package_root.mkdir()
    shutil.copy2(REPO_ROOT / "package.json", package_root / "package.json")
    shutil.copytree(REPO_ROOT / "scripts", package_root / "scripts")
    shutil.copytree(REPO_ROOT / "custom_components", package_root / "custom_components")

    result = subprocess.run(
        [node, "scripts/package-integration.mjs"],
        cwd=package_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout

    version = json.loads((package_root / "package.json").read_text())["version"]
    manual_zip = package_root / "dist" / f"ha-tv-pip-integration-v{version}.zip"
    hacs_zip = package_root / "dist" / "ha-tv-pip-integration.zip"

    assert manual_zip.exists()
    assert hacs_zip.exists()

    manual_names = _zip_names(manual_zip)
    hacs_names = _zip_names(hacs_zip)

    assert "custom_components/ha_tv_pip/manifest.json" in manual_names
    assert "custom_components/ha_tv_pip/config_flow.py" in manual_names
    assert "manifest.json" not in manual_names
    assert not any(
        name.startswith("custom_components/ha_tv_pip/custom_components/")
        for name in manual_names
    )

    assert "manifest.json" in hacs_names
    assert "config_flow.py" in hacs_names
    assert "README.md" in hacs_names
    assert not any(name.startswith("custom_components/") for name in hacs_names)

    for names in (manual_names, hacs_names):
        assert not any("__pycache__" in name for name in names)
        assert not any(name.startswith("dist/") for name in names)
        assert not any(name.startswith(".git/") for name in names)
        assert not any(name.startswith("node_modules/") for name in names)


def _zip_names(path: Path) -> set[str]:
    with ZipFile(path) as archive:
        return set(archive.namelist())
