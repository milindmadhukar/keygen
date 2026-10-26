#!/usr/bin/env python3
"""Check the fabrication geometry, including clearances the case's solid fit check cannot see.

Run with ~/.venvs/keygen-cad/bin/python tools/check_mechanical.py. The part size allowances below
are the design envelopes used for this build, not measurements of an arbitrary substitute part.
"""
import itertools
import math
import sys
from pathlib import Path

import pcbnew
from shapely.affinity import rotate, translate
from shapely.geometry import Point, box

sys.path.insert(0, str(Path(__file__).parent))
import case_geometry as C
import gen_case as G


def rotated_box(k, width, height):
    return translate(rotate(box(-width / 2, -height / 2, width / 2, height / 2),
                            k["rot"], origin=(0, 0)), k["x"], k["y"])


def minimum_pairwise(shapes):
    return min(a.distance(b) for a, b in itertools.combinations(shapes, 2))


def require(condition, description):
    if not condition:
        raise SystemExit(f"FAIL: {description}")


board = pcbnew.LoadBoard(str(C.PCB))
for side, h in C.halves().items():
    caps = [rotated_box(k, k["w"] * 19.05 - C.CAP_GAP, k["h"] * 19.05 - C.CAP_GAP)
            for k in h["keys"]]
    housings = [rotated_box(k, C.SWITCH_FLANGE, C.SWITCH_FLANGE) for k in h["keys"]]
    pads = [rotated_box(k, C.SWITCH_PAD, C.SWITCH_PAD) for k in h["keys"]]
    plate_cuts = [rotated_box(k, C.CUTOUT, C.CUTOUT) for k in h["keys"]]
    cap_gap = minimum_pairwise(caps)
    housing_gap = minimum_pairwise(housings)
    pad_gap = minimum_pairwise(pads)
    plate_web = minimum_pairwise(plate_cuts)
    encoder_cuts = [box(x - C.ENC_CUTOUT / 2, y - C.ENC_CUTOUT / 2,
                        x + C.ENC_CUTOUT / 2, y + C.ENC_CUTOUT / 2) for x, y in h["enc"]]
    x0, y0, x1, y1 = h["oled"]
    oled_cut = box(x0 - C.OLED_CLEAR, y0 - C.OLED_CLEAR,
                   x1 + C.OLED_CLEAR, y1 + C.OLED_CLEAR)
    accessory_web = min([a.distance(b) for a in plate_cuts for b in encoder_cuts]
                        + [a.distance(oled_cut) for a in plate_cuts]
                        + [a.distance(oled_cut) for a in encoder_cuts])
    knob_gap = min(cap.distance(Point(p).buffer(C.KNOB_D / 2, resolution=64))
                   for cap in caps for p in h["enc"])
    # Allow 0.2 mm of additional cap skirt on each neighbouring key.
    require(cap_gap - 0.4 >= 0.5, f"{side} keycaps clash with size allowance")
    require(housing_gap >= 3.0, f"{side} switch housings too close")
    require(pad_gap >= 0.8, f"{side} switch pads overlap")
    require(plate_web >= 4.5, f"{side} plate webs too narrow")
    require(accessory_web >= 4.5, f"{side} plate web at OLED or encoder too narrow")
    require(knob_gap >= 5.0, f"{side} knob too close to keycaps")
    # The deck window must take the largest cap, the plate floating to one side of its gasket
    # pockets, and 0.3 mm of cap wobble and print error, with 0.2 mm to spare.
    window_spare = C.CAP_CLEAR - C.CAP_SIZE_TOL - C.POCKET_CLEAR - 0.3
    require(window_spare >= 0.2, f"{side} case keycap window allowance exhausted")
    require(C.OLED_CLEAR - 0.2 - 0.3 >= 0.5, f"{side} OLED plate opening too small")
    require((C.ENC_CUTOUT - C.ENC_BODY) / 2 - 0.2 - 0.3 >= 0.2,
            f"{side} encoder plate opening too small")
    require(C.ENC_RECESS_TOP - C.ENC_BODY_H - 0.2 >= 0.19,
            f"{side} encoder body too close to deck")
    battery = C.battery(h)["cell"]
    tall_gap = min(C.rects_dist(battery, part) for part in h["tall"])
    antenna_gap = C.rects_dist(battery, h["antenna"])
    require(tall_gap >= 10.0 and antenna_gap >= 15.0, f"{side} battery too close to tall parts or antenna")
    encoder = board.FindFootprintByReference("ENC101" if side == "left" else "ENC201")
    pins = {pad.GetNumber(): pad for pad in encoder.Pads() if pad.GetNumber() != "MP"}
    def mm_point(pad):
        pos = pad.GetPosition()
        return pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
    def pin_distance(a, b):
        return math.dist(mm_point(pins[a]), mm_point(pins[b]))
    encoder_row = tuple((a + b) / 2 for a, b in zip(mm_point(pins["A"]), mm_point(pins["B"])))
    switch_row = tuple((a + b) / 2 for a, b in zip(mm_point(pins["S1"]), mm_point(pins["S2"])))
    require(abs(pin_distance("A", "B") - 5.0) < 0.01 and
            abs(pin_distance("S1", "S2") - 5.0) < 0.01 and
            math.dist(encoder_row, mm_point(pins["C"])) < 0.01 and
            abs(math.dist(encoder_row, switch_row) - 14.5) < 0.01,
            f"{side} encoder pin grid differs from HongYan drawing")
    require(all(min(pcbnew.ToMM(p.GetDrillSize().x), pcbnew.ToMM(p.GetDrillSize().y)) >= 1.0
                for p in pins.values()), f"{side} encoder signal hole too small")
    mounting = [pad for pad in encoder.Pads() if pad.GetNumber() == "MP"]
    require(len(mounting) == 2 and abs(math.dist(*map(mm_point, mounting)) - 11.1) <= 0.5,
            f"{side} encoder mounting slot pitch differs from HongYan drawing")
    for pad in mounting:
        drill = pad.GetDrillSize()
        require(min(pcbnew.ToMM(drill.x), pcbnew.ToMM(drill.y)) >= 2.0,
                f"{side} encoder mounting slot too narrow")
    bottom, top, plate, tabs, screws = G.build(h)
    require(not G.screw_walls(bottom, top, screws), f"{side} case screw walls too thin")
    foam = G.foam_solids(h)
    foam["pads"], _ = G.switch_pads(h)
    foam.update({name + " gaskets": shape for name, shape in G.gaskets(tabs).items()})
    clashes = G.fit_check(h, bottom, top, plate, foam)
    require(not clashes, f"{side} 3D overlaps: {clashes}")
    print(f"{side}: keycap {cap_gap:.2f} mm ({cap_gap - 0.4:.2f} after cap allowance), housing {housing_gap:.2f} mm, "
          f"pad {pad_gap:.2f} mm, plate web {plate_web:.2f} mm, "
          f"accessory web {accessory_web:.2f} mm, knob {knob_gap:.2f} mm, "
          f"deck window {window_spare:.2f} mm spare after tolerances; "
          f"battery lateral {tall_gap:.1f} mm to parts / {antenna_gap:.1f} mm to antenna; "
          "3D overlaps 0", flush=True)

_, battery_gap, pressed_gap = C.battery_heights()
require(pressed_gap >= 1.0, "battery contacts underside at full gasket travel")
require(C.FLOAT_GAP >= 1.5, "controller has insufficient float travel")
threads = C.standoff_threads()
require(abs(threads["standoff and shim short of the plate"]) <= 0.1 + 1e-9, "standoff and shim do not fill the plate gap")
require(min(v for k, v in threads.items() if "into the standoff" in k) >= 0.8, "a plate screw barely reaches its standoff")
require(threads["between the two screws"] >= 0.2, "the screws above and below a standoff meet")
# a keycap pressed fully down, its stem recessed, over a plate screw head
skirt_over_heads = C.CAP_SKIRT - C.CAP_STEM_RECESS - C.KEY_TRAVEL - C.SCREW_HEAD_H
require(skirt_over_heads >= 0.3, "a pressed keycap reaches the plate screw heads")
print(f"battery: {C.BATTERY_STACK_T:.1f} mm installed envelope, {battery_gap:.1f} mm gap at rest, "
      f"{pressed_gap:.1f} mm at full travel; controller: {C.CONTROLLER_DEPTH:.1f} mm envelope "
      f"plus {C.FLOAT_GAP:.1f} mm travel")
print("standoffs: " + ", ".join(f"{k} {v:.1f} mm" for k, v in threads.items()))
print(f"keycaps: skirt {C.CAP_SKIRT:.1f} mm above the plate at rest, {skirt_over_heads:.1f} mm over the plate "
      f"screw heads at full travel with a {C.CAP_STEM_RECESS:.1f} mm recessed stem")
