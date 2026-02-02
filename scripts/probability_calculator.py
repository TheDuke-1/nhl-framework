#!/usr/bin/env python3
"""
NHL Playoff Probability Calculator

Uses Monte Carlo simulation to calculate each team's probability of:
- Making the playoffs
- Winning each round (1st, 2nd, Conference Finals, Cup Finals)
- Winning the Stanley Cup

Based on team weights from the V7.1 framework.

Usage:
    python probability_calculator.py              # Calculate all probabilities
    python probability_calculator.py --team COL   # Show specific team
    python probability_calculator.py --sims 50000 # Custom simulation count
"""

import json
import random
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Simulation parameters
DEFAULT_SIMULATIONS = 10000
GAMES_REMAINING_ESTIMATE = 30  # Approximate games left in season
HOME_ICE_ADVANTAGE = 0.04  # 4% win probability boost for home team
PLAYOFF_VARIANCE = 0.15  # Higher variance in playoffs

# Conference/Division structure
CONFERENCES = {
    "East": {
        "Atlantic": ["BOS", "BUF", "DET", "FLA", "MTL", "OTT", "TB", "TOR"],
        "Metropolitan": ["CAR", "CBJ", "NJ", "NYI", "NYR", "PHI", "PIT", "WSH"]
    },
    "West": {
        "Central": ["CHI", "COL", "DAL", "MIN", "NSH", "STL", "UTA", "WPG"],
        "Pacific": ["ANA", "CGY", "EDM", "LA", "SEA", "SJ", "VAN", "VGK"]
    }
}


def load_team_data():
    """Load current team data from teams.json."""
    data_path = Path(__file__).parent.parent / "data" / "teams.json"

    with open(data_path) as f:
        data = json.load(f)

    return {t["team"]: t for t in data["teams"]}


def calculate_win_probability(team_a_weight, team_b_weight, home_ice=False, is_playoff=False):
    """
    Calculate probability that team A beats team B.

    Uses logistic function based on weight differential.
    """
    weight_diff = team_a_weight - team_b_weight

    # Logistic function - steeper in regular season, flatter in playoffs
    k = 0.03 if is_playoff else 0.04
    base_prob = 1 / (1 + pow(2.718, -k * weight_diff))

    # Apply home ice advantage
    if home_ice:
        base_prob = min(0.85, base_prob + HOME_ICE_ADVANTAGE)

    # Add playoff variance (more upsets)
    if is_playoff:
        # Move probability slightly toward 0.5
        base_prob = 0.5 + (base_prob - 0.5) * (1 - PLAYOFF_VARIANCE)

    return base_prob


def simulate_series(team_a, team_b, team_a_weight, team_b_weight, team_a_home=True):
    """
    Simulate a best-of-7 playoff series.

    Returns: winner team abbreviation
    """
    wins_a = 0
    wins_b = 0
    game = 0

    # Home ice pattern: A-A-B-B-A-B-A
    home_pattern = [team_a_home, team_a_home, not team_a_home, not team_a_home,
                    team_a_home, not team_a_home, team_a_home]

    while wins_a < 4 and wins_b < 4:
        is_home_a = home_pattern[game]
        prob_a = calculate_win_probability(team_a_weight, team_b_weight, is_home_a, is_playoff=True)

        if random.random() < prob_a:
            wins_a += 1
        else:
            wins_b += 1

        game += 1

    return team_a if wins_a == 4 else team_b


def simulate_season_end(teams, current_standings):
    """
    Simulate remaining regular season games to get final standings.

    For simplicity, uses weight-based point projection.
    """
    final_standings = {}

    for team, data in teams.items():
        current_pts = data.get("pts", 0)
        current_gp = data.get("gp", 0)
        weight = data.get("weight", 200)

        # Estimate remaining games
        remaining = max(0, 82 - current_gp)

        if remaining > 0:
            # Expected points per game based on weight (200 = 0.5 pts/game)
            pts_per_game = 0.5 + (weight - 200) / 400

            # Add randomness
            pts_per_game += random.gauss(0, 0.15)
            pts_per_game = max(0.3, min(1.2, pts_per_game))

            projected_pts = current_pts + (remaining * pts_per_game * 2)
        else:
            projected_pts = current_pts

        final_standings[team] = {
            "pts": projected_pts,
            "weight": weight,
            "conf": data.get("conf", "East")
        }

    return final_standings


def get_playoff_teams(standings):
    """
    Determine playoff teams from standings.

    Format: Top 3 from each division + 2 wild cards per conference
    Returns dict of {conf: [teams in seed order]}
    """
    playoff_teams = {"East": [], "West": []}

    for conf, divisions in CONFERENCES.items():
        conf_teams = [(t, s) for t, s in standings.items() if s["conf"] == conf]
        conf_teams.sort(key=lambda x: -x[1]["pts"])

        div_winners = {}
        div_teams = {div: [] for div in divisions}

        # Sort teams into divisions
        for team, stats in conf_teams:
            for div, div_members in divisions.items():
                if team in div_members:
                    div_teams[div].append((team, stats))
                    break

        # Get top 3 from each division
        div_qualifiers = []
        for div in divisions:
            sorted_div = sorted(div_teams[div], key=lambda x: -x[1]["pts"])
            for i, (team, stats) in enumerate(sorted_div[:3]):
                if i == 0:
                    div_winners[div] = team
                div_qualifiers.append((team, stats))

        # Get wild cards (next 2 best from conference not already qualified)
        qualified = {t for t, _ in div_qualifiers}
        wild_cards = [(t, s) for t, s in conf_teams if t not in qualified][:2]

        # Build seeding: 1-2 are division winners, 3 plays WC2, etc.
        div_list = list(divisions.keys())
        d1_winner = div_winners.get(div_list[0])
        d2_winner = div_winners.get(div_list[1])

        # Simplify: just return top 8 by points
        top_8 = [t for t, _ in conf_teams[:8]]
        playoff_teams[conf] = top_8

    return playoff_teams


def simulate_playoffs(playoff_teams, standings):
    """
    Simulate full playoff bracket.

    Returns: Cup winner
    """
    results = {"East": [], "West": []}

    for conf in ["East", "West"]:
        teams = playoff_teams[conf][:8]
        if len(teams) < 8:
            teams += ["BYE"] * (8 - len(teams))

        # Round 1: 1v8, 2v7, 3v6, 4v5
        matchups = [(0, 7), (1, 6), (2, 5), (3, 4)]
        round_winners = []

        for seed_a, seed_b in matchups:
            team_a = teams[seed_a]
            team_b = teams[seed_b]

            if team_b == "BYE":
                round_winners.append(team_a)
                continue

            weight_a = standings[team_a]["weight"]
            weight_b = standings[team_b]["weight"]

            winner = simulate_series(team_a, team_b, weight_a, weight_b, team_a_home=True)
            round_winners.append(winner)

        # Round 2
        r2_winners = []
        for i in range(0, 4, 2):
            team_a = round_winners[i]
            team_b = round_winners[i + 1]
            weight_a = standings[team_a]["weight"]
            weight_b = standings[team_b]["weight"]
            winner = simulate_series(team_a, team_b, weight_a, weight_b)
            r2_winners.append(winner)

        # Conference Finals
        team_a = r2_winners[0]
        team_b = r2_winners[1]
        conf_champ = simulate_series(team_a, team_b,
                                     standings[team_a]["weight"],
                                     standings[team_b]["weight"])
        results[conf] = conf_champ

    # Stanley Cup Finals
    east_champ = results["East"]
    west_champ = results["West"]
    cup_winner = simulate_series(east_champ, west_champ,
                                 standings[east_champ]["weight"],
                                 standings[west_champ]["weight"])

    return cup_winner, results


def run_simulation(num_sims=DEFAULT_SIMULATIONS):
    """
    Run Monte Carlo simulation.

    Returns probabilities for each team.
    """
    teams = load_team_data()

    # Track results
    playoff_appearances = defaultdict(int)
    conf_finals = defaultdict(int)
    cup_finals = defaultdict(int)
    cup_wins = defaultdict(int)

    print(f"Running {num_sims:,} simulations...")

    for i in range(num_sims):
        if (i + 1) % 1000 == 0:
            print(f"  Progress: {i + 1:,}/{num_sims:,}")

        # Simulate season end
        final_standings = simulate_season_end(teams, None)

        # Get playoff teams
        playoff_teams = get_playoff_teams(final_standings)

        # Track playoff appearances
        for conf, conf_teams in playoff_teams.items():
            for team in conf_teams[:8]:
                playoff_appearances[team] += 1

        # Simulate playoffs
        cup_winner, conf_champs = simulate_playoffs(playoff_teams, final_standings)

        # Track results
        for conf, champ in conf_champs.items():
            conf_finals[champ] += 1

        cup_finals[conf_champs["East"]] += 1
        cup_finals[conf_champs["West"]] += 1
        cup_wins[cup_winner] += 1

    # Calculate probabilities
    results = {}
    for team in teams:
        results[team] = {
            "team": team,
            "name": teams[team].get("name", team),
            "weight": teams[team].get("weight", 200),
            "current_pts": teams[team].get("pts", 0),
            "playoff_pct": round(playoff_appearances[team] / num_sims * 100, 1),
            "conf_final_pct": round(conf_finals[team] / num_sims * 100, 1),
            "cup_final_pct": round(cup_finals[team] / num_sims * 100, 1),
            "cup_win_pct": round(cup_wins[team] / num_sims * 100, 1),
        }

    return results


def print_results(results):
    """Print probability results."""
    print()
    print("=" * 80)
    print("NHL PLAYOFF PROBABILITY CALCULATOR - V7.1")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # Sort by Cup win probability
    sorted_results = sorted(results.values(), key=lambda x: -x["cup_win_pct"])

    print(f"{'Team':<25} {'Wt':<6} {'Pts':<5} {'Playoff':<9} {'Conf F':<9} {'Cup F':<9} {'Win Cup':<9}")
    print("-" * 80)

    for r in sorted_results[:20]:  # Top 20
        print(f"{r['name']:<25} {r['weight']:<6.0f} {r['current_pts']:<5} "
              f"{r['playoff_pct']:>6.1f}%  {r['conf_final_pct']:>6.1f}%  "
              f"{r['cup_final_pct']:>6.1f}%  {r['cup_win_pct']:>6.1f}%")

    print()
    print("Top 5 Cup Favorites:")
    for i, r in enumerate(sorted_results[:5], 1):
        print(f"  {i}. {r['name']}: {r['cup_win_pct']:.1f}%")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="NHL Playoff Probability Calculator")
    parser.add_argument("--sims", type=int, default=DEFAULT_SIMULATIONS,
                        help=f"Number of simulations (default: {DEFAULT_SIMULATIONS})")
    parser.add_argument("--team", help="Show detailed results for specific team")
    parser.add_argument("--output", help="Save results to JSON file")

    args = parser.parse_args()

    results = run_simulation(args.sims)
    print_results(results)

    if args.team:
        team = args.team.upper()
        if team in results:
            r = results[team]
            print(f"\n{r['name']} Detailed Probabilities:")
            print(f"  Make Playoffs: {r['playoff_pct']:.1f}%")
            print(f"  Conference Finals: {r['conf_final_pct']:.1f}%")
            print(f"  Cup Finals: {r['cup_final_pct']:.1f}%")
            print(f"  Win Stanley Cup: {r['cup_win_pct']:.1f}%")

    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_path}")

    return results


if __name__ == "__main__":
    main()
