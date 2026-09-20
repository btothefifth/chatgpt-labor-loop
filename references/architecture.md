# Labor-loop architecture

The system has two deliberately separate planes.

## Local authority plane

`labor_loop.py` is a small standard-library CLI. It stores state under a private
state root, normally `%LOCALAPPDATA%\Codex\labor-loop`, with one directory per
project and one job directory per implementation round. The project record holds
the repository path and the persistent ChatGPT thread mapping. The job record
holds the pinned base commit, packet/artifact paths, worktree, status, attempt,
and bounded timeline.

State writes are serialized by an exclusive lock file and committed with a
temporary file plus `os.replace`. Every transition appends a JSONL event. A
restarted process can therefore inspect the last durable state without trusting
in-memory progress or a browser tab that may no longer exist.

The core state machine is:

```text
CREATED -> PACKAGED -> SUBMITTED -> WORKER_RUNNING -> WORKER_COMPLETE
  -> ARTIFACT_DISCOVERED -> ARTIFACT_DOWNLOADED -> VALIDATED
  -> INTEGRATING -> TESTING -> REVIEWING -> COMPLETE
                                      \-> NEEDS_FOLLOWUP
Any active state may become FAILED, BLOCKED, or ABORTED.
```

`review` is the acceptance boundary. A worker completion or passing local check
does not imply `COMPLETE`.

## Browser adapter plane

The browser phase is a volatile adapter, not a Python HTTP client. In this
environment Codex can inspect and operate an existing authenticated Chrome
session through the supported browser-control tool, while ordinary local
scripts cannot safely call that tool. The skill therefore records browser
observations and invokes the adapter from the Codex turn, while all durable
state, validation, and integration stay in the local CLI.

The adapter must expose these conceptual operations:

```text
resolve_thread(project_mapping)
inspect_worker(thread) -> RUNNING | COMPLETE | CLARIFICATION | LIMIT | AUTH_REQUIRED | ERROR
submit(packet)                     # confirmation immediately before upload/send
download_result(thread) -> path
```

The adapter may call `scripts/repair_browser_bridge.py` as a separate local
preflight when the browser runtime itself is unhealthy. This is an environment
repair boundary, not a worker operation: it is read-only until explicitly
asked to apply, operates only on exact recognized runtime files, creates a
backup, performs an atomic replacement, and requires a runtime restart/recreate
before the browser adapter retries. Diagnosis, patch result, backup path,
before/after hashes, and syntax-check result should remain observable in the
local receipt. Unknown layouts and authentication challenges remain human-stop
conditions.

Once `submit(packet)` returns a visible receipt, the adapter should call the
CLI's `record-submission` operation with the canonical thread URL and stable
thread identity. That operation atomically updates the project mapping and
job state; it is a local receipt writer, not another browser action. A later
worker-running observation may advance the same receipt to `WORKER_RUNNING`.

A future supported bridge may implement the same operations without changing
the local state machine. It must not store credentials or bypass product
controls. Browser tab IDs are hints only; the canonical mapping is a visible
thread URL plus a user-chosen project identity.

## Integration plane

Validation happens before extraction and extraction happens outside the checkout.
The canonical returned representation is `changes.patch`. The integration
command creates a detached worktree at the pinned base, runs `git apply --check`,
applies exactly once, then executes project-configured argv arrays. Worker
scripts are never executed. Codex reviews the diff and decides whether the job
is accepted or needs another packet. A failed local check does not necessarily
require a new worker round: after an explicit, reviewable repair in the same
isolated worktree, `repair-checks` can rerun validation and preserve the job
history. It refuses artifact, patch, and missing-worktree failures.

This design keeps three boundaries independent: browser side effects, local
filesystem/Git mutation, and project-specific build/test commands.
