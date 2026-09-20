#!/usr/bin/env python3
"""Unit tests for the narrow, reversible browser-runtime repair utility."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import repair_browser_bridge as repair


SERVICE_SOURCE = """
return await Rm.then(()=>Ab(\"codex_browser_use_agent_request_header\"));
if(!o){await this.documentResponses.failResponse(r,i);return}
""".strip()


class BrowserRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="labor-loop-browser-repair-")
        self.root = Path(self.temp.name) / "runtime"
        self.service = (
            self.root
            / "build-1"
            / "bin"
            / "node_modules"
            / "@oai"
            / "browser-desktop"
            / "scripts"
            / "browser-service.mjs"
        )
        self.service.parent.mkdir(parents=True)
        self.service.write_text(SERVICE_SOURCE, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_patch_is_exact_and_syntax_shape_is_balanced(self) -> None:
        patched, changes = repair.patch_text(SERVICE_SOURCE, download_fallback=True)
        self.assertEqual(
            changes,
            ["request-header-policy-timeout", "download-fallback"],
        )
        self.assertIn(
            "Promise.race([Rm.then(()=>Ab(\"codex_browser_use_agent_request_header\")),",
            patched,
        )
        self.assertNotIn(")));,", patched)
        self.assertIn("continueResponse(r,i)", patched)
        self.assertEqual(patched.count("Promise.race(["), 1)

    def test_diagnose_discovery_and_repair_are_idempotent(self) -> None:
        roots = [self.root]
        before = repair.diagnose(roots)
        self.assertEqual(len(before["files"]), 1)
        self.assertTrue(before["files"][0]["repairable"])
        with patch.object(repair, "syntax_check", return_value={"status": "passed"}):
            result = repair.apply_repairs(
                roots,
                download_fallback=True,
            )
        self.assertEqual(result["files"][0]["status"], "patched")
        backup = Path(result["files"][0]["backup"])
        self.assertTrue(backup.is_file())
        self.assertEqual(backup.read_text(encoding="utf-8"), SERVICE_SOURCE)
        after = repair.diagnose(roots)
        self.assertFalse(after["files"][0]["repairable"])
        with patch.object(repair, "syntax_check", return_value={"status": "passed"}):
            repeat = repair.apply_repairs(roots, download_fallback=True)
        self.assertEqual(repeat["files"][0]["status"], "unchanged")

    def test_explicit_file_must_stay_inside_runtime_root(self) -> None:
        outside = Path(self.temp.name) / "browser-service.mjs"
        outside.write_text(SERVICE_SOURCE, encoding="utf-8")
        with self.assertRaises(repair.RepairError):
            repair.diagnose_path(outside, [self.root])

    def test_unrelated_service_is_not_repaired(self) -> None:
        unrelated = self.root / "build-1" / "bin" / "node_modules" / "other"
        unrelated.mkdir(parents=True)
        path = unrelated / "browser-service.mjs"
        path.write_text("console.log('unrelated');\n", encoding="utf-8")
        result = repair.diagnose_path(path, [self.root])
        self.assertEqual(result["header_policy"], "not-applicable")
        self.assertEqual(result["download_gate"], "not-applicable")
        self.assertFalse(result["repairable"])


if __name__ == "__main__":
    unittest.main()
