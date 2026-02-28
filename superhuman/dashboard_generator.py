#!/usr/bin/env python3
"""
NHL Dashboard Data Generator
==============================
Generates JSON data for the NHL Superhuman Dashboard.
Designed to run daily at 6 AM via cron/scheduler.

Output: dashboard_data.json with all predictions, odds, and metadata.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Support both module and direct-script execution.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from superhuman.predictor import SuperhumanPredictor
    from superhuman.config import (
        CURRENT_SEASON,
        DATA_DIR,
        CONFERENCES,
        select_conference_playoff_teams,
    )
else:
    from .predictor import SuperhumanPredictor
    from .config import CURRENT_SEASON, DATA_DIR, CONFERENCES, select_conference_playoff_teams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Output paths
PROJECT_DIR = Path(__file__).parent.parent
DATA_OUTPUT = PROJECT_DIR / "dashboard_data.json"
HISTORY_DIR = PROJECT_DIR / "history"
BENCHMARK_PATH = PROJECT_DIR / "reports" / "benchmark_latest.json"
RELEASE_CYCLE_LATEST_PATH = PROJECT_DIR / "reports" / "phase7_release_cycle_latest.json"
RELEASE_CYCLE_PATH = PROJECT_DIR / "reports" / "phase7_release_cycle.json"
PHASE11_PATH = PROJECT_DIR / "reports" / "phase11_constrained_edge_batch.json"
PHASE12_PATH = PROJECT_DIR / "reports" / "phase12_goal_gap_closure.json"
PHASE13_PATH = PROJECT_DIR / "reports" / "phase13_eligible_feature_push.json"
PHASE16_PATH = PROJECT_DIR / "reports" / "phase16_adaptive_learning_loop.json"
PHASE17_PATH = PROJECT_DIR / "reports" / "phase17_downside_stability_lane.json"
PHASE18_PATH = PROJECT_DIR / "reports" / "phase18_feedback_control_loop.json"
GRADE_PATH = PROJECT_DIR / "reports" / "current_model_dashboard_grade.json"
EMBEDDED_FALLBACK_PATH = PROJECT_DIR / "js" / "data.js"


# Metric definitions for glossary
METRIC_DEFINITIONS = {
    "composite_strength": {
        "name": "Composite Strength",
        "short": "Overall team power rating combining all factors",
        "formula": "Weighted average of 17 performance metrics"
    },
    "goal_differential_rate": {
        "name": "Goal Differential Rate",
        "short": "Goals scored minus goals allowed per game",
        "formula": "(GF - GA) / GP"
    },
    "territorial_dominance": {
        "name": "Territorial Dominance",
        "short": "How much a team controls play (shot attempts)",
        "formula": "Corsi For % at 5v5"
    },
    "shot_quality_premium": {
        "name": "Shot Quality Premium",
        "short": "Expected goals above league average",
        "formula": "xGF% - 50"
    },
    "goaltending_quality": {
        "name": "Goaltending Quality",
        "short": "Goals saved above expected",
        "formula": "GSAx (Goals Saved Above Expected)"
    },
    "special_teams_composite": {
        "name": "Special Teams",
        "short": "Combined power play and penalty kill effectiveness",
        "formula": "PP% + PK% - 100"
    },
    "playoff_experience": {
        "name": "Playoff Experience",
        "short": "Team's recent playoff history and success",
        "formula": "Weighted playoff rounds won (last 5 years)"
    },
    "dynasty_score": {
        "name": "Dynasty Score",
        "short": "Recent championship pedigree",
        "formula": "Recency-weighted Cup wins and Finals appearances"
    },
    "clutch_performance": {
        "name": "Clutch Performance",
        "short": "Success in close games and pressure situations",
        "formula": "One-goal wins + OT wins - Blown leads"
    },
    "vegas_cup_signal": {
        "name": "Vegas Cup Signal",
        "short": "Market consensus on Cup chances",
        "formula": "Implied probability from betting odds"
    },
    "recent_form": {
        "name": "Recent Form",
        "short": "Performance in last 10-20 games",
        "formula": "Points % in recent games vs season average"
    },
    "sustainability": {
        "name": "Sustainability",
        "short": "How likely current performance continues",
        "formula": "PDO regression to mean (100 = sustainable)"
    },
    "road_performance": {
        "name": "Road Performance",
        "short": "Ability to win away from home",
        "formula": "Road win % vs league average"
    },
    "roster_depth": {
        "name": "Roster Depth",
        "short": "Scoring balance across lineup",
        "formula": "Players with 20+ goals and 40+ points"
    },
    "star_power": {
        "name": "Star Power",
        "short": "Elite player impact",
        "formula": "Top scorer PPG vs league leaders"
    },
    "series_history_signal": {
        "name": "Series History Signal",
        "short": "Recent playoff series success trend",
        "formula": "Recency-weighted playoff rounds won (lookback seasons)"
    },
    "market_close_movement_signal": {
        "name": "Market Movement Signal",
        "short": "How market conviction has moved for Cup outlook",
        "formula": "Open-close Cup probability delta (or conditional market proxy)"
    },
    "goalie_injury_playoff_impact": {
        "name": "Goalie/Injury Impact",
        "short": "Goaltending stability adjusted for injury pressure",
        "formula": "Goalie performance support minus injury/goalie availability penalty"
    }
}

# Tier colors for dashboard
TIER_CONFIG = {
    "Elite": {"color": "#10b981", "bg": "rgba(16, 185, 129, 0.15)", "icon": "🏆"},
    "Contender": {"color": "#3b82f6", "bg": "rgba(59, 130, 246, 0.15)", "icon": "🎯"},
    "Bubble": {"color": "#f59e0b", "bg": "rgba(245, 158, 11, 0.15)", "icon": "⚡"},
    "Longshot": {"color": "#ef4444", "bg": "rgba(239, 68, 68, 0.15)", "icon": "🎲"}
}

# Team metadata
TEAM_INFO = {
    "ANA": {"name": "Anaheim Ducks", "city": "Anaheim", "conference": "West", "division": "Pacific"},
    "BOS": {"name": "Boston Bruins", "city": "Boston", "conference": "East", "division": "Atlantic"},
    "BUF": {"name": "Buffalo Sabres", "city": "Buffalo", "conference": "East", "division": "Atlantic"},
    "CGY": {"name": "Calgary Flames", "city": "Calgary", "conference": "West", "division": "Pacific"},
    "CAR": {"name": "Carolina Hurricanes", "city": "Raleigh", "conference": "East", "division": "Metropolitan"},
    "CHI": {"name": "Chicago Blackhawks", "city": "Chicago", "conference": "West", "division": "Central"},
    "COL": {"name": "Colorado Avalanche", "city": "Denver", "conference": "West", "division": "Central"},
    "CBJ": {"name": "Columbus Blue Jackets", "city": "Columbus", "conference": "East", "division": "Metropolitan"},
    "DAL": {"name": "Dallas Stars", "city": "Dallas", "conference": "West", "division": "Central"},
    "DET": {"name": "Detroit Red Wings", "city": "Detroit", "conference": "East", "division": "Atlantic"},
    "EDM": {"name": "Edmonton Oilers", "city": "Edmonton", "conference": "West", "division": "Pacific"},
    "FLA": {"name": "Florida Panthers", "city": "Sunrise", "conference": "East", "division": "Atlantic"},
    "LA": {"name": "Los Angeles Kings", "city": "Los Angeles", "conference": "West", "division": "Pacific"},
    "MIN": {"name": "Minnesota Wild", "city": "Saint Paul", "conference": "West", "division": "Central"},
    "MTL": {"name": "Montreal Canadiens", "city": "Montreal", "conference": "East", "division": "Atlantic"},
    "NSH": {"name": "Nashville Predators", "city": "Nashville", "conference": "West", "division": "Central"},
    "NJ": {"name": "New Jersey Devils", "city": "Newark", "conference": "East", "division": "Metropolitan"},
    "NYI": {"name": "New York Islanders", "city": "Elmont", "conference": "East", "division": "Metropolitan"},
    "NYR": {"name": "New York Rangers", "city": "New York", "conference": "East", "division": "Metropolitan"},
    "OTT": {"name": "Ottawa Senators", "city": "Ottawa", "conference": "East", "division": "Atlantic"},
    "PHI": {"name": "Philadelphia Flyers", "city": "Philadelphia", "conference": "East", "division": "Metropolitan"},
    "PIT": {"name": "Pittsburgh Penguins", "city": "Pittsburgh", "conference": "East", "division": "Metropolitan"},
    "SJ": {"name": "San Jose Sharks", "city": "San Jose", "conference": "West", "division": "Pacific"},
    "SEA": {"name": "Seattle Kraken", "city": "Seattle", "conference": "West", "division": "Pacific"},
    "STL": {"name": "St. Louis Blues", "city": "St. Louis", "conference": "West", "division": "Central"},
    "TB": {"name": "Tampa Bay Lightning", "city": "Tampa", "conference": "East", "division": "Atlantic"},
    "TOR": {"name": "Toronto Maple Leafs", "city": "Toronto", "conference": "East", "division": "Atlantic"},
    "UTA": {"name": "Utah Hockey Club", "city": "Salt Lake City", "conference": "West", "division": "Central"},
    "VAN": {"name": "Vancouver Canucks", "city": "Vancouver", "conference": "West", "division": "Pacific"},
    "VGK": {"name": "Vegas Golden Knights", "city": "Las Vegas", "conference": "West", "division": "Pacific"},
    "WSH": {"name": "Washington Capitals", "city": "Washington", "conference": "East", "division": "Metropolitan"},
    "WPG": {"name": "Winnipeg Jets", "city": "Winnipeg", "conference": "West", "division": "Central"},
}


def build_actual_bracket() -> Optional[Dict]:
    """Build actual bracket from current NHL standings using real seeding rules."""
    standings_file = PROJECT_DIR / "data" / "nhl_standings.json"
    if not standings_file.exists():
        logger.warning("No standings file found for actual bracket")
        return None

    try:
        with open(standings_file) as f:
            standings = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load standings: {e}")
        return None

    teams_data = standings.get("teams", {})
    if not teams_data:
        return None

    result = {"East": {}, "West": {}, "cupFinal": None, "status": "pre-playoff"}

    for conf_name, divisions in CONFERENCES.items():
        conf_teams = []
        for div_name, div_teams in divisions.items():
            for team_code in div_teams:
                if team_code in teams_data:
                    t = teams_data[team_code]
                    conf_teams.append({
                        "team": team_code,
                        "pts": t.get("pts", 0),
                        "div": div_name,
                        "gp": t.get("gp", 0),
                        "w": t.get("w", 0),
                    })

        # Group by division within conference
        div_groups = {}
        for t in conf_teams:
            div_groups.setdefault(t["div"], []).append(t)
        for div in div_groups:
            div_groups[div].sort(key=lambda t: -t["pts"])

        div_names = sorted(div_groups.keys())
        if len(div_names) != 2:
            continue

        div_a_name, div_b_name = div_names[0], div_names[1]
        div_a = div_groups[div_a_name]
        div_b = div_groups[div_b_name]

        # Top 3 per division
        # Wildcards from remaining
        remaining = div_a[3:] + div_b[3:]
        remaining.sort(key=lambda t: -t["pts"])
        wildcards = remaining[:2]

        # Division winners
        dw_a = div_a[0] if div_a else None
        dw_b = div_b[0] if div_b else None

        if not dw_a or not dw_b:
            continue

        # Seed 1 = div winner with more pts, seed 2 = other
        if dw_a["pts"] >= dw_b["pts"]:
            seed1, seed1_div = dw_a, div_a_name
            seed2, seed2_div = dw_b, div_b_name
        else:
            seed1, seed1_div = dw_b, div_b_name
            seed2, seed2_div = dw_a, div_a_name

        wc1 = wildcards[0] if len(wildcards) > 0 else None
        wc2 = wildcards[1] if len(wildcards) > 1 else None

        # Get 2nd and 3rd from each division
        s1_div_teams = div_groups[seed1_div]
        s2_div_teams = div_groups[seed2_div]

        # Build seed list
        seeds = [
            {"team": seed1["team"], "seed": f"{seed1_div[0]}1", "pts": seed1["pts"], "div": seed1_div},
            {"team": s1_div_teams[1]["team"] if len(s1_div_teams) > 1 else "?",
             "seed": f"{seed1_div[0]}2", "pts": s1_div_teams[1]["pts"] if len(s1_div_teams) > 1 else 0,
             "div": seed1_div},
            {"team": s1_div_teams[2]["team"] if len(s1_div_teams) > 2 else "?",
             "seed": f"{seed1_div[0]}3", "pts": s1_div_teams[2]["pts"] if len(s1_div_teams) > 2 else 0,
             "div": seed1_div},
            {"team": seed2["team"], "seed": f"{seed2_div[0]}1", "pts": seed2["pts"], "div": seed2_div},
            {"team": s2_div_teams[1]["team"] if len(s2_div_teams) > 1 else "?",
             "seed": f"{seed2_div[0]}2", "pts": s2_div_teams[1]["pts"] if len(s2_div_teams) > 1 else 0,
             "div": seed2_div},
            {"team": s2_div_teams[2]["team"] if len(s2_div_teams) > 2 else "?",
             "seed": f"{seed2_div[0]}3", "pts": s2_div_teams[2]["pts"] if len(s2_div_teams) > 2 else 0,
             "div": seed2_div},
            {"team": wc1["team"] if wc1 else "?", "seed": "WC1", "pts": wc1["pts"] if wc1 else 0, "div": wc1["div"] if wc1 else ""},
            {"team": wc2["team"] if wc2 else "?", "seed": "WC2", "pts": wc2["pts"] if wc2 else 0, "div": wc2["div"] if wc2 else ""},
        ]

        # R1 matchups (real NHL bracket)
        round1 = [
            {"higher": seed1["team"], "lower": wc2["team"] if wc2 else "?",
             "higherSeed": seeds[0]["seed"], "lowerSeed": "WC2"},
            {"higher": s1_div_teams[1]["team"] if len(s1_div_teams) > 1 else "?",
             "lower": s1_div_teams[2]["team"] if len(s1_div_teams) > 2 else "?",
             "higherSeed": seeds[1]["seed"], "lowerSeed": seeds[2]["seed"]},
            {"higher": seed2["team"], "lower": wc1["team"] if wc1 else "?",
             "higherSeed": seeds[3]["seed"], "lowerSeed": "WC1"},
            {"higher": s2_div_teams[1]["team"] if len(s2_div_teams) > 1 else "?",
             "lower": s2_div_teams[2]["team"] if len(s2_div_teams) > 2 else "?",
             "higherSeed": seeds[4]["seed"], "lowerSeed": seeds[5]["seed"]},
        ]

        result[conf_name] = {
            "seeds": seeds,
            "round1": round1,
            "round2": [],
            "confFinal": None,
        }

    return result


def build_projected_bracket(mc_result) -> Dict:
    """Transform Monte Carlo results into full projected bracket with R2+ matchups."""
    bracket = {
        "East": {},
        "West": {},
        "cupFinal": [],
        "champion": None,
        "projectedSeeds": {},
        "coherentPath": {},
    }

    if not mc_result:
        return bracket

    # Build projected seeds per conference using NHL rules:
    # Top 3 per division + 2 best remaining as wildcards
    if mc_result.projected_standings:
        for conf_name in ["East", "West"]:
            seeds = select_conference_playoff_teams(conf_name, mc_result.projected_standings)
            bracket["projectedSeeds"][conf_name] = [
                {"team": code, "projectedPts": round(pts, 1)}
                for code, pts in seeds
            ]

    for conf in ["East", "West"]:
        # R1 matchups (deterministic from seeding)
        r1 = []
        for higher, lower, higher_win_prob in mc_result.projected_matchups.get(conf, []):
            r1.append({
                "higher": higher,
                "lower": lower,
                "higherWinProb": round(higher_win_prob * 100, 1),
            })

        # R2 matchups per bracket slot (slot 0 = top half, slot 1 = bottom half)
        r2 = []
        conf_r2_slots = mc_result.r2_matchups.get(conf, [[], []])
        conf_r2_slots = (conf_r2_slots + [[], []])[:2]  # Guarantee exactly 2 slots
        for slot_idx, slot_matchups in enumerate(conf_r2_slots):
            slot_list = []
            for matchup_data in slot_matchups:
                a, b, a_win_prob, freq = matchup_data
                slot_list.append({
                    "teamA": a,
                    "teamB": b,
                    "teamAWinProb": round(a_win_prob * 100, 1),
                    "matchupProb": round(freq * 100, 1),
                })
            r2.append({"slot": slot_idx, "matchups": slot_list})

        # Conference Final matchups
        cf = []
        for matchup_data in mc_result.conf_final_matchups.get(conf, []):
            a, b, a_win_prob, freq = matchup_data
            cf.append({
                "teamA": a,
                "teamB": b,
                "teamAWinProb": round(a_win_prob * 100, 1),
                "matchupProb": round(freq * 100, 1),
            })

        bracket[conf] = {
            "round1": r1,
            "round2": r2,  # 2 slots, each with ranked matchups
            "confFinal": cf[:3],
        }

    # Cup Final matchups
    for matchup_data in mc_result.cup_final_matchups:
        a, b, a_win_prob, freq = matchup_data
        bracket["cupFinal"].append({
            "teamA": a,
            "teamB": b,
            "teamAWinProb": round(a_win_prob * 100, 1),
            "matchupProb": round(freq * 100, 1),
        })
    bracket["cupFinal"] = bracket["cupFinal"][:5]  # Top 5

    # Champion (highest cup probability team)
    if mc_result.cup_probabilities:
        best_team = max(mc_result.cup_probabilities, key=mc_result.cup_probabilities.get)
        bracket["champion"] = {
            "team": best_team,
            "probability": round(mc_result.cup_probabilities[best_team] * 100, 1),
        }

    def _r1_pick(matchup: Dict) -> str:
        return matchup["higher"] if float(matchup.get("higherWinProb", 0.0)) >= 50.0 else matchup["lower"]

    def _select_matchup(matchups: List[Dict], team_a: Optional[str], team_b: Optional[str]) -> Optional[Dict]:
        if not matchups:
            return None
        if team_a and team_b:
            target = {team_a, team_b}
            for row in matchups:
                if {row.get("teamA"), row.get("teamB")} == target:
                    return row
        return matchups[0]

    coherent_path: Dict[str, Dict] = {}
    conf_champions: Dict[str, Optional[str]] = {"East": None, "West": None}
    for conf in ("East", "West"):
        conf_data = bracket.get(conf, {})
        r1 = conf_data.get("round1", [])
        r2_slots = conf_data.get("round2", [])
        cf = conf_data.get("confFinal", [])

        r1_winners = [_r1_pick(row) for row in r1]

        slot_by_idx = {int(slot.get("slot", idx)): slot for idx, slot in enumerate(r2_slots)}
        slot0_matchups = (slot_by_idx.get(0) or {}).get("matchups", [])
        slot1_matchups = (slot_by_idx.get(1) or {}).get("matchups", [])
        slot0_sel = _select_matchup(
            slot0_matchups,
            r1_winners[0] if len(r1_winners) > 0 else None,
            r1_winners[1] if len(r1_winners) > 1 else None,
        )
        slot1_sel = _select_matchup(
            slot1_matchups,
            r1_winners[2] if len(r1_winners) > 2 else None,
            r1_winners[3] if len(r1_winners) > 3 else None,
        )

        def _pick_series_winner(matchup: Optional[Dict]) -> Optional[str]:
            if not matchup:
                return None
            return matchup.get("teamA") if float(matchup.get("teamAWinProb", 0.0)) >= 50.0 else matchup.get("teamB")

        r2_winner_a = _pick_series_winner(slot0_sel)
        r2_winner_b = _pick_series_winner(slot1_sel)
        cf_sel = _select_matchup(cf, r2_winner_a, r2_winner_b)
        conf_winner = _pick_series_winner(cf_sel)

        coherent_path[conf] = {
            "round1Winners": r1_winners,
            "round2Selected": [slot0_sel, slot1_sel],
            "round2Winners": [r2_winner_a, r2_winner_b],
            "confFinalSelected": cf_sel,
            "confChampion": conf_winner,
        }
        conf_champions[conf] = conf_winner

    cup_top = _select_matchup(
        bracket.get("cupFinal", []),
        conf_champions.get("East"),
        conf_champions.get("West"),
    )
    if not cup_top and conf_champions.get("East") and conf_champions.get("West"):
        cup_top = {
            "teamA": conf_champions["East"],
            "teamB": conf_champions["West"],
            "teamAWinProb": 50.0,
            "matchupProb": 0.0,
        }

    path_champion = None
    if cup_top:
        path_winner = cup_top.get("teamA") if float(cup_top.get("teamAWinProb", 0.0)) >= 50.0 else cup_top.get("teamB")
        path_prob = max(float(cup_top.get("teamAWinProb", 0.0)), 100.0 - float(cup_top.get("teamAWinProb", 0.0)))
        path_champion = {
            "team": path_winner,
            "probability": round(path_prob, 1),
            "source": "coherent_path",
        }

    coherent_path["cupFinalSelected"] = cup_top
    coherent_path["champion"] = path_champion
    bracket["coherentPath"] = coherent_path

    return bracket


def load_source_freshness() -> Dict[str, Optional[str]]:
    """
    Load per-source freshness timestamps from the merged teams metadata.
    """
    freshness = {"nhl": None, "moneypuck": None, "nst": None, "odds": None}
    teams_file = DATA_DIR / "teams.json"
    if not teams_file.exists():
        return freshness

    try:
        with open(teams_file) as f:
            teams_data = json.load(f)
        sources = teams_data.get("_metadata", {}).get("sources", {})
        freshness["nhl"] = sources.get("nhl_api")
        freshness["moneypuck"] = sources.get("moneypuck")
        freshness["nst"] = sources.get("nst")
        freshness["odds"] = sources.get("odds")
    except Exception as e:
        logger.warning(f"Could not load source freshness metadata: {e}")

    return freshness


def generate_dashboard_data() -> Dict:
    """Generate complete dashboard data from model predictions."""
    logger.info("Generating dashboard data...")

    # Run predictions
    predictor = SuperhumanPredictor()
    predictor.predict()

    # Load injury data (if available)
    injury_data = {}
    injuries_file = PROJECT_DIR / "data" / "injuries.json"
    if injuries_file.exists():
        try:
            with open(injuries_file) as f:
                raw_injuries = json.load(f)
            injury_data = raw_injuries.get("teams", {})
            logger.info(f"Loaded injury data for {len(injury_data)} teams")
        except Exception as e:
            logger.warning(f"Failed to load injuries: {e}")

    # Build team data
    teams = []
    for i, result in enumerate(predictor.results, 1):
        team_code = result.team
        team_meta = TEAM_INFO.get(team_code, {"name": team_code, "city": "", "conference": "East", "division": ""})
        tier_config = TIER_CONFIG.get(result.tier, TIER_CONFIG["Longshot"])
        team_injury = injury_data.get(team_code, {})

        teams.append({
            "rank": i,
            "code": team_code,
            "name": team_meta["name"],
            "city": team_meta["city"],
            "conference": team_meta["conference"],
            "division": team_meta["division"],
            "tier": result.tier,
            "tierColor": tier_config["color"],
            "tierBg": tier_config["bg"],
            "tierIcon": tier_config["icon"],
            "compositeStrength": round(result.composite_strength, 1),
            "strengthRank": result.strength_rank,
            "playoffProbability": round(result.playoff_probability * 100, 1),
            "conferenceProbability": round(result.conference_final_probability * 100, 2),  # P(reach conf final) = P(win R2)
            "cupFinalProbability": round(result.cup_final_probability * 100, 2),
            "cupProbability": round(result.cup_win_probability * 100, 2),
            "cupProbLower": round(result.cup_prob_lower * 100, 2),
            "cupProbUpper": round(result.cup_prob_upper * 100, 2),
            "injuries": team_injury.get("injuries", []),
            "totalWarLost": team_injury.get("totalWarLost", 0),
        })

    # Build feature weights
    weights = []
    for name, weight in sorted(predictor.feature_weights.items(), key=lambda x: -x[1]):
        definition = METRIC_DEFINITIONS.get(name, {"name": name, "short": name})
        weights.append({
            "key": name,
            "name": definition["name"],
            "description": definition["short"],
            "weight": round(weight, 1)
        })

    # Tier summaries
    tier_summary = {tier: [] for tier in TIER_CONFIG.keys()}
    for team in teams:
        tier_summary[team["tier"]].append(team["code"])

    # Playoff picture by conference
    playoff_picture = {
        "East": sorted([t for t in teams if t["conference"] == "East"],
                      key=lambda x: -x["playoffProbability"])[:8],
        "West": sorted([t for t in teams if t["conference"] == "West"],
                      key=lambda x: -x["playoffProbability"])[:8]
    }

    # Cup favorites (top 10)
    cup_favorites = sorted(teams, key=lambda x: -x["cupProbability"])[:10]

    # Round advancement data from Monte Carlo
    mc_result = predictor.ensemble.monte_carlo_result
    round_advancement = {}
    if mc_result:
        for team_code, rounds in mc_result.round_advancement.items():
            round_advancement[team_code] = {
                "round1": round(rounds.get(1, 0) * 100, 2),
                "round2": round(rounds.get(2, 0) * 100, 2),
                "confFinal": round(rounds.get(3, 0) * 100, 2),
                "cupFinal": round(rounds.get(4, 0) * 100, 2),
                "cupWin": round(rounds.get("cup", 0) * 100, 2),
            }

    # Bracket projections from Monte Carlo + actual standings
    bracket = {
        "projected": build_projected_bracket(mc_result),
        "actual": build_actual_bracket(),
    }

    # Generate backtest report (uses cache if valid)
    backtest_data = None
    try:
        if __package__ in (None, ""):
            from superhuman.validation import generate_backtest_report
            from superhuman.data_loader import load_training_data
            from superhuman.model_profile import load_active_model_profile
        else:
            from .validation import generate_backtest_report
            from .data_loader import load_training_data
            from .model_profile import load_active_model_profile
        historical_data = load_training_data(allow_synthetic_fallback=False)
        if historical_data:
            cache_path = str(DATA_DIR / "backtest_cache.json")
            profile = load_active_model_profile()
            model_overrides = {
                "use_neural_network": bool(profile.get("use_neural_network", True)),
                "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
                "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
                "recency_decay_rate": float(profile.get("recency_decay_rate", 0.15)),
                "cup_winner_boost": float(profile.get("cup_winner_boost", 2.0)),
                "cup_market_prior_blend": float(profile.get("cup_market_prior_blend", 0.0)),
                "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
            }
            backtest_data = generate_backtest_report(
                historical_data,
                cache_path=cache_path,
                model_overrides=model_overrides,
            )
            logger.info("Backtest report ready")
    except Exception as e:
        logger.warning(f"Backtest generation failed (non-fatal): {e}")

    # Generate timestamp
    timestamp = datetime.now().isoformat()
    source_freshness = load_source_freshness()

    benchmark_data = None
    release_cycle = None
    phase11 = None
    phase12 = None
    phase13 = None
    phase16 = None
    phase17 = None
    phase18 = None
    dashboard_grade = None
    try:
        if BENCHMARK_PATH.exists():
            with open(BENCHMARK_PATH) as f:
                benchmark_data = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load benchmark data (non-fatal): {e}")
    try:
        if RELEASE_CYCLE_LATEST_PATH.exists():
            with open(RELEASE_CYCLE_LATEST_PATH) as f:
                release_cycle = json.load(f)
        elif RELEASE_CYCLE_PATH.exists():
            with open(RELEASE_CYCLE_PATH) as f:
                legacy_cycle = json.load(f)
            release_cycle = {
                "generatedAt": legacy_cycle.get("generatedAt"),
                "shipGateStatus": legacy_cycle.get("status"),
                "localAdvisoryStatus": "UNKNOWN",
                "strict": legacy_cycle,
                "advisory": {},
            }
    except Exception as e:
        logger.warning(f"Failed to load release cycle data (non-fatal): {e}")

    release_status_strict = (release_cycle or {}).get("shipGateStatus")
    if not release_status_strict and isinstance((release_cycle or {}).get("strict"), dict):
        release_status_strict = (release_cycle or {}).get("strict", {}).get("status")
    release_status_advisory = (release_cycle or {}).get("localAdvisoryStatus")
    if not release_status_advisory and isinstance((release_cycle or {}).get("advisory"), dict):
        release_status_advisory = (release_cycle or {}).get("advisory", {}).get("status")
    release_truth_policy = (
        "dual-track"
        if isinstance((release_cycle or {}).get("strict"), dict) and isinstance((release_cycle or {}).get("advisory"), dict)
        else "single-track"
    )
    try:
        if PHASE11_PATH.exists():
            with open(PHASE11_PATH) as f:
                phase11_raw = json.load(f)
                phase11 = {
                    "generatedAt": phase11_raw.get("generatedAt"),
                    "phase": phase11_raw.get("phase"),
                    "summary": phase11_raw.get("summary", {}),
                }
    except Exception as e:
        logger.warning(f"Failed to load phase11 data (non-fatal): {e}")
    try:
        if PHASE12_PATH.exists():
            with open(PHASE12_PATH) as f:
                phase12_raw = json.load(f)
                phase12 = {
                    "generatedAt": phase12_raw.get("generatedAt"),
                    "phase": phase12_raw.get("phase"),
                    "summary": phase12_raw.get("summary", {}),
                }
    except Exception as e:
        logger.warning(f"Failed to load phase12 data (non-fatal): {e}")
    try:
        if PHASE13_PATH.exists():
            with open(PHASE13_PATH) as f:
                phase13_raw = json.load(f)
                phase13 = {
                    "generatedAt": phase13_raw.get("generatedAt"),
                    "phase": phase13_raw.get("phase"),
                    "summary": phase13_raw.get("summary", {}),
                }
    except Exception as e:
        logger.warning(f"Failed to load phase13 data (non-fatal): {e}")
    try:
        if PHASE16_PATH.exists():
            with open(PHASE16_PATH) as f:
                phase16_raw = json.load(f)
                phase16 = {
                    "generatedAt": phase16_raw.get("generatedAt"),
                    "phase": phase16_raw.get("phase"),
                    "target": phase16_raw.get("target", {}),
                    "summary": phase16_raw.get("summary", {}),
                    "blockers": phase16_raw.get("blockers", []),
                    "nextActions": phase16_raw.get("nextActions", []),
                }
    except Exception as e:
        logger.warning(f"Failed to load phase16 data (non-fatal): {e}")
    try:
        if PHASE17_PATH.exists():
            with open(PHASE17_PATH) as f:
                phase17_raw = json.load(f)
                phase17 = {
                    "generatedAt": phase17_raw.get("generatedAt"),
                    "phase": phase17_raw.get("phase"),
                    "target": phase17_raw.get("target", {}),
                    "summary": phase17_raw.get("summary", {}),
                    "blockers": phase17_raw.get("blockers", []),
                    "nextActions": phase17_raw.get("nextActions", []),
                }
    except Exception as e:
        logger.warning(f"Failed to load phase17 data (non-fatal): {e}")
    try:
        if PHASE18_PATH.exists():
            with open(PHASE18_PATH) as f:
                phase18_raw = json.load(f)
                phase18 = {
                    "generatedAt": phase18_raw.get("generatedAt"),
                    "phase": phase18_raw.get("phase"),
                    "summary": phase18_raw.get("summary", {}),
                    "recommendedCommands": phase18_raw.get("recommendedCommands", {}),
                    "blockers": phase18_raw.get("blockers", []),
                    "nextActions": phase18_raw.get("nextActions", []),
                }
    except Exception as e:
        logger.warning(f"Failed to load phase18 data (non-fatal): {e}")
    try:
        if GRADE_PATH.exists():
            with open(GRADE_PATH) as f:
                dashboard_grade = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load dashboard grade data (non-fatal): {e}")

    dashboard_data = {
        "meta": {
            "generated": timestamp,
            "season": CURRENT_SEASON,
            "seasonDisplay": f"{CURRENT_SEASON-1}-{str(CURRENT_SEASON)[2:]}",
            "modelVersion": "2.1 - Full Bracket Model",
            "lastUpdate": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "sourceFreshness": source_freshness,
            "benchmarkTimestamp": (benchmark_data or {}).get("current", {}).get("timestamp"),
            "releaseStatus": release_status_strict,
            "releaseStatusStrict": release_status_strict,
            "releaseStatusAdvisory": release_status_advisory,
            "releaseTruthPolicy": release_truth_policy,
            "edgeResearchTimestamp": (phase18 or phase17 or phase16 or phase13 or phase12 or phase11 or {}).get("generatedAt"),
            "dashboardGradeTimestamp": (dashboard_grade or {}).get("generatedAt"),
        },
        "teams": teams,
        "featureWeights": weights,
        "tierSummary": tier_summary,
        "tierConfig": TIER_CONFIG,
        "playoffPicture": playoff_picture,
        "cupFavorites": cup_favorites,
        "roundAdvancement": round_advancement,
        "bracket": bracket,
        "backtest": backtest_data,
        "glossary": METRIC_DEFINITIONS,
        "benchmark": benchmark_data,
        "releaseCycle": release_cycle,
        "dashboardGrade": dashboard_grade,
        "edgeResearch": {
            "phase11": phase11,
            "phase12": phase12,
            "phase13": phase13,
            "phase16": phase16,
            "phase17": phase17,
            "phase18": phase18,
        },
    }

    return dashboard_data


def save_dashboard_data(data: Dict, output_path: Path = DATA_OUTPUT) -> None:
    """Save dashboard data to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved dashboard data to {output_path}")


def save_embedded_fallback_data(data: Dict, output_path: Path = EMBEDDED_FALLBACK_PATH) -> None:
    """
    Save an embedded JS fallback snapshot that mirrors dashboard_data.json.
    """
    serialized = json.dumps(data, separators=(",", ":"))
    content = (
        "// Auto-generated fallback from dashboard_data.json — do not edit manually\n"
        f"window.DASHBOARD_DATA = {serialized};\n"
    )
    with open(output_path, "w") as f:
        f.write(content)
    logger.info(f"Saved embedded fallback data to {output_path}")


def save_historical_snapshot(data: Dict) -> None:
    """Save a historical snapshot for trend tracking."""
    HISTORY_DIR.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    history_file = HISTORY_DIR / f"snapshot_{date_str}.json"

    # Only save essential data for history
    snapshot = {
        "date": date_str,
        "teams": [
            {
                "code": t["code"],
                "rank": t["rank"],
                "tier": t["tier"],
                "strength": t["compositeStrength"],
                "playoffProb": t["playoffProbability"],
                "cupProb": t["cupProbability"],
            }
            for t in data["teams"]
        ]
    }

    with open(history_file, 'w') as f:
        json.dump(snapshot, f, indent=2)
    logger.info(f"Saved historical snapshot to {history_file}")


def load_historical_data() -> List[Dict]:
    """Load all historical snapshots for trend analysis."""
    if not HISTORY_DIR.exists():
        return []

    snapshots = []
    for file in sorted(HISTORY_DIR.glob("snapshot_*.json")):
        with open(file) as f:
            snapshots.append(json.load(f))

    return snapshots


def detect_significant_changes(current: Dict, previous: Dict) -> List[Dict]:
    """Detect significant changes for notifications."""
    changes = []

    if not previous:
        return changes

    current_teams = {t["code"]: t for t in current["teams"]}
    previous_teams = {t["code"]: t for t in previous.get("teams", [])}

    for code, team in current_teams.items():
        if code not in previous_teams:
            continue

        prev = previous_teams[code]

        # Tier change
        if team["tier"] != prev.get("tier"):
            changes.append({
                "type": "tier_change",
                "team": code,
                "from": prev.get("tier"),
                "to": team["tier"],
                "message": f"{code} moved from {prev.get('tier')} to {team['tier']}"
            })

        # Rank jump (5+ positions)
        rank_diff = prev.get("rank", team["rank"]) - team["rank"]
        if abs(rank_diff) >= 5:
            direction = "up" if rank_diff > 0 else "down"
            changes.append({
                "type": "rank_jump",
                "team": code,
                "from": prev.get("rank"),
                "to": team["rank"],
                "change": rank_diff,
                "message": f"{code} jumped {abs(rank_diff)} spots {direction} (#{prev.get('rank')} → #{team['rank']})"
            })

        # Cup odds swing (3%+)
        odds_diff = team["cupProbability"] - prev.get("cupProb", team["cupProbability"])
        if abs(odds_diff) >= 3:
            direction = "increased" if odds_diff > 0 else "decreased"
            changes.append({
                "type": "odds_swing",
                "team": code,
                "from": prev.get("cupProb"),
                "to": team["cupProbability"],
                "change": odds_diff,
                "message": f"{code} Cup odds {direction} by {abs(odds_diff):.1f}%"
            })

    return changes


def main():
    """Generate and save dashboard data."""
    # Generate data
    data = generate_dashboard_data()

    # Load previous data for change detection
    history = load_historical_data()
    previous = history[-1] if history else None

    # Detect changes
    if previous:
        changes = detect_significant_changes(data, previous)
        data["recentChanges"] = changes
        if changes:
            logger.info(f"Detected {len(changes)} significant changes")
            for change in changes:
                logger.info(f"  - {change['message']}")
    else:
        data["recentChanges"] = []

    # Add historical trends
    data["history"] = history[-30:]  # Last 30 days

    # Save current data
    save_dashboard_data(data)
    save_embedded_fallback_data(data)

    # Save historical snapshot
    save_historical_snapshot(data)

    logger.info("Dashboard data generation complete!")
    return data


if __name__ == "__main__":
    main()
