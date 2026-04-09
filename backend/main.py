from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator

from blast_ml import BlastMLService, rock_code_to_category
from pattern_generators import (
    assign_delays,
    gen_diagonal,
    gen_fan,
    gen_line_drilling,
    gen_rectangular,
    gen_square,
    gen_staggered,
    gen_v_pattern,
)
from pattern_selector import choose_pattern, get_pattern_metadata


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("blast_api")

DATASET_PATH = Path(__file__).with_name("blast_ml_dataset.csv")
ml_service = BlastMLService(DATASET_PATH)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

app = FastAPI(
    title="Blast Design Dashboard API",
    description="ML-backed blast design recommendation and pattern generation API",
    version="2.0.0",
    contact={"name": "Blast Design System"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BlastDesignRequest(BaseModel):
    rows: int = Field(4, ge=1, le=20)
    holes_per_row: int = Field(6, ge=1, le=30)
    rock_type_code: int = Field(..., ge=1, le=6)
    density_gcc: float = Field(..., gt=1.0, le=4.0)
    ucs_mpa: float = Field(..., gt=1.0, le=400.0)
    rqd_percent: float = Field(..., ge=0.0, le=100.0)
    hardness: int = Field(..., ge=1, le=10)
    joint_spacing_m: float = Field(..., gt=0.0, le=10.0)
    joint_orientation_deg: int = Field(..., ge=0, le=180)
    fracture_frequency_per_m: int = Field(..., ge=0, le=100)
    powder_factor_kg_m3: float = Field(..., gt=0.0, le=5.0)
    delay_timing_ms: int = Field(..., ge=0, le=1000)
    initiation_sequence_code: int = Field(..., ge=1, le=4)
    bench_height_m: float = Field(..., gt=0.0, le=50.0)
    hole_diameter_mm: int = Field(..., ge=50, le=500)
    hole_depth_m: float = Field(..., gt=0.0, le=60.0)
    explosive_type_code: int = Field(..., ge=1, le=3)
    bench_width_m: float = Field(..., gt=0.0, le=100.0)
    slope_angle_deg: int = Field(..., ge=0, le=90)
    overall_slope_angle_deg: int = Field(..., ge=0, le=90)
    pit_length_m: float = Field(..., gt=0.0, le=5000.0)
    temperature_c: int = Field(..., ge=-20, le=80)
    rainfall_mm: int = Field(..., ge=0, le=1000)
    humidity_percent: int = Field(..., ge=0, le=100)
    pattern_override: Optional[str] = None

    @field_validator("pattern_override")
    @classmethod
    def validate_pattern(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        valid = {"square", "staggered", "rectangular", "v_pattern", "diagonal", "line_drilling", "fan"}
        if value not in valid:
            raise ValueError(f"pattern_override must be one of {sorted(valid)}")
        return value

    @model_validator(mode="after")
    def validate_depth(self) -> "BlastDesignRequest":
        if self.hole_depth_m < self.bench_height_m:
            raise ValueError("hole_depth_m must be greater than or equal to bench_height_m")
        return self

    def to_feature_payload(self) -> Dict[str, Any]:
        return {
            "Rock Type (Limestone-1,Shale-3,Sandstone-4,Basalt-5,Granite-6)": self.rock_type_code,
            "Density (g/cc)": self.density_gcc,
            "UCS (MPa)": self.ucs_mpa,
            "RQD (%)": self.rqd_percent,
            "Hardness": self.hardness,
            "Joint Spacing (m)": self.joint_spacing_m,
            "Joint Orientation (deg)": self.joint_orientation_deg,
            "Fracture Frequency (/m)": self.fracture_frequency_per_m,
            "Powder Factor (kg/m3)": self.powder_factor_kg_m3,
            "Delay Timing (ms)": self.delay_timing_ms,
            "Initiation Sequence (Line-1,Staggered-2,Diagonal-3,Vpattern-4)": self.initiation_sequence_code,
            "Bench Height (m)": self.bench_height_m,
            "Hole Diameter (mm)": self.hole_diameter_mm,
            "Hole Depth (m)": self.hole_depth_m,
            "Explosive Type(Emulsion-1,ANFO-2,Slurry-3)": self.explosive_type_code,
            "Bench Width (m)": self.bench_width_m,
            "Slope Angle (deg)": self.slope_angle_deg,
            "Overall Slope Angle (deg)": self.overall_slope_angle_deg,
            "Pit Length (m)": self.pit_length_m,
            "Temperature (C)": self.temperature_c,
            "Rainfall (mm)": self.rainfall_mm,
            "Humidity (%)": self.humidity_percent,
        }


class HolePoint(BaseModel):
    id: int
    x: float
    y: float
    row: int
    col: int
    delay_sequence: int
    is_initiation: bool
    is_fan_origin: Optional[bool] = False


class BlastResponse(BaseModel):
    pattern: str
    ai_selected: bool
    ai_reasons: List[str]
    points: List[HolePoint]
    metadata: Dict[str, Any]
    predictions: Dict[str, float]
    model_metrics: Dict[str, Dict[str, float | str]]
    input_summary: Dict[str, Any]


GENERATORS = {
    "square": gen_square,
    "staggered": gen_staggered,
    "rectangular": gen_rectangular,
    "v_pattern": gen_v_pattern,
    "diagonal": gen_diagonal,
    "line_drilling": gen_line_drilling,
    "fan": gen_fan,
}


def preferred_pattern_from_sequence(sequence_code: int) -> Optional[str]:
    return {
        1: "line_drilling",
        2: "staggered",
        3: "diagonal",
        4: "v_pattern",
    }.get(sequence_code)


def build_response_points(raw_points: List[Dict[str, Any]]) -> List[HolePoint]:
    response_points: List[HolePoint] = []
    hole_id = 1
    for point in raw_points:
        current_id = 0 if point.get("is_origin") else hole_id
        response_points.append(
            HolePoint(
                id=current_id,
                x=point["x"],
                y=point["y"],
                row=point["row"],
                col=point["col"],
                delay_sequence=point.get("delay", current_id),
                is_initiation=point.get("initiation", False),
                is_fan_origin=point.get("fan_origin", point.get("is_origin", False)),
            )
        )
        if not point.get("is_origin"):
            hole_id += 1
    return response_points


@app.get("/", tags=["Health"])
def root() -> Dict[str, Any]:
    return {
        "service": "Blast Design Dashboard API",
        "version": "2.0.0",
        "status": "operational",
        "dataset": str(DATASET_PATH),
        "endpoints": ["/generate-pattern", "/patterns", "/reference-data", "/health"],
    }


@app.get("/health", tags=["Health"])
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "dataset_loaded": DATASET_PATH.exists(),
        "models": list(ml_service.targets.keys()),
    }


@app.get("/reference-data", tags=["Reference"])
def reference_data() -> Dict[str, Any]:
    return ml_service.reference_data


@app.get("/patterns", tags=["Reference"])
def list_patterns() -> Dict[str, Any]:
    return {
        "patterns": [
            {"key": "square", "name": "Square", "description": "Equal spacing and burden in a regular grid."},
            {"key": "staggered", "name": "Staggered", "description": "Offset rows for stronger fragmentation performance."},
            {"key": "rectangular", "name": "Rectangular", "description": "Wider spacing with softer formations."},
            {"key": "v_pattern", "name": "V-Pattern", "description": "Production blast layout with central initiation."},
            {"key": "diagonal", "name": "Diagonal", "description": "Controlled advance direction through row offset."},
            {"key": "line_drilling", "name": "Line Drilling", "description": "Pre-split or trim blasts with minimal rows."},
            {"key": "fan", "name": "Fan", "description": "Radial fan geometry for special blasting layouts."},
        ]
    }


@app.post("/generate-pattern", response_model=BlastResponse, tags=["Blast Design"])
def generate_pattern(req: BlastDesignRequest) -> BlastResponse:
    feature_payload = ml_service.build_feature_payload(req.to_feature_payload())
    input_summary = ml_service.summarize_inputs(feature_payload)
    predictions = ml_service.predict(feature_payload)

    if req.pattern_override:
        pattern_key = req.pattern_override
        ai_selected = False
        reasons = [f"Pattern manually overridden to: {pattern_key}"]
    else:
        ai_selected = True
        suggested_pattern = preferred_pattern_from_sequence(req.initiation_sequence_code)
        pattern_key, reasons = choose_pattern(
            predictions["burden"],
            predictions["spacing"],
            rock_code_to_category(req.rock_type_code),
            req.rows,
            req.holes_per_row,
            suggested_pattern=suggested_pattern,
        )

    if pattern_key not in GENERATORS:
        raise HTTPException(status_code=400, detail=f"Unknown pattern: {pattern_key}")

    raw_points = GENERATORS[pattern_key](
        predictions["burden"],
        predictions["spacing"],
        req.rows,
        req.holes_per_row,
    )
    raw_points = assign_delays(raw_points, pattern_key)

    metadata = get_pattern_metadata(
        pattern_key,
        {
            "burden": predictions["burden"],
            "spacing": predictions["spacing"],
            "bench_height": req.bench_height_m,
            "hole_depth": req.hole_depth_m,
            "rows": req.rows,
            "holes_per_row": req.holes_per_row,
            "charge_per_hole": predictions["charge_per_hole"],
            "powder_factor": req.powder_factor_kg_m3,
            "hole_diameter_mm": req.hole_diameter_mm,
            "stemming_length": predictions["stemming_length"],
            "sub_drilling": predictions["sub_drilling"],
            "flyrock_distance": predictions["flyrock_distance"],
            "bench_width": req.bench_width_m,
        },
    )
    metadata["selected_features"] = ml_service.selected_features

    response_points = build_response_points(raw_points)
    logger.info(
        "Generated pattern=%s holes=%s burden=%.3f spacing=%.3f",
        pattern_key,
        len(response_points),
        predictions["burden"],
        predictions["spacing"],
    )

    return BlastResponse(
        pattern=pattern_key,
        ai_selected=ai_selected,
        ai_reasons=reasons,
        points=response_points,
        metadata=metadata,
        predictions=predictions,
        model_metrics=ml_service.reference_data["model_metrics"],
        input_summary=input_summary,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
