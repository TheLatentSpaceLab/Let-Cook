#!/usr/bin/env bash
#
# One-liner install for letcook:
#
#   curl -fsSL https://raw.githubusercontent.com/<owner>/letcook/main/install.sh | bash
#
# Or with a custom install directory:
#
#   curl -fsSL ... | LETCOOK_HOME=~/my-dir bash

set -euo pipefail

REPO_URL="https://github.com/<owner>/letcook"
LETCOOK_HOME="${LETCOOK_HOME:-$HOME/.letcook}"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${CYAN}$1${NC}"; }
success() { echo -e "${GREEN}$1${NC}"; }
err()     { echo -e "${RED}$1${NC}" >&2; exit 1; }

# Check for git
command -v git &>/dev/null || err "git is required. Install it and try again."

echo ""
info "${BOLD}Installing letcook...${NC}"
echo ""

# Clone or update
if [ -d "$LETCOOK_HOME/.git" ]; then
    info "Updating existing installation..."
    git -C "$LETCOOK_HOME" pull --quiet
else
    rm -rf "$LETCOOK_HOME"
    git clone --quiet "$REPO_URL" "$LETCOOK_HOME"
fi

# Symlink binary
mkdir -p "$BIN_DIR"
ln -sf "$LETCOOK_HOME/bin/letcook" "$BIN_DIR/letcook"
chmod +x "$LETCOOK_HOME/bin/letcook"

echo ""
success "${BOLD}Installed letcook to $LETCOOK_HOME${NC}"
echo ""

# Check PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "Add this to your shell profile (~/.bashrc or ~/.zshrc):"
    echo ""
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

echo "Get started:"
echo ""
echo "  letcook init ./my-first-task"
echo "  letcook run  ./my-first-task"
echo ""
