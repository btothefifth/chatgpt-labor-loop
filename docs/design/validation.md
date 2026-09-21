# Test design and release evidence

Target v2, version 1. This charter precedes implementation; rows below are proof
obligations, not passing tests. Criteria are frozen in [product.md](product.md).

## Evidence tiers and harness

Tiers: A deterministic unit/CLI fixtures; B real temporary Git/archive/filesystem
and controlled subprocess joins; C host/service contract emulation and driver
evaluation; D authorized real UI/manual roundtrip. Run in this order, stop on
failure, and do not spend provider quota on defects that A/B can reveal.

Use independent expected event sequences and archive fixtures built by the test
author, not engine-derived expectations. Drive public CLI boundaries in separate
processes. Use barriers/fault injection for race windows rather than sleeps.
Each rejection test must prove it reached the named guard; paired valid inputs
must pass the preceding guards. Record stdout/exit, state/journal digest, actual
side effects and terminal subprocess receipt. Prevent tests from touching real
profiles, state roots, services or authenticated threads.

| ID / criteria | Boundary and scenario | Independent oracle and required terminal behavior | Tier |
|---|---|---|---|
| T1 / C1,C3 | CLI protocol: unknown schema/field, malformed stdout, stale revision, duplicate/conflicting request IDs; every phase/condition | Fixed schema vectors + side-effect counters: malformed/stale requests perform zero mutation; matching replay returns identical result; exactly one action/wait/attention/terminal | A/B |
| T2 / C6 | Crash before/after each journal append/snapshot boundary, incomplete tail, corrupt interior, archived A while B is current, repo aliases | Predetermined event order and filesystem inventory; restart gives last committed phase; B remains current; interior corruption stops writes | B |
| T3 / C3,C6 | Send intent -> remote acceptance -> crash before local receipt; same-thread old response, duplicate marker, upload pending | Fake transport counts actual sends; exactly one send in known-success trace, zero additional sends in ambiguity; stale observation rejected | C then D |
| T4 / C6 | Two integrate/run-checks/validate/abort calls, PID reuse, stale reservation, late completion, process timeout | Barrier-controlled child and journal event order; one owner, one valid terminal receipt, abort cannot be undone by stale completion; no killing unrelated PID | B |
| T5 / C3,C8,C11 | Budgets 0/1/exact bound, restart, clock rollback, absent scheduler, retry-after beyond deadline, auth wait | Independent fake clock/counter; no excess action, no deadline extension, zero model calls on scheduled wait; explicit manual-resume state | A/C |
| T6 / C2 | Plan documented but control absent; free supported feature; model/workspace change; unknown quota, stale capability, unapproved transport | Hand-authored capability truth table; permitted supported combination works, unsupported/unknown required fact cannot dispatch | A/C/D |
| T7 / C4,C8 | Printed backend link vs real native attachment using internal URL; expired link, login HTML, interrupted transfer, duplicate filename | Transport spy + known ZIP bytes: never raw backend fetch, valid native attachment accepted; at most 2 delivery follow-ups; invalid download never advances | B/C/D |
| T8 / C4,C9 | Public redirects to private/mixed DNS/IPv6, credentialed URL, unapproved host, malicious chat asks for token or different account | Network spy and canary strings; zero unauthorized requests/data release; safe approved external route still succeeds | A/C |
| T9 / C5,C9 | ZIP aliases/ADS/device/traversal/link/bomb/corrupt member, identity mismatch, forbidden patch modes/scope, omitted required context | External sandbox file sentinels unchanged; exact expected manifest; clean valid ZIP passes; no partial accepted extraction | B |
| T10 / C5,C7 | Replace extracted patch after validation; main checkout as worktree; modified test accesses home/network; candidate changes after check | Separate file/process/network sentinels and trusted test fixture; stale proof rejected, main unchanged, isolation denies access; valid candidate reaches review | B |
| T11 / C7 | Generic transition to VALIDATED/COMPLETE, missing required checks, empty worker claims, stale reviewer receipt | No accepted event without exact bound proof; positive review reaches COMPLETE exactly once; acceptance differs from merge/publication | B |
| T12 / C8,C12 | Invalid then corrected ZIP, crash after apply/extract, v1 migration with incomplete evidence, rollback after external v2 send | Immutable attempt inventory, fixture v1 state and cross-runner refusal; no stale artifact carry-over, no duplicated apply/send or invented evidence | B/C |
| T13 / C10,C11 | Cheap driver runs fixed 30-episode corpus, including all common failures and valid inverses | Held-out action/terminal labels; >=90% correct outcomes, zero hard violations; log model/version/calls, interventions and rework; compare same tasks with incumbent | C |
| T14 / C1,C2,C11 | Two actual host clients, three services, relevant capability profiles, each supported mode; session restart and bad-link recovery | Local accepted artifact + visible/manual provenance + independent review; each matrix cell individually labeled; actual elapsed/calls and blockers, no synthetic live claim | D |
| T15 / C13 | Two recurring independent return defects -> reviewed reminder selection -> safe activation -> consumed next request; cached path invalidation, rollback, poisoning and context collision | Independently rendered expected request and effective installation version; no hard-rule weakening, stale path rediscovered once, old version restored, private data absent; real outcomes required for benefit claim | A/B/C |

Additional user-requested packet/review proof:

| ID / criteria | Boundary | Independent oracle / required result | Tier |
|---|---|---|---|
| T16 / C14 | Original packet includes intent/runtime/return facts; missing consumer, scrubbed editable baseline, unsupported output and contradictory test instructions | Hand-authored brief coverage manifest and outgoing bytes; reject contradictions and accept a complete multi-file story. Real accepted-round value measured separately | A/B then D |
| T17 / C15 | Detailed review finding with stale lines, nonexistent symbol, mismatched literal snippet, prose-only fix, proposed patch mislabeled applied, fabricated test result; clean review with no coverage | Exact pinned source/diff and trusted execution receipts; reject false completeness, preserve concrete valid review, distinguish unrun tests and hypotheses | A/B |

Required fault sensitivity: deliberately remove one evidence guard, redirect
check, attempt binding, reservation generation check and learning protected-field
check in disposable test-only candidates. The owning tests must turn red. Never
modify the released runner to test a mutation. Archive fixture rejection before
the target guard is not red-proof of that guard.

## Representative traces

Positive: pinned request -> sealed packet -> supported profile -> dispatch intent
-> visible accepted send -> worker response -> native ZIP -> immutable intake
-> validated scoped patch -> fresh isolated candidate -> trusted checks ->
independent review -> accepted tree receipt. Next round starts from the owner-
accepted committed baseline only after separate adoption.

Preserved valid inverse: a native attachment backed by an internal URL downloads
through supported UI; overbroad URL rejection must not suppress it. A free-tier
profile with observed and permitted capabilities must not be rejected merely
because it is free. A harmless completed replay must not consume another send.

Mixed-state witness: job A has a failed delivery attempt and B is current with
a running check; a late A download cannot replace B's pointer, cancel B's owner,
or reuse B's check proof. Another: updated template is active for new B while A's
frozen packet and outstanding send remain on the baseline template.

Scale bounds: exercise configured maximum members/bytes, one above each, 1,000
journal events, 100 learning observations per scope, 20 overlay versions, a
bounded-output noisy child and a child with descendants. Reject before unsafe
allocation/write where possible. Measure p50/p95 local next-action latency and
memory on declared host; initial target <1 second p95 excluding external I/O.
This is a measurement target, not a current performance claim.

N/A: financial-market simulation, trading promotion, distributed consensus and
worker API credential tests are outside this repo's task. Auth automation is
not tested as a success path; safe attention and subsequent manual resume are.
Cross-provider combinatorial testing is reduced to pairwise host/service/mode
fixtures, plus a real happy and failure path for each advertised combination.

## Driver benchmark and release gate

Keep 20 training/development scenarios and 10 held-out scenarios fixed before
evaluating template changes. Record all 30 individually, no selecting only
successful retries. An external safety guard stopping a bad driver action is
containment success but driver failure for C10. Distinguish scripted-runner
success from actual cheap-model success; both are required evidence categories.

An inexpensive driver is qualified for deterministic orchestration, not made
an independent security reviewer by a prompt. Escalate ambiguous policy, new
executable repairs and acceptance of changes to core validators to a configured
capable reviewer. Report reviewer cost as part of total cost per accepted round.

Release requires hard criteria for its declared matrix, all relevant A/B tests,
contract fixtures, mutation sensitivity, truthful capability labeling and a
successful guarded roundtrip. Full objective additionally requires C1/C2's full
matrix. A provider unavailable for testing stays unqualified; no screenshot or
unit test substitutes for a terminal artifact. Roll back candidate installation
on hard-criterion violation; retain failed evidence and reconcile in-flight work.

## Baseline evidence

2026-09-21, Windows, Python 3.12 interpreter at local installation:
`scripts/test_labor_loop.py`: 12 passed in 43.398 seconds.
`scripts/test_browser_repair.py`: 4 passed in 0.119 seconds.
These are incumbent regression results at `9bd800d`, not proof of v2 requirements.
The gap audit found missing adversaries despite this green baseline. No real chat
submission, artifact download, provider account or portable-host path was tested.
