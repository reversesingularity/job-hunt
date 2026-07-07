"""JobHunt CLI — discover, score, tailor, render."""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from services.orchestrator.pipeline import discover, run_pipeline, score_all, tailor_job
from services.scoring.location_filter import parse_location_filter


def _add_location_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--location",
        metavar="CODES",
        help="Comma-separated region filter for shortlist (e.g. au,nz)",
    )


def _parse_location(args: argparse.Namespace) -> list[str] | None:
    return parse_location_filter(getattr(args, "location", None))


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser(prog="jobhunt", description="Honest job acquisition engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_disc = sub.add_parser("discover", help="Fetch jobs from APIs")
    p_disc.add_argument("--dry-run", action="store_true", help="Fetch only, no DB write")

    p_score = sub.add_parser("score", help="Score all fetched jobs")
    _add_location_arg(p_score)

    p_tailor = sub.add_parser("tailor", help="Tailor CV for a job")
    p_tailor.add_argument("--job-id", type=int, required=True)

    p_run = sub.add_parser("run", help="Full pipeline: discover -> score -> tailor -> PDF")
    p_run.add_argument("--top", type=int, default=10)
    p_run.add_argument("--dry-run", action="store_true")
    _add_location_arg(p_run)

    p_render = sub.add_parser("render", help="Alias for tailor (includes PDF)")
    p_render.add_argument("--job-id", type=int, required=True)

    args = ap.parse_args()
    location_codes = _parse_location(args) if args.cmd in ("run", "score") else None

    if args.cmd == "discover":
        discover(dry_run=args.dry_run)
    elif args.cmd == "score":
        shortlist = score_all(location_codes=location_codes)
        print(f"Shortlist: {len(shortlist)} jobs")
    elif args.cmd in ("tailor", "render"):
        result = tailor_job(args.job_id)
        print(result)
    elif args.cmd == "run":
        run_pipeline(top=args.top, dry_run=args.dry_run, location_codes=location_codes)


if __name__ == "__main__":
    main()
