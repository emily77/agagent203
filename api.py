from __future__ import annotations

import hashlib
import importlib.util
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BUNDLE_URL = "https://tmpfiles.org/dl/wDwZLjNEF5ON/japan-life-language-school-os.clean.zip"
BUNDLE_SHA256 = "b64765b4955cc49db52d2fff32b5ab1c7db9a72a6a083815f275e9a27e1d6fff"
BUNDLE_CACHE_DIR = BASE_DIR / "_bundle_cache"
BUNDLE_ARCHIVE_PATH = BUNDLE_CACHE_DIR / "school-platform.zip"
BUNDLE_DIR = BASE_DIR / "_bundle_src"
BUNDLE_MARKER_PATH = BUNDLE_DIR / ".bundle_sha256"
APP_MODULE_PATH = BUNDLE_DIR / "api.py"


def _download_bundle() -> None:
    BUNDLE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(BUNDLE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=300) as response, BUNDLE_ARCHIVE_PATH.open("wb") as target:
        shutil.copyfileobj(response, target)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_bundle() -> None:
    if APP_MODULE_PATH.exists() and BUNDLE_MARKER_PATH.exists() and BUNDLE_MARKER_PATH.read_text(encoding="utf-8").strip() == BUNDLE_SHA256:
        if str(BUNDLE_DIR) not in sys.path:
            sys.path.insert(0, str(BUNDLE_DIR))
        return

    _download_bundle()
    actual_sha = _sha256(BUNDLE_ARCHIVE_PATH)
    if actual_sha != BUNDLE_SHA256:
        raise RuntimeError(f"Bundle SHA mismatch: expected {BUNDLE_SHA256}, got {actual_sha}")

    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BUNDLE_ARCHIVE_PATH) as archive:
        archive.extractall(BUNDLE_DIR)
    BUNDLE_MARKER_PATH.write_text(BUNDLE_SHA256, encoding="utf-8")

    if str(BUNDLE_DIR) not in sys.path:
        sys.path.insert(0, str(BUNDLE_DIR))


def _load_app():
    _ensure_bundle()
    spec = importlib.util.spec_from_file_location("school_platform_bundle_api", APP_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load app module from {APP_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.app


app = _load_app()
