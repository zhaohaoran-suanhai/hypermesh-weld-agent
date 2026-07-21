from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from weld_agent.contracts import ContractValidationError, load_document
from weld_agent.export_finalizer import ExportFinalizationError, finalize_export
from weld_agent.geometry.step_inspector import PythonOccStepInspector, StepInspectionError
from weld_agent.geometry.occ_marker_reader import (
    MarkerStepReadError,
    PythonOccMarkerReader,
)
from weld_agent.marker_identification import (
    MarkerIdentificationError,
    identify_weld_markers,
)
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

    finalize = subparsers.add_parser("finalize-export")
    finalize.add_argument("--manifest", type=Path, required=True)
    finalize.add_argument("--profile", type=Path, required=True)

    identify = subparsers.add_parser("identify-markers")
    identify.add_argument("--manifest", type=Path, required=True)
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
        if args.command == "finalize-export":
            result = finalize_export(
                args.manifest,
                args.profile,
                PythonOccStepInspector(),
            )
            print(result.selection_path)
            return 0
        if args.command == "identify-markers":
            artifacts = identify_weld_markers(
                args.manifest,
                PythonOccMarkerReader(),
                print,
            )
            payload = json.loads(artifacts.json_path.read_text(encoding="utf-8"))
            print("\n识别完成")
            for key in (
                "component_count",
                "marker_count",
                "cylinder_marker",
                "triangular_marker",
                "unknown_marker",
            ):
                print(f"  {key:<20}{payload['summary'][key]:>3}")
            print(f"\n详细结果：{artifacts.json_path}")
            print(f"表格结果：{artifacts.csv_path}")
            print(f"运行日志：{artifacts.log_path}")
            return 0
        output = run_analysis(
            args.selection,
            args.output_root,
            FixtureCandidateProvider(),
        )
        print(output)
        return 0
    except ExportFinalizationError as exc:
        print(f"error: {exc.code}: {exc}", file=sys.stderr)
        return 2
    except StepInspectionError as exc:
        print(f"error: {exc.code}: {exc}", file=sys.stderr)
        return 2
    except MarkerIdentificationError as exc:
        print(f"error: {exc.code}: {exc}", file=sys.stderr)
        return 2
    except MarkerStepReadError as exc:
        print(f"error: {exc.code}: {exc}", file=sys.stderr)
        return 2
    except (ContractValidationError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
