"""
pattern_generators.py
Blast Design Dashboard — Coordinate generators for all 7 patterns.
Each function returns a list of dicts: {x, y, row, col, delay, ...}
Units: meters. Origin (0,0) at bottom-left.
"""

import math
from typing import List, Dict, Any


Point = Dict[str, Any]


def gen_square(burden: float, spacing: float, rows: int, holes_per_row: int) -> List[Point]:
    """
    Square Pattern — equal spacing and burden, perfect grid layout.
    """
    points = []
    for r in range(rows):
        for h in range(holes_per_row):
            points.append({
                "x": round(h * spacing, 4),
                "y": round(r * burden, 4),
                "row": r,
                "col": h,
                "initiation": False,
            })
    return points


def gen_staggered(burden: float, spacing: float, rows: int, holes_per_row: int) -> List[Point]:
    """
    Staggered (Triangular) Pattern — alternate rows offset by spacing/2.
    Best fragmentation, commonly used in hard rock.
    """
    points = []
    for r in range(rows):
        offset = (spacing / 2) if (r % 2 == 1) else 0.0
        for h in range(holes_per_row):
            points.append({
                "x": round(h * spacing + offset, 4),
                "y": round(r * burden, 4),
                "row": r,
                "col": h,
                "initiation": False,
            })
    return points


def gen_rectangular(burden: float, spacing: float, rows: int, holes_per_row: int) -> List[Point]:
    """
    Rectangular Pattern — different spacing and burden ratio (S > B typically).
    Good for softer formations where burden can be increased.
    """
    points = []
    for r in range(rows):
        for h in range(holes_per_row):
            points.append({
                "x": round(h * spacing, 4),
                "y": round(r * burden, 4),
                "row": r,
                "col": h,
                "initiation": False,
            })
    return points


def gen_v_pattern(burden: float, spacing: float, rows: int, holes_per_row: int) -> List[Point]:
    """
    V-Pattern — production blasting pattern.
    Rows splay outward from a central initiation point.
    Used in high-output production blasts for good muck pile shape.
    """
    points = []
    mid_col = (holes_per_row - 1) / 2.0
    center_x = mid_col * spacing

    for r in range(rows):
        y = r * burden
        # Each successive row fans out by splay_factor * spacing
        splay = r * spacing * 0.22
        for h in range(holes_per_row):
            base_x = h * spacing
            dx = base_x - center_x
            # Push holes away from center proportionally
            vx = center_x + dx + (math.copysign(1, dx) * splay if dx != 0 else 0)
            is_init = (r == 0 and h == int(round(mid_col)))
            points.append({
                "x": round(vx, 4),
                "y": round(y, 4),
                "row": r,
                "col": h,
                "initiation": is_init,
            })
    return points


def gen_diagonal(burden: float, spacing: float, rows: int, holes_per_row: int) -> List[Point]:
    """
    Diagonal Pattern — holes arranged on a diagonal axis.
    Useful for cut-off blasting and controlled advance.
    """
    points = []
    diag_shift = spacing * 0.4  # each row shifts diagonally
    for r in range(rows):
        for h in range(holes_per_row):
            points.append({
                "x": round(h * spacing + r * diag_shift, 4),
                "y": round(r * burden, 4),
                "row": r,
                "col": h,
                "initiation": False,
            })
    return points


def gen_line_drilling(burden: float, spacing: float, rows: int, holes_per_row: int) -> List[Point]:
    """
    Line Drilling Pattern — all holes in a single straight line.
    Used for pre-splitting, perimeter control, and small blasts.
    rows parameter is ignored (always 1 row), total holes = rows * holes_per_row.
    """
    points = []
    total = rows * holes_per_row
    for i in range(total):
        points.append({
            "x": round(i * spacing, 4),
            "y": 0.0,
            "row": 0,
            "col": i,
            "initiation": False,
        })
    return points


def gen_fan(burden: float, spacing: float, rows: int, holes_per_row: int) -> List[Point]:
    """
    Fan Pattern — holes radiate from a single origin point.
    Used in underground mining, raise boring, and special cut geometries.
    """
    points = []
    total_holes = rows * holes_per_row
    # Angular spread of the fan
    angle_spread = math.pi * 0.80
    start_angle = math.pi / 2 - angle_spread / 2

    # Fan origin sits below the blast area
    center_x = (holes_per_row - 1) * spacing / 2.0
    origin_y = 0.0

    for i in range(total_holes):
        if total_holes > 1:
            angle = start_angle + (i / (total_holes - 1)) * angle_spread
        else:
            angle = math.pi / 2
        ring = i // holes_per_row
        radius = burden * (1.0 + ring * 0.85)
        bx = center_x + math.cos(angle) * radius
        by = origin_y + math.sin(angle) * radius
        points.append({
            "x": round(bx, 4),
            "y": round(by, 4),
            "row": ring,
            "col": i % holes_per_row,
            "initiation": False,
            "fan_origin": False,
        })

    # Add the fan origin as a special marker
    points.append({
        "x": round(center_x, 4),
        "y": round(origin_y, 4),
        "row": -1,
        "col": -1,
        "initiation": False,
        "fan_origin": True,
        "is_origin": True,
    })
    return points


# ─────────────────────────────────────────────
# DELAY SEQUENCER
# ─────────────────────────────────────────────

def assign_delays(points: List[Point], pattern: str) -> List[Point]:
    """
    Assign delay sequence numbers to each hole.
    Delay number represents firing order (1 = first to fire).
    """
    working = [p for p in points if not p.get("is_origin", False)]

    if pattern == "v_pattern":
        # V-pattern: initiation at centre, fire outward radially per row
        def sort_key(p):
            mid = max(pt["col"] for pt in working) / 2.0
            dist_from_mid = abs(p["col"] - mid)
            return (p["row"], dist_from_mid)
        working.sort(key=sort_key)
    else:
        # Default: row by row, left to right (front to back, left to right)
        working.sort(key=lambda p: (p["row"], p["x"]))

    for i, p in enumerate(working):
        p["delay"] = i + 1

    # Origin points get no delay
    for p in points:
        if p.get("is_origin"):
            p["delay"] = 0

    return points
