# Gap register and loop-driven implementation plan

Objective LL-PORTABLE-1 v1. Planning baseline `9bd800d8baee6acdef7c335fd7786cab0a9ecfe5`.
All slices below are pending. No v2 command or provider support is implemented.
The design is compatible with the incumbent's local-authority intent but replaces
its prose-driven orchestration and incomplete evidence gates.

## Evidence-backed gaps

Line references are pinned to the baseline, not future edits. P0 means fix or
independently contain before using returned code; P1 means before portability.

| Gap | Current evidence | Consequence | Owner / proof |
|---|---|---|---|
| G1 P0 proof-free lifecycle | labor_loop.py `cmd_transition` (~1716), `cmd_review` (~1839) | Notes can advance evidence-bearing phases through COMPLETE | S1, T11 |
| G2 P0 worktree identity | `prepare_worktree` (~1139) checks existing HEAD without sufficient checkout identity | Main/dirty/foreign checkout can be treated as disposable candidate | S0/S2, T10 |
| G3 P0 mutable proof | `apply_canonical_patch` (~1185), cached `cmd_validate_artifact` (~1741), `run_checks` (~1241) | Replaced patch or edited tree can reuse old proof | S1/S2, T10/T11 |
| G4 P1 corrected return dead end | `cmd_retry` (~1858), `copy_artifact` (~1108), `extract_zip_safely` (~969) | Retry retains rejected immutable artifact/extraction | S2, T12 |
| G5 P1 current pointer/ownership | `Store.save_state` (~490), integrate/check lock scopes (~1784/1804) | Archived updates steal pointer; competing checks overwrite evidence | S1/S3, T2/T4 |
| G6 P1 crash and duplicate effects | `transition` (~598), apply before state commit, `cmd_record_submission` (~1445) | Split persistence and post-send-only receipt cannot prevent duplicated work | S3/S4, T2/T3 |
| G7 P1 limits not enforced | Default config (~550) defines loop limits without consuming them | Driver can keep spending/retrying | S1/S4, T5 |
| G8 P1 hardcoded service/client | `validate_project_config` (~565), bind/record URL checks (~1402/1449), prose `cmd_resume` (~1626) | Other services rejected; client must invent behavior | S4/S5/S6, T1/T6/T14 |
| G9 P1 artifact-link policy informal | browser-adapter.md; `artifact-followup` (~1653) only generates text | No deterministic presentation classifier or download recovery | S5, T7/T8 |
| G10 P0 execution boundary | `run_checks` executes configured argv in returned source | Configured tests may execute hostile candidate code | S0/S2, T10 |
| G11 P1 portable archive/lock edges | `safe_relative` (~343), `StoreLock` (~383) | Windows aliases/ADS, PID reuse and stale lock races undercovered | S2/S3, T4/T9 |
| G12 P1 repair proof overclaim | repair_browser_bridge.py `node_for` (~163), syntax not-run accepted (~302) | Missing checker can still report patched; tests mock checker | S5, real Node/missing-Node fixture |
| G13 P1 no learning consumer | No installation overlay or outcome aggregation in current core | Same access/packaging problems recur; requests stay static | S2a recording, S5a path reuse, S7 reminders; T15 |
| G14 P1 limited CI/evidence | CI runs core tests on Ubuntu 3.11/3.12, omits browser-repair suite and Windows | Green CI misses host-specific failures; no cheap-driver/provider matrix | S0/S8, T13/T14 |

Audit findings are source-derived counterexamples, not all reproduced exploits.
Baseline local tests passed (12 core, 4 repair). Reproduce each target defect in
a temporary fixture before its implementation slice; never probe live state.

## Bootstrap: use the loop without trusting its current gaps

S0 is the irreducible local trust bootstrap, owned by the integrating local
agent. The remote worker can propose code, but cannot establish the runner that
will judge its own patch. Before the first implementation submission:

1. Review and commit only the approved design files locally on a dedicated
   branch, preserving any unrelated changes. Record commit SHA and packet
   inventory. Until that happens these new untracked docs are not in v1's
   committed-file packet. No remote publication is needed.
2. Make a hash-pinned read-only copy of incumbent scripts and validation
   definitions outside the candidate checkout, under private bootstrap state.
   Inventory executable/interpreter versions; use a private new project ID/root.
   Never execute the candidate's installer or use its validator to approve itself.
3. Establish trusted bootstrap intake/execution controls locally: independently
   validate archive names/limits/manifest/scope before extraction, rehash artifact
   and patch before use, allocate a new detached Git worktree at the exact base,
   prove canonical worktree path differs from main and belongs to this repo,
   require clean initial status and disabled hooks, and bind final candidate
   digest to trusted checks/review. Use `git worktree list --porcelain`,
   `git rev-parse --show-toplevel`, `git status --porcelain`, and full base SHA;
   HEAD equality alone is insufficient. The old `integrate` path is not the
   bootstrap authority. A small locally reviewed harness may implement these
   checks; freeze it before it sees worker code.
4. Select an available execution sandbox and prove denied credential/home reads,
   external network, unrelated writes and child-process escape with synthetic
   sentinels. If absent, continue packaging/static review but stop before executing
   returned code; owner waiver is diagnostic only as defined in architecture.md.
   Do not label a detached worktree a sandbox.
5. Apply run bounds locally until S1 enforces them: one outstanding job, one
   mutation/check owner, at most two delivery follow-ups and six-hour run limit.
   Keep a durable pre-send marker and inspect thread before retrying unknown send.
   Use native/manual download, not public-link fetching during bootstrap.
6. Prove the bootstrap gate with a valid synthetic patch plus tampered-patch,
   wrong-worktree and post-test edit adversaries. Its acceptance record, not
   incumbent COMPLETE, is the authority for adopting the first slices.

This local prerequisite deliberately prevents circular validation. It need not
implement all of v2; replace it with the accepted engine only after equivalent
positive and negative proof. If S0 cannot be satisfied, stop execution honestly
while continuing design/static review; do not send unbounded repair rounds.

## Epics and bounded stories

Core dependencies: S0 -> S1a/S1b -> S2a/S2b -> S3 -> S4 -> S5a.
S6 and S7 each depend on S5a, not on each other; S8 joins their evidence.
S5b is optional and blocks only a release claim that uses its repair/public-fetch
capability. Capture return-defect observations in S2a and reuse verified paths
in S5a. S7 reminder activation need not wait for another provider account.
Independent
review/research can run alongside the current slice; only one code integration
owner writes a candidate or Git index. Split a story further if its packet no
longer names one outer boundary and a bounded proof.

| Slice / files or seam | User-visible result and exit evidence | Loop packet / rollback |
|---|---|---|
| S0 local bootstrap | Frozen runner, trusted checks, isolation probe and independent candidate gate on the execution machine | Local owner only; no provider messages needed; discard private fixtures |
| S1a evidence gates (`labor_loop.py`, focused tests) | Additive proof.v1 sidecars per proof-contract.md; generic transition cannot assert proof; valid round remains reachable (T11) | First worker request below; old runner plus bootstrap judges; reject stale proof; state schema stays v1 |
| S1b budgets and status (`labor_loop.py`, config/tests) | Enforced run/recovery bounds and typed reason/next-action read model for existing phases (T1/T5) | Preserve existing CLI compatibility; no browser feature changes |
| S2a intake attempts (artifact functions/tests) | Corrected ZIP gets new immutable generation; portable path/scope guards, late-artifact rejection and typed defect observations (T9/T12/T15) | One packet for download -> validated join; preserve failed attempts |
| S2b candidate/check proof (integration functions/tests) | Fresh detached identity, immutable patch/tree binding and supported isolation gate (T10) | Trusted bootstrap remains outside candidate; rollback candidate only |
| S3 transactional state (`state` seam, migration/tests) | Journal/revision/reservations, canonical repo ownership, crash recovery and v1 read-only migration (T2/T4/T12) | Schema change isolated here; no automatic active-state migration |
| S4 typed orchestration (`protocol`, scheduling/dispatch and request preflight) | Single-use claim, send reconciliation, waiting/attention, runtime-aware high-value brief and detailed review-receipt validation (T1/T3/T5/T16/T17) | Host fake transport first; production send only after contract gate |
| S5a ChatGPT + manual transport (`adapters`, doctor) | Native vs printed-link distinction, bounded recovery, verified consumed path/preference cache, usable manual roundtrip (T7/T15) | First useful v2.0 roundtrip; preserve explicit unsupported routes |
| S5b optional repair/public download modules | Exact repair proof, no protection bypass; approved-host redirect/DNS enforcement (T8, G12) | Defer public fetch if unsupported; native/manual remains sufficient |
| S6 client/service portability (`clients`, `services`, capability catalog) | Second client plus Gemini/Claude adapters, versioned profile negotiation and patch_text mode (T6/T14) | One service per packet, shared conformance fixtures; never claim qualification from code only |
| S7 return-pattern adaptation (templates/experience) | Reviewed typed reminders selected from recurring defects, safe activation, hard revocation and measured/unmeasured benefit (T15) | No separate learner service; new prose reviewed separately; baseline request retained |
| S8 qualification (CI, fixtures, client docs) | Both baseline suites on Windows/Linux, 30-episode cheap-driver benchmark, supported matrix, full review and migration receipt (T13/T14) | Release labels match evidence; keep untested cells experimental |

S5a is the v2.0 core/manual checkpoint. Optional public downloads and advanced
learning promotion do not delay it. S6-S8 complete the broader objective. File
module names under new seams are proposed ownership, not an instruction to
refactor all code before producing the first useful result.

## Run each slice through the loop

The following are incumbent commands, unlike the proposed v2 command names.
Fill paths/IDs from the verified local environment; never copy placeholders
literally. Keep state outside Git and use a fresh project mapping.

```text
<python> -B <pinned-runner>/scripts/labor_loop.py --state-root <private-root> --project-id labor-loop-self init --repo <repo> --config-file <reviewed-config.json>
<python> -B <pinned-runner>/scripts/labor_loop.py --state-root <private-root> --project-id labor-loop-self start --request <slice-request.md> --base <full-reviewed-commit>
<python> -B <pinned-runner>/scripts/labor_loop.py --state-root <private-root> --project-id labor-loop-self status
```

Use a reviewed config derived from references/project-config.example.json:
include scripts, references, README, SKILL, agents, docs; no private bootstrap
paths or state. Validation argv uses the known interpreter and the two current
test scripts plus independently frozen slice tests. Never accept worker-proposed
commands or allow-no-checks. Inspect every packet omission; required design/test
context omission stops dispatch rather than silently shrinking the problem.

For every round:

1. Pin accepted baseline and runner; write one request with criteria, allowed
   files, non-goals, failure examples and return contract. Include the prior
   accepted integration and relevant-seam review requirement. Previous findings
   become follow-up stories, not unbounded additions to the current patch.
2. Package and inspect outgoing bytes. Use existing permitted/manual transport;
   bind the dedicated thread from verified user-selected identity. Obtain missing
   destination/action scope only if not already authorized. This planning task
   itself does not authorize sending implementation packets.
3. Upload/send once with marker; record-submission after visible acceptance.
   Poll with bounded scheduler/manual resume. Resolve questions only from frozen
   facts; product/security choices return attention.
4. Download native attachment. For invalid printed link, generate
   `artifact-followup --job-id <id> --reason <typed-diagnosis>` and use the same
   thread within bounds. Before S2, a corrected ZIP goes through fresh private
   bootstrap acquisition state; never overwrite v1's sealed artifact to force it.
5. Intake and integrate through S0's independent gate until replaced. Review
   diff before checks, run trusted checks in isolation, review adversarial cases,
   then bind acceptance to candidate digest. Keep v1 status only as bookkeeping.
6. Integrating owner locally adopts approved scoped changes in a coherent commit,
   reruns owning regression gate, updates CURRENT with proof and open requests,
   and freezes the next runner only after its own cross-version tests pass.
   No remote push, release or installation is implied.
7. Feed observed friction to the experience backlog. Before S7, use reviewed
   request edits recorded with evidence; afterward use its constrained promotion
   pipeline. Start the next bounded round from the newly accepted commit.

Cheap-model recommendation: use a low-cost model for typed action execution and
settled implementation packets once contracts pass. Keep bootstrap, state races,
trust-boundary changes and independent acceptance on a capable reviewer. Measure
total cost per accepted slice, including repair/review; no fixed model-brand
dependency or unverified price ranking is part of the design.

## Handoff and continuation receipt

At each round record: slice ID, baseline/runner/design hashes, project/job IDs,
thread identity (private), phase/condition, submission uncertainty, outstanding
action owner and wake, candidate/check receipt, exact unresolved defect, next
eligible action, and rollback version. Keep secrets and session links out of
public docs. A future timestamp without a scheduled waiter is not continuity.

Planning completion does not mean any slice is implemented. Next action after
this task is S0: commit the reviewed design and establish trusted bootstrap proof.
No calendar ETA is asserted; measure S1a/S1b accepted-round durations before
forecasting the remaining critical path.
