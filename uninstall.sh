#!/usr/bin/env bash
set -e

echo "Terminating any active Mint Tasks instances..."
pkill -f "mint_tasks/main.py" || true

echo "Completely purging application binaries, databases, and caches..."
rm -rf "$HOME/.local/share/mint_tasks"
rm -rf "$HOME/.config/mint_tasks"
rm -rf "$HOME/.cache/mint_tasks"

echo "Removing desktop entry and application icon..."
rm -f "$HOME/.local/share/applications/mint_tasks.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/mint-tasks.svg"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo "Success: Mint Tasks, all SQLite records, configurations, icons, and shortcuts have been permanently removed."
