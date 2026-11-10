import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C, mono, sans } from "../theme";
import { chapterCount, chapterOf, scenes, timing, Timing } from "../data";

/** The dark studio background behind every scene. */
export const Backdrop: React.FC = () => {
  const f = useCurrentFrame();
  const x = 50 + 12 * Math.sin(f / 400);
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(1400px 900px at ${x}% 35%, #171a24 0%, ${C.bg} 70%)`,
      }}
    >
      <AbsoluteFill
        style={{
          opacity: 0.35,
          backgroundImage:
            "linear-gradient(#1a1d27 1px, transparent 1px), linear-gradient(90deg, #1a1d27 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(1200px 700px at 50% 40%, black 0%, transparent 80%)",
        }}
      />
    </AbsoluteFill>
  );
};

/** Top bar: the guide's name, the chapter, and the progress through the whole video. */
export const TopBar: React.FC<{ id: string }> = ({ id }) => {
  const f = useCurrentFrame();
  const t = timing.scenes.find((s) => s.id === id)!;
  const ch = chapterOf(id);
  const progress = (t.start + f) / timing.frames;
  const marks = scenes
    .filter((s) => s.kind === "chapter")
    .map((s) => timing.scenes.find((x) => x.id === s.id)!.start / timing.frames);
  return (
    <>
      <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 5, background: "#1b1e28" }}>
        <div
          style={{
            width: `${progress * 100}%`,
            height: 5,
            background: `linear-gradient(90deg, ${C.accent}, ${C.accent2})`,
          }}
        />
        {marks.map((m, i) => (
          <div key={i} style={{ position: "absolute", left: `${m * 100}%`, top: 0, width: 3, height: 5, background: C.bg }} />
        ))}
      </div>
      <div
        style={{
          position: "absolute",
          left: 60,
          top: 34,
          right: 60,
          display: "flex",
          justifyContent: "space-between",
          fontFamily: mono,
          fontSize: 20,
          letterSpacing: 2,
          color: C.muted,
        }}
      >
        <span>
          <span style={{ color: C.text, fontWeight: 600 }}>KEYGEN</span>
          <span style={{ color: C.dim }}> / </span>BUILD GUIDE
        </span>
        {ch ? (
          <span>
            <span style={{ color: C.accent }}>{ch.number}</span>
            <span style={{ color: C.dim }}> / {String(chapterCount).padStart(2, "0")} </span>
            <span style={{ color: C.text }}>{ch.title?.toUpperCase()}</span>
          </span>
        ) : null}
      </div>
    </>
  );
};

/** The sentence being spoken, at the bottom. */
export const Captions: React.FC<{ t: Timing }> = ({ t }) => {
  const f = useCurrentFrame();
  const abs = t.start + f;
  const s = t.sentences.find((x) => abs >= x.start - 2 && abs <= x.end + 8);
  if (!s) return null;
  const a = interpolate(abs, [s.start - 2, s.start + 4, s.end + 2, s.end + 8], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 46,
        display: "flex",
        justifyContent: "center",
        opacity: a,
      }}
    >
      <div
        style={{
          maxWidth: 1560,
          padding: "14px 28px",
          borderRadius: 14,
          background: "rgba(8,9,12,0.78)",
          border: `1px solid ${C.border}`,
          color: C.text,
          fontFamily: sans,
          fontSize: 33,
          lineHeight: 1.32,
          fontWeight: 500,
          textAlign: "center",
        }}
      >
        {s.text}
      </div>
    </div>
  );
};

/** Fade a scene in and out at its edges. */
export const SceneFade: React.FC<{ frames: number; children: React.ReactNode; edge?: number }> = ({
  frames,
  children,
  edge = 9,
}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, edge, frames - edge, frames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};
