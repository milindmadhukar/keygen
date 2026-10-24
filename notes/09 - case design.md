---
created: 2026-03-09
updated: 2026-10-22T17:53
name: 09 - case design
---

> [!success] Case
> A **closed, flat, gasket-mounted 3D-printed PETG case** per half: a bottom shell and a top frame, with the FR-4 switch plate floating on Poron gaskets between them. Openings on the top edge for **USB-C and the power switch**, a guided reset pinhole in the floor, and foam layers inside. Summary: [[12 - final design#Case]]. Clearances, plate spec and PCB positions: [[14 - case & plate requirements]].

## Status

Designed and generated from the PCB; tenting, base weight and rubber feet are still to be added to the floor.

- `tools/gen_case.py` (build123d) writes the printable parts to `case/bottom/stl/` and `case/top/stl/` in the repo, with STEP files in each part's `step/` folder. It also runs a fit check against the PCB, plate, controller, reset button, OLED modules and keycaps at full travel; it reports no overlaps.
- `tools/gen_plate.py` writes the plate as its own KiCad board, `pcb/plate/keygen-plate.kicad_pcb`, and its Gerbers, `case/plate/gerber/keygen-plate-{left,right}-gerbers.zip`, with the order settings in `case/plate/PLATE.md`.
- Both read `tools/case_geometry.py`, which takes every position from the PCB, so a PCB change is one rerun away. `tools/render_case.py` renders the board in its case into `assets/`.
- The parts go to a printing service.

## Construction

- **Material: PETG**, plastic all round because the nRF52840's antenna is inside.
- **Shape:** flat, following the PCB outline 7.5 mm out, with sharp corners. Each half is 175.4 × 143.7 mm and 23.2 mm tall (bottom shell 18.0 mm, top frame 5.2 mm).
- **Gasket mount:** the plate and PCB are one unit, tied together by M2 standoffs, and touch the case only through the gaskets.
  - The plate has **8 tabs per half**, 12 × 5 mm, spread round its edge and kept clear of the USB-C and power switch.
  - Each tab sits between two **Poron strips, 12 × 4 × 2 mm**, cut from 80 × 4 × 2 mm strips: one on a ledge in the bottom shell, one under the top frame. Closing the case squeezes each strip by 0.4 mm. That is 16 strips per half.
  - The PCB and plate edges keep 1.0 mm from the walls, and the controller 1.5 mm from the floor, so the unit floats.
- **Closing the case:** 8 **M2 × 16 socket-head screws** per half go up from the underside, through the bottom shell's walls, into **M2 × 3 heat-set inserts** in blind holes in the top frame's underside. The top frame has no screw holes on top: 1.4 mm of frame covers each insert. The heads sit 3 mm up inside counterbores in the floor. No insert or screw is within 15 mm of the controller's antenna end.
- **Top frame deck:** inside the rim, the top frame carries a deck level with it (6.6 to 8.6 mm above the PCB, 3.6 mm over the plate top) that covers the plate everywhere but the keycaps, keeping 0.8 mm clear of each; webs under 1 mm are dropped.
- **Walls:** 6.5 mm thick, thinned to 1.5 mm across the USB-C and power switch out to the corner. The floor is 3.0 mm, and 2.0 mm under the battery bay.

## The stack

Heights above the PCB's top surface:

| Layer | From | To |
|---|---|---|
| Case floor (battery bay sunk to −12.6 mm) | −14.6 mm | −11.6 mm |
| Cavity (the controller envelope reaches −10.1 mm) | −11.6 mm | −1.6 mm |
| PCB | −1.6 mm | 0 |
| Bottom shell walls, up to the joint | | 3.5 mm |
| Lower gasket strip, on the ledge | 1.9 mm | 3.5 mm |
| Plate tab, 1.5 mm FR-4 | 3.5 mm | 5.0 mm |
| Upper gasket strip, under the frame | 5.0 mm | 6.6 mm |
| Top frame rim | 3.5 mm | 8.6 mm |
| Top frame deck, over the plate | 6.6 mm | 8.6 mm |
| Poron ring switch pads, on the PCB | 0 | 0.5 mm |
| EVA plate foam | 0.5 mm | 2.5 mm |
| EVA case foam, on the floor | −11.6 mm | −6.6 mm |
| Knob underside, using the encoder's maximum bushing height | 14.1 mm | |

So the PCB top is 14.6 mm above the desk and the plate top 19.6 mm. Keycap tops are about 34 mm, before tenting and feet.

## Openings

- **USB-C:** an open slot 20 mm wide from the floor up to the PCB's underside. That covers the whole controller end, which overhangs the slanted top edge, and any cable overmould.
- **Power switch:** a 9 × 3.4 mm slot at the lever, through the 1.5 mm wall.
- **Reset:** a 2 mm pinhole through the floor, countersunk outside, with a guide tube up to 1 mm under the button so a paperclip finds it. The reset buttons mirror between the halves, and so do the pinholes.
- **Through the plate:** on each half a 15 × 15 mm encoder cut-out and a 29.5 × 30 mm OLED window, with the OLED glass about level with the plate top.
- **Through the deck:** an OLED window round the display's active area, 1 mm clear at the deck's underside, opening at 45° on three sides and further towards the thumbs, so the whole active area shows at 50° from vertical. The glass sits 3.5 mm below the deck top. The encoder bushing (7 mm) passes through a 9 mm hole, hidden under the knob; the body has a 15 mm square underside relief to 7.4 mm. The knob's underside is 5.5 mm above the deck using the tallest bushing. The plate screw heads sit 0.5 mm under the deck.

Exact sizes and positions: [[14 - case & plate requirements]].

## Sound

- **Gaskets:** the Poron strips on the tabs carry the whole plate and PCB, which is what gives the soft, deep sound.
- **Case floor foam:** 5 mm EVA, round the battery bay, the controller, the battery connector, the slide switch, the reset tube and the encoder and OLED pins, 1 mm clear of each and 0.5 mm from the walls. Its top is 3.0 mm below the parts under the PCB, 1.5 mm with the stack pressed down.
- **Between plate and PCB:** the gap is 3.5 mm, filled at each mounting hole by an M2 × 3 mm standoff on a 0.5 mm shim. A 0.5 mm Poron ring switch pad is stuck on the PCB round each switch: a square ring about 18 mm across with a 14.2 mm open middle, notched on the clip sides, which keeps the pins and the LED window clear. Seven rings per half have a corner snipped off round a standoff. Then 2 mm EVA plate foam, with 14.4 mm switch cut-outs, the plate's encoder and OLED cut-outs and holes for the pads and standoffs. Plate foam up to 2.8 mm thick fits.
- **Cut files:** the switch pads come ready-made; `gen_case.py` models them in place in `case/foam/step/`. It writes the plate foam and the case foam per half as 1:1 DXF and SVG, seen from above, to `case/foam/dxf/` and `case/foam/svg/` in the repo, for a laser or a printed template. No strip is narrower than 1.5 mm. The fit check covers the foam too.
- PETG is light and resonant on its own, so the foam and the gaskets do most of the work.

## Still to add: tenting, weight and feet

Tenting is not chosen yet; it decides what the flat floor gets. Weight goes in the base, away from the controller's antenna end. Rubber feet go on the floor.

## Assembly

Plate on its standoffs on the PCB, the OLED module in through its window, switches in, then the unit onto the lower gaskets in the bottom shell, upper gaskets on the tabs, and the top frame screwed down. Steps: [[10 - assembly & build guide#Case assembly]].

## Related notes
- [[14 - case & plate requirements]]: openings, clearances, plate and positions
- [[12 - final design]]: the design as a whole
- [[07 - switch & keycap selection]]: switch pads and keycaps
- [[10 - assembly & build guide]]: build steps

## Resources

- [build123d](https://build123d.readthedocs.io/): the Python CAD library the case is written in
- [FreeCAD](https://www.freecad.org/): opens the STEP files for a look or a hand edit
- [Heat-set insert guide (video)](https://www.youtube.com/watch?v=cyof7fYFcuQ)
- [Mantaray keyboard case files](https://github.com/tuxedocurly/mantaray_keyboard/tree/main/case): a reference 3D-printed split case with M2 heat-set inserts and a floor reset hole

### Video notes
- [[How To Build A Corne Keyboard - Beginners Guide]]: 3D-printed tented case with screw-in tenting legs (18 mm front / 40 mm rear)
- [[I Built a Ridiculous Keyboard by Hand - Dactyl-Manuform]]: a heavy base keeps a split half from sliding
