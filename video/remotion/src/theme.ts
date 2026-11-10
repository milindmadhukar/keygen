import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";

export const sans = loadInter("normal", { weights: ["400", "500", "600", "700", "800"], subsets: ["latin"] }).fontFamily;
export const mono = loadMono("normal", { weights: ["400", "600"], subsets: ["latin"] }).fontFamily;

export const C = {
  bg: "#0a0b0f",
  panel: "#12141b",
  panel2: "#181b24",
  border: "#262a37",
  text: "#eceef4",
  muted: "#8a90a2",
  dim: "#4b5163",
  accent: "#a78bfa",
  accent2: "#67e8f9",
  warn: "#fbbf24",
  danger: "#f87171",
  ok: "#4ade80",
  copper: "#d39b4a",
  pcb: "#15171c",
  mask: "#1d2027",
  silk: "#e9e9ef",
};

export const W = 1920;
export const H = 1080;
export const FPS = 30;

// the panel the steps scenes show their visual in
export const PANEL = { x: 60, y: 108, w: 1200, h: 780 };
export const SIDE = { x: 1310, y: 108, w: 550 };
