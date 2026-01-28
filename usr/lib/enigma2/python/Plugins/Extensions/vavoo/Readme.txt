---

#########################################################
#                                                       #
#  Vavoo Stream Live Plugin                             #
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: CC BY-NC-SA 4.0                             #
#  https://creativecommons.org/licenses/by-nc-sa/4.0    #
#  Last Modified: 20260122                              #
#                                                       #
#  Credits:                                             #
#  - Original concept by Lululla                        #
#  - Special thanks to @KiddaC for support              #
#  - Background images by @oktus                        #
#  - Additional contributions by Qu4k3                  #
#  - Linuxsat-support.com & Corvoboys communities       #
#                                                       #
#  Usage of this code without proper attribution        #
#  is strictly prohibited.                              #
#  For modifications and redistribution,                #
#  please maintain this credit header.                  #
#########################################################


VAVOO PLUGIN - USER FEATURES
1. Live TV Streaming
Watch thousands of live TV channels from multiple countries.

Streams are delivered through a local proxy for better reliability and speed.

2. Country and Category Browsing
Browse channels by country (e.g., Italy, France, Germany) or by category (e.g., Sports, News).

The plugin organizes channels in a hierarchical structure for easy navigation.

3. Search Channels
Search for specific channels by name using the built-in search function.

The search is real-time and filters the current list of channels.

4. Export to Enigma2 Bouquets
Export your favorite channels or entire countries as bouquets in Enigma2.

The exported bouquets appear in your channel list, just like regular TV channels.

5. Generate M3U Playlists
Export channels as standard M3U playlists for use in other media players.

You can choose to export a single country or all countries at once.

6. Automatic Bouquet Updates
Schedule automatic updates for your exported bouquets to keep the channel list up to date.

Choose between interval-based (every X minutes) or fixed time updates.

7. Proxy Integration
The plugin uses a built-in proxy to handle channel resolution and streaming.

The proxy runs locally on your receiver and manages authentication and stream URLs.

8. Customization
Change the plugin's appearance: background images and fonts.

Configure various settings: server, DNS, bouquet position, and more.

9. User-Friendly Interface
Simple and intuitive interface designed for ease of use.

Support for multiple screen resolutions (HD, FHD, WQHD).

10. Multi-Language Support
The plugin supports multiple languages, including right-to-left languages like Arabic.

---
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

---

BROWSER COMMANDS / API ENDPOINTS
"""
VAVOO PROXY ENDPOINTS (127.0.0.1:4323)
1. /status - Proxy status
URL: http://127.0.0.1:4323/status
Description: Returns the current status of the proxy, including initialization, number of channels, addonSig validity, local IP and port.

2. /channels?country=CountryName - Get channels for a country
URL: http://127.0.0.1:4323/channels?country=Italy
Description: Returns the list of channels for the specified country. Country names must be URL-encoded.

3. /vavoo?channel=ChannelID - Resolve a channel by ID
URL: http://127.0.0.1:4323/vavoo?channel=abc123
Description: Returns a 302 redirect to the stream URL for the given channel ID. This is the primary endpoint for playback.

4. /catalog - Full catalog
URL: http://127.0.0.1:4323/catalog
Description: Returns the entire channel catalog in JSON format (all channels with proxy URLs).

5. /countries - List all countries
URL: http://127.0.0.1:4323/countries
Description: Returns a list of all unique countries available in the catalog.

6. /refresh_token - Refresh addonSig token
URL: http://127.0.0.1:4323/refresh_token
Description: Forces a refresh of the authentication token (addonSig).

7. /shutdown - Shutdown proxy
URL: http://127.0.0.1:4323/shutdown
Description: Gracefully shuts down the proxy server.
"""
---

## 🔧 PROXY FEATURES

### Currently Working

* Automatic country filtering (uses `COUNTRY_SETTINGS` for LANGUAGE/REGION)
* Automatic authentication (addonSig refreshes every 10 minutes)
* Stream resolution with correct country-specific settings
* Automatically generated M3U playlist using proxy URLs
* Enigma2 bouquet support with URLs pointing to the proxy

### No Longer Supported

* Direct access to `vavoo.to` without the proxy
* M3U export with direct URLs (old format)
* Manual authentication

---

## HOW TO MANAGE EXPORTS

### 1. Bouquet Export (Working)

**Path:** Plugin menu → Select country → GREEN button (Export Fav)

**What it does:**
Creates Enigma2 bouquets with URLs in the following format:

```
http://127.0.0.1:4323/vavoo?channel=CHANNEL_ID
```

**Requirement:**
The proxy must be running during the export.

---

### 2. M3U Export (To Be Tested)

**Path:** Config Menu → “Generate .m3u files” → OK

**What it does:**
Downloads `/playlist.m3u` from the proxy and saves it as:

```
vavoo_[country]_playlist.m3u
```

**Resulting file:**
Contains all channels with proxy URLs.

---

### 3. Export Verification

```bash
# Check if bouquets were created
ls -la /etc/enigma2/*.vavoo*

# Check the contents of a bouquet
grep "vavoo" /etc/enigma2/userbouquet.vavoo_italy.tv

# You should see URLs like:
# http://127.0.0.1:4323/vavoo?channel=abc123
```

---

## ▶️ HOW TO RUN THE PLAYER

### Normal Flow

* Plugin opened → Proxy starts automatically
* Select country → Proxy configured for that country
* Select channel → Player starts with proxy URL
* Player → Requests stream from proxy → Proxy resolves → Stream plays

### From Enigma2 Bouquets

* Enigma2 channel list → Select a Vavoo channel
* Enigma2 → Requests
  `http://127.0.0.1:4323/vavoo?channel=...`
* Proxy → **Must be running!** → Resolves stream → Playback starts

---

## IF SOMETHING DOESN’T WORK

### Quick Diagnostics

```bash
# 1. Check if the proxy is running
curl -s http://127.0.0.1:4323/status | python -m json.tool

# 2. Check connection to vavoo.to
curl -I https://vavoo.to

# 3. Check proxy logs
cat /tmp/vavoo_proxy.log 2>/dev/null || echo "No proxy log"

# 4. Check plugin logs
cat /tmp/vavoo.log 2>/dev/null || echo "No plugin log"
```

---

### Common Issues and Solutions

| Problem                  | Likely Cause               | Solution                                        |
| ------------------------ | -------------------------- | ----------------------------------------------- |
| “No channels found”      | Proxy not initialized      | Restart plugin, check internet                  |
| Bouquets do not open     | Proxy not running          | Start proxy: `python /path/to/vavoo_proxy.py &` |
| Stream does not start    | addonSig expired           | Proxy should refresh it automatically           |
| M3U export fails         | Proxy not responding       | Check port 4323: `netstat -tlnp \| grep 4323`   |
| Only some countries work | Missing `COUNTRY_SETTINGS` | Add country to map in `vavoo_proxy.py`          |

---

### Recovery Commands

```bash
# Restart the proxy manually
pkill -f vavoo_proxy.py
python /usr/lib/enigma2/python/Plugins/Extensions/vavoo/vavoo_proxy.py > /tmp/proxy.log 2>&1 &

# Reload Enigma2 bouquets
wget -qO- "http://127.0.0.1/web/servicelistreload?mode=0" > /dev/null

# Clear cache
rm -f /tmp/vavoo_flags/* /tmp/vavoo.log
```

---

## KEY CONFIGURATION

### Files to Check

* `vavoo_proxy.py` – `COUNTRY_SETTINGS` and `PORT` configuration
* `bouquet_manager.py` – Ensure proxy URLs are used (around line ~230)
* `plugin.py` – Updated `generate_m3u` function
* `vUtils.py` – `is_proxy_ready`, `get_proxy_stream_url` functions

### Important Variables

```python
# Proxy port (configurable)
PORT = 4323

# Authentication timeout (10 minutes)
ADDON_SIG_TTL = 600

# Country → (LANGUAGE, REGION) mapping
COUNTRY_SETTINGS = {
    "Italy": ("it", "IT"),
    "USA": ("en", "US"),
    # ... other countries
}
```

---

## FULL TEST WORKFLOW

Follow these steps to verify everything works:

### Start Plugin

```bash
# From the Enigma2 box, open the Vavoo plugin
# Check logs for:
# "[✓] Proxy initialized successfully"
```

### Test Bouquet Export

* Enter a country (e.g. Italy)
* Press GREEN to export bouquets
* Verify:
  `/etc/enigma2/userbouquet.vavoo_italy.tv` exists

### Test Playback from Plugin

* Select a channel in the plugin
* Verify playback starts

### Test Playback from Bouquets

* Exit plugin
* Go to Enigma2 channel list
* Open bouquet “Italy”
* Play a channel

### Test M3U Export

* Config Menu → Generate .m3u
* Verify file in `/media/hdd/movie/` (or your configured directory)

---

## FREQUENTLY ASKED QUESTIONS

**Q: Do I need to keep the plugin open for bouquets to work?**
A: No. The proxy runs in the background. Bouquets work even after closing the plugin.

**Q: Can I use old bouquets with the new system?**
A: No. The URLs are different. You must re-export them.

**Q: How much memory does the proxy use?**
A: Very little (~20–50MB), only while resolving streams.

**Q: What if vavoo.to changes its API?**
A: You only need to update `vavoo_proxy.py`, not the entire plugin.

**Q: Can I use the proxy on other devices?**
A: Yes. Replace `127.0.0.1` with the box IP address in the configuration.

---

### If you have specific issues, please provide:

* What you are doing exactly
* The full error message
* Output of
  `curl -s http://127.0.0.1:4323/status`
* Contents of a non-working bouquet

---
