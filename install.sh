#!/usr/bin/env bash
set -e

APP_DIR="$HOME/.local/share/mint_tasks/app"
VENV_DIR="$HOME/.local/share/mint_tasks/venv"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

echo "Creating secure directories..."
mkdir -p "$APP_DIR"
mkdir -p "$HOME/.local/share/mint_tasks"
chmod 700 "$HOME/.local/share/mint_tasks"
mkdir -p "$ICON_DIR"

echo "Setting up Python virtual environment..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt

echo "Copying application source files and icons..."
cp -r ./* "$APP_DIR/"
if [ -f "./mint_tasks_icon.svg" ]; then
    cp "./mint_tasks_icon.svg" "$ICON_DIR/mint-tasks.svg"
elif [ -f "./Task-svg.svg" ]; then
    cp "./Task-svg.svg" "$ICON_DIR/mint-tasks.svg"
    cp "./Task-svg.svg" "$APP_DIR/mint_tasks_icon.svg"
fi

echo "Installing desktop launcher..."
mkdir -p "$DESKTOP_DIR"
cat <<EOF> "$DESKTOP_DIR/mint_tasks.desktop"
[Desktop Entry]
Name=Mint Tasks
Comment=Minimalist Tasks & Notes for Linux Mint
Exec=$VENV_DIR/bin/python3 $APP_DIR/main.py
Icon=$APP_DIR/mint_tasks_icon.svg
Terminal=false
Type=Application
Categories=Utility;Office;
EOF

update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo "Installation complete. Mint Tasks is now available in your application menu."
