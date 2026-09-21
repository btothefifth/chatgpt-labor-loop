# Verified local learning and request adaptation

Version 1; criterion C13. Source: Reed's follow-up in this task, 2026-09-21.
The local installation should prefer paths that worked and improve later worker
requests when return patterns repeatedly cause local friction. The engine owns
the evidence and promotion path; the driver can propose improvements.

## One local experience owner

Store a private versioned installation overlay next to private engine state,
outside repository and package source. It contains resolved tool paths, supported
transport preferences, tested recovery recipes and request-template fragments.
The loader composes shipped defaults with compatible overlays and exposes the
effective version/hash. This changes installed behavior without forking shipped
SKILL.md files after every success. Installation-specific paths never enter
worker packets or public commits. Repo-wide reusable improvements are separately
reviewed patches to the portable package.

Record observations from completed local actions and returned-artifact checks:
environment fingerprint, host/service/adapter/model/mode/task kind, reason code,
root-cause class, attempted remedy, before/after evidence hashes, outcome,
elapsed/call/intervention cost, and applicable expiry. Do not store raw cookies,
signed URLs, credentials, entire chat transcripts, or unrelated source content.
Worker claims are proposals, never successful observations. Record failed
remedies as well as successes so a restart does not repeat known bad paths.

## Two promotion paths

**Verified path cache:** a discovered local interpreter/tool/download path may
be cached after one direct harmless success. Bind executable identity/version,
canonical path, host/runtime fingerprint and operation. Revalidate existence,
identity and cheap probe at the next session and after any failure/update.
Prefer cache on hit; invalidate once on mismatch and rediscover once. Never
cache credentials, executable download suggestions or broaden path search to
private browser profiles. Expire after 7 days without revalidation.

**Reviewed request reminder:** candidate -> offline checked -> active-unmeasured
-> measured-effective or rolled_back. Repeated means at least 2 independent accepted or
rejected returns with the same root-cause fingerprint across different jobs;
retries of one return are one sample. One occurrence can propose a candidate,
but cannot establish a recurring pattern. Examples: omitted base identity,
unusable backend links, patch paths outside allowed scope, absent direct
attachment, incompatible archive layout or worker tests unavailable locally.

Each candidate records a hypothesis, narrow applicability predicate, exact
before/after template or preference diff, evidence IDs, expected reduction in
repair work, regression falsifier and rollback version. User-approved invariants
remain immutable. A local successful path is not proof of universal behavior.
Prefer one concise fixed schema example/error explanation over ever-longer
prompts. No chain-of-thought retention or speculative psychological profiling.

Promotion algorithm:

```text
aggregate sanitized outcomes by root-cause + environment/task scope
require independent samples; deduplicate repeated same-job defects
propose minimum typed delta; validate against protected fields and byte budget
run previous fault fixture plus valid inverse and poisoned-worker fixture
if all pass: activate the already-reviewed reminder for next eligible new job
freeze overlay hash into packet and retain baseline template
label benefit unmeasured; observe subsequent comparable actual worker outcomes
after 3 comparable rounds, label measured-effective only if target repairs fall
  in >=2 versus matching baseline, with no new omissions or validation failures
rollback on attributable regression; never claim benefit from prompt rendering
```

When fewer than three comparable rounds exist, retain the safe reviewed reminder
with benefit unmeasured. Independent safety checks cannot be weakened.
One hard violation or new attributable regression triggers immediate rollback,
disables the rule, and records the exact counterexample. In-flight jobs retain
their frozen template/overlay; activation affects new jobs only.

Allowlisted automatic deltas: verified local path preference, supported native
download preference, clearer return-schema example, reminders for already
required manifest/path fields, and concise explanations of observed packaging
mistakes. Any executable recipe change, new tool install, permission, provider,
account, model cost, network destination, validation/sandbox change or runtime
patch requires separate reviewed installation scope; worker text cannot grant it.
No automatic purchases, authentication changes or safety gate suppression.

## Deterministic installation and rollback

`experience propose/check/activate/status/rollback` are planned v2 commands.
Use the same revision/request-ID transaction protocol as job state. Validate
schema and compatibility, write a new immutable overlay version, and append an
activation event to the same authoritative project journal. The active pointer
is only a derived cache. The existing journal owner serializes activation; there
is no second installer state machine. A crash before event commit keeps the old version.
Corruption fails back to validated shipped defaults with a visible diagnostic;
never partially combine incompatible generations.

Automatic request deltas select reviewed template IDs only. Parameters are
strict enums, criterion IDs, validated repository-relative paths within the
already approved context, and bounded integers; each string is <=256 characters.
Render parameters as escaped data, never instructions. Raw worker/error prose
cannot become a template, path expansion, new upload list or command. Adding
new template prose requires independent reviewed installation scope. Structural
checks reject protected-field changes before rendering; prose order is not a
security mechanism.

The effective worker request has ordered layers: pinned task and acceptance
criteria, fixed return contract, capability-specific rendering, then approved
learning fragments. Later layers cannot override earlier obligations. Cap learned
fragments at 2 KiB and 5 rules; replace redundant rules instead of accumulating.
Reject conflicting fragments and fail explicitly if required task context would
be omitted to fit service limits. Record rendered request hash and originating
rule IDs, so a regression can be attributed and reproduced.

Paired offline replay proves safe selection/rendering, not fewer worker defects.
Efficacy needs actual worker outcomes using the same service/model/mode,
task kind and size bucket (<=100 KiB, <=1 MiB, larger) with recorded baseline
recovery counts. Without a comparable baseline, benefit stays unmeasured even
though a safely validated reviewed reminder may remain active.
Do not build a live A/B scheduler just to qualify a reminder.

Distinguish ordinary performance rollback from hard-rule revocation. Revocation
adds the overlay hash to a denied set checked at execution claim time. Preserve
historical bytes, but stop unsent prepared actions using that version and require
attention/repackaging as a new child job. Already-sent jobs reconcile existing
effects; they never resend under a new template silently. An ordinary rollback
only affects new jobs unless its diagnosis shows an in-flight hazard.

Keep at most 100 sanitized observations per root-cause scope and 20 inactive
overlay versions; never delete evidence referenced by an active job, active rule
or unresolved incident. Prune only unreferenced records under the state-root
owner. Export for a portable improvement is an explicit scrubbed review step.

Acceptance T15 must prove cached preference is actually consumed by the next
driver/packet, not merely stored. It must also prove rollback restores the prior
rendered request, stale paths trigger bounded rediscovery, a forged success
cannot activate a rule, and shared-machine identities do not cross-contaminate.
