from typing import Any, Dict, List, Tuple


PATTERN_NAMES = [
    "square",
    "staggered",
    "rectangular",
    "v_pattern",
    "diagonal",
    "line_drilling",
    "fan",
]


def choose_pattern(
    burden: float,
    spacing: float,
    rock_type: str,
    rows: int,
    holes_per_row: int,
    suggested_pattern: str | None = None,
) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    ratio = spacing / burden
    total_holes = rows * holes_per_row

    if suggested_pattern in {"line_drilling", "staggered", "diagonal", "v_pattern"}:
        reasons.append(f"Initiation sequence preference points to {suggested_pattern.replace('_', ' ')}")

    if total_holes <= 4 or rows == 1:
        reasons.append(f"Small blast ({total_holes} holes / {rows} rows) -> Line Drilling for pre-split or trim")
        return "line_drilling", reasons

    if rock_type == "hard":
        if ratio > 1.20:
            reasons.append(f"Hard rock + high S/B ratio ({ratio:.2f}) -> Staggered for maximum fragmentation")
            return "staggered", reasons
        if suggested_pattern == "v_pattern" and rows >= 3:
            reasons.append(f"Hard rock with V-pattern initiation preference -> V-Pattern")
            return "v_pattern", reasons
        if rows >= 4:
            reasons.append(f"Hard rock, multiple rows ({rows}) -> V-Pattern for controlled production blast")
            return "v_pattern", reasons
        reasons.append("Hard rock, few rows -> Staggered for fragmentation efficiency")
        return "staggered", reasons

    if rock_type == "soft":
        if ratio < 1.05:
            reasons.append(f"Soft rock + near-equal S/B ({ratio:.2f}) -> Square for even energy distribution")
            return "square", reasons
        reasons.append(f"Soft rock + wider spacing ({ratio:.2f}) -> Rectangular to reduce over-break")
        return "rectangular", reasons

    if abs(ratio - 1.0) < 0.08:
        reasons.append(f"S/B approximately 1.0 ({ratio:.2f}) -> Square pattern")
        return "square", reasons

    if ratio > 1.45:
        reasons.append(f"High S/B ratio ({ratio:.2f}) -> Staggered for optimum fragmentation")
        return "staggered", reasons

    if ratio > 1.20:
        reasons.append(f"Moderate-high S/B ({ratio:.2f}) -> Staggered for improved throw")
        return "staggered", reasons

    if ratio < 0.88:
        reasons.append(f"Low S/B ratio ({ratio:.2f}) -> Rectangular layout")
        return "rectangular", reasons

    if suggested_pattern == "diagonal" and rows >= 4:
        reasons.append(f"Diagonal initiation preference with {rows} rows -> Diagonal pattern")
        return "diagonal", reasons

    if suggested_pattern == "v_pattern" and rows >= 3:
        reasons.append(f"V-pattern initiation preference with {rows} rows -> V-Pattern")
        return "v_pattern", reasons

    if rows >= 6:
        reasons.append(f"Many rows ({rows}) -> Diagonal pattern for controlled advance direction")
        return "diagonal", reasons

    if holes_per_row >= 8 and rows >= 3:
        reasons.append(f"Wide blast ({holes_per_row} holes/row x {rows} rows) -> V-Pattern")
        return "v_pattern", reasons

    if suggested_pattern == "staggered":
        reasons.append("Balanced parameters with staggered initiation preference -> Staggered")
        return "staggered", reasons

    reasons.append(f"Balanced parameters (S/B={ratio:.2f}, rock={rock_type}) -> Staggered as robust default")
    return "staggered", reasons


def get_pattern_metadata(pattern: str, params: Dict[str, Any]) -> Dict[str, Any]:
    burden = params["burden"]
    spacing = params["spacing"]
    bench_height = params["bench_height"]
    hole_depth = params["hole_depth"]
    rows = params["rows"]
    hpr = params["holes_per_row"]

    subdrill = hole_depth - bench_height
    sb_ratio = round(spacing / burden, 3)
    charge_per_hole = float(params.get("charge_per_hole", 0.0))
    powder_factor_input = params.get("powder_factor")
    hole_diameter_mm = float(params.get("hole_diameter_mm", 89))
    stemming_length = float(params.get("stemming_length", max(hole_depth * 0.35, 0)))
    predicted_subdrill = float(params.get("sub_drilling", subdrill))
    flyrock_distance = float(params.get("flyrock_distance", 0.0))
    bench_width = float(params.get("bench_width", hpr * spacing))

    blast_area = round((rows * burden) * (hpr * spacing), 2)
    total_holes = rows * hpr
    blasted_volume = total_holes * spacing * burden * bench_height
    total_explosive = total_holes * charge_per_hole if charge_per_hole > 0 else 0.0
    powder_factor = (
        round(float(powder_factor_input), 3)
        if powder_factor_input is not None
        else round(total_explosive / blasted_volume, 3) if blasted_volume > 0 else 0
    )

    return {
        "total_holes": total_holes,
        "rows": rows,
        "holes_per_row": hpr,
        "spacing_burden_ratio": sb_ratio,
        "subdrill_m": round(predicted_subdrill, 2),
        "stemming_length_m": round(stemming_length, 2),
        "hole_diameter_mm": round(hole_diameter_mm, 1),
        "blast_area_m2": blast_area,
        "bench_width_m": round(bench_width, 2),
        "blasted_volume_m3": round(blasted_volume, 1),
        "total_explosive_kg": round(total_explosive, 1),
        "powder_factor_kg_m3": powder_factor,
        "charge_per_hole_kg": round(charge_per_hole, 2),
        "flyrock_distance_m": round(flyrock_distance, 2),
        "pattern": pattern,
    }
