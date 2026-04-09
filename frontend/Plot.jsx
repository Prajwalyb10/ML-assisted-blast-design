// Plot.jsx
// SVG visualization of blast hole layout
// - Scales coordinates to fit viewport
// - Colors by row, highlights initiation points
// - Delay sequence numbers inside holes
// - Hover tooltips, grid lines, axis labels

import { useMemo, useState } from "react";

const ROW_COLORS = [
  "#f0b429", "#58a6ff", "#3fb950", "#ff6b35",
  "#bc8cff", "#39d353", "#f97316", "#e879f9",
  "#06b6d4", "#84cc16",
];

const PAD       = 72;
const SVG_W     = 720;
const SVG_H     = 520;
const PLOT_W    = SVG_W - PAD * 2;
const PLOT_H    = SVG_H - PAD * 2 - 10;

function scalePoints(points) {
  const holes = points.filter(p => !p.is_fan_origin);
  if (!holes.length) return { scaled: [], sx: () => 0, sy: () => 0, scale: 1 };

  const xs     = holes.map(p => p.x);
  const ys     = holes.map(p => p.y);
  const minX   = Math.min(...xs);
  const maxX   = Math.max(...xs);
  const minY   = Math.min(...ys);
  const maxY   = Math.max(...ys);
  const rangeX = maxX - minX || 1;
  const rangeY = maxY - minY || 1;

  const scaleX = PLOT_W / (rangeX * 1.15);
  const scaleY = PLOT_H / (rangeY * 1.15);
  const scale  = Math.min(scaleX, scaleY, 38);

  const offX = PAD + (PLOT_W - rangeX * scale) / 2;
  const offY = PAD;

  const sx = x => offX + (x - minX) * scale;
  const sy = y => offY + PLOT_H - (y - minY) * scale;

  return { sx, sy, scale, minX, minY, rangeX, rangeY, offX, offY };
}

export default function Plot({ design }) {
  const [hovered, setHovered]     = useState(null);
  const [mousePos, setMousePos]   = useState({ x: 0, y: 0 });

  const { points, pattern, metadata } = design;
  const { sx, sy, scale, rangeX, rangeY, offX, offY } = useMemo(
    () => scalePoints(points), [points]
  );

  // Group holes by row for row-lines
  const byRow = useMemo(() => {
    const m = {};
    points.forEach(p => {
      if (p.is_fan_origin) return;
      if (!m[p.row]) m[p.row] = [];
      m[p.row].push(p);
    });
    return m;
  }, [points]);

  const holeRadius = Math.max(7, Math.min(15, scale * 0.38));

  // Grid ticks (every 5 m)
  const gridStep = 5;
  const xTicks = [];
  for (let v = 0; v <= Math.ceil(rangeX + 5); v += gridStep) xTicks.push(v);
  const yTicks = [];
  for (let v = 0; v <= Math.ceil(rangeY + 5); v += gridStep) yTicks.push(v);

  return (
    <div className="plot-wrap">
      {/* Toolbar */}
      <div className="plot-toolbar">
        <span className="plot-pattern-name">{design.pattern.replace("_", " ").toUpperCase()}</span>
        <span className="chip">{metadata.total_holes} holes</span>
        <span className="chip">{metadata.rows} rows</span>
        <span className="chip">S/B = {metadata.spacing_burden_ratio}</span>
      </div>

      {/* SVG */}
      <div className="svg-scroll">
        <svg
          width={SVG_W} height={SVG_H}
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          onMouseMove={e => {
            const r = e.currentTarget.getBoundingClientRect();
            setMousePos({ x: e.clientX - r.left, y: e.clientY - r.top });
          }}
        >
          <defs>
            <pattern id="bg-grid" width={scale * gridStep} height={scale * gridStep}
              patternUnits="userSpaceOnUse"
              x={(offX) % (scale * gridStep)} y={(offY) % (scale * gridStep)}>
              <path d={`M ${scale * gridStep} 0 L 0 0 0 ${scale * gridStep}`}
                fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
            </pattern>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2.5" result="c"/>
              <feMerge><feMergeNode in="c"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
            <marker id="ax-arr" viewBox="0 0 8 8" refX="7" refY="4"
              markerWidth="5" markerHeight="5" orient="auto">
              <path d="M1 1L7 4L1 7" fill="none" stroke="rgba(255,255,255,0.3)"
                strokeWidth="1.5" strokeLinecap="round"/>
            </marker>
          </defs>

          {/* Background */}
          <rect width={SVG_W} height={SVG_H} fill="#0d1117"/>
          <rect width={SVG_W} height={SVG_H} fill="url(#bg-grid)"/>

          {/* Plot area */}
          <rect x={offX - 6} y={offY - 6}
            width={rangeX * scale + 12 + 20}
            height={PLOT_H + 12}
            fill="rgba(255,255,255,0.015)"
            stroke="rgba(255,255,255,0.07)" strokeWidth="0.5" rx="6"/>

          {/* Axes */}
          <line
            x1={offX} y1={offY + PLOT_H + 8}
            x2={offX + rangeX * scale + 40} y2={offY + PLOT_H + 8}
            stroke="rgba(255,255,255,0.22)" strokeWidth="0.8"
            markerEnd="url(#ax-arr)"/>
          <line
            x1={offX} y1={offY + PLOT_H + 8}
            x2={offX} y2={offY - 20}
            stroke="rgba(255,255,255,0.22)" strokeWidth="0.8"
            markerEnd="url(#ax-arr)"/>

          {/* Axis labels */}
          <text x={offX + rangeX * scale / 2 + 20} y={SVG_H - 6}
            textAnchor="middle"
            fontFamily="Space Grotesk, sans-serif" fontSize="10"
            fill="rgba(255,255,255,0.3)" letterSpacing="0.08em">
            SPACING DIRECTION (m)
          </text>
          <text
            x={18} y={offY + PLOT_H / 2}
            textAnchor="middle"
            fontFamily="Space Grotesk, sans-serif" fontSize="10"
            fill="rgba(255,255,255,0.3)" letterSpacing="0.08em"
            transform={`rotate(-90 18 ${offY + PLOT_H / 2})`}>
            BURDEN DIRECTION (m)
          </text>

          {/* Row connector lines */}
          {Object.entries(byRow).map(([rowIdx, rowPts]) => {
            const sorted = [...rowPts].sort((a, b) => a.x - b.x);
            const color  = ROW_COLORS[parseInt(rowIdx) % ROW_COLORS.length];
            return sorted.slice(0, -1).map((p, i) => {
              const p2 = sorted[i + 1];
              return (
                <line key={`${rowIdx}-${i}`}
                  x1={sx(p.x)} y1={sy(p.y)}
                  x2={sx(p2.x)} y2={sy(p2.y)}
                  stroke={color + "50"} strokeWidth="1"
                  strokeDasharray="4 3"/>
              );
            });
          })}

          {/* Fan lines from origin */}
          {pattern === "fan" && (() => {
            const origin = points.find(p => p.is_fan_origin);
            if (!origin) return null;
            return points
              .filter(p => !p.is_fan_origin)
              .map(p => (
                <line key={`fan-${p.id}`}
                  x1={sx(origin.x)} y1={sy(origin.y)}
                  x2={sx(p.x)} y2={sy(p.y)}
                  stroke="rgba(188,140,255,0.15)" strokeWidth="0.8"/>
              ));
          })()}

          {/* Holes */}
          {points.filter(p => !p.is_fan_origin).map(p => {
            const cx     = sx(p.x);
            const cy     = sy(p.y);
            const color  = p.is_initiation
              ? "#ffff00"
              : ROW_COLORS[p.row % ROW_COLORS.length];
            const isHov  = hovered === p.id;

            return (
              <g key={p.id}
                style={{ cursor: "pointer" }}
                onMouseEnter={() => setHovered(p.id)}
                onMouseLeave={() => setHovered(null)}>

                {/* Outer glow ring on hover */}
                {isHov && (
                  <circle cx={cx} cy={cy} r={holeRadius + 5}
                    fill={color} opacity="0.12"/>
                )}

                {/* Main hole circle */}
                <circle cx={cx} cy={cy} r={holeRadius}
                  fill={color} fillOpacity={p.is_initiation ? 0.35 : 0.18}
                  stroke={color} strokeWidth={p.is_initiation ? 2.5 : 1.5}
                  filter={p.is_initiation ? "url(#glow)" : undefined}/>

                {/* Delay number */}
                <text x={cx} y={cy + 0.5}
                  textAnchor="middle" dominantBaseline="central"
                  fontFamily="JetBrains Mono, monospace"
                  fontSize={Math.max(7, holeRadius * 0.7)}
                  fontWeight="500" fill={color}>
                  {p.delay_sequence}
                </text>
              </g>
            );
          })}

          {/* Fan origin marker */}
          {pattern === "fan" && (() => {
            const origin = points.find(p => p.is_fan_origin);
            if (!origin) return null;
            const cx = sx(origin.x), cy = sy(origin.y);
            return (
              <g>
                <circle cx={cx} cy={cy} r={10}
                  fill="#bc8cff" fillOpacity="0.3"
                  stroke="#bc8cff" strokeWidth="2"
                  filter="url(#glow)"/>
                <text x={cx} y={cy + 0.5}
                  textAnchor="middle" dominantBaseline="central"
                  fontFamily="JetBrains Mono, monospace" fontSize="9"
                  fontWeight="700" fill="#bc8cff">F</text>
              </g>
            );
          })()}

          {/* Scale bar */}
          {scale > 5 && (() => {
            const barLen = scale * 5;
            const bx = SVG_W - 80, by = SVG_H - 22;
            return (
              <g>
                <line x1={bx - barLen/2} y1={by} x2={bx + barLen/2} y2={by}
                  stroke="rgba(255,255,255,0.35)" strokeWidth="1.5" strokeLinecap="round"/>
                <line x1={bx - barLen/2} y1={by-4} x2={bx - barLen/2} y2={by+4}
                  stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
                <line x1={bx + barLen/2} y1={by-4} x2={bx + barLen/2} y2={by+4}
                  stroke="rgba(255,255,255,0.35)" strokeWidth="1.5"/>
                <text x={bx} y={by - 7} textAnchor="middle"
                  fontFamily="JetBrains Mono, monospace" fontSize="9"
                  fill="rgba(255,255,255,0.4)">5 m</text>
              </g>
            );
          })()}
        </svg>
      </div>

      {/* Tooltip */}
      {hovered !== null && (() => {
        const p = points.find(q => q.id === hovered);
        if (!p) return null;
        return (
          <div className="plot-tooltip" style={{
            left: mousePos.x + 14,
            top:  mousePos.y - 10,
          }}>
            <div className="tt-title">Hole #{p.delay_sequence}</div>
            <div className="tt-row">X: <strong>{p.x.toFixed(3)} m</strong></div>
            <div className="tt-row">Y: <strong>{p.y.toFixed(3)} m</strong></div>
            <div className="tt-row">Row: <strong>{p.row + 1}</strong></div>
            <div className="tt-row">Delay: <strong>#{p.delay_sequence}</strong></div>
            {p.is_initiation && (
              <div className="tt-init">⚡ Initiation Point</div>
            )}
          </div>
        );
      })()}

      {/* Legend */}
      <div className="plot-legend">
        {[...new Set(points.map(p => p.row))].filter(r => r >= 0).slice(0, 5).map(r => (
          <div key={r} className="leg-item">
            <span className="leg-dot" style={{ background: ROW_COLORS[r % ROW_COLORS.length] }}/>
            Row {r + 1}
          </div>
        ))}
        {points.some(p => p.is_initiation) && (
          <div className="leg-item">
            <span className="leg-dot init-dot"/>
            Initiation
          </div>
        )}
        {pattern === "fan" && (
          <div className="leg-item">
            <span className="leg-dot" style={{ background: "#bc8cff" }}/>
            Fan Origin
          </div>
        )}
        <div className="leg-note">Hover holes for coordinates · Numbers = delay sequence</div>
      </div>
    </div>
  );
}
