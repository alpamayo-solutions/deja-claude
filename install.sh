#!/usr/bin/env bash
set -euo pipefail

echo "deja-claude installer"
echo "====================="
echo

# Check Python 3.10+
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is required but not found."
    echo "Install it from https://python.org or via your package manager."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
    echo "Error: Python 3.10+ is required (found $PYTHON_VERSION)."
    exit 1
fi

echo "Found Python $PYTHON_VERSION"

# Install pipx if not present
if ! command -v pipx &>/dev/null; then
    echo "Installing pipx..."
    if command -v brew &>/dev/null; then
        brew install pipx
        pipx ensurepath
    else
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    fi
    echo "pipx installed. You may need to restart your shell."
fi

REPO="https://github.com/alpamayo-solutions/deja-claude.git"

# Install deja-claude
echo "Installing deja-claude from GitHub..."
pipx install "git+${REPO}" 2>/dev/null || pipx upgrade "git+${REPO}"

echo
echo "Done! Run 'deja-claude' to start browsing your Claude Code sessions."
