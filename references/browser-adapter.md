# Browser adapter procedure

This environment exposes the supported browser through Codex browser-control
tools rather than a stable local ChatGPT API. The labor-loop skill keeps the
adapter behind the following procedure so DOM details do not leak into the
state model:

1. Resolve the project’s stored `thread_url` in the existing authenticated
   Chrome session. If it is missing, ask the user to choose or create the dedicated
   project thread; do not guess from another project’s conversation.
2. Read-only inspect the visible thread and composer. Classify the state before
   acting. A tab ID may be re-discovered from the URL and must not be treated as
   durable identity.
3. Immediately before file upload and message send, obtain the required action
   confirmation. Upload only the generated packet ZIP and send the standalone
   request; do not paste secrets or local paths.
4. Record `SUBMITTED` and `WORKER_RUNNING` with the CLI. Poll with exponential
   backoff (for example 15s, 30s, 60s, 120s, then 5-minute intervals) and keep
   Luna out of a tight reasoning loop. Read-only polling is safe; a follow-up
   answer to a worker question is another representational message and requires
   the same action confirmation.
5. If the worker asks a question, answer automatically only when the request,
   repository contract, or explicit project config determines the answer. For a
   product choice, security boundary, unexpected auth challenge, or repeated
   failure, record `BLOCKED` and ask the user.
6. When a completed message exposes the expected artifact, download it through
   the visible browser control, record `ARTIFACT_DOWNLOADED`, and hand the path
   to `record-artifact`. Never trust the download merely because its filename
   looks correct.

Do not automate login, password entry, CAPTCHA, rate-limit evasion, hidden
network endpoints, cookie extraction, or browser profile copying. If the UI
changes, repair this adapter procedure or add a new supported adapter; do not
couple the local state machine to brittle selectors.
