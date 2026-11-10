import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { activeStep, clips, SceneSpec, Timing } from "../data";
import { C, mono, sans } from "../theme";
import { Clip } from "../components/Media";
import { TABLES, TOOLS } from "../tables";

const useEnter = (delay = 0) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: f - delay, fps, config: { damping: 20 } });
};

const Shade: React.FC<{ dir?: string; strength?: number }> = ({ dir = "90deg", strength = 0.85 }) => (
  <AbsoluteFill
    style={{ background: `linear-gradient(${dir}, rgba(8,9,12,${strength}) 0%, rgba(8,9,12,${strength * 0.5}) 40%, rgba(8,9,12,0) 70%)` }}
  />
);

export const Title: React.FC<{ spec: SceneSpec; t: Timing }> = ({ spec }) => {
  const f = useCurrentFrame();
  const a = useEnter(15);
  const b = useEnter(35);
  const chips = ["66 keys", "Wireless split", "nRF52840 · ZMK", "Per-key RGB", "Encoder + OLED per half"];
  return (
    <AbsoluteFill>
      <Clip name="hero" />
      <Shade />
      <div style={{ position: "absolute", left: 120, top: 330 }}>
        <div style={{ fontFamily: mono, fontSize: 26, letterSpacing: 8, color: C.accent, opacity: a }}>BUILD GUIDE</div>
        <div
          style={{
            fontFamily: sans,
            fontSize: 190,
            fontWeight: 800,
            letterSpacing: -4,
            color: C.text,
            lineHeight: 1,
            marginTop: 10,
            opacity: a,
            transform: `translateY(${(1 - a) * 30}px)`,
          }}
        >
          {spec.title}
        </div>
        <div style={{ height: 6, width: 420 * b, marginTop: 26, background: `linear-gradient(90deg, ${C.accent}, ${C.accent2})`, borderRadius: 3 }} />
        <div style={{ display: "flex", gap: 14, marginTop: 34, flexWrap: "wrap", width: 900 }}>
          {chips.map((c, i) => {
            const o = interpolate(f, [50 + i * 6, 62 + i * 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return (
              <div
                key={c}
                style={{
                  opacity: o,
                  fontFamily: sans,
                  fontSize: 25,
                  fontWeight: 500,
                  color: C.text,
                  padding: "10px 18px",
                  borderRadius: 999,
                  background: "rgba(20,22,30,0.75)",
                  border: `1px solid ${C.border}`,
                }}
              >
                {c}
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Chapter: React.FC<{ spec: SceneSpec; t: Timing }> = ({ spec }) => {
  const a = useEnter(0);
  const b = useEnter(8);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 50 }}>
        <div
          style={{
            fontFamily: mono,
            fontSize: 220,
            fontWeight: 600,
            color: "transparent",
            WebkitTextStroke: `3px ${C.accent}`,
            opacity: a,
            transform: `scale(${0.9 + 0.1 * a})`,
          }}
        >
          {spec.number}
        </div>
        <div style={{ width: 6, height: 220 * b, background: `linear-gradient(${C.accent}, ${C.accent2})`, borderRadius: 3 }} />
        <div style={{ opacity: b, transform: `translateX(${(1 - b) * 30}px)` }}>
          <div style={{ fontFamily: mono, fontSize: 26, letterSpacing: 6, color: C.muted }}>CHAPTER {spec.number}</div>
          <div style={{ fontFamily: sans, fontSize: 92, fontWeight: 800, color: C.text, lineHeight: 1.05, maxWidth: 1000 }}>
            {spec.title}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** The exploded half, each layer labelled where it hangs (anchors come from the Blender clip). */
export const Explode: React.FC<{ spec: SceneSpec; t: Timing }> = ({ spec, t }) => {
  const f = useCurrentFrame();
  const active = activeStep(t, f);
  const meta = clips["explode"];
  const anchors = meta?.anchors ?? {};
  const labelX = 1450;
  const show = interpolate(f, [100, 120], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const names = spec.steps ?? [];
  return (
    <AbsoluteFill>
      <Clip name="explode" />
      <AbsoluteFill style={{ background: "linear-gradient(270deg, rgba(8,9,12,0.8) 0%, rgba(8,9,12,0) 35%)" }} />
      <div style={{ position: "absolute", left: 80, top: 110, fontFamily: sans, fontSize: 56, fontWeight: 800, color: C.text }}>
        {spec.heading}
      </div>
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0, opacity: show }}>
        {names.map((n, i) => {
          const a = anchors[n];
          if (!a) return null;
          const x = a[0] * 1920, y = a[1] * 1080;
          const on = i === active;
          const seen = i <= active;
          const col = on ? C.accent : seen ? C.text : C.dim;
          return (
            <g key={n}>
              <circle cx={x} cy={y} r={on ? 9 : 6} fill={col} />
              <line x1={x} y1={y} x2={labelX - 20} y2={y} stroke={col} strokeWidth={on ? 3 : 2} strokeDasharray={seen ? undefined : "6 6"} />
              <text x={labelX} y={y + 12} fontFamily={sans} fontSize={on ? 40 : 32} fontWeight={on ? 800 : 600} fill={col}>
                {n}
              </text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

export const Table: React.FC<{ spec: SceneSpec; t: Timing }> = ({ spec }) => {
  const f = useCurrentFrame();
  const tbl = TABLES[spec.table!];
  return (
    <AbsoluteFill style={{ padding: "110px 90px 0 90px" }}>
      <div style={{ fontFamily: sans, fontSize: 54, fontWeight: 800, color: C.text, marginBottom: 26 }}>{spec.heading}</div>
      <div style={{ display: "grid", gridTemplateColumns: tbl.columns, gap: "0 0", fontFamily: sans }}>
        {tbl.head.map((h) => (
          <div key={h} style={{ fontFamily: mono, fontSize: 19, letterSpacing: 2, color: C.muted, padding: "8px 16px", borderBottom: `1px solid ${C.border}` }}>
            {h.toUpperCase()}
          </div>
        ))}
        {tbl.rows.map((r, i) => {
          const o = interpolate(f, [8 + i * 5, 20 + i * 5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return r.map((c, j) => (
            <div
              key={`${i}-${j}`}
              style={{
                opacity: o,
                transform: `translateY(${(1 - o) * 12}px)`,
                fontSize: tbl.size ?? 25,
                padding: "9px 16px",
                color: j === 0 ? C.text : j === 1 && tbl.countCol ? C.accent : C.muted,
                fontWeight: j === 0 ? 600 : j === 1 && tbl.countCol ? 700 : 400,
                fontFamily: j === 1 && tbl.countCol ? mono : sans,
                borderBottom: `1px solid #1a1d27`,
                lineHeight: 1.25,
              }}
            >
              {c}
            </div>
          ));
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Tools: React.FC<{ spec: SceneSpec; t: Timing }> = ({ spec }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ padding: "110px 90px 0 90px" }}>
      <div style={{ fontFamily: sans, fontSize: 54, fontWeight: 800, color: C.text, marginBottom: 30 }}>{spec.heading}</div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 18 }}>
        {TOOLS.map(([name, detail], i) => {
          const o = interpolate(f, [6 + i * 4, 18 + i * 4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div
              key={name}
              style={{
                opacity: o,
                transform: `scale(${0.94 + 0.06 * o})`,
                background: C.panel,
                border: `1px solid ${C.border}`,
                borderRadius: 16,
                padding: "20px 22px",
                minHeight: 112,
              }}
            >
              <div style={{ fontFamily: sans, fontSize: 27, fontWeight: 700, color: C.text }}>{name}</div>
              <div style={{ fontFamily: sans, fontSize: 21, color: C.muted, marginTop: 6, lineHeight: 1.3 }}>{detail}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Timeline: React.FC<{ spec: SceneSpec; t: Timing }> = ({ spec, t }) => {
  const f = useCurrentFrame();
  const active = activeStep(t, f);
  const steps = spec.steps ?? [];
  const x0 = 150, x1 = 1770, y = 520;
  const step = (x1 - x0) / (steps.length - 1);
  const fill = active < 0 ? 0 : active / (steps.length - 1);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 90, top: 110, fontFamily: sans, fontSize: 54, fontWeight: 800, color: C.text }}>
        {spec.heading}
      </div>
      <div style={{ position: "absolute", left: 90, top: 190, fontFamily: sans, fontSize: 28, color: C.muted, width: 1300 }}>
        The plate waits for the OLED modules, the case for the sockets, their pins and the OLED modules.
        Soldering needs neither.
      </div>
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0 }}>
        <line x1={x0} y1={y} x2={x1} y2={y} stroke={C.border} strokeWidth={6} strokeLinecap="round" />
        <line x1={x0} y1={y} x2={x0 + (x1 - x0) * fill} y2={y} stroke={C.accent} strokeWidth={6} strokeLinecap="round" />
        {steps.map((s, i) => {
          const x = x0 + i * step;
          const on = i === active, seen = i <= active;
          const up = i % 2 === 0;
          return (
            <g key={s}>
              <circle cx={x} cy={y} r={on ? 20 : 14} fill={seen ? C.accent : C.panel2} stroke={seen ? C.accent : C.border} strokeWidth={3} />
              <line x1={x} y1={up ? y - 30 : y + 30} x2={x} y2={up ? y - 70 : y + 70} stroke={seen ? C.accent : C.border} strokeWidth={2} />
              <foreignObject x={x - 130} y={up ? y - 250 : y + 80} width={260} height={180}>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: up ? "flex-end" : "flex-start",
                    height: 170,
                    textAlign: "center",
                    opacity: seen ? 1 : 0.4,
                  }}
                >
                  <div style={{ fontFamily: sans, fontSize: on ? 28 : 25, fontWeight: 800, color: on ? C.accent : C.text, lineHeight: 1.15 }}>{s}</div>
                  <div style={{ fontFamily: sans, fontSize: 21, color: C.muted, marginTop: 6, lineHeight: 1.25 }}>{spec.details?.[i]}</div>
                </div>
              </foreignObject>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

export const Outro: React.FC<{ spec: SceneSpec; t: Timing }> = () => {
  const a = useEnter(20);
  return (
    <AbsoluteFill>
      <Clip name="wave" />
      <Shade dir="0deg" strength={0.9} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 200, textAlign: "center", opacity: a }}>
        <div style={{ fontFamily: sans, fontSize: 120, fontWeight: 800, color: C.text, letterSpacing: -3 }}>Keygen</div>
        <div style={{ fontFamily: mono, fontSize: 30, color: C.accent2, marginTop: 10 }}>github.com/milindmadhukar/keygen</div>
        <div style={{ fontFamily: sans, fontSize: 26, color: C.muted, marginTop: 14 }}>
          The full written guide is INSTRUCTIONS.md
        </div>
      </div>
    </AbsoluteFill>
  );
};
