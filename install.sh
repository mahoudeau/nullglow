#!/usr/bin/env bash
#
# Nullglow installer.
#
#   ./install.sh              install the Nullglow variant
#   ./install.sh --neon       install the Nullglow Neon variant
#   ./install.sh --uninstall  remove everything and restore backups
#
# Nothing is overwritten without a backup. Your shell rc and gitconfig are never
# edited. The lines you need get printed at the end for you to paste.

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
    --batman)    echo "Nice try. Noir didn't survive the contrast checker. See palette.json."; exit 0 ;;
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

  if [[ "$(uname)" == "Darwin" ]]; then
    # Through Terminal itself. Editing its preferences file behind its back is
    # what corrupted a profile during development.
    for prof in "Nullglow" "Nullglow Neon"; do
      osascript -e "tell application \"Terminal\" to delete settings set \"$prof\"" \
        >/dev/null 2>&1 || true
    done
    say "Terminal.app profiles removed (pick a new default in its settings)"
  fi

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
  echo "dist/ is missing. Run: python3 build.py" >&2
  exit 1
fi

printf '\n\033[1mNullglow\033[0m installing \033[1m%s\033[0m\n' "$LABEL"

step "VS Code"
if [[ -d "$HOME/.vscode/extensions" ]]; then
  EXT="$HOME/.vscode/extensions/nullglow-theme"
  rm -rf "$EXT"; mkdir -p "$EXT"
  cp -R "$DIST/vscode/." "$EXT/"
  say "installed to ~/.vscode/extensions/nullglow-theme"
  say "reload the window, then pick '$LABEL' in the theme list"
else
  skip "no ~/.vscode/extensions, skipped"
fi

step "bat"
if have bat; then
  mkdir -p "$(bat --config-dir)/themes"
  cp "$DIST/bat/Nullglow.tmTheme" "$DIST/bat/Nullglow Neon.tmTheme" "$(bat --config-dir)/themes/"
  bat cache --build >/dev/null 2>&1
  say "both themes registered. set BAT_THEME=\"$LABEL\""
else
  skip "bat not installed, skipped"
fi

step "starship"
if have starship; then
  place "$DIST/starship/$VARIANT.toml" "$HOME/.config/starship.toml"
  say "~/.config/starship.toml"
else
  skip "starship not installed, skipped"
fi

step "vivid"
if have vivid; then
  mkdir -p "$HOME/.config/vivid/themes"
  cp "$DIST/vivid/"*.yml "$HOME/.config/vivid/themes/"
  say "themes installed, theme.zsh sets LS_COLORS from them"
else
  skip "vivid not installed, skipped"
fi

step "zsh"
mkdir -p "$HOME/.config/nullglow"
cp "$DIST/zsh/$VARIANT-theme.zsh"    "$HOME/.config/nullglow/theme.zsh"
cp "$DIST/delta/$VARIANT.gitconfig"  "$HOME/.config/nullglow/delta.gitconfig"
say "~/.config/nullglow/theme.zsh"
say "it sets bat, LS_COLORS, fzf, highlighting, completion and history colours"

step "Terminal.app"
# Two steps, because neither one can do the whole job. The .terminal file
# carries the colours, since Terminal's scripting API has no ANSI colour
# properties. The AppleScript then makes it the default and sets the font,
# which the file cannot do reliably. Writing profiles straight into Terminal's
# preferences with `defaults` does not work: Terminal ignores profiles it did
# not import and strips unknown keys from any it rewrites.
# Filename must equal the profile name: Terminal takes the profile's name from
# the filename and ignores the "name" key inside the file.
TERM_FILE="$DIST/terminal-app/$LABEL.terminal"
TERM_SCRIPT="$DIST/terminal-app/$VARIANT.applescript"
if [[ "$(uname)" != "Darwin" ]]; then
  skip "not macOS, skipped"
elif [[ ! -f "$TERM_FILE" ]]; then
  skip "no profile for this variant, skipped"
else
  open "$TERM_FILE" && say "imported $(basename "$TERM_FILE")"
  # Terminal needs a moment to register the profile before we can address it.
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    osascript -e "tell application \"Terminal\" to exists settings set \"$LABEL\"" 2>/dev/null \
      | grep -q true && break
  done
  if osascript "$TERM_SCRIPT" >/dev/null 2>&1; then
    say "set as the default profile, font applied"
  else
    say "imported, but couldn't set it as default automatically."
    say "Terminal > Settings > Profiles > $LABEL > Default"
  fi
fi

# ── the two lines you add once, and never again ──────────────────────────────

cat <<EOF

$(printf '\033[1mAdd to the END of ~/.zshrc, once\033[0m')

  source ~/.config/nullglow/theme.zsh

$(printf '\033[1mAdd to ~/.gitconfig, once\033[0m')

  [include]
      path = ~/.config/nullglow/delta.gitconfig

$(printf '\033[2mAfter that, switching variants is just re-running this script.\033[0m')

EOF

# ── egg ──────────────────────────────────────────────────────────────────────

printf '\033[38;2;43;245;155m'
cat <<'EOF'
           .-"""-.
          /  o o  \
         |    >    |    nullglow
          \  ---  /
           '-...-'
EOF
printf '\033[0m\n'
