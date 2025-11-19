#!/usr/bin/python
# -*- coding: utf-8 -*-

# Standard library
import base64
import json
import ssl
import types
from os import listdir, remove, system
from os.path import exists, getsize, isfile, join, splitext
from random import choice
from re import compile, search, sub
from sys import maxsize, version_info
from time import time
from unicodedata import normalize

# Six library (third-party / compatibility)
import six
from six import iteritems, unichr
from six.moves import html_entities, html_parser

# Third-party library
import requests

# Project-specific imports
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
MAXSIZE = maxsize  # Compatibile con entrambe le versioni

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
        # Decodifica le stringhe in Unicode per Python 2
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

        def do_delayed_reload():
            try:
                reload_timer2 = eTimer()
                try:
                    reload_timer2.callback.append(do_reload)
                except BaseException:
                    reload_timer2.timeout.connect(do_reload)
                reload_timer2.start(2000, True)
            except Exception as e:
                print("Error setting up delayed reload: " + str(e))

        reload_timer = eTimer()
        try:
            reload_timer.callback.append(do_delayed_reload)
        except BaseException:
            reload_timer.timeout.connect(do_delayed_reload)
        reload_timer.start(100, True)

    except Exception as e:
        print("Error setting up service reload: " + str(e))


def sanitizeFilename(filename):
    """Sanitize filename for safe filesystem use"""
    # Remove unsafe characters
    filename = sub(r'[\\/:*?"<>|\0]', '', filename)
    filename = ''.join(c for c in filename if ord(c) > 31)
    # Normalize and strip trailing characters
    filename = normalize('NFKD', filename).encode('ascii', 'ignore').decode()
    filename = filename.rstrip('. ').strip()
    # Handle reserved names
    reserved = ["CON", "PRN", "AUX", "NUL"] + ["COM" +
                                               str(i) for i in range(1, 10)] + ["LPT" + str(i) for i in range(1, 10)]
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
