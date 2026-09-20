#!/usr/bin/env python3
"""Diagnose and safely repair known Codex browser-runtime regressions.

This utility deliberately operates on a narrow, discovered set of
``browser-service.mjs`` files.  It never reads browser profiles, cookies, or
credentials, and it never kills a process.  Repairs are exact, reversible
source transformations with a backup and a JavaScript syntax check.

The supported repairs address two observed classes of failure:

* an unbounded optional request-header policy lookup that prevents the browser
  bridge from becoming usable when the identity/policy service is unavailable;
* a browser-use download gate that turns an intended attachment download into
  ``ERR_BLOCKED_BY_CLIENT`` before the normal download adapter can observe it.

The download fallback is opt-in because it changes the bridge's handling of
unmanaged document downloads.  The request-header timeout repair is the
default repair when its exact pre-patch pattern is present.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


TOOL_SCHEMA = "labor-loop.browser-repair.v1"
MAX_SCAN_BYTES = 32 * 1024 * 1024
HEADER_MARKER = "labor-loop-browser-header-timeout-v1"
DOWNLOAD_MARKER = "labor-loop-browser-download-fallback-v1"
HEADER_POLICY = "codex_browser_use_agent_request_header"


class RepairError(RuntimeError):
    """A safe, actionable diagnosis or repair failure."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def default_roots() -> list[Path]:
    """Return narrowly scoped runtime roots without assuming a user name."""
    roots: list[Path] = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        roots.append(Path(local_app_data) / "OpenAI" / "Codex" / "runtimes" / "cua_node")
    app_data = os.environ.get("APPDATA")
    if app_data:
        roots.append(Path(app_data) / "OpenAI" / "Codex" / "runtimes" / "cua_node")
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        roots.append(Path(xdg_cache) / "codex-runtimes")
    home = Path.home()
    roots.extend(
        [
            home / ".cache" / "codex-runtimes",
            home / ".local" / "share" / "codex" / "runtimes" / "cua_node",
        ]
    )
    return dedupe_paths(roots)


def dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = path.expanduser().resolve(strict=False)
        key = os.path.normcase(str(resolved))
        if key not in seen:
            seen.add(key)
            result.append(resolved)
    return result


def discover_files(roots: Iterable[Path]) -> list[Path]:
    """Find only the known runtime service filenames beneath explicit roots."""
    files: list[Path] = []
    for root in dedupe_paths(roots):
        if not root.is_dir():
            continue
        patterns = ("*/bin/node_modules/**/browser-service.mjs", "bin/node_modules/**/browser-service.mjs")
        for pattern in patterns:
            for path in root.glob(pattern):
                if path.is_file() and not path.is_symlink():
                    files.append(path.resolve())
    return sorted(dedupe_paths(files), key=lambda item: str(item).lower())


def assert_safe_candidate(path: Path, roots: Iterable[Path]) -> None:
    resolved = path.expanduser().resolve(strict=True)
    if resolved.name != "browser-service.mjs":
        raise RepairError(f"refusing non-service file: {resolved}")
    if resolved.is_symlink():
        raise RepairError(f"refusing symlinked service file: {resolved}")
    root_strings = [str(root.resolve(strict=False)).lower() for root in roots]
    if not any(str(resolved).lower().startswith(root + os.sep) for root in root_strings):
        raise RepairError(f"service file is outside a discovered runtime root: {resolved}")
    if resolved.stat().st_size > MAX_SCAN_BYTES:
        raise RepairError(f"service file exceeds the scan limit: {resolved}")


def read_text(path: Path) -> str:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise RepairError(f"cannot read {path}: {exc}") from exc
    if len(payload) > MAX_SCAN_BYTES:
        raise RepairError(f"service file exceeds the scan limit: {path}")
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RepairError(f"service file is not UTF-8: {path}") from exc


def header_status(text: str) -> str:
    if HEADER_MARKER in text or "Promise.race([" in header_region(text):
        return "bounded-or-already-repaired"
    if HEADER_POLICY not in text:
        return "not-applicable"
    if re.search(
        r"\.then\(\(\)=>[^)]*\([\"']" + re.escape(HEADER_POLICY),
        header_region(text),
    ):
        return "unbounded-policy-lookup"
    return "unknown-layout"


def header_region(text: str) -> str:
    marker = text.find(HEADER_POLICY)
    if marker < 0:
        return text[:20000]
    return text[max(0, marker - 1800) : marker + 500]


def download_status(text: str) -> str:
    if DOWNLOAD_MARKER in text:
        return "already-repaired"
    old = "if(!o){await this.documentResponses.failResponse(r,i);return}"
    if old in text:
        return "fail-closed-download-gate"
    if "documentResponses.continueResponse(r,i)" in text:
        return "bounded-or-already-repaired"
    return "not-applicable"


def node_for(path: Path) -> Path | None:
    # Runtime layout: <runtime>/bin/node_modules/.../browser-service.mjs.
    candidate = path.parents[3] / ("node.exe" if os.name == "nt" else "node")
    if candidate.is_file():
        return candidate
    return shutil.which("node") and Path(str(shutil.which("node")))


def syntax_check(path: Path) -> dict[str, Any]:
    node = node_for(path)
    if node is None:
        return {"status": "not-run", "reason": "node executable not found"}
    result = subprocess.run(
        [str(node), "--check", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RepairError(
            f"JavaScript syntax check failed for {path}: "
            f"{(result.stderr or result.stdout).strip()}"
        )
    return {"status": "passed", "node": str(node)}


def diagnose_path(path: Path, roots: Iterable[Path]) -> dict[str, Any]:
    assert_safe_candidate(path, roots)
    payload = path.read_bytes()
    text = read_text(path)
    return {
        "path": str(path),
        "sha256": sha256_bytes(payload),
        "bytes": len(payload),
        "header_policy": header_status(text),
        "download_gate": download_status(text),
        "repairable": header_status(text) == "unbounded-policy-lookup"
        or download_status(text) == "fail-closed-download-gate",
    }


def diagnose(roots: Iterable[Path], explicit_files: Iterable[Path] = ()) -> dict[str, Any]:
    root_list = dedupe_paths(roots)
    files = dedupe_paths(explicit_files) or discover_files(root_list)
    entries = [diagnose_path(path, root_list) for path in files]
    return {
        "schema_version": TOOL_SCHEMA,
        "roots": [str(root) for root in root_list],
        "files": entries,
        "recommended": [
            "run repair --apply for an exact request-header timeout match",
            "run repair --apply --download-fallback only for a confirmed blocked attachment download",
            "restart or recreate the browser-control runtime after a repair",
            "re-run diagnose and a harmless browser smoke test before submitting work",
        ],
    }


def patch_text(text: str, *, download_fallback: bool) -> tuple[str, list[str]]:
    changed: list[str] = []
    header_old_patterns = (
        r"return await (Rm|Im)\.then\(\(\)=>[A-Za-z0-9_$]+\([\"']"
        + re.escape(HEADER_POLICY)
        + r"[\"']\)\);",
    )
    if HEADER_MARKER not in text and "Promise.race([" not in header_region(text):
        match = None
        for pattern in header_old_patterns:
            match = re.search(pattern, text)
            if match:
                break
        if match:
            original = match.group(0)
            promise_expression = original[len("return await ") :].rstrip(";")
            replacement = (
                f"/* {HEADER_MARKER} */ return await Promise.race(["
                f"{promise_expression},"
                "new Promise(e=>setTimeout(()=>e(!1),2500))]);"
            )
            text = text[: match.start()] + replacement + text[match.end() :]
            changed.append("request-header-policy-timeout")

    if download_fallback and DOWNLOAD_MARKER not in text:
        old = "if(!o){await this.documentResponses.failResponse(r,i);return}"
        if text.count(old) == 1:
            text = text.replace(
                old,
                f"/* {DOWNLOAD_MARKER} */ if(!o){{await this.documentResponses.continueResponse(r,i);return}}",
            )
            changed.append("download-fallback")
    return text, changed


def atomic_write(path: Path, payload: bytes) -> None:
    """Replace a file through a same-directory temporary file."""
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.labor-loop-", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def apply_repairs(
    roots: Iterable[Path],
    explicit_files: Iterable[Path] = (),
    *,
    download_fallback: bool,
) -> dict[str, Any]:
    root_list = dedupe_paths(roots)
    files = dedupe_paths(explicit_files) or discover_files(root_list)
    results: list[dict[str, Any]] = []
    stamp = utc_stamp()
    for path in files:
        assert_safe_candidate(path, root_list)
        before = path.read_bytes()
        old_text = before.decode("utf-8")
        new_text, changed = patch_text(old_text, download_fallback=download_fallback)
        if not changed:
            results.append(
                {
                    "path": str(path),
                    "status": "unchanged",
                    "sha256": sha256_bytes(before),
                    "header_policy": header_status(old_text),
                    "download_gate": download_status(old_text),
                }
            )
            continue
        backup = path.with_name(f"{path.name}.bak-{TOOL_SCHEMA}-{stamp}")
        if backup.exists():
            raise RepairError(f"refusing to overwrite an existing backup: {backup}")
        shutil.copy2(path, backup)
        atomic_write(path, new_text.encode("utf-8"))
        try:
            syntax = syntax_check(path)
        except Exception:
            atomic_write(path, before)
            backup.unlink(missing_ok=True)
            raise
        results.append(
            {
                "path": str(path),
                "status": "patched",
                "changes": changed,
                "backup": str(backup),
                "before_sha256": sha256_bytes(before),
                "after_sha256": sha256_bytes(path.read_bytes()),
                "syntax": syntax,
            }
        )
    return {
        "schema_version": TOOL_SCHEMA,
        "download_fallback_requested": download_fallback,
        "files": results,
        "next": "restart or recreate the browser-control runtime, then run diagnose and a smoke test",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose and repair known Codex browser bridge regressions")
    parser.add_argument("--root", action="append", type=Path, help="explicit runtime root; repeatable")
    parser.add_argument("--file", action="append", type=Path, help="explicit browser-service.mjs; repeatable")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("diagnose")
    repair = sub.add_parser("repair")
    repair.add_argument("--apply", action="store_true", help="write exact repairs and create backups")
    repair.add_argument(
        "--download-fallback",
        action="store_true",
        help="also allow unmanaged attachment responses to continue to Chrome",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    roots = dedupe_paths(args.root or default_roots())
    files = dedupe_paths(args.file or [])
    try:
        if args.command == "diagnose":
            result = diagnose(roots, files)
        elif not args.apply:
            raise RepairError("repair is read-only unless --apply is supplied")
        else:
            result = apply_repairs(roots, files, download_fallback=args.download_fallback)
    except (OSError, RepairError, UnicodeError) as exc:
        print(json.dumps({"schema_version": TOOL_SCHEMA, "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
