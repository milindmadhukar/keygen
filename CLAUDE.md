# Keygen

## Keep the README current

Update `README.md` in the same change whenever something fundamental changes. That covers:

- the board: outline, parts added or removed, routing approach, design rules
- the specifications: keys, layout, controller, connectivity, power, lighting
- the build: steps or scripts added to or removed from the PCB pipeline, new requirements
- documentation, manufacturing files or firmware being added, moved or removed
- the project status checklist, when a milestone is reached

Keep its style: professional, no emojis, and link to the relevant document or file rather than
repeating it. Keep it short: the specifications, a few pictures and links. Detail goes in the notes
(below), and the step-by-step build in `INSTRUCTIONS.md`, which changes with the build too. Describe
only what the board has, as plain facts: no reasons for a choice, and no parts or features that
were removed or left out. The reasoning lives in the vault notes.

When the board's look changes, regenerate the images in `assets/` from the current board too:

```sh
python3 tools/render_board.py     # assets/render-hero.png, render-top.png, render-bottom.png
python3 tools/render_routing.py   # assets/pcb-routing.png (the two-layer routing picture)
```

`render_board.py` renders with the board's stackup colours, from a temporary copy whose mask is
an opaque black: KiCad's named "Black" mask, which the board keeps so the Gerber job file says
"Black", renders as see-through brown.

## Layout of the documentation

- `assets/`: images only (renders, keymap pictures), written by the `tools/render_*.py` scripts.
- `docs/`: Markdown documentation and the part datasheets.
- `notes/`: the Keygen design notes (Obsidian Markdown). Edit them here; the vault folder
  `~/Documents/Obsidian Vault/01 - Projects/Hardware & Electronics/Keygen Custom Keyboard/` is a
  copy. `tools/sync_notes.sh` mirrors `notes/` into it, run by the `.githooks/` post-commit (when
  a commit on `main` touches `notes/`) and post-merge hooks. In a fresh clone, turn the hooks on
  with `git config core.hooksPath .githooks`. The vault's obsidian-git commits the copy itself.
