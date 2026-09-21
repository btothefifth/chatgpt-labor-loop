# Recursive adversarial, intent and simplification review

Objective LL-PORTABLE-1 v1; 2026-09-21. Scope is the entire active document graph
from CURRENT.md. Runtime remains baseline v1. Documentation review is not
implementation validation or a claim that adversarial defects cannot remain.

## Method and bounded stop

Freeze user criteria first, inspect incumbent code, trace constructive behavior,
then challenge intent, failure boundaries, simplification and proof cost.
After each material finding, revise the owning leaf and rerun the affected
end-to-end trace. Independent reviewers receive the original user objective and
current files, not just the author's conclusions. Stop when the next pass adds
no material counterexample or useful simplification to the current plan; defer
implementation-specific policy-free details to the owning slice with its gate.
Reopen for a new counterexample, changed provider/host contract, failed fixture,
or user intent change. Do not interpret a fixed number of reviewers as proof.

Review lanes: root owns all files/integration and constructive traces; one
read-only agent audited code and then state/security/design; another researched
official provider sources and independently challenged intent/simplification.
Short isolated context, no worker chat messages or shared mutation. Available
disk headroom before delegation was ~24.9 GB; no large test/build artifacts or
full-history agent forks were required.

## Intent trace and captured requests

| User intent | Owning rule / implementation | Falsifier |
|---|---|---|
| This thread tracks chatgpt-labor-loop | Repo-local CURRENT and plan; thread named for this repo | Work changes an unrelated repository instead of the target repo |
| Cheap model is hand-held | C3/C10; typed next action, doctor, fixed recovery; S1/S4/S5 | Model must invent shell/URL/repair policy after a routine fault |
| Robust thread and artifact access | C4/C6/C8; single-use send claim, native attachment classification, immutable corrected returns | Duplicate send or inaccessible printed backend link counted as result |
| Client application independence | C1; core CLI + client/transport seams; S6 | Requires Codex tool names inside service-independent state |
| Chat service and tier independence | C2; observed capability/profile/task mode; S6 | Paid label treated as proof, free feature suppressed, unavailable ZIP inferred from document export |
| Retain successful local paths | C13; verified installation overlay consumed by driver; S5a | Cache is written but next loop rediscovers or ignores it |
| Improve requests from recurring returned defects | C13; evidence -> reviewed template selection -> safe activation -> consume/rollback; S2a/S7 | Repeated same-job error falsely counted as independent evidence or prompts grow without benefit |
| Full BMAD and recursive adversarial review | Criteria, architecture/leaves, tests, gap register, packets, this review | Missing criterion-to-real-consumer proof or unreviewed leaf |
| Explicit intent and design simplification review | This table and ownership reduction record below | Safe but oversized framework displaces early useful recovery |
| Plan implementation using loop itself | S0 trusted bootstrap then pinned worker packets and independent local acceptance | Candidate validator approves its own changes |
| Get more valuable, easy-to-integrate work per request | C14; worker-brief.md, runtime compatibility, complete seam context, coherent outcome sizing; S4/S5a | Worker invents missing APIs, certifies wrong runtime, or returns a disconnected helper |
| Extremely detailed code review receipts | C15; code-review.md and enriched first packet | Generic feedback lacks pinned lines, literal edits or falsifying regression evidence |

## Pass 0: baseline and constructive trace

Inspected README, SKILL, references, current scripts/tests and CI at pinned HEAD.
Independent source audit identified G1-G14 in plan.md. Ran 12 core and 4 repair
tests successfully; proposed adversarial gaps are not covered by those results.
Constructive trace follows packet -> send -> native download -> scoped immutable
candidate -> local checks -> independent acceptance -> next baseline. The
existing references are incomplete but compatible: retain them as explicitly v1,
and give v2 one current pointer instead of silently claiming it already works.

Criteria C1-C12 were written before the architecture. C13 was added on Reed's
follow-up with no weakening of other criteria. Reed's later review clarification
adds explicit intent/simplification proof obligations to this record.

## Pass 1: independent counterexamples and revisions

| Counterexample | Revision | Retest obligation |
|---|---|---|
| Two drivers invoke same prepared send before either records receipt | Single-use engine-mediated execution claim; uncertain claim cannot expire into resend | T3 pre-send barrier |
| Two poisoned returns teach malicious prompt text | Automatic learning selects reviewed template IDs with constrained escaped parameters; new prose separately reviewed | T15 hostile defect fixture |
| Revoked overlay still has a prepared unsent job | Denied overlay hash checked at claim; unsent job requires attention/repackage | T15 revocation race |
| Human isolation waiver produces indistinguishable green receipt | Diagnostic-only `unisolated-owner-waiver`, cannot satisfy C5 or qualified COMPLETE | T10 missing-isolation positive/negative |
| Pinning broken v1 makes self-host bootstrap look safe | S0 independent intake/worktree/digest/isolation proof and trusted harness; v1 COMPLETE not authority | S0 synthetic adversaries |
| ZIP-to-text mode switch contradicts frozen job request | Mode change creates child job; no silent new-mode attempt | T6/T12 |
| Download attempt unclear to worker | Separate return_generation in manifest from local acquisition_id | T7/T12 late old return |
| Three easier tasks falsely prove learning benefit | Paired offline replay plus matching live stratum; mark unmeasured without comparable baseline | T15 efficacy |
| Two clients mistaken for two machines | Explicit client/machine/transport terminology; one-machine sequential handover in scope | T14 |
| Learning leaf omitted from current read chain | Add learning and provider evidence to CURRENT | Documentation link/read audit |

## Simplification decisions

| Candidate reduction | Decision and invariant retained | Falsifier / residual cost |
|---|---|---|
| One core CLI instead of separate client engines | Adopted; one state/review authority, thin wrappers only | Two clients disagree on same protocol fixture |
| One journal with derived snapshots instead of multiple authoritative JSON stores | Adopted; recoverable commit boundary | Crash reveals divergent accepted phases |
| Merge all browser details into generic engine | Rejected; service identity/DOM and host APIs change independently | A provider selector update should not require core policy changes |
| Remove capability resolver and use plan labels | Rejected; entitlement, observed controls and permission differ | Paid unavailable / free available inverse cases |
| Remove quarantine/generation separation | Rejected; corrected bytes and delayed returns need immutable identity | Old artifact accepted as new correction |
| General self-modifying prompt/code agent | Replaced with verified path cache and typed template overlay | Poisoned worker text enters installed instructions |
| Add MCP server and central account scheduler immediately | Deferred; shell CLI and one project owner suffice initially | A real client cannot use CLI and demonstrates need |
| Public link downloader before useful v2 release | Deferred; native/manual artifact path is enough for S5a | Eligible provider can only deliver approved public URL |
| Automated upgrades, provider switching or public hosting | Excluded; not needed for user objective and expands authority | Explicit future user requirement would reopen |
| Blanket rewrite before vertical slices | Rejected; S1a evidence gates and S5a usable checkpoint precede full portability | Safe incumbent can no longer accept a bounded slice |

Irreducible mechanisms each have a named failure witness above; no additional
daemon, queue, credential store, universal browser framework or plugin marketplace
is planned. Performance/cost benefits remain hypotheses until T13/T14/T15.

## Evidence and outstanding decisions

Design validation includes independent source audit, provider documentation
research, constructive trace, adversarial revisions and relative-link checks.
Actual implementation proofs remain T1-T17, with detailed scope in validation.md.
Provider account access, authorized automated transport, execution sandbox and
cheap-driver selection are environment-dependent S0/S6 qualification inputs,
not hidden assumptions. Missing inputs must not cause guessed actions.

## Pass 2: intent and simplification re-review

Both independent reviewers found that the pass-1 boundary fixes were present.
They challenged delivery order and uncovered a first-packet ambiguity. Revisions:

| Finding | Change / preserved obligation |
|---|---|
| S1a asked a cheap worker to invent proof semantics, while later slices owned schema/digests | Added proof-contract.md: additive sidecars, complete candidate inventory, scratch exclusion, exact required check set, reviewer binding, replay and legacy rejection. S3 owns state schema migration, not sidecars |
| 'Relevant untracked inputs' could omit executable source or count harmless outputs | Freeze all base files plus approved additions/deletion tombstones, reject undisclosed inputs, require explicit disjoint output roots |
| Learning delayed behind unrelated provider account qualification | Move defect observations to S2a, consumed path cache to S5a, reminders S7 dependent on S5a but independent of S6 |
| S0 included cross-platform release work unnecessary for first local proof | Keep local bootstrap safety; move Windows/Linux CI expansion to S8 |
| Low-risk reviewed reminder needed too much experimental machinery | Safe activation after fixed validation; label benefit unmeasured until comparable actual outcomes. No separate learner daemon or live A/B scheduler |
| Overlay active pointer introduced a second state authority | Immutable overlay bytes plus activation event in existing journal; pointer is derived |
| Weekly documentation expiry could block a proven live path | Stale entitlement becomes advisory; current controls and permission still required |
| Unknown numeric quota could block nearly every subscription | Permit one bounded authorized task attempt if required controls/features exist; known exhaustion still waits |
| Two-host wording exceeded client-independence intent | Require two client applications on a supported machine |

The first usable shape is now one CLI/journal, one host transport plus manual
fallback, one service adapter, exact local evidence gates, bounded actions, and
a small consumed path cache. Additional providers and request-reminder learning
can proceed independently after that join. Public fetching/runtime repair remain
optional. Offline rendering tests establish safety/selection only, never actual
worker quality improvement.

## Pass 3: targeted convergence and new user requirements

The state/proof reviewer found one final literal-contract issue: pre-materialization
artifact candidate hash is null while later receipts require a concrete digest.
proof-contract.md now explicitly permits that transition and requires equality
across candidate/check/review. Both reviewers then reported no remaining material
intent/simplification blocker in the reviewed graph. This is bounded design
convergence, not implementation or runtime proof.

Subsequent user requests reopened only the request/review leaves: C14 adds
high-value coherent work selection and explicit local/worker runtime facts;
C15 requires revision-bound literal-code review receipts. The same request
renderer consumes these contracts; no extra agent service or state authority
was added. The first packet now contains local limitations, worker-proof limits,
context prerequisites and detailed review instructions. Targeted review of these
new leaves found and resolved these final joins:

* Remote partial-context reviewers bind packet/patch/reviewed-file hashes; only
  the local coordinator binds the full canonical candidate digest.
* Editable paths, read-only context and proposed-only new test locations are
  distinct. Useful out-of-scope findings are retained without expanding apply scope.
* Privacy overrides literal snippet delivery; missing required private coverage
  remains local/unresolved, never fabricated or disclosed to complete a form.
* review.json is structural authority, REVIEW.md its readable rendering; semantic
  judgment remains independent. Split receipts still obey total artifact limits.

The reviewer found no need for further architecture expansion. These local fixes
preserve the user's detailed-review requirement while keeping S1a bounded and S4
the owner of machine enforcement. Root rechecked the affected producer/carrier/
consumer joins after applying them. No known code-driving policy ambiguity blocks
the planned S0 bootstrap; environment qualification and implementation proof
remain explicitly pending.

## Final documentation verification

Relative links, fenced blocks and trailing whitespace checked across all 15
Markdown files in the changed documentation graph; no errors. Git diff whitespace
check passed for tracked changes. Both baseline test suites remained unchanged
and had passed earlier (12 + 4). Only documentation changed; no worker message,
runtime patch, installation, account action, remote publication or implementation
qualification occurred. No claim of reduced costs or improved worker quality has
yet been measured. Next authorized phase when implementation is requested: S0.
