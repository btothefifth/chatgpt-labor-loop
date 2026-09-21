# Labor Loop current work

Objective LL-PORTABLE-1, version 1, 2026-09-21: make the loop reliably operable
by inexpensive local models across client applications and subscription chat
services. This thread owns design and implementation planning in this repository.

Baseline: `9bd800d`. Existing code remains a Codex/ChatGPT v1 implementation.
The v2 documents are a target contract, not implemented capability.

Read in order:

1. [Product and criteria](../design/product.md)
2. [Architecture and protocol](../design/architecture.md)
   and [transitional proof contract](../design/proof-contract.md)
3. [Adapters, capabilities, and recovery](../design/adapters.md)
4. [Local learning and request adaptation](../design/learning.md)
   and [high-value worker brief](../design/worker-brief.md)
   and [detailed code-review receipt](../design/code-review.md)
5. [Provider evidence](../design/providers.md)
6. [Test design](../design/validation.md)
7. [Gap register and implementation sequence](plan.md)
8. [Adversarial review record](review.md)

This documentation extends the incomplete but compatible v1 references. Those
references describe the incumbent; these documents govern v2 implementation.
No runtime migration, browser submission, publication, or provider support is
implied by their existence. The next implementation action is S0 in the plan.

Stop boundary for this task: complete the BMAD documents, review them
recursively, identify current gaps, and prepare an executable loop-based plan.
Implementation and chat submissions are a subsequent phase.

Planning receipt: criteria C1-C15, gap register G1-G14, test design T1-T17,
recursive adversarial/intent/simplification review and first worker brief are
complete. Baseline suites passed 12 + 4 tests. Files are local uncommitted
documentation; the packet builder cannot include them until the S0 reviewed
design commit. No implementation slices or real chat qualification are complete.
