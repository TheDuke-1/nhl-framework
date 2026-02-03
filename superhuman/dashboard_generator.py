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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .predictor import SuperhumanPredictor
from .config import CURRENT_SEASON, DATA_DIR, CONFERENCES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Output paths
PROJECT_DIR = Path(__file__).parent.parent
DATA_OUTPUT = PROJECT_DIR / "dashboard_data.json"
HISTORY_DIR = PROJECT_DIR / "history"


# Metric definitions for glossary
METRIC_DEFINITIONS = {
    "composite_strength": {
        "name": "Composite Strength",
        "short": "Overall team power rating combining all factors",
        "formula": "Weighted average of 14 performance metrics"
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
    bracket = {"East": {}, "West": {}, "cupFinal": [], "champion": None}

    if not mc_result:
        return bracket

    for conf in ["East", "West"]:
        # R1 matchups (deterministic from seeding)
        r1 = []
        for higher, lower, higher_win_prob in mc_result.projected_matchups.get(conf, []):
            r1.append({
                "higher": higher,
                "lower": lower,
                "higherWinProb": round(higher_win_prob * 100, 1),
            })

        # R2 matchups (from tracking, show top 3 most likely per bracket slot)
        r2 = []
        for matchup_data in mc_result.r2_matchups.get(conf, []):
            a, b, a_win_prob, freq = matchup_data
            r2.append({
                "teamA": a,
                "teamB": b,
                "teamAWinProb": round(a_win_prob * 100, 1),
                "matchupProb": round(freq * 100, 1),
            })

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
            "round2": r2[:3],  # Top 3 most likely R2 matchups per conf
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

    return bracket


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
        from .validation import generate_backtest_report
        from .data_loader import load_training_data
        historical_data = load_training_data()
        if historical_data:
            cache_path = str(DATA_DIR / "backtest_cache.json")
            backtest_data = generate_backtest_report(historical_data, cache_path=cache_path)
            logger.info("Backtest report ready")
    except Exception as e:
        logger.warning(f"Backtest generation failed (non-fatal): {e}")

    # Generate timestamp
    timestamp = datetime.now().isoformat()

    dashboard_data = {
        "meta": {
            "generated": timestamp,
            "season": CURRENT_SEASON,
            "seasonDisplay": f"{CURRENT_SEASON-1}-{str(CURRENT_SEASON)[2:]}",
            "modelVersion": "2.1 - Full Bracket Model",
            "lastUpdate": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
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
    }

    return dashboard_data


def save_dashboard_data(data: Dict, output_path: Path = DATA_OUTPUT) -> None:
    """Save dashboard data to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved dashboard data to {output_path}")


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

    # Save historical snapshot
    save_historical_snapshot(data)

    logger.info("Dashboard data generation complete!")
    return data


if __name__ == "__main__":
    main()
