from __future__ import annotations

import argparse
import json
from pathlib import Path

from apps.quant_platform.research.publishing import publish_research_snapshot
from apps.quant_platform.research.scripts.run_factor_research import run_full_factor_research


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish research serving snapshots for the frontend.")
    parser.add_argument("--from-db", action="store_true", help="Refresh the full research outputs from tushare_database before publishing.")
    parser.add_argument("--start-date", default="2018-01-01")
    parser.add_argument("--end-date")
    parser.add_argument("--output-dir", default="apps/quant_platform/research/output/full_research")
    parser.add_argument("--publish-dir")
    parser.add_argument("--picks-limit", type=int, default=20)
    parser.add_argument(
        "--skip-chip-distribution",
        action="store_true",
        help="Skip stock_cyq_chips when refreshing from the database before publishing.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    result: dict[str, object] = {}
    if args.from_db:
        result["research"] = run_full_factor_research(
            start_date=args.start_date,
            end_date=args.end_date,
            output_dir=output_dir,
            include_chip_distribution=not args.skip_chip_distribution,
        )

    manifest = publish_research_snapshot(
        output_root=output_dir.parent,
        full_research_dir=output_dir,
        publish_dir=args.publish_dir,
        picks_limit=args.picks_limit,
    )
    result["snapshot"] = manifest
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
