# 🎬 Vavoo Stream Live - Enigma2 Plugin

[![Python package](https://github.com/Belfagor2005/vavoo/actions/workflows/pylint.yml/badge.svg)](https://github.com/Belfagor2005/vavoo/actions/workflows/pylint.yml)
[![Version](https://img.shields.io/badge/Version-1.41-blue.svg)](https://github.com/Belfagor2005/vavoo)
[![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-green.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python](https://img.shields.io/badge/Python-2.7%2F3.x-yellow.svg)](https://python.org)

A sophisticated Enigma2 plugin for streaming live TV channels from multiple sources with advanced bouquet management.

## ✨ Features

### 📺 Streaming & Playback
- 🎥 **Live TV Streaming** from multiple servers (Vavoo, Oha, Kool, Huhu)
- 🔄 **Auto-refresh** streams with configurable intervals
- 🎭 **Multiple Player Support**: GStreamer, Exteplayer3, ServiceApp
- 🌐 **IPv6 Support** with toggle option
- ⚡ **Fast Channel Switching** with next/previous navigation

### 🗂️ Content Organization
- 🌍 **Dual View Modes**: Countries view & Categories view
- 🏴 **Country Flags** with automatic icon detection
- 📑 **Hierarchical Bouquet Export** with container structure
- 🔍 **Search Functionality** within categories
- 📊 **Channel Filtering** by country and genre

### ⚙️ Configuration & Management
- 🛠️ **Comprehensive Settings**: DNS, servers, update intervals
- 💾 **Automatic Bouquet Updates** with scheduling
- 📁 **M3U File Generation** for external players
- 🎨 **Customizable UI**: Backgrounds, fonts, layouts
- 🔄 **Auto-update System** with version checking

### 🔧 Technical Features
- 🐍 **Python 2.7/3.x Compatible**
- 📱 **Multi-resolution Support** (HD, FHD, WQHD)
- 🌍 **RTL Language Support** (Arabic, etc.)
- 🔒 **Authentication Handling**
- 📝 **Comprehensive Logging**

## 🖼️ Screenshots

| Main Interface | Categories View | Settings |
|----------------|-----------------|----------|
| <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen1.png" width="200"> | <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen2.png" width="200"> | <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen3.png" width="200"> |

| Player | Bouquet Export | Search |
|--------|----------------|--------|
| <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen4.png" width="200"> | <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen5.png" width="200"> | <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen7.png" width="200"> |

## 🚀 Installation

### Manual Installation
```bash
cd /tmp
wget https://github.com/Belfagor2005/vavoo/releases/latest/download/vavoo.ipk
opkg install vavoo.ipk
```

### Auto-Update
The plugin includes built-in update checking with one-click installation.

## ⚙️ Configuration

Access plugin settings through:
- **Enigma2 Menu** → Plugins → Vavoo Stream Live
- **Plugin Menu** → Configuration

### Key Settings:
- **Server Selection**: Choose between Vavoo, Oha, Kool, Huhu
- **Update Intervals**: Configure automatic bouquet updates
- **DNS Settings**: Google, Cloudflare, Quad9, or default
- **View Preferences**: Countries or Categories as default
- **Player Settings**: Service reference configuration

## 🏗️ Bouquet Export System

### Flat Structure (Countries View)
```
userbouquet.vavoo_italy.tv
userbouquet.vavoo_france.tv
userbouquet.vavoo_germany.tv
```

### Hierarchical Structure (Categories View)
```
bouquet.tv
├── userbouquet.vavoo_italy_cowntry.tv
│   ├── userbouquet.vavoo_italy_documentary.tv
│   ├── userbouquet.vavoo_italy_sports.tv
│   └── userbouquet.vavoo_italy_movie.tv
└── userbouquet.vavoo_france_cowntry.tv
    ├── userbouquet.vavoo_france_documentary.tv
    └── userbouquet.vavoo_france_sports.tv
```

## 🌍 Supported Countries

- 🇦🇱 Albania - 🇸🇦 Arabia - 🇧🇬 Bulgaria - 🇭🇷 Croatia 
- 🇫🇷 France - 🇩🇪 Germany - 🇮🇹 Italy - 🇳🇱 Netherlands
- 🇵🇱 Poland - 🇵🇹 Portugal - 🇷🇴 Romania - 🇷🇺 Russia
- 🇪🇸 Spain - 🇹🇷 Turkey - 🇬🇧 United Kingdom

## 🛠️ Technical Details

- **Architecture**: Modular Python plugin for Enigma2
- **Compatibility**: Enigma2-based receivers (OpenPLi, OpenATV, etc.)
- **Dependencies**: Standard Enigma2 components, requests library
- **Skin Support**: HD, FHD, and WQHD resolutions
- **Font Support**: Custom TTF/OTF font integration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

### Credit & Acknowledgments
- **Developer**: [Lululla](https://github.com/Belfagor2005)
- **Support**: @KiddaC for technical guidance
- **Graphics**: @oktus for background images
- **Testing**: Qu4k3 and the community
- **Communities**: Linuxsat-support.com & Corvoboys.org

## 📄 License

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. See the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This plugin provides access to publicly available video stream URLs. No video files are stored in this repository. All links point to content that we believe has been intentionally made publicly available by copyright holders.

If you believe any content infringes on your rights, please:
1. Contact the actual content host
2. Open an issue for link removal

This repository contains only links and does not host any content. DMCA notices should be directed to the actual content hosts, not GitHub or this repository's maintainers.

---

**⭐ If you find this plugin useful, please give it a star!**
```
