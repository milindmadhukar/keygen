import React from "react";
import { AbsoluteFill, Freeze, Img, interpolate, OffthreadVideo, staticFile, useCurrentFrame } from "remotion";
import { clips } from "../data";
import { C, mono } from "../theme";
import { Diagram } from "./Diagrams";

/** A rendered Blender clip; it holds its last frame once it ends. */
export const Clip: React.FC<{ name: string; fit?: "cover" | "contain"; startFrom?: number }> = ({
  name,
  fit = "cover",
  startFrom = 0,
}) => {
  const f = useCurrentFrame();
  const meta = clips[name];
  if (!meta) {
    return (
      <AbsoluteFill
        style={{ background: C.panel2, alignItems: "center", justifyContent: "center", color: C.dim, fontFamily: mono, fontSize: 28 }}
      >
        clip {name} not rendered yet
      </AbsoluteFill>
    );
  }
  const video = (
    <OffthreadVideo
      src={staticFile(`clips/${name}.mp4`)}
      startFrom={startFrom}
      muted
      style={{ width: "100%", height: "100%", objectFit: fit }}
    />
  );
  const last = meta.frames - 1 - startFrom;
  return f >= last ? <Freeze frame={last}>{video}</Freeze> : video;
};

const light = (file: string) => file.startsWith("assembly-") || file.endsWith(".svg") || file.startsWith("encoder-");

/** A picture from assets/, slowly pushed in. Line drawings sit on a white card. */
export const Picture: React.FC<{ file: string; frames: number; w: number; h: number }> = ({ file, frames, w, h }) => {
  const f = useCurrentFrame();
  const s = interpolate(f, [0, Math.max(frames, 1)], [1.0, 1.05], { extrapolateRight: "clamp" });
  const card = light(file);
  return (
    <AbsoluteFill style={{ background: card ? "#f7f8fb" : "transparent", alignItems: "center", justifyContent: "center" }}>
      <Img
        src={staticFile(`assets/${file}`)}
        style={{
          maxWidth: w - (card ? 70 : 20),
          maxHeight: h - (card ? 70 : 20),
          objectFit: "contain",
          transform: `scale(${s})`,
        }}
      />
    </AbsoluteFill>
  );
};

/** Any visual named in scenes.json: clip:<name>, image:<file>, svg:<file>, diagram:<name>. */
export const Visual: React.FC<{ spec: string; frames: number; w: number; h: number }> = ({ spec, frames, w, h }) => {
  const [kind, name] = spec.split(":");
  if (kind === "clip") return <Clip name={name} />;
  if (kind === "image" || kind === "svg") return <Picture file={name} frames={frames} w={w} h={h} />;
  if (kind === "diagram") return <Diagram name={name} w={w} h={h} />;
  return null;
};
