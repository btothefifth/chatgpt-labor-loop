# First implementation request: S1a evidence-bearing acceptance gates

Template status: ready to bind after S0. Do not submit until the coordinator
fills actual job/base/runner identities through the packet generator and verifies
all referenced design files are included from the pinned commit.

Implement S1a only in the provided committed baseline. The goal is to stop
prose-only lifecycle commands from certifying local validation or acceptance,
while preserving a legitimate artifact -> checks -> review round.

Why: the coordinator may be a cheap model following instructions literally.
Deliver the complete gate/receipt/test/documentation join, not a helper or plan.
S1a is the first safety slice; later packets may combine coherent related stories
under docs/design/worker-brief.md to increase accepted value per round.

Local runtime: Windows/PowerShell, Python 3.12, standard-library project; existing
CI declares Ubuntu Python 3.11/3.12. The 12 core and 4 repair baseline tests passed
locally. Your runtime may differ or lack execution tools. Report actual OS/version;
do not claim Windows proof from Linux results. Do not add dependencies, assume
private repo/filesystem access or run network installers. Use portable argv and
path handling. Return complete source/tests and explicit unrun-check reasons if
local-only facilities are unavailable to you.

Before dispatch the coordinator must bind actual base/runner identities, included
file inventory, approved check IDs and S0 isolation-receipt interface. Include
complete labor_loop.py/tests and relevant config plus owning design leaves.
Missing required context blocks dispatch; do not guess missing source. Baseline
commands are python -B scripts/test_labor_loop.py and python -B
scripts/test_browser_repair.py; trusted acceptance/isolation checks are local-only.

Read docs/design/product.md C5/C7, architecture.md evidence/acceptance rules,
validation.md T10/T11, proof-contract.md in full, and implementation/plan.md bootstrap boundary. These are
target contracts; do not claim other v2 functionality already exists.

Allowed changes: scripts/labor_loop.py, scripts/test_labor_loop.py, and directly
affected command/reference documentation. Do not alter browser repair, install
dependencies, replace the journal, add providers, change package policy, weaken
existing tests, change CI secrets, or edit external/private state. Keep public CLI
compatibility where possible; return explicit rejection for unsafe old operations.

Required behavior:

* Generic observations cannot set VALIDATED, INTEGRATING, TESTING, REVIEWING or
  COMPLETE without the owning operation's locally established proof.
* COMPLETE requires a candidate identity and local check/review evidence bound
  to the same base/request/artifact/candidate. Stale, missing or mismatched
  evidence fails closed with an actionable reason.
* Existing positive integration/check/review remains reachable. A skipped check
  does not become passing evidence. Worker validation prose never substitutes.
* Implement the frozen proof.v1 sidecars and inventory/check-set/replay semantics
  from proof-contract.md; do not invent alternative digest policy. Defer
  the full S2 isolation/worktree redesign; explicitly report residual dependence
  on the trusted bootstrap. Do not invent a sandbox claim.

Independent acceptance scenarios: try advancing every phase using generic
transition notes with no artifact/checks; edit candidate after green checks;
replace extracted patch after validation; missing required check; replay a
matching review; and one valid full local round. Tests must reach their named
guard and use independent expected outcomes, not just mirror the implementation.

Review the most recent accepted integration and relevant nearby mechanisms for
intent mismatch, regressions, missing tests and documentation gaps. Record
out-of-scope findings in REMAINING.md rather than expanding this patch. State
explicitly if no actionable issue is found.

Return the exact packet's manifest/job/base identity and required ZIP layout.
Also return REVIEW.md and review.json following docs/design/code-review.md:
revision-bound file/line/symbol locations, literal code, concrete failure paths,
exact implemented/proposed diffs and regression test code/evidence for every
finding; exact coverage and limitations for a clean review. High-level feedback
alone is not a review. Proposed-only patches stay separate from changes.patch.
changes.patch is canonical. Provide concise SUMMARY/INTEGRATION/REMAINING/
VALIDATION and distinguish checks actually run from proposed checks. Attach the
ZIP using the chat's native downloadable attachment. Do not provide a printed
backend/API/session link or publish the package to public hosting. If no native
artifact can be delivered, report that fact without claiming delivery complete.

The coordinator will validate using a separately pinned trusted runner and
tests. Your patch cannot approve itself or change that review authority.
