#!/usr/bin/env python3
"""
NHL Playoff Framework Backtesting Module

Tests the V7.1 weight formula against historical playoff outcomes (2007-2025).
Validates whether our metrics actually predict playoff success.

Data sources:
- MoneyPuck (2007-2025): Advanced stats (CF%, xG, GSAx)
- Hockey-Reference: Playoff results
- NHL API: Historical standings

Usage:
    python backtest.py                    # Run full backtest
    python backtest.py --season 2023      # Test single season
    python backtest.py --report           # Generate summary report
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Historical playoff results (Cup winners and finalists) - manually verified
# Format: {season: {"winner": "TEAM", "finalist": "TEAM", "conf_finals": ["TEAM", "TEAM", ...], "playoff_teams": [...]}}
HISTORICAL_PLAYOFFS = {
    # 2024-25 season (current - incomplete)
    "2024-25": {"winner": None, "finalist": None, "conf_finals": [], "playoff_teams": []},

    # 2023-24 season
    "2023-24": {
        "winner": "FLA",
        "finalist": "EDM",
        "conf_finals": ["FLA", "NYR", "EDM", "DAL"],
        "playoff_teams": ["FLA", "BOS", "TOR", "TB", "NYR", "CAR", "PHI", "WSH",
                         "VAN", "EDM", "DAL", "WPG", "COL", "NSH", "VGK", "LA"]
    },

    # 2022-23 season
    "2022-23": {
        "winner": "VGK",
        "finalist": "FLA",
        "conf_finals": ["VGK", "DAL", "FLA", "CAR"],
        "playoff_teams": ["BOS", "CAR", "NJ", "TOR", "NYR", "TB", "FLA", "NYI",
                         "VGK", "EDM", "COL", "DAL", "MIN", "SEA", "WPG", "LA"]
    },

    # 2021-22 season
    "2021-22": {
        "winner": "COL",
        "finalist": "TB",
        "conf_finals": ["COL", "EDM", "TB", "NYR"],
        "playoff_teams": ["FLA", "CAR", "TOR", "NYR", "TB", "BOS", "PIT", "WSH",
                         "COL", "MIN", "STL", "CGY", "EDM", "LA", "NSH", "DAL"]
    },

    # 2020-21 season
    "2020-21": {
        "winner": "TB",
        "finalist": "MTL",
        "conf_finals": ["TB", "NYI", "MTL", "VGK"],
        "playoff_teams": ["CAR", "FLA", "TB", "BOS", "WSH", "PIT", "NYI", "MTL",
                         "COL", "VGK", "MIN", "STL", "EDM", "TOR", "WPG", "NSH"]
    },

    # 2019-20 season (bubble playoffs)
    "2019-20": {
        "winner": "TB",
        "finalist": "DAL",
        "conf_finals": ["TB", "NYI", "DAL", "VGK"],
        "playoff_teams": ["BOS", "TB", "WSH", "PHI", "PIT", "CAR", "NYI", "MTL",
                         "STL", "COL", "VGK", "DAL", "EDM", "NSH", "VAN", "CGY"]
    },

    # 2018-19 season
    "2018-19": {
        "winner": "STL",
        "finalist": "BOS",
        "conf_finals": ["STL", "SJ", "BOS", "CAR"],
        "playoff_teams": ["TB", "BOS", "TOR", "WSH", "NYI", "PIT", "CAR", "CBJ",
                         "CGY", "SJ", "NSH", "WPG", "STL", "DAL", "COL", "VGK"]
    },

    # 2017-18 season
    "2017-18": {
        "winner": "WSH",
        "finalist": "VGK",
        "conf_finals": ["WSH", "TB", "VGK", "WPG"],
        "playoff_teams": ["TB", "BOS", "TOR", "WSH", "PIT", "PHI", "CBJ", "NJ",
                         "NSH", "WPG", "MIN", "COL", "VGK", "LA", "ANA", "SJ"]
    },

    # 2016-17 season
    "2016-17": {
        "winner": "PIT",
        "finalist": "NSH",
        "conf_finals": ["PIT", "OTT", "NSH", "ANA"],
        "playoff_teams": ["WSH", "PIT", "CBJ", "NYR", "TOR", "OTT", "BOS", "MTL",
                         "CHI", "MIN", "STL", "NSH", "ANA", "EDM", "SJ", "CGY"]
    },

    # 2015-16 season
    "2015-16": {
        "winner": "PIT",
        "finalist": "SJ",
        "conf_finals": ["PIT", "TB", "SJ", "STL"],
        "playoff_teams": ["WSH", "PIT", "FLA", "NYR", "TB", "NYI", "DET", "PHI",
                         "DAL", "STL", "CHI", "ANA", "LA", "SJ", "NSH", "MIN"]
    },

    # 2014-15 season
    "2014-15": {
        "winner": "CHI",
        "finalist": "TB",
        "conf_finals": ["CHI", "ANA", "TB", "NYR"],
        "playoff_teams": ["NYR", "MTL", "TB", "WSH", "NYI", "OTT", "PIT", "DET",
                         "STL", "NSH", "CHI", "ANA", "VAN", "CGY", "MIN", "WPG"]
    },

    # 2013-14 season
    "2013-14": {
        "winner": "LA",
        "finalist": "NYR",
        "conf_finals": ["LA", "CHI", "NYR", "MTL"],
        "playoff_teams": ["BOS", "PIT", "TB", "MTL", "DET", "NYR", "PHI", "CBJ",
                         "ANA", "SJ", "COL", "STL", "CHI", "MIN", "DAL", "LA"]
    },

    # 2012-13 season (lockout shortened)
    "2012-13": {
        "winner": "CHI",
        "finalist": "BOS",
        "conf_finals": ["CHI", "LA", "BOS", "PIT"],
        "playoff_teams": ["PIT", "MTL", "WSH", "BOS", "TOR", "NYR", "OTT", "NYI",
                         "CHI", "ANA", "VAN", "STL", "LA", "SJ", "DET", "MIN"]
    },

    # 2011-12 season
    "2011-12": {
        "winner": "LA",
        "finalist": "NJ",
        "conf_finals": ["LA", "PHX", "NJ", "NYR"],
        "playoff_teams": ["NYR", "BOS", "FLA", "PIT", "PHI", "NJ", "WSH", "OTT",
                         "VAN", "STL", "PHX", "NSH", "DET", "CHI", "SJ", "LA"]
    },

    # 2010-11 season
    "2010-11": {
        "winner": "BOS",
        "finalist": "VAN",
        "conf_finals": ["BOS", "TB", "VAN", "SJ"],
        "playoff_teams": ["WSH", "PHI", "BOS", "PIT", "MTL", "TB", "NYR", "BUF",
                         "VAN", "SJ", "DET", "ANA", "NSH", "PHX", "LA", "CHI"]
    },

    # 2009-10 season
    "2009-10": {
        "winner": "CHI",
        "finalist": "PHI",
        "conf_finals": ["CHI", "SJ", "PHI", "MTL"],
        "playoff_teams": ["WSH", "NJ", "BUF", "PIT", "OTT", "BOS", "PHI", "MTL",
                         "SJ", "CHI", "VAN", "PHX", "DET", "LA", "COL", "NSH"]
    },

    # 2008-09 season
    "2008-09": {
        "winner": "PIT",
        "finalist": "DET",
        "conf_finals": ["PIT", "CAR", "DET", "CHI"],
        "playoff_teams": ["BOS", "WSH", "NJ", "PIT", "PHI", "NYR", "CAR", "MTL",
                         "SJ", "DET", "VAN", "CHI", "CGY", "STL", "ANA", "CBJ"]
    },

    # 2007-08 season
    "2007-08": {
        "winner": "DET",
        "finalist": "PIT",
        "conf_finals": ["DET", "DAL", "PIT", "PHI"],
        "playoff_teams": ["MTL", "PIT", "WSH", "NJ", "NYR", "PHI", "OTT", "BOS",
                         "DET", "SJ", "MIN", "ANA", "COL", "DAL", "CGY", "NSH"]
    },
}

# V7.2 Weight formula configuration (must match merge_data.py)
# Changes from V7.1: GSAx increased 15%→20%, CF% reduced 20%→15%,
# PDO reduced 15%→12%, PK% increased 10%→13%
WEIGHT_CONFIG = {
    "hdcf": {"weight": 0.25, "min": 42, "max": 58},   # 25% - Best predictor
    "gsax": {"weight": 0.20, "min": -25, "max": 25},  # 20% - Goaltending wins Cups
    "cf": {"weight": 0.15, "min": 44, "max": 56},     # 15% - Reduced (possession overrated)
    "pp": {"weight": 0.15, "min": 12, "max": 30},     # 15% - PP% critical in playoffs
    "pk": {"weight": 0.13, "min": 72, "max": 88},     # 13% - Increased (playoff importance)
    "pdo": {"weight": 0.12, "min": 96, "max": 104},   # 12% - Reduced (luck regresses)
}


def normalize(value, min_val, max_val):
    """Normalize a value to 0-100 scale."""
    if max_val == min_val:
        return 50
    normalized = (value - min_val) / (max_val - min_val) * 100
    return max(0, min(100, normalized))


def calculate_weight(team_stats):
    """Calculate championship weight from team stats."""
    hdcf = team_stats.get("hdcf_pct", 50)
    cf = team_stats.get("cf_pct", 50)
    pdo = team_stats.get("pdo", 100)
    pp = team_stats.get("pp_pct", 20)
    pk = team_stats.get("pk_pct", 80)
    gsax = team_stats.get("gsax", 0)

    # Normalize each metric
    hdcf_norm = normalize(hdcf, WEIGHT_CONFIG["hdcf"]["min"], WEIGHT_CONFIG["hdcf"]["max"])
    cf_norm = normalize(cf, WEIGHT_CONFIG["cf"]["min"], WEIGHT_CONFIG["cf"]["max"])
    pdo_norm = normalize(pdo, WEIGHT_CONFIG["pdo"]["min"], WEIGHT_CONFIG["pdo"]["max"])
    pp_norm = normalize(pp, WEIGHT_CONFIG["pp"]["min"], WEIGHT_CONFIG["pp"]["max"])
    pk_norm = normalize(pk, WEIGHT_CONFIG["pk"]["min"], WEIGHT_CONFIG["pk"]["max"])
    gsax_norm = normalize(gsax, WEIGHT_CONFIG["gsax"]["min"], WEIGHT_CONFIG["gsax"]["max"])

    # Calculate weighted score
    score = (
        hdcf_norm * WEIGHT_CONFIG["hdcf"]["weight"] +
        cf_norm * WEIGHT_CONFIG["cf"]["weight"] +
        pdo_norm * WEIGHT_CONFIG["pdo"]["weight"] +
        pp_norm * WEIGHT_CONFIG["pp"]["weight"] +
        pk_norm * WEIGHT_CONFIG["pk"]["weight"] +
        gsax_norm * WEIGHT_CONFIG["gsax"]["weight"]
    )

    # Scale to 100-300 range
    return round(100 + score * 2, 0)


def load_historical_stats(season):
    """
    Load historical team stats for a season.
    Returns dict of {team_abbr: {stats...}}

    TODO: Implement data fetching from MoneyPuck/Hockey-Reference
    For now, returns placeholder indicating data needed.
    """
    data_dir = Path(__file__).parent.parent / "data" / "historical"
    season_file = data_dir / f"stats_{season.replace('-', '_')}.json"

    if season_file.exists():
        with open(season_file) as f:
            return json.load(f)

    return None


def evaluate_season(season, team_stats, playoff_data):
    """
    Evaluate how well weights predicted playoff success for a season.

    Returns dict with:
    - weight_rankings: Teams ranked by weight
    - playoff_accuracy: How many top-16 by weight made playoffs
    - winner_rank: Where the Cup winner ranked by weight
    - finalist_rank: Where the finalist ranked
    - correlation: Correlation between weight rank and playoff success
    """
    if not team_stats or not playoff_data:
        return None

    # Calculate weights for all teams
    team_weights = {}
    for team, stats in team_stats.items():
        team_weights[team] = calculate_weight(stats)

    # Rank by weight
    ranked = sorted(team_weights.items(), key=lambda x: -x[1])
    weight_ranks = {team: i+1 for i, (team, _) in enumerate(ranked)}

    # Evaluate accuracy
    results = {
        "season": season,
        "total_teams": len(ranked),
        "weight_rankings": ranked[:16],  # Top 16 by weight
    }

    # How many of our top-16 made playoffs?
    top_16_by_weight = [t for t, _ in ranked[:16]]
    playoff_teams = playoff_data.get("playoff_teams", [])

    if playoff_teams:
        correct_playoffs = len(set(top_16_by_weight) & set(playoff_teams))
        results["playoff_accuracy"] = correct_playoffs / 16 * 100
        results["correct_playoff_picks"] = correct_playoffs

    # Where did winner/finalist rank?
    winner = playoff_data.get("winner")
    finalist = playoff_data.get("finalist")

    if winner and winner in weight_ranks:
        results["winner_rank"] = weight_ranks[winner]
        results["winner_weight"] = team_weights[winner]

    if finalist and finalist in weight_ranks:
        results["finalist_rank"] = weight_ranks[finalist]
        results["finalist_weight"] = team_weights[finalist]

    # Conference finalists
    conf_finals = playoff_data.get("conf_finals", [])
    if conf_finals:
        cf_ranks = [weight_ranks.get(t, 32) for t in conf_finals if t in weight_ranks]
        results["conf_final_avg_rank"] = sum(cf_ranks) / len(cf_ranks) if cf_ranks else None

    return results


def run_backtest(seasons=None):
    """
    Run backtesting across multiple seasons.

    Args:
        seasons: List of seasons to test, or None for all available

    Returns:
        Summary statistics and per-season results
    """
    if seasons is None:
        seasons = list(HISTORICAL_PLAYOFFS.keys())

    results = []
    missing_data = []

    for season in seasons:
        if season not in HISTORICAL_PLAYOFFS:
            continue

        playoff_data = HISTORICAL_PLAYOFFS[season]

        # Skip incomplete seasons
        if not playoff_data.get("winner"):
            continue

        # Load historical stats
        team_stats = load_historical_stats(season)

        if team_stats is None:
            missing_data.append(season)
            continue

        # Evaluate this season
        season_result = evaluate_season(season, team_stats, playoff_data)
        if season_result:
            results.append(season_result)

    # Calculate summary statistics
    summary = calculate_summary(results)
    summary["missing_data_seasons"] = missing_data
    summary["seasons_evaluated"] = len(results)

    return summary, results


def calculate_summary(results):
    """Calculate aggregate statistics from backtest results."""
    if not results:
        return {"error": "No results to summarize"}

    summary = {
        "total_seasons": len(results),
    }

    # Playoff accuracy
    accuracies = [r["playoff_accuracy"] for r in results if "playoff_accuracy" in r]
    if accuracies:
        summary["avg_playoff_accuracy"] = round(sum(accuracies) / len(accuracies), 1)
        summary["min_playoff_accuracy"] = min(accuracies)
        summary["max_playoff_accuracy"] = max(accuracies)

    # Winner rankings
    winner_ranks = [r["winner_rank"] for r in results if "winner_rank" in r]
    if winner_ranks:
        summary["avg_winner_rank"] = round(sum(winner_ranks) / len(winner_ranks), 1)
        summary["winners_in_top_5"] = len([r for r in winner_ranks if r <= 5])
        summary["winners_in_top_10"] = len([r for r in winner_ranks if r <= 10])
        summary["winners_in_top_16"] = len([r for r in winner_ranks if r <= 16])

    # Finalist rankings
    finalist_ranks = [r["finalist_rank"] for r in results if "finalist_rank" in r]
    if finalist_ranks:
        summary["avg_finalist_rank"] = round(sum(finalist_ranks) / len(finalist_ranks), 1)

    return summary


def generate_report(summary, results):
    """Generate a human-readable backtest report."""
    lines = []
    lines.append("=" * 70)
    lines.append("NHL CHAMPIONSHIP FRAMEWORK V7.1 - BACKTEST REPORT")
    lines.append("=" * 70)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    lines.append("SUMMARY STATISTICS")
    lines.append("-" * 70)
    lines.append(f"Seasons Evaluated: {summary.get('seasons_evaluated', 0)}")
    lines.append(f"Missing Data Seasons: {len(summary.get('missing_data_seasons', []))}")
    lines.append("")

    if "avg_playoff_accuracy" in summary:
        lines.append(f"Average Playoff Prediction Accuracy: {summary['avg_playoff_accuracy']:.1f}%")
        lines.append(f"  (Correctly picking playoff teams from top-16 by weight)")
        lines.append("")

    if "avg_winner_rank" in summary:
        lines.append("Cup Winner Performance:")
        lines.append(f"  Average Rank by Weight: {summary['avg_winner_rank']:.1f}")
        lines.append(f"  Winners in Top 5: {summary.get('winners_in_top_5', 0)}/{summary['total_seasons']}")
        lines.append(f"  Winners in Top 10: {summary.get('winners_in_top_10', 0)}/{summary['total_seasons']}")
        lines.append(f"  Winners in Top 16: {summary.get('winners_in_top_16', 0)}/{summary['total_seasons']}")
        lines.append("")

    if summary.get("missing_data_seasons"):
        lines.append("MISSING DATA - Need to fetch historical stats for:")
        for season in summary["missing_data_seasons"]:
            lines.append(f"  - {season}")
        lines.append("")

    if results:
        lines.append("PER-SEASON RESULTS")
        lines.append("-" * 70)
        for r in sorted(results, key=lambda x: x["season"], reverse=True):
            winner_info = f"Winner rank: #{r.get('winner_rank', 'N/A')}" if "winner_rank" in r else ""
            accuracy = f"{r.get('playoff_accuracy', 0):.0f}%" if "playoff_accuracy" in r else "N/A"
            lines.append(f"{r['season']}: Playoff accuracy {accuracy}, {winner_info}")

    return "\n".join(lines)


def main():
    """Main entry point for backtesting."""
    import argparse

    parser = argparse.ArgumentParser(description="Backtest NHL Championship Framework")
    parser.add_argument("--season", help="Test single season (e.g., 2023-24)")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    parser.add_argument("--fetch", action="store_true", help="Fetch missing historical data")

    args = parser.parse_args()

    if args.season:
        seasons = [args.season]
    else:
        seasons = None

    print("Running NHL Championship Framework Backtest...")
    print()

    summary, results = run_backtest(seasons)

    if args.report or True:  # Always generate report for now
        report = generate_report(summary, results)
        print(report)

        # Save report
        report_dir = Path(__file__).parent.parent / "reports"
        report_dir.mkdir(exist_ok=True)
        report_file = report_dir / f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, "w") as f:
            f.write(report)
        print(f"\nReport saved to: {report_file}")

    return summary, results


if __name__ == "__main__":
    main()
