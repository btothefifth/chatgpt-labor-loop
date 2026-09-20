# Labor Loop

`labor-loop` is a reusable Codex skill and local CLI for delegating bounded
implementation work to a persistent normal ChatGPT Chat thread while keeping
the repository, tests, Git state, and acceptance decision under local control.

It is deliberately not an API client. The supported browser adapter uses the
existing authenticated browser session when available; credentials, cookies,
CAPTCHAs, hidden endpoints, and rate-limit bypasses are out of scope.

## What it provides

- private project-to-thread mapping and resumable per-job state;
- sealed packets from pinned committed Git snapshots with secret/path filtering;
- a machine-readable worker return contract;
- safe ZIP validation before extraction;
- detached-worktree patch integration and configured build/test/lint commands;
- durable receipts, retry/abort/status operations, and a Codex review gate.

Project-specific configurations belong outside the public core when they
contain repository-specific context. Use
`references/project-config.example.json` as the portable starting point and
keep local project adapters in the private state root.

## Install as a Codex skill

Copy this directory to the Codex skills directory as `labor-loop`, or clone the
public repository and copy its contents into that directory. Keep the private
state root outside any Git checkout. A fresh Codex turn may be needed before a
newly installed skill appears in automatic discovery.

## Local CLI

Use the Python interpreter available on the machine:

```text
python -B scripts/labor_loop.py --project-id example init --repo C:\work\example
python -B scripts/labor_loop.py --project-id example start --request request.md
python -B scripts/labor_loop.py --project-id example status
python -B scripts/labor_loop.py --project-id example resume
```

Use `--state-root` to select a private state directory explicitly. Configure
project-specific `validation.commands` as argv arrays; worker-provided commands
are never executed. The browser submission and polling procedure is documented
in `references/browser-adapter.md`.

After the browser adapter visibly uploads the packet and sends the request,
record that receipt in one operation. Add `--worker-started` only after the
worker is visibly answering:

```text
python -B scripts/labor_loop.py --project-id example-project record-submission `
  --job-id LL-... --thread-url https://chatgpt.com/c/... `
  --thread-id WEB:... --model-mode configured --worker-started
```

This command does not send a message or control a browser; it makes the
already-observed external action durable and atomic with the local lifecycle.
It is safe to repeat after a browser or process interruption: a matching
submission receipt is treated as an idempotent observation, does not regress
the job, and does not duplicate timeline events. A different worker URL or
provider thread ID is rejected for an active job; abort/retry is required
before intentionally changing worker identity.

## Testing

```text
python -B scripts/test_labor_loop.py
python -B -m py_compile scripts/labor_loop.py scripts/validate_artifact.py
```

The tests use a temporary Git repository and exercise packet sealing, secret
omission, ZIP traversal/link rejection, isolated patch application, local
checks, review, retry, and resumability. They do not send a ChatGPT message.

## Scope and safety

The remote worker is an untrusted subcontractor. Do not apply a returned ZIP to
main, run its scripts, publish credentials, force-push, deploy, or expand
authority merely because a worker report says it succeeded. Review the isolated
diff and local evidence first.
