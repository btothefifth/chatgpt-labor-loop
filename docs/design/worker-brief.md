# High-value worker brief and integration-ready return

Version 1, criterion C14. Source: Reed's request to communicate specific intent,
local limitations and runtime differences up front, so each chat pass performs
substantial useful work and returns an easy-to-integrate result.

## Optimize accepted value per round

Choose the largest coherent outcome that fits known worker capabilities,
context/file limits and local proof budget. Prefer a complete producer-to-consumer
change including tests, failure handling and documentation over a helper-only
patch. Bounded scope does not mean one small file. Combine related stories when
they share a frozen contract, baseline and independent acceptance boundary;
split for unresolved policy, different authority, incompatible runtime proof or
separate rollback. A long unrelated wishlist is not a valuable batch.

Track accepted criteria per round, integration/rework minutes, usable patch rate,
clarification turns, delivery retries, local first-pass test rate and elapsed time.
Do not optimize lines changed, response length or nominal token savings. After
two high-repair rounds, refine context/scope from root causes before shrinking
every task or switching models. If a worker repeatedly has spare usable capacity,
combine the next compatible stories. Keep independent review cost in the budget.

## Required outgoing brief

Render sections from pinned facts and reviewed configuration. Missing product
choices require explicit resolution; never infer them from stale thread history.
Unknown runtime facts get an unknown label and safe verification path. The packet
is self-contained even when sent to a persistent thread.

| Section | Required content / omission consequence |
|---|---|
| Outcome and intent | User problem, why it matters, before/after examples, priorities, non-goals, preserved behavior and unacceptable shortcuts. Missing policy requires clarification |
| Baseline and authority | Job/base/repo identity, contract versions, changed-path scope, protected/read-only context, integration owner. Do not assume private repo/main access |
| Architectural placement | Real caller/producer/consumer, states, interfaces, data formats, relevant neighbors and dependency order. Enough surrounding code for a complete join |
| Local runtime | Target OS/architecture, interpreter/toolchain versions, shell constraints, dependency policy, case/newline/path rules, test framework, isolation and network limits; source/check date |
| Worker runtime | Observed provider file/output/tool capability and explicit unknowns; execution, internet/repo access and persistence. Worker declares what it actually used |
| Integration | Canonical patch format, exact scope/base, no unrelated cleanup, modes/line endings, required manifest/summaries, migration/rollback and output mode. Full files are optional review aids |
| Validation | Approved argv/check IDs, prerequisites, local-only checks, independent outcomes/fault cases, baseline results and known failures. Separate worker-run from coordinator proof |
| Prior friction | Relevant rejected approaches, recurring return defects, reviewed reminder IDs, prior accepted integration and nearby risks. Reopen decisions only with a counterexample |
| Work/completion | Ordered deliverables, must-haves vs permitted related improvements, clarification boundary, partial-work reporting and strict delivery instructions |

No credentials or machine-specific absolute paths where semantic tool aliases or
relative paths suffice. Actual local interpreter paths stay in coordinator config;
the brief gives versions/argv semantics. Runtime facts do not authorize installs,
browser-profile access, external writes or deployment. Suggestions are proposals.

## Runtime compatibility table in every packet

| Surface | Local target | Worker environment | Required behavior |
|---|---|---|---|
| OS/filesystem | Observed OS, case/path constraints | Declared Linux/Windows/unknown | No absolute paths, case aliases, ADS/device names; test target semantics |
| Interpreter/dependencies | Pinned minimum/version, approved dependencies | Tested versions or unavailable | Standard library unless approved; no silent installer |
| Commands | Argv, shell if needed, cwd and scratch policy | May lack PowerShell | Return portable source/tests and mark target-only checks unrun |
| Network/repo | Snapshot authoritative, local network denied by default | Access may be unavailable | Use supplied context; never fabricate fetched code/version evidence |
| Chat artifacts | Negotiated input/output format | Confirm actual creation/download support | Deliver bytes in chosen mode or report delivery blocked |

Linux execution cannot prove Windows behavior. Worker tests are useful evidence,
not substitutes for local trusted checks. Without code execution the worker should
still deliver complete source, meaningful tests and a precise unrun-check list;
do not spend the round inventing an execution environment. Missing source must
be identified by exact path/interface; never invent the current API.

## Context inventory and preflight

Select context from the real seam: owning contract, affected functions, callers,
data producers/consumers, adjacent tests, config/schema and dependencies. Include
full small files; excerpts carry path/base hash and full syntactic boundaries.
Excerpts are read-only context: omitted surrounding bytes are not a safe patch
baseline. Include file hashes, omissions and redactions. Required omission blocks
dispatch. Scrubbed source is not byte-exact patch context: exclude it from changed
scope or provide an explicitly mapped safe exact source fixture.

Rendering precedence: user outcome -> frozen architecture/acceptance -> runtime
and integration facts -> task/output mode -> reviewed reminders. Preflight rejects
contradictions: unsupported required ZIP, Linux worker told to certify Windows,
scope excluding required consumer, or mandatory tests requiring unavailable
secrets. Print a short value/scope/context/limits/mode summary for the coordinator.

Do not send the whole BMAD corpus each round. Select owning leaves and necessary
hard rules, with criterion-to-included-rule coverage. Never silently truncate a
contract. Keep the short installed driver guide separate from rich worker packets;
the cheap driver should follow typed actions, not repeatedly reinterpret design.

## Worker instructions and result

Ask the worker to inspect the supplied seam, briefly state its understanding,
then implement within the same run. Do not stop at a plan unless material
ambiguity blocks implementation. Use available compatible execution tools,
review the final diff and repair bounded in-scope defects.

Review the latest accepted integration and relevant recent seams. Repairs needed
for current acceptance belong in scope; unrelated valuable findings go in
REMAINING with evidence, priority and proposed next slice. Optional improvements
must stay within approved paths/criteria and not displace required proof.

Require one artifact in the negotiated mode:

* changes.patch against exact base, no encoded apply script, private absolute
  paths or conflicting alternative patch representations;
* manifest with job/base/return-generation identity and changed files;
* SUMMARY mapping each criterion to delivered files/behavior and outcome;
* VALIDATION with actual commands/runtime/results and checks not run with reasons;
* INTEGRATION with ordered local steps, compatibility/migration/rollback notes;
  worker-proposed commands do not become approved commands;
* REMAINING with residual work, assumptions, contextual-review findings and
  expected local friction; START_HERE points to patch and summary.

Empty patch requires explicit no-change reason and does not satisfy implementation
criteria. Partial work must state unmet criteria; no placeholder implementation,
invented logs, or summarized code that was not delivered. Local owner may salvage
reviewed partial changes without declaring the round fully complete.

Prefer native attachment. If unavailable, report the limitation and preserve
completed work in the thread. Never substitute a printed backend/API link or
unauthorized public upload. The coordinator owns delivery recovery.

## Ownership and proof

C14 belongs to request rendering/preflight in S4/S5a; apply it manually in the
bootstrap first request. S7 feeds approved reminders into this same renderer,
not another prompt generator. T16 drives packet creation with conflicting runtime
facts, missing consumer, scrubbed editable baseline, unsupported output and a
valid coherent multi-file story. Use an independently authored brief coverage
manifest. Only locally accepted criteria and measured integration effort prove
valuable work per pass; packet schema compliance alone does not.
