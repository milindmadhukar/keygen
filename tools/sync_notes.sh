#!/bin/sh
# Copy notes/ into the Obsidian vault's Keygen folder. The repo's notes/ is the original; the
# vault's obsidian-git picks the copy up from there. Run by the post-commit and post-merge hooks
# in .githooks/ on main, or by hand.
set -e
VAULT="$HOME/Documents/Obsidian Vault/01 - Projects/Hardware & Electronics/Keygen Custom Keyboard"
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
[ -d "$VAULT" ] || { echo "sync_notes: no vault folder at $VAULT, skipped" >&2; exit 0; }
rsync -a --delete --exclude .claude --exclude .DS_Store "$ROOT/notes/" "$VAULT/"
echo "sync_notes: notes/ copied to the Obsidian vault"
