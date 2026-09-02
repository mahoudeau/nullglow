# Nullglow for zsh-syntax-highlighting and zsh-autosuggestions.
# Source AFTER the plugins themselves.

ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#6e7d71'

typeset -A ZSH_HIGHLIGHT_STYLES
ZSH_HIGHLIGHT_STYLES[command]='fg=#05f98b'
ZSH_HIGHLIGHT_STYLES[builtin]='fg=#05f98b'
ZSH_HIGHLIGHT_STYLES[function]='fg=#05f98b'
ZSH_HIGHLIGHT_STYLES[alias]='fg=#05f98b'
ZSH_HIGHLIGHT_STYLES[precommand]='fg=#05f98b,italic'
ZSH_HIGHLIGHT_STYLES[unknown-token]='fg=#fe1115,bold'
ZSH_HIGHLIGHT_STYLES[path]='fg=#0690fc,underline'
ZSH_HIGHLIGHT_STYLES[single-quoted-argument]='fg=#fcc60b'
ZSH_HIGHLIGHT_STYLES[double-quoted-argument]='fg=#fcc60b'
ZSH_HIGHLIGHT_STYLES[comment]='fg=#6e7d71,italic'
ZSH_HIGHLIGHT_STYLES[redirection]='fg=#c312f9'
ZSH_HIGHLIGHT_STYLES[reserved-word]='fg=#f81578'
