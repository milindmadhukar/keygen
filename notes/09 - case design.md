---
created: 2026-03-09
updated: 2026-10-22T17:53
name: 09 - case design
---

> [!success] Case
> A **closed, flat, gasket-mounted 3D-printed PETG case** per half: a bottom shell and a top frame, with the polycarbonate switch plate floating on Poron gaskets between them. Openings on the top edge for **USB-C and the power switch**, a guided reset pinhole in the floor, and foam layers inside. Summary: [[12 - final design#Case]]. Clearances, plate spec and PCB positions: [[14 - case & plate requirements]].

## Status

Designed and generated from the PCB. The floor takes rubber feet, and a steel disc set flush into a pocket for a detachable magnetic tenting stand.

- `tools/gen_case.py` (build123d) writes the printable parts to `case/bottom/stl/` and `case/top/stl/` in the repo, with STEP files in each part's `step/` folder. It also runs a fit check against the PCB, plate, controller, reset button, OLED modules and keycaps at full travel, the keycaps taken at their largest and lowest and grown by the plate's float; it reports no overlaps.
- `tools/gen_plate.py` writes the plate as its own KiCad board, `pcb/plate/keygen-plate.kicad_pcb`, and its Gerbers, `case/plate/gerber/keygen-plate-{left,right}-gerbers.zip`, with the order settings in `case/plate/PLATE.md`.
- Both read `tools/case_geometry.py`, which takes every position from the PCB, so a PCB change is one rerun away. `tools/render_case.py` renders the board in its case into `assets/`.
- The parts go to a printing service.

## Construction

- **Material: PETG**, plastic all round because the nRF52840's antenna is inside.
- **Shape:** flat, following the PCB outline 7.5 mm out, with sharp corners. Each half is 175.4 × 143.7 mm and 22.6 mm tall (bottom shell 17.1 mm, top frame 5.5 mm).
- **Gasket mount:** the plate and PCB are one unit, held together by the switches and spaced by M2 standoffs, and touch the case only through the gaskets.
  - The plate has **8 tabs per half**, 12 × 5 mm, spread round its edge and kept clear of the USB-C and power switch.
  - Each tab sits between two **Poron strips, 12 × 4 × 3 mm**, cut from 80 × 4 × 3 mm strips: one on a ledge in the bottom shell, one under the top frame. Closing the case squeezes each strip by 1.0 mm, a third of it, so a part printed 0.2 mm off still leaves it firmly held. That is 16 strips per half.
  - The PCB and plate edges keep 1.0 mm from the walls, and the controller 1.5 mm from the floor, so the unit floats.
- **Closing the case:** 8 **M2 × 16 socket-head screws** per half go up from the underside, through the bottom shell's walls, into **M2 × 3 heat-set inserts** in blind holes in the top frame's underside. The top frame has no screw holes on top: 1.7 mm of frame covers each insert. The heads sit 2 mm up inside counterbores in the floor. No insert or screw is within 15 mm of the controller's antenna end.
- **Top frame deck:** inside the rim, the top frame carries a deck level with it (7.0 to 9.0 mm above the PCB, 4.0 mm over the plate top) that covers the plate everywhere but the keycaps, keeping 1.2 mm clear of each, with a 0.4 mm chamfer round each window's mouth on the deck top. A pressed keycap's skirt sinks about 1 mm into its window, so the clearance takes an 18.4 mm DSA skirt, the plate floating 0.5 mm to one side in its gasket pockets, and cap wobble and print error; the chamfer takes the first-layer squish, as the deck top is printed on the bed. Every web or point of deck narrower than 4 mm is trimmed back to a rounded end, so nothing on the 2 mm printed deck can snap off.
- **Walls:** 6.5 mm thick, thinned outside across the USB-C and power switch out to the corner: 1.5 mm past the inner wall at the lever, and 1.5 mm in front of the controller's pocket at the USB-C. The floor is 3.0 mm, and 1.4 mm under the battery bay.

## The stack

Heights above the PCB's top surface:

| Layer | From | To |
|---|---|---|
| Case floor (battery bay sunk to −12.2 mm) | −13.6 mm | −10.6 mm |
| Cavity (the controller envelope reaches −9.1 mm) | −10.6 mm | −1.6 mm |
| PCB | −1.6 mm | 0 |
| Bottom shell walls, up to the joint | | 3.5 mm |
| Lower gasket strip, on the ledge | 1.5 mm | 3.5 mm |
| Plate tab, 1.5 mm polycarbonate | 3.5 mm | 5.0 mm |
| Upper gasket strip, under the frame | 5.0 mm | 7.0 mm |
| Top frame rim | 3.5 mm | 9.0 mm |
| Top frame deck, over the plate | 7.0 mm | 9.0 mm |
| Poron ring switch pads, on the PCB | 0 | 0.5 mm |
| EVA plate foam, taped under the plate | 1.5 mm | 3.5 mm |
| EVA case foam, on the floor | −10.6 mm | −5.6 mm |
| Knob underside, using the encoder's maximum bushing height | 14.1 mm | |

So the PCB top is 13.6 mm above the desk and the plate top 18.6 mm. Keycap tops are about 33 mm, before tenting and feet.

## Openings

- **USB-C:** the controller's end, which overhangs the slanted top edge, sits in a 20 mm pocket inside the wall, open at the top of the bottom shell so the stack drops in straight. A 14.2 × 9.8 mm port with 2 mm corners goes through the wall in front of it, centred on the receptacle: a 12.35 × 6.5 mm plug overmould, moved by the floating stack, keeps 0.4 mm clear of it, so the cable never ties the stack to the case. The port's height comes from the socket height, `SOCKET_H` in `tools/gen_schematic.py`.
- **Power switch:** a 9 × 3.4 mm slot at the lever, through the 1.5 mm wall.
- **Reset:** a 2 mm pinhole through the floor, countersunk outside, with a guide tube up to 2 mm under the button so a paperclip finds it; the button clears it with the stack pressed 1.5 mm down onto its gaskets. The reset buttons mirror between the halves, and so do the pinholes.
- **Through the plate:** on each half a 15 × 15 mm encoder cut-out and a 29.5 × 30 mm OLED window, clear of the OLED module above it.
- **Through the deck:** an OLED window round the display's active area, 1 mm clear at the lip's underside, opening at 45° on three sides and further towards the thumbs, so the whole active area shows at 50° from vertical. The OLED module is held in the top frame: its glass sits in a pocket under a 1.0 mm lip, 1.0 mm below the deck top, and its board sits on a boss that thickens the deck down to 6.4 mm above the PCB, located and held by four Ø 1.7 mm pegs through its corner holes, their tips melted over or glued, with 1.5 mm reliefs over its four solder joints and over the flex cable at its far edge. A 4-pin Dupont lead from it plugs onto a right-angle header in J101/J201, lying flat under it in the plate's window, so the top frame comes off; the module clears the floating plate by 0.5 mm all round. The encoder bushing (7 mm) passes through a 9 mm hole, hidden under the knob; the body has a 15 mm square underside relief to 7.4 mm. The knob's underside is 5.1 mm above the deck using the tallest bushing.

Exact sizes and positions: [[14 - case & plate requirements]].

## Sound

- **Gaskets:** the Poron strips on the tabs carry the whole plate and PCB, which is what gives the soft, deep sound.
- **Case floor foam:** 5 mm EVA, round the battery bay, the controller, the battery connector, the slide switch, the reset tube and the encoder and OLED pins, 1 mm clear of each and 0.5 mm from the walls. Its top is 3.0 mm below the parts under the PCB, 1.5 mm with the stack pressed down.
- **Between plate and PCB:** the gap is 3.5 mm, filled at each mounting hole by an M2 × 3 mm standoff on a 0.5 mm shim, screwed on from below with an M2 × 5 button head that fills 2.9 mm of its thread. Nothing screws into the standoffs from above: they bear on the plate, and the switches, clipped into the plate and plugged into their sockets, hold plate and PCB together. A 0.5 mm Poron ring switch pad is stuck on the PCB round each switch: a square ring about 18 mm across with a 14.2 mm open middle, notched on the clip sides, which keeps the pins and the LED window clear. Seven rings per half have a corner snipped off round a standoff. The 2 mm EVA plate foam is taped to the plate's underside, 1.0 mm above the rings, so it damps the plate without pressing on the PCB. It has 14.4 mm switch cut-outs, notched 4.5 × 1.0 mm on the clip sides for the switch latches, the plate's encoder and OLED cut-outs and holes for the pads and standoffs. Plate foam up to 3.0 mm thick fits.
- **Cut files:** the switch pads come ready-made; `gen_case.py` models them in place in `case/foam/step/`. It writes the plate foam and the case foam per half as 1:1 DXF and SVG, seen from above, to `case/foam/dxf/` and `case/foam/svg/` in the repo, for a laser or a printed template. No strip is narrower than 1.5 mm. The fit check covers the foam too.
- PETG is light and resonant on its own, so the foam and the gaskets do most of the work.

## Feet and tenting

- **Feet:** four clear domed silicone bumpers per half, 8 mm across and 3 mm tall, self-adhesive, near the floor's corners: outer bottom and the thumb tip, 7 mm in from the edges, and outer top and inner top, 7 mm in from the side and 17 mm below the top edge, which keeps them clear of the outer top case screw and the USB-C opening. All clear the screw counterbores and the reset pinhole.
- **Tenting:** a detachable magnetic tenting stand per half, made for split keyboards: a magnetic puck on a height- and angle-adjustable arm. Its puck holds to a 40 mm self-adhesive steel disc in a 1.0 mm pocket in the floor's underside, so it sits flush like the screw heads. `case_geometry.steel_disc()` places it on the inner half, at least 15 mm from the controller's antenna end, 2 mm or more off the battery bay (whose floor is thinner), the counterbores and the reset pinhole, and 12 mm in from the floor's edge, clear of the feet. The floor over the pocket is 2.0 mm. The half tilts on its two outer feet, about 13° with the arm at 30 mm; without the stand it lies flat on its feet.
- Placement is in the Feet and tenting section of `INSTRUCTIONS.md` in the repo.

## Assembly

Plate foam taped under the plate, plate on its standoffs on the PCB, the OLED's right-angle header in, switches in, then the unit onto the lower gaskets in the bottom shell, upper gaskets on the tabs, and the top frame, with the OLED module pegged into it and plugged in, screwed down. Steps: [[10 - assembly & build guide#Case assembly]].

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
