#!/usr/bin/env bash
#
# Nullglow installer.
#
#   ./install.sh              install the Nullglow variant
#   ./install.sh --neon       install the Nullglow Neon variant
#   ./install.sh --uninstall  remove everything and restore backups
#
# Nothing is overwritten without a backup, and your shell rc and gitconfig are
# never edited — the lines you need are printed at the end for you to paste.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST="$ROOT/dist"
BACKUP="$ROOT/.backup"

VARIANT="nullglow"
LABEL="Nullglow"
UNINSTALL=0

for arg in "$@"; do
  case "$arg" in
    --neon)      VARIANT="nullglow-neon"; LABEL="Nullglow Neon" ;;
    --uninstall) UNINSTALL=1 ;;
    --batman)    echo "Nice try. Noir didn't survive the contrast checker — see palette.json."; exit 0 ;;
    -h|--help)   sed -n '3,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)           echo "unknown option: $arg" >&2; exit 1 ;;
  esac
done

# ── helpers ──────────────────────────────────────────────────────────────────

say()  { printf '  %s\n' "$*"; }
step() { printf '\n\033[1m%s\033[0m\n' "$*"; }
skip() { printf '  \033[2m%s\033[0m\n' "$*"; }

have() { command -v "$1" >/dev/null 2>&1; }

# copy src -> dst, backing up whatever was there
place() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [[ -e "$dst" ]] && ! cmp -s "$src" "$dst"; then
    mkdir -p "$BACKUP/$(dirname "${dst#"$HOME"/}")"
    cp -p "$dst" "$BACKUP/${dst#"$HOME"/}"
    say "backed up $(basename "$dst")"
  fi
  cp "$src" "$dst"
}

# ── uninstall ────────────────────────────────────────────────────────────────

if [[ $UNINSTALL -eq 1 ]]; then
  step "Removing Nullglow"
  rm -rf "$HOME/.vscode/extensions/nullglow-theme" && say "VS Code extension removed"
  rm -f "$HOME/.config/bat/themes/Nullglow.tmTheme" \
        "$HOME/.config/bat/themes/Nullglow Neon.tmTheme"
  have bat && bat cache --build >/dev/null 2>&1 && say "bat themes removed"
  rm -rf "$HOME/.config/nullglow" && say "shell snippets removed"
  rm -f "$HOME/.config/vivid/themes/nullglow.yml" \
        "$HOME/.config/vivid/themes/nullglow-neon.yml" && say "vivid themes removed"

  if [[ -d "$BACKUP" ]]; then
    step "Restoring backups"
    (cd "$BACKUP" && find . -type f -print0) | while IFS= read -r -d '' f; do
      cp -p "$BACKUP/${f#./}" "$HOME/${f#./}" && say "restored ${f#./}"
    done
    rm -rf "$BACKUP"
  fi
  printf '\nDone. Remove the lines you pasted into ~/.zshrc and ~/.gitconfig by hand.\n'
  exit 0
fi

# ── install ──────────────────────────────────────────────────────────────────

if [[ ! -d "$DIST" ]]; then
  echo "dist/ is missing — run: python3 build.py" >&2
  exit 1
fi

printf '\n\033[1mNullglow\033[0m — installing \033[1m%s\033[0m\n' "$LABEL"

step "VS Code"
if [[ -d "$HOME/.vscode/extensions" ]]; then
  EXT="$HOME/.vscode/extensions/nullglow-theme"
  rm -rf "$EXT"; mkdir -p "$EXT"
  cp -R "$DIST/vscode/." "$EXT/"
  say "installed to ~/.vscode/extensions/nullglow-theme"
  say "reload the window, then pick '$LABEL' in the theme list"
else
  skip "no ~/.vscode/extensions — skipped"
fi

step "bat"
if have bat; then
  mkdir -p "$(bat --config-dir)/themes"
  cp "$DIST/bat/Nullglow.tmTheme" "$DIST/bat/Nullglow Neon.tmTheme" "$(bat --config-dir)/themes/"
  bat cache --build >/dev/null 2>&1
  say "both themes registered — set BAT_THEME=\"$LABEL\""
else
  skip "bat not installed — skipped"
fi

step "starship"
if have starship; then
  place "$DIST/starship/$VARIANT.toml" "$HOME/.config/starship.toml"
  say "~/.config/starship.toml"
else
  skip "starship not installed — skipped"
fi

step "vivid"
if have vivid; then
  mkdir -p "$HOME/.config/vivid/themes"
  cp "$DIST/vivid/"*.yml "$HOME/.config/vivid/themes/"
  say "themes installed — LS_COLORS line below"
else
  skip "vivid not installed — skipped"
fi

step "Shell snippets"
mkdir -p "$HOME/.config/nullglow"
cp "$DIST/fzf/$VARIANT.sh"              "$HOME/.config/nullglow/fzf.sh"
cp "$DIST/zsh/$VARIANT-highlight.zsh"   "$HOME/.config/nullglow/highlight.zsh"
cp "$DIST/delta/$VARIANT.gitconfig"     "$HOME/.config/nullglow/delta.gitconfig"
say "~/.config/nullglow/"

step "Terminal.app"
say "double-click dist/terminal-app/$(echo "$LABEL" | tr -d ' ').terminal"
say "then Terminal > Settings > Profiles > $LABEL > Default"

# ── what you still have to paste ─────────────────────────────────────────────

cat <<EOF

$(printf '\033[1mAdd to ~/.zshrc\033[0m')

  export BAT_THEME="$LABEL"
  export LS_COLORS="\$(vivid generate $VARIANT)"
  source ~/.config/nullglow/fzf.sh
  source ~/.config/nullglow/highlight.zsh   # after the zsh plugins load

$(printf '\033[1mAdd to ~/.gitconfig\033[0m')

  [include]
      path = ~/.config/nullglow/delta.gitconfig

EOF

# ── and one more thing ───────────────────────────────────────────────────────

printf '\033[38;2;43;245;155m'
cat <<'EOF'
           .-"""-.
          /  o o  \
         |    >    |    nullglow
          \  ---  /     go make something
           '-...-'
EOF
printf '\033[0m\n'
