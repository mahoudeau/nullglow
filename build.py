#!/usr/bin/env python3
"""
Nullglow theme generator.

Reads palette.json and writes every target under dist/. Standard library only. No
toolchain, no node_modules, no build step for anyone installing the theme.

    python3 build.py            regenerate dist/
    python3 build.py --check    re-verify the accessibility claims and exit

A role ("pink means git-dirty and deletions") is defined once here and stays the
same in the editor, the prompt and the diff. Theme repos kept by hand drift.
"""

import colorsys
import hashlib
import json
import math
import os
import plistlib
import sys
from plistlib import UID

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")


# ─────────────────────────────────────────────────────────────────────────────
# colour helpers
# ─────────────────────────────────────────────────────────────────────────────

def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb2hex(rgb):
    return "#%02x%02x%02x" % tuple(min(255, max(0, round(c * 255))) for c in rgb)


def lighten(h, amount):
    """Move a colour toward white in HLS space."""
    r, g, b = hex2rgb(h)
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    return rgb2hex(colorsys.hls_to_rgb(hh, min(1.0, ll + (1 - ll) * amount), ss))


def mix(a, b, t):
    """Linear blend of two colours; t=0 returns a, t=1 returns b."""
    ra, rb = hex2rgb(a), hex2rgb(b)
    return rgb2hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def alpha(h, a):
    """#rrggbb + float alpha -> #rrggbbaa, for the VS Code theme."""
    return h + "%02x" % min(255, max(0, round(a * 255)))


def relative_luminance(h):
    def f(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = map(f, hex2rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def to_lab(h):
    def f(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = map(f, hex2rgb(h))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def k(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = k(x), k(y), k(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(to_lab(a), to_lab(b))))


def deuteranopia(h):
    """Rough deuteranopia simulation, good enough to catch collisions."""
    r, g, b = (c * 255 for c in hex2rgb(h))
    return rgb2hex((
        (0.625 * r + 0.375 * g) / 255,
        (0.700 * g + 0.300 * r) / 255,
        (0.300 * g + 0.700 * b) / 255,
    ))


# ─────────────────────────────────────────────────────────────────────────────
# palette
# ─────────────────────────────────────────────────────────────────────────────

class Palette(object):
    """Roles plus everything derived from them."""

    ACCENTS = ("green", "pink", "cyan", "blue", "purple", "yellow", "red")

    def __init__(self, slug, spec, derive, meta):
        self.meta = meta
        self.slug = slug
        self.label = spec.get("label", meta["name"])
        self.file = self.label.replace(" ", "")
        for role, value in spec.items():
            if not role.startswith("$") and role != "label":
                setattr(self, role, value)

        amount = derive["bright_lighten"]
        self.ansi = {name: getattr(self, role) for name, role in derive["ansi"].items()}
        self.bright = {name: lighten(value, amount) for name, value in self.ansi.items()}
        self.bright["black"] = lighten(getattr(self, derive["bright_black_from"]), amount)

        # surfaces derived from the ground so they always sit in the same family
        self.selection = alpha(self.green, 0.22)
        self.highlight = alpha(self.green, 0.12)
        self.overlay = mix(self.ground, self.fg, 0.06)


# ─────────────────────────────────────────────────────────────────────────────
# emitters
# ─────────────────────────────────────────────────────────────────────────────

def write(path, data, binary=False):
    full = os.path.join(DIST, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    mode = "wb" if binary else "w"
    with open(full, mode) as fh:
        fh.write(data)
    size = os.path.getsize(full)
    print("  %-44s %6d B" % (path, size))


def emit_vscode(p):
    c = {
        "editor.background": p.ground,
        "editor.foreground": p.fg,
        "editor.lineHighlightBackground": p.surface,
        "editor.selectionBackground": p.selection,
        "editor.selectionHighlightBackground": p.highlight,
        "editor.inactiveSelectionBackground": alpha(p.green, 0.08),
        "editor.wordHighlightBackground": alpha(p.cyan, 0.12),
        "editor.wordHighlightStrongBackground": alpha(p.green, 0.15),
        "editor.findMatchBackground": alpha(p.pink, 0.33),
        "editor.findMatchHighlightBackground": alpha(p.pink, 0.15),
        "editor.hoverHighlightBackground": alpha(p.cyan, 0.10),
        "editor.rangeHighlightBackground": p.highlight,
        "editorCursor.foreground": p.cursor,
        "editorWhitespace.foreground": p.line,
        "editorIndentGuide.background1": p.line,
        "editorIndentGuide.activeBackground1": alpha(p.green, 0.25),
        "editorLineNumber.foreground": p.comment,
        "editorLineNumber.activeForeground": p.green,
        "editorRuler.foreground": p.line,
        "editorBracketMatch.background": alpha(p.green, 0.15),
        "editorBracketMatch.border": alpha(p.green, 0.50),
        "editorBracketHighlight.foreground1": p.green,
        "editorBracketHighlight.foreground2": p.pink,
        "editorBracketHighlight.foreground3": p.cyan,
        "editorBracketHighlight.foreground4": p.purple,
        "editorBracketHighlight.foreground5": p.yellow,
        "editorBracketHighlight.foreground6": p.blue,
        "editorBracketHighlight.unexpectedBracket.foreground": p.red,

        "editorError.foreground": p.red,
        "editorWarning.foreground": p.yellow,
        "editorInfo.foreground": p.blue,
        "editorHint.foreground": p.green,
        "editorGutter.addedBackground": p.green,
        "editorGutter.modifiedBackground": p.blue,
        "editorGutter.deletedBackground": p.pink,
        "editorOverviewRuler.border": alpha(p.ground, 0.0),
        "editorOverviewRuler.addedForeground": alpha(p.green, 0.6),
        "editorOverviewRuler.modifiedForeground": alpha(p.blue, 0.6),
        "editorOverviewRuler.deletedForeground": alpha(p.pink, 0.6),
        "editorOverviewRuler.errorForeground": p.red,
        "editorOverviewRuler.warningForeground": p.yellow,

        "diffEditor.insertedTextBackground": alpha(p.green, 0.12),
        "diffEditor.removedTextBackground": alpha(p.pink, 0.12),
        "diffEditor.insertedLineBackground": alpha(p.green, 0.08),
        "diffEditor.removedLineBackground": alpha(p.pink, 0.08),

        "editorWidget.background": p.surface,
        "editorWidget.border": p.line,
        "editorSuggestWidget.background": p.surface,
        "editorSuggestWidget.border": p.line,
        "editorSuggestWidget.foreground": p.fg,
        "editorSuggestWidget.highlightForeground": p.green,
        "editorSuggestWidget.selectedBackground": alpha(p.green, 0.15),
        "editorHoverWidget.background": p.surface,
        "editorHoverWidget.border": p.line,
        "editorGhostText.foreground": p.comment,

        "peekView.border": alpha(p.green, 0.40),
        "peekViewEditor.background": p.surface,
        "peekViewEditor.matchHighlightBackground": alpha(p.pink, 0.25),
        "peekViewResult.background": p.surface,
        "peekViewResult.selectionBackground": alpha(p.green, 0.15),
        "peekViewTitle.background": p.surface,

        "foreground": p.fg,
        "descriptionForeground": p.fg_dim,
        "errorForeground": p.red,
        "focusBorder": alpha(p.green, 0.40),
        "widget.shadow": "#00000080",
        "selection.background": p.selection,

        "activityBar.background": p.ground,
        "activityBar.foreground": p.green,
        "activityBar.inactiveForeground": p.comment,
        "activityBar.border": p.line,
        "activityBarBadge.background": p.green,
        "activityBarBadge.foreground": p.ground,

        "sideBar.background": p.surface,
        "sideBar.foreground": p.fg_dim,
        "sideBar.border": p.line,
        "sideBarTitle.foreground": p.green,
        "sideBarSectionHeader.background": p.overlay,
        "sideBarSectionHeader.foreground": p.fg,
        "sideBarSectionHeader.border": p.line,

        "list.activeSelectionBackground": alpha(p.green, 0.12),
        "list.activeSelectionForeground": p.green,
        "list.inactiveSelectionBackground": p.overlay,
        "list.inactiveSelectionForeground": p.fg,
        "list.hoverBackground": p.overlay,
        "list.hoverForeground": p.fg,
        "list.highlightForeground": p.cyan,
        "list.focusBackground": alpha(p.green, 0.15),
        "list.errorForeground": p.red,
        "list.warningForeground": p.yellow,
        "tree.indentGuidesStroke": p.line,

        "statusBar.background": p.surface,
        "statusBar.foreground": p.fg_dim,
        "statusBar.border": p.line,
        "statusBar.noFolderBackground": p.surface,
        "statusBar.debuggingBackground": p.pink,
        "statusBar.debuggingForeground": p.ground,
        "statusBarItem.remoteBackground": p.green,
        "statusBarItem.remoteForeground": p.ground,
        "statusBarItem.hoverBackground": alpha(p.green, 0.12),

        "titleBar.activeBackground": p.ground,
        "titleBar.activeForeground": p.fg,
        "titleBar.inactiveBackground": p.ground,
        "titleBar.inactiveForeground": p.comment,
        "titleBar.border": p.line,

        "menu.background": p.surface,
        "menu.foreground": p.fg,
        "menu.selectionBackground": alpha(p.green, 0.15),
        "menu.selectionForeground": p.green,
        "menu.separatorBackground": p.line,
        "menubar.selectionBackground": alpha(p.green, 0.12),

        "editorGroup.border": p.line,
        "editorGroupHeader.tabsBackground": p.surface,
        "editorGroupHeader.tabsBorder": p.line,
        "tab.activeBackground": p.ground,
        "tab.activeForeground": p.green,
        "tab.activeBorderTop": p.green,
        "tab.inactiveBackground": p.surface,
        "tab.inactiveForeground": p.comment,
        "tab.border": p.line,
        "tab.hoverForeground": p.fg,
        "tab.unfocusedActiveForeground": p.fg_dim,

        "panel.background": p.ground,
        "panel.border": p.line,
        "panelTitle.activeForeground": p.green,
        "panelTitle.activeBorder": p.green,
        "panelTitle.inactiveForeground": p.comment,

        "input.background": p.surface,
        "input.foreground": p.fg,
        "input.border": p.line,
        "input.placeholderForeground": p.comment,
        "inputOption.activeBorder": p.green,
        "inputOption.activeBackground": alpha(p.green, 0.15),
        "inputValidation.errorBackground": mix(p.ground, p.red, 0.18),
        "inputValidation.errorBorder": p.red,
        "inputValidation.warningBackground": mix(p.ground, p.yellow, 0.15),
        "inputValidation.warningBorder": p.yellow,
        "inputValidation.infoBackground": mix(p.ground, p.blue, 0.15),
        "inputValidation.infoBorder": p.blue,

        "dropdown.background": p.surface,
        "dropdown.foreground": p.fg,
        "dropdown.border": p.line,

        "button.background": p.green,
        "button.foreground": p.ground,
        "button.hoverBackground": lighten(p.green, 0.18),
        "button.secondaryBackground": p.surface,
        "button.secondaryForeground": p.fg,

        "badge.background": p.green,
        "badge.foreground": p.ground,
        "progressBar.background": p.green,

        "scrollbarSlider.background": alpha(p.line, 0.60),
        "scrollbarSlider.hoverBackground": alpha(p.green, 0.20),
        "scrollbarSlider.activeBackground": alpha(p.green, 0.33),

        "breadcrumb.foreground": p.comment,
        "breadcrumb.focusForeground": p.green,
        "breadcrumb.background": p.ground,

        "gitDecoration.addedResourceForeground": p.green,
        "gitDecoration.modifiedResourceForeground": p.blue,
        "gitDecoration.deletedResourceForeground": p.pink,
        "gitDecoration.untrackedResourceForeground": p.purple,
        "gitDecoration.ignoredResourceForeground": p.comment,
        "gitDecoration.conflictingResourceForeground": p.yellow,

        "notificationCenterHeader.background": p.surface,
        "notifications.background": p.surface,
        "notifications.border": p.line,
        "notificationLink.foreground": p.cyan,

        "textLink.foreground": p.cyan,
        "textLink.activeForeground": p.green,
        "textPreformat.foreground": p.yellow,
        "textBlockQuote.background": p.surface,
        "textCodeBlock.background": p.surface,

        "minimap.findMatchHighlight": p.pink,
        "minimapGutter.addedBackground": p.green,
        "minimapGutter.modifiedBackground": p.blue,
        "minimapGutter.deletedBackground": p.pink,

        "terminal.background": p.ground,
        "terminal.foreground": p.fg,
        "terminalCursor.foreground": p.cursor,
        "terminalCursor.background": p.ground,
        "terminal.selectionBackground": p.selection,
    }
    for name, value in p.ansi.items():
        c["terminal.ansi" + name.capitalize()] = value
    for name, value in p.bright.items():
        c["terminal.ansiBright" + name.capitalize()] = value

    def tok(name, scopes, fg=None, style=None):
        settings = {}
        if fg:
            settings["foreground"] = fg
        if style:
            settings["fontStyle"] = style
        return {"name": name, "scope": scopes, "settings": settings}

    tokens = [
        tok("Comment", ["comment", "punctuation.definition.comment"], p.comment, "italic"),
        tok("Variables", ["variable", "variable.other.readwrite", "meta.definition.variable"], p.fg),
        tok("Language constants", ["variable.language", "constant.language", "support.constant"], p.purple, "italic"),
        tok("Numbers and constants", ["constant.numeric", "constant.character", "constant.escape", "constant.other"], p.purple),
        tok("Strings", ["string", "string.quoted", "punctuation.definition.string"], p.yellow),
        tok("Template expressions and regex", ["string.template", "string.regexp", "meta.template.expression"], p.cyan),
        tok("Keywords and storage", ["keyword", "keyword.control", "storage", "storage.type", "storage.modifier"], p.pink),
        tok("Operators and punctuation", ["keyword.operator", "punctuation", "meta.brace"], p.fg_dim),
        tok("Functions", ["entity.name.function", "support.function", "meta.function-call", "variable.function"], p.green),
        tok("Types and classes", ["entity.name.type", "entity.name.class", "entity.name.namespace",
                                  "support.type", "support.class", "entity.other.inherited-class"], p.cyan),
        tok("Parameters", ["variable.parameter", "meta.parameter"], p.fg, "italic"),
        tok("Properties", ["variable.other.property", "variable.other.object.property",
                           "support.variable.property", "meta.object-literal.key"], p.blue),
        tok("Tags", ["entity.name.tag", "punctuation.definition.tag"], p.pink),
        tok("Attributes", ["entity.other.attribute-name"], p.green, "italic"),
        tok("CSS properties", ["support.type.property-name.css", "meta.property-name"], p.cyan),
        tok("CSS selectors", ["entity.other.attribute-name.class.css",
                              "entity.other.attribute-name.id.css", "entity.name.tag.css"], p.green),
        tok("JSON keys", ["support.type.property-name.json"], p.green),
        tok("Markdown headings", ["markup.heading", "entity.name.section"], p.green, "bold"),
        tok("Markdown bold", ["markup.bold"], p.yellow, "bold"),
        tok("Markdown italic", ["markup.italic"], p.purple, "italic"),
        tok("Markdown links", ["markup.underline.link", "string.other.link"], p.cyan, "underline"),
        tok("Markdown code", ["markup.inline.raw", "markup.fenced_code", "markup.raw"], p.cyan),
        tok("Diff inserted", ["markup.inserted"], p.green),
        tok("Diff deleted", ["markup.deleted"], p.pink),
        tok("Diff changed", ["markup.changed"], p.blue),
        tok("Invalid", ["invalid", "invalid.illegal"], p.red, "underline"),
        tok("Deprecated", ["invalid.deprecated"], p.yellow, "strikethrough"),
    ]

    theme = {
        "name": p.label,
        "type": p.meta["type"],
        "semanticHighlighting": True,
        "colors": c,
        "tokenColors": tokens,
    }
    write("vscode/themes/%s-color-theme.json" % p.slug, json.dumps(theme, indent=2) + "\n")


def emit_vscode_package(palettes, meta):
    """One extension contributing every variant, so both appear in the picker."""
    pkg = {
        "name": meta["slug"] + "-theme",
        "displayName": meta["name"],
        "description": meta["description"],
        "version": meta["version"],
        "publisher": meta["author"],
        "license": meta["license"],
        "repository": {"type": "git", "url": meta["homepage"] + ".git"},
        "engines": {"vscode": "^1.70.0"},
        "categories": ["Themes"],
        "keywords": ["theme", "dark", "cyberpunk", "neon", "accessible", "wcag"],
        "contributes": {
            "themes": [{
                "label": p.label,
                "uiTheme": "vs-dark",
                "path": "./themes/%s-color-theme.json" % p.slug,
            } for p in palettes]
        },
    }
    write("vscode/package.json", json.dumps(pkg, indent=2) + "\n")


def _ns_color(h):
    """An NSColor inside an NSKeyedArchiver blob, which is what .terminal wants."""
    r, g, b = hex2rgb(h)
    return plistlib.dumps({
        "$version": 100000,
        "$archiver": "NSKeyedArchiver",
        "$top": {"root": UID(1)},
        "$objects": [
            "$null",
            {"$class": UID(2), "NSColorSpace": 1,
             "NSRGB": ("%.6f %.6f %.6f" % (r, g, b)).encode() + b"\x00"},
            {"$classes": ["NSColor", "NSObject"], "$classname": "NSColor"},
        ],
    }, fmt=plistlib.FMT_BINARY)


def _ns_font(name, size):
    return plistlib.dumps({
        "$version": 100000,
        "$archiver": "NSKeyedArchiver",
        "$top": {"root": UID(1)},
        "$objects": [
            "$null",
            {"$class": UID(3), "NSName": UID(2), "NSSize": size, "NSfFlags": 16},
            name,
            {"$classes": ["NSFont", "NSObject"], "$classname": "NSFont"},
        ],
    }, fmt=plistlib.FMT_BINARY)


def emit_terminal_app(p):
    prof = {
        "name": p.label,
        "type": "Window Settings",
        # Match what current macOS writes. Ship an older number and Terminal
        # tries to migrate the profile on import, fails, and reports the file
        # as damaged.
        "ProfileCurrentVersion": 2.09,
        "BackgroundColor": _ns_color(p.ground),
        "TextColor": _ns_color(p.fg),
        "TextBoldColor": _ns_color(p.fg),
        "CursorColor": _ns_color(p.cursor),
        "SelectionColor": _ns_color(p.line),
        "Font": _ns_font("JetBrainsMonoNF-Regular", 14),
        "FontAntialias": True,
        "fontAllowsDisableAntialias": 0,
        "FontWidthSpacing": 1.0,
        "FontHeightSpacing": 1.15,
        "columnCount": 120,
        "rowCount": 34,
        "CursorType": 2,
        "CursorBlink": True,
        "ShowActiveProcessInTitle": True,
        "ShowWindowSettingsNameInTitle": False,
        "ShowDimensionsInTitle": False,
        "ShowShellCommandInTitle": False,
        "ShowRepresentedURLInTitle": False,
        "useOptionAsMetaKey": True,
        "ScrollbackLines": 20000,
        "ShouldLimitScrollback": 0,
        "BlinkText": False,
        "UseBrightBold": True,
    }
    order = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
    for name in order:
        prof["ANSI%sColor" % name.capitalize()] = _ns_color(p.ansi[name])
        prof["ANSIBright%sColor" % name.capitalize()] = _ns_color(p.bright[name])
    write("terminal-app/%s.terminal" % p.file, plistlib.dumps(prof), binary=True)


def emit_iterm2(p):
    def comp(h):
        r, g, b = hex2rgb(h)
        return {"Color Space": "sRGB", "Red Component": r,
                "Green Component": g, "Blue Component": b, "Alpha Component": 1.0}

    out = {
        "Background Color": comp(p.ground),
        "Foreground Color": comp(p.fg),
        "Bold Color": comp(p.fg),
        "Cursor Color": comp(p.cursor),
        "Cursor Text Color": comp(p.ground),
        "Selection Color": comp(p.line),
        "Selected Text Color": comp(p.fg),
        "Link Color": comp(p.cyan),
        "Badge Color": comp(p.pink),
    }
    order = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
    for i, name in enumerate(order):
        out["Ansi %d Color" % i] = comp(p.ansi[name])
        out["Ansi %d Color" % (i + 8)] = comp(p.bright[name])
    write("iterm2/%s.itermcolors" % p.file, plistlib.dumps(out, fmt=plistlib.FMT_XML), binary=True)


def emit_bat(p):
    def rule(name, scope, fg, style=None):
        s = {"foreground": fg}
        if style:
            s["fontStyle"] = style
        return {"name": name, "scope": scope, "settings": s}

    settings = [
        {"settings": {"background": p.ground, "foreground": p.fg,
                      "caret": p.cursor, "lineHighlight": p.surface,
                      "selection": p.line, "invisibles": p.line}},
        rule("Comment", "comment", p.comment, "italic"),
        rule("String", "string", p.yellow),
        rule("Number", "constant.numeric", p.purple),
        rule("Constant", "constant", p.purple),
        rule("Keyword", "keyword, storage, storage.type", p.pink),
        rule("Operator", "keyword.operator, punctuation", p.fg_dim),
        rule("Function", "entity.name.function, support.function", p.green),
        rule("Class", "entity.name.type, entity.name.class, support.type, support.class", p.cyan),
        rule("Variable", "variable", p.fg),
        rule("Parameter", "variable.parameter", p.fg, "italic"),
        rule("Property", "variable.other.property, meta.object-literal.key", p.blue),
        rule("Tag", "entity.name.tag", p.pink),
        rule("Attribute", "entity.other.attribute-name", p.green, "italic"),
        rule("Heading", "markup.heading", p.green, "bold"),
        rule("Link", "markup.underline.link", p.cyan, "underline"),
        rule("Inserted", "markup.inserted", p.green),
        rule("Deleted", "markup.deleted", p.pink),
        rule("Changed", "markup.changed", p.blue),
        rule("Invalid", "invalid", p.red),
    ]
    theme = {"name": p.label, "settings": settings,
             # stable across runs. hash() is salted per process, which would
             # make dist/ differ on every build
             "uuid": "7f9c1a2e-4b6d-4f18-9c3a-%012x"
                     % (int(hashlib.md5(p.slug.encode()).hexdigest()[:12], 16)),
             "colorSpaceName": "sRGB"}
    # bat derives the theme name from the FILENAME, not the plist "name" key,
    # so this must match what delta's syntax-theme and BAT_THEME expect.
    write("bat/%s.tmTheme" % p.label, plistlib.dumps(theme, fmt=plistlib.FMT_XML), binary=True)


def emit_starship(p):
    # NB: the body contains starship's own ${count} placeholders, so it must not
    # go through .format(). Only the palette block below is substituted.
    body = """# Nullglow for starship. https://github.com/mahoudeau/nullglow
# Generated by build.py. Copy to ~/.config/starship.toml

"$schema" = 'https://starship.rs/config-schema.json'

palette = '__SLUG__'
add_newline = true

format = \"\"\"
$directory\\
$git_branch\\
$git_state\\
$git_status\\
$nodejs$bun$deno$python$rust$golang$java$ruby$php$lua$docker_context\\
$cmd_duration\\
$line_break\\
$character\"\"\"

right_format = \"\"\"$status$jobs$time\"\"\"

[character]
success_symbol = "[➜](bold green)"
error_symbol = "[➜](bold red)"
vicmd_symbol = "[❮](bold yellow)"

[directory]
style = "bold blue"
format = "[$path]($style)[$read_only]($read_only_style) "
truncation_length = 3
truncate_to_repo = true
truncation_symbol = "…/"
read_only = " \U000f033e"
read_only_style = "red"

[git_branch]
symbol = " "
style = "bold purple"
format = "on [$symbol$branch]($style) "
truncation_length = 24

[git_status]
style = "bold pink"
format = '([\\[$all_status$ahead_behind\\]]($style) )'
ahead = "⇡${count}"
behind = "⇣${count}"
diverged = "⇕⇡${ahead_count}⇣${behind_count}"
untracked = "?${count}"
stashed = "\U000f03d7 ${count}"
modified = "!${count}"
staged = "+${count}"
renamed = "»${count}"
deleted = "✘${count}"

[git_state]
style = "bold yellow"
format = '\\([$state( $progress_current/$progress_total)]($style)\\) '

[cmd_duration]
min_time = 2_000
format = "took [$duration]($style) "
style = "bold yellow"

[status]
disabled = false
style = "bold red"
symbol = "✘ "
format = '[$symbol$status]($style) '
map_symbol = true

[jobs]
symbol = " "
style = "bold blue"
number_threshold = 1
format = "[$symbol$number]($style) "

[time]
disabled = false
format = "[$time]($style)"
time_format = "%R"
style = "comment"

[nodejs]
symbol = " "
style = "green"
format = "via [$symbol($version )]($style)"

[python]
symbol = " "
style = "yellow"
format = 'via [${symbol}(${version} )(\\($virtualenv\\) )]($style)'

[rust]
symbol = " "
style = "pink"
format = "via [$symbol($version )]($style)"

[golang]
symbol = " "
style = "cyan"
format = "via [$symbol($version )]($style)"

[package]
disabled = true

# Palette. Every value clears WCAG AA against the ground.
[palettes.__SLUG__]
"""
    palette_block = "".join(
        '%-7s = "%s"\n' % (role, getattr(p, role))
        for role in ("ground", "surface", "line", "fg", "fg_dim", "comment",
                     "green", "pink", "cyan", "blue", "purple", "yellow", "red")
    )
    out = (body + palette_block).replace("__SLUG__", p.slug)
    write("starship/%s.toml" % p.slug, out)


def emit_vivid(p):
    """LS_COLORS. Schema keys per sharkdp/vivid; all values are ours."""
    def hx(h):
        return h.lstrip("#")

    yml = """# Nullglow for vivid -> LS_COLORS
# Generated by build.py.
#   vivid generate nullglow.yml   (or drop into ~/.config/vivid/themes/)

colors:
  ground:  '{ground}'
  fg:      '{fg}'
  dim:     '{comment}'
  green:   '{green}'
  pink:    '{pink}'
  cyan:    '{cyan}'
  blue:    '{blue}'
  purple:  '{purple}'
  yellow:  '{yellow}'
  red:     '{red}'

core:
  normal_text: {{}}
  regular_file: {{}}
  reset_to_normal: {{}}

  directory:
    foreground: blue
    font-style: bold

  symlink:
    foreground: cyan

  multi_hard_link: {{}}

  fifo:
    foreground: ground
    background: cyan

  socket:
    foreground: ground
    background: pink

  door:
    foreground: ground
    background: pink

  block_device:
    foreground: cyan
    background: dim

  character_device:
    foreground: pink
    background: dim

  broken_symlink:
    foreground: ground
    background: red

  missing_symlink_target:
    foreground: ground
    background: red

  setuid: {{}}
  setgid: {{}}
  file_with_capability: {{}}
  sticky_other_writable: {{}}
  other_writable: {{}}
  sticky: {{}}

  executable_file:
    foreground: green
    font-style: bold

text:
  special:
    foreground: ground
    background: yellow

  todo:
    font-style: bold

  licenses:
    foreground: dim

  configuration:
    foreground: purple

  other:
    foreground: fg

markup:
  foreground: yellow

programming:
  source:
    foreground: green

  tooling:
    foreground: purple

    continuous-integration:
      foreground: cyan

media:
  foreground: pink

office:
  foreground: yellow

archives:
  foreground: red
  font-style: underline

executable:
  foreground: green
  font-style: bold

unimportant:
  foreground: dim
""".format(ground=hx(p.ground), fg=hx(p.fg), comment=hx(p.comment),
           green=hx(p.green), pink=hx(p.pink), cyan=hx(p.cyan), blue=hx(p.blue),
           purple=hx(p.purple), yellow=hx(p.yellow), red=hx(p.red))
    write("vivid/%s.yml" % p.slug, yml)


def emit_theme_zsh(p):
    """One file that owns every colour zsh touches.

    Without this you end up pasting hex values into your own .zshrc in eight
    places, and switching variants means editing all eight. Here it's one
    source line, and the values stay attached to the palette that made them.
    """
    zsh = """# %(label)s for zsh. Generated by build.py. Don't edit it.
#
# Add ONE line to the end of your ~/.zshrc, after compinit and after the zsh
# plugins load:
#
#   source ~/.config/nullglow/theme.zsh
#
# That's the whole install. This file owns bat, LS_COLORS, fzf, syntax
# highlighting, autosuggestions, the completion menu and history search.
# Switching variants is re-running install.sh, not editing your rc.

# ── bat, and delta through it ────────────────────────────────────────────────
export BAT_THEME="%(label)s"

# ── ls, eza and fd, through LS_COLORS ────────────────────────────────────────
if command -v vivid >/dev/null 2>&1; then
  export LS_COLORS="$(vivid generate %(slug)s)"
fi

# ── fzf. Appended, so options you set earlier survive ────────────────────────
export FZF_DEFAULT_OPTS="${FZF_DEFAULT_OPTS:-} \\
  --color=bg+:%(surface)s,bg:-1,spinner:%(green)s,hl:%(pink)s \\
  --color=fg:%(fg)s,header:%(pink)s,info:%(purple)s,pointer:%(green)s \\
  --color=marker:%(green)s,fg+:%(fg)s,prompt:%(green)s,hl+:%(pink)s \\
  --color=border:%(line)s"

# ── zsh-syntax-highlighting ──────────────────────────────────────────────────
typeset -A ZSH_HIGHLIGHT_STYLES
ZSH_HIGHLIGHT_STYLES[command]='fg=%(green)s'
ZSH_HIGHLIGHT_STYLES[builtin]='fg=%(green)s'
ZSH_HIGHLIGHT_STYLES[function]='fg=%(green)s'
ZSH_HIGHLIGHT_STYLES[alias]='fg=%(green)s'
ZSH_HIGHLIGHT_STYLES[precommand]='fg=%(green)s,italic'
ZSH_HIGHLIGHT_STYLES[unknown-token]='fg=%(red)s,bold'
ZSH_HIGHLIGHT_STYLES[path]='fg=%(blue)s,underline'
ZSH_HIGHLIGHT_STYLES[single-quoted-argument]='fg=%(yellow)s'
ZSH_HIGHLIGHT_STYLES[double-quoted-argument]='fg=%(yellow)s'
ZSH_HIGHLIGHT_STYLES[comment]='fg=%(comment)s,italic'
ZSH_HIGHLIGHT_STYLES[redirection]='fg=%(purple)s'
ZSH_HIGHLIGHT_STYLES[reserved-word]='fg=%(pink)s'

# ── zsh-autosuggestions ──────────────────────────────────────────────────────
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=%(comment)s'

# ── completion menu ──────────────────────────────────────────────────────────
# This one has to live here, not in your rc. It expands $LS_COLORS at the point
# it's called, so it has to run after the export above, not before it.
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*:descriptions' format '%%F{%(purple)s}%%B%%d%%b%%f'
zstyle ':completion:*:messages'     format '%%F{%(blue)s}%%d%%f'
zstyle ':completion:*:warnings'     format '%%F{%(pink)s}no match%%f'
zstyle ':completion:*:corrections'  format '%%F{%(yellow)s}%%d (errors: %%e)%%f'

# ── history-substring-search ─────────────────────────────────────────────────
HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_FOUND='bg=%(line)s,fg=%(yellow)s,bold'
HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_NOT_FOUND='fg=%(red)s,bold'
""" % {"label": p.label, "slug": p.slug, "surface": p.surface, "line": p.line,
       "fg": p.fg, "comment": p.comment, "green": p.green, "pink": p.pink,
       "blue": p.blue, "purple": p.purple, "yellow": p.yellow, "red": p.red}
    write("zsh/%s-theme.zsh" % p.slug, zsh)


def emit_delta(p):
    cfg = """# Nullglow for delta. Include from ~/.gitconfig:
#   [include] path = ~/.config/nullglow/delta.gitconfig

[delta]
    syntax-theme = %s
    navigate = true
    line-numbers = true
    hyperlinks = true
    file-style = bold "%s"
    file-decoration-style = "%s" ul
    hunk-header-decoration-style = "%s" box
    line-numbers-zero-style = "%s"
    line-numbers-left-style = "%s"
    line-numbers-right-style = "%s"
    minus-style = syntax "%s"
    minus-emph-style = normal "%s"
    plus-style = syntax "%s"
    plus-emph-style = normal "%s"
    zero-style = syntax
""" % (p.label, p.yellow, p.yellow, p.blue, p.comment, p.comment, p.comment,
       mix(p.ground, p.pink, 0.16), mix(p.ground, p.pink, 0.30),
       mix(p.ground, p.green, 0.16), mix(p.ground, p.green, 0.30))
    write("delta/%s.gitconfig" % p.slug, cfg)


def emit_preview(p):
    """A specimen SVG per variant, so the README needs no hand-made screenshots."""
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    role = {"k": p.pink, "f": p.green, "s": p.yellow, "n": p.purple, "t": p.cyan,
            "p": p.blue, "o": p.fg_dim, "c": p.comment, "v": p.fg, "d": p.comment}

    lines = [
        [("// Bind late so PORT can come from the environment.", "c")],
        [("import", "k"), (" { ", "o"), ("createServer", "v"), (" } ", "o"),
         ("from", "k"), (" 'node:http'", "s"), (";", "o")],
        [],
        [("const", "k"), (" port ", "v"), ("= ", "o"), ("process", "v"), (".", "o"),
         ("env", "p"), (".", "o"), ("PORT", "p"), (" ?? ", "o"), ("3000", "n"), (";", "o")],
        [("const", "k"), (" routes ", "v"), ("= ", "o"), ("new", "k"), (" ", "o"),
         ("Map", "t"), ("([", "o")],
        [("  ['", "o"), ("/api/jobs", "s"), ("', ", "o"), ("listJobs", "f"), ("],", "o")],
        [("]);", "o")],
        [],
        [("export", "k"), (" ", "o"), ("async", "k"), (" ", "o"), ("function", "k"),
         (" ", "o"), ("start", "f"), ("(", "o"), ("opts", "v"), (" = {}) {", "o")],
        [("  ", "o"), ("return", "k"), (" ", "o"), ("createServer", "f"), ("(", "o"),
         ("handler", "v"), (").", "o"), ("listen", "f"), ("(", "o"), ("port", "v"), (");", "o")],
        [("}", "o")],
    ]
    term = [
        # no Nerd Font glyphs here, GitHub renders this SVG with generic fonts
        [("~/Code/nullglow", "p"), (" on ", "d"), ("main", "n"), (" [!2+1]", "k"),
         (" via ", "d"), ("node v22.11.0", "f")],
        [("➜", "f"), (" git diff", "v")],
        [("- const port = 3000", "k")],
        [("+ const port = process.env.PORT ?? 3000", "f")],
    ]

    W, LH, PAD = 900, 21, 22
    top = 46
    y = top
    rows = []
    for ln in lines:
        if ln:
            spans = "".join('<tspan fill="%s">%s</tspan>' % (role[c], esc(t)) for t, c in ln)
            rows.append('<text xml:space="preserve" x="%d" y="%d">%s</text>'
                        % (PAD + 8, y, spans))
        y += LH
    y += 14
    term_top = y
    for ln in term:
        spans = "".join('<tspan fill="%s">%s</tspan>' % (role[c], esc(t)) for t, c in ln)
        rows.append('<text xml:space="preserve" x="%d" y="%d">%s</text>'
                    % (PAD + 8, y, spans))
        y += LH

    swatch_y = y + 16
    chips = "".join(
        '<rect x="%d" y="%d" width="30" height="18" rx="3" fill="%s"/>'
        % (PAD + 8 + i * 34, swatch_y, getattr(p, r))
        for i, r in enumerate(Palette.ACCENTS)
    )
    H = swatch_y + 18 + PAD

    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="ui-monospace, 'JetBrains Mono', 'SF Mono', Menlo, monospace" font-size="13.5">
  <rect width="{w}" height="{h}" rx="10" fill="{ground}"/>
  <rect x="0" y="0" width="{w}" height="32" rx="10" fill="{surface}"/>
  <rect x="0" y="22" width="{w}" height="10" fill="{surface}"/>
  <circle cx="20" cy="16" r="5" fill="{line}"/><circle cx="38" cy="16" r="5" fill="{line}"/><circle cx="56" cy="16" r="5" fill="{line}"/>
  <text x="76" y="21" fill="{comment}" font-size="11.5">{label}: server.js</text>
  <line x1="{pad}" y1="{tsep}" x2="{w2}" y2="{tsep}" stroke="{line}" stroke-width="1"/>
{rows}
  {chips}
</svg>
""".format(w=W, h=H, w2=W - PAD, pad=PAD, ground=p.ground, surface=p.surface,
           line=p.line, comment=p.comment, label=esc(p.label),
           tsep=term_top - 30, rows="\n".join("  " + r for r in rows), chips=chips)
    write("preview/%s.svg" % p.slug, svg)


# ─────────────────────────────────────────────────────────────────────────────
# self-check
# ─────────────────────────────────────────────────────────────────────────────

def check(p):
    """Re-verify every accessibility claim. Exits non-zero if any fails."""
    print("── %s ──\n" % p.label)
    ok = True

    print("  contrast against ground (%s), need >= 4.5:1" % p.ground)
    roles = ["fg", "fg_dim", "comment"] + list(Palette.ACCENTS)
    for role in roles:
        c = contrast(getattr(p, role), p.ground)
        good = c >= 4.5
        ok = ok and good
        print("    %-8s %s  %6.2f:1  %s" % (role, getattr(p, role), c,
                                            "pass" if good else "FAIL"))

    print("\n  accent separation, need ΔE >= 25")
    worst = min((delta_e(getattr(p, a), getattr(p, b)), a, b)
                for i, a in enumerate(Palette.ACCENTS)
                for b in Palette.ACCENTS[i + 1:])
    ok = ok and worst[0] >= 25
    print("    worst pair: %s/%s  ΔE %.1f  %s"
          % (worst[1], worst[2], worst[0], "pass" if worst[0] >= 25 else "FAIL"))

    print("\n  separation under deuteranopia, need ΔE >= 18")
    worst = min((delta_e(deuteranopia(getattr(p, a)), deuteranopia(getattr(p, b))), a, b)
                for i, a in enumerate(Palette.ACCENTS)
                for b in Palette.ACCENTS[i + 1:])
    ok = ok and worst[0] >= 18
    print("    worst pair: %s/%s  ΔE %.1f  %s"
          % (worst[1], worst[2], worst[0], "pass" if worst[0] >= 18 else "FAIL"))

    print("\n  %s\n" % ("verified" if ok else "FAILED. Variant does not meet its own spec."))
    return ok


def main():
    with open(os.path.join(ROOT, "palette.json")) as fh:
        spec = json.load(fh)

    meta = spec["meta"]
    palettes = [Palette(slug, variant, spec["derive"], meta)
                for slug, variant in spec["variants"].items()]

    if "--check" in sys.argv:
        print("Nullglow: verifying palette claims\n")
        results = [check(p) for p in palettes]
        if all(results):
            print("All variants meet the spec.")
            return 0
        print("At least one variant FAILED.")
        return 1

    print("Nullglow %s: generating dist/ for %d variant(s)\n"
          % (meta["version"], len(palettes)))
    for p in palettes:
        print("  [%s]" % p.label)
        for emit in (emit_vscode, emit_terminal_app, emit_iterm2, emit_bat,
                     emit_starship, emit_vivid, emit_theme_zsh, emit_delta,
                     emit_preview):
            emit(p)
        print("")
    emit_vscode_package(palettes, meta)
    print("\nDone. Run `python3 build.py --check` to verify the palette claims.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
