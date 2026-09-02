# Nullglow for zsh-syntax-highlighting and zsh-autosuggestions.
# Source AFTER the plugins themselves.

ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#6e7d71'

typeset -A ZSH_HIGHLIGHT_STYLES
ZSH_HIGHLIGHT_STYLES[command]='fg=#2bf59b'
ZSH_HIGHLIGHT_STYLES[builtin]='fg=#2bf59b'
ZSH_HIGHLIGHT_STYLES[function]='fg=#2bf59b'
ZSH_HIGHLIGHT_STYLES[alias]='fg=#2bf59b'
ZSH_HIGHLIGHT_STYLES[precommand]='fg=#2bf59b,italic'
ZSH_HIGHLIGHT_STYLES[unknown-token]='fg=#ff5c5c,bold'
ZSH_HIGHLIGHT_STYLES[path]='fg=#48b8f5,underline'
ZSH_HIGHLIGHT_STYLES[single-quoted-argument]='fg=#f5d76b'
ZSH_HIGHLIGHT_STYLES[double-quoted-argument]='fg=#f5d76b'
ZSH_HIGHLIGHT_STYLES[comment]='fg=#6e7d71,italic'
ZSH_HIGHLIGHT_STYLES[redirection]='fg=#d79bff'
ZSH_HIGHLIGHT_STYLES[reserved-word]='fg=#ff4d9e'
