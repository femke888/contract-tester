import argparse
import json
import sys
from typing import List, Optional

from .diff import diff_specs
from .license import DEMO_MAX_PATHS, DEMO_MAX_TRAFFIC, get_license_status
from .openapi import load_spec
from .output import err, ok, strong, supports_color, warn
from .report import build_html_report
from .traffic import load_traffic
from .validate import validate_traffic_against_spec
from . import __version__


def _cmd_validate(args: argparse.Namespace) -> int:
    color = supports_color() and (not args.no_color)
    if args.max_errors is not None and args.max_errors <= 0:
        raise ValueError("--max-errors must be a positive integer")
    spec = load_spec(args.spec)
    traffic = load_traffic(args.traffic)
    license_status = get_license_status()
    if not license_status["valid"]:
        print(
            warn(
                f"Demo mode: limiting traffic to {DEMO_MAX_TRAFFIC} entries.",
                color,
            )
        )
        if len(traffic) > DEMO_MAX_TRAFFIC:
            traffic = traffic[:DEMO_MAX_TRAFFIC]
        if isinstance(spec.get("paths"), dict) and len(spec.get("paths", {})) > DEMO_MAX_PATHS:
            print(
                err(
                    f"Demo mode: spec has more than {DEMO_MAX_PATHS} paths. Add a license to run.",
                    color,
                ),
                file=sys.stderr,
            )
            return 2
    result = validate_traffic_against_spec(
        spec,
        traffic,
        max_errors=args.max_errors,
        ignore_unknown=args.ignore_unknown,
    )
    result["license_status"] = license_status

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{strong('Total checks:', color)} {result['total_checks']}")
        print(f"{strong('Errors:', color)} {result['error_count']}")
        if result["stopped_early"]:
            print(warn("Stopped early due to max error limit.", color))
        if result["error_count"]:
            grouped = result.get("errors_grouped", {})
            if grouped:
                print("\nTop error groups:")
                for key in list(grouped.keys())[:5]:
                    print(f"- {key} ({len(grouped[key])})")
                print("\nTop errors:")
            else:
                print("\nTop errors:")
            details = result.get("error_details") or []
            if details:
                for item in details[:10]:
                    msg = item.get("message", "")
                    hint = item.get("hint")
                    if hint:
                        print(f"- {msg} (hint: {hint})")
                    else:
                        print(f"- {msg}")
            else:
                for err_msg in result["errors"][:10]:
                    print(f"- {err_msg}")

    if args.report:
        html = build_html_report(result)
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(html)
        if not args.json:
            print(f"\nReport written to {args.report}")

    return 1 if result["error_count"] else 0


def _cmd_diff(args: argparse.Namespace) -> int:
    color = supports_color() and (not args.no_color)
    old_spec = load_spec(args.old)
    new_spec = load_spec(args.new)
    license_status = get_license_status()
    if not license_status["valid"]:
        old_paths = len(old_spec.get("paths", {}) or {})
        new_paths = len(new_spec.get("paths", {}) or {})
        if max(old_paths, new_paths) > DEMO_MAX_PATHS:
            print(
                err(
                    f"Demo mode: specs have more than {DEMO_MAX_PATHS} paths. Add a license to run.",
                    color,
                ),
                file=sys.stderr,
            )
            return 2
        print(
            warn(
                f"Demo mode: limited to specs with up to {DEMO_MAX_PATHS} paths.",
                color,
            )
        )
    result = diff_specs(old_spec, new_spec)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(strong("Breaking changes:", color))
        for item in result["breaking_changes"]:
            print(f"- {item}")
        if not result["breaking_changes"]:
            print(f"- {ok('None', color)}")

    return 1 if result["breaking_changes"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="contract-tester", description="Local API Contract Tester (MVP)")
    license_status = get_license_status()
    license_tag = "licensed" if license_status["valid"] else "demo"
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__} ({license_tag})",
    )
    parser.add_argument(
        "--license-status",
        action="store_true",
        help="Print license status and exit",
    )
    parser.add_argument(
        "--license-json",
        action="store_true",
        help="Output license status as JSON (use with --license-status)",
    )
    sub = parser.add_subparsers(dest="command")

    p_validate = sub.add_parser("validate", help="Validate traffic against an OpenAPI spec")
    p_validate.add_argument("--spec", required=True, help="Path to OpenAPI JSON/YAML")
    p_validate.add_argument("--traffic", required=True, help="Path to HAR or normalized traffic JSON")
    p_validate.add_argument(
        "--ignore-unknown",
        action="store_true",
        help="Ignore traffic entries that don't match any operation",
    )
    p_validate.add_argument(
        "--report",
        nargs="?",
        const="report.html",
        help="Write an HTML report to this path (default: report.html)",
    )
    p_validate.add_argument(
        "--max-errors",
        type=int,
        default=None,
        help="Stop after this many errors (useful for large logs)",
    )
    p_validate.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    p_validate.add_argument("--json", action="store_true", help="Output JSON")
    p_validate.set_defaults(func=_cmd_validate)

    p_diff = sub.add_parser("diff", help="Compare two OpenAPI specs for breaking changes")
    p_diff.add_argument("--old", required=True, help="Old spec")
    p_diff.add_argument("--new", required=True, help="New spec")
    p_diff.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    p_diff.add_argument("--json", action="store_true", help="Output JSON")
    p_diff.set_defaults(func=_cmd_diff)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    color = supports_color() and (not getattr(args, "no_color", False))
    try:
        if getattr(args, "license_status", False):
            status = get_license_status()
            if getattr(args, "license_json", False):
                print(json.dumps(status, indent=2))
                return 0 if status["valid"] else 1
            if status["valid"]:
                expiry = status.get("expires_on")
                suffix = f" (expires {expiry})" if expiry else ""
                print(ok(f"License: valid{suffix}", color))
                return 0
            code = status.get("code") or "unknown"
            message = status.get("message") or "Invalid license."
            print(warn(f"License: demo mode [{code}] {message}", color))
            return 1
        if not hasattr(args, "func"):
            parser.print_usage(sys.stderr)
            print(err("error: the following arguments are required: command", color), file=sys.stderr)
            return 2
        return args.func(args)
    except FileNotFoundError as exc:
        print(err(f"File not found: {exc.filename}", color), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(err(f"Invalid input: {exc}", color), file=sys.stderr)
        return 2
    except Exception as exc:
        print(err(f"Unexpected error: {exc}", color), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
