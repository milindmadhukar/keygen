# Keygen

A one-off wireless split keyboard built on the [Redox](https://github.com/mattdibi/redox-keyboard)
layout: 66 QWERTY keys (Redox minus its inner column), a 2×2 + 1.25u thumb cluster per hand,
one rotary encoder on the right, per-key RGB + underglow and no screen. Two nRF52840
controllers (nice!nano v2) are hidden on the PCB underside and run ZMK, connecting over
Bluetooth or USB-C to the host and over Bluetooth or a TRRS cable between halves.

- `plan/index.html` — the build plan: layout drawing, connectivity, parts, pin budget,
  firmware notes, build steps, checklist, references. Open it in a browser.
- `notes/` — symlink to the project notes in the Obsidian vault
  (`~/Documents/Obsidian Vault/01 - Projects/Hardware & Electronics/Keygen Custom Keyboard`).
  `notes/12 - final design.md` is the source of truth. The link only resolves on this machine.

Redox is © 2018 Mattia Dal Ben, MIT licensed.
