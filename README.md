# Nullglow

Near-black cyberpunk for the terminal and the editor — **tuned, not eyeballed**.

Two variants. Every colour in both clears WCAG AA against the background, and every
pair of accents stays distinguishable to a colour-blind reader. The theme ships a
checker that proves it.

### Nullglow

![Nullglow](dist/preview/nullglow.svg)

### Nullglow Neon

![Nullglow Neon](dist/preview/nullglow-neon.svg)

Same neutrals, accents pushed to the highest chroma that still satisfies every
constraint. Neon is the louder one; Nullglow is easier over a long session.

---

## Why another dark theme

Most themes pick colours by eye and hope. This one derives them from three rules:

| Rule | Threshold | Why |
|---|---|---|
| Contrast against the background | ≥ 4.5:1 (WCAG AA) | including `comment`, which most themes let fail |
| Perceptual distance between accents | ΔE ≥ 25 | so two roles never read as the same colour |
| Distance under simulated deuteranopia | ΔE ≥ 18 | so red/green deficiency doesn't collapse the palette |

Neon's values came from searching 240,000 candidates for the most saturated palette
that satisfies all three. The result is *more* vivid than the hand-picked palette it
replaced (mean CIELAB chroma 81.7 vs 70.6) and fails none of the checks.

Run the checker yourself:

```console
$ python3 build.py --check
── Nullglow ──
  contrast against ground (#060b09), need >= 4.5:1
    comment  #6e7d71    4.56:1  pass
    ...
  accent separation, need ΔE >= 25
    worst pair: pink/red  ΔE 40.5  pass
  separation under deuteranopia, need ΔE >= 18
    worst pair: cyan/purple  ΔE 22.8  pass
  verified
...
All variants meet the spec.
```

It exits non-zero if a value ever regresses.

## Roles, not colours

A colour is defined once, as a *role*, and means the same thing everywhere:

| Role | Nullglow | Neon | Means |
|---|---|---|---|
| `green` | `#2bf59b` | `#05f98b` | functions, prompt arrow, additions |
| `pink` | `#ff4d9e` | `#f81578` | keywords, git-dirty, deletions |
| `cyan` | `#5ce6e0` | `#45fdf3` | types, links, timestamps |
| `blue` | `#48b8f5` | `#0690fc` | paths, properties |
| `purple` | `#d79bff` | `#c312f9` | constants, untracked |
| `yellow` | `#f5d76b` | `#fcc60b` | strings, command duration |
| `red` | `#ff5c5c` | `#fe1115` | errors only |
| `ground` | `#060b09` | `#060b09` | background |
| `fg` | `#cfd8d3` | `#cfd8d3` | body text |
| `comment` | `#6e7d71` | `#6e7d71` | comments, ghost text |

Pink means *deleted* in a diff, *dirty* in the prompt and *keyword* in the editor.
That consistency is why everything is generated from one file rather than
maintained by hand.

## What's included

| Target | File | Verified |
|---|---|---|
| VS Code | `dist/vscode/` | yes — both variants in the picker |
| Terminal.app | `dist/terminal-app/*.terminal` | yes |
| iTerm2 | `dist/iterm2/*.itermcolors` | **no** — not installed on the author's machine; lints clean only |
| bat | `dist/bat/*.tmTheme` | yes |
| delta | `dist/delta/*.gitconfig` | yes |
| starship | `dist/starship/*.toml` | yes |
| fzf | `dist/fzf/*.sh` | yes |
| vivid → `LS_COLORS` | `dist/vivid/*.yml` | yes |
| zsh-syntax-highlighting | `dist/zsh/*-highlight.zsh` | yes |

## Install

```sh
git clone https://github.com/mahoudeau/nullglow.git
cd nullglow
./install.sh          # Nullglow
./install.sh --neon   # Nullglow Neon
```

The installer backs up anything it overwrites into `.backup/`, skips tools you don't
have, and **never edits your shell rc or gitconfig** — it prints the lines to paste.
`./install.sh --uninstall` reverses everything and restores the backups.

### By hand

<details>
<summary>Per-tool instructions</summary>

**VS Code** — copy `dist/vscode/` to `~/.vscode/extensions/nullglow-theme/`, reload the
window, then pick the theme.

**bat** — copy `dist/bat/*.tmTheme` into `$(bat --config-dir)/themes/`, run
`bat cache --build`, then `export BAT_THEME="Nullglow"`. bat takes the theme name from
the *filename*, so keep the spaces.

**delta** — add to `~/.gitconfig`:
```ini
[include]
    path = /path/to/nullglow/dist/delta/nullglow.gitconfig
```
delta reads its syntax theme from bat, so install the bat theme first.

**starship** — copy `dist/starship/nullglow.toml` to `~/.config/starship.toml`.

**vivid** — copy `dist/vivid/*.yml` into `~/.config/vivid/themes/`, then
`export LS_COLORS="$(vivid generate nullglow)"`.

**fzf / zsh** — source `dist/fzf/nullglow.sh` and `dist/zsh/nullglow-highlight.zsh`
from your `.zshrc`. Source the highlight file *after* the zsh plugins load.

**Terminal.app** — double-click `dist/terminal-app/Nullglow.terminal`, then
Terminal → Settings → Profiles → Nullglow → Default.

**iTerm2** — Settings → Profiles → Colors → Color Presets → Import, then choose
`dist/iterm2/Nullglow.itermcolors`. Untested; please open an issue if it's wrong.

</details>

## Build from source

`dist/` is committed, so nothing is required to *use* the theme. To change a colour,
edit `palette.json` and regenerate — Python 3.9+, standard library only:

```sh
python3 build.py          # regenerate every target
python3 build.py --check  # re-verify the accessibility claims
```

Adding a platform means writing one emitter in `build.py`. Pull requests welcome —
especially for the targets marked unverified above.

## Credits

The aesthetic direction came from [0daybeats.com](https://www.0daybeats.com), whose
palette started this. **No colour value is taken from it** — every value here was
re-derived under the constraints above, and the search explicitly excludes their
exact values. Credit where it's due for the inspiration.

Thanks to [hardhackerlabs/themes](https://github.com/hardhackerlabs/themes) for
demonstrating that a cyberpunk theme can take accessibility seriously.

## License

MIT — see [LICENSE](LICENSE).
