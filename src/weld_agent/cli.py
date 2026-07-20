from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from weld_agent.contracts import ContractValidationError, load_document
from weld_agent.providers.fixture import FixtureCandidateProvider
from weld_agent.runtime import probe_pythonocc
from weld_agent.workflow import run_analysis


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hypermesh-weld-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--selection", type=Path, required=True)
    analyze.add_argument("--output-root", type=Path, required=True)
    analyze.add_argument("--provider", choices=["fixture"], required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--schema", required=True)
    validate.add_argument("--input", type=Path, required=True)

    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--pythonocc-python", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "doctor":
            result = probe_pythonocc(args.pythonocc_python)
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            return 0 if result.available else 2
        if args.command == "validate":
            load_document(args.input, args.schema)
            return 0
        output = run_analysis(
            args.selection,
            args.output_root,
            FixtureCandidateProvider(),
        )
        print(output)
        return 0
    except (ContractValidationError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
