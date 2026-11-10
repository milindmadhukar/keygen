import React from "react";
import { AbsoluteFill, Audio, Composition, Sequence, staticFile } from "remotion";
import { scenes, timing, timingOf, SceneSpec, Timing } from "./data";
import { Backdrop, Captions, SceneFade, TopBar } from "./components/Chrome";
import { Steps } from "./scenes/Steps";
import { Chapter, Explode, Outro, Table, Timeline, Title, Tools } from "./scenes/Other";
import { FPS, H, W } from "./theme";

const KIND: Record<string, React.FC<{ spec: SceneSpec; t: Timing }>> = {
  title: Title,
  chapter: Chapter,
  explode: Explode,
  steps: Steps,
  table: Table,
  tools: Tools,
  timeline: Timeline,
  outro: Outro,
};

const NO_CHROME = new Set(["title", "chapter", "outro"]);

const Scene: React.FC<{ spec: SceneSpec; t: Timing }> = ({ spec, t }) => {
  const Body = KIND[spec.kind];
  return (
    <SceneFade frames={t.frames}>
      <Body spec={spec} t={t} />
      {NO_CHROME.has(spec.kind) ? null : <TopBar id={spec.id} />}
      <Captions t={t} />
    </SceneFade>
  );
};

export const BuildGuide: React.FC = () => (
  <AbsoluteFill style={{ background: "#0a0b0f" }}>
    <Backdrop />
    {scenes.map((spec) => {
      const t = timingOf(spec.id);
      return (
        <Sequence key={spec.id} from={t.start} durationInFrames={t.frames} name={spec.id}>
          <Scene spec={spec} t={t} />
        </Sequence>
      );
    })}
    <Audio src={staticFile("vo/voice.wav")} />
    <Audio src={staticFile("music/bed.wav")} volume={0.16} />
  </AbsoluteFill>
);

export const Root: React.FC = () => (
  <Composition id="BuildGuide" component={BuildGuide} durationInFrames={timing.frames} fps={FPS} width={W} height={H} />
);
