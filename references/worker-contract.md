# Worker packet and return contract

The packet is a ZIP assembled from committed, allowlisted context plus a
standalone request. Its root contains:

```text
job.json
REQUEST.md
CONTEXT.md
START_HERE.md
context/<repository-relative snapshots>
```

`job.json` is safe to upload and includes the unique `job_id`, project identity,
repository URL when known, full pinned `base_commit`, selected files, omitted
files, acceptance contract, and the exact return layout. It intentionally does
not contain a local path, browser credentials, or browser storage.

Every generated request also includes a generic recent-integration feedback
contract. The worker must inspect the latest accepted baseline against the
project intent, report mismatches, regression risks, missing tests,
documentation gaps, and safe integration repairs in `SUMMARY.md` and
`REMAINING.md`, and state explicitly when that review found no actionable gap.

The worker is asked to return one ZIP with this root layout:

```text
manifest.json
START_HERE.md
SUMMARY.md
INTEGRATION.md
REMAINING.md
VALIDATION.md
changes.patch
files/<optional complete changed files for review/recovery>
evidence/<optional worker evidence>
```

`manifest.json` must identify the same `job_id`, `base_commit`, and repository.
`changes.patch` is canonical and may be empty only when the worker made no code
change. The local validator rejects traversal, absolute names, symlinks, `.git`,
executable payloads, size-limit violations, required-file omissions, identity
mismatches, and likely secret material before extraction.

The worker may report partial progress, but it must not claim local test proof
that it could not actually run. It must list unresolved work and assumptions.
The local review accepts only what the repository and local checks establish.

## Artifact delivery

Delivery is part of the worker contract, not an optional presentation detail.
The preferred result is the ZIP attached directly to the ChatGPT response. A
fallback public URL is acceptable only when it is HTTPS and can be opened
without login, cookies, bearer tokens, internal hostnames, private-network
addresses, localhost, or a session-bound/backend/API endpoint. `file://` paths
and inaccessible execution-environment links are not valid deliveries.

The browser adapter must download the attachment or public URL visibly, then
`record-artifact` and `validate-artifact` must succeed locally. A worker claim
or a URL-shaped string is never proof that delivery occurred. If the worker
returns only an inaccessible link, use the state-aware `artifact-followup`
command to generate a recovery request in the same thread. The follow-up must
repeat the same direct-attachment/public-URL contract.
