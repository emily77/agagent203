from __future__ import annotations

import base64
import hashlib
import importlib.util
import shutil
import sys
import tarfile
from pathlib import Path

from fastapi import Request

BASE_DIR = Path(__file__).resolve().parent
BUNDLE_PARTS_DIR = BASE_DIR / "bundles"
BUNDLE_PART_GLOB = "jls-render-source.part*.b64"
BUNDLE_SHA256 = "9b79bac5d58bc1b79b272a9825f76158ae7f5c523471af3f414266360b9d00b7"
BUNDLE_CACHE_DIR = BASE_DIR / "_bundle_cache"
BUNDLE_ARCHIVE_PATH = BUNDLE_CACHE_DIR / "school-platform.tar.xz"
BUNDLE_DIR = BASE_DIR / "_bundle_src"
BUNDLE_MARKER_PATH = BUNDLE_DIR / ".bundle_sha256"
APP_MODULE_PATH = BUNDLE_DIR / "api.py"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _materialize_archive() -> None:
    BUNDLE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    parts = sorted(BUNDLE_PARTS_DIR.glob(BUNDLE_PART_GLOB))
    if not parts:
        raise RuntimeError(f"No bundle parts found in {BUNDLE_PARTS_DIR}")
    encoded = "".join(part.read_text(encoding="utf-8").strip() for part in parts)
    BUNDLE_ARCHIVE_PATH.write_bytes(base64.b64decode(encoded))


def _ensure_bundle() -> None:
    if APP_MODULE_PATH.exists() and BUNDLE_MARKER_PATH.exists() and BUNDLE_MARKER_PATH.read_text(encoding="utf-8").strip() == BUNDLE_SHA256:
        if str(BUNDLE_DIR) not in sys.path:
            sys.path.insert(0, str(BUNDLE_DIR))
        return

    _materialize_archive()
    actual_sha = _sha256(BUNDLE_ARCHIVE_PATH)
    if actual_sha != BUNDLE_SHA256:
        raise RuntimeError(f"Bundle SHA mismatch: expected {BUNDLE_SHA256}, got {actual_sha}")

    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    with tarfile.open(BUNDLE_ARCHIVE_PATH, mode="r:xz") as archive:
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


@app.middleware("http")
async def ensure_utf8_json_responses(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/school-platform/api"):
        content_type = response.headers.get("content-type", "")
        if content_type.lower().startswith("application/json") and "charset=" not in content_type.lower():
            response.headers["content-type"] = "application/json; charset=utf-8"
    return response
