#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
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
"""

__author__ = "Lululla"
__license__ = "CC BY-NC-SA 4.0"

import gzip
import requests
import uuid
import time
import threading
import socket
from json import loads, dumps
import threading

_starting_lock = threading.Lock()
_starting = False


try:
    unicode
except NameError:
    unicode = str

socket.setdefaulttimeout(30)

try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from urlparse import urlparse, parse_qs
    print("[Proxy] Python 2 detected")
except ImportError:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse, parse_qs
    print("[Proxy] Python 3 detected")


# ========== CONFIGURAZIONE ==========
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

7. /health - Monitors proxy
URL: http://127.0.0.1:4323/health
Description: Monitors proxy health and restarts it if necessary.

8. /shutdown - Shutdown proxy
URL: http://127.0.0.1:4323/shutdown
Description: Gracefully shuts down the proxy server.
"""

# API Endpoints
TOKEN_ADDON_SIG = 600  # 10 minutes - TOKEN EXPIRES EVERY 10 MINUTES!
TOKEN_REFRESH_AGE = 480
PORT = 4323
GEOIP_URL = "https://www.vavoo.tv/geoip"
PING_URL = "https://www.lokke.app/api/app/ping"
PING_URL2 = "https://www.vavoo.tv/api/app/ping"
CATALOG_URL = "https://vavoo.to/mediahubmx-catalog.json"
RESOLVE_URL = "https://vavoo.to/mediahubmx-resolve.json"

HEADERS = {
    "accept": "*/*",
    "user-agent": "Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "close",
}


def decode_response(resp):
    """Decode gzip response if needed"""
    if resp.content[:2] == b'\x1f\x8b':
        return loads(gzip.decompress(resp.content))
    return resp.json()


class ProxyHealthMonitor:
    """Monitors proxy health and restarts it if necessary"""

    def __init__(self, proxy_instance):
        self.proxy = proxy_instance
        self.last_health_check = time.time()
        self.failure_count = 0
        self.max_failures = 3
        self.monitor_thread = None
        self.running = False

    def start(self):
        """Start the background health monitor"""
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        print("[Proxy Health Monitor] Started")

    def stop(self):
        """Stop the monitor"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)

    def _monitor_loop(self):
        """Main monitor loop"""
        while self.running:
            try:
                self._check_proxy_health()
                time.sleep(60)  # Check every 60 seconds
            except Exception as e:
                print("[Health Monitor] Error: " + str(e))
                time.sleep(30)

    def _check_proxy_health(self):
        """Check proxy health status"""
        try:
            # 1. Check if proxy responds
            response = requests.get(
                "http://127.0.0.1:{}/health".format(PORT), timeout=2)

            if response.status_code == 200:
                data = response.json()

                # 2. Check token status
                token_age = data.get("token_age", 0)
                # needs_refresh = data.get("needs_refresh", False)

                if token_age > 550:  # > 9 minutes (almost expired)
                    print(
                        "[Health Monitor] Old token (" +
                        str(token_age) +
                        "s), forcing refresh..."
                    )
                    self.proxy.refresh_addon_sig_if_needed(force=True)

                # 3. Reset failure count if everything is OK
                self.failure_count = 0
                self.last_health_check = time.time()

            else:
                self._handle_proxy_failure()

        except Exception as e:
            print("[Health Monitor] Proxy not responding: " + str(e))
            self._handle_proxy_failure()

    def _handle_proxy_failure(self):
        """Handle proxy failure"""
        self.failure_count += 1
        print(
            "[Health Monitor] Proxy failure #" +
            str(self.failure_count)
        )

        if self.failure_count >= self.max_failures:
            print(
                "[Health Monitor] Too many failures, attempting to restart proxy..."
            )
            self._restart_proxy()
            self.failure_count = 0

    def _restart_proxy(self):
        try:
            # 1. Try to shut down the current proxy
            try:
                requests.get(
                    "http://127.0.0.1:{}/shutdown".format(PORT),
                    timeout=2)
                time.sleep(2)
            except Exception:
                pass

            # 2. Kill proxy python processes
            import subprocess
            with open('/dev/null', 'w') as devnull:
                subprocess.call(
                    ["pkill", "-f", "python.*vavoo_proxy"],
                    stdout=devnull,
                    stderr=devnull
                )
            time.sleep(3)

            # 3. Restart the proxy
            global proxy
            proxy = VavooProxy()

            if proxy.initialize_proxy():
                server = HTTPServer(('0.0.0.0', PORT), VavooHTTPHandler)
                proxy.server = server
                server_thread = threading.Thread(
                    target=server.serve_forever, daemon=True)
                server_thread.start()
                print("[Health Monitor] Proxy restarted successfully")
                return True

        except Exception as e:
            print("[Health Monitor] Failed to restart proxy: " + str(e))
        return False


class VavooProxy:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        # 1. ADAPTER IMPROVED: more intelligent retries
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=5,
            pool_maxsize=5,
            max_retries=2,
            pool_block=False
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # 2. REPLACE request wrapper with safer version
        self.session.request = self._robust_request

        self.addon_sig_lock = threading.Lock()
        self.addon_sig_data = {"sig": None, "ts": 0}
        self.all_filtered_items = []
        self.initialized = False
        self.current_language = "en"
        self.current_region = "US"
        self.refresh_timer = None
        self.active_streams = {}
        self.last_heartbeat = time.time()
        self.server = None
        self.start_time = time.time()

        # 3. Start periodic refresh and Token Monitor
        self.start_periodic_refresh()
        self.start_token_monitor()
        print("[Proxy] Initialized at " + time.ctime())

    def _robust_request(self, method, url, **kwargs):
        """Simplified and safer version"""
        # Set reasonable timeouts
        if 'timeout' not in kwargs:
            kwargs['timeout'] = (5, 15)  # 5s connect, 15s read

        try:
            # SINGLE REQUEST, no infinite retries
            response = requests.Session.request(
                self.session, method, url, **kwargs)
            return response
        except (requests.exceptions.Timeout, socket.timeout) as e:
            print("[Proxy] Timeout on " + str(url) + ": " + str(e))
            raise
        except requests.exceptions.ConnectionError as e:
            print("[Proxy] Connection error on " + str(url) + ": " + str(e))
            raise
        except Exception as e:
            print("[Proxy] Error on " + str(url) + ": " + str(e))
            raise

    def start_token_monitor(self):
        """Monitor and refresh token automatically"""
        def token_monitor_loop():
            while True:
                time.sleep(30)  # Check every 30 seconds
                try:
                    with self.addon_sig_lock:
                        now = time.time()
                        if self.addon_sig_data["sig"]:
                            token_age = now - self.addon_sig_data["ts"]
                            # Refresh if token older than 8 minutes (480s)
                            if token_age > TOKEN_REFRESH_AGE:
                                print("[Token Monitor] Token old (" + \
                                      str(int(token_age)) + "s), refreshing...")
                                self.refresh_addon_sig_if_needed(force=True)

                    # ALSO: Send heartbeat to keep connections alive
                    try:
                        self.session.head("https://vavoo.to/", timeout=5)
                        self.last_heartbeat = now
                    except Exception as e:
                        print("[Token Monitor] Heartbeat error: " + str(e))

                except Exception as e:
                    print("[Token Monitor] Error: " + str(e))

        monitor_thread = threading.Thread(
            target=token_monitor_loop, daemon=True)
        monitor_thread.start()
        print("[Proxy] Token monitor started (with heartbeat)")

    def start_periodic_refresh(self):
        """Refresh token periodically (every 8 minutes)"""
        if self.refresh_timer:
            self.refresh_timer.cancel()

        self.refresh_timer = threading.Timer(
            TOKEN_REFRESH_AGE, self._periodic_refresh_task)
        self.refresh_timer.daemon = True
        self.refresh_timer.start()
        print("[Proxy] Periodic refresh scheduled (480s)")

    def _periodic_refresh_task(self):
        """Periodic task to refresh token"""
        try:
            print("[Proxy] Periodic refresh task running...")
            sig = self.refresh_addon_sig_if_needed(force=True)
            if sig:
                print("[Proxy] Token refreshed via periodic task")
        except Exception as e:
            print("[Proxy] Error in periodic refresh: " + str(e))

        # Schedule next refresh
        self.start_periodic_refresh()

    def refresh_addon_sig_if_needed(self, force=False):
        """Refresh the addonSig if needed with better error handling"""
        with self.addon_sig_lock:
            now = time.time()
            if not force and self.addon_sig_data["sig"] and (
                    now - self.addon_sig_data["ts"] < 300):  # 8 minutes
                return self.addon_sig_data["sig"]

            try:
                unique_id = str(uuid.uuid4())
                current_timestamp = int(time.time() * 1000)

                payload = {
                    "reason": "app-focus",
                    "locale": self.current_language,
                    "theme": "dark",
                    "metadata": {
                        "device": {
                            "type": "desktop",
                            "uniqueId": unique_id},
                        "os": {
                            "name": "win32",
                            "version": "Windows 10 Pro",
                            "abis": ["x64"],
                            "host": "Lenovo"},
                        "app": {
                            "platform": "electron"},
                        "version": {
                            "package": "tv.vavoo.app",
                            "binary": "3.1.8",
                            "js": "3.1.8"}},
                    "appFocusTime": 0,
                    "playerActive": False,
                    "playDuration": 0,
                        "devMode": False,
                        "hasAddon": True,
                        "castConnected": False,
                        "package": "tv.vavoo.app",
                        "version": "3.1.8",
                        "process": "app",
                        "firstAppStart": current_timestamp,
                        "lastAppStart": current_timestamp,
                        "ipLocation": None,
                        "adblockEnabled": True,
                        "proxy": {
                            "supported": ["ss"],
                            "engine": "Mu",
                            "enabled": False,
                            "autoServer": True},
                    "iap": {
                        "supported": False}}

                # Use the robust request method
                urls = [PING_URL, PING_URL2]
                sig = None
                for url in urls:
                    try:
                        r = self._robust_request(
                            "POST", url, json=payload, timeout=15)
                        r.raise_for_status()
                        data = decode_response(r)
                        sig = data.get("addonSig")
                        if sig:
                            break  # Found, exit loop
                        else:
                            print(
                                "[AddonSig] No addonSig received from {}".format(url))
                    except Exception as e:
                        print(
                            "[AddonSig] Request to {} failed: {}".format(
                                url, e))

                if sig:
                    self.addon_sig_data["sig"] = sig
                    self.addon_sig_data["ts"] = now
                else:
                    print("[AddonSig] Unable to obtain addonSig from any URL")

                """"
                # r = self._robust_request(
                    # "POST", PING_URL, json=payload, timeout=15)
                # r.raise_for_status()
                # data = decode_response(r)
                # sig = data.get("addonSig")
                # if not sig:
                    # raise RuntimeError("No addonSig received")
                # self.addon_sig_data["sig"] = sig
                # self.addon_sig_data["ts"] = now
                """
                print("[Proxy] Token refreshed successfully")
                return sig

            except Exception as e:
                print("[Proxy] Error updating addonSig: " + str(e))
                if self.addon_sig_data["sig"]:
                    print("[Proxy] Using old token")
                    return self.addon_sig_data["sig"]
                return None

    def initialize_proxy(self):
        """Initialize the proxy by loading the catalog with fallback"""
        try:
            print("[Proxy] Initializing...")

            # First, obtain a valid token
            sig = self.refresh_addon_sig_if_needed()
            if not sig:
                print(
                    "[Proxy] Warning: Could not get a valid token, but continuing anyway")
                # We may continue with an old token or no token at all

            # Load the catalog
            print("[Proxy] Attempting to load catalog...")
            all_channels = self.load_catalog(sig)

            if not all_channels or len(all_channels) == 0:
                print("[Proxy] Warning: Catalog is empty or failed to load")
                # Create an empty list but mark as initialized
                self.all_filtered_items = []
                self.initialized = True
                print("[Proxy] Initialized with empty catalog")
                return True

            self.all_filtered_items = all_channels
            self.initialized = True

            # Analysis
            countries = set()
            for channel in all_channels:
                country = channel.get("country")
                if country and country != "default":
                    countries.add(country)

            print(
                "[Proxy] ✓ Initialized: %d channels, %d countries" %
                (len(all_channels), len(countries))
            )
            return True

        except Exception as e:
            print("[Proxy] Initialization error: %s" % str(e))
            # Even in case of error, try to continue with an empty catalog
            print("[Proxy] Continuing with empty catalog")
            self.all_filtered_items = []
            self.initialized = True
            return True  # Always return True; the proxy can work even without a catalog

    def load_catalog(self, sig):
        """Load the complete catalog with better error handling"""
        try:
            catalog_headers = {
                "content-type": "application/json; charset=utf-8",
                "mediahubmx-signature": sig,
                "user-agent": "MediaHubMX/2",
                "accept": "*/*",
                "Accept-Language": self.current_language,
                "Accept-Encoding": "gzip, deflate",
                "Connection": "close",
            }

            all_channels = []
            cursor = None
            page = 1
            max_retries = 3

            print("[Proxy] Loading catalog...")

            while True:
                catalog_payload = {
                    "language": self.current_language,
                    "region": self.current_region,
                    "catalogId": "iptv",
                    "id": "iptv",
                    "adult": False,
                    "search": "",
                    "sort": "",
                    "filter": {},
                    "cursor": cursor,
                    "clientVersion": "3.0.2"
                }

                success = False
                last_exception = None

                for attempt in range(max_retries):
                    try:
                        print(
                            "[Proxy] Fetching catalog page {0} (attempt {1}/{2})" .format(
                                page, attempt + 1, max_retries))

                        r_catalog = self.session.post(
                            CATALOG_URL,
                            json=catalog_payload,
                            headers=catalog_headers,
                            timeout=30
                        )

                        if r_catalog.status_code == 502:
                            print(
                                "[Proxy] 502 Bad Gateway on page {0}, attempt {1}" .format(
                                    page, attempt + 1))
                            if attempt < max_retries - 1:
                                # Backoff esponenziale
                                time.sleep(2 ** attempt)
                                continue
                            else:
                                print(
                                    "[Proxy] Giving up on page {0} after {1} attempts" .format(
                                        page, max_retries))
                                break

                        r_catalog.raise_for_status()
                        catalog_data = decode_response(r_catalog)
                        success = True
                        break

                    except requests.exceptions.HTTPError as e:
                        last_exception = e
                        print("[Proxy] HTTP error on page {0}: {1}"
                              .format(page, e))

                        if e.response.status_code == 502 and attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                            continue
                        else:
                            break

                    except Exception as e:
                        last_exception = e
                        print("[Proxy] Error on page {0}: {1}"
                              .format(page, e))
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                            continue
                        else:
                            break

                if not success:
                    print(
                        "[Proxy] Failed to load page {0}, stopping catalog download" .format(page))
                    if last_exception:
                        print("[Proxy] Last error: {0}"
                              .format(last_exception))
                    break

                items = catalog_data.get("items", [])
                if not items:
                    print("[Proxy] No more items on page {0}"
                          .format(page))
                    break

                # Process items
                items_processed = 0
                for item in items:
                    if item.get("type") == "iptv":
                        group = item.get("group", "")
                        base_country = group

                        # Extract country
                        separators = ["➾", "⟾", "->", "→", "»", "›"]
                        for sep in separators:
                            if sep in base_country:
                                base_country = base_country.split(sep)[
                                    0].strip()
                                break

                        if not base_country:
                            base_country = "default"

                        channel_data = {
                            "country": base_country,
                            "id": item["ids"]["id"],
                            "name": item["name"],
                            "url": item["url"],
                            "logo": item.get("logo", ""),
                            "group": group
                        }

                        all_channels.append(channel_data)
                        items_processed += 1

                print(
                    "[Proxy] Page {0}: processed {1} items, total {2} channels" .format(
                        page, items_processed, len(all_channels)))

                cursor = catalog_data.get("nextCursor")
                if not cursor:
                    print("[Proxy] No more pages, catalog complete")
                    break

                page += 1

                if page % 5 == 0:
                    time.sleep(1)

            print("[Proxy] Catalog loaded: {0} channels in {1} pages"
                  .format(len(all_channels), page - 1))
            return all_channels
        except Exception as e:
            print("[Proxy] Catalog load error: %s" % str(e))
            from .vUtils import trace_error
            trace_error()
            if all_channels:
                print("[Proxy] Returning {0} channels already loaded"
                      .format(len(all_channels)))
                return all_channels
            return None

    def resolve_with_retry(self, channel_url, max_retries=3):
        """Resolve URLs with retries and improved error handling"""
        if not channel_url:
            print("[Proxy] No channel URL provided")
            return None

        for attempt in range(max_retries):
            try:
                # First, try to obtain a fresh token if needed
                if attempt > 0:
                    self.refresh_addon_sig_if_needed(force=True)

                resolve_headers = {
                    "content-type": "application/json; charset=utf-8",
                    "mediahubmx-signature": self.addon_sig_data["sig"],
                    "user-agent": "MediaHubMX/2",
                    "accept": "*/*",
                    "Accept-Language": self.current_language,
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "close",
                }

                resolve_payload = {
                    "language": self.current_language,
                    "region": self.current_region,
                    "url": channel_url,
                    "clientVersion": "3.0.2"
                }

                print(
                    "[Proxy] Resolving channel URL (attempt %d/%d)" %
                    (attempt + 1, max_retries)
                )

                r_resolve = self.session.post(
                    RESOLVE_URL,
                    json=resolve_payload,
                    headers=resolve_headers,
                    timeout=15
                )

                # Handle HTTP errors
                if r_resolve.status_code == 502:
                    print(
                        "[Proxy] 502 Bad Gateway on resolve, attempt %d" %
                        (attempt + 1)
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        print("[Proxy] Giving up on resolve after max retries")
                        return None

                r_resolve.raise_for_status()
                result = decode_response(r_resolve)

                if result and len(result) > 0:
                    stream_url = result[0].get("url")
                    if stream_url:
                        print("[Proxy] Successfully resolved channel URL")
                        return stream_url
                    else:
                        print("[Proxy] No stream URL in response")
                else:
                    print("[Proxy] Empty response from resolve")

            except requests.exceptions.HTTPError as e:
                print(
                    "[Proxy] HTTP error in resolve attempt %d: %s" %
                    (attempt + 1, str(e))
                )
                if (
                    e.response is not None and
                    e.response.status_code == 502 and
                    attempt < max_retries - 1
                ):
                    time.sleep(2 ** attempt)
                    continue
                else:
                    break

            except Exception as e:
                print(
                    "[Proxy] Error in resolve attempt %d: %s" %
                    (attempt + 1, str(e))
                )
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    break

        print("[Proxy] Failed to resolve channel URL after all retries")
        return None

    def get_local_ip(self):
        """Get local IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except BaseException:
            return "127.0.0.1"


class VavooHTTPHandler(BaseHTTPRequestHandler):
    timeout = 10

    def safe_write(self, data):
        try:
            if isinstance(data, unicode):
                data = data.encode('utf-8')
            elif not isinstance(data, bytes):
                data = str(data).encode('utf-8')
            self.wfile.write(data)
            self.wfile.flush()
        except (socket.error, IOError):
            return False
        return True

    def safe_send_response(self, code, message=None):
        """Safe response sending"""
        try:
            if message:
                self.send_response(code, message)
            else:
                self.send_response(code)
        except (BrokenPipeError, ConnectionResetError):
            print("[Proxy] Client disconnected during response - ignoring")
            return False
        return True

    def do_GET(self):
        client_address = self.client_address[0]
        print("[Proxy] Request from {0}: {1}"
              .format(client_address, self.path))
        try:
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)

            if parsed_path.path == '/vavoo':
                channel_id = query_params.get('channel', [None])[0]
                if not channel_id:
                    self.send_error(400, "Missing channel parameter")
                    return

                channel = None
                if hasattr(proxy, 'all_filtered_items'):
                    for ch in proxy.all_filtered_items:
                        if ch.get("id") == channel_id:
                            channel = ch
                            break

                if not channel:
                    self.send_error(404, "Channel not found")
                    return

                try:
                    # 1. Resolve the Vavoo stream URL
                    stream_url = proxy.resolve_with_retry(channel.get("url"))
                    if not stream_url:
                        self.send_error(404, "Stream not resolved")
                        return

                    # 2. Quick test to see if the stream is reachable
                    try:
                        test_response = proxy.session.get(
                            stream_url, stream=True, timeout=5)
                        test_response.raise_for_status()

                        # Read first 1024 bytes to check if data exists
                        test_chunk = next(
                            test_response.iter_content(
                                chunk_size=1024), None)
                        test_response.close()

                        if not test_chunk:
                            print(
                                "[Proxy] WARNING: Upstream stream returned empty data for channel: " +
                                channel_id)

                    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                        print(
                            "[Proxy] CRITICAL: Cannot reach upstream stream for channel " +
                            channel_id +
                            ": " +
                            str(e))
                        self.send_error(502, "Cannot connect to video source")
                        return
                    except Exception as e:
                        print(
                            "[Proxy] Warning during stream test for " +
                            channel_id +
                            ": " +
                            str(e))
                        # Proceed anyway, might be a false positive

                    # 3. If the test is OK (or we decide to proceed), do a 302
                    # REDIRECT
                    if not self.safe_send_response(302):
                        return

                    self.send_header('Location', stream_url)
                    self.end_headers()
                    print(
                        "[Proxy] 302 Redirect to upstream stream for channel: " +
                        channel_id)

                except Exception as e:
                    print("[Proxy] Error in /vavoo handler: " + str(e))
                    self.send_error(500, "Internal proxy error")

            elif parsed_path.path == '/stream':
                """True streaming proxy with keep-alive monitoring
                # Change from:
                service_url = "http://127.0.0.1:4323/vavoo?channel=" + channel_id
                # To:
                service_url = "http://127.0.0.1:4323/stream?channel=" + channel_id
                """
                channel_id = query_params.get('channel', [None])[0]
                if not channel_id:
                    self.send_error(400, "Missing channel parameter")
                    return

                channel = None
                if hasattr(proxy, 'all_filtered_items'):
                    for ch in proxy.all_filtered_items:
                        if ch.get("id") == channel_id:
                            channel = ch
                            break

                if not channel:
                    self.send_error(404, "Channel not found")
                    return

                try:
                    # 1. Get stream URL
                    stream_url = proxy.resolve_with_retry(channel["url"])
                    if not stream_url:
                        self.send_error(404, "Stream not resolved")
                        return

                    # 2. Connect to upstream with streaming
                    upstream = proxy.session.get(
                        stream_url, stream=True, timeout=30)
                    upstream.raise_for_status()

                    # 3. Send headers to player
                    if not self.safe_send_response(200):
                        return
                    self.send_header(
                        'Content-Type',
                        upstream.headers.get(
                            'Content-Type',
                            'video/mp2t'))
                    self.send_header('Connection', 'keep-alive')
                    self.end_headers()

                    # 4. Forward data with timeout monitoring
                    last_data_time = time.time()
                    try:
                        for chunk in upstream.iter_content(chunk_size=8192):
                            if chunk:
                                self.wfile.write(chunk)
                                self.wfile.flush()
                                last_data_time = time.time()
                            else:
                                # Empty chunk - check if upstream is dead
                                if time.time() - last_data_time > 10:  # 10 seconds timeout
                                    print(
                                        "[Proxy Stream] Upstream timeout for channel: " + channel_id)
                                    break
                                time.sleep(0.1)
                    except (socket.timeout, ConnectionError, BrokenPipeError) as e:
                        print("[Proxy Stream] Downstream error: " + str(e))
                    finally:
                        upstream.close()
                        print(
                            "[Proxy Stream] Finished for channel: " +
                            channel_id)

                except Exception as e:
                    print("[Proxy Stream] Error: " + str(e))
                    self.send_error(500, "Streaming error")

            elif parsed_path.path == '/channels':
                country = query_params.get('country', [None])[0]
                if not country:
                    self.send_error(400, "Missing country parameter")
                    return

                matching_channels = []
                if hasattr(proxy, 'all_filtered_items'):
                    for channel in proxy.all_filtered_items:
                        channel_country = channel.get("country", "")
                        if channel_country.lower() == country.lower():
                            matching_channels.append(channel)

                response_channels = []
                local_ip = proxy.get_local_ip()

                for channel in matching_channels:
                    channel_id = channel.get("id", "")
                    if channel_id:
                        proxy_url = "http://%s:%d/vavoo?channel=%s" % (
                            local_ip, PORT, channel_id)
                        response_channels.append({
                            "id": channel_id,
                            "name": channel.get("name", ""),
                            "url": proxy_url,
                            "logo": channel.get("logo", ""),
                            "country": channel.get("country", country)
                        })

                if not self.safe_send_response(200):
                    return
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                if not self.safe_write(dumps(response_channels)):
                    return

            elif parsed_path.path == '/catalog':
                if hasattr(proxy, 'all_filtered_items'):
                    if not self.safe_send_response(200):
                        return
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    if not self.safe_write(dumps(proxy.all_filtered_items)):
                        return
                else:
                    self.send_error(404, "No catalog loaded")

            elif parsed_path.path == '/countries':
                countries = set()
                if hasattr(proxy, 'all_filtered_items'):
                    for channel in proxy.all_filtered_items:
                        country = channel.get("country", "")
                        if country and country != "default":
                            countries.add(country)

                countries_list = sorted(list(countries))
                if not self.safe_send_response(200):
                    return
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                if not self.safe_write(dumps(countries_list)):
                    return

            elif parsed_path.path == '/status':
                status = {
                    "initialized": proxy.initialized,
                    "channels_count": len(
                        proxy.all_filtered_items),
                    "addon_sig_valid": proxy.addon_sig_data["sig"] is not None,
                    "addon_sig_age": int(
                        time.time() -
                        proxy.addon_sig_data["ts"]),
                    "local_ip": proxy.get_local_ip(),
                    "port": PORT}

                if not self.safe_send_response(200):
                    return

                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                if not self.safe_write(dumps(status)):
                    return

            elif parsed_path.path == '/health':
                """Health check endpoint with detailed status"""
                try:
                    now = time.time()
                    token_age = now - proxy.addon_sig_data["ts"]
                    token_valid = proxy.addon_sig_data["sig"] is not None
                    needs_refresh = token_age > 300  # 8 minutes

                    # Calculate token expiration
                    ttl = max(0, TOKEN_ADDON_SIG - int(token_age))

                    # Check if proxy is initialized
                    initialized = proxy.initialized
                    channels_count = len(
                        proxy.all_filtered_items) if initialized else 0

                    # Proxy status
                    proxy_status = {
                        "status": "healthy" if initialized and token_valid else "unhealthy",
                        "initialized": initialized,
                        "channels_count": channels_count,
                        "token": {
                            "valid": token_valid,
                            "age": int(token_age),
                            "ttl": ttl,
                            "needs_refresh": needs_refresh,
                            "expires_in": str(ttl) + "s"
                        },
                        "system": {
                            "uptime": int(now - proxy.start_time if hasattr(proxy, 'start_time') else 0),
                            "heartbeat": int(now - proxy.last_heartbeat),
                            "port": PORT,
                            "local_ip": proxy.get_local_ip()
                        },
                        "timestamp": now,
                        "message": "Proxy is running normally" if initialized else "Proxy not initialized"
                    }

                    # Refresh token if needed
                    if needs_refresh and token_valid:
                        sig = proxy.refresh_addon_sig_if_needed(force=True)
                        proxy_status["token"]["refreshed"] = sig is not None
                        proxy_status["message"] = "Token refreshed" if sig else "Token refresh failed"

                    # self.send_response(200)
                    if not self.safe_send_response(200):
                        return
                    self.send_header('Content-Type', 'application/json')
                    self.send_header(
                        'Cache-Control',
                        'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Expires', '0')
                    self.end_headers()
                    if not self.safe_write(dumps(proxy_status)):
                        return
                except Exception as e:
                    error_response = {
                        "status": "error",
                        "message": str(e),
                        "timestamp": time.time()
                    }
                    if not self.safe_send_response(500):
                        return
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    if not self.safe_write(dumps(error_response)):
                        return

            elif parsed_path.path == '/refresh_token':
                sig = proxy.refresh_addon_sig_if_needed(force=True)
                response = {
                    "status": "success" if sig else "error",
                    "message": "Token refreshed" if sig else "Failed to refresh token"}
                if not self.safe_send_response(200):
                    return
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                if not self.safe_write(dumps(response)):
                    return

            elif parsed_path.path == '/shutdown':
                if not self.safe_send_response(200):
                    return
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                if not self.safe_write(b"Proxy shutting down..."):
                    return

                def shutdown_server():
                    time.sleep(1)
                    if proxy.server:
                        proxy.server.shutdown()

                threading.Thread(target=shutdown_server, daemon=True).start()

            else:
                self.send_error(404, "Not Found")

        except BrokenPipeError:
            print("[Proxy] Client disconnected (BrokenPipeError)")
            return
        except ConnectionResetError:
            print("[Proxy] Connection reset by client")
            return
        except Exception as e:
            print("[Handler] Error: %s" % str(e))
            try:
                self.send_error(500, "Internal Server Error")
            except (BrokenPipeError, ConnectionResetError):
                print("[Proxy] Client gone while sending error")
                return

    def handle_one_request(self):
        """Gestisci una singola richiesta con cleanup garantito"""
        try:
            BaseHTTPRequestHandler.handle_one_request(self)
        except (socket.timeout, socket.error) as e:
            print("[Proxy] Socket error in request: " + str(e))
            try:
                self.connection.close()
            except BaseException:
                pass
        except Exception as e:
            print("[Proxy] Unexpected error in request: " + str(e))

    def finish(self):
        """Override finish per gestire cleanup"""
        try:
            BaseHTTPRequestHandler.finish(self)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def setup(self):
        """Setup con timeout"""
        BaseHTTPRequestHandler.setup(self)
        self.request.settimeout(self.timeout)

    def log_message(self, format, *args):
        pass


proxy = VavooProxy()


def shutdown_proxy():
    """Shutdown the proxy server if running."""
    try:
        response = requests.get(
            "http://127.0.0.1:{}/shutdown".format(PORT), timeout=2)
        if response.status_code == 200:
            print("[Proxy] Shutdown request sent successfully")
            return True
    except Exception as e:
        print("[Proxy] Shutdown via HTTP failed: {}".format(e))

    # Fallback: kill process
    try:
        import subprocess
        subprocess.call(["pkill", "-f", "python.*vavoo_proxy"])
        print("[Proxy] Killed by pkill")
        return True
    except Exception as e:
        print("[Proxy] Failed to kill process: {}".format(e))
    return False


def start_proxy():
    """Start the proxy server with restart on failure"""

    global proxy
    max_restarts = 3
    restart_count = 0

    while restart_count < max_restarts:
        try:
            print("=" * 50)
            print("VAVOO PROXY v1.0 (Attempt " +
                  str(restart_count + 1) + "/" + str(max_restarts) + ")")
            print("=" * 50)

            if not proxy.initialize_proxy():
                print("[✗] Failed to initialize proxy")
                restart_count += 1
                if restart_count < max_restarts:
                    time.sleep(3)
                    proxy = VavooProxy()  # Recreate proxy
                    continue
                else:
                    print("[✗] Max restart attempts reached")
                    return False

            server = HTTPServer(('0.0.0.0', PORT), VavooHTTPHandler)
            server.timeout = 30
            server.request_queue_size = 10
            proxy.server = server
            local_ip = proxy.get_local_ip()

            print("[✓] Channels: " + str(len(proxy.all_filtered_items)))
            print("[✓] IP: " + str(local_ip) + ":" + str(PORT))
            print("[✓] Timeout: " + str(server.timeout) + "s")
            print("[✓] Ready")
            print("=" * 50)

            # Reset restart counter on success
            restart_count = 0

            try:
                server.serve_forever(poll_interval=0.5)
            except KeyboardInterrupt:
                print("\n[!] Proxy stopped by user")
                break
            except Exception as e:
                print("[✗] Server error: " + str(e))
                restart_count += 1
                if restart_count < max_restarts:
                    print("[!] Restarting proxy in 5 seconds...")
                    time.sleep(5)
                    # Shutdown old server if exists
                    if proxy.server:
                        try:
                            proxy.server.shutdown()
                            proxy.server.server_close()
                        except BaseException:
                            pass
                    proxy = VavooProxy()  # Recreate proxy
                    continue

        except Exception as e:
            print("[✗] Critical error: " + str(e))
            from .vUtils import trace_error
            trace_error()
            restart_count += 1
            if restart_count < max_restarts:
                print("[!] Restarting proxy in 5 seconds...")
                time.sleep(5)
                # Shutdown old server if exists
                if proxy.server:
                    try:
                        proxy.server.shutdown()
                        proxy.server.server_close()
                    except BaseException:
                        pass
                proxy = VavooProxy()  # Recreate proxy
                continue

    print("[✗] Proxy cannot start after " + str(max_restarts) + " attempts")
    return False


def run_proxy_in_background():
    """Start the proxy in background only if it is not already running"""
    global _starting
    with _starting_lock:
        if _starting:
            print("[Proxy] Already starting, skipping...")
            return False
        _starting = True

    try:
        def is_proxy_running():
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    return s.connect_ex(('127.0.0.1', PORT)) == 0
            except BaseException:
                return False

        # If already running, perform a health check
        if is_proxy_running():
            from os import system
            try:
                response = requests.get(
                    "http://127.0.0.1:{}/status".format(PORT), timeout=2)
                if response.status_code == 200:
                    return True
                else:
                    # Proxy is running but not responding, kill it
                    print("[Proxy] Proxy is running but not responding, killing...")
                    system("pkill -f 'python.*vavoo_proxy' 2>/dev/null")
                    time.sleep(2)
            except BaseException:
                # Proxy not responding, kill it
                system("pkill -f 'python.*vavoo_proxy' 2>/dev/null")
                time.sleep(2)

        # Start new proxy
        proxy_thread = threading.Thread(target=start_proxy)
        proxy_thread.setDaemon(True)
        proxy_thread.start()

        # Wait for startup with longer timeout
        for i in range(30):  # 30 attempts
            if is_proxy_running():
                try:
                    # Health check
                    response = requests.get(
                        "http://127.0.0.1:{}/status".format(PORT), timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("initialized", False):
                            print("[Proxy] Started and initialized successfully")
                            return True
                except BaseException:
                    pass
            time.sleep(1)

        print("[Proxy] Failed to start within timeout")
        return False
    finally:
        with _starting_lock:
            _starting = False


if __name__ == "__main__":
    start_proxy()
