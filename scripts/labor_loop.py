#!/usr/bin/env python3
"""Deterministic local state, packet, artifact, and Git integration core.

The browser/ChatGPT phase is intentionally outside this module.  Codex uses the
supported browser adapter and records its observations through this CLI.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


SCHEMA = "labor-loop.v1"
PROJECT_SCHEMA = "labor-loop.project.v1"
JOB_SCHEMA = "labor-loop.job.v1"
STATE_SCHEMA = "labor-loop.state.v1"

STATUSES = (
    "CREATED",
    "PACKAGED",
    "SUBMITTED",
    "WORKER_RUNNING",
    "WORKER_COMPLETE",
    "ARTIFACT_DISCOVERED",
    "ARTIFACT_DOWNLOADED",
    "VALIDATED",
    "INTEGRATING",
    "TESTING",
    "REVIEWING",
    "COMPLETE",
    "NEEDS_FOLLOWUP",
    "BLOCKED",
    "FAILED",
    "ABORTED",
)
TERMINAL = {"COMPLETE", "NEEDS_FOLLOWUP", "BLOCKED", "FAILED", "ABORTED"}
ACTIVE = set(STATUSES) - TERMINAL

TRANSITIONS: dict[str, set[str]] = {
    "CREATED": {"PACKAGED", "FAILED", "ABORTED"},
    "PACKAGED": {"SUBMITTED", "FAILED", "ABORTED"},
    "SUBMITTED": {
        "WORKER_RUNNING",
        "WORKER_COMPLETE",
        "NEEDS_FOLLOWUP",
        "BLOCKED",
        "FAILED",
        "ABORTED",
    },
    "WORKER_RUNNING": {
        "WORKER_RUNNING",
        "WORKER_COMPLETE",
        "ARTIFACT_DISCOVERED",
        "NEEDS_FOLLOWUP",
        "BLOCKED",
        "FAILED",
        "ABORTED",
    },
    "WORKER_COMPLETE": {
        "ARTIFACT_DISCOVERED",
        "ARTIFACT_DOWNLOADED",
        "NEEDS_FOLLOWUP",
        "BLOCKED",
        "FAILED",
        "ABORTED",
    },
    "ARTIFACT_DISCOVERED": {"ARTIFACT_DOWNLOADED", "FAILED", "BLOCKED", "ABORTED"},
    "ARTIFACT_DOWNLOADED": {"VALIDATED", "FAILED", "BLOCKED", "ABORTED"},
    "VALIDATED": {"INTEGRATING", "FAILED", "ABORTED"},
    "INTEGRATING": {"INTEGRATING", "TESTING", "FAILED", "ABORTED"},
    "TESTING": {"TESTING", "REVIEWING", "FAILED", "ABORTED"},
    "REVIEWING": {"COMPLETE", "NEEDS_FOLLOWUP", "BLOCKED", "FAILED", "ABORTED"},
    "COMPLETE": set(),
    "NEEDS_FOLLOWUP": {"PACKAGED", "ABORTED"},
    "BLOCKED": {"PACKAGED", "ABORTED"},
    "FAILED": {"PACKAGED", "TESTING", "ABORTED"},
    "ABORTED": set(),
}

DEFAULT_EXCLUDES = [
    ".git/**",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*credential*",
    "*secret*",
    "*token*",
    "*cookie*",
    "*.pcap",
    "*.pcapng",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "target/**",
    "node_modules/**",
    ".venv/**",
    "__pycache__/**",
    "*.zip",
]
DEFAULT_INCLUDE = [
    "README.md",
    "README.rst",
    "LICENSE",
    "SKILL.md",
    "agents",
    "scripts",
    "references",
    "Cargo.toml",
    "Cargo.lock",
    "pyproject.toml",
    "src",
    "tests",
    "docs",
    "docs/implementation/CURRENT.md",
    "docs/product",
]

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|secret[_-]?key|client[_-]?secret)\b\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"
    ),
    re.compile(r"(?i)\b(?:password|passwd)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
)


class LaborError(RuntimeError):
    """A user-actionable validation or state error."""


def now_iso() -> str:
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    )


def json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(
        path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LaborError(f"missing JSON file: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise LaborError(f"invalid JSON file: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LaborError(f"JSON root must be an object: {path}")
    return value


def safe_identifier(value: str, label: str = "identifier") -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", value):
        raise LaborError(f"invalid {label}: {value!r}")
    return value


def default_state_root() -> Path:
    configured = os.environ.get("LABOR_LOOP_STATE_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return (Path(local_app_data) / "Codex" / "labor-loop").resolve()
    xdg = os.environ.get("XDG_STATE_HOME")
    if xdg:
        return (Path(xdg) / "codex" / "labor-loop").resolve()
    return (Path(tempfile.gettempdir()) / "Codex" / "labor-loop").resolve()


def decode_output(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def run_command(
    argv: Sequence[str], *, cwd: Path | None = None, timeout: int | None = None
) -> subprocess.CompletedProcess[bytes]:
    if not argv or any(not isinstance(item, str) or not item for item in argv):
        raise LaborError(f"command must be a nonempty argv array: {argv!r}")
    try:
        return subprocess.run(
            list(argv),
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise LaborError(f"command not found: {argv[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise LaborError(
            f"command timed out after {timeout}s: {' '.join(argv)}"
        ) from exc


def run_git(
    repo: Path, args: Sequence[str], *, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    result = run_command(["git", "-C", str(repo), *args])
    if check and result.returncode != 0:
        raise LaborError(
            f"git {' '.join(args)} failed: {decode_output(result.stderr).strip()[-2000:]}"
        )
    return result


def git_text(repo: Path, args: Sequence[str], *, check: bool = True) -> str:
    result = run_git(repo, args, check=check)
    if check and result.returncode != 0:
        return ""
    return decode_output(result.stdout)


def repository_root(path: Path) -> Path:
    candidate = path.expanduser().resolve()
    if not candidate.exists():
        raise LaborError(f"repository path does not exist: {candidate}")
    root = git_text(candidate, ["rev-parse", "--show-toplevel"]).strip()
    if not root:
        raise LaborError(f"not a Git repository: {candidate}")
    return Path(root).resolve()


def repository_info(path: Path) -> dict[str, str | None]:
    root = repository_root(path)
    head = git_text(root, ["rev-parse", "HEAD"]).strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", head):
        raise LaborError(f"could not resolve a full Git base commit for {root}")
    branch_result = run_git(
        root, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False
    )
    branch = decode_output(branch_result.stdout).strip() or "main"
    remote_result = run_git(root, ["remote", "get-url", "origin"], check=False)
    remote = decode_output(remote_result.stdout).strip() or None
    changed = git_text(root, ["diff", "--name-status", "--"]).splitlines()
    return {
        "root": str(root),
        "head": head,
        "branch": branch,
        "remote": remote,
        "changed": changed,
    }


def normalize_remote(value: Any) -> str | None:
    if isinstance(value, Mapping):
        value = value.get("url")
    if not isinstance(value, str) or not value:
        return None
    return value.rstrip("/").removesuffix(".git").lower()


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def scrub_local_paths(text: str, repo: Path) -> str:
    output = text.replace(str(repo), "<repository>")
    try:
        output = output.replace(str(Path.home()), "<user-home>")
    except RuntimeError:
        pass
    return output


def is_sensitive_path(path: str, excludes: Iterable[str]) -> bool:
    normalized = path.replace("\\", "/")
    if any(
        fnmatch.fnmatch(normalized, pattern)
        or fnmatch.fnmatch(normalized.lower(), pattern.lower())
        for pattern in excludes
    ):
        return True
    basename = normalized.rsplit("/", 1)[-1].lower()
    return basename in {
        ".env",
        "id_rsa",
        "id_ed25519",
        "credentials.json",
        "cookies.json",
    }


def safe_relative(path: str) -> str:
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if not normalized or pure.is_absolute() or re.match(r"^[A-Za-z]:", normalized):
        raise LaborError(f"unsafe relative path: {path!r}")
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise LaborError(f"unsafe relative path: {path!r}")
    return pure.as_posix()


def process_is_alive(pid: int) -> bool:
    """Check a lock owner's process without a potentially blocking Windows kill probe."""
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(
            process_query_limited_information,
            False,
            pid,
        )
        if handle:
            kernel32.CloseHandle(handle)
            return True
        # Access denied means the process exists but cannot be queried.
        return ctypes.get_last_error() == 5
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


class StoreLock:
    def __init__(self, path: Path):
        self.path = path
        self.acquired = False

    def __enter__(self) -> "StoreLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"pid": os.getpid(), "created_at": now_iso()})
        for attempt in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError as exc:
                owner_text = self.path.read_text(encoding="utf-8", errors="replace")[
                    :500
                ]
                try:
                    owner = json.loads(owner_text)
                    owner_pid = int(owner.get("pid", -1))
                except (ValueError, TypeError, json.JSONDecodeError) as parse_error:
                    raise LaborError(
                        f"project state lock metadata is incomplete: {owner_text}"
                    ) from parse_error
                owner_alive = process_is_alive(owner_pid)
                if not owner_alive and attempt == 0:
                    try:
                        self.path.unlink()
                    except FileNotFoundError:
                        continue
                    continue
                raise LaborError(
                    f"project state is locked by another process: {owner_text}"
                ) from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        self.acquired = True
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if self.acquired:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass


class Store:
    def __init__(self, root: Path, project_id: str):
        self.root = root.expanduser().resolve()
        self.project_id = safe_identifier(project_id, "project_id")
        self.project_dir = self.root / "projects" / self.project_id

    @property
    def project_path(self) -> Path:
        return self.project_dir / "project.json"

    @property
    def state_path(self) -> Path:
        return self.project_dir / "state.json"

    @property
    def timeline_path(self) -> Path:
        return self.project_dir / "timeline.jsonl"

    @property
    def lock_path(self) -> Path:
        return self.project_dir / ".lock"

    def ensure(self) -> None:
        self.project_dir.mkdir(parents=True, exist_ok=True)
        (self.project_dir / "jobs").mkdir(exist_ok=True)

    def lock(self) -> StoreLock:
        return StoreLock(self.lock_path)

    def job_dir(self, job_id: str) -> Path:
        safe_identifier(job_id, "job_id")
        return self.project_dir / "jobs" / job_id

    def load_project(self) -> dict[str, Any]:
        self.ensure()
        value = read_json(self.project_path)
        if value.get("schema_version") != PROJECT_SCHEMA:
            raise LaborError(
                f"unsupported project config schema: {value.get('schema_version')!r}"
            )
        if value.get("project_id") != self.project_id:
            raise LaborError("project config identity does not match --project-id")
        return value

    def save_project(self, value: dict[str, Any]) -> None:
        if value.get("schema_version") != PROJECT_SCHEMA:
            raise LaborError("refusing to write an unknown project schema")
        atomic_write_json(self.project_path, value)

    def load_state(self, job_id: str | None = None) -> dict[str, Any]:
        path = self.state_path
        if job_id:
            path = self.job_dir(job_id) / "state.json"
        value = read_json(path)
        if value.get("schema_version") != STATE_SCHEMA:
            raise LaborError(
                f"unsupported state schema: {value.get('schema_version')!r}"
            )
        if value.get("project_id") != self.project_id:
            raise LaborError("state project identity does not match --project-id")
        return value

    def save_state(self, value: dict[str, Any]) -> None:
        if value.get("schema_version") != STATE_SCHEMA:
            raise LaborError("refusing to write an unknown state schema")
        job_id = safe_identifier(str(value.get("job_id")), "job_id")
        job_dir = self.job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        atomic_write_json(job_dir / "state.json", value)
        atomic_write_json(self.state_path, value)

    def append_event(self, value: Mapping[str, Any]) -> None:
        self.timeline_path.parent.mkdir(parents=True, exist_ok=True)
        with self.timeline_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(
                json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n"
            )


def deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = deep_merge(dict(result[key]), value)
        else:
            result[key] = value
    return result


def default_project_config(project_id: str, info: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": PROJECT_SCHEMA,
        "project_id": project_id,
        "repository": {
            "path": info["root"],
            "url": info["remote"],
            "default_branch": info["branch"],
        },
        "worker": {
            "provider": "chatgpt-chat",
            "thread_url": None,
            "thread_id": None,
            "model_mode": "configured",
            "browser": "chrome",
            "require_confirmation": True,
        },
        "packet": {
            "include_paths": list(DEFAULT_INCLUDE),
            "exclude_globs": list(DEFAULT_EXCLUDES),
            "max_files": 250,
            "max_file_bytes": 1024 * 1024,
            "max_total_bytes": 12 * 1024 * 1024,
        },
        "artifacts": {
            "max_zip_bytes": 50 * 1024 * 1024,
            "max_member_bytes": 10 * 1024 * 1024,
            "max_total_uncompressed_bytes": 100 * 1024 * 1024,
            "max_members": 1000,
        },
        "validation": {"commands": [], "timeout_seconds": 1800},
        "loop": {
            "max_jobs": 3,
            "max_elapsed_seconds": 21600,
            "max_consecutive_failures": 2,
        },
        "integration": {"worktree_root": None},
    }


def validate_project_config(value: Mapping[str, Any], project_id: str) -> None:
    if (
        value.get("schema_version") != PROJECT_SCHEMA
        or value.get("project_id") != project_id
    ):
        raise LaborError("invalid project config identity or schema")
    worker = value.get("worker")
    if not isinstance(worker, Mapping) or worker.get("provider") != "chatgpt-chat":
        raise LaborError(
            "worker.provider must remain chatgpt-chat; API workers are not the default loop"
        )
    packet = value.get("packet")
    if not isinstance(packet, Mapping):
        raise LaborError("project.packet must be an object")
    for key in ("max_files", "max_file_bytes", "max_total_bytes"):
        if not isinstance(packet.get(key), int) or packet[key] <= 0:
            raise LaborError(f"packet.{key} must be a positive integer")
    artifacts = value.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise LaborError("project.artifacts must be an object")
    for key in (
        "max_zip_bytes",
        "max_member_bytes",
        "max_total_uncompressed_bytes",
        "max_members",
    ):
        if not isinstance(artifacts.get(key), int) or artifacts[key] <= 0:
            raise LaborError(f"artifacts.{key} must be a positive integer")


def project_and_store(args: argparse.Namespace) -> tuple[Store, dict[str, Any]]:
    store = Store(
        Path(args.state_root) if args.state_root else default_state_root(),
        args.project_id,
    )
    project = store.load_project()
    validate_project_config(project, args.project_id)
    return store, project


def transition(
    store: Store, state: dict[str, Any], target: str, note: str, **extra: Any
) -> dict[str, Any]:
    current = str(state.get("status"))
    if target not in STATUSES:
        raise LaborError(f"unknown status: {target}")
    if target != current and target not in TRANSITIONS.get(current, set()):
        raise LaborError(f"invalid state transition {current} -> {target}")
    state["status"] = target
    state["updated_at"] = now_iso()
    if note:
        state["last_note"] = note
    state.update(extra)
    store.save_state(state)
    store.append_event(
        {
            "schema_version": SCHEMA,
            "at": state["updated_at"],
            "project_id": state["project_id"],
            "job_id": state["job_id"],
            "from": current,
            "to": target,
            "note": note,
            "extra": extra,
        }
    )
    return state


def active_state(store: Store) -> dict[str, Any] | None:
    if not store.state_path.exists():
        return None
    value = store.load_state()
    return value if value.get("status") in ACTIVE else None


def tracked_files(repo: Path, base: str, specs: Sequence[str]) -> list[str]:
    found: set[str] = set()
    for spec in specs:
        if not spec or Path(spec).is_absolute() or "\x00" in spec:
            raise LaborError(f"invalid packet include path: {spec!r}")
        result = run_git(repo, ["ls-tree", "-r", "-z", "--name-only", base, "--", spec])
        for raw in result.stdout.split(b"\x00"):
            if raw:
                found.add(safe_relative(decode_output(raw)))
    return sorted(found)


def read_git_file(repo: Path, base: str, relative: str) -> bytes:
    result = run_git(repo, ["show", f"{base}:{relative}"])
    return result.stdout


def make_packet_zip(job_dir: Path, files: Mapping[str, bytes]) -> Path:
    packet_path = job_dir / "worker-packet.zip"
    with zipfile.ZipFile(packet_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files):
            safe_name = safe_relative(name)
            info = zipfile.ZipInfo(safe_name)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name])
    return packet_path


def worker_return_contract() -> str:
    return """Return exactly one ZIP with these root entries:

manifest.json
START_HERE.md
SUMMARY.md
INTEGRATION.md
REMAINING.md
VALIDATION.md
changes.patch
files/<optional complete changed files>
evidence/<optional supporting evidence>

manifest.json must include this job_id, base_commit, and repository. changes.patch
is the canonical integration representation. Be honest about partial work and
unresolved items; do not claim tests that were not actually run.

Artifact delivery is part of acceptance. Prefer attaching the ZIP directly to
this ChatGPT response so it appears as a downloadable attachment. If a direct
attachment is unavailable, provide a genuinely public HTTPS URL that works
without login, cookies, bearer tokens, an internal hostname, a private-network
address, a localhost address, or a session-bound/backend/API endpoint. Do not
return a file:// path or ask the integrator to fetch an inaccessible backend
link. If neither direct attachment nor a public URL is possible, report
delivery as blocked and do not claim that the artifact was delivered.
"""


def recent_integration_feedback_contract() -> str:
    """Require every worker round to review recent and relevant implementation."""
    return """## Recent integration feedback (required)

Before changing code, review the most recent accepted integration or baseline
commit named by this request, plus any other recent or relevant implemented
mechanism that the requested slice touches or depends on. Compare those
surfaces with the repository's stated intent and acceptance contract. In the
returned SUMMARY.md and REMAINING.md, record:

- any intent mismatch, regression risk, missing test, documentation gap, or
  integration repair you found;
- which findings are in scope for this round and which remain deferred; and
- why the new work preserves the accepted behavior and does not duplicate an
  existing mechanism. Name the reviewed surfaces, not just the new files.

Only repair a prior finding when the evidence is direct, the change is
bounded, and it does not silently expand the requested scope. A clean review
is valid evidence too: state that you checked and found no actionable gap.
"""


def artifact_delivery_followup(
    *, job_id: str, base_commit: str, repository_url: str | None, reason: str
) -> str:
    """Build a safe, reusable recovery request for a failed artifact delivery."""
    repository_line = f"Repository: {repository_url}\n" if repository_url else ""
    return f"""# Artifact delivery recovery

The implementation response for job `{job_id}` did not produce a usable local
artifact. The integration owner observed this delivery problem:

> {reason}

Please repackage the completed work and return the same integration contract.
The pinned base commit is `{base_commit}`.
{repository_line}

{recent_integration_feedback_contract()}
Delivery is part of acceptance. Use one of these methods, in priority order:

1. Attach the ZIP directly to this ChatGPT response so it is visibly
   downloadable.
2. If direct attachment is unavailable, provide a genuinely public HTTPS URL
   that can be opened without login, cookies, bearer tokens, an internal
   hostname, a private-network address, a localhost address, or a
   session-bound/backend/API endpoint.

Do not return a `file://` path, localhost URL, internal/backend/API URL, or a
link that only works inside your execution environment. Do not claim delivery
until the attachment or public URL is actually present. If neither method is
possible, state that artifact delivery is blocked and explain why. Preserve
the required ZIP root layout, `job_id`, `base_commit`, `repository`, and
`changes.patch` contract from the original request.
"""


def create_job(
    store: Store,
    project: dict[str, Any],
    request_path: Path,
    *,
    base: str | None,
    parent_job_id: str | None,
) -> dict[str, Any]:
    info = repository_info(Path(project["repository"]["path"]))
    repo = Path(str(info["root"]))
    base_commit = base or str(info["head"])
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/@-]{0,199}", base_commit):
        raise LaborError(f"unsafe base ref: {base_commit!r}")
    resolved_base = git_text(
        repo, ["rev-parse", "--verify", f"{base_commit}^{{commit}}"]
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", resolved_base):
        raise LaborError(f"invalid base commit: {base_commit}")
    if (
        not request_path.exists()
        or not request_path.is_file()
        or request_path.is_symlink()
    ):
        raise LaborError(f"request file must be a regular file: {request_path}")
    request_raw = request_path.read_bytes()
    if len(request_raw) > 2 * 1024 * 1024:
        raise LaborError("request file exceeds 2 MiB")
    request_text = request_raw.decode("utf-8")
    if contains_secret(request_text):
        raise LaborError("request contains a likely secret; remove it before packaging")
    request_text = scrub_local_paths(request_text, repo)

    if active_state(store):
        current = store.load_state()
        raise LaborError(
            f"project already has active job {current['job_id']} in {current['status']}"
        )

    packet_cfg = project["packet"]
    specs = packet_cfg.get("include_paths") or DEFAULT_INCLUDE
    excludes = packet_cfg.get("exclude_globs") or DEFAULT_EXCLUDES
    selected: dict[str, bytes] = {}
    omitted: list[dict[str, str]] = []
    total = 0
    candidates = tracked_files(repo, resolved_base, [str(item) for item in specs])
    for relative in candidates:
        if is_sensitive_path(relative, [str(item) for item in excludes]):
            omitted.append({"path": relative, "reason": "sensitive-or-excluded-path"})
            continue
        if len(selected) >= int(packet_cfg["max_files"]):
            omitted.append({"path": relative, "reason": "max-files"})
            continue
        content = read_git_file(repo, resolved_base, relative)
        if len(content) > int(packet_cfg["max_file_bytes"]):
            omitted.append({"path": relative, "reason": "max-file-bytes"})
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            omitted.append({"path": relative, "reason": "binary-context"})
            continue
        if contains_secret(text):
            omitted.append({"path": relative, "reason": "likely-secret-content"})
            continue
        if total + len(content) > int(packet_cfg["max_total_bytes"]):
            omitted.append({"path": relative, "reason": "max-total-bytes"})
            continue
        selected[relative] = scrub_local_paths(text, repo).encode("utf-8")
        total += len(content)

    job_id = f"LL-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    job_dir = store.job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=False)
    context_files: dict[str, bytes] = {}
    for relative, content in selected.items():
        context_files[f"context/{relative}"] = content
        target = job_dir / "context" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_bytes(target, content)

    repository_url = project["repository"].get("url")
    safe_job = {
        "schema_version": JOB_SCHEMA,
        "job_id": job_id,
        "project_id": store.project_id,
        "repository": {
            "url": repository_url,
            "base_commit": resolved_base,
            "branch": info["branch"],
        },
        "worker": {
            "provider": "chatgpt-chat",
            "model_mode": project["worker"].get("model_mode", "configured"),
        },
        "request": {
            "path": "REQUEST.md",
            "sha256": sha256_bytes(request_text.encode("utf-8")),
        },
        "context": {
            "files": sorted(selected),
            "omitted": omitted,
            "total_bytes": total,
        },
        "scope": {"local_changes_excluded": info["changed"]},
        "return_contract": worker_return_contract(),
        "artifact_delivery": {
            "schema_version": "labor-loop.artifact-delivery.v1",
            "preferred": "direct-attachment",
            "fallback": "public-https-url",
            "backend-or-session-links": "rejected",
        },
        "parent_job_id": parent_job_id,
    }
    request_out = (
        "# Labor-loop worker request\n\n"
        + request_text.rstrip()
        + "\n\n"
        + recent_integration_feedback_contract()
        + "\n\n## Machine return contract\n\n"
        + worker_return_contract()
    )
    context_out = (
        "# Selected context\n\n"
        + json.dumps(
            {
                "job_id": job_id,
                "base_commit": resolved_base,
                "repository_url": repository_url,
                "selected_files": sorted(selected),
                "omitted": omitted,
                "excluded_local_changes": info["changed"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n\nThe files under context/ are committed snapshots from the pinned base.\n"
    )
    start_out = "# Start here\n\nRead REQUEST.md, then CONTEXT.md and the files under context/. Implement the scoped task and return one ZIP matching the contract.\n"
    atomic_write_json(job_dir / "job.json", safe_job)
    atomic_write_text(job_dir / "REQUEST.md", request_out)
    atomic_write_text(job_dir / "CONTEXT.md", context_out)
    atomic_write_text(job_dir / "START_HERE.md", start_out)
    packet_files = {
        "job.json": json_bytes(safe_job) + b"\n",
        "REQUEST.md": request_out.encode("utf-8"),
        "CONTEXT.md": context_out.encode("utf-8"),
        "START_HERE.md": start_out.encode("utf-8"),
        **context_files,
    }
    packet_path = make_packet_zip(job_dir, packet_files)
    private_job = dict(safe_job)
    private_job["repository"] = {**safe_job["repository"], "path": str(repo)}
    private_job["private_request_source"] = str(request_path)
    atomic_write_json(job_dir / "private-job.json", private_job)
    state = {
        "schema_version": STATE_SCHEMA,
        "project_id": store.project_id,
        "job_id": job_id,
        "status": "CREATED",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "attempt": 0,
        "base_commit": resolved_base,
        "repository_path": str(repo),
        "packet_path": str(packet_path),
        "artifact_path": None,
        "worktree_path": None,
        "parent_job_id": parent_job_id,
        "omitted_context": omitted,
    }
    store.save_state(state)
    store.append_event(
        {
            "schema_version": SCHEMA,
            "at": state["created_at"],
            "project_id": store.project_id,
            "job_id": job_id,
            "from": None,
            "to": "CREATED",
            "note": "job created",
        }
    )
    transition(
        store,
        state,
        "PACKAGED",
        "sealed worker packet created",
        packet_sha256=sha256_file(packet_path),
        selected_files=len(selected),
    )
    return {
        "job_id": job_id,
        "status": "PACKAGED",
        "packet_path": str(packet_path),
        "base_commit": resolved_base,
        "selected_files": len(selected),
        "omitted_files": len(omitted),
    }


def safe_zip_name(name: str) -> str:
    return safe_relative(name)


def is_zip_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0o170000
    return mode == stat.S_IFLNK


def validate_patch_paths(patch: str) -> None:
    for line in patch.splitlines():
        if line.startswith(("--- ", "+++ ")):
            value = line[4:].split("\t", 1)[0].strip()
            if value == "/dev/null":
                continue
            if value.startswith("a/") or value.startswith("b/"):
                value = value[2:]
            safe_relative(value)


def extract_zip_safely(
    archive: zipfile.ZipFile, infos: Sequence[zipfile.ZipInfo], target: Path
) -> None:
    if target.exists():
        if any(target.iterdir()):
            raise LaborError(
                f"refusing to overwrite existing validated artifact: {target}"
            )
    target.mkdir(parents=True, exist_ok=True)
    root = target.resolve()
    for info in infos:
        name = safe_zip_name(info.filename)
        destination = (target / name).resolve()
        if root != destination and root not in destination.parents:
            raise LaborError(f"artifact extraction escaped its root: {info.filename!r}")
        if info.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise LaborError(f"duplicate artifact member: {name}")
        with archive.open(info, "r") as source, destination.open("xb") as sink:
            shutil.copyfileobj(source, sink, length=1024 * 1024)


def validate_return_artifact(
    zip_path: Path, state: Mapping[str, Any], project: Mapping[str, Any]
) -> dict[str, Any]:
    if not zip_path.exists() or not zip_path.is_file() or zip_path.is_symlink():
        raise LaborError(f"artifact must be a regular file: {zip_path}")
    limits = project["artifacts"]
    size = zip_path.stat().st_size
    if size > int(limits["max_zip_bytes"]):
        raise LaborError(f"artifact exceeds max ZIP size: {size}")
    expected = {
        "manifest.json",
        "START_HERE.md",
        "SUMMARY.md",
        "INTEGRATION.md",
        "REMAINING.md",
        "VALIDATION.md",
        "changes.patch",
    }
    members: list[dict[str, Any]] = []
    total = 0
    try:
        archive = zipfile.ZipFile(zip_path, "r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise LaborError(f"invalid artifact ZIP: {exc}") from exc
    with archive:
        infos = archive.infolist()
        if len(infos) > int(limits["max_members"]):
            raise LaborError(f"artifact has too many ZIP members: {len(infos)}")
        names: set[str] = set()
        for info in infos:
            name = safe_zip_name(info.filename)
            if name in names:
                raise LaborError(f"duplicate artifact member: {name}")
            names.add(name)
            if ".git" in {part.lower() for part in PurePosixPath(name).parts}:
                raise LaborError(f"artifact contains .git material: {name}")
            if is_zip_symlink(info):
                raise LaborError(f"artifact contains a symlink: {name}")
            member_size = int(info.file_size)
            if member_size > int(limits["max_member_bytes"]):
                raise LaborError(f"artifact member exceeds size limit: {name}")
            total += member_size
            if total > int(limits["max_total_uncompressed_bytes"]):
                raise LaborError("artifact exceeds total uncompressed size limit")
            compressed = max(int(info.compress_size), 1)
            if member_size > 100 * 1024 * 1024 or (
                member_size > 1024 * 1024 and member_size / compressed > 1000
            ):
                raise LaborError(f"suspicious ZIP compression ratio: {name}")
            if not info.is_dir():
                raw = archive.read(info)
                if raw.startswith((b"MZ", b"\x7fELF")):
                    raise LaborError(f"artifact contains an executable payload: {name}")
                if (info.external_attr >> 16) & 0o111:
                    raise LaborError(
                        f"artifact contains an executable-mode member: {name}"
                    )
                if name.lower().endswith(
                    (".exe", ".dll", ".so", ".dylib", ".msi", ".appimage")
                ):
                    raise LaborError(f"artifact contains a binary member: {name}")
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    text = ""
                if text and contains_secret(text):
                    raise LaborError(
                        f"artifact member looks like it contains a secret: {name}"
                    )
                members.append(
                    {"name": name, "bytes": member_size, "sha256": sha256_bytes(raw)}
                )
        missing = sorted(expected - names)
        if missing:
            raise LaborError(f"artifact missing required members: {', '.join(missing)}")
        try:
            manifest = json.loads(
                archive.read(archive.getinfo("manifest.json")).decode("utf-8")
            )
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LaborError(f"invalid artifact manifest: {exc}") from exc
        if not isinstance(manifest, dict):
            raise LaborError("artifact manifest must be an object")
        job_identity = manifest.get("job_id") or manifest.get("handoff_id")
        if job_identity != state["job_id"]:
            raise LaborError(f"artifact job identity mismatch: {job_identity!r}")
        if manifest.get("base_commit") != state["base_commit"]:
            raise LaborError("artifact base_commit does not match the pinned job")
        expected_url = normalize_remote(project.get("repository", {}).get("url"))
        returned_url = normalize_remote(manifest.get("repository"))
        if expected_url and returned_url and expected_url != returned_url:
            raise LaborError(
                f"artifact repository mismatch: {returned_url!r} != {expected_url!r}"
            )
        patch = archive.read(archive.getinfo("changes.patch")).decode("utf-8")
        validate_patch_paths(patch)
        job_dir = Path(str(state["job_dir"]))
        extracted = job_dir / "validated" / "artifact"
        extract_zip_safely(archive, infos, extracted)
    receipt = {
        "schema_version": "labor-loop.artifact-receipt.v1",
        "validated_at": now_iso(),
        "artifact_sha256": sha256_file(zip_path),
        "artifact_bytes": size,
        "member_count": len(members),
        "total_uncompressed_bytes": total,
        "members": sorted(members, key=lambda item: item["name"]),
        "manifest": manifest,
        "extracted_path": str(extracted),
    }
    atomic_write_json(job_dir / "validated" / "validation.json", receipt)
    return receipt


def copy_artifact(
    store: Store, state: dict[str, Any], source: Path, project: Mapping[str, Any]
) -> dict[str, Any]:
    source = source.expanduser().resolve()
    if not source.exists() or not source.is_file() or source.is_symlink():
        raise LaborError(f"downloaded artifact must be a regular file: {source}")
    if source.stat().st_size > int(project["artifacts"]["max_zip_bytes"]):
        raise LaborError("downloaded artifact exceeds configured size limit")
    destination = Path(str(state["job_dir"])) / "artifact.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(destination) != sha256_file(source):
            raise LaborError("a different artifact is already recorded for this job")
    else:
        shutil.copyfile(source, destination)
    state["artifact_path"] = str(destination)
    transition(
        store,
        state,
        "ARTIFACT_DOWNLOADED",
        "downloaded artifact recorded",
        artifact_sha256=sha256_file(destination),
    )
    return {
        "job_id": state["job_id"],
        "status": state["status"],
        "artifact_path": str(destination),
        "artifact_sha256": sha256_file(destination),
    }


def prepare_worktree(
    store: Store, state: dict[str, Any], project: Mapping[str, Any]
) -> dict[str, Any]:
    if state["status"] != "VALIDATED":
        raise LaborError(
            f"integration requires VALIDATED state, found {state['status']}"
        )
    configured = project.get("integration", {}).get("worktree_root")
    root = (
        Path(configured).expanduser().resolve()
        if configured
        else Path(str(state["job_dir"])) / "worktree"
    )
    root.parent.mkdir(parents=True, exist_ok=True)
    if root.exists():
        existing_head = git_text(root, ["rev-parse", "HEAD"], check=False).strip()
        if existing_head != state["base_commit"]:
            raise LaborError(
                f"existing integration worktree does not match base: {root}"
            )
    else:
        result = run_git(
            Path(str(state["repository_path"])),
            ["worktree", "add", "--detach", str(root), state["base_commit"]],
            check=False,
        )
        if result.returncode != 0:
            raise LaborError(
                f"git worktree add failed: {decode_output(result.stderr).strip()[-2000:]}"
            )
    state["worktree_path"] = str(root)
    transition(
        store,
        state,
        "INTEGRATING",
        "isolated worktree prepared",
        worktree_path=str(root),
    )
    return {
        "job_id": state["job_id"],
        "status": state["status"],
        "worktree_path": str(root),
        "base_commit": state["base_commit"],
    }


def apply_canonical_patch(store: Store, state: dict[str, Any]) -> dict[str, Any]:
    if state["status"] != "INTEGRATING":
        raise LaborError(
            f"patch application requires INTEGRATING state, found {state['status']}"
        )
    worktree = Path(str(state["worktree_path"]))
    patch = Path(str(state["job_dir"])) / "validated" / "artifact" / "changes.patch"
    if not patch.exists():
        raise LaborError(f"validated patch is missing: {patch}")
    patch_text = patch.read_text(encoding="utf-8")
    if patch_text.strip():
        checked = run_git(
            worktree,
            ["apply", "--check", "--recount", "--whitespace=error-all", str(patch)],
            check=False,
        )
        if checked.returncode != 0:
            transition(
                store,
                state,
                "FAILED",
                "git apply --check rejected the worker patch",
                failure_kind="patch-check",
                stderr=decode_output(checked.stderr)[-4000:],
            )
            raise LaborError("git apply --check rejected the worker patch")
        applied = run_git(
            worktree,
            ["apply", "--recount", "--whitespace=error-all", str(patch)],
            check=False,
        )
        if applied.returncode != 0:
            transition(
                store,
                state,
                "FAILED",
                "git apply failed after successful check",
                failure_kind="patch-apply",
                stderr=decode_output(applied.stderr)[-4000:],
            )
            raise LaborError("git apply failed after successful check")
    transition(
        store,
        state,
        "TESTING",
        "canonical patch applied in isolated worktree",
        patch_sha256=sha256_file(patch),
    )
    return {
        "job_id": state["job_id"],
        "status": state["status"],
        "worktree_path": str(worktree),
        "patch_sha256": sha256_file(patch),
    }


def run_checks(
    store: Store,
    state: dict[str, Any],
    project: Mapping[str, Any],
    *,
    allow_none: bool = False,
) -> dict[str, Any]:
    if state["status"] not in {"TESTING", "INTEGRATING"}:
        raise LaborError(
            f"checks require TESTING or INTEGRATING state, found {state['status']}"
        )
    if state["status"] == "INTEGRATING":
        transition(
            store, state, "TESTING", "testing requested after integration preparation"
        )
    commands = project.get("validation", {}).get("commands", [])
    if not commands and not allow_none:
        transition(
            store,
            state,
            "FAILED",
            "no project validation commands configured",
            failure_kind="no-validation-commands",
        )
        raise LaborError(
            "no project validation commands configured; use --allow-no-checks only for an explicit review-only round"
        )
    timeout = int(project.get("validation", {}).get("timeout_seconds", 1800))
    log_dir = Path(str(state["job_dir"])) / "checks"
    log_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    worktree = Path(str(state["worktree_path"]))
    for index, command in enumerate(commands):
        if not isinstance(command, Mapping) or not isinstance(
            command.get("argv"), list
        ):
            raise LaborError(f"validation command {index} must contain an argv array")
        argv = [str(item) for item in command["argv"]]
        name = str(command.get("name") or f"check-{index + 1}")
        slug = (
            re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")[:48]
            or f"check-{index + 1}"
        )
        log_path = log_dir / f"{index + 1:02d}-{slug}.log"
        started = time.monotonic()
        try:
            with log_path.open("w", encoding="utf-8", newline="\n") as log:
                log.write("$ " + " ".join(argv) + "\n\n")
                process = subprocess.run(
                    argv,
                    cwd=str(worktree),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                    check=False,
                )
            code = process.returncode
            timed_out = False
        except subprocess.TimeoutExpired:
            code = None
            timed_out = True
            with log_path.open("a", encoding="utf-8") as log:
                log.write(f"\nTIMEOUT after {timeout}s\n")
        result = {
            "name": name,
            "argv": argv,
            "returncode": code,
            "timed_out": timed_out,
            "seconds": round(time.monotonic() - started, 3),
            "log": str(log_path),
        }
        results.append(result)
        if timed_out or code != 0:
            receipt = {
                "schema_version": "labor-loop.check-receipt.v1",
                "completed_at": now_iso(),
                "passed": False,
                "checks": results,
            }
            atomic_write_json(
                Path(str(state["job_dir"])) / "checks" / "receipt.json", receipt
            )
            transition(
                store,
                state,
                "FAILED",
                f"validation command failed: {name}",
                failure_kind="validation",
                check_receipt=str(
                    Path(str(state["job_dir"])) / "checks" / "receipt.json"
                ),
            )
            raise LaborError(f"validation command failed: {name}")
    receipt = {
        "schema_version": "labor-loop.check-receipt.v1",
        "completed_at": now_iso(),
        "passed": bool(commands),
        "checks": results,
        "review_only": not bool(commands),
    }
    atomic_write_json(Path(str(state["job_dir"])) / "checks" / "receipt.json", receipt)
    transition(
        store,
        state,
        "REVIEWING",
        "configured local checks completed",
        check_receipt=str(Path(str(state["job_dir"])) / "checks" / "receipt.json"),
        checks_passed=len(results),
    )
    return {
        "job_id": state["job_id"],
        "status": state["status"],
        "receipt": str(Path(str(state["job_dir"])) / "checks" / "receipt.json"),
        "checks": results,
    }


def cmd_init(args: argparse.Namespace) -> dict[str, Any]:
    store = Store(
        Path(args.state_root) if args.state_root else default_state_root(),
        args.project_id,
    )
    info = repository_info(Path(args.repo))
    store.ensure()
    if store.project_path.exists() and not args.force:
        raise LaborError(
            f"project already initialized: {store.project_path}; use --force only to replace it"
        )
    project = default_project_config(args.project_id, info)
    if args.config_file:
        supplied = read_json(Path(args.config_file).expanduser().resolve())
        project = deep_merge(project, supplied)
    project["schema_version"] = PROJECT_SCHEMA
    project["project_id"] = args.project_id
    project["repository"]["path"] = str(Path(str(info["root"])).resolve())
    if not project["repository"].get("url"):
        project["repository"]["url"] = info["remote"]
    validate_project_config(project, args.project_id)
    with store.lock():
        store.save_project(project)
        store.append_event(
            {
                "schema_version": SCHEMA,
                "at": now_iso(),
                "project_id": args.project_id,
                "job_id": None,
                "from": None,
                "to": "PROJECT_INITIALIZED",
                "note": "project mapping initialized",
            }
        )
    return {
        "project_id": args.project_id,
        "state_root": str(store.root),
        "project_path": str(store.project_path),
        "repository": project["repository"],
    }


def cmd_bind_thread(args: argparse.Namespace) -> dict[str, Any]:
    store, project = project_and_store(args)
    url = args.thread_url.strip()
    if not re.fullmatch(r"https://(?:chatgpt\.com|chat\.openai\.com)/.+", url):
        raise LaborError("thread URL must be an https ChatGPT conversation URL")
    existing = project["worker"].get("thread_url")
    if existing and existing != url and not args.replace:
        raise LaborError(
            "a different thread is already bound; pass --replace for an intentional reset"
        )
    worker = dict(project["worker"])
    worker.update(
        {
            "provider": "chatgpt-chat",
            "thread_url": url,
            "thread_id": args.thread_id,
            "browser": args.browser,
            "model_mode": args.model_mode,
        }
    )
    project["worker"] = worker
    with store.lock():
        store.save_project(project)
        store.append_event(
            {
                "schema_version": SCHEMA,
                "at": now_iso(),
                "project_id": args.project_id,
                "job_id": None,
                "from": None,
                "to": "THREAD_BOUND",
                "note": "persistent ChatGPT thread mapping updated",
                "thread_url": url,
                "browser": args.browser,
            }
        )
    return {
        "project_id": args.project_id,
        "thread_url": url,
        "thread_id": args.thread_id,
        "browser": args.browser,
        "provider": "chatgpt-chat",
    }


def cmd_record_submission(args: argparse.Namespace) -> dict[str, Any]:
    """Persist a browser adapter's successful send observation atomically."""
    store, project = project_and_store(args)
    url = args.thread_url.strip()
    if not re.fullmatch(r"https://(?:chatgpt\.com|chat\.openai\.com)/.+", url):
        raise LaborError("thread URL must be an https ChatGPT conversation URL")
    with store.lock():
        project = store.load_project()
        state = store.load_state(args.job_id if args.job_id else None)
        status = str(state["status"])
        was_already_submitted = status != "PACKAGED"
        state_url = state.get("thread_url")
        state_thread_id = state.get("thread_id")
        same_submission = (not state_url or state_url == url) and (
            not state_thread_id
            or not args.thread_id
            or state_thread_id == args.thread_id
        )
        if status not in {"PACKAGED", "SUBMITTED", "WORKER_RUNNING"}:
            if same_submission and status in {
                "WORKER_COMPLETE",
                "ARTIFACT_DISCOVERED",
                "ARTIFACT_DOWNLOADED",
                "VALIDATED",
                "INTEGRATING",
                "TESTING",
                "REVIEWING",
                "COMPLETE",
            }:
                # A browser retry can arrive after durable state advanced. It
                # must never regress the state or append a duplicate event.
                return {
                    "job_id": state["job_id"],
                    "status": status,
                    "thread_url": state_url or url,
                    "thread_id": state_thread_id or args.thread_id,
                    "worker_started": args.worker_started,
                    "idempotent": True,
                }
            raise LaborError(
                "record-submission requires PACKAGED, SUBMITTED, or WORKER_RUNNING state, "
                f"found {status}"
            )
        existing = project["worker"].get("thread_url")
        existing_thread_id = project["worker"].get("thread_id")
        if existing and existing != url and not args.replace:
            raise LaborError(
                "a different thread is already bound; pass --replace for an intentional reset"
            )
        if not same_submission:
            raise LaborError(
                "submission identity differs from the durable job receipt; "
                "abort/retry the job before using a different worker thread"
            )
        recorded_thread_id = args.thread_id or state_thread_id or existing_thread_id
        binding_changed = (
            existing != url
            or existing_thread_id != recorded_thread_id
            or project["worker"].get("browser") != args.browser
            or project["worker"].get("model_mode") != args.model_mode
        )
        worker = dict(project["worker"])
        worker.update(
            {
                "provider": "chatgpt-chat",
                "thread_url": url,
                "thread_id": recorded_thread_id,
                "browser": args.browser,
                "model_mode": args.model_mode,
            }
        )
        project["worker"] = worker
        if binding_changed:
            store.save_project(project)
            store.append_event(
                {
                    "schema_version": SCHEMA,
                    "at": now_iso(),
                    "project_id": args.project_id,
                    "job_id": state["job_id"],
                    "from": None,
                    "to": "THREAD_BOUND",
                    "note": "browser adapter recorded the submitted worker thread",
                    "thread_url": url,
                    "thread_id": recorded_thread_id,
                    "browser": args.browser,
                }
            )
        if status == "PACKAGED":
            state = transition(
                store,
                state,
                "SUBMITTED",
                args.note,
                thread_url=url,
                thread_id=recorded_thread_id,
            )
            status = "SUBMITTED"
        if args.worker_started and status == "SUBMITTED":
            state = transition(
                store,
                state,
                "WORKER_RUNNING",
                "worker visibly entered its answering state",
                thread_url=url,
                thread_id=recorded_thread_id,
            )
    return {
        "job_id": state["job_id"],
        "status": state["status"],
        "thread_url": url,
        "thread_id": recorded_thread_id,
        "worker_started": args.worker_started,
        "idempotent": was_already_submitted,
    }


def cmd_start(
    args: argparse.Namespace, parent_job_id: str | None = None
) -> dict[str, Any]:
    store, project = project_and_store(args)
    with store.lock():
        return create_job(
            store,
            project,
            Path(args.request).expanduser().resolve(),
            base=args.base,
            parent_job_id=parent_job_id or args.parent_job_id,
        )


def current_state_for_args(
    args: argparse.Namespace,
) -> tuple[Store, dict[str, Any], dict[str, Any]]:
    store, project = project_and_store(args)
    state = store.load_state(args.job_id if getattr(args, "job_id", None) else None)
    state["job_dir"] = str(store.job_dir(state["job_id"]))
    return store, project, state


def cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    store, project = project_and_store(args)
    state = (
        store.load_state(args.job_id if args.job_id else None)
        if store.state_path.exists()
        else None
    )
    result: dict[str, Any] = {
        "project_id": args.project_id,
        "state_root": str(store.root),
        "thread": project["worker"],
        "current": None,
    }
    if state:
        result["current"] = {
            key: state.get(key)
            for key in (
                "job_id",
                "status",
                "created_at",
                "updated_at",
                "attempt",
                "base_commit",
                "packet_path",
                "artifact_path",
                "worktree_path",
                "last_note",
                "thread_url",
                "thread_id",
            )
        }
        if store.timeline_path.exists():
            lines = store.timeline_path.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()[-8:]
            result["recent_events"] = [
                json.loads(line) for line in lines if line.strip()
            ]
    return result


def cmd_resume(args: argparse.Namespace) -> dict[str, Any]:
    store, project, state = current_state_for_args(args)
    next_action = {
        "PACKAGED": "resolve the mapped ChatGPT thread, confirm, upload packet, send request, then transition SUBMITTED",
        "SUBMITTED": "inspect the ChatGPT thread and classify whether the worker started",
        "WORKER_RUNNING": "poll with backoff; record completion, clarification, limit, or blocked state",
        "WORKER_COMPLETE": "discover/download the returned ZIP and record-artifact; if only a backend/session link was returned, use artifact-followup",
        "ARTIFACT_DISCOVERED": "record-artifact <downloaded-zip>",
        "ARTIFACT_DOWNLOADED": "validate-artifact",
        "VALIDATED": "integrate",
        "INTEGRATING": "integrate or inspect the isolated worktree",
        "TESTING": "run-checks or inspect its receipt",
        "REVIEWING": "perform Codex review, then review --decision complete|followup|blocked",
        "COMPLETE": "no further action for this job",
        "NEEDS_FOLLOWUP": "write the next bounded request and run next",
        "BLOCKED": "resolve the human/external blocker, then retry or start a follow-up",
        "FAILED": "inspect the receipt; use repair-checks for a local validation repair or retry explicitly",
        "ABORTED": "start a new job if still needed",
    }.get(state["status"], "inspect state")
    return {
        "job_id": state["job_id"],
        "status": state["status"],
        "next_action": next_action,
        "thread": project["worker"],
    }


def cmd_artifact_followup(args: argparse.Namespace) -> dict[str, Any]:
    """Prepare a delivery-only follow-up without sending a browser message."""
    store, project, state = current_state_for_args(args)
    allowed = {"WORKER_COMPLETE", "ARTIFACT_DISCOVERED", "BLOCKED", "FAILED"}
    if state["status"] not in allowed:
        raise LaborError(
            "artifact-followup requires WORKER_COMPLETE, ARTIFACT_DISCOVERED, "
            f"BLOCKED, or an artifact-related FAILED state; found {state['status']}"
        )
    if state["status"] == "FAILED" and state.get("failure_kind") not in {
        "artifact-validation",
        "artifact-delivery",
    }:
        raise LaborError(
            "artifact-followup is limited to artifact delivery/validation failures"
        )
    reason = args.reason.strip()
    if not reason:
        raise LaborError("artifact-followup requires a non-empty --reason")
    if len(reason) > 2000:
        raise LaborError("artifact-followup reason exceeds 2000 characters")
    if contains_secret(reason):
        raise LaborError("artifact-followup reason contains a likely secret")
    safe_reason = scrub_local_paths(reason, Path(str(state["repository_path"])))
    repository_url = project["repository"].get("url")
    prompt = artifact_delivery_followup(
        job_id=state["job_id"],
        base_commit=str(state["base_commit"]),
        repository_url=repository_url,
        reason=safe_reason,
    )
    output_path = None
    with store.lock():
        current = store.load_state(state["job_id"])
        current["job_dir"] = str(store.job_dir(current["job_id"]))
        store.append_event(
            {
                "schema_version": SCHEMA,
                "at": now_iso(),
                "project_id": current["project_id"],
                "job_id": current["job_id"],
                "from": current["status"],
                "to": current["status"],
                "note": "artifact delivery follow-up prepared",
                "extra": {"reason": safe_reason},
            }
        )
        if args.output:
            output = Path(args.output).expanduser().resolve()
            if output.exists() and output.is_symlink():
                raise LaborError(f"refusing symlink output: {output}")
            output.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(output, prompt)
            output_path = str(output)
    return {
        "job_id": state["job_id"],
        "status": state["status"],
        "prompt": prompt,
        "output_path": output_path,
        "send_manually_or_with_browser_adapter": True,
    }


def cmd_transition(args: argparse.Namespace) -> dict[str, Any]:
    store, project, state = current_state_for_args(args)
    with store.lock():
        state = store.load_state(state["job_id"])
        state["job_dir"] = str(store.job_dir(state["job_id"]))
        transition(store, state, args.to, args.note)
    return {"job_id": state["job_id"], "status": state["status"], "note": args.note}


def cmd_record_artifact(args: argparse.Namespace) -> dict[str, Any]:
    store, project, state = current_state_for_args(args)
    if state["status"] not in {
        "WORKER_COMPLETE",
        "ARTIFACT_DISCOVERED",
        "ARTIFACT_DOWNLOADED",
    }:
        raise LaborError(
            f"record-artifact requires a worker-complete state, found {state['status']}"
        )
    with store.lock():
        state = store.load_state(state["job_id"])
        state["job_dir"] = str(store.job_dir(state["job_id"]))
        return copy_artifact(store, state, Path(args.path), project)


def cmd_validate_artifact(args: argparse.Namespace) -> dict[str, Any]:
    store, project, state = current_state_for_args(args)
    if state["status"] == "VALIDATED":
        receipt_path = Path(str(state["job_dir"])) / "validated" / "validation.json"
        return read_json(receipt_path)
    if state["status"] not in {"ARTIFACT_DOWNLOADED", "ARTIFACT_DISCOVERED"}:
        raise LaborError(
            f"validate-artifact requires a downloaded artifact, found {state['status']}"
        )
    state["job_dir"] = str(store.job_dir(state["job_id"]))
    artifact = Path(str(state.get("artifact_path") or ""))
    if not artifact.exists():
        raise LaborError("state does not name an existing artifact")
    try:
        receipt = validate_return_artifact(artifact, state, project)
    except LaborError as exc:
        with store.lock():
            current = store.load_state(state["job_id"])
            current["job_dir"] = str(store.job_dir(current["job_id"]))
            transition(
                store,
                current,
                "FAILED",
                "artifact validation rejected the returned ZIP",
                failure_kind="artifact-validation",
                error=str(exc),
            )
        raise
    with store.lock():
        current = store.load_state(state["job_id"])
        current["job_dir"] = str(store.job_dir(current["job_id"]))
        transition(
            store,
            current,
            "VALIDATED",
            "artifact validated and extracted safely",
            validation_receipt=str(
                Path(str(current["job_dir"])) / "validated" / "validation.json"
            ),
        )
    return receipt


def cmd_integrate(args: argparse.Namespace) -> dict[str, Any]:
    store, project, state = current_state_for_args(args)
    with store.lock():
        state = store.load_state(state["job_id"])
        state["job_dir"] = str(store.job_dir(state["job_id"]))
        if state["status"] == "VALIDATED":
            prepare_worktree(store, state, project)
        if state["status"] == "INTEGRATING":
            apply_canonical_patch(store, state)
    if args.skip_checks:
        return {
            "job_id": state["job_id"],
            "status": state["status"],
            "worktree_path": state["worktree_path"],
            "checks": "skipped",
        }
    store, project, state = current_state_for_args(args)
    return run_checks(store, state, project, allow_none=args.allow_no_checks)


def cmd_run_checks(args: argparse.Namespace) -> dict[str, Any]:
    store, project, state = current_state_for_args(args)
    with store.lock():
        state = store.load_state(state["job_id"])
        state["job_dir"] = str(store.job_dir(state["job_id"]))
        return run_checks(store, state, project, allow_none=args.allow_no_checks)


def cmd_repair_checks(args: argparse.Namespace) -> dict[str, Any]:
    """Resume validation after an explicit local repair of an intact worktree."""
    store, project, state = current_state_for_args(args)
    if state["status"] != "FAILED":
        raise LaborError(
            f"repair-checks requires FAILED state, found {state['status']}"
        )
    if state.get("failure_kind") != "validation":
        raise LaborError(
            "repair-checks is limited to validation failures; inspect and retry other failures"
        )
    worktree = Path(str(state.get("worktree_path") or ""))
    if not worktree.is_dir():
        raise LaborError("repair-checks requires the existing isolated worktree")
    with store.lock():
        state = store.load_state(state["job_id"])
        state["job_dir"] = str(store.job_dir(state["job_id"]))
        transition(
            store,
            state,
            "TESTING",
            args.note,
            recovery_kind="validation-repair",
        )
        return run_checks(store, state, project, allow_none=args.allow_no_checks)


def cmd_review(args: argparse.Namespace) -> dict[str, Any]:
    store, project, state = current_state_for_args(args)
    target = {
        "complete": "COMPLETE",
        "followup": "NEEDS_FOLLOWUP",
        "blocked": "BLOCKED",
    }[args.decision]
    with store.lock():
        state = store.load_state(state["job_id"])
        state["job_dir"] = str(store.job_dir(state["job_id"]))
        transition(store, state, target, args.note, review_decision=args.decision)
    return {
        "job_id": state["job_id"],
        "status": state["status"],
        "review_decision": args.decision,
        "note": args.note,
    }


def cmd_retry(args: argparse.Namespace) -> dict[str, Any]:
    store, project, state = current_state_for_args(args)
    if state["status"] not in {"FAILED", "BLOCKED", "NEEDS_FOLLOWUP"}:
        raise LaborError(
            f"retry requires FAILED, BLOCKED, or NEEDS_FOLLOWUP, found {state['status']}"
        )
    with store.lock():
        state = store.load_state(state["job_id"])
        state["job_dir"] = str(store.job_dir(state["job_id"]))
        state["attempt"] = int(state.get("attempt", 0)) + 1
        transition(store, state, "PACKAGED", args.note, attempt=state["attempt"])
    return {
        "job_id": state["job_id"],
        "status": state["status"],
        "attempt": state["attempt"],
    }


def cmd_abort(args: argparse.Namespace) -> dict[str, Any]:
    store, project, state = current_state_for_args(args)
    if state["status"] in TERMINAL:
        return {
            "job_id": state["job_id"],
            "status": state["status"],
            "note": "already terminal",
        }
    with store.lock():
        state = store.load_state(state["job_id"])
        state["job_dir"] = str(store.job_dir(state["job_id"]))
        transition(store, state, "ABORTED", args.note)
    return {"job_id": state["job_id"], "status": state["status"], "note": args.note}


def cmd_inspect(args: argparse.Namespace) -> dict[str, Any]:
    store, project, state = current_state_for_args(args)
    job_dir = Path(str(state["job_dir"]))
    result: dict[str, Any] = {
        "state": state,
        "job": read_json(job_dir / "job.json")
        if (job_dir / "job.json").exists()
        else None,
    }
    for relative in ("validated/validation.json", "checks/receipt.json"):
        path = job_dir / relative
        if path.exists():
            result[relative] = read_json(path)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resumable local core for the ChatGPT labor loop"
    )
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--state-root")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--repo", required=True)
    init.add_argument("--config-file")
    init.add_argument("--force", action="store_true")

    bind = sub.add_parser("bind-thread")
    bind.add_argument("--thread-url", required=True)
    bind.add_argument("--thread-id")
    bind.add_argument("--browser", default="chrome")
    bind.add_argument("--model-mode", default="configured")
    bind.add_argument("--replace", action="store_true")

    submission = sub.add_parser(
        "record-submission",
        help="atomically record a browser adapter's already-completed send",
    )
    submission.add_argument("--job-id")
    submission.add_argument("--thread-url", required=True)
    submission.add_argument("--thread-id")
    submission.add_argument("--browser", default="chrome")
    submission.add_argument("--model-mode", default="configured")
    submission.add_argument("--replace", action="store_true")
    submission.add_argument("--worker-started", action="store_true")
    submission.add_argument("--note", default="worker request submitted")

    for name in ("start", "next"):
        command = sub.add_parser(name)
        command.add_argument("--request", required=True)
        command.add_argument("--base")
        command.add_argument("--parent-job-id")

    status = sub.add_parser("status")
    status.add_argument("--job-id")
    resume = sub.add_parser("resume")
    resume.add_argument("--job-id")
    inspect = sub.add_parser("inspect")
    inspect.add_argument("--job-id")

    transition_parser = sub.add_parser("transition")
    transition_parser.add_argument("--job-id")
    transition_parser.add_argument("--to", choices=STATUSES, required=True)
    transition_parser.add_argument("--note", required=True)

    record = sub.add_parser("record-artifact")
    record.add_argument("--job-id")
    record.add_argument("--path", required=True)
    validate = sub.add_parser("validate-artifact")
    validate.add_argument("--job-id")

    integrate = sub.add_parser("integrate")
    integrate.add_argument("--job-id")
    integrate.add_argument("--skip-checks", action="store_true")
    integrate.add_argument("--allow-no-checks", action="store_true")
    checks = sub.add_parser("run-checks")
    checks.add_argument("--job-id")
    checks.add_argument("--allow-no-checks", action="store_true")
    repair_checks = sub.add_parser(
        "repair-checks",
        help="rerun checks after an explicit local repair of an intact worktree",
    )
    repair_checks.add_argument("--job-id")
    repair_checks.add_argument("--allow-no-checks", action="store_true")
    repair_checks.add_argument("--note", default="local validation repair applied")

    artifact_followup = sub.add_parser(
        "artifact-followup",
        help="prepare a direct-attachment/public-URL recovery request",
    )
    artifact_followup.add_argument("--job-id")
    artifact_followup.add_argument("--reason", required=True)
    artifact_followup.add_argument("--output")

    review = sub.add_parser("review")
    review.add_argument("--job-id")
    review.add_argument(
        "--decision", choices=("complete", "followup", "blocked"), required=True
    )
    review.add_argument("--note", required=True)
    retry = sub.add_parser("retry")
    retry.add_argument("--job-id")
    retry.add_argument("--note", default="explicit retry requested")
    abort = sub.add_parser("abort")
    abort.add_argument("--job-id")
    abort.add_argument("--note", default="explicit abort requested")
    return parser


def dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "init":
        return cmd_init(args)
    if args.command == "bind-thread":
        return cmd_bind_thread(args)
    if args.command == "record-submission":
        return cmd_record_submission(args)
    if args.command == "start":
        return cmd_start(args)
    if args.command == "next":
        store, project = project_and_store(args)
        current = store.load_state() if store.state_path.exists() else None
        parent = current["job_id"] if current else None
        return cmd_start(args, parent_job_id=parent)
    if args.command == "status":
        return cmd_status(args)
    if args.command == "resume":
        return cmd_resume(args)
    if args.command == "inspect":
        return cmd_inspect(args)
    if args.command == "transition":
        return cmd_transition(args)
    if args.command == "record-artifact":
        return cmd_record_artifact(args)
    if args.command == "validate-artifact":
        return cmd_validate_artifact(args)
    if args.command == "integrate":
        return cmd_integrate(args)
    if args.command == "run-checks":
        return cmd_run_checks(args)
    if args.command == "repair-checks":
        return cmd_repair_checks(args)
    if args.command == "artifact-followup":
        return cmd_artifact_followup(args)
    if args.command == "review":
        return cmd_review(args)
    if args.command == "retry":
        return cmd_retry(args)
    if args.command == "abort":
        return cmd_abort(args)
    raise LaborError(f"unknown command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = dispatch(args)
    except LaborError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
