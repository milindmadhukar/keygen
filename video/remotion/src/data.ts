import script from "../../script/scenes.json";
import timings from "./timings.json";
import clipsJson from "./clips.json";

export type Sentence = { text: string; step: number | null; start: number; end: number };
export type Timing = { id: string; start: number; frames: number; sentences: Sentence[] };
export type Callout = { at: number; text: string };
export type SceneSpec = {
  id: string;
  kind: string;
  visual?: string;
  visuals?: string[];
  title?: string;
  subtitle?: string;
  number?: string;
  heading?: string;
  steps?: string[];
  details?: string[];
  side?: string;
  table?: string;
  warning?: Callout;
  note?: Callout;
  say?: (string | [string, number])[];
};
export type ClipMeta = { frames: number; fps: number; anchors?: Record<string, [number, number]> };

export const scenes: SceneSpec[] = (script as any).scenes;
export const timing: { fps: number; frames: number; scenes: Timing[] } = timings as any;
export const clips: Record<string, ClipMeta> = clipsJson as any;

export const timingOf = (id: string) => timing.scenes.find((t) => t.id === id)!;

/** Chapter (number, title) each scene belongs to. */
export const chapterOf = (id: string) => {
  let ch: SceneSpec | null = null;
  for (const s of scenes) {
    if (s.kind === "chapter") ch = s;
    if (s.id === id) return ch;
  }
  return null;
};
export const chapterCount = scenes.filter((s) => s.kind === "chapter").length;

/** The step (index) active at a scene-local frame: the last sentence started that carries one. */
export const activeStep = (t: Timing, frame: number) => {
  let step = -1;
  for (const s of t.sentences) {
    if (s.start - t.start > frame + 4) break;
    if (s.step !== null && s.step !== undefined) step = s.step;
  }
  return step;
};

/** Index of the sentence a callout appears with, as a scene-local frame. */
export const sentenceStart = (t: Timing, i: number) =>
  t.sentences[Math.min(i, t.sentences.length - 1)].start - t.start;
