from __future__ import annotations

import argparse
import json
import sys

from .commands import (
    check_report,
    compare_reports,
    init_suite,
    normalize_output_command,
    score_suite,
    write_compare_outputs,
    write_score_outputs,
)


def add_threshold_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--min-precision", type=float)
    parser.add_argument("--min-recall", type=float)
    parser.add_argument("--min-f1", type=float)
    parser.add_argument("--min-rule-coverage", type=float)
    parser.add_argument("--max-fp", type=int)
    parser.add_argument("--max-fn", type=int)
    parser.add_argument("--check", choices=["warning", "error"], default="error")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="review-benchmark-harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    score_parser = subparsers.add_parser("score", help="Score a system output against a benchmark suite.")
    score_parser.add_argument("--suite", required=True)
    score_parser.add_argument("--predictions", required=True)
    score_parser.add_argument("--system-name", default="candidate")
    score_parser.add_argument("--input-format", choices=["auto", "json", "markdown"], default="auto")
    score_parser.add_argument("--output")
    score_parser.add_argument("--markdown-output")
    score_parser.add_argument("--csv-output")
    score_parser.add_argument("--junit-output")
    add_threshold_arguments(score_parser)

    init_parser = subparsers.add_parser("init-suite", help="Create a benchmark suite scaffold.")
    init_parser.add_argument("target_dir")
    init_parser.add_argument("--force", action="store_true")
    init_parser.add_argument("--no-sample", action="store_true")

    normalize_parser = subparsers.add_parser("normalize-output", help="Normalize review output into JSON findings.")
    normalize_parser.add_argument("input_path")
    normalize_parser.add_argument("--format", choices=["auto", "json", "markdown"], default="auto")
    normalize_parser.add_argument("--output", required=True)

    compare_parser = subparsers.add_parser("compare", help="Compare one or more score reports.")
    compare_parser.add_argument("reports", nargs="+")
    compare_parser.add_argument("--output")
    compare_parser.add_argument("--markdown-output")
    compare_parser.add_argument("--csv-output")

    check_parser = subparsers.add_parser("check", help="Apply CI thresholds to a JSON score report.")
    check_parser.add_argument("report")
    add_threshold_arguments(check_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "score":
        payload = score_suite(
            suite_dir=args.suite,
            predictions_path=args.predictions,
            system_name=args.system_name,
            input_format=args.input_format,
            min_precision=args.min_precision,
            min_recall=args.min_recall,
            min_f1=args.min_f1,
            min_rule_coverage=args.min_rule_coverage,
            max_fp=args.max_fp,
            max_fn=args.max_fn,
            check_level=args.check,
        )
        if args.output or args.markdown_output or args.csv_output or args.junit_output:
            write_score_outputs(
                payload,
                json_output=args.output,
                markdown_output=args.markdown_output,
                csv_output=args.csv_output,
                junit_output=args.junit_output,
            )
        else:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        if args.check == "error" and payload.get("issues"):
            return 1
        return 0

    if args.command == "init-suite":
        payload = init_suite(args.target_dir, with_sample=not args.no_sample, force=args.force)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.command == "normalize-output":
        payload = normalize_output_command(args.input_path, args.output, input_format=args.format)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.command == "compare":
        payload = compare_reports(args.reports)
        if args.output or args.markdown_output or args.csv_output:
            write_compare_outputs(payload, json_output=args.output, markdown_output=args.markdown_output, csv_output=args.csv_output)
        else:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.command == "check":
        payload = check_report(
            args.report,
            min_precision=args.min_precision,
            min_recall=args.min_recall,
            min_f1=args.min_f1,
            min_rule_coverage=args.min_rule_coverage,
            max_fp=args.max_fp,
            max_fn=args.max_fn,
            check_level=args.check,
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        if args.check == "error" and payload["issues"]:
            return 1
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
