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
#  Last Modified: 20251216                              #
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

import time
from json import loads
from os import listdir, remove
from os.path import exists as file_exists, isfile, join
from re import sub
from sys import version_info

try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote

from enigma import eDVBDB, eTimer
from Tools.Directories import SCOPE_PLUGINS, resolveFilename

from .vUtils import getAuthSignature, getUrl, decodeHtml, rimuovi_parentesi, sanitizeFilename

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
            reload_timer_conn = reload_timer.timeout.connect(do_reload)
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
                # If name is specified, check the match
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
        service,
        name,
        url,
        export_type="flat",
        server_url=None,
        list_position="bottom"):
    """
    Convert a bouquet with the option of flat or hierarchical structure
    """
    sig = getAuthSignature()
    if sig is None:
        print("ERROR: Cannot get authentication signature!")
        return 0

    app = "?n=1&b=5&vavoo_auth=%s#User-Agent=VAVOO/2.6" % str(sig)
    sig = getAuthSignature()

    bouquet_type = "radio" if "radio" in name.lower() else "tv"
    separators = ["➾", "⟾", "->", "→"]
    has_separator = any(sep in name for sep in separators)

    print(
        "DEBUG convert_bouquet: name='%s', export_type='%s', has_separator=%s" %
        (name, export_type, has_separator))

    if has_separator:
        print("CREATING SINGLE CATEGORY: %s" % name)
        ch_count = _create_category_bouquet(
            name, url, service, app, bouquet_type, server_url)

        country_name = None
        for sep in separators:
            if sep in name:
                parts = name.split(sep)
                if len(parts) >= 1:
                    country_name = parts[0].strip()
                    break

        if country_name:
            content = getUrl(url)
            if PY3:
                content = content.decode(
                    "utf-8") if isinstance(content, bytes) else content
            all_data = loads(content)

            all_categories = set()
            for entry in all_data:
                country = unquote(entry["country"]).strip("\r\n")
                if country.startswith(country_name) and any(
                        sep in country for sep in separators):
                    all_categories.add(country)

            if all_categories:
                _create_or_update_container_bouquet(
                    country_name, [name], bouquet_type, list_position)

        print("DEBUG: convert_bouquet calling ReloadBouquets after export")
        return ch_count

    else:
        print("CREATING BOUQUET FOR COUNTRY: %s (export_type: %s)" %
              (name, export_type))

        if export_type == "hierarchical":
            result = _create_hierarchical_bouquet(
                name, url, service, app, bouquet_type, server_url, list_position)
        else:
            result = _create_flat_bouquet(
                name, url, service, app, bouquet_type, server_url)

        print("DEBUG: convert_bouquet calling ReloadBouquets after export")
        return result


def _prepare_bouquet_filenames(name, bouquet_type):
    """Prepare sanitized file names for bouquet creation"""
    name_file = sub(r'[<>:"/\\|?*, ]', '_', str(name))
    name_file = sub(r'\d+:\d+:[\d.]+', '_', name_file)
    name_file = sub(r'_+', '_', name_file)
    name_file = sub(r'[^a-zA-Z0-9_]', '', name_file)

    separators = ["➾", "⟾", "->", "→"]
    has_separator = any(sep in name for sep in separators)

    if has_separator:
        for sep in separators:
            if sep in name:
                parts = name.split(sep)
                if len(parts) >= 2:
                    country_part = parts[0].strip().lower().replace(' ', '_')
                    category_part = parts[1].strip().lower().replace(' ', '_')
                    name_file = country_part + "_" + category_part
                    break

        bouquet_name = "subbouquet.vavoo_" + name_file + "." + bouquet_type.lower()
        print("DEBUG: Creating SUBBOUQUET: " + bouquet_name)
    else:
        bouquet_name = "userbouquet.vavoo_" + name_file.lower() + "." + bouquet_type.lower()
        print("DEBUG: Creating USERBOUQUET: " + bouquet_name)

    return name_file, bouquet_name


def _create_flat_bouquet(name, url, service, app, bouquet_type, server_url):
    """Create flat bouquet directly from JSON data"""
    try:
        content = getUrl(url)
        if PY3:
            content = content.decode(
                "utf-8") if isinstance(content, bytes) else content
        all_data = loads(content)

        separators = ["➾", "⟾", "->", "→"]
        has_separator = any(sep in name for sep in separators)

        if has_separator:
            for sep in separators:
                if sep in name:
                    country_part = name.split(sep)[0].strip()
                    category_part = name.split(sep)[1].strip()
                    safe_name = country_part.lower().replace(' ', '_') + "_" + \
                        category_part.lower().replace(' ', '_')
                    bouquet_name = "subbouquet.vavoo_" + safe_name + "." + bouquet_type
                    display_name = country_part + " - " + category_part
                    break
        else:
            safe_name = name.lower().replace(' ', '_')
            bouquet_name = "userbouquet.vavoo_%s.%s" % (
                safe_name, bouquet_type)
            display_name = name

        bouquet_path = join(ENIGMA_PATH, bouquet_name)

        # Save favorite record
        with open(join(PLUGIN_PATH, "Favorite.txt"), "w") as r:
            r.write(str(name) + "###" + str(url))

        print("Creating bouquet from JSON: " + name)

        filtered_data = []
        for entry in all_data:
            entry_country = unquote(entry["country"]).strip("\r\n")

            if has_separator:
                if entry_country == name:
                    filtered_data.append(entry)
            else:
                if entry_country == name or entry_country.startswith(
                        name + " ➾"):
                    filtered_data.append(entry)

        if not filtered_data:
            print("No channels found for: " + name)
            return 0

        filtered_data.sort(
            key=lambda x: unquote(
                x["name"]).strip("\r\n").lower())
        content_lines = [
            "#NAME " + display_name
        ]

        ch_count = 0
        for entry in filtered_data:
            name_channel = unquote(entry["name"]).strip("\r\n")
            name_channel = decodeHtml(name_channel)
            name_channel = rimuovi_parentesi(name_channel)
            name_channel = sanitizeFilename(name_channel)
            ids = str(
                entry["id"]).replace(
                ':',
                '').replace(
                ' ',
                '').replace(
                ',',
                '')

            # server_url = cfg.server.value
            if not server_url.startswith('http'):
                server_url = 'https://' + server_url

            url_channel = server_url + "/live2/play/" + ids + '.ts' + app
            tag = "2" if bouquet_type.upper() == "RADIO" else "1"
            url_encoded = url_channel.replace(":", "%3a")

            # SERVICE and DESCRIPTION lines
            service_line = "#SERVICE " + service + ":0:" + tag + \
                ":0:0:0:0:0:0:0:" + url_encoded + ":" + name_channel
            desc_line = "#DESCRIPTION " + name_channel

            content_lines.append(service_line)
            content_lines.append(desc_line)
            ch_count += 1

        # Write bouquet file
        with open(bouquet_path, 'w') as f:
            f.write('\n'.join(content_lines))

        # Always add to main bouquet
        _add_to_main_bouquet(bouquet_name, bouquet_type)

        print(
            "Created bouquet: " +
            bouquet_name +
            " with " +
            str(ch_count) +
            " channels")
        return ch_count

    except Exception as error:
        print("Error creating bouquet: " + str(error))
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

        # Use the same robust approach for separators
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
                "No categories found for " +
                country_name +
                ", using flat structure")
            return _create_flat_bouquet(
                country_name, url, service, app, bouquet_type, server_url)

        # Create category sub-bouquets (CHILDREN) and track which ones were
        # actually created
        exported_categories = []
        total_ch = 0
        for category in sorted(all_categories):
            ch_count = _create_category_bouquet(
                category, url, service, app, bouquet_type, server_url)
            if ch_count > 0:  # Only add categories that were successfully exported
                exported_categories.append(category)
                total_ch += ch_count

        # Create container bouquet (PARENT) with ONLY exported categories
        if exported_categories:
            container_ch_count = _create_or_update_container_bouquet(
                country_name, exported_categories, bouquet_type, list_position)
        else:
            container_ch_count = 0

        return total_ch + container_ch_count

    except Exception as error:
        print("Error creating hierarchical bouquet:", error)
        return _create_flat_bouquet(
            country_name,
            url,
            service,
            app,
            bouquet_type,
            server_url)


def _create_or_update_container_bouquet(
        country_name, new_categories, bouquet_type, list_position="bottom"):
    """Create or update container bouquet"""
    print("DEBUG: _create_or_update_container_bouquet called")
    print("DEBUG: country_name = " + country_name)
    print("DEBUG: new_categories = " + str(new_categories))

    # Container filename
    container_name = "userbouquet.vavoo_" + country_name.lower().replace(' ', '_') + \
        "_cowntry." + bouquet_type
    container_path = join(ENIGMA_PATH, container_name)

    # Read existing content to preserve already added categories
    existing_categories = set()
    content = []

    # Check if container already exists and read existing categories
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

    # service_type = "2" if bouquet_type.lower() == "radio" else "1"
    # Process each new category
    for category in sorted(new_categories):
        if '➾' in category:
            category_part = category.split('➾')[1].strip()
        elif '⟾' in category:
            category_part = category.split('⟾')[1].strip()
        elif '->' in category:
            category_part = category.split('->')[1].strip()
        else:
            category_part = category

        country_safe = country_name.lower().replace(' ', '_')
        category_safe = category_part.lower().replace(' ', '_')
        subbouquet_ref = "subbouquet.vavoo_" + country_safe + \
            "_" + category_safe + "." + bouquet_type

        # Add only if this subbouquet is not already in the container
        if subbouquet_ref not in existing_categories:
            bouquet_line = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + \
                subbouquet_ref + '" ORDER BY bouquet'
            content.append(bouquet_line)
            existing_categories.add(subbouquet_ref)
            print("DEBUG: Added new subbouquet reference: " + subbouquet_ref)
        else:
            print("DEBUG: Subbouquet already exists: " + subbouquet_ref)

    print("DEBUG: Final content lines: " + str(len(content)))
    print("DEBUG: Total categories in container: " +
          str(len(existing_categories)))

    # Write the container bouquet file
    try:
        with open(container_path, 'w') as f:
            for line in content:
                f.write(line + '\n')
        print("✓ Container bouquet updated: " + container_name + " with " + str(len(existing_categories)) + " categories")

        # Add to main bouquet
        _add_to_main_bouquet(container_name, bouquet_type, list_position)

        return len(existing_categories)

    except Exception as e:
        print("ERROR: Failed to save container bouquet: " + str(e))
        return 0


def _create_category_bouquet(
        category_name,
        url,
        service,
        app,
        bouquet_type,
        server_url):
    """Create a sub-bouquet for a specific category"""
    try:
        content = getUrl(url)
        if PY3:
            content = content.decode(
                "utf-8") if isinstance(content, bytes) else content
        all_data = loads(content)

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
            print("ERROR: Could not parse category name: " + category_name)
            return 0

        print("Creating category bouquet: " + category_name)

        filtered_data = []
        for entry in all_data:
            entry_country = unquote(entry["country"]).strip("\r\n")
            if entry_country == category_name:
                filtered_data.append(entry)
                print("   Found: " + unquote(entry["name"]).strip())

        print("   Total channels found: " + str(len(filtered_data)))

        if not filtered_data:
            print("No channels found for: " + category_name)
            return 0

        filtered_data.sort(
            key=lambda x: unquote(
                x["name"]).strip("\r\n").lower())

        # Prepare filename
        name_file, subbouquet_name = _prepare_bouquet_filenames(
            category_name, bouquet_type)
        subbouquet_path = join(ENIGMA_PATH, subbouquet_name)

        print("DEBUG: Category bouquet path: " + subbouquet_path)

        display_name = country_part + " - " + category_part
        content_lines = [
            "#NAME " + display_name
        ]

        ch_count = 0
        for entry in filtered_data:
            name_channel = unquote(entry["name"]).strip("\r\n")
            name_channel = decodeHtml(name_channel)
            name_channel = rimuovi_parentesi(name_channel)
            name_channel = sanitizeFilename(name_channel)

            ids = str(
                entry["id"]).replace(
                ':',
                '').replace(
                ' ',
                '').replace(
                ',',
                '')

            # server_url = cfg.server.value
            if not server_url.startswith('http'):
                server_url = 'https://' + server_url

            url_channel = server_url + "/live2/play/" + ids + \
                '.ts' + str(app)

            tag = "2" if bouquet_type.upper() == "RADIO" else "1"
            url_encoded = url_channel.replace(":", "%3a")

            service_line = "#SERVICE " + service + ":0:" + tag + \
                ":0:0:0:0:0:0:0:" + url_encoded + ":" + name_channel
            desc_line = "#DESCRIPTION " + name_channel
            content_lines.append(service_line)
            content_lines.append(desc_line)
            ch_count += 1

        # Write file
        try:
            with open(subbouquet_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content_lines))
            print("✓ Subbouquet saved: " + subbouquet_name)
        except Exception as e:
            print("Error saving subbouquet: " + str(e))
            with open(subbouquet_path, 'w') as f:
                f.write('\n'.join(content_lines))

        # Verify
        if isfile(subbouquet_path):
            with open(subbouquet_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                service_lines = [line for line in lines if line.startswith(
                    '#SERVICE') and '0:0:0' in line]
                print("Subbouquet created successfully with " +
                      str(len(service_lines)) + " service lines")
                return ch_count
        else:
            print("ERROR: Subbouquet file was not created: " + subbouquet_path)
            return 0

    except Exception as e:
        print("Error creating category bouquet: " + str(e))
        return 0


def _update_favorite_file(name, url, export_type):
    """Update Favorite.txt with all exported bouquets and their settings"""
    favorite_path = join(PLUGIN_PATH, 'Favorite.txt')

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
                            bouq_name = parts[0]
                            existing_bouquets[bouq_name] = {
                                'url': parts[1],
                                'export_type': parts[2],
                                'timestamp': parts[3] if len(parts) > 3 else str(
                                    time.time())}
        except Exception as e:
            print("Error reading Favorite.txt: " + str(e))

    # Add or update the current bouquet
    existing_bouquets[name] = {
        'url': url,
        'export_type': export_type,
        'timestamp': str(time.time())
    }

    # Write all bouquets in the format: name|url|export_type|timestamp
    with open(favorite_path, 'w') as f:
        for bouq_name, bouq_data in existing_bouquets.items():
            line = "{}|{}|{}|{}".format(
                bouq_name,
                bouq_data['url'],
                bouq_data['export_type'],
                bouq_data['timestamp']
            )
            f.write(line + "\n")

    print("DEBUG: Updated Favorite.txt with " +
          str(len(existing_bouquets)) + " bouquets")


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


# log
def trace_error():
    """error tracing and logging"""
    import traceback
    from sys import stdout, stderr
    try:
        traceback.print_exc(file=stdout)
        with open("/tmp/vavoo.log", "a", encoding='utf-8') as log_file:
            traceback.print_exc(file=log_file)
    except Exception as e:
        print("Failed to log the error:", e, file=stderr)
