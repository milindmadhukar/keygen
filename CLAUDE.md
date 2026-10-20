# Keygen

## Keep the README current

Update `README.md` in the same change whenever something fundamental changes. That covers:

- the board: outline, parts added or removed, routing approach, design rules
- the specifications: keys, layout, controller, connectivity, power, lighting
- the build: steps or scripts added to or removed from the PCB pipeline, new requirements
- documentation, manufacturing files or firmware being added, moved or removed
- the project status checklist, when a milestone is reached

Keep its style: professional, no emojis, and link to the relevant document or file rather than
repeating it.

When the board's look changes, regenerate the images in `docs/` from the current board too:

```sh
python3 tools/render_board.py     # docs/render-hero.png, render-top.png, render-bottom.png
python3 tools/render_routing.py   # docs/pcb-routing.png (the two-layer routing picture)
```

`render_board.py` renders with the board's stackup colours, from a temporary copy whose mask is
an opaque black: KiCad's named "Black" mask, which the board keeps so the Gerber job file says
"Black", renders as see-through brown.
