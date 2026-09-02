# Installing Nullglow

The short version:

```sh
git clone https://github.com/mahoudeau/nullglow.git
cd nullglow
./install.sh          # Nullglow
./install.sh --neon   # Nullglow Neon
```

Then add two lines, once, and you're done. The script prints them and they're below.

Everything after this is detail: what the script touches, what it deliberately won't
touch, and how to undo it.

## What the script does

| It does | It doesn't |
|---|---|
| copies the VS Code extension into `~/.vscode/extensions/` | pick the theme for you, VS Code needs a click |
| registers both bat themes and rebuilds bat's cache | |
| writes `~/.config/starship.toml`, backing up the old one | |
| installs the vivid themes | |
| writes `~/.config/nullglow/theme.zsh` and `delta.gitconfig` | edit your `.zshrc` or `.gitconfig` |
| installs the Terminal.app profile and makes it default | anything, if Terminal.app is open |

Anything it overwrites is copied to `.backup/` in the repo first.

## The two lines

**`~/.zshrc`**, at the very end:

```zsh
source ~/.config/nullglow/theme.zsh
```

It has to be last. It sets styles that `compinit` and the zsh plugins own, so it has to
run after them. This one file covers bat, `LS_COLORS`, fzf, syntax highlighting,
autosuggestions, the completion menu and history search.

**`~/.gitconfig`**:

```ini
[include]
    path = ~/.config/nullglow/delta.gitconfig
```

Put it after any `[delta]` section of your own, since later values win.

Once those two lines are in, they never change again. Switching between Nullglow and
Nullglow Neon is re-running `./install.sh --neon` and opening a new terminal.

## VS Code

The extension carries both variants. After installing, reload the window
(`Cmd-Shift-P`, "Reload Window"), then `Cmd-K Cmd-T` and pick **Nullglow** or
**Nullglow Neon**.

One setting is worth adding yourself:

```json
"terminal.integrated.minimumContrastRatio": 1
```

VS Code otherwise rewrites terminal colours to force a contrast ratio, which undoes the
tuning. Setting it to 1 leaves them alone.

## Terminal.app

It takes two steps and the script does both, because neither one is enough on its own.

1. **Import the colours.** `open "dist/terminal-app/Nullglow.terminal"`. Terminal adds it
   to your profiles.
2. **Make it the default and set the font.** `osascript dist/terminal-app/nullglow.applescript`.

The split isn't arbitrary. Terminal's AppleScript API has properties for the background,
text, bold and cursor colours, and **none at all for the 16 ANSI colours**, so those have
to arrive in the file. The file in turn can't reliably make itself the default profile.

### By hand

Double-click the `.terminal` file, then Terminal > Settings > Profiles, select the
profile, and click **Default** at the bottom. Without that click it applies only to the
window that just opened, not to new ones.

### Things that will waste your afternoon

- **The filename becomes the profile name.** Terminal takes the name from the file, not
  from the `name` key inside it. Rename `Nullglow Neon.terminal` to `NullglowNeon.terminal`
  and you get a profile called `NullglowNeon`, which the AppleScript then can't find.
- **Don't write profiles with `defaults`.** They land in the preferences file and Terminal
  ignores them. It only loads profiles it imported itself, and it strips unknown keys from
  any profile it rewrites.
- **Terminal rewrites its preferences when it quits.** Anything you edit in that file
  while it's running is discarded.
- **An app with no windows is still running.** Closing the last Terminal window does not
  quit Terminal.
- **`plutil -lint` proves nothing here.** A `.terminal` file can be a perfectly valid
  plist and still be refused as damaged. The profile has to match the shape Terminal
  expects: colours only, no `Font` key, no cursor or scrollback keys.
  `python3 build.py --check` diffs the generated file against `tests/reference.terminal`,
  a known-working profile, and fails if the key set drifts.

## iTerm2

Settings > Profiles > Colors > Color Presets > Import, then choose
`dist/iterm2/Nullglow.itermcolors`, then select it from the same menu.

I don't use iTerm2, so this path is untested. Open an issue if it's wrong.

## A Nerd Font helps

The starship prompt uses branch and language glyphs. Without a Nerd Font you get empty
boxes. Any of them work:

```sh
brew install --cask font-jetbrains-mono-nerd-font
```

Then set your terminal and `terminal.integrated.fontFamily` to `JetBrainsMono NF`. Note
the name Homebrew registers is `JetBrainsMono NF`, not `JetBrainsMono Nerd Font`, and
picking the wrong one falls back silently to a font with no glyphs.

## Undoing it

```sh
./install.sh --uninstall
```

That removes the extension, the bat and vivid themes, `~/.config/nullglow/`, the
Terminal.app profiles, and restores anything in `.backup/`. It can't remove the two lines
you added to `.zshrc` and `.gitconfig`, so delete those yourself.

## Checking a variant before you install it

```sh
python3 build.py --check
```

Prints the contrast ratio of every colour against the background, the closest pair of
accents, and the closest pair under simulated colour blindness. It exits non-zero if
anything is below threshold.
