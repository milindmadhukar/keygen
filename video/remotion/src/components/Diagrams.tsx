import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";
import { C, mono, sans } from "../theme";

// Every diagram draws in a 1200 x 780 box (the steps panel) and animates on its own local frame.
const VB = "0 0 1200 780";

const ease = Easing.bezier(0.22, 1, 0.36, 1);
const k = (f: number, a: number, d = 18) =>
  interpolate(f, [a, a + d], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });

const T: React.FC<React.SVGProps<SVGTextElement> & { size?: number; weight?: number; m?: boolean }> = ({
  size = 26,
  weight = 500,
  m = false,
  children,
  ...p
}) => (
  <text fontFamily={m ? mono : sans} fontSize={size} fontWeight={weight} fill={C.text} {...p}>
    {children}
  </text>
);

const Svg: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <svg viewBox={VB} width="100%" height="100%" style={{ display: "block" }}>
    {children}
  </svg>
);

const Check: React.FC<{ x: number; y: number; o: number; ok?: boolean; r?: number }> = ({ x, y, o, ok = true, r = 26 }) => (
  <g opacity={o} transform={`translate(${x},${y})`}>
    <circle r={r} fill={ok ? C.ok : C.danger} />
    {ok ? (
      <path d={`M${-r * 0.45} 0 L${-r * 0.1} ${r * 0.35} L${r * 0.5} ${-r * 0.35}`} stroke="#08130b" strokeWidth={r * 0.22} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    ) : (
      <path d={`M${-r * 0.38} ${-r * 0.38} L${r * 0.38} ${r * 0.38} M${r * 0.38} ${-r * 0.38} L${-r * 0.38} ${r * 0.38}`} stroke="#1a0808" strokeWidth={r * 0.22} strokeLinecap="round" />
    )}
  </g>
);

const Dim: React.FC<{ x1: number; y1: number; x2: number; y2: number; label: string; o?: number; side?: number }> = ({
  x1, y1, x2, y2, label, o = 1, side = 1,
}) => {
  const vertical = x1 === x2;
  return (
    <g opacity={o} stroke={C.accent2} strokeWidth={2.5} fill="none">
      <line x1={x1} y1={y1} x2={x2} y2={y2} />
      {vertical ? (
        <>
          <line x1={x1 - 10} y1={y1} x2={x1 + 10} y2={y1} />
          <line x1={x2 - 10} y1={y2} x2={x2 + 10} y2={y2} />
        </>
      ) : (
        <>
          <line x1={x1} y1={y1 - 10} x2={x1} y2={y1 + 10} />
          <line x1={x2} y1={y2 - 10} x2={x2} y2={y2 + 10} />
        </>
      )}
      <T
        stroke="none"
        fill={C.accent2}
        m
        size={24}
        weight={600}
        x={vertical ? x1 + 18 * side : (x1 + x2) / 2}
        y={vertical ? (y1 + y2) / 2 + 8 : y1 - 16}
        textAnchor={vertical ? (side > 0 ? "start" : "end") : "middle"}
      >
        {label}
      </T>
    </g>
  );
};

// ---------------------------------------------------------------- the diagrams

const FitTest: React.FC = () => {
  const f = useCurrentFrame();
  const ruler = k(f, 30, 40);
  return (
    <Svg>
      <g transform="translate(330,60)" opacity={k(f, 0)}>
        <rect width={540} height={660} rx={6} fill="#f4f5f8" />
        <T x={30} y={50} fill="#334" size={20} m>keygen-plate-print.pdf</T>
        <path d="M70 130 h170 v-20 h60 v20 h60 v30 h60 v130 l-60 40 l-60 70 l-120 0 l-110 -60 z" fill="none" stroke="#556" strokeWidth={3} />
        {[0, 1, 2, 3, 4].map((r) =>
          [0, 1, 2, 3, 4, 5].map((c) => (
            <rect key={`${r}${c}`} x={82 + c * 52} y={150 + r * 40 - (c === 3 ? 18 : c === 2 ? 10 : 0)} width={40} height={32} rx={3} fill="none" stroke="#99a" strokeWidth={2} />
          )),
        )}
        <g transform="translate(60,520)">
          <line x1={0} y1={0} x2={420 * ruler} y2={0} stroke="#223" strokeWidth={4} />
          {Array.from({ length: 11 }).map((_, i) => (
            <line key={i} x1={i * 42} x2={i * 42} y1={0} y2={i % 5 === 0 ? 26 : 14} stroke="#223" strokeWidth={3} opacity={ruler >= i / 10 ? 1 : 0} />
          ))}
          <T x={210} y={64} textAnchor="middle" fill="#223" size={26} weight={700} m opacity={k(f, 70)}>100 mm</T>
        </g>
      </g>
      <g opacity={k(f, 90)}>
        <T x={920} y={360} size={30} weight={700}>Print at 100 %</T>
        <T x={920} y={400} size={24} fill={C.muted}>"actual size", on A4</T>
        <T x={920} y={470} size={24} fill={C.muted}>Ruler not 100 mm?</T>
        <T x={920} y={502} size={24} fill={C.muted}>Reprint.</T>
      </g>
      <Check x={870} y={590} o={k(f, 100)} />
    </Svg>
  );
};

const OledPins: React.FC = () => {
  const f = useCurrentFrame();
  const pins = ["GND", "VCC", "SCL", "SDA"];
  const mod = (x: number, labels: string[], ok: boolean, start: number) => (
    <g transform={`translate(${x},150)`} opacity={k(f, start)}>
      <rect width={380} height={390} rx={10} fill="#1d3b6e" stroke="#0e2141" strokeWidth={4} />
      <rect x={34} y={120} width={312} height={200} rx={4} fill="#06070a" />
      <rect x={60} y={150} width={260} height={130} fill="#0c1220" />
      {labels.map((p, i) => (
        <g key={p} transform={`translate(${95 + i * 64},40)`}>
          <circle r={14} fill={C.copper} />
          <circle r={6} fill="#1d3b6e" />
          <T y={52} textAnchor="middle" size={22} m weight={600} fill={k(f, start + 15 + i * 8) > 0.5 ? (ok ? C.text : (i < 2 ? C.danger : C.text)) : C.dim}>
            {p}
          </T>
        </g>
      ))}
      <Check x={190} y={480} o={k(f, start + 50)} ok={ok} r={30} />
    </g>
  );
  return (
    <Svg>
      {mod(150, pins, true, 0)}
      {mod(670, ["VCC", "GND", "SCL", "SDA"], false, 40)}
      <T x={340} y={110} textAnchor="middle" size={26} weight={700} opacity={k(f, 0)}>Use</T>
      <T x={860} y={110} textAnchor="middle" size={26} weight={700} fill={C.danger} opacity={k(f, 40)}>GND and VCC swapped</T>
    </Svg>
  );
};

const Battery: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <Svg>
      <g opacity={k(f, 0)}>
        <rect x={140} y={200} width={620} height={340} rx={26} fill="#c9ccd4" stroke="#9aa0ad" strokeWidth={4} />
        <T x={420} y={370} textAnchor="middle" fill="#334" size={34} weight={700}>LiPo KP-355085</T>
        <T x={420} y={410} textAnchor="middle" fill="#556" size={24} m>3.5 × 50 × 85 mm</T>
      </g>
      <g opacity={k(f, 20)}>
        <rect x={700} y={290} width={110} height={160} rx={6} fill="#1f6b4e" stroke="#0d3a28" strokeWidth={3} />
        <T x={755} y={480} textAnchor="middle" size={20} fill={C.muted}>protection</T>
        <T x={755} y={505} textAnchor="middle" size={20} fill={C.muted}>board</T>
      </g>
      <g opacity={k(f, 40)}>
        <path d="M810 340 C 880 340, 880 300, 960 300" stroke="#e33" strokeWidth={9} fill="none" />
        <path d="M810 400 C 880 400, 880 330, 960 330" stroke="#222" strokeWidth={9} fill="none" />
        <rect x={955} y={280} width={70} height={70} rx={6} fill="#eee8d8" stroke="#998" strokeWidth={3} />
        <T x={990} y={390} textAnchor="middle" size={22} fill={C.muted}>JST-PH</T>
      </g>
      <g opacity={k(f, 60)}>
        <T x={960} y={220} size={44} weight={800} fill={C.danger}>+</T>
        <T x={1010} y={220} size={24} fill={C.text}>red to the + pad</T>
      </g>
      <g opacity={k(f, 80)}>
        <T x={140} y={640} size={26} fill={C.muted}>Side-entry connector S2B-PH-K-S: its opening faces sideways.</T>
      </g>
    </Svg>
  );
};

const Foam: React.FC = () => {
  const f = useCurrentFrame();
  const tiles = [
    ["keygen-left-plate-foam.dxf", "2 mm EVA", "under the left plate", "#4f5563"],
    ["keygen-right-plate-foam.dxf", "2 mm EVA", "under the right plate", "#4f5563"],
    ["keygen-left-case-foam.dxf", "5 mm EVA", "left shell floor", "#3a3f4a"],
    ["keygen-right-case-foam.dxf", "5 mm EVA", "right shell floor", "#3a3f4a"],
  ];
  return (
    <Svg>
      {tiles.map(([file, mat, where, col], i) => {
        const x = 70 + (i % 2) * 545, y = 70 + Math.floor(i / 2) * 340;
        return (
          <g key={file} transform={`translate(${x},${y})`} opacity={k(f, i * 12)}>
            <rect width={515} height={310} rx={14} fill={C.panel2} stroke={C.border} strokeWidth={2} />
            <path d="M40 60 h250 v40 h100 v60 l-70 70 l-140 0 l-140 -50 z" fill={col} stroke="#6b7285" strokeWidth={2} />
            {[0, 1, 2, 3, 4].map((c) => (
              <rect key={c} x={60 + c * 48} y={86} width={30} height={30} rx={3} fill={C.panel2} />
            ))}
            <T x={30} y={262} size={20} m fill={C.muted}>{file}</T>
            <T x={30} y={292} size={24} weight={700}>{mat} <tspan fill={C.muted} fontWeight={400}>· {where}</tspan></T>
          </g>
        );
      })}
    </Svg>
  );
};

const Solder: React.FC = () => {
  const f = useCurrentFrame();
  const phase = Math.min(3, Math.floor(f / 45));
  const labels = ["Tin one pad", "Place it, reheat that pad", "Solder the other pads", "Touch up the first"];
  const iron = [
    [400, 420],
    [400, 420],
    [800, 420],
    [400, 420],
  ][phase];
  const lift = interpolate(f % 45, [0, 10, 35, 45], [60, 0, 0, 60], { extrapolateRight: "clamp" });
  return (
    <Svg>
      <rect x={200} y={460} width={800} height={60} fill="#1b1d23" />
      <rect x={300} y={444} width={200} height={16} fill={C.copper} />
      <rect x={700} y={444} width={200} height={16} fill={C.copper} />
      <ellipse cx={400} cy={444} rx={80} ry={phase >= 0 ? 16 : 0} fill="#c6c9d2" />
      {phase >= 1 && <rect x={380} y={380} width={440} height={64} rx={6} fill="#2a2d33" stroke="#555a66" strokeWidth={3} />}
      {phase >= 1 && <rect x={380} y={380} width={60} height={64} fill="#b9bcc6" />}
      {phase >= 1 && <rect x={760} y={380} width={60} height={64} fill="#b9bcc6" />}
      {phase >= 2 && <path d="M820 444 Q 860 400 900 444 Z" fill="#c6c9d2" />}
      {phase >= 3 && <path d="M300 444 Q 340 400 380 444 Z" fill="#c6c9d2" />}
      {phase === 1 && (
        <g>
          <path d="M600 160 L590 380 M640 160 L610 380" stroke="#9aa3b5" strokeWidth={10} strokeLinecap="round" />
          <T x={660} y={200} size={22} fill={C.muted}>tweezers</T>
        </g>
      )}
      <g transform={`translate(${iron[0] - 120},${iron[1] - 300 - lift}) rotate(-28)`}>
        <rect x={0} y={0} width={46} height={230} rx={10} fill="#3b3f4a" />
        <path d="M8 230 L23 300 L38 230 Z" fill="#c0c4cc" />
      </g>
      {labels.map((l, i) => (
        <g key={l} transform={`translate(${170 + (i % 2) * 480},${620 + Math.floor(i / 2) * 64})`} opacity={i <= phase ? 1 : 0.3}>
          <circle r={22} cx={22} cy={-8} fill={i === phase ? C.accent : C.panel2} stroke={C.border} />
          <T x={22} y={0} textAnchor="middle" size={22} weight={700} fill={i === phase ? "#140d26" : C.text}>{i + 1}</T>
          <T x={56} y={0} size={21}>{l}</T>
        </g>
      ))}
    </Svg>
  );
};

const SuperMini: React.FC = () => {
  const f = useCurrentFrame();
  const v = interpolate(f, [30, 70], [0, 3.3], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <Svg>
      <g transform="translate(150,110)" opacity={k(f, 0)}>
        <rect width={330} height={560} rx={14} fill="#1c2a66" stroke="#0b1438" strokeWidth={4} />
        <rect x={115} y={-20} width={100} height={60} rx={10} fill="#b8bcc6" />
        <T x={165} y={90} textAnchor="middle" size={20} m fill="#cdd">USB-C</T>
        {Array.from({ length: 12 }).map((_, i) => (
          <g key={i}>
            <circle cx={30} cy={120 + i * 36} r={11} fill={C.copper} />
            <circle cx={300} cy={120 + i * 36} r={11} fill={C.copper} />
          </g>
        ))}
        <rect x={110} y={230} width={110} height={110} fill="#0b0c10" />
        <T x={300} y={124 + 0 * 36} textAnchor="end" dx={-22} size={18} m fill={C.warn}>B+</T>
        <T x={300} y={124 + 3 * 36} textAnchor="end" dx={-22} size={18} m fill={C.accent2}>VCC</T>
        <T x={30} y={124 + 1 * 36} dx={22} size={18} m fill={C.muted}>GND</T>
        <g opacity={k(f, 90)}>
          <rect x={120} y={430} width={90} height={40} rx={4} fill="none" stroke={C.accent} strokeWidth={3} strokeDasharray="6 5" />
          <rect x={132} y={440} width={66} height={20} rx={8} fill="#c6c9d2" opacity={k(f, 110)} />
          <T x={165} y={500} textAnchor="middle" size={20} m fill={C.accent}>BOOST</T>
        </g>
      </g>
      <g transform="translate(640,170)" opacity={k(f, 15)}>
        <rect width={380} height={240} rx={22} fill="#2c2f37" stroke="#444955" strokeWidth={3} />
        <rect x={30} y={30} width={320} height={110} rx={8} fill="#a9b59a" />
        <T x={330} y={115} textAnchor="end" size={70} m weight={600} fill="#1d2416">{v.toFixed(2)}</T>
        <T x={190} y={200} textAnchor="middle" size={24} fill={C.muted}>VCC on USB</T>
      </g>
      <Check x={1080} y={250} o={k(f, 75)} />
      <g opacity={k(f, 110)}>
        <T x={640} y={500} size={26} weight={700}>Bridge BOOST</T>
        <T x={640} y={540} size={23} fill={C.muted}>the unfitted 0 Ω link on its back:</T>
        <T x={640} y={575} size={23} fill={C.muted}>charges at about 300 mA</T>
      </g>
    </Svg>
  );
};

const SocketStack: React.FC = () => {
  const f = useCurrentFrame();
  const layers = [
    { y: 560, h: 34, fill: "#1b1d23", label: "PCB, back up", s: 0 },
    { y: 480, h: 80, fill: "#2b2d33", label: "Socket strip  3.0 mm", s: 20 },
    { y: 430, h: 50, fill: "#3b3226", label: "Pin carrier  1.9 mm", s: 40 },
    { y: 400, h: 30, fill: "#1c2a66", label: "Controller, chip up", s: 60 },
  ];
  return (
    <Svg>
      {layers.map((l, i) => {
        const a = k(f, l.s, 22);
        const dy = (1 - a) * -120;
        return (
          <g key={i} opacity={a} transform={`translate(0,${dy})`}>
            <rect x={i === 0 ? 120 : i === 3 ? 230 : 270} y={l.y} width={i === 0 ? 700 : i === 3 ? 630 : 420} height={l.h} rx={4} fill={l.fill} stroke="#4a4f5c" strokeWidth={2} />
            {i === 3 && <rect x={420} y={370} width={120} height={30} fill="#0a0a0d" />}
            {i === 3 && <rect x={830} y={384} width={60} height={40} rx={8} fill="#b8bcc6" />}
            {i === 1 &&
              Array.from({ length: 8 }).map((_, j) => <rect key={j} x={300 + j * 50} y={490} width={12} height={110} fill="#c8a24a" />)}
            <T x={940} y={l.y + l.h / 2 + 9} size={24} weight={600}>{l.label}</T>
            <line x1={i === 0 ? 820 : i === 3 ? 900 : 690} y1={l.y + l.h / 2} x2={925} y2={l.y + l.h / 2} stroke={C.dim} strokeWidth={2} />
          </g>
        );
      })}
      <g opacity={k(f, 90)}>
        <line x1={820} y1={300} x2={820} y2={640} stroke={C.accent2} strokeWidth={2} strokeDasharray="8 6" />
        <T x={820} y={680} textAnchor="middle" size={22} fill={C.accent2}>board's top edge</T>
        <Dim x1={820} y1={340} x2={890} y2={340} label="USB-C 1 mm over" />
      </g>
    </Svg>
  );
};

const Flash: React.FC = () => {
  const f = useCurrentFrame();
  const press = (a: number) => interpolate(f, [a, a + 4, a + 8], [0, 12, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const p = press(50) + press(62);
  const fileX = interpolate(f, [110, 150], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  return (
    <Svg>
      <g opacity={k(f, 0)}>
        <rect x={100} y={260} width={300} height={200} rx={16} fill={C.panel2} stroke={C.border} strokeWidth={3} />
        <T x={250} y={320} textAnchor="middle" size={26} weight={700}>1. USB-C</T>
        <path d="M250 360 v60" stroke={C.accent2} strokeWidth={10} strokeLinecap="round" />
      </g>
      <g opacity={k(f, 30)}>
        <rect x={450} y={260} width={300} height={200} rx={16} fill={C.panel2} stroke={C.border} strokeWidth={3} />
        <T x={600} y={320} textAnchor="middle" size={26} weight={700}>2. Reset × 2</T>
        <rect x={560} y={360 + p} width={80} height={60 - p} rx={8} fill="#ddd" />
        <T x={600} y={448} textAnchor="middle" size={18} m fill={C.muted}>GENERATE</T>
      </g>
      <g opacity={k(f, 80)}>
        <rect x={800} y={230} width={320} height={260} rx={16} fill={C.panel2} stroke={C.accent} strokeWidth={3} />
        <T x={960} y={290} textAnchor="middle" size={26} weight={700}>3. NICENANO</T>
        <path d="M880 330 h160 v110 h-160 z" fill="#2a2e3b" stroke="#596079" strokeWidth={3} />
        <T x={960} y={395} textAnchor="middle" size={20} m fill={C.muted}>drive</T>
      </g>
      <g opacity={k(f, 100) * (1 - k(f, 150, 10))} transform={`translate(${interpolate(fileX, [0, 1], [600, 880])},${interpolate(fileX, [0, 1], [580, 370])})`}>
        <rect width={170} height={60} rx={8} fill={C.accent} />
        <T x={85} y={39} textAnchor="middle" size={18} m weight={600} fill="#140d26">keygen_left.uf2</T>
      </g>
      <Check x={960} y={560} o={k(f, 155)} />
      <T x={600} y={680} textAnchor="middle" size={24} fill={C.muted} opacity={k(f, 165)}>
        Won't pair? settings_reset to both halves, then the normal firmware.
      </T>
    </Svg>
  );
};

const Polarity: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <Svg>
      <g opacity={k(f, 0)}>
        <rect x={160} y={240} width={520} height={300} rx={10} fill="#16181e" stroke="#30343f" strokeWidth={3} />
        <T x={190} y={290} size={22} m fill={C.muted}>PCB · BT101</T>
        <rect x={430} y={340} width={150} height={110} rx={6} fill="#eee8d8" />
        <T x={460} y={330} size={36} weight={800} fill={C.danger}>+</T>
        <T x={540} y={330} size={36} weight={800} fill={C.muted}>−</T>
      </g>
      <g opacity={k(f, 25)}>
        <path d="M1000 360 C 800 360, 760 380, 470 380" stroke="#e33" strokeWidth={10} fill="none" />
        <path d="M1000 420 C 800 420, 760 410, 545 410" stroke="#222" strokeWidth={10} fill="none" />
        <T x={1010} y={368} size={24}>red</T>
        <T x={1010} y={428} size={24}>black</T>
      </g>
      <Check x={510} y={620} o={k(f, 55)} />
      <T x={560} y={630} size={26} opacity={k(f, 55)}>Red wire on +, checked with the meter</T>
    </Svg>
  );
};

const Meter: React.FC<{ value: number; unit: string; digits: number; lo?: number; hi?: number; caption: string; band: string }> = ({
  value, unit, digits, lo, hi, caption, band,
}) => {
  const f = useCurrentFrame();
  const v = interpolate(f, [20, 70], [0, value], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  return (
    <Svg>
      <g transform="translate(330,90)" opacity={k(f, 0)}>
        <rect width={540} height={600} rx={40} fill="#e3b400" />
        <rect x={30} y={30} width={480} height={540} rx={26} fill="#2a2c33" />
        <rect x={70} y={70} width={400} height={170} rx={10} fill="#a9b59a" />
        <T x={440} y={200} textAnchor="end" size={110} m weight={600} fill="#1d2416">{v.toFixed(digits)}</T>
        <T x={270} y={300} textAnchor="middle" size={34} m weight={700} fill="#eee">{unit}</T>
        <circle cx={270} cy={440} r={90} fill="#1b1c21" stroke="#555" strokeWidth={4} />
        <line x1={270} y1={440} x2={270} y2={360} stroke="#eee" strokeWidth={8} strokeLinecap="round" />
      </g>
      <g opacity={k(f, 75)}>
        <T x={600} y={740} textAnchor="middle" size={28} weight={700} fill={C.ok}>{band}</T>
      </g>
      <T x={600} y={60} textAnchor="middle" size={26} fill={C.muted} opacity={k(f, 5)}>{caption}</T>
    </Svg>
  );
};

const LedChain: React.FC = () => {
  const f = useCurrentFrame();
  const n = 8;
  const lit = Math.floor(interpolate(f, [10, 70], [0, n], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const broken = f > 110;
  return (
    <Svg>
      <T x={600} y={150} textAnchor="middle" size={26} fill={C.muted}>Data runs LED101 → LED102 → … in number order</T>
      {Array.from({ length: n }).map((_, i) => {
        const x = 130 + i * 135;
        const on = broken ? i < 3 : i < lit;
        const hue = 260 - i * 14;
        return (
          <g key={i}>
            {i < n - 1 && <line x1={x + 45} y1={380} x2={x + 90} y2={380} stroke={on && (!broken || i < 2) ? C.accent2 : C.dim} strokeWidth={5} />}
            <rect x={x - 45} y={335} width={90} height={90} rx={12} fill={on ? `hsl(${hue},90%,70%)` : "#22252e"} style={{ filter: on ? `drop-shadow(0 0 18px hsl(${hue},90%,65%))` : undefined }} />
            <T x={x} y={480} textAnchor="middle" size={20} m fill={C.muted}>LED{101 + i}</T>
            {broken && i === 3 && <Check x={x} y={260} o={k(f, 110)} ok={false} />}
          </g>
        );
      })}
      <T x={600} y={620} textAnchor="middle" size={28} weight={700} opacity={k(f, 120)} fill={C.warn}>
        One bad joint at LED104: every LED after it stays dark
      </T>
      <T x={600} y={665} textAnchor="middle" size={24} opacity={k(f, 135)} fill={C.muted}>
        Check the first dark LED, or the one before it
      </T>
    </Svg>
  );
};

const Encoder: React.FC = () => {
  const f = useCurrentFrame();
  const rows = [
    ["1", "A", "ENC_A"],
    ["2", "C", "GND"],
    ["3", "B", "ENC_B"],
    ["4", "S1", "COL6"],
    ["5", "S2", "K06"],
  ];
  const cols = ["#e4572e", "#222", "#29a3e0", "#f2c14e", "#7fb069"];
  return (
    <Svg>
      <g transform="translate(110,180)" opacity={k(f, 0)}>
        <rect width={110} height={420} rx={8} fill="#16181e" stroke="#30343f" strokeWidth={3} />
        <T x={55} y={-20} textAnchor="middle" size={24} weight={700}>J102</T>
        {rows.map((r, i) => (
          <g key={i}>
            {i === 0 ? <rect x={35} y={40 + i * 80} width={40} height={40} fill={C.copper} /> : <circle cx={55} cy={60 + i * 80} r={20} fill={C.copper} />}
            <T x={-20} y={68 + i * 80} textAnchor="end" size={24} m>{r[0]}</T>
          </g>
        ))}
      </g>
      {rows.map((r, i) => {
        const a = k(f, 20 + i * 12, 24);
        const y1 = 240 + i * 80;
        const y2 = 230 + i * 85;
        return (
          <g key={i}>
            <path d={`M190 ${y1} C 450 ${y1}, 500 ${y2}, ${190 + 520 * a} ${y2}`} stroke={cols[i]} strokeWidth={9} fill="none" strokeLinecap="round" />
            <g opacity={a}>
              <rect x={720} y={y2 - 28} width={80} height={56} rx={8} fill={C.panel2} stroke={C.border} strokeWidth={2} />
              <T x={760} y={y2 + 9} textAnchor="middle" size={24} weight={700}>{r[1]}</T>
              <T x={830} y={y2 + 9} size={22} m fill={C.muted}>{r[2]}</T>
            </g>
          </g>
        );
      })}
      <g opacity={k(f, 90)}>
        <Dim x1={260} y1={130} x2={700} y2={130} label="100 mm" />
        <T x={1000} y={300} size={24} weight={700}>Mark pin 1</T>
        <T x={1000} y={335} size={22} fill={C.muted}>the plug isn't keyed</T>
        <T x={1000} y={420} size={24} weight={700}>A ↔ B swapped</T>
        <T x={1000} y={455} size={22} fill={C.muted}>reverses the turn</T>
        <T x={1000} y={540} size={24} weight={700} fill={C.danger}>C, S1, S2 wrong</T>
        <T x={1000} y={575} size={22} fill={C.muted}>a dead encoder</T>
      </g>
    </Svg>
  );
};

const OledLead: React.FC = () => {
  const f = useCurrentFrame();
  const pins = ["GND", "VCC", "SCL", "SDA"];
  const cols = ["#222", "#e33", "#f2c14e", "#29a3e0"];
  return (
    <Svg>
      <g opacity={k(f, 0)} transform="translate(120,250)">
        <rect width={150} height={230} rx={8} fill="#222" stroke="#555" strokeWidth={3} />
        <T x={75} y={-20} textAnchor="middle" size={22} weight={700}>4-pin plug</T>
        {pins.map((p, i) => (
          <g key={p}>
            <rect x={45} y={20 + i * 52} width={60} height={40} rx={4} fill="#111" />
            <T x={-15} y={48 + i * 52} textAnchor="end" size={22} m>{p}</T>
          </g>
        ))}
        <circle cx={130} cy={40} r={9} fill="#fff" opacity={k(f, 95)} />
      </g>
      {pins.map((p, i) => {
        const a = k(f, 20 + i * 10, 26);
        const y = 290 + i * 52;
        return <line key={p} x1={270} y1={y} x2={270 + 400 * a} y2={y} stroke={cols[i]} strokeWidth={10} strokeLinecap="round" />;
      })}
      <g opacity={k(f, 60)} transform="translate(670,170)">
        <rect width={380} height={390} rx={10} fill="#1d3b6e" stroke="#0e2141" strokeWidth={4} />
        <rect x={34} y={120} width={312} height={200} rx={4} fill="#06070a" opacity={0.5} />
        {pins.map((p, i) => (
          <circle key={p} cx={30} cy={120 + i * 52} r={12} fill={C.copper} />
        ))}
        <T x={190} y={360} textAnchor="middle" size={20} fill="#cbd">soldered from the back</T>
      </g>
      <Dim x1={270} y1={200} x2={670} y2={200} label="45 mm" o={k(f, 70)} />
      <T x={120} y={650} size={24} fill={C.muted} opacity={k(f, 95)}>Superglue the four plug housings into one, and mark pin 1 (GND) with a paint pen.</T>
    </Svg>
  );
};

const Gap: React.FC = () => {
  const f = useCurrentFrame();
  const s = 70; // px per mm
  const base = 640; // PCB top
  const rows = [
    { mm0: 0, mm1: 0.5, fill: "#4b505b", label: "Poron switch pad  0.5", d: 20 },
    { mm0: 0.5, mm1: 1.5, fill: "none", label: "air  1.0", d: 35 },
    { mm0: 1.5, mm1: 3.5, fill: "#626a76", label: "EVA plate foam  2.0", d: 50 },
    { mm0: 3.5, mm1: 5.0, fill: "#acd6e5", label: "polycarbonate plate  1.5", d: 65 },
  ];
  return (
    <Svg>
      <rect x={80} y={base} width={820} height={1.6 * s} fill="#1b1d23" stroke="#3a3f4a" strokeWidth={2} opacity={k(f, 0)} />
      <T x={920} y={base + 60} size={24} weight={600} opacity={k(f, 0)}>PCB</T>
      {rows.map((r, i) => (
        <g key={i} opacity={k(f, r.d)}>
          {r.fill !== "none" ? (
            <rect x={i === 0 ? 300 : 80} y={base - r.mm1 * s} width={i === 0 ? 380 : 820} height={(r.mm1 - r.mm0) * s} fill={r.fill} opacity={i === 3 ? 0.7 : 1} />
          ) : (
            <rect x={80} y={base - r.mm1 * s} width={820} height={(r.mm1 - r.mm0) * s} fill="none" stroke={C.dim} strokeDasharray="6 6" />
          )}
          <T x={920} y={base - ((r.mm0 + r.mm1) / 2) * s + 9} size={24}>{r.label}</T>
        </g>
      ))}
      <g opacity={k(f, 80)}>
        <rect x={120} y={base - 0.5 * s} width={70} height={0.5 * s} fill="#c0c4cc" />
        <rect x={130} y={base - 3.5 * s} width={50} height={3.0 * s} fill="#d9a143" />
        <T x={155} y={base - 3.7 * s} textAnchor="middle" size={20} fill={C.muted}>shim + standoff</T>
      </g>
      <Dim x1={60} y1={base} x2={60} y2={base - 3.5 * s} label="3.5" side={-1} o={k(f, 95)} />
      <T x={500} y={110} textAnchor="middle" size={26} fill={C.muted} opacity={k(f, 100)}>
        The plate's top sits 5.0 mm above the PCB's
      </T>
    </Svg>
  );
};

export const Diagram: React.FC<{ name: string; w: number; h: number }> = ({ name }) => {
  switch (name) {
    case "fittest": return <FitTest />;
    case "oledpins": return <OledPins />;
    case "battery": return <Battery />;
    case "foam": return <Foam />;
    case "solder": return <Solder />;
    case "supermini": return <SuperMini />;
    case "socketstack": return <SocketStack />;
    case "flash": return <Flash />;
    case "polarity": return <Polarity />;
    case "meter-rail":
      return <Meter value={4.95} unit="V DC" digits={2} caption="LED rail at C101, LED test build" band="4.83 – 5.08 V" />;
    case "meter-charge":
      return <Meter value={300} unit="mA" digits={0} caption="In series with the battery, USB in" band="≈ 300 mA · an empty cell takes about ten hours" />;
    case "ledchain": return <LedChain />;
    case "encoder": return <Encoder />;
    case "oledlead": return <OledLead />;
    case "gap": return <Gap />;
    default: return null;
  }
};
