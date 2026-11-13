"""Command-line interface and output formatting."""

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from typing import List, Optional, Sequence

from linux_healthcheck import __version__
from linux_healthcheck.checks import CHECK_FUNCTIONS, DEFAULT_CHECKS, collect_checks
from linux_healthcheck.host import Host
from linux_healthcheck.models import CheckResult, STATUS_ORDER


SYMBOLS = {"ok": "OK", "skip": "SKIP", "warning": "WARN", "critical": "CRIT"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="linux-healthcheck",
        description="Run portable, read-only Linux health checks.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--check",
        action="append",
        choices=sorted(CHECK_FUNCTIONS),
        dest="checks",
        help="Run only this check; repeat for multiple checks",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _overall(results: Sequence[CheckResult]) -> str:
    if any(result.status == "critical" for result in results):
        return "critical"
    if any(result.status == "warning" for result in results):
        return "warning"
    return "ok"


def _print_text(results: Sequence[CheckResult]) -> None:
    print(f"Linux health check {__version__}")
    for result in results:
        print(f"[{SYMBOLS[result.status]:4}] {result.title}: {result.summary}")
        for line in result.details:
            print(f"       - {line}")
    print(f"Overall: {_overall(results).upper()}")


def _print_json(results: Sequence[CheckResult]) -> None:
    payload = {
        "tool": "linux-healthcheck",
        "version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": _overall(results),
        "checks": [result.as_dict() for result in results],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: Optional[List[str]] = None, host: Optional[Host] = None) -> int:
    args = build_parser().parse_args(argv)
    if platform.system() != "Linux":
        print("linux-healthcheck can only inspect a Linux host.", file=sys.stderr)
        return 2

    selected = args.checks or list(DEFAULT_CHECKS)
    try:
        results = collect_checks(host or Host(), selected)
    except (KeyError, OSError, ValueError) as error:
        print(f"health check failed: {error}", file=sys.stderr)
        return 2

    if args.json:
        _print_json(results)
    else:
        _print_text(results)

    return 1 if max((STATUS_ORDER[result.status] for result in results), default=0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
