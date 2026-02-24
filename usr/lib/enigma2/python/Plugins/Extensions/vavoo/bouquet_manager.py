#!/usr/bin/python
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

import io
import time
from json import loads
from os import listdir, remove
from os.path import exists as file_exists, isfile, join
from re import compile
from sys import version_info

try:
    from urllib.parse import unquote, quote
except ImportError:
    from urllib import unquote, quote

from enigma import eDVBDB, eTimer
from Tools.Directories import SCOPE_PLUGINS, resolveFilename

from .vUtils import (
    # getAuthSignature,
    get_proxy_channels,
    getUrl,
    decodeHtml,
    rimuovi_parentesi,
    sanitizeFilename,
    trace_error
)

PORT = 4323

# Constants
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('vavoo'))
PY2 = version_info[0] == 2
PY3 = version_info[0] == 3


def get_enigma2_path():
    barry_active = '/media/ba/active/etc/enigma2'
    if file_exists(barry_active):
        return barry_active.rstrip('/')

    possible_paths = [
        '/autofs/sda1/etc/enigma2',
        '/autofs/sda2/etc/enigma2',
        '/etc/enigma2'
    ]
    for path in possible_paths:
        if file_exists(path):
            return path.rstrip('/')
    return '/etc/enigma2'


ENIGMA_PATH = get_enigma2_path()


def get_local_ip():
    """Get the local IP address"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except BaseException:
        return "127.0.0.1"


def _reload_services_after_delay(delay=3000):
    """Reload services after a manual edit"""
    try:
        def do_reload():
            try:
                db = eDVBDB.getInstance()
                if db:
                    db.reloadBouquets()
                    print("Bouquets reloaded successfully")
                else:
                    print("Could not get eDVBDB instance for reload")
            except Exception as e:
                print("Error during service reload: " + str(e))

        reload_timer = eTimer()
        try:
            # Python 3
            reload_timer.callback.append(do_reload)
        except Exception:
            # Python 2
            reload_timer.timeout.connect(do_reload)
        reload_timer.start(delay, True)

    except Exception as e:
        print("Error setting up service reload: " + str(e))


def _add_to_main_bouquet(bouquet_name, bouquet_type, list_position="bottom"):
    """Add bouquet reference to the main bouquet file"""
    main_bouquet_path = join(ENIGMA_PATH, "bouquets." + bouquet_type.lower())

    if not bouquet_name.startswith("userbouquet."):
        print("DEBUG: Skipping " + bouquet_name + " - not a userbouquet")
        return

    bouquet_line = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + \
        bouquet_name + '" ORDER BY bouquet\n'

    try:
        # Read existing content
        if isfile(main_bouquet_path):
            with open(main_bouquet_path, 'r') as f:
                lines = f.readlines()
        else:
            lines = []

        # Check if bouquet already exists
        bouquet_already_exists = False
        for line in lines:
            if bouquet_name in line and 'FROM BOUQUET' in line:
                bouquet_already_exists = True
                break

        if bouquet_already_exists:
            print(
                "DEBUG: Bouquet " +
                bouquet_name +
                " already exists in main bouquet file")
            return

        # Remove all Vavoo lines first
        non_vavoo_lines = []
        vavoo_lines = []

        for line in lines:
            if 'vavoo' in line.lower():
                vavoo_lines.append(line)
            else:
                non_vavoo_lines.append(line)

        # Remove the specific bouquet if already exists in Vavoo lines
        vavoo_lines = [
            line for line in vavoo_lines if bouquet_name not in line]

        # Add the current bouquet to Vavoo lines
        vavoo_lines.append(bouquet_line)

        position_info = list_position

        # Configurable position
        if list_position == "top":
            new_lines = vavoo_lines + non_vavoo_lines
            position_info = "top"
        else:
            new_lines = non_vavoo_lines + vavoo_lines
            position_info = "bottom"

        # Write file
        with open(main_bouquet_path, 'w') as f:
            f.writelines(new_lines)

        print(
            "Added " +
            bouquet_name +
            " to " +
            position_info +
            " (all Vavoo grouped)")

    except Exception as e:
        print("Error adding to main bouquet: " + str(e))


def deep_clean_bouquet_files():
    """Remove Vavoo references from main bouquet files"""
    try:
        for bfile in ['bouquets.tv', 'bouquets.radio']:
            bouquet_path = join(ENIGMA_PATH, bfile)
            if file_exists(bouquet_path):
                with open(bouquet_path, 'r') as f:
                    lines = f.readlines()

                # Keep only lines that do not contain ".vavoo_"
                new_lines = [line for line in lines if '.vavoo_' not in line]

                with open(bouquet_path, 'w') as f:
                    f.writelines(new_lines)

                print("✓ Cleaned: " + bfile)

    except Exception as e:
        print("Error in deep clean: " + str(e))


def remove_bouquets_by_name(name=None):
    """Remove Vavoo bouquets by name. If name is None, remove all Vavoo bouquets."""
    try:
        removed_count = 0
        for fname in listdir(ENIGMA_PATH):
            if '.vavoo_' in fname and (
                    fname.endswith('.tv') or fname.endswith('.radio')):
                if name is not None:
                    name_safe = name.lower().replace(
                        ' ',
                        '_').replace(
                        '➾',
                        '_').replace(
                        '⟾',
                        '_').replace(
                        '->',
                        '_')
                    if name_safe not in fname:
                        continue

                bouquet_path = join(ENIGMA_PATH, fname)
                try:
                    remove(bouquet_path)
                    removed_count += 1
                    print("✓ Removed: " + fname)
                except Exception as e:
                    print("Error removing " + fname + ": " + str(e))

        deep_clean_bouquet_files()
        return removed_count
    except Exception as e:
        print("Error removing bouquets: " + str(e))
        return 0


def convert_bouquet(
        servicetype,
        name,
        url,
        export_type,
        server,
        bouquet_position):
    """Create bouquet using PROXY only - ignore URL parameter"""
    try:
        print("[Bouquet] Creating bouquet for: " + name)
        print("[Bouquet] Ignoring URL parameter (proxy only system)")
        # 1. Check if proxy is running
        from .vUtils import is_proxy_ready, is_proxy_running
        from .vavoo_proxy import run_proxy_in_background

        if not is_proxy_running():
            print("[Bouquet] Proxy not running, starting...")
            if not run_proxy_in_background():
                print("[Bouquet] Failed to start proxy")
                return 0

        # 2. Wait until proxy is ready
        print("[Bouquet] Waiting for proxy to be ready...")
        for i in range(15):  # 15 attempts, 1 second each
            if is_proxy_ready(timeout=2):
                print("[Bouquet] Proxy is ready")
                break
            if i % 5 == 0:
                print("[Bouquet] Still waiting for proxy... (" + str(i + 1) + "/15)")
            time.sleep(1)
        else:
            print("[Bouquet] Proxy not ready after 15 seconds")
            return 0

        # 3. Get channels from proxy
        print("[Bouquet] Retrieving channels from proxy for: " + name)
        channels = get_channels_from_proxy(name, export_type)

        if not channels or len(channels) == 0:
            print("[Bouquet] No channels received from proxy for: " + name)
            return 0

        print("[Bouquet] Received " +
              str(len(channels)) +
              " channels from proxy")

        # 4. Create bouquet file
        bouquet_count = create_bouquet_file(
            name, channels, servicetype, export_type, bouquet_position)

        if bouquet_count > 0:
            print("[Bouquet] Successfully created bouquet: " +
                  name + " (" + str(bouquet_count) + " channels)")
            # Reload services
            _reload_services_after_delay(2000)
        else:
            print("[Bouquet] Failed to create bouquet file for: " + name)

        return bouquet_count

    except Exception as e:
        print("[Bouquet] Error creating bouquet for " + name + ": " + str(e))
        trace_error()
        return 0


def get_channels_from_proxy(name, export_type):
    """Get channels from the proxy"""
    try:
        # Encode the name
        encoded_name = quote(name)

        # Proxy URL
        proxy_url = "http://127.0.0.1:{}/channels?country={}".format(PORT, encoded_name)

        # Request to the proxy
        response = getUrl(proxy_url, timeout=30)

        if not response:
            print("[Proxy] No response for %s" % name)
            return []

        # JSON parsing
        try:
            channels = loads(response)
        except Exception:
            # Se response è bytes, decodifica
            if isinstance(response, bytes):
                channels = loads(response.decode('utf-8', 'ignore'))
            else:
                raise

        if not isinstance(channels, list):
            print("[Proxy] Invalid response format for %s" % name)
            return []

        print("[Proxy] Got %d channels for %s" % (len(channels), name))
        return channels

    except Exception as e:
        print("[Proxy] Error getting channels: %s" % str(e))
        trace_error()
        return []


def _prepare_bouquet_filenames(name, bouquet_type, max_length=100):
    """Prepare sanitized file names for bouquet creation with ReDoS protection"""
    # Convert to string and truncate to prevent excessively long inputs
    name_str = str(name)
    if len(name_str) > max_length:
        name_str = name_str[:max_length]
        print("WARNING: Input truncated to {} characters".format(max_length))

    # Use compiled regex patterns for better performance
    # Simple character class replacements - safe from backtracking
    invalid_chars = compile(r'[<>:"/\\|?*, ]')
    digit_colon_pattern = compile(
        r'\d+:\d+(?:\.\d+)+')  # More specific pattern
    multiple_underscores = compile(r'_+')
    non_alnum = compile(r'[^a-zA-Z0-9_]')

    # Apply patterns in sequence
    name_file = invalid_chars.sub('_', name_str)
    name_file = digit_colon_pattern.sub('_', name_file)
    name_file = multiple_underscores.sub('_', name_file)
    name_file = non_alnum.sub('', name_file)

    # Check for separators with length limits
    separators = ["➾", "⟾", "->", "→"]
    has_separator = False
    separator_found = None

    for sep in separators:
        if sep in name_str:
            has_separator = True
            separator_found = sep
            break

    if has_separator and separator_found:
        # Split only once to avoid unnecessary processing
        parts = name_str.split(separator_found, 1)
        if len(parts) >= 2:
            # Limit the length of each part
            country_part = parts[0].strip().lower().replace(' ', '_')[:50]
            category_part = parts[1].strip().lower().replace(' ', '_')[:50]
            name_file = country_part + "_" + category_part
        else:
            name_file = name_file[:100]  # Truncate if something went wrong

    # Ensure final filename has reasonable length
    name_file = name_file[:100]

    if has_separator:
        bouquet_name = "subbouquet.vavoo_" + name_file + "." + bouquet_type.lower()
        print("DEBUG: Creating SUBBOUQUET: " + bouquet_name)
    else:
        bouquet_name = "userbouquet.vavoo_" + name_file.lower() + "." + \
            bouquet_type.lower()
        print("DEBUG: Creating USERBOUQUET: " + bouquet_name)

    return name_file, bouquet_name


def _create_flat_bouquet_proxy(
        country_name,
        channels,
        servicetype,
        bouquet_position):
    """Create a flat bouquet (no categories) using proxy channels"""
    try:
        # Prepare file names
        safe_name = country_name.lower().replace(' ', '_')
        bouquet_name = "userbouquet.vavoo_%s.tv" % safe_name
        bouquet_path = join(ENIGMA_PATH, bouquet_name)

        # Create bouquet lines
        lines = ["#NAME %s" % country_name]

        for channel in channels:
            channel_name = channel.get('name', '')
            channel_url = channel.get('url', '')

            if not channel_name or not channel_url:
                continue

            # Encode URL
            encoded_url = channel_url.replace(":", "%3a")
            encoded_name = channel_name.replace(":", "%3a")

            # Add service line
            line = "#SERVICE %s:0:1:0:0:0:0:0:0:0:%s:%s" % (
                servicetype, encoded_url, encoded_name)
            lines.append(line)
            lines.append("#DESCRIPTION %s" % channel_name)

        # Write the file
        with open(bouquet_path, 'w') as f:
            f.write('\n'.join(lines))

        # Add to main bouquet
        _add_to_main_bouquet(bouquet_name, 'tv', bouquet_position)

        return len(channels)

    except Exception as e:
        print("[Flat Bouquet] Error: %s" % str(e))
        return 0


def _create_hierarchical_bouquet_proxy(
        category_name,
        channels,
        servicetype,
        bouquet_position):
    """Create a bouquet for a category and add it to the country's container"""
    try:
        # Extract country and category from name (e.g., "Italy ➾ Sports")
        separators = ["➾", "⟾", "->", "→"]
        country = None
        category = None

        for sep in separators:
            if sep in category_name:
                parts = category_name.split(sep)
                country = parts[0].strip()
                category = parts[1].strip()
                break

        if not country or not category:
            print("[Hierarchical] Invalid category name: %s" % category_name)
            return 0

        # Create the bouquet for the category
        safe_country = country.lower().replace(' ', '_')
        safe_category = category.lower().replace(' ', '_')
        bouquet_name = "subbouquet.vavoo_%s_%s.tv" % (
            safe_country, safe_category)
        bouquet_path = join(ENIGMA_PATH, bouquet_name)

        # Create bouquet lines
        lines = ["#NAME %s - %s" % (country, category)]

        for channel in channels:
            channel_name = channel.get('name', '')
            channel_url = channel.get('url', '')

            if not channel_name or not channel_url:
                continue

            encoded_url = channel_url.replace(":", "%3a")
            encoded_name = channel_name.replace(":", "%3a")

            line = "#SERVICE %s:0:1:0:0:0:0:0:0:0:%s:%s" % (
                servicetype, encoded_url, encoded_name)
            lines.append(line)
            lines.append("#DESCRIPTION %s" % channel_name)

        with open(bouquet_path, 'w') as f:
            f.write('\n'.join(lines))

        # Update country container
        container_name = "userbouquet.vavoo_%s_cowntry.tv" % safe_country
        container_path = join(ENIGMA_PATH, container_name)

        # Read existing container or create new
        if isfile(container_path):
            with open(container_path, 'r') as f:
                container_lines = f.read().splitlines()
        else:
            container_lines = ["#NAME %s - Categories" % country]

        # Add reference to sub-bouquet if not already present
        new_line = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet' % bouquet_name
        if new_line not in container_lines:
            container_lines.append(new_line)
            with open(container_path, 'w') as f:
                f.write('\n'.join(container_lines))

            # Add container to main bouquet if not already present
            _add_to_main_bouquet(container_name, 'tv', bouquet_position)

        return len(channels)

    except Exception as e:
        print("[Hierarchical Bouquet] Error: %s" % str(e))
        return 0


def create_bouquet_file(
        name,
        channels,
        servicetype,
        export_type,
        bouquet_position):
    """Create the Enigma2 bouquet file"""
    try:
        print("[Bouquet] Creating bouquet: %s (%s)" % (name, export_type))

        # Determine if it is a country or category
        separators = ["➾", "⟾", "->", "→"]
        is_category = any(sep in name for sep in separators)

        # Prepare file name
        if export_type == "flat" or not is_category:
            # Flat bouquet for country
            safe_name = name.lower().replace(
                ' ',
                '_').replace(
                '➾',
                '').replace(
                '⟾',
                '').replace(
                '->',
                '').replace(
                    '→',
                '')
            bouquet_filename = "userbouquet.vavoo_%s.tv" % safe_name
        else:
            # Hierarchical bouquet for category
            country_part = ""
            category_part = ""

            # Extract country and category
            for sep in separators:
                if sep in name:
                    parts = name.split(sep)
                    country_part = parts[0].strip()
                    category_part = parts[1].strip()
                    break

            if not country_part or not category_part:
                safe_name = name.lower().replace(
                    ' ',
                    '_').replace(
                    '➾',
                    '_').replace(
                    '⟾',
                    '_').replace(
                    '->',
                    '_').replace(
                    '→',
                    '_')
                bouquet_filename = "userbouquet.vavoo_%s.tv" % safe_name
            else:
                country_safe = country_part.lower().replace(' ', '_')
                category_safe = category_part.lower().replace(' ', '_')
                bouquet_filename = "userbouquet.vavoo_%s_%s.tv" % (
                    country_safe, category_safe)

        # Full bouquet path
        bouquet_path = join(ENIGMA_PATH, bouquet_filename)

        # Bouquet content
        content = ["#NAME %s" % name]

        channel_count = 0
        for channel in channels:
            try:
                if isinstance(channel, dict):
                    channel_name = channel.get('name', 'Unknown')
                    channel_url = channel.get('url', '')

                    # If URL is proxy /resolve?id=, convert to /vavoo?channel=
                    if "/resolve?id=" in channel_url:
                        channel_id = channel_url.split("/resolve?id=")[1]
                        channel_url = "http://127.0.0.1:{}/vavoo?channel={}".format(PORT, channel_id)

                    # If URL is not proxy, use base version
                    if not channel_url.startswith("http://127.0.0.1"):
                        channel_id = channel.get('id', '')
                        if channel_id:
                            channel_url = "http://127.0.0.1:{}/vavoo?channel={}".format(PORT, channel_id)

                    # Clean channel name
                    channel_name = decodeHtml(channel_name)
                    channel_name = rimuovi_parentesi(channel_name)
                    channel_name = sanitizeFilename(channel_name)

                    # Encode for Enigma2
                    encoded_url = channel_url.replace(":", "%3a")
                    encoded_name = channel_name.replace(":", "%3a")

                    # Service line
                    service_line = "#SERVICE %s:0:1:0:0:0:0:0:0:0:%s:%s" % (
                        servicetype, encoded_url, encoded_name)
                    desc_line = "#DESCRIPTION %s" % channel_name

                    content.append(service_line)
                    content.append(desc_line)
                    channel_count += 1

            except Exception as e:
                print("[Bouquet] Error processing channel: %s" % str(e))
                continue

        if channel_count == 0:
            print("[Bouquet] No valid channels for %s" % name)
            return 0

        # Write bouquet file
        try:
            with io.open(bouquet_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            print("[Bouquet] File created: %s (%d channels)" % (bouquet_filename, channel_count))
        except Exception as e:
            print("[Bouquet] Error writing file with encoding: %s" % str(e))
            try:
                with open(bouquet_path, 'wb') as f:
                    f.write(('\n'.join(content)).encode('utf-8', 'ignore'))
                print("[Bouquet] File created (binary fallback): %s (%d channels)" % (bouquet_filename, channel_count))
            except Exception as e2:
                print("[Bouquet] Critical error writing file: %s" % str(e2))

        # Add to main bouquet
        _add_to_main_bouquet(bouquet_filename, 'tv', bouquet_position)

        return channel_count

    except Exception as e:
        print("[Bouquet] Error in create_bouquet_file: %s" % str(e))
        trace_error()
        return 0


def _create_flat_bouquet(name, url, service, bouquet_type, server_url):
    """Create flat bouquet using PROXY ONLY"""
    try:
        print(
            "[bouquet_manager] Creating bouquet for: " +
            name +
            " using proxy")

        # Get channels from proxy
        channels = get_proxy_channels(name)

        if not channels:
            print("[bouquet_manager] No channels received from proxy for: " + name)
            return 0

        # Prepare filenames
        safe_name = name.lower().replace(' ', '_')
        bouquet_name = "userbouquet.vavoo_" + safe_name + "." + bouquet_type
        bouquet_path = join(ENIGMA_PATH, bouquet_name)

        # Build bouquet
        content_lines = ["#NAME " + name]
        ch_count = 0

        # Use proxy URL format
        local_ip = "127.0.0.1"

        for channel in channels:
            if not isinstance(channel, dict):
                continue

            name_channel = channel.get("name", "")
            if not name_channel:
                continue

            name_channel = decodeHtml(name_channel)
            name_channel = rimuovi_parentesi(name_channel)
            name_channel = sanitizeFilename(name_channel)

            channel_id = channel.get("id", "")
            if not channel_id:
                continue

            # Use proxy URL format
            url_channel = "https://" + local_ip + ":" + \
                str(PORT) + "/vavoo?channel=" + channel_id

            tag = "2" if bouquet_type.upper() == "RADIO" else "1"
            url_encoded = url_channel.replace(":", "%3a")

            service_line = "#SERVICE " + \
                str(service) + ":0:" + tag + ":0:0:0:0:0:0:0:" + url_encoded + ":" + name_channel
            desc_line = "#DESCRIPTION " + name_channel

            content_lines.append(service_line)
            content_lines.append(desc_line)
            ch_count += 1

        if ch_count == 0:
            print("[bouquet_manager] No valid channels found for: " + name)
            return 0

        # Save file
        try:
            if PY3:
                with io.open(bouquet_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(content_lines))
            else:
                with open(bouquet_path, 'w') as f:
                    f.write('\n'.join(content_lines).encode('utf-8'))
        except Exception as e:
            print("[bouquet_manager] Error writing with encoding: " + str(e))
            with open(bouquet_path, 'w') as f:
                f.write('\n'.join(content_lines))

        _add_to_main_bouquet(bouquet_name, bouquet_type)

        print("[bouquet_manager] Created bouquet: " +
              bouquet_name + " (" + str(ch_count) + " channels)")
        return ch_count

    except Exception as error:
        print("[bouquet_manager] Error in _create_flat_bouquet: " + str(error))
        trace_error()
        return 0


def _create_hierarchical_bouquet(
        country_name,
        url,
        service,
        app,
        bouquet_type,
        server_url,
        list_position="bottom"):
    """Create hierarchical bouquet structure with only exported categories"""
    try:
        # Get all data to find categories for this country
        content = getUrl(url)
        if PY3:
            content = content.decode(
                "utf-8") if isinstance(content, bytes) else content
        all_data = loads(content)

        # Use robust approach for separators
        separators = ["➾", "⟾", "->", "→"]

        # Find all categories for this country
        all_categories = set()
        for entry in all_data:
            country = unquote(entry["country"]).strip("\r\n")
            # Check if starts with the country and has any separator
            if country.startswith(country_name) and any(
                    sep in country for sep in separators):
                all_categories.add(country)

        if not all_categories:
            print(
                "[bouquet_manager] No categories found for " +
                country_name +
                ", using flat structure")
            return _create_flat_bouquet(
                country_name, url, service, bouquet_type, server_url
            )

        # Create category sub-bouquets (children) and track which ones were
        # created
        exported_categories = []
        total_ch = 0
        for category in sorted(all_categories):
            ch_count = _create_category_bouquet(
                category, url, service, bouquet_type, server_url
            )
            if ch_count > 0:  # Only add successfully exported categories
                exported_categories.append(category)
                total_ch += ch_count

        # Create container bouquet (parent) with only exported categories
        if exported_categories:
            container_ch_count = _create_or_update_container_bouquet(
                country_name, exported_categories, bouquet_type, list_position
            )
        else:
            container_ch_count = 0

        return total_ch + container_ch_count

    except Exception as error:
        print(
            "[bouquet_manager] Error creating hierarchical bouquet: " +
            str(error))
        return _create_flat_bouquet(
            country_name,
            url,
            service,
            bouquet_type,
            server_url
        )


def _create_or_update_container_bouquet(
        country_name, new_categories, bouquet_type, list_position="bottom"):
    """Create or update container bouquet"""
    print("[bouquet_manager] _create_or_update_container_bouquet called")
    print("[bouquet_manager] country_name = " + country_name)
    print("[bouquet_manager] new_categories = " + str(new_categories))

    # Container filename
    container_name = "userbouquet.vavoo_" + country_name.lower().replace(' ', '_') + \
        "_cowntry." + bouquet_type
    container_path = join(ENIGMA_PATH, container_name)

    # Read existing content to preserve already added categories
    existing_categories = set()
    content = []

    if isfile(container_path):
        with open(container_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#NAME'):
                    content = [line]  # Keep existing name
                elif line.startswith('#SERVICE') and 'FROM BOUQUET "' in line:
                    # Extract subbouquet reference from existing line
                    parts = line.split('FROM BOUQUET "')
                    if len(parts) > 1:
                        subbouquet_ref = parts[1].split('"')[0]
                        existing_categories.add(subbouquet_ref)
                        content.append(line)  # Keep existing categories
    else:
        content = ["#NAME " + country_name + " - Categories"]

    # Process each new category
    for category in sorted(new_categories):
        category_part = category
        for sep in ["➾", "⟾", "->", "→"]:
            if sep in category:
                category_part = category.split(sep)[1].strip()
                break

        country_safe = country_name.lower().replace(' ', '_')
        category_safe = category_part.lower().replace(' ', '_')
        subbouquet_ref = "subbouquet.vavoo_" + country_safe + \
            "_" + category_safe + "." + bouquet_type

        if subbouquet_ref not in existing_categories:
            bouquet_line = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + \
                subbouquet_ref + '" ORDER BY bouquet'
            content.append(bouquet_line)
            existing_categories.add(subbouquet_ref)
            print(
                "[bouquet_manager] Added new subbouquet reference: " +
                subbouquet_ref)
        else:
            print(
                "[bouquet_manager] Subbouquet already exists: " +
                subbouquet_ref)

    print("[bouquet_manager] Final content lines: " + str(len(content)))
    print("[bouquet_manager] Total categories in container: " +
          str(len(existing_categories)))

    # Write the container bouquet file
    try:
        with open(container_path, 'w') as f:
            for line in content:
                f.write(line + '\n')
        print("[bouquet_manager] ✓ Container bouquet updated: " +
              container_name +
              " with " +
              str(len(existing_categories)) +
              " categories")

        # Add to main bouquet
        _add_to_main_bouquet(container_name, bouquet_type, list_position)

        return len(existing_categories)

    except Exception as e:
        print(
            "[bouquet_manager] ERROR: Failed to save container bouquet: " +
            str(e))
        return 0


def _create_category_bouquet(
        category_name,
        url,
        service,
        bouquet_type,
        server_url):
    """Create category bouquet using PROXY ONLY"""
    try:
        print("[bouquet_manager] Creating category bouquet: " + category_name)

        separators = ["➾", "⟾", "->", "→"]
        country_part = None
        category_part = None

        for sep in separators:
            if sep in category_name:
                parts = category_name.split(sep)
                if len(parts) >= 2:
                    country_part = parts[0].strip()
                    category_part = parts[1].strip()
                    break

        if country_part is None or category_part is None:
            print("ERROR: Could not parse category: " + category_name)
            return 0

        # Get channels from proxy for the main country
        channels = get_proxy_channels(country_part)

        if not channels:
            print(
                "[bouquet_manager] No channels received from proxy for: " +
                country_part)
            return 0

        # Filter channels for this specific category
        filtered_channels = []
        for channel in channels:
            if not isinstance(channel, dict):
                continue

            channel_country = channel.get("country", "")
            if category_name == channel_country:
                filtered_channels.append(channel)

        if not filtered_channels:
            print(
                "[bouquet_manager] No channels found for category: " +
                category_name)
            return 0

        # Prepare filenames
        country_safe = country_part.lower().replace(' ', '_')
        category_safe = category_part.lower().replace(' ', '_')
        bouquet_name = "subbouquet.vavoo_" + country_safe + \
            "_" + category_safe + "." + bouquet_type
        bouquet_path = join(ENIGMA_PATH, bouquet_name)

        # Build bouquet
        content_lines = ["#NAME " + country_part + " - " + category_part]
        ch_count = 0

        # Use proxy URL format
        local_ip = "127.0.0.1"

        for channel in filtered_channels:
            name_channel = channel.get("name", "")
            if not name_channel:
                continue

            name_channel = decodeHtml(name_channel)
            name_channel = rimuovi_parentesi(name_channel)
            name_channel = sanitizeFilename(name_channel)

            channel_id = channel.get("id", "")
            if not channel_id:
                continue

            # Use proxy URL format
            url_channel = "https://" + local_ip + ":" + \
                str(PORT) + "/vavoo?channel=" + channel_id

            tag = "2" if bouquet_type.upper() == "RADIO" else "1"
            url_encoded = url_channel.replace(":", "%3a")

            service_line = "#SERVICE " + \
                str(service) + ":0:" + tag + ":0:0:0:0:0:0:0:" + url_encoded + ":" + name_channel
            desc_line = "#DESCRIPTION " + name_channel

            content_lines.append(service_line)
            content_lines.append(desc_line)
            ch_count += 1

        # Save file
        try:
            if PY3:
                with io.open(bouquet_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(content_lines))
            else:
                with open(bouquet_path, 'w') as f:
                    f.write('\n'.join(content_lines).encode('utf-8'))
        except Exception as e:
            print("[bouquet_manager] Error writing with encoding: " + str(e))
            with open(bouquet_path, 'w') as f:
                f.write('\n'.join(content_lines))

        print("Created category bouquet: " + bouquet_name +
              " (" + str(ch_count) + " channels)")
        return ch_count

    except Exception as e:
        print("Error in _create_category_bouquet: " + str(e))
        trace_error()
        return 0


def _update_favorite_file(name, url, export_type):
    """Update Favorite.txt - URL is always empty (proxy only)"""
    favorite_path = join(PLUGIN_PATH, 'Favorite.txt')

    print("[Bouquet] Updating Favorite.txt: " +
          name + " (type: " + export_type + ")")

    # Read existing bouquets
    existing_bouquets = {}
    if isfile(favorite_path):
        try:
            with open(favorite_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            bouq_name = parts[0].strip()
                            existing_bouquets[bouq_name] = {
                                'url': parts[1].strip() if len(parts) > 1 and parts[1].strip() else "",
                                'export_type': parts[2].strip(),
                                'timestamp': parts[3].strip() if len(parts) > 3 else str(
                                    time.time())}
        except Exception as e:
            print("[Bouquet] Error reading Favorite.txt: " + str(e))

    # Update/add current bouquet
    existing_bouquets[name] = {
        'url': "",  # ALWAYS empty (proxy only)
        'export_type': export_type,
        'timestamp': str(time.time())
    }

    # Write file
    try:
        with open(favorite_path, 'w') as f:
            for bouq_name, bouq_data in sorted(existing_bouquets.items()):
                line = bouq_name + "|" + \
                    bouq_data['url'] + "|" + bouq_data['export_type'] + "|" + bouq_data['timestamp']
                f.write(line + "\n")

        print("[Bouquet] Favorite.txt updated with " +
              str(len(existing_bouquets)) + " bouquets")

    except Exception as e:
        print("[Bouquet] Error writing Favorite.txt: " + str(e))


def reorganize_all_bouquets_position(list_position="bottom"):
    """Reorganize all Vavoo bouquets to the configured position"""
    try:
        for bouquet_type in ['tv', 'radio']:
            main_bouquet_path = join(ENIGMA_PATH, "bouquets." + bouquet_type)

            if not isfile(main_bouquet_path):
                continue

            with open(main_bouquet_path, 'r') as f:
                lines = f.readlines()

            non_vavoo_lines = []
            vavoo_lines = []

            for line in lines:
                if 'vavoo' in line.lower():
                    vavoo_lines.append(line)
                else:
                    non_vavoo_lines.append(line)

            # Apply the configured position - usa il parametro
            if list_position == "top":
                new_lines = vavoo_lines + non_vavoo_lines
            else:
                new_lines = non_vavoo_lines + vavoo_lines

            with open(main_bouquet_path, 'w') as f:
                f.writelines(new_lines)

        print("Reorganized all Vavoo bouquets to " + list_position)
        return True

    except Exception as e:
        print("Error reorganizing bouquets: " + str(e))
        return False
