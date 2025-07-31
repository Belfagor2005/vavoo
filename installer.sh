#!/bin/bash

##setup command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/vavoo/main/installer.sh -O - | /bin/sh

######### Only These 2 lines to edit with new version ######
version='1.38'
changelog='\n- Test Upgrade\n- fix player - infobar - Add --> refresh player'
##############################################################

TMPPATH=/tmp/vavoo-main
FILEPATH=/tmp/main.tar.gz

# Determine plugin path based on architecture
if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/vavoo
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/vavoo
fi

# Cleanup function
cleanup() {
    [ -d "$TMPPATH" ] && rm -rf "$TMPPATH"
    [ -f "$FILEPATH" ] && rm -f "$FILEPATH"
    [ -d "$PLUGINPATH" ] && rm -rf "$PLUGINPATH"
}

# Check package manager type
if [ -f /var/lib/dpkg/status ]; then
    STATUS=/var/lib/dpkg/status
    OSTYPE=DreamOs
    PKG_MANAGER="apt-get"
else
    STATUS=/var/lib/opkg/status
    OSTYPE=Dream
    PKG_MANAGER="opkg"
fi

echo ""
cleanup

# Install wget if missing
if ! command -v wget >/dev/null 2>&1; then
    echo "Installing wget..."
    if [ "$OSTYPE" = "DreamOs" ]; then
        apt-get update && apt-get install -y wget || { echo "Failed to install wget"; exit 1; }
    else
        opkg update && opkg install wget || { echo "Failed to install wget"; exit 1; }
    fi
fi

# Detect Python version
if python --version 2>&1 | grep -q '^Python 3\.'; then
    echo "Python3 image detected"
    PYTHON=PY3
    Packagesix=python3-six
    Packagerequests=python3-requests
else
    echo "Python2 image detected"
    PYTHON=PY2
    Packagerequests=python-requests
fi

# Install required packages
install_pkg() {
    local pkg=$1
    if ! grep -qs "Package: $pkg" "$STATUS"; then
        echo "Installing $pkg..."
        if [ "$OSTYPE" = "DreamOs" ]; then
            apt-get update && apt-get install -y "$pkg" || { echo "Failed to install $pkg"; exit 1; }
        else
            opkg update && opkg install "$pkg" || { echo "Failed to install $pkg"; exit 1; }
        fi
    fi
}

[ "$PYTHON" = "PY3" ] && install_pkg "$Packagesix"
install_pkg "$Packagerequests"

# Download and install plugin
mkdir -p "$TMPPATH"
cd "$TMPPATH" || { echo "Failed to enter directory $TMPPATH"; exit 1; }
set -e

echo -e "\n# Your image is ${OSTYPE}\n"

# Install additional dependencies for non-DreamOs systems
if [ "$OSTYPE" != "DreamOs" ]; then
    for pkg in ffmpeg gstplayer exteplayer3 enigma2-plugin-systemplugins-serviceapp; do
        install_pkg "$pkg"
    done
fi

echo "Downloading vavoo..."
wget --no-check-certificate 'https://github.com/Belfagor2005/vavoo/archive/refs/heads/main.tar.gz' -O "$FILEPATH"
if [ $? -ne 0 ]; then
    echo "Failed to download vavoo package!"
    exit 1
fi

tar -xzf "$FILEPATH"
if [ $? -ne 0 ]; then
    echo "Failed to extract vavoo package!"
    exit 1
fi

cp -r 'vavoo-main/usr' '/'

set +e

# Verify installation
if [ ! -d "$PLUGINPATH" ]; then
    echo "Error: Plugin installation failed!"
    cleanup
    exit 1
fi

# Cleanup
cleanup
sync

# System info
FILE="/etc/image-version"
box_type=$(head -n 1 /etc/hostname 2>/dev/null || echo "Unknown")
distro_value=$(grep '^distro=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
distro_version=$(grep '^version=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
python_vers=$(python --version 2>&1)

cat <<EOF
#########################################################
#               INSTALLED SUCCESSFULLY                  #
#                developed by LULULLA                   #
#               https://corvoboys.org                   #
#########################################################
#           your Device will RESTART Now                #
#########################################################
^^^^^^^^^^Debug information:
BOX MODEL: $box_type
OO SYSTEM: $OSTYPE
PYTHON: $python_vers
IMAGE NAME: ${distro_value:-Unknown}
IMAGE VERSION: ${distro_version:-Unknown}
EOF

sleep 5
killall -9 enigma2
exit 0
