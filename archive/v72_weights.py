"""
Archived V7.2 Championship Weight Formula
==========================================
Removed from merge_data.py in favor of the Superhuman ML model.
All team scoring is now handled by the ensemble model in superhuman/.

Kept for reference only.
"""


def calculate_v72_weight(team):
    """
    V7.2 hand-tuned weight formula (retired).

    V7.2 Weights: HDCF% 25%, CF% 15%, PDO 12%, PP% 15%, PK% 13%, GSAx 20%
    Each metric normalized to 0-100 scale then weighted.
    Final weight ranges roughly 100-300 (200 = average).
    """

    def normalize(value, min_val, max_val, invert=False):
        if max_val == min_val:
            return 50
        normalized = (value - min_val) / (max_val - min_val) * 100
        if invert:
            normalized = 100 - normalized
        return max(0, min(100, normalized))

    hdcf_pct = team.get("hdcfPct", 50.0)
    cf_pct = team.get("cfPct", 50.0)
    pdo = team.get("pdo", 1.0)
    if pdo < 2:
        pdo = pdo * 100
    pp_pct = team.get("ppPct", 20.0)
    pk_pct = team.get("pkPct", 80.0)
    gsax = team.get("gsax", 0.0)

    hdcf_norm = normalize(hdcf_pct, 42, 58)
    cf_norm = normalize(cf_pct, 44, 56)
    pdo_norm = normalize(pdo, 96, 104)
    pp_norm = normalize(pp_pct, 12, 30)
    pk_norm = normalize(pk_pct, 72, 88)
    gsax_norm = normalize(gsax, -25, 25)

    weight_score = (
        hdcf_norm * 0.25 +
        cf_norm * 0.15 +
        pdo_norm * 0.12 +
        pp_norm * 0.15 +
        pk_norm * 0.13 +
        gsax_norm * 0.20
    )

    return round(100 + weight_score * 2, 0)
