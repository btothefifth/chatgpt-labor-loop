#!/usr/bin/env python3
"""Forward tests for the local labor-loop core.

These tests use a temporary Git repository and never contact a browser or a
remote service.  The browser adapter is intentionally tested by contract and
read-only inspection in the skill runtime, not by sending a message.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from labor_loop import LaborError, StoreLock, process_is_alive, validate_return_artifact


SCRIPT = Path(__file__).with_name("labor_loop.py")


def run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv, cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=False
    )


class LaborLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="labor-loop-test-")
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.state = self.root / "state"
        self.project_id = "fixture-project"
        self.write("README.md", "fixture\n")
        self.write("src/lib.txt", "old\n")
        self.git(["init", "-q"])
        self.git(["config", "user.email", "fixture@example.invalid"])
        self.git(["config", "user.name", "Fixture"])
        self.git(["add", "."])
        self.git(["commit", "-qm", "initial"])
        self.cli("init", "--repo", str(self.repo))
        project_path = self.state / "projects" / self.project_id / "project.json"
        project = json.loads(project_path.read_text(encoding="utf-8"))
        project["repository"]["url"] = "https://github.com/example/fixture.git"
        project["packet"]["include_paths"] = ["."]
        project["validation"]["commands"] = [
            {"name": "diff-check", "argv": ["git", "diff", "--check"]}
        ]
        project_path.write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, relative: str, text: str) -> None:
        target = self.repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def git(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        result = run(["git", "-C", str(self.repo), *args])
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def cli(self, *args: str, check: bool = True) -> dict:
        result = run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "--state-root",
                str(self.state),
                "--project-id",
                self.project_id,
                *args,
            ]
        )
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        if result.stdout:
            return json.loads(result.stdout)
        return {"stderr": result.stderr}

    def make_job(self) -> dict:
        request = self.root / "request.md"
        request.write_text(
            "Implement the fixture change and prove it with local checks.\n",
            encoding="utf-8",
        )
        return self.cli("start", "--request", str(request))

    def advance_to_worker_complete(self, job_id: str) -> None:
        for status in ("SUBMITTED", "WORKER_RUNNING", "WORKER_COMPLETE"):
            self.cli(
                "transition", "--job-id", job_id, "--to", status, "--note", "fixture"
            )

    def make_artifact(
        self, job_id: str, base_commit: str, patch: str | None = None
    ) -> Path:
        artifact = self.root / f"{job_id}.zip"
        manifest = {
            "schema_version": "labor-loop.return.v1",
            "job_id": job_id,
            "base_commit": base_commit,
            "repository": "https://github.com/example/fixture.git",
        }
        patch = patch if patch is not None else ""
        entries = {
            "manifest.json": json.dumps(manifest).encode("utf-8"),
            "START_HERE.md": b"start\n",
            "SUMMARY.md": b"summary\n",
            "INTEGRATION.md": b"integration\n",
            "REMAINING.md": b"none\n",
            "VALIDATION.md": b"worker validation is not local proof\n",
            "changes.patch": patch.encode("utf-8"),
        }
        with zipfile.ZipFile(
            artifact, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for name, content in entries.items():
                archive.writestr(name, content)
        return artifact

    def test_packet_state_and_safe_integration(self) -> None:
        job = self.make_job()
        job_id = job["job_id"]
        base = job["base_commit"]
        self.advance_to_worker_complete(job_id)
        patch = """diff --git a/src/lib.txt b/src/lib.txt
--- a/src/lib.txt
+++ b/src/lib.txt
@@ -1 +1 @@
-old
+new
"""
        artifact = self.make_artifact(job_id, base, patch)
        self.cli("record-artifact", "--job-id", job_id, "--path", str(artifact))
        self.cli("validate-artifact", "--job-id", job_id)
        integrated = self.cli("integrate", "--job-id", job_id)
        self.assertEqual(integrated["status"], "REVIEWING")
        status = self.cli("status")
        self.assertEqual(status["current"]["status"], "REVIEWING")
        self.cli(
            "review",
            "--job-id",
            job_id,
            "--decision",
            "complete",
            "--note",
            "fixture diff and local check reviewed",
        )
        self.assertEqual(self.cli("status")["current"]["status"], "COMPLETE")
        self.assertEqual(
            (self.repo / "src/lib.txt").read_text(encoding="utf-8"),
            "old\n",
            "main checkout must remain unchanged",
        )

    def test_initial_request_requires_direct_or_public_artifact_delivery(self) -> None:
        job = self.make_job()
        job_dir = self.state / "projects" / self.project_id / "jobs" / job["job_id"]
        request = (job_dir / "REQUEST.md").read_text(encoding="utf-8")
        packet_job = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
        self.assertIn("attaching the ZIP directly", request)
        self.assertIn("public HTTPS URL", request)
        self.assertIn("backend/API endpoint", request)
        self.assertIn("Recent integration feedback (required)", request)
        self.assertIn("intent mismatch", request)
        self.assertIn("other recent or relevant implemented", request)
        self.assertIn("Name the reviewed surfaces", request)
        self.assertEqual(
            packet_job["artifact_delivery"]["preferred"], "direct-attachment"
        )

    def test_artifact_followup_repeats_delivery_contract(self) -> None:
        job = self.make_job()
        self.advance_to_worker_complete(job["job_id"])
        followup = self.cli(
            "artifact-followup",
            "--job-id",
            job["job_id"],
            "--reason",
            "worker returned an inaccessible backend API link",
        )
        self.assertIn("Attach the ZIP directly", followup["prompt"])
        self.assertIn("public HTTPS URL", followup["prompt"])
        self.assertIn("Do not return a `file://` path", followup["prompt"])
        self.assertIn("Recent integration feedback (required)", followup["prompt"])
        self.assertIn("other recent or relevant implemented", followup["prompt"])
        self.assertIn(job["job_id"], followup["prompt"])
        timeline = [
            json.loads(line)
            for line in (
                self.state / "projects" / self.project_id / "timeline.jsonl"
            )
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertIn(
            "artifact delivery follow-up prepared",
            [event["note"] for event in timeline],
        )

    def test_record_submission_binds_thread_and_advances_running_atomically(self) -> None:
        job = self.make_job()
        result = self.cli(
            "record-submission",
            "--job-id",
            job["job_id"],
            "--thread-url",
            "https://chatgpt.com/c/example-thread",
            "--thread-id",
            "WEB:example-thread",
            "--model-mode",
            "6 Pro",
            "--worker-started",
            "--note",
            "fixture browser receipt",
        )
        self.assertEqual(result["status"], "WORKER_RUNNING")
        status = self.cli("status")
        self.assertEqual(status["thread"]["thread_id"], "WEB:example-thread")
        self.assertEqual(status["thread"]["model_mode"], "6 Pro")
        self.assertEqual(
            status["current"]["thread_url"],
            "https://chatgpt.com/c/example-thread",
        )
        events = [
            json.loads(line)
            for line in (
                self.state / "projects" / self.project_id / "timeline.jsonl"
            )
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertIn("THREAD_BOUND", [event["to"] for event in events])

    def test_repair_checks_resumes_after_local_validation_fix(self) -> None:
        job = self.make_job()
        job_id = job["job_id"]
        base = job["base_commit"]
        self.advance_to_worker_complete(job_id)
        patch = """diff --git a/src/lib.txt b/src/lib.txt
--- a/src/lib.txt
+++ b/src/lib.txt
@@ -1 +1 @@
-old
+new
"""
        artifact = self.make_artifact(job_id, base, patch)
        self.cli("record-artifact", "--job-id", job_id, "--path", str(artifact))
        self.cli("validate-artifact", "--job-id", job_id)
        integrated = self.cli("integrate", "--job-id", job_id, "--skip-checks")
        worktree = Path(integrated["worktree_path"])
        (worktree / "src/lib.txt").write_text("new  \n", encoding="utf-8")
        failed = self.cli("run-checks", "--job-id", job_id, check=False)
        self.assertIn("validation command failed", failed["stderr"])
        self.assertEqual(self.cli("status")["current"]["status"], "FAILED")
        (worktree / "src/lib.txt").write_text("new\n", encoding="utf-8")
        repaired = self.cli("repair-checks", "--job-id", job_id)
        self.assertEqual(repaired["status"], "REVIEWING")

    def test_record_submission_is_idempotent_after_worker_started(self) -> None:
        job = self.make_job()
        submission = [
            "record-submission",
            "--job-id",
            job["job_id"],
            "--thread-url",
            "https://chatgpt.com/c/idempotent-thread",
            "--thread-id",
            "WEB:idempotent-thread",
            "--model-mode",
            "6 Pro",
            "--worker-started",
        ]
        first = self.cli(*submission)
        second = self.cli(*submission)
        self.assertEqual(first["status"], "WORKER_RUNNING")
        self.assertEqual(second["status"], "WORKER_RUNNING")
        self.assertTrue(second["idempotent"])
        events = [
            json.loads(line)
            for line in (
                self.state / "projects" / self.project_id / "timeline.jsonl"
            )
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(
            [event["to"] for event in events].count("THREAD_BOUND"),
            1,
        )
        self.assertEqual(
            [event["to"] for event in events].count("WORKER_RUNNING"),
            1,
        )

    def test_active_submission_rejects_identity_change_even_with_replace(self) -> None:
        job = self.make_job()
        self.cli(
            "record-submission",
            "--job-id",
            job["job_id"],
            "--thread-url",
            "https://chatgpt.com/c/original-thread",
            "--thread-id",
            "WEB:original-thread",
            "--worker-started",
        )
        rejected = self.cli(
            "record-submission",
            "--job-id",
            job["job_id"],
            "--thread-url",
            "https://chatgpt.com/c/replacement-thread",
            "--thread-id",
            "WEB:replacement-thread",
            "--replace",
            check=False,
        )
        self.assertIn("submission identity differs", rejected["stderr"])

    def test_record_submission_rejects_thread_replacement_without_explicit_flag(self) -> None:
        job = self.make_job()
        self.cli(
            "record-submission",
            "--job-id",
            job["job_id"],
            "--thread-url",
            "https://chatgpt.com/c/first-thread",
        )
        self.cli(
            "abort",
            "--job-id",
            job["job_id"],
            "--note",
            "rotate fixture job",
        )
        next_job = self.make_job()
        second = self.cli(
            "record-submission",
            "--job-id",
            next_job["job_id"],
            "--thread-url",
            "https://chatgpt.com/c/second-thread",
            check=False,
        )
        self.assertIn("different thread is already bound", second["stderr"])

    def test_packet_omits_secret_path_and_records_omission(self) -> None:
        self.write(".env", "API_KEY=not-for-upload-123456789\n")
        self.git(["add", ".env"])
        self.git(["commit", "-qm", "secret fixture"])
        job = self.make_job()
        job_doc = json.loads(
            (
                self.state
                / "projects"
                / self.project_id
                / "jobs"
                / job["job_id"]
                / "job.json"
            ).read_text(encoding="utf-8")
        )
        omitted = {
            item["path"]: item["reason"] for item in job_doc["context"]["omitted"]
        }
        self.assertEqual(omitted.get(".env"), "sensitive-or-excluded-path")

    def test_artifact_traversal_and_symlink_are_rejected(self) -> None:
        job = self.make_job()
        job_id = job["job_id"]
        project_path = self.state / "projects" / self.project_id / "project.json"
        project = json.loads(project_path.read_text(encoding="utf-8"))
        state = json.loads(
            (self.state / "projects" / self.project_id / "state.json").read_text(
                encoding="utf-8"
            )
        )
        state["job_dir"] = str(
            self.state / "projects" / self.project_id / "jobs" / job_id
        )

        traversal = self.root / "traversal.zip"
        with zipfile.ZipFile(traversal, "w") as archive:
            archive.writestr("../escape.txt", b"bad")
        with self.assertRaises(LaborError):
            validate_return_artifact(traversal, state, project)

        symlink = self.root / "symlink.zip"
        info = zipfile.ZipInfo("manifest.json")
        info.external_attr = (0o120777 << 16) | 0xA000
        with zipfile.ZipFile(symlink, "w") as archive:
            archive.writestr(info, b"{}")
        with self.assertRaises(LaborError):
            validate_return_artifact(symlink, state, project)

    def test_retry_is_explicit_and_resumable(self) -> None:
        job = self.make_job()
        job_id = job["job_id"]
        self.cli(
            "transition", "--job-id", job_id, "--to", "SUBMITTED", "--note", "fixture"
        )
        self.cli(
            "transition",
            "--job-id",
            job_id,
            "--to",
            "BLOCKED",
            "--note",
            "needs a product choice",
        )
        retry = self.cli(
            "retry", "--job-id", job_id, "--note", "human resolved the choice"
        )
        self.assertEqual(retry["attempt"], 1)
        self.assertEqual(self.cli("resume", "--job-id", job_id)["status"], "PACKAGED")

    def test_dead_lock_owner_is_recovered_but_active_lock_is_not(self) -> None:
        self.assertFalse(process_is_alive(2147483647))
        self.assertTrue(process_is_alive(os.getpid()))
        lock_path = self.state / "projects" / self.project_id / ".lock"
        lock_path.write_text(
            '{"pid": 2147483647, "created_at": "old"}\n', encoding="utf-8"
        )
        with StoreLock(lock_path):
            self.assertTrue(lock_path.exists())
        self.assertFalse(lock_path.exists())

        lock_path.write_text(
            json.dumps({"pid": os.getpid(), "created_at": "now"}), encoding="utf-8"
        )
        with self.assertRaises(LaborError):
            with StoreLock(lock_path):
                pass
        lock_path.unlink()


if __name__ == "__main__":
    unittest.main(verbosity=2)
