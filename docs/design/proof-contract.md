# Transitional candidate proof contract

Version `labor-loop.proof.v1`; required for S1a before v2 journal migration.
An additive local sidecar freezes early acceptance semantics without changing
v1's state schema. Architecture.md owns the target behavior.

## Trust and identity

Only the trusted local owning operation writes its sidecars, outside candidate
and artifact directories in private job evidence state. The candidate sandbox
cannot write that root; worker-supplied JSON and generic transitions cannot
create proof. The local OS user and explicit integrator are trusted. Hashes are
consistency bindings, not a claim to resist that user's intentional forgery.

All receipts contain schema, kind, project_id, job_id, base_commit,
request_sha256, artifact_sha256, patch_sha256, candidate_sha256,
runner_sha256, policy_sha256, created_at and receipt_id. candidate_sha256 is null
only before materialization. Other digests are lowercase 64-character SHA-256.
receipt_id hashes canonical JSON excluding receipt_id: UTF-8, sorted object keys,
separators `,` and `:`, no whitespace/NaN, exact string/integer values. Times are
UTC RFC3339. Reject unknown schema/kind, missing/extra fields, duplicate JSON keys
and inconsistent cross-receipt bindings. Preserve raw content bytes.
The artifact receipt's pre-materialization candidate_sha256=null is exempt from
equality with later candidate hashes. Candidate/check/review receipts agree on
the concrete digest and link the original artifact receipt by ID. Null never
authorizes a missing candidate at those later phases.

| Kind | Additional fields / producer |
|---|---|
| artifact | validator_version, immutable_artifact_path (private), validated_member_inventory_sha256, approved_changed_paths_sha256; intake validator |
| candidate | artifact_receipt_id, input_inventory, output_policy_sha256, worktree_identity, isolation_class; trusted materializer/bootstrap |
| checks | candidate_receipt_id, check_set_sha256, results, isolation_receipt_id; trusted runner after terminal execution |
| review | candidate_receipt_id, checks_receipt_id, reviewer_id, decision, criteria_results, note; configured local reviewer interface |

worktree_identity contains canonical repository common-directory identity,
canonical candidate path, detached=true and base_commit. isolation_class is
qualified or unisolated-owner-waiver; only qualified reaches COMPLETE. S1a uses
S0's independently verified isolation receipt. S2b later owns the automatic
producer. Missing proof is attention, not an invented success. reviewer_id is
a configured alias distinct from remote worker; decision is complete/followup/
blocked. criteria_results maps every pinned required slice criterion to pass/fail
and evidence references. Acceptance requires a nonempty reviewer note.

## Exact candidate inventory

Start from a fresh detached base worktree. Inventory every regular file in the
base Git tree and every approved added file in the validated patch. Require
patch changed paths/modes to match approved scope. Deletions remain explicit
tombstones. Reject symlinks/submodules for initial task modes. Each entry has
forward-slash relative path, Git mode (100644/100755), state present/deleted,
byte_size and raw SHA-256 (null size/hash for deleted). Sort by UTF-8 path bytes.
candidate_sha256 hashes canonical JSON of the entire inventory, not just edits.
No choice of 'relevant' inputs is delegated to the worker.

Before checks, independently scan for extra files beyond inventory and Git's
administrative `.git` entry; reject undisclosed inputs. Use read-only source
where supported and separate approved scratch/output roots. Validation argv,
interpreter/toolchain identities, environment allowlist and dependency/lockfile
identities belong to the policy/check-set digest. Do not discover arbitrary home
plugins or executable dependencies. Provision dependencies before freezing inputs;
missing dependencies require attention, not automatic installation.

Checks requiring generated files inside candidate need trusted exact output
roots declared before execution. Output roots cannot overlap input paths,
validation definitions or source-import roots. Outputs never become later inputs
without a new inventory/check generation. Recompute input inventory and extra-
file scan after checks and immediately before review. New/changed/missing inputs
invalidate proof; approved scratch output does not. Independent tests must prove
post-check source mutation rejection and harmless output success.

## Check set and completion

Check definitions are a nonempty ordered array of unique IDs, argv, cwd policy,
environment allowlist, timeout, output bounds and required=true. Hash canonical
definitions and relevant tool identities. Each result has check_id, start/end
UTC, terminal=true, exit_code, stdout_sha256, stderr_sha256 and
execution_receipt_id. Require exact check-ID set equality: missing, extra,
duplicate, running, timed-out or nonzero results fail. Empty/skip/no-checks cannot
produce passing proof. Changed inputs/check definitions require a fresh run.

COMPLETE validates current hashes, receipt chain, qualified isolation and pass
for every pinned required criterion. Matching repeated review returns its stored
decision without another event; a changed decision/input using the same review
identity conflicts. Post-review candidate drift invalidates applicability, not
history: report accepted snapshot differs from current candidate and refuse
adoption until new validation/review.

Legacy v1 jobs lacking receipts remain inspectable but cannot gain qualified
COMPLETE from notes. Require fresh trusted intake/materialization/check proof or
explicit attention. S1a introduces this sidecar schema; S3 later changes journal/
state schema. S2b strengthens producers without redefining S1a's acceptance.
