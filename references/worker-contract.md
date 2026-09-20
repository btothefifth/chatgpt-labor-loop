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
