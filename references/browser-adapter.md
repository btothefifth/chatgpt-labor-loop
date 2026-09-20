# Browser adapter procedure

This environment exposes the supported browser through Codex browser-control
tools rather than a stable local ChatGPT API. The labor-loop skill keeps the
adapter behind the following procedure so DOM details do not leak into the
state model:

## Bridge preflight and recovery

Before attempting an upload or download, run the read-only bridge diagnosis
against the runtime root supplied by the host:

```text
python -B scripts/repair_browser_bridge.py --root <runtime-root> diagnose
```

The companion utility recognizes only narrow `browser-service.mjs` files under
a discovered runtime layout. It never reads browser profiles, cookies,
credentials, or page contents. If it reports an exact known repair, apply it
with an explicit write request:

```text
python -B scripts/repair_browser_bridge.py --root <runtime-root> repair --apply
```

The request-header repair bounds an optional policy lookup. The attachment
download fallback is deliberately separate because it changes how an
unmanaged document response is handled:

```text
python -B scripts/repair_browser_bridge.py --root <runtime-root> repair --apply --download-fallback
```

Only use the download fallback when the visible browser failure is a blocked
attachment download and the exact gate is present. The utility creates a
timestamped backup, writes atomically, runs `node --check`, and rolls back the
file if syntax validation fails. Restart or recreate the browser-control
runtime after any successful repair, then rerun `diagnose` and perform a
harmless browser smoke test. An unknown layout is a stop-and-report condition;
do not broaden the patch by guessing at selectors or service endpoints.

1. Resolve the project’s stored `thread_url` in the existing authenticated
   Chrome session. If it is missing, ask the user to choose or create the dedicated
   project thread; do not guess from another project’s conversation.
2. Read-only inspect the visible thread and composer. Classify the state before
   acting. A tab ID may be re-discovered from the URL and must not be treated as
   durable identity.
3. Immediately before file upload and message send, obtain the required action
   confirmation. Upload only the generated packet ZIP and send the standalone
   request; do not paste secrets or local paths. The generated request contains
   the artifact-delivery contract: ask the worker to attach the result ZIP
   directly to the response, with a public HTTPS URL as the only fallback.
4. After the send is visibly accepted, run `record-submission` once with the
   visible canonical thread URL and stable thread identity. Add
   `--worker-started` only when the worker is visibly answering; this records
   the mapping and lifecycle atomically. Poll with exponential backoff (for
   example 15s, 30s, 60s, 120s, then 5-minute intervals) and keep Luna out of
   a tight reasoning loop. Read-only polling is safe; a follow-up
   answer to a worker question is another representational message and requires
   the same action confirmation.
5. If the worker asks a question, answer automatically only when the request,
   repository contract, or explicit project config determines the answer. For a
   product choice, security boundary, unexpected auth challenge, or repeated
   failure, record `BLOCKED` and ask the user.
6. When a completed message exposes the expected artifact, prefer the visible
   direct attachment. A fallback URL must be HTTPS, have no embedded
   credentials, and not target localhost, a private/reserved address, an
   internal hostname, or a backend/API/session-only endpoint. Open/download it
   visibly, record `ARTIFACT_DOWNLOADED`, and hand the local path to
   `record-artifact`. Never trust a URL-shaped string merely because its
   filename looks correct.
7. If the worker gives only an inaccessible backend/API link, do not keep
   retrying that link. Prepare the state-aware recovery request:

   ```text
   python -B scripts/labor_loop.py --project-id <id> artifact-followup \
     --job-id <job-id> \
     --reason "worker returned an inaccessible backend or session link"
   ```

   Send the generated prompt as a follow-up in the same mapped thread. It asks
   for a direct attachment first and a genuinely public HTTPS URL second. If
   neither is possible, the worker must report delivery blocked rather than
   claim completion. Sending the follow-up remains a visible browser action;
   the CLI only prepares and records the request.

Do not automate login, password entry, CAPTCHA, rate-limit evasion, hidden
network endpoints, cookie extraction, or browser profile copying. If the UI
changes, repair this adapter procedure or add a new supported adapter; do not
couple the local state machine to brittle selectors.
