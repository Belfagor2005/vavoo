# 🎬 Vavoo Stream Live - Enigma2 Plugin

[![Python package](https://github.com/Belfagor2005/vavoo/actions/workflows/pylint.yml/badge.svg)](https://github.com/Belfagor2005/vavoo/actions/workflows/pylint.yml)
[![Version](https://img.shields.io/badge/Version-1.46-blue.svg)](https://github.com/Belfagor2005/vavoo)
[![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-green.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python](https://img.shields.io/badge/Python-2.7%2F3.x-yellow.svg)](https://python.org)

## 📌 Overview
Vavoo Stream Live Plugin is an Enigma2 extension that provides access to thousands of live TV channels from multiple countries. It features a built-in local proxy for improved reliability, automatic bouquet updates, and seamless integration with your Enigma2 receiver.

## 🖼️ Screenshots

| Main Interface | Categories View | Settings |
|----------------|-----------------|----------|
| <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen1.png" width="200"> | <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen2.png" width="200"> | <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen3.png" width="200"> |

| Player | Bouquet Export | Search |
|--------|----------------|--------|
| <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen4.png" width="200"> | <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen5.png" width="200"> | <img src="https://raw.githubusercontent.com/Belfagor2005/vavoo/main/screen/screen7.png" width="200"> |


## ✨ Key Features
- **Live TV Streaming** – Watch live channels from various countries
- **Country & Category Browsing** – Organized by country and category
- **Search Functionality** – Find channels by name in real-time
- **Enigma2 Bouquet Export** – Export channels directly to your channel list
- **M3U Playlist Generation** – Create standard M3U playlists for external players
- **Automatic Updates** – Scheduled bouquet updates to keep channels current
- **Local Proxy Integration** – Enhanced reliability and no 10-minute blocks
- **Multi-Language Support** – Including right-to-left language support
- **Customizable Interface** – Change backgrounds, fonts, and settings
- **Proxy Status Monitor** – Real-time proxy status display in main interface
- **Text Key Functions** – Manual proxy refresh using TEXT button

## 🚀 Quick Start Guide

### First-Time Setup
1. **Open the Vavoo Plugin** – The proxy will start automatically
2. **Select a Country** – Choose your desired country (e.g., "Italy")
3. **Press GREEN Button** – Export favorites to Enigma2 bouquets
4. **Return to TV** – Your channels will appear in the channel list!

### Automatic Updates (Recommended)
- Go to **Menu Config** → Enable **"Scheduled Bouquet Update: ON"**
- Choose update interval (5-15 minutes) or fixed time
- The proxy will handle everything automatically

### Manual Use
- If auto-update is OFF, simply open the plugin when you want to update
- The proxy starts automatically when plugin opens
- Select country and press GREEN to export

## 🔧 User Configuration
In the Config Menu:
- ✅ **Scheduled Bouquet Update**: ON/OFF (only required setting)
- ✅ If ON: Choose interval (5-15 min) or fixed time
- ✅ Proxy and updates are managed automatically

## 🎯 Benefits
- ✅ **No 10-minute blocks** – Proxy handles authentication tokens
- ✅ **Automatic updates** – Keep bouquets fresh without manual work
- ✅ **Improved performance** – Local proxy provides stable streams
- ✅ **Clean system** – Single configuration point
- ✅ **No manual refreshes** – Everything happens automatically
- ✅ **Real-time monitoring** – Proxy status always visible
- ✅ **Manual control** – Force proxy refresh with TEXT button

## 🛠 Technical Features
The local proxy (127.0.0.1:4323):
- Manages authentication with Vavoo servers
- Automatically renews tokens every 8-9 minutes
- Provides stable URLs for bouquets
- Completely eliminates 10-minute streaming blocks
- Self-monitoring with automatic restart on failure
- Connection pool management to prevent timeouts

## 📋 API Endpoints
The proxy provides these endpoints:
- `/status` – Check proxy status
- `/channels?country=CountryName` – Get channels by country
- `/vavoo?channel=ChannelID` – Resolve stream URLs
- `/catalog` – Full channel catalog
- `/countries` – List all countries
- `/refresh_token` – Force token refresh
- `/shutdown` – Gracefully stop proxy

## 🗂 File Management
### Bouquet Export
- Path: Plugin menu → Select country → GREEN button
- Creates bouquets with proxy URLs: `http://127.0.0.1:4323/vavoo?channel=CHANNEL_ID`
- Requires proxy to be running during export

### M3U Export
- Path: Config Menu → "Generate .m3u files"
- Downloads playlist from proxy and saves as `vavoo_[country]_playlist.m3u`

## 🚨 Troubleshooting
### Quick Diagnostics
```bash
# Check proxy status
curl -s http://127.0.0.1:4323/status

# Check proxy logs
cat /tmp/vavoo_proxy.log

# Check plugin logs
cat /tmp/vavoo.log
```

### Common Issues
| Problem | Solution |
|---------|----------|
| "No channels found" | Restart plugin, check internet connection |
| Bouquets don't open | Ensure proxy is running |
| Stream doesn't start | Proxy should auto-refresh tokens |
| M3U export fails | Verify port 4323 is accessible |

## 📝 Important Notes
- Old bouquets won't work with new system – re-export required
- Proxy runs in background – bouquets work even after closing plugin
- Minimal memory usage (~20-50MB)
- Only `vavoo_proxy.py` needs updates if Vavoo API changes
- Use **TEXT button** in main menu to manually refresh proxy token
- Proxy status is displayed in real-time in the main interface

## 🤝 Credits
- **Created by**: Lululla (https://github.com/Belfagor2005)
- **Special thanks to**: @KiddaC for suggestions
- **Background images**: @oktus
- **Contributions**: Qu4k3
- **Communities**: Linuxsat-support.com & Corvoboys

## 📄 License
CC BY-NC-SA 4.0  
https://creativecommons.org/licenses/by-nc-sa/4.0

**Usage of this code without proper attribution is strictly prohibited.**
**For modifications and redistribution, please maintain this credit header.**

---
*Last Modified: 2026-01-23*
