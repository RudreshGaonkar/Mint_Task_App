#!/usr/bin/env bash
set -e

PACKAGE_NAME="mint-tasks"
VERSION="1.0.0"
ARCH="amd64"
BUILD_DIR="deb_dist/${PACKAGE_NAME}_${VERSION}_${ARCH}"
OUTPUT_DEB="${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo "=== Building Debian Package: ${OUTPUT_DEB} ==="

# Clean previous build artifacts
rm -rf deb_dist "${OUTPUT_DEB}" mint-tasks.deb
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/opt/mint_tasks/bin"
mkdir -p "${BUILD_DIR}/opt/mint_tasks/app"
mkdir -p "${BUILD_DIR}/opt/mint_tasks/venv"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps"

# 1. Copy application files
echo "Copying application source code..."
cp main.py database.py scheduler.py theme.py requirements.txt mint_tasks_icon.svg "${BUILD_DIR}/opt/mint_tasks/app/"
cp -r ui "${BUILD_DIR}/opt/mint_tasks/app/"

# 2. Set up standalone Virtual Environment
echo "Setting up standalone Python virtual environment in package..."
TEMP_VENV_BUILD="/tmp/mint_tasks_deb_venv_$$"
rm -rf "$TEMP_VENV_BUILD"
python3 -m venv "$TEMP_VENV_BUILD"
"$TEMP_VENV_BUILD/bin/pip" install --upgrade pip
"$TEMP_VENV_BUILD/bin/pip" install -r requirements.txt

# Copy venv contents to /opt/mint_tasks/venv
cp -r "$TEMP_VENV_BUILD"/* "${BUILD_DIR}/opt/mint_tasks/venv/"
rm -rf "$TEMP_VENV_BUILD"

# Fix venv shebangs and configs for /opt/mint_tasks/venv
find "${BUILD_DIR}/opt/mint_tasks/venv/bin" -type f -exec sed -i '1s|^#!.*python.*|#!/opt/mint_tasks/venv/bin/python3|' {} + 2>/dev/null || true
if [ -f "${BUILD_DIR}/opt/mint_tasks/venv/pyvenv.cfg" ]; then
    sed -i 's|home = .*|home = /usr/bin|' "${BUILD_DIR}/opt/mint_tasks/venv/pyvenv.cfg"
fi

# 3. Create launcher script
echo "Creating launcher script..."
cat << 'EOF' > "${BUILD_DIR}/opt/mint_tasks/bin/mint-tasks"
#!/usr/bin/env bash
exec /opt/mint_tasks/venv/bin/python3 /opt/mint_tasks/app/main.py "$@"
EOF
chmod 755 "${BUILD_DIR}/opt/mint_tasks/bin/mint-tasks"

# Symlink to /usr/bin/mint-tasks
ln -sf /opt/mint_tasks/bin/mint-tasks "${BUILD_DIR}/usr/bin/mint-tasks"

# 4. Desktop entry
echo "Installing desktop launcher..."
cat << 'EOF' > "${BUILD_DIR}/usr/share/applications/mint-tasks.desktop"
[Desktop Entry]
Name=Mint Tasks
Comment=Minimalist Tasks & Notes for Linux Mint
Exec=/opt/mint_tasks/bin/mint-tasks
Icon=mint-tasks
Terminal=false
Type=Application
Categories=Utility;Office;
Keywords=Task;Todo;Notes;Notepad;Mint;
EOF
chmod 644 "${BUILD_DIR}/usr/share/applications/mint-tasks.desktop"

# 5. Application Icon
echo "Installing vector icon..."
cp mint_tasks_icon.svg "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/mint-tasks.svg"
chmod 644 "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/mint-tasks.svg"

# 6. DEBIAN/control file
echo "Creating Debian control metadata..."
cat << EOF > "${BUILD_DIR}/DEBIAN/control"
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Rudresh Gaonkar
Depends: python3 (>= 3.10), libgl1, libegl1, libxkbcommon0, libdbus-1-3, libxcb1
Description: Native Linux Mint Tasks & Multi-Tab Notes App
 Lightweight, privacy-first Google Tasks alternative and Windows 11-style
 tabbed scratchpad built with PyQt6 and SQLite for Linux Mint, Ubuntu, and Debian.
 Consumes only 35MB-65MB RAM with strict POSIX 0600 security permissions.
EOF
chmod 644 "${BUILD_DIR}/DEBIAN/control"

# 7. DEBIAN maintainer scripts (postinst, prerm, postrm)
cat << 'EOF' > "${BUILD_DIR}/DEBIAN/postinst"
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
    chmod -R 755 /opt/mint_tasks 2>/dev/null || true
    update-desktop-database /usr/share/applications 2>/dev/null || true
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi
exit 0
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"

cat << 'EOF' > "${BUILD_DIR}/DEBIAN/prerm"
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "upgrade" ] || [ "$1" = "deconfigure" ]; then
    pkill -f "/opt/mint_tasks/app/main.py" 2>/dev/null || true
fi
exit 0
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/prerm"

cat << 'EOF' > "${BUILD_DIR}/DEBIAN/postrm"
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi
exit 0
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/postrm"

# 8. Build package
echo "Compiling .deb package using dpkg-deb..."
dpkg-deb --build --root-owner-group "${BUILD_DIR}" "${OUTPUT_DEB}"
ln -sf "${OUTPUT_DEB}" mint-tasks.deb

echo "=== Build Complete! Package generated: ==="
ls -lh "${OUTPUT_DEB}"
dpkg-deb --info "${OUTPUT_DEB}"
