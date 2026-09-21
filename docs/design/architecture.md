# Portable engine and protocol

Target v2, contract version 1. This is not the current CLI API. Criteria are in
[product.md](product.md); implementation order is in [plan](../implementation/plan.md).

## Ownership

Retain the standard-library Python core and CLI. Introduce only these seams:

Terminology: a client adapter connects a local application (for example Codex or
Cursor); a machine is the operating-system host; a transport provides supported
browser/file operations. Two clients on one machine suffice for client
portability. Cross-machine distributed ownership is not a v2 requirement.

| Owner | Responsibility | Explicit exclusion |
|---|---|---|
| Engine | Job state, policy, action selection, attempts, budgets, proof gates | Provider DOM, host model reasoning |
| Host transport | Supported browser/file/tool operations, local execution isolation, evidence capture | Choosing task policy or accepting patches |
| Service adapter | Thread identity, visible UI interpretation, mode selection and artifact presentation | Reading credentials, changing engine state directly |
| Capability resolver | Join documented, configured, observed and tested capability facts | Granting transport permission from a plan label |
| Local integrator/reviewer | Candidate materialization, trusted checks, evidence-bound acceptance | Worker self-approval, implicit publication |

These are modules/contracts, not five daemons. One CLI owns private persisted
state. Host instruction files and optional tool wrappers invoke the same CLI.
The model chooses neither recovery algorithms nor shell strings. Browser
selectors live in versioned service adapters; browser API calls live in host
transports. Adapters are local reviewed code, not remotely discovered plugins.

## Versioned protocol

Proposed commands: `doctor`, `capabilities`, `next-action`, `prepare-action`,
`record-observation`, `reconcile`, `migrate`, plus existing task operations.
Do not advertise them as runnable until their implementation slice is accepted.
All commands accept JSON via a file or stdin, emit one JSON result to stdout,
and send bounded diagnostics to stderr. No shell-evaluated strings. Paths and
argv arrays are concrete values selected by the engine, not page instructions.

Each request carries `protocol=2`, `project_id`, `job_id` when applicable,
`expected_revision`, and `request_id` (UUID, reused for retries). Mutations use
compare-and-swap; duplicate matching requests return their stored result,
and a reused request ID with different input returns `REQUEST_CONFLICT`.
Unknown major versions, fields on authority-bearing objects, enum values and
oversized payloads are rejected before side effects. Limits: 1 MiB JSON input,
64 KiB inline diagnostic output; larger local evidence is a referenced file.

Result example (illustrative schema, not a current invocation):

```json
{
  "protocol": 2,
  "ok": true,
  "project_id": "example",
  "job_id": "LL-example",
  "revision": 12,
  "phase": "WORKER_RUNNING",
  "condition": "WAITING",
  "reason_code": "WORKER_BUSY",
  "next_action": {
    "action_id": "job-attempt-operation-generation",
    "kind": "WAIT_UNTIL",
    "not_before": "2026-09-21T15:00:00Z",
    "expires_at": "2026-09-21T15:05:00Z",
    "executor": "host-scheduler",
    "arguments": {},
    "requires_scope": "observe-thread"
  },
  "attention": null,
  "evidence_refs": []
}
```

Exactly one of actionable `next_action`, future `WAIT_UNTIL`, named `attention`,
or terminal result exists. Attention includes owner, reason, redacted evidence,
the exact missing fact/action, and a typed resume condition. Exit codes: 0 for
valid response (including waits), 2 invalid input, 3 stale/conflicting state,
4 attention required, 5 operation failed, 6 unsupported. Drivers inspect both
exit code and JSON; contradictory/malformed output is `PROTOCOL_INVALID` and
permits only doctor/read-only inspection. CLI help and templates must agree.

## State and durable side effects

Preserve the existing phase names from CREATED through COMPLETE. Separate
`condition=READY|WAITING|ATTENTION|FAILED|ABORTED` from last proven phase; a quota
or authentication problem does not erase progress. COMPLETE is terminal.
NEEDS_FOLLOWUP closes the round with unmet criteria; a child job receives a new
request and a separately approved base. Phase advancement is engine-only;
generic `transition` becomes observation-only and cannot assert validation,
testing, review or acceptance.

State identity: project, job, attempt, revision, base commit, request hash,
packet hash, policy hash, capability snapshot, service/account alias/thread,
selected model/mode, artifact hash, candidate tree hash and runner hash.
Account alias is local and nonsecret, never an email or authentication token.
Thread identity includes provider and workspace/account alias; tab IDs are hints.

| Advance | Mandatory evidence |
|---|---|
| CREATED -> PACKAGED | Pinned base exists; complete outgoing-byte preview approved by local policy; sealed packet and omissions receipt |
| PACKAGED -> SUBMITTED | Prepared dispatch intent and matching visible send receipt in bound thread; attachment readiness observed before send |
| SUBMITTED -> WORKER_RUNNING/COMPLETE | New observation from same thread and submission, not an old assistant response |
| COMPLETE worker -> ARTIFACT_DOWNLOADED | Supported download completed; local ordinary file sealed into attempt quarantine |
| ARTIFACT_DOWNLOADED -> VALIDATED | Immutable artifact hash, identity/scope/archive checks and manifest agreement |
| VALIDATED -> INTEGRATING -> TESTING | Exact fresh candidate at pinned base; canonical patch applied once; resulting tree sealed |
| TESTING -> REVIEWING | All required trusted checks terminated on that exact candidate with retained receipts |
| REVIEWING -> COMPLETE | Reviewer decision binds criteria, candidate tree and validation receipt set; no missing required check |

Artifact discovery may be recorded while worker generation runs. Intake cannot
accept a partial download or a prior response. No-file completion is valid only
for a declared review-only task mode with its own structured return contract.

Use one append-only authoritative journal per project. Each event has sequence,
request ID, payload digest and prior-event digest. Derived state/current-index
snapshots are reconstructible caches. Under an OS-backed exclusive project
lock, validate revision, append complete event, flush, then replace snapshots.
Readers recover a missing snapshot from events. Ignore only an incomplete final
record after a crash; a corrupt interior record requires attention. Digests
detect corruption and binding mismatch, not forgery by the local OS user.
The journal, not a collection of separately replaced JSON files, defines commit.

Long operations use recorded operation reservations with generation tokens.
Release the short journal lock while waiting for browser or subprocess work;
every completion must match its reservation generation and input hashes.
Only one integration/check operation may run per candidate. A timeout does not
release a running owner's reservation. Retain process handle/creation identity
and cancellation receipt; unknown process liveness requires attention. Locks
are scoped to canonical repository identity as well as project ID, so two
aliases cannot mutate the same checkout concurrently. V1 lock/state and v2
state are not concurrently writable during migration.

`current_job` changes only on explicit create/select events. Events for an old
job cannot change it. Handover between hosts uses the same state root and a new
reservation generation after proving the old executor quiescent. Copying state
to two hosts does not grant concurrent ownership; remote distributed operation
is out of scope for v2.

## Submission ambiguity and idempotency

```text
prepare dispatch under lock:
  validate revision, scope, thread, mode, capabilities, packet, deadlines
  persist intent with action_id and nonsecret round marker
host:
  atomically claim action for one executor/generation before any remote effect
  reject a second execution claim; replay of claimed action only reconciles
  resolve and visibly verify bound thread and account context
  verify upload finished; send once with round marker in message
  return visible receipt (thread, message identity if exposed, marker evidence)
record result:
  accept only matching pending intent and current reservation
  same receipt is idempotent; conflicting receipt requires attention
after crash without result:
  inspect bound thread for marker and packet identity
  one unambiguous match -> reconcile, never resend
  multiple/uncertain/no readable history -> attention, never blind resend
```

No remote exactly-once guarantee is claimed. Absence in a partial UI view is
not proof the send failed. A definite pre-send failure permits a new dispatch
generation; an uncertain send needs reconciliation or explicit human resolution.
The same protocol covers artifact follow-ups, clarification replies and any
other remote message, with separate operation IDs and a shared send budget.
The claim is an engine-mediated single-use capability consumed by the host
transport entrypoint, not an advisory instruction to the model. A crash after
claim but before a known send result also reconciles; automatic claim expiry
cannot authorize resending. Test two callers at a pre-send barrier.

## Attempts, budgets and freshness

A delivery attempt owns its immutable download/extraction directory. A corrected
ZIP creates a new attempt with a supersedes link; prior evidence remains.
Resending implementation is a different operation from re-requesting delivery.
No retry carries forward accepted extraction, applied marker, checks, or review
for a different artifact. Keep the original request/base bound to the job.
Changed request/base creates a new child job, never an in-place rewrite.
Use two explicit identities: `return_generation` is allocated before initial
dispatch or a correction/regeneration follow-up and is required in the worker
manifest; `acquisition_id` identifies each local download of those bytes. A
redownload keeps return_generation; a correction/regeneration increments it.
The pending expected generation is authoritative. Late older returns are retained
as superseded evidence and cannot advance the current job. Manifest expectations
are included in the generated follow-up, never inferred from filenames.

Defaults: 3 jobs per run, 6 hours total elapsed, 2 consecutive failed jobs,
2 delivery follow-ups per job, 2 transient transport retries per operation,
1 known repair attempt per fault fingerprint. A successful retry does not reset
the run deadline or cumulative send counter. Check budgets before every costly
or external action and after wake. Poll 15/30/60/120/300 seconds, then 300 seconds,
bounded by provider retry-after and deadline; zero model calls while waiting.
Authentication/security/user-choice attention never consumes retry loops.

Use monotonic elapsed time within a process and persisted UTC deadline across
restart. UTC rollback greater than 5 seconds or untrusted clock change blocks
new side effects until local reconciliation; never extend deadline silently.
Expiration uses now >= expires_at. Persist due time and continuation owner;
if the host cannot schedule a wake, explicitly report that a manual resume is
required. A recorded future timestamp alone does not constitute a running loop.

## Artifact, candidate and execution trust

Seal download bytes into a new local quarantine before parsing. Reject path
traversal, absolute/drive/UNC/ADS paths, NULs, links/reparse escapes, duplicate
normalized/casefold names, Windows reserved names, encryption, nested archive
expansion and size/count/ratio excess. Existing limits are upper bounds; add
compression-ratio bound 100:1 and reject >100 MiB total expansion before writing.
Require schema/job/base/repository/attempt binding and hash agreement. Validate
patch paths and modes independently from optional full-file representations.
Only changes.patch applies; optional full files never execute or override it.
No files outside the approved changed-path scope, even if the ZIP is structurally
valid. Candidate symlinks and submodule changes need an explicitly supported task
type; otherwise reject rather than infer safe behavior.

Treat every returned file and source comment as untrusted instructions. A
configured test command can execute worker-modified code: argv allowlisting
alone is not isolation. Before checks require host-declared execution isolation
that excludes credentials, home/profile state and unrelated repos, limits writes
to the disposable candidate/scratch, denies network by default, and enforces
CPU/time/output/process-tree bounds. If unavailable, stop before execution for
an explicit trusted local execution decision; do not silently use the host.
Such an owner override is labeled `unisolated-owner-waiver`, bound to one exact
candidate/check set, and never satisfies C5 or portable qualification. It can
produce diagnostic results but cannot produce qualified COMPLETE; the owner may
adopt code outside the loop under their own separate decision. Keep the job in
attention until qualifying isolation/check evidence exists.
Never run worker-provided installers, hooks, Git aliases or validation commands.

Validation and review bind runner version/hash, policy/check definition hash,
candidate content digest (the complete frozen input inventory defined in
[proof-contract.md](proof-contract.md)), base, request
and artifact hashes. Any mutation invalidates prior checks. Promotion rechecks
those identities. Code that changes tests cannot erase externally pinned
acceptance checks. Worker claims are separate from local receipts.

## Migration and self-hosting

Keep v1 state read-only; back it up and migrate into a sibling v2 state root.
Unknown fields are preserved as opaque legacy data, never active policy.
Preview conversion, compare job/thread/base/artifact identities and state
cardinality, then explicitly switch the owning runner. V1 incomplete evidence
becomes v2 attention at its last proven phase, never fabricated receipts.
Rollback switches to untouched v1 only if no v2 external effect occurred;
otherwise reconcile those effects before another send. Old code refuses v2.

When improving the loop using itself, pin the incumbent runner and independent
validator outside the candidate. A candidate cannot replace the runner,
lower check requirements or review itself in the same round. Accept in an
isolated worktree, run the cross-version gate, then activate a new pinned runner
for the next round. Deployment/publication remain separate owner actions.
