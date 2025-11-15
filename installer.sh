#!/bin/bash

##setup command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/vavoo/main/installer.sh -O - | /bin/sh

######### Only These 2 lines to edit with new version ######
version='1.39'
changelog='\n- Add Category and Cowntry\n- fix Config\n- Add Flag'
##############################################################

TMPPATH=/tmp/vavoo-install
FILEPATH=/tmp/vavoo-main.tar.gz

# Determine plugin path based on architecture
if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/vavoo
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/vavoo
fi

echo "Starting vavoo installation..."

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up temporary files..."
    [ -d "$TMPPATH" ] && rm -rf "$TMPPATH"
    [ -f "$FILEPATH" ] && rm -f "$FILEPATH"
}

# Detect OS type
detect_os() {
    if [ -f /var/lib/dpkg/status ]; then
        OSTYPE="DreamOs"
        STATUS="/var/lib/dpkg/status"
    elif [ -f /etc/opkg/opkg.conf ] || [ -f /var/lib/opkg/status ]; then
        OSTYPE="OE"  # Open Embedded
        STATUS="/var/lib/opkg/status"
    elif [ -f /etc/debian_version ]; then
        OSTYPE="Debian"
        STATUS="/var/lib/dpkg/status"
    else
        OSTYPE="Unknown"
        STATUS=""
    fi
    echo "🔍 Detected OS type: $OSTYPE"
}

detect_os

# Install wget if missing
if ! command -v wget >/dev/null 2>&1; then
    echo "📥 Installing wget..."
    case "$OSTYPE" in
        "DreamOs"|"Debian")
            apt-get update && apt-get install -y wget || { echo "❌ Failed to install wget"; exit 1; }
            ;;
        "OE")
            opkg update && opkg install wget || { echo "❌ Failed to install wget"; exit 1; }
            ;;
        *)
            echo "❌ Unsupported OS type. Cannot install wget."
            exit 1
            ;;
    esac
fi

# Detect Python version
if python --version 2>&1 | grep -q '^Python 3\.'; then
    echo "🐍 Python3 image detected"
    PYTHON="PY3"
    Packagesix="python3-six"
    Packagerequests="python3-requests"
else
    echo "🐍 Python2 image detected"
    PYTHON="PY2"
    Packagerequests="python-requests"
    # python-six per PY2
    if [ "$OSTYPE" = "DreamOs" ] || [ "$OSTYPE" = "Debian" ]; then
        Packagesix="python-six"
    else
        Packagesix="python-six"
    fi
fi

# Install required packages
install_pkg() {
    local pkg=$1
    if [ -z "$STATUS" ] || ! grep -qs "Package: $pkg" "$STATUS" 2>/dev/null; then
        echo "📦 Installing $pkg..."
        case "$OSTYPE" in
            "DreamOs"|"Debian")
                apt-get update && apt-get install -y "$pkg" || { echo "⚠️ Could not install $pkg, continuing anyway..."; }
                ;;
            "OE")
                opkg update && opkg install "$pkg" || { echo "⚠️ Could not install $pkg, continuing anyway..."; }
                ;;
            *)
                echo "⚠️ Cannot install $pkg on unknown OS type, continuing..."
                ;;
        esac
    else
        echo "✅ $pkg already installed"
    fi
}

# Install Python dependencies
[ "$PYTHON" = "PY3" ] && install_pkg "$Packagesix"
install_pkg "$Packagerequests"

# Install additional dependencies for OE systems
if [ "$OSTYPE" = "OE" ]; then
    echo "📥 Installing additional dependencies for OpenEmbedded..."
    for pkg in ffmpeg gstplayer exteplayer3 enigma2-plugin-systemplugins-serviceapp; do
        install_pkg "$pkg"
    done
fi

# Cleanup before download
cleanup
mkdir -p "$TMPPATH"

# Download and extract
echo "⬇️ Downloading vavoo..."
wget --no-check-certificate 'https://github.com/Belfagor2005/vavoo/archive/refs/heads/main.tar.gz' -O "$FILEPATH"
if [ $? -ne 0 ]; then
    echo "❌ Failed to download vavoo package!"
    cleanup
    exit 1
fi

echo "📦 Extracting package..."
tar -xzf "$FILEPATH" -C "$TMPPATH"
if [ $? -ne 0 ]; then
    echo "❌ Failed to extract vavoo package!"
    cleanup
    exit 1
fi

# Install plugin files
echo "🔧 Installing plugin files..."
mkdir -p "$PLUGINPATH"

# Cerca la directory corretta nella struttura estratta
if [ -d "$TMPPATH/vavoo-main/usr/lib/enigma2/python/Plugins/Extensions/vavoo" ]; then
    cp -r "$TMPPATH/vavoo-main/usr/lib/enigma2/python/Plugins/Extensions/vavoo"/* "$PLUGINPATH/" 2>/dev/null
    echo "✅ Copied from standard plugin directory"
elif [ -d "$TMPPATH/vavoo-main/usr/lib64/enigma2/python/Plugins/Extensions/vavoo" ]; then
    cp -r "$TMPPATH/vavoo-main/usr/lib64/enigma2/python/Plugins/Extensions/vavoo"/* "$PLUGINPATH/" 2>/dev/null
    echo "✅ Copied from lib64 plugin directory"
elif [ -d "$TMPPATH/vavoo-main/usr" ]; then
    # Copia tutto l'albero usr
    cp -r "$TMPPATH/vavoo-main/usr"/* /usr/ 2>/dev/null
    echo "✅ Copied entire usr structure"
else
    echo "❌ Could not find plugin files in extracted archive"
    echo "📋 Available directories:"
    find "$TMPPATH" -type d -name "*vavoo*" | head -10
    cleanup
    exit 1
fi

sync

# Verify installation
echo "🔍 Verifying installation..."
if [ -d "$PLUGINPATH" ] && [ -n "$(ls -A "$PLUGINPATH" 2>/dev/null)" ]; then
    echo "✅ Plugin directory found and not empty: $PLUGINPATH"
    echo "📁 Contents:"
    ls -la "$PLUGINPATH/" | head -10
else
    echo "❌ Plugin installation failed or directory is empty!"
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
OS SYSTEM: $OSTYPE
PYTHON: $python_vers
IMAGE NAME: ${distro_value:-Unknown}
IMAGE VERSION: ${distro_version:-Unknown}
PLUGIN VERSION: $version
EOF

echo "🔄 Restarting enigma2 in 5 seconds..."
sleep 5
killall -9 enigma2
exit 0