---
created: 2026-06-16
name: How Im Designing My Dream Keyboard - Dungeon Delver
source: https://www.youtube.com/watch?v=CZaAxaHlsBY
type: video-note
---

"How I'm Designing My Dream Keyboard" by Nick the Mimic documents the ground-up design of **The Dungeon Delver**, a modular split keyboard. After buying a $400 ZSA Moonlander and immediately wanting to change the function row, thumb keys, and macros, the creator (a mechanical engineer with no EE background) spent all of 2025 learning electrical engineering from scratch to build his own board: PCBs, firmware (QMK), and case included. The video is a design-process narrative through ~mark-10 switch-plate prototypes, two-plus PCB revisions, and a from-scratch redesign driven by cost. Two core principles dominate: **independence per side** (each half works alone — born from his past work building split keyboards for people with limb differences/prosthetics) and **modularity/upgradeability** (dockable open-source modules, a swappable control board for a future wireless kit).

## Key Takeaways

- **Design philosophy: concept before constraints.** He deliberately sketched the keyboard concept *before* learning EE, arguing that more knowledge means more self-imposed rules that narrow problem-solving. The first concept was "deeply flawed" but gave a north star to iterate against.
- **Iterate physically, early and often.** Modeled the layout to scale in **Blender** for a rough physical reference, then built a non-electrical switch-plate grid in **KiCad** just to 3D-print, stuff with switches, and feel on the desk. The first print was "truly terrible"; the final plate was ~**mark 10**. Holding ugly rev-1 PCBs surfaced architecture problems far faster than CAD alone.
- **Modularity + independence per side are the top pillars.** Each half must function independently of the other (not the usual "left half is master, right extends from it" arrangement) — directly motivated by users who only need one half (prosthetic/limb-difference accessibility).
- **Upgradeability via a separated control board.** The controller is kept separate from the matrix so a future **wireless kit** can be installed by popping the back panel and swapping the control board + adding a battery (~10-minute upgrade), rather than buying a whole new keyboard. Repairability is framed as a personal engineering ethic.
- **Cost forced a reversible-board redesign.** Each half originally needed 3 matrix sub-boards → 6 boards + 2 controllers per set, projecting to an unaffordable BOM. He restarted the PCB design to make boards **reversible**, cutting 8 unique boards per set down to 4 — halving price and manufacturing overhead while keeping things upgradeable/repairable. Case was optimized for either **CNC or 3D printing**.
- **Firmware staged deliberately (QMK).** Matrix/cross-board connectivity first (typed within an hour), then LEDs (**SK6812 mini**, individually addressable — both for RGB and as an accessibility backlight), then position-aware matrix effects, then the OLED + UI.
- **Real debugging war stories.** A dead OLED (not a code bug — his wife suggested swapping the hardware) cost hours; QMK docs were "optimistic" and forced a UI rewrite; severe input lag (~1s key delay, choppy LEDs) was fixed by capping the OLED update limit to 1 and setting the **I2C clock to 400 kHz** to free bandwidth for scan + LED + display simultaneously.
- **Tradeoff honesty.** A connector chosen to link matrix→controller was too tall, forcing yet another revision. He treats restarts and revs as expected practice, not failure ("progress comes in waves").

## Notable Timestamps

- **00:45** — Lands on the ZSA Moonlander as the $400 starting point that sparked the project.
- **02:42** — Models layout to scale in Blender before any electronics decisions.
- **03:04** — KiCad switch-plate mockup; first 3D print "awful," iterates to ~mark 10.
- **03:43** — Quick primer on how a keyboard matrix + GPIO + controller works.
- **05:40** — First rev-1 PCBs arrive from JLCPCB in a little **blue box** ("very ugly, nearly instantly outdated"); holding them drives major architecture changes.
- **07:17** — Dives into QMK; first matrix test passes, he can type — beats his imposter syndrome.
- **08:13** — SK6812 mini LED bring-up, column by column.
- **11:05** — Input-lag disaster, fixed via OLED update cap + 400 kHz I2C.
- **13:00–14:20** — Backstory on building split keyboards for veterans/limb-difference users, leading into the **core design pillars**.
- **14:11 (what the user flagged)** — This is the moment the two foundational pillars are stated on screen while the keyboard/PCBs are shown: **"this keyboard must be modular and each half must be capable of independence from the opposite side."** The "blue keyboard" reads as the blue (likely JLCPCB-blue) reversible board / prototype being displayed exactly as the independence-per-side principle is articulated — i.e., the cool part is seeing the actual hardware that embodies "either half stands alone." (The earlier "little blue box" of rev-1 boards appears at 5:40 if that's the blue the user remembered.)
- **15:07** — The from-scratch reversible-board redesign that halves the board count (8→4).
- **15:54** — Why the control board is separate: future swappable wireless kit.
- **16:39** — "Check them out" — the finished reversible boards are shown in hand.
- **17:00** — Roadmap: add-on numpad/macropad, USB dock for dockable modules, a web-hosted keymap customizer modeled on **ZSA's Oryx**.

## Relevance to Keygen build

- **Split architecture:** Strong argument for true **independence per side** rather than a master/slave split — worth deciding early for Keygen since it dictates whether each half carries its own controller or a shared one. Note his reversibility trick (one board layout serving both halves) as a cost/manufacturing lever.
- **Tenting/adjustability:** This build is light on physical ergonomics — it focuses on *electrical/modular* adjustability (swappable control board, dockable modules, web keymap editor) rather than tenting/splay/tilt mechanics. So it's a weaker reference for the mechanical adjustability questions; pair it with dedicated ergonomic-keyboard sources for tenting.
- **Layout design:** The Blender-then-KiCad-then-print loop (mock the layout non-electrically, print, type-test, iterate to ~mark 10 before committing copper) is a directly reusable workflow for nailing Keygen's key positions.
- **Thumb cluster:** The video doesn't deep-dive thumb geometry. Relevant to the **Keygen preference for Kinesis Advantage-style scooped block thumb clusters over the Corne/Kyria curved arc** mainly as a contrast — Nick's pain point that kicked off the whole project was the Moonlander's thumb keys "starting to bug me," reinforcing that thumb-cluster comfort is make-or-break. His modular/independent approach doesn't prescribe an arc, so it's compatible with adopting a scooped-block thumb layout rather than the splayed-arc style. Treat thumb geometry as a Keygen-specific decision to source elsewhere.

## Related

- [[02 - layout design]]
- [[06 - split architecture]]
- [[09 - case design]]
- [[01 - overview]]
- [[11 - learning resources & references]]
