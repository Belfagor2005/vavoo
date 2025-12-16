#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
#########################################################
#                                                       #
#  Vavoo Stream Live Plugin                             #
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: CC BY-NC-SA 4.0                             #
#  https://creativecommons.org/licenses/by-nc-sa/4.0    #
#  Last Modified: 20251118                              #
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

# -----------------------------
# Standard library
# -----------------------------
import base64
import json
import ssl
import types
from os import listdir, makedirs, remove, system, unlink
from os.path import exists, getmtime, getsize, isfile, join, splitext
from random import choice
from re import compile, search, sub
from shutil import copy2
from sys import maxsize, version_info
from time import time
from unicodedata import normalize

import six
from six import iteritems, unichr
from six.moves import html_entities, html_parser

import requests
from Tools.Directories import SCOPE_PLUGINS, resolveFilename


try:
    unicode
except NameError:
    unicode = str

try:
    from Components.AVSwitch import AVSwitch
except ImportError:
    from Components.AVSwitch import eAVControl as AVSwitch


PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/vavoo")
PYTHON_VER = version_info.major

if PYTHON_VER == 3:
    from urllib.request import urlopen, Request
    ssl_context = ssl.create_default_context()
    # Disabilita SSLv2, SSLv3, TLS1.0 e TLS1.1 esplicitamente
    ssl_context.options |= ssl.OP_NO_SSLv2
    ssl_context.options |= ssl.OP_NO_SSLv3
    ssl_context.options |= ssl.OP_NO_TLSv1
    ssl_context.options |= ssl.OP_NO_TLSv1_1
    unichr_func = unichr
else:
    from urllib2 import urlopen, Request
    ssl_context = None
    unichr_func = chr


def get_screen_width():
    """Get current screen width"""
    try:
        from enigma import getDesktop
        desktop = getDesktop(0)
        width = desktop.size().width()
        print("[vUtils] Screen width detected: %d" % width)
        return width
    except Exception as e:
        print("[vUtils] Error getting screen width: %s" % str(e))
        return 1920  # Default FHD


class AspectManager:
    """Manages aspect ratio settings for the plugin"""

    def __init__(self):
        try:
            self.init_aspect = self.get_current_aspect()
            print("[INFO] Initial aspect ratio:", self.init_aspect)
        except Exception as e:
            print("[ERROR] Failed to initialize aspect manager:", str(e))
            self.init_aspect = 0  # Fallback

    def get_current_aspect(self):
        """Get current aspect ratio setting"""
        try:
            aspect = AVSwitch().getAspectRatioSetting()
            # Assicurati che sia un intero valido
            return int(aspect) if aspect is not None else 0
        except (ValueError, TypeError, Exception) as e:
            print("[ERROR] Failed to get aspect ratio:", str(e))
            return 0  # Default 4:3

    def restore_aspect(self):
        """Restore original aspect ratio"""
        try:
            if hasattr(self, 'init_aspect') and self.init_aspect is not None:
                print("[INFO] Restoring aspect ratio to:", self.init_aspect)
                AVSwitch().setAspectRatio(self.init_aspect)
            else:
                print("[WARNING] No initial aspect ratio to restore")
        except Exception as e:
            print("[ERROR] Failed to restore aspect ratio:", str(e))


aspect_manager = AspectManager()


class_types = (type,) if PYTHON_VER == 3 else (type, types.ClassType)
text_type = six.text_type  # unicode in Py2, str in Py3
binary_type = six.binary_type  # str in Py2, bytes in Py3
MAXSIZE = maxsize

_UNICODE_MAP = {
    k: unichr(v) for k,
    v in iteritems(
        html_entities.name2codepoint)}
_ESCAPE_RE = compile(r"[&<>\"']")
_UNESCAPE_RE = compile(r"&\s*(#?)(\w+?)\s*;")
_ESCAPE_DICT = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&apos;",
}


def ensure_str(s, encoding="utf-8", errors="strict"):
    if isinstance(s, str):
        return s
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    raise TypeError("not expecting type '%s'" % type(s))


def html_escape(value):
    """Escape HTML special characters"""
    return _ESCAPE_RE.sub(lambda m: _ESCAPE_DICT[m.group(0)], value.strip())


def html_unescape(value):
    """Unescape HTML entities"""
    return _UNESCAPE_RE.sub(_convert_entity, ensure_str(value).strip())


def _convert_entity(m):
    """Helper for HTML entity conversion, compatible with Python 2 and 3"""
    if m.group(1) == "#":
        try:
            return unichr(int(m.group(2)[1:], 16)) if m.group(
                2)[:1].lower() == "x" else unichr(int(m.group(2)))
        except ValueError:
            return "&#%s;" % m.group(2)
    return _UNICODE_MAP.get(m.group(2), "&%s;" % m.group(2))


def b64decoder(data):
    """Robust base64 decoding with padding correction"""
    data = data.strip()
    pad = len(data) % 4
    if pad == 1:  # Invalid base64 length
        return ""
    if pad:
        data += "=" * (4 - pad)

    try:
        decoded = base64.b64decode(data)
        return decoded.decode('utf-8') if PYTHON_VER == 3 else decoded
    except Exception as e:
        print("Base64 decoding error: %s" % e)
        return ""


def getUrl(url):
    """Fetch URL content with fallback SSL handling"""
    headers = {'User-Agent': RequestAgent()}

    try:
        if PYTHON_VER == 3:
            response = urlopen(
                Request(
                    url,
                    headers=headers),
                timeout=20,
                context=ssl_context)
            return response.read().decode('utf-8', errors='ignore')
        else:
            response = urlopen(Request(url, headers=headers), timeout=20)
            return response.read()
    except Exception as e:
        print("URL fetch error: %s" % e)
        return ""


def get_external_ip():
    """Get external IP using multiple fallback services"""
    import requests
    from subprocess import Popen, PIPE

    services = [
        lambda: Popen(
            [
                'curl',
                '-s',
                'ifconfig.me'],
            stdout=PIPE).communicate()[0].decode('utf-8').strip(),
        lambda: requests.get(
            'https://v4.ident.me',
                timeout=5).text.strip(),
        lambda: requests.get(
                    'https://api.ipify.org',
                    timeout=5).text.strip(),
        lambda: requests.get(
                        'https://api.myip.com',
                        timeout=5).json().get(
                            "ip",
                            "").strip(),
        lambda: requests.get(
                                'https://checkip.amazonaws.com',
                                timeout=5).text.strip(),
    ]

    for service in services:
        try:
            ip = service()
            if ip:
                return ip
        except Exception:
            continue
    return None


def set_cache(key, data, timeout):
    file_path = join(PLUGIN_PATH, key + '.json')
    try:
        if not isinstance(data, dict):
            data = {"value": data}
        if PYTHON_VER < 3:
            import io
            converted_data = convert_to_unicode(data)
            with io.open(file_path, 'w', encoding='utf-8') as cache_file:
                json.dump(
                    converted_data,
                    cache_file,
                    indent=4,
                    ensure_ascii=False)
        else:
            with open(file_path, 'w', encoding='utf-8') as cache_file:
                json.dump(data, cache_file, indent=4, ensure_ascii=False)
    except Exception as e:
        print("Error saving cache:", e)


def convert_to_unicode(data):
    if isinstance(data, dict):
        return {convert_to_unicode(key): convert_to_unicode(value)
                for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_to_unicode(element) for element in data]
    elif PYTHON_VER < 3 and isinstance(data, str):
        # Decode strings to Unicode for Python 2
        return data.decode('utf-8')
    elif PYTHON_VER < 3 and isinstance(data, unicode):
        return data
    else:
        return data


def get_cache(key):
    file_path = join(PLUGIN_PATH, key + '.json')
    if not (exists(file_path) and getsize(file_path) > 0):
        return None
    try:
        data = _read_json_file(file_path)
        if isinstance(data, str):
            data = {"value": data}
            _write_json_file(file_path, data)

        if not isinstance(data, dict):
            print(
                "Unexpected data format in {}: Expected a dict, got {}".format(
                    file_path, type(data)))
            remove(file_path)
            return None

        if _is_cache_valid(data):
            return data.get('value')

    except ValueError as e:
        print("Error decoding JSON from", file_path, ":", e)
    except Exception as e:
        print("Unexpected error reading cache file {}:".format(file_path), e)
        remove(file_path)

    return None


def _read_json_file(file_path):
    if PYTHON_VER < 3:
        import io
        with io.open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)


def _write_json_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _is_cache_valid(data):
    return (
        data.get('sigValidUntil', 0) > int(time())
        and data.get('ip', "") == get_external_ip()
    )


def getAuthSignature():
    print("DEBUG: Getting auth signature...")

    signfile = get_cache('signfile')
    if signfile:
        print("DEBUG: Found cached signature:",
              signfile[:50] + "..." if signfile else "None")
        return signfile

    print("DEBUG: No cached signature, fetching new one...")

    veclist = get_cache("veclist")
    if not veclist:
        print("DEBUG: No cached veclist, fetching from GitHub...")
        try:
            if ssl_context:
                req = Request(
                    "https://raw.githubusercontent.com/Belfagor2005/vavoo/refs/heads/main/data.json")
                with urlopen(req, context=ssl_context) as r:
                    veclist = json.load(r)
            else:
                response = requests.get(
                    "https://raw.githubusercontent.com/Belfagor2005/vavoo/refs/heads/main/data.json",
                    verify=False)
                veclist = response.json()
            print("DEBUG: Fetched veclist with", len(
                veclist) if veclist else 0, "items")
        except Exception as e:
            print("[vUtils] Failed to fetch veclist:", e)
            return None

        set_cache("veclist", veclist, timeout=3600)

    sig = None
    i = 0
    print("DEBUG: Trying to get signature from Vavoo API...")
    while not sig and i < 50:
        i += 1
        vec = {"vec": choice(veclist)}
        try:
            req = requests.post(
                'https://www.vavoo.tv/api/box/ping2',
                data=vec,
                timeout=10).json()
            sig = req.get('signed') or req.get(
                'data', {}).get('signed') or req.get(
                'response', {}).get('signed')
            if sig:
                print("DEBUG: Successfully got signature on attempt", i)
                break
        except Exception as e:
            print("DEBUG: Attempt", i, "failed:", e)
            continue

    if sig:
        print("DEBUG: Saving signature to cache...")
        set_cache('signfile', convert_to_unicode(sig), timeout=3600)
    else:
        print("DEBUG: Failed to get signature after", i, "attempts")

    return sig


def fetch_vec_list():
    """Fetch vector list from GitHub"""
    try:
        vec_list = requests.get(
            "https://raw.githubusercontent.com/Belfagor2005/vavoo/main/data.json",
            timeout=10).json()
        set_cache("vec_list", vec_list, 3600)
        return vec_list
    except Exception as e:
        print("Vector list fetch error: " + str(e))
        return None


def rimuovi_parentesi(text):
    """Remove parentheses and their content from text"""
    return sub(r'\s*\([^()]*\)\s*', ' ', text).strip()


def purge(directory, pattern):
    """Delete files matching pattern in directory"""
    for f in listdir(directory):
        file_path = join(directory, f)
        if isfile(file_path) and search(pattern, f):
            remove(file_path)


def MemClean():
    """Clear system memory cache"""
    try:
        system('sync')
        for i in range(1, 4):
            system("echo " + str(i) + " > /proc/sys/vm/drop_caches")
    except Exception:
        pass


def ReloadBouquets():
    """Reload Enigma2 bouquets and service lists"""
    from enigma import eDVBDB, eTimer
    try:
        def do_reload():
            try:
                db = eDVBDB.getInstance()
                if db:
                    db.reloadServicelist()
                    db.reloadBouquets()
            except Exception as e:
                print("Error during service reload: " + str(e))

        reload_timer = eTimer()
        try:
            reload_timer.callback.append(do_reload)
        except BaseException:
            reload_timer_conn = reload_timer.timeout.connect(
                do_reload)
        reload_timer.start(2000, True)
    except Exception as e:
        print("Error setting up service reload: " + str(e))


def sanitizeFilename(filename):
    """Sanitize filename for safe filesystem use"""
    # Remove unsafe characters
    filename = sub(r'[\\/:*?"<>|\0]', '', filename)
    filename = ''.join(c for c in filename if ord(c) > 31)

    # Unicode support for Python 2 and 3
    try:
        # Python 2
        if isinstance(filename, str):
            filename = filename.decode('utf-8', 'ignore')
        filename = normalize('NFKD', filename).encode('ascii', 'ignore')
    except BaseException:
        # Python 3
        filename = normalize(
            'NFKD',
            filename).encode(
            'ascii',
            'ignore').decode()

    filename = filename.rstrip('. ').strip()

    # Handle reserved names
    reserved = (
        ["CON", "PRN", "AUX", "NUL"]
        + ["COM" + str(i) for i in range(1, 10)]
        + ["LPT" + str(i) for i in range(1, 10)]
    )

    if filename.upper() in reserved or not filename:
        if filename:
            filename = "__" + filename
        else:
            filename = "__"

    # Truncate if necessary
    if len(filename) > 255:
        base, ext = splitext(filename)
        ext = ext[:254]
        filename = base[:255 - len(ext)] + ext

    return filename or "__"


def decodeHtml(text):
    if PYTHON_VER == 3:
        import html
        text = html.unescape(text)
    else:
        h = html_parser.HTMLParser()
        text = h.unescape(text.decode('utf8')).encode('utf8')

    replacements = {
        '&amp;': '&', '&apos;': "'", '&lt;': '<', '&gt;': '>', '&ndash;': '-',
        '&quot;': '"', '&ntilde;': '~', '&rsquo;': "'", '&nbsp;': ' ',
        '&equals;': '=', '&quest;': '?', '&comma;': ',', '&period;': '.',
        '&colon;': ':', '&lpar;': '(', '&rpar;': ')', '&excl;': '!',
        '&dollar;': '$', '&num;': '#', '&ast;': '*', '&lowbar;': '_',
        '&lsqb;': '[', '&rsqb;': ']', '&half;': '1/2', '&DiacriticalTilde;': '~',
        '&OpenCurlyDoubleQuote;': '"', '&CloseCurlyDoubleQuote;': '"'
    }
    for entity, char in replacements.items():
        text = text.replace(entity, char)

    return text.strip()


def remove_line(filename, pattern):
    """Remove lines containing pattern from file"""
    if not isfile(filename):
        return
    with open(filename, 'r') as f:
        lines = [line for line in f if pattern not in line]
    with open(filename, 'w') as f:
        f.writelines(lines)


# this def returns the current playing service name and stream_url from
# give sref
def getserviceinfo(service_ref):
    """Get service name and URL from service reference"""
    try:
        from ServiceReference import ServiceReference
        ref = ServiceReference(service_ref)
        return ref.getServiceName(), ref.getPath()
    except Exception:
        return None, None


std_headers = {
    'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-us,en;q=0.5'}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.88 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

]


def RequestAgent():
    """Get random user agent from list"""
    return choice(USER_AGENTS)


# ============================================================================
# FLAG DOWNLOAD FUNCTIONS
# ============================================================================
def initialize_cache_with_local_flags():
    """Copy all local flags from skin/cowntry/ to cache directory"""
    local_dir = join(PLUGIN_PATH, 'skin/cowntry')
    cache_dir = "/tmp/vavoo_flags"

    if not exists(local_dir):
        print("[vUtils] Local flags directory not found: %s" % local_dir)
        return 0

    # Python 2 compatible directory creation
    if not exists(cache_dir):
        try:
            makedirs(cache_dir)
        except Exception:
            pass

    copied = 0
    for filename in listdir(local_dir):
        if filename.lower().endswith('.png'):
            src = join(local_dir, filename)
            dst = join(cache_dir, filename.lower())

            try:
                with open(src, 'rb') as f:
                    # Check PNG header
                    header = f.read(8)
                    if header == b'\x89PNG\r\n\x1a\n':
                        copy2(src, dst)
                        copied += 1
                        print("[vUtils] Copied local flag: %s" % filename)
                    else:
                        print("[vUtils] Skipping invalid PNG: %s" % filename)
            except Exception as e:
                print("[vUtils] Error copying %s: %s" % (filename, e))

    print("[vUtils] Initialized cache with %d local flags" % copied)
    return copied


def download_flag_online(country_name, cache_dir="/tmp/vavoo_flags", screen_width=None):
    """
    Download country flag from online service (TV Garden style)
    Returns: (success, flag_path_or_error_message)
    """
    try:
        # 1. Determine screen width if not provided
        if screen_width is None:
            screen_width = get_screen_width()  # deve restituire int

        print("[vUtils] Processing %s with screen_width=%d" % (country_name, screen_width))

        # 2. Get country code
        country_code = get_country_code(country_name)
        if not country_code:
            return False, "No country code found for: %s" % country_name

        country_code_lower = country_code.lower()
        special_flags = ['bk', 'internat']

        if country_code_lower in special_flags:
            local_path = join(PLUGIN_PATH, 'skin/cowntry', '%s.png' % country_code_lower)
            if exists(local_path):
                print("[vUtils] Using special flag: %s -> %s" % (country_name, local_path))
                return True, local_path

        # 3. Create cache directory (Python 2 safe)
        if not exists(cache_dir):
            try:
                makedirs(cache_dir)
            except Exception:
                pass

        # 4. Cache file path
        cache_file = join(cache_dir, "%s.png" % country_code_lower)

        # 5. Check fresh cache (<7 days)
        if exists(cache_file):
            try:
                file_age = time() - getmtime(cache_file)
                if file_age < 604800:
                    print("[vUtils] Cache HIT: %s" % country_name)
                    return True, cache_file
            except Exception:
                pass

        # 6. Set fixed flag dimensions
        if screen_width >= 2560:      # WQHD
            width, height = 80, 60
        elif screen_width >= 1920:    # FHD
            width, height = 60, 45
        else:                         # HD
            width, height = 40, 30

        # 7. Build URL
        url = "https://flagcdn.com/%dx%d/%s.png" % (width, height, country_code_lower)
        print("[vUtils] Downloading %s (%dx%d) from: %s" % (country_name, width, height, url))

        # 8. Download
        req = Request(url, headers={'User-Agent': 'Vavoo-Stream/1.0'})
        try:
            if PYTHON_VER == 3:
                response = urlopen(req, timeout=5, context=ssl_context)
            else:
                response = urlopen(req, timeout=5)
        except Exception as e:
            print("[vUtils] Network error for %s: %s" % (country_name, e))
            return False, "Network error: %s" % e

        # 9. Read data
        if response.getcode() != 200:
            return False, "Download failed (HTTP %d)" % response.getcode()
        flag_data = response.read()
        try:
            response.close()
        except Exception:
            pass

        # 10. Validate small file
        if len(flag_data) < 100:
            print("[vUtils] Warning: Flag file too small (%d bytes)" % len(flag_data))

        # 11. Save to cache
        try:
            f = open(cache_file, 'wb')
            f.write(flag_data)
            f.close()

            # Verify PNG header
            f = open(cache_file, 'rb')
            header = f.read(8)
            f.close()
            if header != b'\x89PNG\r\n\x1a\n':
                print("[vUtils] ERROR: Not a valid PNG file!")
                try:
                    unlink(cache_file)
                except Exception:
                    pass
                return False, "Invalid PNG file downloaded"

            print("[vUtils] Flag %dx%d saved: %s (%d bytes)" % (width, height, cache_file, len(flag_data)))
            return True, cache_file

        except Exception as e:
            print("[vUtils] Error saving to cache: %s" % e)
            return False, "Save error: %s" % e

    except Exception as e:
        print("[vUtils] Flag download error: %s" % e)
        return False, "Flag download error: %s" % e


def download_flag_with_size(country_name, size="40x30", cache_dir="/tmp/vavoo_flags"):
    """
    Download flag with specific size (40x30, 80x60, etc.)
    Returns: success (True/False)
    """
    try:
        country_code = get_country_code(country_name)
        if not country_code:
            print("[vUtils] No code for: %s" % country_name)
            return False

        # Parse dimensioni
        if "x" in size:
            try:
                width, height = size.split("x")
                width = int(width)
                height = int(height)
            except:
                width, height = 40, 30
        else:
            width, height = 40, 30

        # URL with fixed size w/h
        url = "https://flagcdn.com/w%d/h%d/%s.png" % (width, height, country_code.lower())

        print("[vUtils] Downloading %s flag %dx%d from: %s" % (country_name, width, height, url))

        # Create cache folder
        makedirs(cache_dir, exist_ok=True)

        # Cache path
        cache_file = join(cache_dir, "%s.png" % country_code.lower())

        req = Request(url, headers={'User-Agent': 'Vavoo-Stream/1.0'})

        try:
            if PYTHON_VER == 3:
                response = urlopen(req, timeout=5, context=ssl_context)
            else:
                response = urlopen(req, timeout=5)
        except Exception as e:
            print("[vUtils] Network error: %s" % str(e))
            return False

        if response.getcode() == 200:
            flag_data = response.read()
            response.close()

            # Save to cache
            with open(cache_file, 'wb') as f:
                f.write(flag_data)

            print("[vUtils] ✓ Flag %dx%d saved: %s (%d bytes)" %
                  (width, height, cache_file, len(flag_data)))
            return True
        else:
            print("[vUtils] ✗ Download failed for %s (HTTP %d)" % (country_name, response.getcode()))
            return False

    except Exception as e:
        print("[vUtils] Error downloading %s: %s" % (country_name, str(e)))
        return False


def get_country_code(country_name):
    """
    Extract country code from country name.
    Handles formats like 'France', 'France ➾ Sports', etc.
    Returns ISO 2-letter country code or empty string if not found.
    """
    if not country_name:
        return ""

    # Remove category separators and extra text
    separators = ["➾", "⟾", "->", "→", "»", "›"]
    for sep in separators:
        if sep in country_name:
            country_name = country_name.split(sep)[0].strip()
            break

    country_name = country_name.strip()
    special_mapping = {
        'Internat': 'internat',
        'International': 'internat',
        'Internaz': 'internat',
        'Global': 'internat',
        'World': 'internat',
        'Balkans': 'bk',
        'Arabia': 'sa',
        'Scandinavia': 'scandinavia',
        'Baltic': 'baltic',
        'United Kingdom': 'gb',
        'UK': 'gb',
        'Great Britain': 'gb',
        'United States': 'us',
        'USA': 'us',
        'America': 'us',
        'Czech Republic': 'cz',
        'Czech': 'cz',
        'Slovak Republic': 'sk',
        'Slovakia': 'sk',
        'South Korea': 'kr',
        'North Korea': 'kp',
        'Russia': 'ru',
        'Russian Federation': 'ru',
        'UAE': 'ae',
        'United Arab Emirates': 'ae',
        'Vatican City': 'va',
        'Holy See': 'va',
    }

    if country_name in special_mapping:
        return special_mapping[country_name]

    # Full country map
    country_map = {
        # Europe
        'Albania': 'al', 'Andorra': 'ad', 'Austria': 'at', 'Belarus': 'by',
        'Belgium': 'be', 'Bosnia': 'ba', 'Bulgaria': 'bg', 'Croatia': 'hr',
        'Cyprus': 'cy', 'Czechia': 'cz', 'Denmark': 'dk', 'Estonia': 'ee',
        'Finland': 'fi', 'France': 'fr', 'Germany': 'de', 'Greece': 'gr',
        'Hungary': 'hu', 'Iceland': 'is', 'Ireland': 'ie', 'Italy': 'it',
        'Latvia': 'lv', 'Liechtenstein': 'li', 'Lithuania': 'lt',
        'Luxembourg': 'lu', 'Malta': 'mt', 'Moldova': 'md', 'Monaco': 'mc',
        'Montenegro': 'me', 'Netherlands': 'nl', 'North Macedonia': 'mk',
        'Norway': 'no', 'Poland': 'pl', 'Portugal': 'pt', 'Romania': 'ro',
        'Russia': 'ru', 'San Marino': 'sm', 'Serbia': 'rs', 'Slovakia': 'sk',
        'Slovenia': 'si', 'Spain': 'es', 'Sweden': 'se', 'Switzerland': 'ch',
        'Ukraine': 'ua', 'United Kingdom': 'gb', 'Vatican': 'va',
        # Americas
        'Argentina': 'ar', 'Bolivia': 'bo', 'Brazil': 'br', 'Canada': 'ca',
        'Chile': 'cl', 'Colombia': 'co', 'Costa Rica': 'cr', 'Cuba': 'cu',
        'Dominican Republic': 'do', 'Ecuador': 'ec', 'El Salvador': 'sv',
        'Guatemala': 'gt', 'Haiti': 'ht', 'Honduras': 'hn', 'Jamaica': 'jm',
        'Mexico': 'mx', 'Nicaragua': 'ni', 'Panama': 'pa', 'Paraguay': 'py',
        'Peru': 'pe', 'Puerto Rico': 'pr', 'United States': 'us',
        'Uruguay': 'uy', 'Venezuela': 've',
        # Asia
        'Afghanistan': 'af', 'Armenia': 'am', 'Azerbaijan': 'az', 'Bahrain': 'bh',
        'Bangladesh': 'bd', 'Bhutan': 'bt', 'Brunei': 'bn', 'Cambodia': 'kh',
        'China': 'cn', 'Georgia': 'ge', 'India': 'in', 'Indonesia': 'id',
        'Iran': 'ir', 'Iraq': 'iq', 'Israel': 'il', 'Japan': 'jp',
        'Jordan': 'jo', 'Kazakhstan': 'kz', 'Kuwait': 'kw', 'Kyrgyzstan': 'kg',
        'Laos': 'la', 'Lebanon': 'lb', 'Malaysia': 'my', 'Maldives': 'mv',
        'Mongolia': 'mn', 'Myanmar': 'mm', 'Nepal': 'np', 'Oman': 'om',
        'Pakistan': 'pk', 'Palestine': 'ps', 'Philippines': 'ph', 'Qatar': 'qa',
        'Saudi Arabia': 'sa', 'Singapore': 'sg', 'South Korea': 'kr',
        'Sri Lanka': 'lk', 'Syria': 'sy', 'Taiwan': 'tw', 'Tajikistan': 'tj',
        'Thailand': 'th', 'Turkey': 'tr', 'Turkmenistan': 'tm',
        'United Arab Emirates': 'ae', 'Uzbekistan': 'uz', 'Vietnam': 'vn',
        'Yemen': 'ye',
        # Africa
        'Algeria': 'dz', 'Angola': 'ao', 'Benin': 'bj', 'Botswana': 'bw',
        'Burkina Faso': 'bf', 'Burundi': 'bi', 'Cameroon': 'cm',
        'Cape Verde': 'cv', 'Central African Republic': 'cf', 'Chad': 'td',
        'Comoros': 'km', 'Congo': 'cg', 'Djibouti': 'dj', 'Egypt': 'eg',
        'Equatorial Guinea': 'gq', 'Eritrea': 'er', 'Eswatini': 'sz',
        'Ethiopia': 'et', 'Gabon': 'ga', 'Gambia': 'gm', 'Ghana': 'gh',
        'Guinea': 'gn', 'Guinea-Bissau': 'gw', 'Ivory Coast': 'ci',
        'Kenya': 'ke', 'Lesotho': 'ls', 'Liberia': 'lr', 'Libya': 'ly',
        'Madagascar': 'mg', 'Malawi': 'mw', 'Mali': 'ml', 'Mauritania': 'mr',
        'Mauritius': 'mu', 'Morocco': 'ma', 'Mozambique': 'mz', 'Namibia': 'na',
        'Niger': 'ne', 'Nigeria': 'ng', 'Rwanda': 'rw', 'Senegal': 'sn',
        'Seychelles': 'sc', 'Sierra Leone': 'sl', 'Somalia': 'so',
        'South Africa': 'za', 'South Sudan': 'ss', 'Sudan': 'sd',
        'Tanzania': 'tz', 'Togo': 'tg', 'Tunisia': 'tn', 'Uganda': 'ug',
        'Zambia': 'zm', 'Zimbabwe': 'zw',
        # Oceania
        'Australia': 'au', 'Fiji': 'fj', 'Kiribati': 'ki', 'Marshall Islands': 'mh',
        'Micronesia': 'fm', 'Nauru': 'nr', 'New Zealand': 'nz', 'Palau': 'pw',
        'Papua New Guinea': 'pg', 'Samoa': 'ws', 'Solomon Islands': 'sb',
        'Tonga': 'to', 'Tuvalu': 'tv', 'Vanuatu': 'vu'
    }

    # Exact match
    if country_name in country_map:
        return country_map[country_name]

    # Case-insensitive
    name_lower = country_name.lower()
    for key, code in country_map.items():
        if key.lower() == name_lower:
            return code

    # Partial match
    for key, code in country_map.items():
        if key.lower() in name_lower or name_lower in key.lower():
            return code

    return ""


def cleanup_flag_cache(max_age_days=7):
    """
    Remove old cached flag files from cache directory.
    Only files older than max_age_days are deleted.
    """
    cache_dir = "/tmp/vavoo_flags"

    if not exists(cache_dir):
        return

    now = time()
    max_age = max_age_days * 86400  # seconds

    try:
        for filename in listdir(cache_dir):
            filepath = join(cache_dir, filename)
            if isfile(filepath):
                try:
                    file_age = now - getmtime(filepath)
                    if file_age > max_age:
                        unlink(filepath)
                        print("[vUtils] Removed old flag: %s" % filename)
                except Exception as e:
                    print("[vUtils] Error removing %s: %s" % (filename, str(e)))
    except Exception as e:
        print("[vUtils] Error cleaning flag cache: %s" % str(e))


def cleanup_old_temp_files(max_age_hours=1):
    """
    Remove old temporary files in /tmp matching specific patterns.
    Files older than max_age_hours are deleted.
    """
    import glob

    try:
        now = time()
        max_age = max_age_hours * 3600  # seconds

        patterns = [
            "/tmp/*vavoo*",
            "/tmp/*flag*",
            "/tmp/tmp*.png"
        ]

        cleaned = 0
        for pattern in patterns:
            for filepath in glob.glob(pattern):
                try:
                    if isfile(filepath):
                        file_age = now - getmtime(filepath)
                        if file_age > max_age:
                            unlink(filepath)
                            cleaned += 1
                            print("[vUtils] Cleaned old temp file: %s" % filepath)
                except Exception as e:
                    print("[vUtils] Error removing %s: %s" % (filepath, str(e)))

        if cleaned > 0:
            print("[vUtils] Total cleaned old temp files: %d" % cleaned)

        return cleaned

    except Exception as e:
        print("[vUtils] Error cleaning temp files: %s" % str(e))
        return 0


def preload_country_flags(country_list, cache_dir="/tmp/vavoo_flags"):
    """
    Preload flags for a list of countries.
    Each chunk of countries is downloaded in a separate daemon thread.
    Compatible with Python 2 and 3.
    """
    import threading

    def download_flags_worker(countries):
        for country in countries:
            try:
                success, _ = download_flag_online(country, cache_dir)
                if success:
                    print("[vUtils] Preloaded flag for: %s" % country)
            except Exception as e:
                print("[vUtils] Error preloading flag for %s: %s" % (country, str(e)))

    # Split list into chunks to avoid overloading
    chunk_size = 10
    threads = []

    if not country_list:
        return threads

    total = len(country_list)

    for i in range(0, total, chunk_size):
        chunk = country_list[i:i + chunk_size]
        t = threading.Thread(
            target=download_flags_worker,
            args=(chunk,)
        )
        t.daemon = True
        t.start()
        threads.append(t)

    return threads
