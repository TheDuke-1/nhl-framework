#!/usr/bin/env python3
"""
Backfill historical advanced-metric override files.

Creates `data/historical/verified/advanced/season_YYYY.json` files with
best-available advanced metrics:
- provider values when available
- conservative proxy fallback to reach full-team coverage
"""

import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERIFIED_DIR = PROJECT_ROOT / "data" / "historical" / "verified"
ADVANCED_DIR = VERIFIED_DIR / "advanced"


def _estimate_expected_goal_profile(goals_for: int, goals_against: int, cf_pct: float, hdcf_pct: float):
    xgf_pct_proxy = min(65.0, max(35.0, (0.65 * cf_pct) + (0.35 * hdcf_pct)))
    xgf_proxy = max(0.0, goals_for * (xgf_pct_proxy / 50.0))
    xga_proxy = max(0.0, goals_against * ((100.0 - xgf_pct_proxy) / 50.0))
    return xgf_proxy, xga_proxy, xgf_pct_proxy


def _estimate_gsax_proxy(save_pct_decimal: float, games_played: int, ca: int) -> float:
    league_sv = 0.910
    shots_against_est = (ca * 0.55) if ca > 0 else (games_played * 30.0)
    shots_against_est = max(1000.0, shots_against_est)
    gsax = (save_pct_decimal - league_sv) * shots_against_est
    return max(-40.0, min(40.0, gsax))


def build_2024_best_available(fill_proxy: bool = False, fill_xg_only: bool = False) -> int:
    """
    Build 2024 overrides with provider-first policy.
    - default: provider-only rows
    - --fill-proxy: full proxy rows for all teams (xG + GSAX)
    - --fill-xg-only: full xG rows for all teams, GSAX only from provider
    """
    archived_src = PROJECT_ROOT / "data" / "historical" / "stats_2023_24.json"
    season_src = VERIFIED_DIR / "season_2024.json"

    if not season_src.exists():
        print(f"SKIP: season file not found: {season_src}")
        return 0

    archived = {}
    if archived_src.exists():
        archived = json.loads(archived_src.read_text())
    season_data = json.loads(season_src.read_text())
    teams = season_data.get("teams", {})
    if not teams:
        print(f"SKIP: no teams in season file: {season_src}")
        return 0

    overrides = {}
    for team, vals in teams.items():
        if not isinstance(vals, dict):
            continue

        gp = int(vals.get("gp") or 0)
        gf = int(vals.get("gf") or 0)
        ga = int(vals.get("ga") or 0)
        cf_pct = float(vals.get("cfPct") or 50.0)
        hdcf_pct = float(vals.get("hdcfPct") or 50.0)
        ca = int(vals.get("ca") or 0)
        sv_raw = float(vals.get("svPct") or 91.0)
        sv_pct_decimal = sv_raw / 100.0 if sv_raw > 1.0 else sv_raw

        xgf, xga, xgf_pct = _estimate_expected_goal_profile(gf, ga, cf_pct, hdcf_pct)
        gsax = _estimate_gsax_proxy(sv_pct_decimal, gp, ca)

        archived_team = archived.get(team)
        if isinstance(archived_team, dict) and archived_team.get("gsax") is not None:
            try:
                gsax = float(archived_team["gsax"])
            except (TypeError, ValueError):
                pass

        if fill_xg_only:
            row = {
                "xgf": round(float(xgf), 3),
                "xga": round(float(xga), 3),
                "xgfPct": round(float(xgf_pct), 3),
            }
            if isinstance(archived_team, dict) and archived_team.get("gsax") is not None:
                row["gsax"] = round(float(gsax), 3)
            overrides[team] = row
        elif isinstance(archived_team, dict) and archived_team.get("gsax") is not None:
            overrides[team] = {
                "gsax": round(float(gsax), 3),
            }
            if fill_proxy:
                overrides[team].update({
                    "xgf": round(float(xgf), 3),
                    "xga": round(float(xga), 3),
                    "xgfPct": round(float(xgf_pct), 3),
                })
        elif fill_proxy:
            overrides[team] = {
                "xgf": round(float(xgf), 3),
                "xga": round(float(xga), 3),
                "xgfPct": round(float(xgf_pct), 3),
                "gsax": round(float(gsax), 3),
            }

    if not overrides:
        print("SKIP: no override rows produced")
        return 0

    ADVANCED_DIR.mkdir(parents=True, exist_ok=True)
    out = ADVANCED_DIR / "season_2024.json"
    out.write_text(json.dumps(overrides, indent=2) + "\n")
    print(f"WROTE: {out} ({len(overrides)} teams)")
    return len(overrides)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill advanced override files")
    parser.add_argument(
        "--fill-proxy",
        action="store_true",
        help="Fill non-provider teams with proxy values (can change model behavior)",
    )
    parser.add_argument(
        "--fill-xg-only",
        action="store_true",
        help="Fill xG metrics for all teams; keep GSAX provider-only",
    )
    args = parser.parse_args()

    if args.fill_proxy and args.fill_xg_only:
        raise SystemExit("Choose only one of --fill-proxy or --fill-xg-only")

    count = build_2024_best_available(
        fill_proxy=args.fill_proxy,
        fill_xg_only=args.fill_xg_only,
    )
    print(f"Backfill complete. Rows written: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
