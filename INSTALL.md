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

The script handles this, but **only when Terminal.app is closed**. Terminal rewrites its
own preferences when it quits, so anything written while it's running gets thrown away.

If it was open, quit it (`Cmd-Q`) and run `./install.sh` again.

### If you'd rather do it by hand

Double-click `dist/terminal-app/Nullglow.terminal`, then Terminal > Settings > Profiles,
select Nullglow, and click **Default** at the bottom of the list. Without that last click
the profile is only used by the window that just opened, not by new ones.

### "The file is damaged"

Older versions of this repo shipped a `ProfileCurrentVersion` that current macOS refuses
to migrate, and Terminal reported the file as damaged. Pull the latest and rebuild:

```sh
git pull && python3 build.py
```

If it still fails, skip the file entirely and write the profile straight into Terminal's
preferences, with Terminal closed:

```sh
defaults write com.apple.Terminal "Window Settings" -dict-add "Nullglow Neon" \
  "$(plutil -convert xml1 -o - dist/terminal-app/NullglowNeon.terminal)"
defaults write com.apple.Terminal "Default Window Settings" -string "Nullglow Neon"
defaults write com.apple.Terminal "Startup Window Settings" -string "Nullglow Neon"
```

That's what `install.sh` does, and it skips Terminal's import parser.

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
