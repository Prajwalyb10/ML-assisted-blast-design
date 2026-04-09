import { useEffect, useState } from "react";

const PATTERNS = [
  { value: "", label: "Auto Select" },
  { value: "square", label: "Square" },
  { value: "staggered", label: "Staggered" },
  { value: "rectangular", label: "Rectangular" },
  { value: "v_pattern", label: "V-Pattern" },
  { value: "diagonal", label: "Diagonal" },
  { value: "line_drilling", label: "Line Drilling" },
  { value: "fan", label: "Fan" },
];

const FALLBACK_DEFAULTS = {
  rows: 4,
  holes_per_row: 6,
  rock_type_code: 5,
  density_gcc: 2.6,
  ucs_mpa: 120,
  rqd_percent: 75,
  hardness: 6,
  joint_spacing_m: 1.2,
  joint_orientation_deg: 45,
  fracture_frequency_per_m: 6,
  powder_factor_kg_m3: 0.8,
  delay_timing_ms: 42,
  initiation_sequence_code: 2,
  bench_height_m: 12,
  hole_diameter_mm: 150,
  hole_depth_m: 15,
  explosive_type_code: 2,
  bench_width_m: 12,
  slope_angle_deg: 50,
  overall_slope_angle_deg: 44,
  pit_length_m: 600,
  temperature_c: 30,
  rainfall_mm: 50,
  humidity_percent: 60,
  pattern_override: "",
};

function createInitialState(referenceData) {
  if (!referenceData?.defaults) return FALLBACK_DEFAULTS;
  const defaults = referenceData.defaults;
  return {
    rows: 4,
    holes_per_row: 6,
    rock_type_code: Math.round(defaults["Rock Type (Limestone-1,Shale-3,Sandstone-4,Basalt-5,Granite-6)"] ?? 5),
    density_gcc: defaults["Density (g/cc)"] ?? 2.6,
    ucs_mpa: defaults["UCS (MPa)"] ?? 120,
    rqd_percent: defaults["RQD (%)"] ?? 75,
    hardness: Math.round(defaults.Hardness ?? 6),
    joint_spacing_m: defaults["Joint Spacing (m)"] ?? 1.2,
    joint_orientation_deg: Math.round(defaults["Joint Orientation (deg)"] ?? 45),
    fracture_frequency_per_m: Math.round(defaults["Fracture Frequency (/m)"] ?? 6),
    powder_factor_kg_m3: defaults["Powder Factor (kg/m3)"] ?? 0.8,
    delay_timing_ms: Math.round(defaults["Delay Timing (ms)"] ?? 42),
    initiation_sequence_code: 2,
    bench_height_m: defaults["Bench Height (m)"] ?? 12,
    hole_diameter_mm: Math.round(defaults["Hole Diameter (mm)"] ?? 150),
    hole_depth_m: defaults["Hole Depth (m)"] ?? 15,
    explosive_type_code: 2,
    bench_width_m: defaults["Bench Width (m)"] ?? 12,
    slope_angle_deg: Math.round(defaults["Slope Angle (deg)"] ?? 50),
    overall_slope_angle_deg: Math.round(defaults["Overall Slope Angle (deg)"] ?? 44),
    pit_length_m: defaults["Pit Length (m)"] ?? 600,
    temperature_c: Math.round(defaults["Temperature (C)"] ?? 30),
    rainfall_mm: Math.round(defaults["Rainfall (mm)"] ?? 50),
    humidity_percent: Math.round(defaults["Humidity (%)"] ?? 60),
    pattern_override: "",
  };
}

function NumberField({ label, name, value, onChange, step = 1, min, max }) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}<span className="field-val">{value}</span></label>
      <input
        id={name}
        type="number"
        className="text-input"
        name={name}
        value={value}
        step={step}
        min={min}
        max={max}
        onChange={onChange}
      />
    </div>
  );
}

function SelectField({ label, name, value, onChange, options }) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <select id={name} name={name} value={value} onChange={onChange}>
        {options.map(option => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </div>
  );
}

function mapOptions(optionMap) {
  return Object.entries(optionMap || {}).map(([value, label]) => ({
    value: Number(value),
    label: `${label} (${value})`,
  }));
}

export default function Form({ onGenerate, loading, referenceData, bootLoading }) {
  const [form, setForm] = useState(() => createInitialState(referenceData));

  useEffect(() => {
    if (referenceData) {
      setForm(createInitialState(referenceData));
    }
  }, [referenceData]);

  function updateField(event) {
    const { name, value } = event.target;
    const numericValue = name === "pattern_override" ? value : Number(value);
    setForm(current => ({ ...current, [name]: numericValue }));
  }

  function handleSubmit() {
    onGenerate({
      ...form,
      pattern_override: form.pattern_override || null,
    });
  }

  const rockOptions = mapOptions(referenceData?.options?.rock_type);
  const explosiveOptions = mapOptions(referenceData?.options?.explosive_type);
  const initiationOptions = mapOptions(referenceData?.options?.initiation_sequence);
  const invalidDepth = form.hole_depth_m < form.bench_height_m;

  return (
    <div className="form-panel">
      <div className="form-section-title">Blast Inputs</div>
      <div className="mini-note">The backend predicts burden, spacing, charge, stemming, sub-drill, and flyrock from these inputs.</div>

      {bootLoading ? (
        <div className="inline-warn">Loading dataset defaults...</div>
      ) : (
        <>
          <div className="subsection-title">Layout</div>
          <div className="row2">
            <NumberField label="Rows" name="rows" value={form.rows} onChange={updateField} min={1} max={20} />
            <NumberField label="Holes/Row" name="holes_per_row" value={form.holes_per_row} onChange={updateField} min={1} max={30} />
          </div>
          <SelectField label="Pattern Override" name="pattern_override" value={form.pattern_override} onChange={updateField} options={PATTERNS} />

          <div className="subsection-title">Rock Mass</div>
          <SelectField label="Rock Type" name="rock_type_code" value={form.rock_type_code} onChange={updateField} options={rockOptions} />
          <div className="row2">
            <NumberField label="Density (g/cc)" name="density_gcc" value={form.density_gcc} onChange={updateField} step={0.01} min={1} max={4} />
            <NumberField label="UCS (MPa)" name="ucs_mpa" value={form.ucs_mpa} onChange={updateField} step={0.1} min={1} max={400} />
          </div>
          <div className="row2">
            <NumberField label="RQD (%)" name="rqd_percent" value={form.rqd_percent} onChange={updateField} step={0.1} min={0} max={100} />
            <NumberField label="Hardness" name="hardness" value={form.hardness} onChange={updateField} min={1} max={10} />
          </div>
          <div className="row2">
            <NumberField label="Joint Spacing (m)" name="joint_spacing_m" value={form.joint_spacing_m} onChange={updateField} step={0.01} min={0.01} max={10} />
            <NumberField label="Joint Orientation (deg)" name="joint_orientation_deg" value={form.joint_orientation_deg} onChange={updateField} min={0} max={180} />
          </div>
          <NumberField label="Fracture Frequency (/m)" name="fracture_frequency_per_m" value={form.fracture_frequency_per_m} onChange={updateField} min={0} max={100} />

          <div className="subsection-title">Bench and Timing</div>
          <div className="row2">
            <NumberField label="Bench Height (m)" name="bench_height_m" value={form.bench_height_m} onChange={updateField} step={0.1} min={1} max={50} />
            <NumberField label="Hole Depth (m)" name="hole_depth_m" value={form.hole_depth_m} onChange={updateField} step={0.1} min={1} max={60} />
          </div>
          <div className="row2">
            <NumberField label="Hole Diameter (mm)" name="hole_diameter_mm" value={form.hole_diameter_mm} onChange={updateField} min={50} max={500} />
            <NumberField label="Bench Width (m)" name="bench_width_m" value={form.bench_width_m} onChange={updateField} step={0.1} min={1} max={100} />
          </div>
          <div className="row2">
            <NumberField label="Powder Factor" name="powder_factor_kg_m3" value={form.powder_factor_kg_m3} onChange={updateField} step={0.01} min={0.01} max={5} />
            <NumberField label="Delay Timing (ms)" name="delay_timing_ms" value={form.delay_timing_ms} onChange={updateField} min={0} max={1000} />
          </div>
          <div className="row2">
            <SelectField label="Initiation Sequence" name="initiation_sequence_code" value={form.initiation_sequence_code} onChange={updateField} options={initiationOptions} />
            <SelectField label="Explosive Type" name="explosive_type_code" value={form.explosive_type_code} onChange={updateField} options={explosiveOptions} />
          </div>

          <div className="subsection-title">Environment</div>
          <NumberField label="Pit Length (m)" name="pit_length_m" value={form.pit_length_m} onChange={updateField} step={0.1} min={1} max={5000} />
          <div className="row2">
            <NumberField label="Slope Angle (deg)" name="slope_angle_deg" value={form.slope_angle_deg} onChange={updateField} min={0} max={90} />
            <NumberField label="Overall Slope (deg)" name="overall_slope_angle_deg" value={form.overall_slope_angle_deg} onChange={updateField} min={0} max={90} />
          </div>
          <div className="row2">
            <NumberField label="Temperature (C)" name="temperature_c" value={form.temperature_c} onChange={updateField} min={-20} max={80} />
            <NumberField label="Rainfall (mm)" name="rainfall_mm" value={form.rainfall_mm} onChange={updateField} min={0} max={1000} />
          </div>
          <NumberField label="Humidity (%)" name="humidity_percent" value={form.humidity_percent} onChange={updateField} min={0} max={100} />

          {invalidDepth && <div className="inline-warn">Hole depth must be greater than or equal to bench height.</div>}

          <button className="btn-generate" onClick={handleSubmit} disabled={loading || invalidDepth}>
            {loading ? "Generating..." : "Generate Blast Design"}
          </button>
        </>
      )}
    </div>
  );
}
