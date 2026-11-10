import React from "react";
import { AbsoluteFill, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { activeStep, sentenceStart, SceneSpec, Timing } from "../data";
import { C, mono, PANEL, sans, SIDE } from "../theme";
import { Visual } from "../components/Media";

/** Segments of the scene: which visual shows from which frame, merging repeats so a clip keeps playing. */
export const segments = (spec: SceneSpec, t: Timing) => {
  const vis = spec.visuals ?? (spec.visual ? [spec.visual] : []);
  const out: { spec: string; from: number }[] = [];
  const push = (v: string, from: number) => {
    if (!out.length || out[out.length - 1].spec !== v) out.push({ spec: v, from });
  };
  push(vis[0], 0);
  for (const s of t.sentences) {
    if (s.step === null || s.step === undefined || s.step < 0) continue;
    push(vis[Math.min(s.step, vis.length - 1)], Math.max(0, s.start - t.start - 6));
  }
  return out.map((s, i) => ({ ...s, to: i + 1 < out.length ? out[i + 1].from : t.frames }));
};

const XFADE = 12;

export const VisualStack: React.FC<{ spec: SceneSpec; t: Timing; box: { w: number; h: number } }> = ({ spec, t, box }) => {
  const segs = segments(spec, t);
  return (
    <>
      {segs.map((s, i) => (
        <Sequence key={i} from={s.from} durationInFrames={s.to - s.from + (i + 1 < segs.length ? XFADE : 0)} layout="none">
          <Fader first={i === 0}>
            <Visual spec={s.spec} frames={s.to - s.from} w={box.w} h={box.h} />
          </Fader>
        </Sequence>
      ))}
    </>
  );
};

const Fader: React.FC<{ first: boolean; children: React.ReactNode }> = ({ first, children }) => {
  const f = useCurrentFrame();
  const o = first ? 1 : interpolate(f, [0, XFADE], [0, 1], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

export const Callout: React.FC<{ kind: "warning" | "note"; text: string; from: number }> = ({ kind, text, from }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (f < from) return null;
  const s = spring({ frame: f - from, fps, config: { damping: 18 } });
  const col = kind === "warning" ? C.warn : C.accent2;
  return (
    <div
      style={{
        marginTop: 26,
        transform: `translateY(${(1 - s) * 30}px)`,
        opacity: s,
        borderLeft: `6px solid ${col}`,
        background: kind === "warning" ? "rgba(251,191,36,0.10)" : "rgba(103,232,249,0.08)",
        borderRadius: 10,
        padding: "16px 20px",
      }}
    >
      <div style={{ fontFamily: mono, fontSize: 18, letterSpacing: 2, color: col, fontWeight: 600, marginBottom: 6 }}>
        {kind === "warning" ? "WARNING" : "NOTE"}
      </div>
      <div style={{ fontFamily: sans, fontSize: 25, lineHeight: 1.3, color: C.text }}>{text}</div>
    </div>
  );
};

export const StepList: React.FC<{ steps: string[]; active: number; size?: number }> = ({ steps, active, size = 28 }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
    {steps.map((s, i) => {
      const state = i < active ? "done" : i === active ? "now" : "next";
      return (
        <div
          key={i}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 18,
            padding: "14px 18px",
            borderRadius: 12,
            background: state === "now" ? "rgba(167,139,250,0.14)" : "transparent",
            border: `1px solid ${state === "now" ? "rgba(167,139,250,0.55)" : "transparent"}`,
            transition: "none",
          }}
        >
          <div
            style={{
              flex: "0 0 44px",
              height: 44,
              borderRadius: 22,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: mono,
              fontWeight: 600,
              fontSize: 21,
              background: state === "now" ? C.accent : state === "done" ? "#2a2440" : C.panel2,
              color: state === "now" ? "#140d26" : state === "done" ? C.accent : C.muted,
              border: `1px solid ${state === "next" ? C.border : "transparent"}`,
            }}
          >
            {state === "done" ? "✓" : i + 1}
          </div>
          <div
            style={{
              fontFamily: sans,
              fontSize: size,
              fontWeight: state === "now" ? 700 : 500,
              color: state === "next" ? C.muted : C.text,
              lineHeight: 1.22,
            }}
          >
            {s}
          </div>
        </div>
      );
    })}
  </div>
);

export const Steps: React.FC<{ spec: SceneSpec; t: Timing }> = ({ spec, t }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const active = activeStep(t, f);
  const enter = spring({ frame: f, fps, config: { damping: 20 } });
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: PANEL.x,
          top: PANEL.y,
          width: PANEL.w,
          height: PANEL.h,
          borderRadius: 22,
          overflow: "hidden",
          background: C.panel,
          border: `1px solid ${C.border}`,
          boxShadow: "0 30px 80px rgba(0,0,0,0.5)",
          transform: `translateX(${(1 - enter) * -40}px)`,
          opacity: enter,
        }}
      >
        <VisualStack spec={spec} t={t} box={PANEL} />
        {spec.side ? (
          <div
            style={{
              position: "absolute",
              left: 22,
              top: 22,
              fontFamily: mono,
              fontSize: 19,
              letterSpacing: 2,
              fontWeight: 600,
              padding: "8px 14px",
              borderRadius: 8,
              color: "#140d26",
              background: spec.side === "back" ? C.accent2 : C.accent,
            }}
          >
            {spec.side === "back" ? "BACK OF THE PCB" : "FRONT"}
          </div>
        ) : null}
      </div>
      <div
        style={{
          position: "absolute",
          left: SIDE.x,
          top: SIDE.y + 6,
          width: SIDE.w,
          opacity: enter,
          transform: `translateX(${(1 - enter) * 40}px)`,
        }}
      >
        <div style={{ fontFamily: sans, fontSize: 50, fontWeight: 800, color: C.text, lineHeight: 1.08, marginBottom: 30 }}>
          {spec.heading}
        </div>
        {spec.steps ? <StepList steps={spec.steps} active={active} /> : null}
        {spec.warning ? <Callout kind="warning" text={spec.warning.text} from={sentenceStart(t, spec.warning.at) - 4} /> : null}
        {spec.note ? <Callout kind="note" text={spec.note.text} from={sentenceStart(t, spec.note.at) - 4} /> : null}
      </div>
    </AbsoluteFill>
  );
};
