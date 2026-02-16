#!/usr/bin/env python3
"""
Phase 6: betting-edge layer report using model vs market-implied Cup probabilities.

Note: data/odds.json is currently Hockey-Reference simulation probabilities,
not sportsbook lines. This report is an edge proxy until sportsbook history exists.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ODDS_PATH = PROJECT_ROOT / "data" / "odds.json"
DASHBOARD_PATH = PROJECT_ROOT / "dashboard_data.json"
OUT_JSON = PROJECT_ROOT / "reports" / "phase6_betting_edge.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE6_BETTING_EDGE.md"
BENCHMARK_PATH = PROJECT_ROOT / "reports" / "benchmark_latest.json"


def _american_to_decimal(american: float) -> float:
    if american >= 0:
        return 1.0 + (american / 100.0)
    return 1.0 + (100.0 / abs(american))


def main() -> int:
    with open(ODDS_PATH) as f:
        odds = json.load(f)
    with open(DASHBOARD_PATH) as f:
        dash = json.load(f)

    market = odds.get("teams", {})
    model_rows = {t.get("code"): t for t in dash.get("teams", [])}
    edges = []

    for code, m in market.items():
        if code not in model_rows:
            continue
        model_prob = float(model_rows[code].get("cupProbability", 0.0)) / 100.0
        market_prob = float(m.get("cupPct", 0.0)) / 100.0
        american = float(m.get("impliedCupOdds", 0.0))
        if american == 0:
            continue

        decimal_odds = _american_to_decimal(american)
        ev = (model_prob * (decimal_odds - 1.0)) - (1.0 - model_prob)
        edge = model_prob - market_prob
        kelly = max(0.0, ev / (decimal_odds - 1.0)) if decimal_odds > 1 else 0.0

        edges.append(
            {
                "team": code,
                "model_prob": round(model_prob, 4),
                "market_prob": round(market_prob, 4),
                "edge_prob": round(edge, 4),
                "implied_odds_american": int(american),
                "implied_odds_decimal": round(decimal_odds, 3),
                "expected_value_unit": round(ev, 4),
                "kelly_fraction": round(kelly, 4),
            }
        )

    edges.sort(key=lambda r: r["edge_prob"], reverse=True)
    positive = [r for r in edges if r["edge_prob"] > 0]

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "phase6_betting_edge_proxy",
        "marketSource": odds.get("_metadata", {}),
        "nTeamsCompared": len(edges),
        "nPositiveEdges": len(positive),
        "topEdges": positive[:15],
        "allEdges": edges,
        "historicalBenchmark": {},
    }

    if BENCHMARK_PATH.exists():
        try:
            with open(BENCHMARK_PATH) as f:
                benchmark = json.load(f).get("current", {})
            vegas = benchmark.get("vegas", {})
            report["historicalBenchmark"] = {
                "available": vegas.get("available", False),
                "model_minus_vegas_brier_playoff": vegas.get("model_minus_vegas_brier_playoff"),
                "model_minus_vegas_brier_cup": vegas.get("model_minus_vegas_brier_cup"),
                "model_minus_vegas_log_loss_playoff": vegas.get("model_minus_vegas_log_loss_playoff"),
                "model_minus_vegas_log_loss_cup": vegas.get("model_minus_vegas_log_loss_cup"),
                "cup_relative_brier_edge": vegas.get("cup_relative_brier_edge"),
                "cup_relative_brier_edge_ci_low": vegas.get("cup_relative_brier_edge_ci_low"),
                "cup_relative_brier_edge_ci_high": vegas.get("cup_relative_brier_edge_ci_high"),
                "cup_target": vegas.get("cup_target", {}),
            }
        except Exception:
            report["historicalBenchmark"] = {"available": False}

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 6 Betting Edge Report",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        "## Source",
        "",
        f"- Market Source: `{report['marketSource'].get('source', 'unknown')}`",
        f"- Notes: `{report['marketSource'].get('notes', 'n/a')}`",
        f"- Teams Compared: `{len(edges)}`",
        f"- Positive Edge Teams: `{len(positive)}`",
    ]
    lines += [
        "",
        "## Historical Vegas Validation (strict walk-forward)",
        "",
    ]
    hist = report.get("historicalBenchmark", {})
    if not hist.get("available"):
        lines.append("- Historical Vegas benchmark unavailable.")
    else:
        cup_target = hist.get("cup_target", {})
        lines.append(
            f"- Cup relative Brier edge: `{(hist.get('cup_relative_brier_edge') or 0) * 100:.2f}%` "
            f"(CI: `{(hist.get('cup_relative_brier_edge_ci_low') or 0) * 100:.2f}%` to "
            f"`{(hist.get('cup_relative_brier_edge_ci_high') or 0) * 100:.2f}%`)"
        )
        lines.append(
            f"- Cup release-floor status: `{'PASS' if cup_target.get('goal_met') else 'FAIL'}` "
            f"(floor >= `{cup_target.get('relative_brier_improvement_min', 0) * 100:.1f}%`, "
            f"strong >= `{(cup_target.get('relative_brier_improvement_strong') or 0) * 100:.1f}%`, "
            f"stretch >= `{(cup_target.get('relative_brier_improvement_stretch') or 0) * 100:.1f}%`, "
            f"moonshot >= `{(cup_target.get('relative_brier_improvement_moonshot') or 0) * 100:.1f}%`)"
        )
        lines.append(f"- Tier reached: `{cup_target.get('goal_tier', 'unknown')}`")
        lines.append(
            f"- Model - Vegas Brier (Cup): `{hist.get('model_minus_vegas_brier_cup')}`"
        )
        lines.append(
            f"- Model - Vegas Log Loss (Cup): `{hist.get('model_minus_vegas_log_loss_cup')}`"
        )
    lines += [
        "",
        "## Top Positive Edges",
        "",
        "| Team | Model Cup % | Market Cup % | Edge % | Implied Odds | EV (1u) | Kelly f |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in positive[:15]:
        lines.append(
            f"| {r['team']} | {100*r['model_prob']:.2f} | {100*r['market_prob']:.2f} | "
            f"{100*r['edge_prob']:.2f} | {r['implied_odds_american']} | {r['expected_value_unit']:.4f} | {r['kelly_fraction']:.4f} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
