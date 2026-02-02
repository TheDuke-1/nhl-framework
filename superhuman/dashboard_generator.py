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
from .data_models import PredictionResult
from .config import CURRENT_SEASON

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


def generate_dashboard_data() -> Dict:
    """Generate complete dashboard data from model predictions."""
    logger.info("Generating dashboard data...")

    # Run predictions
    predictor = SuperhumanPredictor()
    predictor.predict()

    # Build team data
    teams = []
    for i, result in enumerate(predictor.results, 1):
        team_code = result.team
        team_meta = TEAM_INFO.get(team_code, {"name": team_code, "city": "", "conference": "East", "division": ""})
        tier_config = TIER_CONFIG.get(result.tier, TIER_CONFIG["Longshot"])

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
            "cupProbability": round(result.cup_win_probability * 100, 2),
            "cupProbLower": round(result.cup_prob_lower * 100, 2),
            "cupProbUpper": round(result.cup_prob_upper * 100, 2),
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

    # Generate timestamp
    timestamp = datetime.now().isoformat()

    dashboard_data = {
        "meta": {
            "generated": timestamp,
            "season": CURRENT_SEASON,
            "seasonDisplay": f"{CURRENT_SEASON-1}-{str(CURRENT_SEASON)[2:]}",
            "modelVersion": "2.0 - Enhanced Playoff Model",
            "lastUpdate": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        },
        "teams": teams,
        "featureWeights": weights,
        "tierSummary": tier_summary,
        "tierConfig": TIER_CONFIG,
        "playoffPicture": playoff_picture,
        "cupFavorites": cup_favorites,
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
