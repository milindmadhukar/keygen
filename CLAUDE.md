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
B="$PWD/pcb/keygen.kicad_pcb"
kicad-cli pcb render -o hero.png -w 2800 -h 1300 --quality high --floor --perspective \
  --rotate '-38,0,0' --zoom 1.85 --background transparent "$B"
kicad-cli pcb render -o top.png -w 2800 -h 1100 --quality basic --side top --zoom 2.5 --background transparent "$B"
kicad-cli pcb render -o bottom.png -w 2800 -h 1100 --quality basic --side bottom --zoom 2.5 --background transparent "$B"
# then trim and shrink each one, e.g.:
magick hero.png -trim +repage -bordercolor none -border 20 -resize 2000x -strip docs/render-hero.png
```

These produce `docs/render-hero.png`, `docs/render-top.png` and `docs/render-bottom.png`,
and `python3 tools/render_routing.py` writes `docs/pcb-routing.png` (the two-layer routing picture).
