#!/usr/bin/env python3
"""Small direct wrapper for the labor-loop artifact validator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from labor_loop import (
    LaborError,
    Store,
    default_state_root,
    project_and_store,
    validate_return_artifact,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a labor-loop return ZIP")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--state-root")
    parser.add_argument("--job-id")
    parser.add_argument("artifact")
    args = parser.parse_args()
    try:
        store = Store(
            Path(args.state_root) if args.state_root else default_state_root(),
            args.project_id,
        )
        project = store.load_project()
        state = store.load_state(args.job_id if args.job_id else None)
        state["job_dir"] = str(store.job_dir(state["job_id"]))
        receipt = validate_return_artifact(
            Path(args.artifact).expanduser().resolve(), state, project
        )
    except LaborError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
