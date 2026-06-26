#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Run repeatable RWA Risk Sentinel demo cycles.")
    parser.add_argument("--asset", default="invoice-2026-001")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--real", action="store_true", help="submit as non-dry-run; requires real Casper publisher")
    args = parser.parse_args()

    for i in range(args.count):
        resp = requests.post(
            f"{args.base_url}/agent/run",
            json={"asset_id": args.asset, "dry_run": not args.real, "force_publish": True},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        print(json.dumps({
            "cycle": i + 1,
            "asset": payload["report"]["asset_id"],
            "score_bps": payload["report"]["score_bps"],
            "band": payload["report"]["band"],
            "evidence_hash": payload["report"]["evidence_hash"],
            "deploy_hash": payload["casper"].get("deploy_hash"),
            "dry_run": payload["casper"].get("dry_run"),
        }, indent=2))
        time.sleep(1)


if __name__ == "__main__":
    main()
