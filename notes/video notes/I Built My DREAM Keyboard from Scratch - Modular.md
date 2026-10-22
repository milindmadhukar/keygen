---
created: 2026-06-16
name: I Built My DREAM Keyboard from Scratch - Modular
source: https://www.youtube.com/watch?v=KwFWBdfZKnI
type: video-note
---

A start-to-finish "end game" custom split keyboard build by Modern Hobbyist, designing **Project Mode** entirely from scratch rather than from a kit: requirements → layout in Keyboard Layout Editor → PCB design in KiCad → fabrication at PCBWay → hot-air SMD soldering → QMK firmware → Fusion 360 case → 3D printing and assembly. The board is a low-profile columnar-staggered split with Kailh Choc Brown switches, per-key RGB, 2.2 in per-side LCDs, a large thumb cluster, dedicated arrow keys tucked under the right hand, and a **magnetically detachable numpad/macro module** (the "modular" hook). Most valuable for this project: a candid postmortem of the PCB/firmware **mistakes** he made and the concrete **tools** he used at each stage.

## Key Takeaways

**From-scratch build workflow (the order he followed)**
- Start by writing down hard **requirements vs. nice-to-haves** before touching any design tool. His must-haves: split, low profile, QWERTY (to avoid learning two layouts vs. his laptop), dedicated arrow keys, numpad, and **no stabilizers** (so every key stays ≤ 2u).
- Name the project first, then lay out keys in **Keyboard Layout Editor (KLE)**: build the first row, then offset each column by **0.25u** to get the columnar (column) stagger. Key positions in KLE aren't final since the keymap is set later in firmware.
- Resolve uncertain physical positions (thumb cluster, arrow keys) by **3D printing test plates** — he printed ~20 — instead of guessing. This is how he settled on more than two thumb keys per side and on tucking the arrow keys into the natural "cave" under a properly-postured right hand.
- Electronics in **KiCad**: drop switch footprints, import the KLE layout via the **KB Placer** plugin, route switches/LEDs/LCD/USB to the MCU, then repeat for the second half. Export the PCB's 3D model from KiCad into Fusion so the case lines up exactly.
- Firmware in **QMK**, then case in **Fusion 360**, foam inserts laser-cut, heat-set inserts melted in, bolt together, clip in switches and keycaps.

**Modular design approach**
- The numpad became a **separate third PCB** that attaches via **5-pin magnetic pogo connectors** (idea sparked by a MagSafe charger handling 18.5 V — a 5 V keyboard-matrix signal is trivial by comparison).
- Because it's pogo-pin modular, the numpad snaps onto **either** the left or right half, and he can print a second module to run numpad + 20 extra macro keys simultaneously.
- Splitting the numpad off also solved a hard constraint: the combined right half wouldn't fit his **200 × 200 mm** 3D-printer bed.

## Mistakes to Avoid

- **Forgot the 5.1 kΩ resistors on the split USB data lines**, so the two halves couldn't communicate. He bodged tiny 5.1 kΩ resistors across the USB connector pins as a hardware fix — design these in from the start. (He also calls this out again in the postmortem as a fix that *required* hardware, not firmware.)
- **Poor MCU pin selection for the LEDs and LCD** — "not all pins are created equal"; some don't support the functions needed. He was lucky to remap them in firmware (with community help) instead of respinning the boards. Check pin capabilities/peripheral mapping before routing.
- **Chose an entry-level MCU with too little RAM/flash** to save money — not enough to drive LCD animations. He had to disable beefier QMK features and shrink the LCD painting-module buffer just to compile. Spec the MCU for the LCD/RGB workload up front.
- **No handedness auto-detect pin** — without a pin to detect left/right, he now has to flash **two different firmwares** every time he updates. Add a handedness pin (or use EEPROM handedness) in the design.
- **Jumped into hot-air soldering with no practice** — watched a couple of videos and improvised. Pro tip from him: practice on a non-critical board / start with less critical components before touching the boards you're emotionally attached to.
- General: he underestimated firmware effort — being a software engineer didn't make QMK on a *split + buggy PCB* easy. Expect the split + custom-PCB combination to be the hard part.

## Tools Used

- **Keyboard Layout Editor (KLE)** — initial physical layout / column stagger.
- **KiCad** — schematic + PCB design for both halves and the numpad; also exports the PCB 3D model.
- **KB Placer** (KiCad plugin) — imports the KLE layout into KiCad.
- **ai03 Plate Generator** (the "I/O plate generator") — converts the KLE layout into a switch plate.
- **Fusion 360** — case modeling, switch-cutout plate, USB/pogo cutouts, standoffs, foam-insert design.
- **QMK** — firmware (chosen mainly for its large community).
- **PCBWay** — PCB fabrication (video sponsor); noted for assembly, flex/rigid-flex, CNC, and 3D-printing services too.
- **Hot-air soldering / rework station** + solder paste, tweezers, **IPA (isopropyl alcohol)** for cleanup.
- **3D printer** (200 × 200 mm bed) — test plates and final case; **laser cutter** for foam inserts.
- **Heat-set inserts** + bolts for assembly; scuff/rubber feet.
- **5-pin magnetic pogo connectors** (sourced from AliExpress) for the modular numpad.
- **Keyboard Italia Discord** and the **QMK Discord** — communities that helped debug PCB/firmware issues.

## Notable Timestamps

- **00:00** — Premise: design the perfect keyboard (layout, switches, keycaps, firmware) from scratch.
- **00:30** — Inspiration: ZSA Voyager and the Cantor/"Gen Rev2" split influenced the design.
- **01:03** — Requirements: split, low profile, QWERTY, arrow keys, numpad, no stabilizers (keys ≤ 2u).
- **01:53** — Layout in KLE; 0.25u column offset for the columnar stagger.
- **02:43** — Thumb-cluster experimentation via ~20 printed test plates.
- **03:08** — Arrow keys tucked under the right hand; verified with a test plate.
- **03:57** — Electronics: KiCad, KB Placer import, routing switches/LEDs/LCD/USB to MCU.
- **04:38** — Found the Keyboard Italia Discord community for help.
- **05:00** — Numpad journey: print-bed limit → magnetic pogo connectors → separate third PCB.
- **05:53** — PCBs sent to PCBWay (sponsor segment).
- **06:53** — First-time hot-air soldering; practice-first pro tip; IPA cleanup.
- **07:50** — QMK firmware chosen; harder than expected on a split.
- **08:16** — Mistake 1: missing 5.1 kΩ resistors on split USB lines (+ resistor bodge fix).
- **08:35** — Mistake 2: bad MCU pin choices for LEDs/LCD, remapped in firmware.
- **09:00** — Mistake 3: underpowered MCU (RAM/flash), disabled QMK features / shrank LCD buffer.
- **09:41** — Case in Fusion 360; KiCad 3D export; ai03 plate generator; foam inserts.
- **10:33** — Final assembly: heat-set inserts, foam, bolts, switches, keycaps.
- **10:49** — Finished "Project Mode" feature tour (LCD shows keymap/layer/RGB/caps).
- **11:18** — Modular numpad demo (left/right swap, second module option).
- **11:36** — Postmortem: likes (thumb clusters, LCDs, arrow keys) and dislikes (thumb-key reach, pinky-heavy, miskeys, MCU, missing handedness pin).

## Checked against Keygen (2026-10-22)

- **Pull-ups on the split link:** Keygen's halves talk over Bluetooth, so there is no wired link to pull up. The one shared bus per half is the OLED's I2C: the module has its own pull-ups, and the firmware turns on the controller's internal ones too.
- **Pin choice:** `tools/check_datasheets.py` checks every controller pin against the nRF52840 datasheet: LED data on P0.06 (SPIM3, 4 MHz), I2C on the full-speed P0.17 / P0.20, the matrix on the low-frequency pins, the encoder on the NFC pins with `nfct-pins-as-gpios`. SPIM3 and TWIM0 are separate peripherals, and the nice!nano's UART on P0.06 / P0.08 stays disabled. One firmware bug turned up and is fixed: the I2C (TWIM) driver's 16-byte merge buffer would have failed every SSD1306 frame write and left both OLEDs blank; it is now 1025 bytes.
- **MCU size:** the nRF52840 has 256 KB RAM and 1 MB flash. The left half's build, with display, RGB and ZMK Studio, uses 49 % of flash and 33 % of RAM.
- **Handedness:** ZMK builds each half separately by design (`keygen_left`, `keygen_right`). Keymap changes need only the left half reflashed, and ZMK Studio remaps without flashing.
- **Soldering practice:** Keygen is hand-soldered with an iron (1206, SOT-23, SK6812MINI-E). Practise on one of the spare boards from the order of 5 and test each LED column as you go ([[10 - assembly & build guide]]).
- **Thumb position:** print `docs/plate-print.pdf` at 1:1 and rest your hands on it before ordering, to check the thumb keys sit where the thumbs rest.
- **Print bed:** each case part is 177.8 × 143.1 mm.

## Relevance to Keygen build

- **Full from-scratch pipeline:** This is the clearest end-to-end map of the *design-it-yourself* path (KLE → KiCad → fab → firmware → Fusion case) rather than the kit-assembly path of the Corne video. Directly informs the workflow ordering for [[10 - assembly & build guide]] and [[05 - pcb design]].
- **PCB mistakes are a pre-flight checklist:** The split-USB **5.1 kΩ data-line resistors**, **MCU pin/peripheral suitability** for LEDs+LCD, **MCU RAM/flash sizing** for LCD/RGB animations, and a **handedness-detect pin** are four concrete things to verify before sending a Keygen PCB to fab — feeds [[05 - pcb design]] and component/MCU planning in [[08 - electronics & components]].
- **Thumb cluster:** He explicitly chose *more than two thumb keys per side* and validated geometry with printed test plates — but his own postmortem says the thumb keys ended up slightly too far outboard of where thumbs rest. For the Keygen target (Kinesis Advantage-style scooped block), the actionable lesson is the **print-test-plates-before-committing** method, and his miss is a caution to dial thumb-key position to natural thumb rest.
- **Modular approach:** The magnetic-pogo-connector module is a reusable pattern if Keygen ever wants a detachable numpad/macro pad. Also note the **print-bed size constraint** drove the modular split — relevant to case planning.
- **Tooling overlap:** KiCad + KB Placer + ai03 plate generator + Fusion 360 + QMK is a directly adoptable toolchain; the KiCad→Fusion 3D-model export trick guarantees case/PCB fit — useful for [[05 - pcb design]] and case design.
- **Switches/profile:** Low-profile Kailh Choc + no-stabilizer ≤2u constraint is one design point for [[01 - overview]] to weigh against a normal-profile MX build.

## Related

- [[10 - assembly & build guide]]
- [[08 - electronics & components]]
- [[05 - pcb design]]
- [[01 - overview]]
- [[11 - learning resources & references]]
