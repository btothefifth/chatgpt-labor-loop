# Portable Labor Loop product contract

Version 1; objective LL-PORTABLE-1; source: Reed's 2026-09-21 request.

BMAD classification: substantial. Client/service boundaries, untrusted code,
crash recovery, concurrency, and self-hosted improvement need an explicit
contract to prevent inexpensive drivers from inventing policy.

## Outcome and scope

A local driver requests one bounded change, follows machine-produced next
actions, delegates through a supported subscription chat UI, retrieves the
result, validates it in local isolation, and obtains an evidence-bound review.
It can stop and resume without losing work or duplicating a remote submission.
Successful completion means an accepted candidate with local proof, not a merge
or publication. The integration owner separately adopts accepted changes.

The engine must not depend on Codex, Cursor, Claude Code, or any model's hidden
reasoning. A host with a supported shell can run the core. Browser operations
require a declared, tested transport; absence is an explicit unsupported result,
not a claim that all hosts can operate every browser. Manual transport is a
first-class fallback with the same local validation obligations.

Service adapters initially cover ChatGPT, Gemini, and Claude subscription chat.
Plan, selected model/mode, account policy, remaining quota, artifact generation,
and current UI availability are separate dimensions. A paid plan is not proof
of a usable capability. The product must explain both unsupported combinations
and capabilities that were unavailable only in this session.

The first useful milestone is deterministic v1 recovery and truthful next
actions. Portability follows a stable core; three thin wrappers around today's
informal instructions would not achieve the objective.

Non-goals: provider API execution, authentication automation, defeating product
controls, automated purchases/upgrades, public artifact hosting by default,
arbitrary plugin loading, background unlimited work, and replacing Git/review
authority. Local model inference itself is supplied by the host, not this repo.

## Personas and required journeys

* Inexpensive driver: run status/next, execute the one approved typed action,
  record its result, and repeat. Never compose recovery shell from chat text.
* Maintainer: diagnose a missing thread, broken browser bridge, expired artifact,
  changed UI, or limit with a bounded redacted evidence bundle and exact next step.
* Multi-service user: select an allowed profile and task mode; see why it is
  eligible, unavailable, stale, or incompatible before uploading.
* Reviewer: inspect immutable inputs, patch, local evidence, residual work, and
  changed-file scope; reject stale evidence even when all recorded tests passed.

Required journeys: successful code-change round; wrong-account/thread recovery;
crash after send; backend-link recovery; expired native attachment regeneration;
quota wait and resume; unsupported artifact mode; client handover mid-job;
failed local test repair; returned ZIP attempting to change the loop's own
validator; and migration/rollback of an existing v1 job.

## Objective criteria (frozen before architecture)

All criteria are v1. H is a hard constraint, O an optimization target. Priorities
are P0 before external execution, P1 before portable release, P2 improvement.
Any change must retain its previous wording and explain new evidence in review.md.

| ID | Source / priority / kind | Measurable acceptance and cheapest falsifier | Owner / evidence and rejection |
|---|---|---|---|
| C1 | User / P1 / H | Two distinct client applications on a supported machine drive the same pinned job protocol to accepted candidates with equivalent receipts; inject a client-specific assumption | Core + client adapter; T1/T14. Reject portability claim for untested combinations |
| C2 | User / P1 / H | ChatGPT, Gemini, Claude each pass their declared task mode end to end or truthfully refuse unsupported mode; unknown tier never grants permission | Capability resolver; T6/T14. Unsupported is honest coverage, not successful service qualification |
| C3 | User / P0 / H | Every reachable nonterminal condition has one typed next action, a due time, or a named attention owner; malformed/stale commands fail closed | Protocol; T1/T3/T5. Reject prose-only recovery and unbounded retry |
| C4 | User + existing trust boundary / P0 / H | Zero hidden-endpoint, credential, private-host, or protection-bypass operations; native attachments remain usable through supported UI | Transport; T7/T8. Any boundary escape rejects release |
| C5 | Existing local authority / P0 / H | Zero accepted ZIP escape or unreviewed command/scope execution; only pinned approved checks run inside execution isolation | Intake + validation; T9/T10. Any escape rejects release |
| C6 | Correctness / P0 / H | Crash/replay/concurrent callers cannot duplicate authorized dispatch or overwrite another job's current pointer | Journal + dispatch; T2/T3/T4. Unknown external outcome blocks resending |
| C7 | Existing review semantics / P0 / H | COMPLETE binds exact candidate tree, base, request, artifact, checks and reviewer; edits invalidate proof | Acceptance; T10/T11. False completion rejects release |
| C8 | User robustness / P0 / H | Each supported fault reaches recovery or actionable attention within configured attempt/deadline bounds; corrected artifacts get a clean attempt | Recovery; T5/T7/T12. No endlessly re-requested same link |
| C9 | Privacy / P0 / H | Packet preview covers every outgoing byte; state and diagnostics contain no credentials; no provider switch or public upload outside approved scope | Packaging + policy; T8/T9. Secret canary leakage rejects release |
| C10 | Cheap operation / P1 / O | >=90% of 30 fixed offline fault episodes reach correct terminal/attention state with no maintainer reinterpretation; zero hard violations, <=2 driver calls per state change excluding review | Driver harness; T13. Below threshold retains experimental label |
| C11 | Efficiency / P1 / O | Deterministic waiting uses zero model calls; collect accepted-round time, calls, intervention count and rework against incumbent on same tasks | Harness; T13/T14. No fabricated cost savings or speed SLA |
| C12 | Maintainability / P1 / H | One state authority, no executable discovery downloads, versioned adapters and lossless reversible migration; old runner accepts its own unchanged state | Core + migration; T12. Unknown schema/adapter refuses writes |
| C13 | User follow-up / P1 / H | Verified local working paths and recurring worker-return defects produce scoped versioned installation/request improvements; poison, stale evidence and regressions cannot silently promote | Learning owner; T15. Attributable regression rolls back; benefit stays unmeasured without actual comparable outcomes |

Criteria added from subsequent explicit user requests:

| ID | Source / priority / kind | Acceptance and falsifier | Owner / proof |
|---|---|---|---|
| C14 | User original-request quality / P1 / H | Brief communicates intent, local/worker runtime limits, complete seam context, validation and return format; maximize coherent accepted work per pass. Missing required context or contradictory instructions blocks dispatch | Request renderer; T16 and actual accepted-round metrics |
| C15 | User detailed code reviews / P1 / H | Every actionable finding has revision-bound lines, literal code, concrete failure, exact proposed/applied edit and regression proof; clean review lists exact coverage and limitations | Review receipt; T17. High-level-only feedback cannot satisfy review completeness |

Runtime signals: phase, reason code, state revision, attempt, next action,
next due time, deadline, retry budget remaining, evidence fidelity, and review
status. Never expose signed URLs, thread content, account identity, or local
paths in public summaries by default.

## Release scope and tradeoffs

Hard constraints are never traded for fewer model calls. Conservative attention
is preferable to duplicate send, but must include a reproducible diagnostic
and exact resumption condition. Keep one CLI and one protocol; add MCP or other
wrappers only where a host demonstrably needs them. Do not build a central
account manager or a general autonomous browser framework.

v2.0 targets one qualified host/service path plus manual transport and v1
migration. Full LL-PORTABLE-1 qualification needs two distinct client applications and all
three service adapters tested on real eligible accounts. Unavailable accounts
remain explicit release blockers for that matrix cell, not simulated successes.
