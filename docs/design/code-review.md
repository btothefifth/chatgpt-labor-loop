# Detailed code-review receipt contract

Version 1; C15. Source: Reed requires extremely detailed code-review receipts
with line numbers and literal code changes, not high-level design feedback.
Applies to the remote worker's prior-integration/current-change review and the
independent local acceptance review. Design-only review may cite document
sections, but does not count as a code-review receipt.

## Identity and coverage

Return REVIEW.md plus review.json in each implementation/review artifact. Remote
reports bind job, supplied base/packet identity, canonical patch hash, exact
reviewed-file hashes, reviewer role, request and contract versions. A worker
with partial context or no execution tools must not invent the full local
candidate digest. The coordinator independently materializes the full tree and
binds the remote report to its canonical candidate digest in local acceptance.
review.json is structural authority; REVIEW.md is its readable rendering/index.
Compare IDs, dispositions, source references and literal snippets mechanically;
semantic narrative agreement still needs independent review. During v1 bootstrap they
are additional files alongside the existing required return layout; S4 validates
the extension without silently changing older manifests.

Coverage records every changed file, relevant caller/consumer and examined test,
with exact revision, source hash, function/class/symbol, one-based line ranges,
review dimensions examined and limitations. Explicitly identify unreviewed scope
and reason. 'Reviewed all code' is not an acceptable coverage statement. A clean
review has findings=[], concrete coverage and examined invariants/failure paths;
it cannot substitute generic approval for coverage. For source absent from the
packet, name it as unavailable, not reviewed.

Privacy takes precedence over literal-code completeness. Mark redacted/unavailable
coverage and keep any sensitive detailed review local. Never send raw code just
to satisfy this format. Safe mapped fixtures are illustrative, not proof against
original bytes or an editable baseline. Unresolved required coverage blocks
acceptance rather than producing invented snippets or a false clean review.

## Every actionable finding must contain

1. Stable finding ID, severity, category, status and affected criterion. Status:
   observed-defect, reproduced-defect, hypothesis-needs-proof, proposed-fix,
   fixed-in-return, or verified-fixed-locally. Keep historical status transitions.
2. Repository-relative file path, exact base/candidate revision or content digest,
   symbol, and one-based inclusive line start/end. State whether coordinates
   refer to before or after. New/deleted code needs the appropriate snapshot;
   never cite line numbers from a different revision.
3. The actual literal relevant code, with surrounding lines needed to understand
   its guard/caller/state. No ellipsis inside the causal expression or replacement.
   Link larger complete source in the packet and give its hash when necessary.
4. A concrete trigger and reachable call path, input/state/preconditions,
   expected behavior, actual behavior and consequence. Identify why existing
   tests miss it. A concern with no concrete witness is an explicit hypothesis.
5. Exact remediation as a unified diff against the identified snapshot, or
   before/after literal code plus exact insertion/deletion location. Include
   signatures/imports/call-site changes needed to apply the edit. 'Add a check',
   'improve error handling' and similar prose alone are insufficient.
6. The minimal regression test: exact test file/symbol/location, literal test
   code or diff, independent oracle, intentional fault, expected red/green
   outcome, valid inverse and relevant adjacent behavior. Distinguish tests
   actually run from proposed tests; include argv/runtime/result/evidence hash
   only when observed. Never invent terminal logs or line locations.
7. Integration impact: changed interfaces/data/state, migration/rollback if
   needed, compatibility with supported runtimes, affected neighboring callers,
   dependencies and remaining uncertainty. Say none with reason when applicable.
8. Disposition: fixed in canonical patch with hunk reference; proposed only with
   standalone suggested patch; deferred with rationale/owner/next action; or
   rejected with concrete counterevidence. Local reviewer independently verifies
   any fixed claim against actual candidate bytes.

The level of detail applies to each actionable issue; do not collapse a group of
distinct failure mechanisms into one broad recommendation. Root-cause duplicates
may reference one finding but must enumerate affected locations and remediation
coverage. For cross-file changes show all necessary hunks and matching tests.

## Literal-edit ownership and safe integration

Only changes.patch is canonical for integration. For an already implemented
finding, REVIEW cites its actual hunk plus before/after code and must match the
delivered candidate. For an unimplemented finding, put the suggested unified
diff in `evidence/proposed-fixes/<finding-id>.patch` and label it PROPOSED ONLY
in both formats. Never replay suggested patches automatically or apply two
representations of the same change. Independent findings that conflict must
state their dependency/conflict; do not present mutually incompatible patches
as simultaneously ready to apply.

If a concrete safe remediation cannot yet be specified, label the finding a
hypothesis with exact code, counterexample, missing fact and proposed diagnostic
test. It remains unresolved and cannot count as an implementation-ready fix or
completed criterion. This exception preserves truth; it does not permit
high-level-only review in place of examining the supplied source.

Review.json fields: schema=`labor-loop.review.v1`, identity, coverage[],
findings[], limitations[], and overall_decision. Coverage entries have path,
source_sha256, snapshot, symbol, line_start, line_end, dimensions[], limitations.
Finding entries have id, severity, category, status, criterion_ids[], locations[],
literal_code, trigger, call_path, expected, actual, consequence, missed_test_reason,
fix_kind, fix_ref, regression_ref, test_execution[], integration_impact,
disposition and remaining_uncertainty. IDs/paths use validated existing scope;
no raw worker text becomes executable commands. Distinguish editable scope from
supplied read-only context and proposed-only new paths. A finding in supplied
read-only source is reportable; its patch cannot apply without scope expansion.
New tests use explicit new-file/insertion coordinates, never fabricated existing
line numbers. Out-of-packet source is unavailable and cannot be claimed reviewed.
Empty required evidence prevents
claiming review complete; use explicit hypothesis/limitation where facts lack.

The local validator checks schema, source existence/hash, coordinate bounds,
snippet equality to pinned bytes, hunk applicability for proposed fixes in a
disposable copy, and agreement of fixed hunks with the canonical patch. A human
or capable independent reviewer still judges causal reasoning and completeness;
schema checking alone cannot establish semantic correctness.

Large receipts belong in the returned artifact, with a short chat index of
finding IDs and dispositions. Do not truncate detailed review to fit the chat
response. Split review sections into indexed files when required by size limits;
include all parts and hashes in the manifest. Preserve readable literal code and
exact revisions rather than replacing them with vague summary prose.
All parts together remain within negotiated member/byte limits. If mandatory
detail exceeds the cap, request a scoped split/new round; never bypass limits
or truncate required findings. Worker-declared test results remain explicitly
untrusted observations; only separately produced local execution receipts count
as trusted proof. S1a bootstrap reviews these files manually; S4 adds structural
enforcement without expanding the first slice into a review framework.
