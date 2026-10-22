---
created: 2026-06-16
name: I Built a Ridiculous Keyboard by Hand - Dactyl-Manuform
source: https://www.youtube.com/watch?v=VlHgEqLVYqA
type: video-note
---

A hobbyist build log of a hand-wired **Dactyl-Manuform**, a fully 3D-printed split ergonomic keyboard with a sculpted, concave key bowl and a curved thumb cluster. The maker prints both halves, sands and paints the cases, hand-wires the switch matrix (no PCB) with diodes onto Arduino Pro Micro controllers, flashes firmware, and assembles the result over roughly four weeks. The design's premise: by letting each hand sit at its own distance and angle, the keyboard reduces wrist and finger strain. GitHub for the build: https://github.com/abstracthat/dactyl-manuform

## Key Takeaways

- **Sculpted 3D split design** — the Dactyl-Manuform is a two-half ergonomic board where each key sits in a concave bowl at its own height/angle, so the hands can be placed independently to ease wrist/finger strain. This is the sculpted-3D philosophy, not a flat board.
- **Fully 3D printed case** — both halves are printed. Because almost the entire shell is overhanging geometry, the print needs *massive* support structures that take a long time to remove (contributed to a ~3-day print/cleanup window).
- **Finishing is the hidden cost** — getting a printed part smooth enough to paint took ~2 full days of sanding (120 → 240 → 320 → 1000 grit), then prime + paint. A satin black left a rough finish, so he re-sanded with 1000 grit afterward. He notes you can skip all of this and just run the raw printed part.
- **Switches** — 54 needed per the guide, but the real count was 64 (he ordered too few and broke one jamming it in sideways). Used "alias" silent-clicky switches (similar to silent reds but with a slight click); Cherry MX profile, clip into the printed plate sideways, pins oriented consistently (pins at bottom).
- **Keycaps** — DSA profile chosen because every cap is uniform and rotation-agnostic, which matters when keys must go in non-standard positions on a sculpted board. Letters were left on for learning; the **thumb cluster was left blank** because labeled custom sets were too expensive.
- **Controller** — each half uses an **Arduino Pro Micro** (cheap clone). Being a split board, both halves need a controller and they communicate to each other over a cable (TRRS-style).
- **Hand-wired matrix (no PCB)** — every row and every column of the switch matrix is soldered by hand. Columns done first in insulated wire (kept flat to the base for clearance), then the rows. Each column took ~30 min; ~3 hours total per side. Where he nicked a wire, he just re-soldered the break.
- **Diodes on the rows** — diodes give N-key rollover so the controller can tell which keys are pressed simultaneously. Technically optional (cheap boards omit them), but at ~5 cents each and since you're soldering anyway, worth adding.
- **Switches hot-glued in, not just clipped** — done so keycaps can be pulled later without yanking the switch (and its soldered diode) out with them.
- **Heavy metal base for stability** — added a ~800 g (1 lb), 5 mm water-jet-cut stainless steel base. Because you push *inward* on a split board, mass keeps it from sliding even with rubber feet. Had to watch wire length so leads don't short on the metal base. Brushed finish by hand-sanding; noted it's a fingerprint magnet.
- **Wiring gotcha — cable pin swap** — through the connecting cable the contacts don't pass straight through; black↔yellow and orange↔grey-green swap, so power/ground/data had to be reassigned on the second half to match.
- **Final assembly** — controller and USB epoxied in place; soldered + flashed the firmware over about a weekend. Total project ~4 weeks. Inspired by a Zach Freeman keyboard video.

## Notable Timestamps

- **00:00** — Intro: what the Dactyl-Manuform is and the ergonomic premise (independent hand angle/distance to reduce strain)
- **00:22** — 3D printed part, massive supports, ~3-day build
- **00:48** — Removing supports; most of the print is overhanging material
- **01:03** — Sanding ladder (120/240/320/1000 grit); ~2 days of sanding
- **01:46** — Prime and paint; satin black went rough, re-sanded with 1000 grit
- **02:05** — Switches: 54 "alias" silent-clicky, Cherry MX profile, clipping them into the plate
- **02:58** — Lesson learned: didn't count, needed 64 not 54, broke one
- **03:46** — Stainless steel water-jet base (~800 g, 5 mm) for mass/stability
- **05:06** — DSA keycaps; uniform/rotation-agnostic; thumb cluster left unlabeled
- **06:04** — Controller circuitry; split board needs two controllers + cable; Arduino Pro Micro
- **06:53** — Soldering switches; hot-gluing them in so keycaps pull without diodes
- **07:24** — Hand-wiring the matrix: columns first (insulated), then rows; ~30 min/column
- **08:21** — Diodes on rows for N-key rollover; optional but cheap
- **08:46** — Flashed and working
- **09:17** — Cable pin-swap problem and power/ground/data reassignment
- **09:58** — Epoxying the USB/controller in
- **10:41** — Done; ~4 weeks total; now has to learn to type on it
- **10:59** — GitHub link + credits Zach Freeman as inspiration

## Relevance to Keygen build

This build is a direct, hands-on look at the **sculpted-3D / Kinesis-Advantage-style** path the Keygen project is leaning toward, as opposed to the flat-PCB tented-arc style of the Corne/Kyria.

- **Concave bowl + scooped thumb cluster** — the Dactyl-Manuform's defining feature is exactly what the user wants: a deeply scooped concave key bowl with a curved/clustered thumb section, the same family as the Kinesis Advantage scooped block. It is the strongest reference for *why* a sculpted 3D bowl beats the flat Corne/Kyria curved-arc thumb arrangement the user dislikes. See [[02 - layout design]] and [[06 - split architecture]].
- **Hand-wired vs PCB tradeoff** — this build deliberately skips a PCB and hand-wires the whole matrix with diodes. That is the most practical route for a fully sculpted 3D case (a rigid flat PCB can't follow the curved bowl). The cost is time: ~3 hrs/side of fiddly soldering plus re-soldering nicked wires. The Keygen build's case/architecture decision (sculpted 3D bowl) likely forces this same hand-wired choice over [[05 - pcb design]] — relevant context for [[10 - assembly & build guide]].
- **3D-printed sculpted case is achievable but labor-heavy** — confirms a printed Dactyl-style shell is viable on a hobbyist budget, but the real cost is *finishing* (days of sanding/painting) and *support removal* on the overhang-heavy print. Useful expectation-setting for [[09 - case design]] if Keygen goes the printed-bowl route; the raw-print option is also valid if finish isn't a priority.
- **Heavy base for split stability** — the inward-push-causes-sliding insight and the stainless-steel mass base is a concrete, cheap stability fix worth noting for [[09 - case design]].
- **Controller + firmware** — Arduino Pro Micro per half with cable interconnect is the baseline split topology; relevant to [[06 - split architecture]] and controller/firmware decisions.

## Related

- [[09 - case design]]
- [[06 - split architecture]]
- [[02 - layout design]]
- [[10 - assembly & build guide]]
- [[11 - learning resources & references]]
