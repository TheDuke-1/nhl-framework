#!/usr/bin/env python3
"""
Upgrade backlog fields with true-source inputs where available.

Current true-source upgrades are applied to the latest verified season only.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERIFIED_DIR = PROJECT_ROOT / "data" / "historical" / "verified"
BACKLOG_DIR = VERIFIED_DIR / "backlog"
INJURIES_PATH = PROJECT_ROOT / "data" / "injuries.json"
COACHING_PATH = PROJECT_ROOT / "data" / "coaching-data.json"
POWERPLAY_PATH = PROJECT_ROOT / "data" / "powerplay-data.json"
H2H_PATH = PROJECT_ROOT / "data" / "head-to-head.json"
OUT_JSON = PROJECT_ROOT / "reports" / "phase4_true_source_upgrade.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE4_TRUE_SOURCE_UPGRADE.md"


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def main() -> int:
    seasons = sorted(int(p.stem.split("_")[1]) for p in VERIFIED_DIR.glob("season_*.json"))
    if not seasons:
        raise SystemExit("No verified season files found")
    target_season = max(seasons)

    season_path = VERIFIED_DIR / f"season_{target_season}.json"
    backlog_path = BACKLOG_DIR / f"season_{target_season}.json"
    if not backlog_path.exists():
        raise SystemExit(f"Missing backlog file: {backlog_path}")

    with open(season_path) as f:
        season_payload = json.load(f)
    with open(backlog_path) as f:
        backlog_payload = json.load(f)
    with open(INJURIES_PATH) as f:
        injuries = json.load(f).get("teams", {})
    with open(COACHING_PATH) as f:
        coaches = json.load(f).get("coaches", {})
    with open(POWERPLAY_PATH) as f:
        pp = json.load(f).get("teams", {})
    with open(H2H_PATH) as f:
        h2h = json.load(f).get("records", {})

    teams = season_payload.get("teams", {})
    backlog_teams = backlog_payload.setdefault("teams", {})

    counts = {
        "injury_adjusted_strength": 0,
        "coach_system_continuity": 0,
        "discipline_taken_drawn_split": 0,
        "schedule_travel_rest_load": 0,
    }

    for team, row in teams.items():
        b = backlog_teams.setdefault(team, {})

        # 1) Injury-adjusted strength from true injuries file.
        injury_row = injuries.get(team, {})
        war_lost = float(injury_row.get("totalWarLost", 0.0) or 0.0)
        injury_adj = _clip(1.0 - (war_lost / 10.0))
        b["injury_adjusted_strength"] = round(injury_adj, 4)
        counts["injury_adjusted_strength"] += 1

        # 2) Coach continuity from true coaching file.
        years = float((coaches.get(team, {}) or {}).get("yearsAsHeadCoach", 0.0) or 0.0)
        continuity = _clip(years / 8.0)
        b["coach_system_continuity"] = round(continuity, 4)
        counts["coach_system_continuity"] += 1

        # 3) Discipline profile from true PP rank/pct + season PK%.
        pp_row = pp.get(team, {})
        pp_pct = float(pp_row.get("ppPct", row.get("ppPct", 20.0)) or 20.0)
        pk_pct = float(row.get("pkPct", 80.0) or 80.0)
        discipline = _clip((0.5 * (pp_pct - 10.0) / 25.0) + (0.5 * (pk_pct - 70.0) / 25.0))
        b["discipline_taken_drawn_split"] = round(discipline, 4)
        counts["discipline_taken_drawn_split"] += 1

        # 4) Schedule/travel load from head-to-head game concentration.
        # More games vs fewer opponents implies tighter divisional concentration.
        rec = h2h.get(team, {}) if isinstance(h2h, dict) else {}
        total_games = 0.0
        opp_count = 0
        for opp, stats in rec.items():
            opp_count += 1
            total_games += float(stats.get("wins", 0) or 0)
            total_games += float(stats.get("losses", 0) or 0)
            total_games += float(stats.get("otl", 0) or 0)
        concentration = _clip((total_games / max(1.0, opp_count)) / 4.0)
        b["schedule_travel_rest_load"] = round(concentration, 4)
        counts["schedule_travel_rest_load"] += 1

    meta = backlog_payload.setdefault("_metadata", {})
    meta["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    meta["trueSourceUpgrade"] = {
        "season": target_season,
        "sources": {
            "injury_adjusted_strength": "data/injuries.json",
            "coach_system_continuity": "data/coaching-data.json",
            "discipline_taken_drawn_split": "data/powerplay-data.json + season pkPct",
            "schedule_travel_rest_load": "data/head-to-head.json",
        },
        "notes": "Upgraded fields use true in-repo source signals for latest verified season; remaining backlog fields still proxy-populated.",
    }

    with open(backlog_path, "w") as f:
        json.dump(backlog_payload, f, indent=2)

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "phase4_true_source_upgrade",
        "targetSeason": target_season,
        "fieldUpdates": counts,
        "teamsUpdated": len(teams),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 4 True-Source Upgrade",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"Target Season: `{target_season}`",
        f"Teams Updated: `{len(teams)}`",
        "",
        "## Field Updates",
        "",
        "| Field | Team Rows Updated |",
        "|---|---:|",
    ]
    for field, n in counts.items():
        lines.append(f"| {field} | {n} |")
    lines += [
        "",
        "## Source Notes",
        "",
        "- `injury_adjusted_strength`: `data/injuries.json`",
        "- `coach_system_continuity`: `data/coaching-data.json`",
        "- `discipline_taken_drawn_split`: `data/powerplay-data.json` + season `pkPct`",
        "- `schedule_travel_rest_load`: `data/head-to-head.json`",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")

    print(f"Upgraded true-source fields for season {target_season}")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
