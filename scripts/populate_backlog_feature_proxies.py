#!/usr/bin/env python3
"""
Populate backlog feature files with deterministic season-level proxy values.

These are transparent proxy values (not true source-integrated measurements)
to support testing, wiring, and non-null feature pipelines.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERIFIED_DIR = PROJECT_ROOT / "data" / "historical" / "verified"
BACKLOG_DIR = VERIFIED_DIR / "backlog"
COACHING_PATH = PROJECT_ROOT / "data" / "coaching-data.json"


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _pdo_to_100_scale(v: float) -> float:
    # Some files store PDO around 1.000 and some around 100.
    if v is None:
        return 100.0
    return float(v * 100.0 if v <= 2.0 else v)


def _season_payloads(season: int) -> Tuple[Dict, Dict]:
    season_path = VERIFIED_DIR / f"season_{season}.json"
    with open(season_path) as f:
        season_payload = json.load(f)

    adv_path = VERIFIED_DIR / "advanced" / f"season_{season}.json"
    advanced_payload = {}
    if adv_path.exists():
        with open(adv_path) as f:
            advanced_payload = json.load(f)
    return season_payload, advanced_payload


def _compute_proxy_features(team_data: Dict, adv_data: Dict, coach_years: float) -> Dict[str, float]:
    gp = max(1.0, float(team_data.get("gp", 82) or 82))
    pts_pct = float(team_data.get("ptsPct", 0.5) or 0.5)
    cf_pct = float(team_data.get("cfPct", 50.0) or 50.0)
    hdcf_pct = float(team_data.get("hdcfPct", 50.0) or 50.0)
    sv_pct = float(team_data.get("svPct", 91.0) or 91.0)
    pdo_100 = _pdo_to_100_scale(team_data.get("pdo"))
    pp_pct = float(team_data.get("ppPct", 20.0) or 20.0)
    pk_pct = float(team_data.get("pkPct", 80.0) or 80.0)
    road_w = float(team_data.get("roadW", 0) or 0)
    road_l = float(team_data.get("roadL", 0) or 0)
    road_otl = float(team_data.get("roadOTL", 0) or 0)
    home_w = float(team_data.get("homeW", 0) or 0)
    home_l = float(team_data.get("homeL", 0) or 0)
    home_otl = float(team_data.get("homeOTL", 0) or 0)
    gd = float(team_data.get("gd", 0.0) or 0.0)
    gd_per_game = gd / gp
    playoff_rounds = float(team_data.get("playoffRoundsWon", 0) or 0)

    adv_xgf_pct = float((adv_data or {}).get("xgfPct", team_data.get("xgfPct", 50.0)) or 50.0)

    home_gp = max(1.0, home_w + home_l + home_otl)
    road_gp = max(1.0, road_w + road_l + road_otl)
    home_win_pct = 100.0 * home_w / home_gp
    road_win_pct = 100.0 * road_w / road_gp

    # Proxy features in [0, 1], where higher indicates stronger positive signal
    goalie_dependency = _clip((abs(pdo_100 - 100.0) * 0.08) + max(0.0, sv_pct - 91.0) * 0.12)
    backup_dropoff = _clip((91.2 - sv_pct) / 2.5)

    # Positive value means results exceeded expected profile.
    expected_gap = pts_pct - (adv_xgf_pct / 100.0)
    injury_adjusted_strength = _clip(0.5 + expected_gap * 2.0)

    score_state_adjusted = _clip((((0.40 * cf_pct) + (0.40 * adv_xgf_pct) + (0.20 * hdcf_pct)) - 45.0) / 15.0)
    travel_rest_load = _clip((home_win_pct - road_win_pct + 5.0) / 30.0)
    discipline_profile = _clip((0.55 * ((pk_pct - 75.0) / 20.0)) + (0.45 * ((pp_pct - 15.0) / 15.0)))
    deadline_delta = _clip(0.45 + (0.60 * gd_per_game) + (0.30 * (pts_pct - 0.5)) + (0.08 * playoff_rounds))
    playoff_style = _clip((((0.55 * hdcf_pct) + (0.30 * cf_pct) + (0.15 * (50.0 + 5.0 * gd_per_game))) - 45.0) / 15.0)
    coach_continuity = _clip((coach_years - 1.0) / 6.0)

    return {
        "goalie_usage_starter_load": round(goalie_dependency, 4),
        "goalie_backup_dropoff": round(backup_dropoff, 4),
        "injury_adjusted_strength": round(injury_adjusted_strength, 4),
        "score_state_adjusted_5v5_close_game": round(score_state_adjusted, 4),
        "schedule_travel_rest_load": round(travel_rest_load, 4),
        "discipline_taken_drawn_split": round(discipline_profile, 4),
        "trade_deadline_roster_delta": round(deadline_delta, 4),
        "playoff_style_netfront_rush_forecheck": round(playoff_style, 4),
        "coach_system_continuity": round(coach_continuity, 4),
    }


def main() -> int:
    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)
    season_files = sorted(VERIFIED_DIR.glob("season_*.json"))
    with open(COACHING_PATH) as f:
        coaching = json.load(f).get("coaches", {})

    updated_files = 0
    total_cells_set = 0
    total_cells = 0

    for sf in season_files:
        season = int(sf.stem.split("_")[1])
        season_payload, advanced_payload = _season_payloads(season)
        season_teams = season_payload.get("teams", {})

        backlog_path = BACKLOG_DIR / f"season_{season}.json"
        if backlog_path.exists():
            with open(backlog_path) as f:
                backlog_payload = json.load(f)
        else:
            backlog_payload = {"_metadata": {"season": season}, "teams": {}}

        teams_node = backlog_payload.setdefault("teams", {})
        changed = False

        for team, tdata in season_teams.items():
            coach_years = float((coaching.get(team, {}) or {}).get("yearsAsHeadCoach", 2) or 2)
            proxy_vals = _compute_proxy_features(tdata, advanced_payload.get(team, {}), coach_years)
            team_row = teams_node.setdefault(team, {k: None for k in proxy_vals.keys()})
            for k, v in proxy_vals.items():
                total_cells += 1
                if team_row.get(k) is None:
                    team_row[k] = v
                    changed = True
                if team_row.get(k) is not None:
                    total_cells_set += 1

        meta = backlog_payload.setdefault("_metadata", {})
        meta["lastUpdated"] = datetime.now(timezone.utc).isoformat()
        meta["proxyVersion"] = "phase4-proxy-v1"
        meta["proxyNotes"] = "Deterministic proxy values from season aggregates; replace with true source data when available."
        if changed:
            with open(backlog_path, "w") as f:
                json.dump(backlog_payload, f, indent=2)
            updated_files += 1

    coverage = (total_cells_set / total_cells) if total_cells else 0.0
    print(f"Updated backlog files: {updated_files}")
    print(f"Backlog proxy coverage: {coverage:.3f} ({total_cells_set}/{total_cells})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
