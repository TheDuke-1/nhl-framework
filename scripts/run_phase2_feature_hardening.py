#!/usr/bin/env python3
"""
Phase 2 feature hardening:
- Convert strict matrix outputs into final keep/reduce/remove/add decisions
- Score features per objective (Cup Top-1, Cup Top-5, Playoff field)
- Add era-stability and confidence labels
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MATRIX_JSON = PROJECT_ROOT / "reports" / "feature_test_matrix.json"
OUT_JSON = PROJECT_ROOT / "reports" / "phase2_feature_hardening.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE2_FEATURE_HARDENING.md"


def _safe(v, default=0.0):
    return default if v is None else v


def _metric_delta(base: Dict, other: Dict, key: str) -> float:
    return float(_safe(other.get(key), 0.0) - _safe(base.get(key), 0.0))


def _stability_summary(add_one_eval: Dict) -> Dict:
    era = add_one_eval.get("era_stability", {})
    if not era:
        return {
            "eras_evaluated": 0,
            "top1_range": 0.0,
            "top5_range": 0.0,
            "winner_rank_range": 0.0,
            "playoff_f1_range": 0.0,
            "stable": False,
            "notes": "missing era buckets",
        }

    top1_vals = [float(v.get("cup_top1_accuracy_pct", 0.0)) for v in era.values()]
    top5_vals = [float(v.get("cup_top5_accuracy_pct", 0.0)) for v in era.values()]
    rank_vals = [float(v.get("cup_average_winner_rank", 0.0)) for v in era.values()]
    f1_vals = [float(v.get("playoff_f1", 0.0)) for v in era.values()]

    top1_range = max(top1_vals) - min(top1_vals)
    top5_range = max(top5_vals) - min(top5_vals)
    rank_range = max(rank_vals) - min(rank_vals)
    f1_range = max(f1_vals) - min(f1_vals)

    stable = (
        top1_range <= 25.0
        and top5_range <= 35.0
        and rank_range <= 3.0
        and f1_range <= 0.08
    )
    semi_stable = (
        top1_range <= 40.0
        and top5_range <= 55.0
        and rank_range <= 5.0
        and f1_range <= 0.12
    )

    stability_label = "stable" if stable else ("semi_stable" if semi_stable else "unstable")
    notes = "stable across eras" if stable else ("acceptable era variance" if semi_stable else "material era variance detected")
    return {
        "eras_evaluated": len(era),
        "top1_range": round(top1_range, 1),
        "top5_range": round(top5_range, 1),
        "winner_rank_range": round(rank_range, 2),
        "playoff_f1_range": round(f1_range, 3),
        "stable": stable,
        "stability_label": stability_label,
        "notes": notes,
    }


def _confidence(evidence: int, stability_label: str) -> str:
    if evidence >= 5 and stability_label == "stable":
        return "high"
    if evidence >= 3:
        return "medium"
    return "low"


def _final_decision(evidence: int, stability_label: str, removal_harm: Dict) -> str:
    if stability_label == "unstable" and evidence <= 2:
        return "reduce_or_remove"
    if (
        evidence >= 4
        and (
            removal_harm["top1_drop"] >= 4.0
            or removal_harm["top5_drop"] >= 8.0
            or removal_harm["winner_rank_increase"] >= 0.5
            or removal_harm["playoff_f1_drop"] >= 0.01
        )
    ):
        return "keep_or_increase"
    if evidence >= 3:
        return "keep_reduce_weight"
    return "reduce_or_remove"


def _sort_key(row: Dict):
    return (
        -row["importance"]["cup_top1_importance"],
        -row["importance"]["cup_top5_importance"],
        -row["importance"]["playoff_field_importance"],
        row["stability"]["winner_rank_range"],
    )


def main() -> int:
    if not MATRIX_JSON.exists():
        raise SystemExit(f"Missing matrix report: {MATRIX_JSON}")

    with open(MATRIX_JSON) as f:
        matrix = json.load(f)

    baseline = matrix.get("baseline", {}).get("summary", {})
    add_one = matrix.get("addOne", {})
    leave_one_out = matrix.get("leaveOneOut", {})
    decision_table = {
        r.get("feature"): r.get("recommendation")
        for r in matrix.get("decisionTable", [])
        if r.get("feature")
    }
    interactions = matrix.get("interactionsTop", [])
    unavailable = matrix.get("unavailableBacklogDatapoints", [])

    rows: List[Dict] = []
    interaction_bonus = {}
    baseline_top1 = float(_safe(baseline.get("cup_top1_accuracy_pct"), 0.0))
    baseline_top5 = float(_safe(baseline.get("cup_top5_accuracy_pct"), 0.0))
    for row in interactions:
        pair = row.get("pair", [])
        if len(pair) != 2:
            continue
        s = row.get("summary", {})
        bonus = 0
        if float(_safe(s.get("cup_top1_accuracy_pct"), 0.0)) >= baseline_top1 + 8.0:
            bonus += 2
        if float(_safe(s.get("cup_top5_accuracy_pct"), 0.0)) >= baseline_top5 + 8.0:
            bonus += 1
        if bonus:
            for f in pair:
                interaction_bonus[f] = interaction_bonus.get(f, 0) + bonus

    for feature, add_eval in add_one.items():
        add_summary = add_eval.get("summary", {})
        loo_summary = leave_one_out.get(feature, {}).get("summary", {})
        if not add_summary or not loo_summary:
            continue

        removal_harm = {
            "top1_drop": round(_safe(baseline.get("cup_top1_accuracy_pct")) - _safe(loo_summary.get("cup_top1_accuracy_pct")), 1),
            "top5_drop": round(_safe(baseline.get("cup_top5_accuracy_pct")) - _safe(loo_summary.get("cup_top5_accuracy_pct")), 1),
            "winner_rank_increase": round(_safe(loo_summary.get("cup_average_winner_rank")) - _safe(baseline.get("cup_average_winner_rank")), 2),
            "playoff_f1_drop": round(_safe(baseline.get("playoff_f1")) - _safe(loo_summary.get("playoff_f1")), 3),
        }
        add_strength = {
            "top1_vs_baseline": round(_metric_delta(baseline, add_summary, "cup_top1_accuracy_pct"), 1),
            "top5_vs_baseline": round(_metric_delta(baseline, add_summary, "cup_top5_accuracy_pct"), 1),
            "winner_rank_vs_baseline": round(_metric_delta(baseline, add_summary, "cup_average_winner_rank"), 2),
            "playoff_f1_vs_baseline": round(_metric_delta(baseline, add_summary, "playoff_f1"), 3),
        }

        stability = _stability_summary(add_eval)

        evidence = 0
        matrix_rec = decision_table.get(feature, "")
        if matrix_rec == "keep_or_increase":
            evidence += 2
        elif matrix_rec == "reduce_but_keep":
            evidence += 1
        elif matrix_rec == "reduce_or_remove":
            evidence -= 1

        if removal_harm["top1_drop"] > 0:
            evidence += 1
        if removal_harm["top5_drop"] > 0:
            evidence += 1
        if removal_harm["winner_rank_increase"] > 0:
            evidence += 1
        if removal_harm["playoff_f1_drop"] > 0:
            evidence += 1
        if add_summary.get("cup_top1_accuracy_pct", 0.0) >= baseline.get("cup_top1_accuracy_pct", 0.0) - 2.0:
            evidence += 1
        if add_summary.get("cup_top5_accuracy_pct", 0.0) >= baseline.get("cup_top5_accuracy_pct", 0.0) - 5.0:
            evidence += 1
        evidence += interaction_bonus.get(feature, 0)

        if stability["stability_label"] == "unstable":
            evidence -= 1

        importance = {
            "cup_top1_importance": round(max(0.0, removal_harm["top1_drop"]) + max(0.0, add_strength["top1_vs_baseline"] * 0.5), 2),
            "cup_top5_importance": round(max(0.0, removal_harm["top5_drop"]) + max(0.0, add_strength["top5_vs_baseline"] * 0.5), 2),
            "playoff_field_importance": round(max(0.0, removal_harm["playoff_f1_drop"] * 100.0) + max(0.0, add_strength["playoff_f1_vs_baseline"] * 50.0), 2),
        }

        final_decision = _final_decision(evidence, stability["stability_label"], removal_harm)
        confidence = _confidence(evidence, stability["stability_label"])

        rows.append(
            {
                "feature": feature,
                "final_decision": final_decision,
                "confidence": confidence,
                "evidence_score": evidence,
                "matrix_recommendation": matrix_rec,
                "importance": importance,
                "removal_harm": removal_harm,
                "add_one_signal": {
                    "cup_top1_accuracy_pct": round(add_summary.get("cup_top1_accuracy_pct", 0.0), 1),
                    "cup_top5_accuracy_pct": round(add_summary.get("cup_top5_accuracy_pct", 0.0), 1),
                    "cup_average_winner_rank": round(add_summary.get("cup_average_winner_rank", 0.0), 2),
                    "playoff_f1": round(add_summary.get("playoff_f1", 0.0), 3),
                },
                "stability": stability,
            }
        )

    rows.sort(key=_sort_key)

    top_interactions = sorted(
        interactions,
        key=lambda r: (
            -_safe(r.get("summary", {}).get("cup_top1_accuracy_pct"), 0.0),
            -_safe(r.get("summary", {}).get("cup_top5_accuracy_pct"), 0.0),
            _safe(r.get("summary", {}).get("cup_average_winner_rank"), 999.0),
            -_safe(r.get("summary", {}).get("playoff_f1"), 0.0),
        ),
    )[:10]

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "phase2_feature_hardening",
        "baselineSummary": baseline,
        "finalFeatureTable": rows,
        "topInteractions": top_interactions,
        "unavailableBacklogDatapoints": unavailable,
        "selectionRules": {
            "era_stability": "top1_range<=25, top5_range<=35, winner_rank_range<=3.0, playoff_f1_range<=0.08",
            "decision": "keep_or_increase / keep_reduce_weight / reduce_or_remove",
            "confidence": "high/medium/low based on evidence + stability",
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 2 Feature Hardening",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        "## Baseline",
        "",
        f"- Cup Top-1: {baseline.get('cup_top1_accuracy_pct', 0.0):.1f}%",
        f"- Cup Top-5: {baseline.get('cup_top5_accuracy_pct', 0.0):.1f}%",
        f"- Avg Winner Rank: {baseline.get('cup_average_winner_rank', 0.0):.2f}",
        f"- Playoff F1: {baseline.get('playoff_f1', 0.0):.3f}",
        "",
        "## Final Keep / Reduce / Remove / Add Table",
        "",
        "| Feature | Decision | Confidence | Top1 Importance | Top5 Importance | Playoff Importance | Era Stable |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['feature']} | {r['final_decision']} | {r['confidence']} | "
            f"{r['importance']['cup_top1_importance']:.2f} | {r['importance']['cup_top5_importance']:.2f} | "
            f"{r['importance']['playoff_field_importance']:.2f} | {r['stability']['stable']} |"
        )

    lines += [
        "",
        "## Top Interaction Pairs",
        "",
        "| Pair | Cup Top1 | Cup Top5 | Winner Rank | Playoff F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in top_interactions:
        s = row.get("summary", {})
        pair = row.get("pair", ["?", "?"])
        lines.append(
            f"| {pair[0]} + {pair[1]} | {s.get('cup_top1_accuracy_pct', 0.0):.1f} | "
            f"{s.get('cup_top5_accuracy_pct', 0.0):.1f} | {s.get('cup_average_winner_rank', 0.0):.2f} | "
            f"{s.get('playoff_f1', 0.0):.3f} |"
        )

    lines += [
        "",
        "## Backlog Datapoints Still Missing",
        "",
    ]
    for name in unavailable:
        lines.append(f"- {name}")

    OUT_MD.write_text("\n".join(lines) + "\n")

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
