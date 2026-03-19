# -*- coding: utf-8 -*-

from __future__ import absolute_import
__author__ = "Lululla"
__email__ = "ekekaz@gmail.com"
__copyright__ = 'Copyright (c) 2024 Lululla'
__license__ = "CC BY-NC-SA 4.0"
__version__ = "1.61"

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
import os
import subprocess
from sys import version_info
import threading

# Lock to serialize exports (prevents concurrent executions)
export_lock = threading.Lock()

EXPORT_IN_PROGRESS = False
PROXY_ACTIVE = False
PORT = 4323
PLUGIN_ID = 'vavoo'
PLUGIN_ROOT = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format(PLUGIN_ID))

PROXY_HOST = "127.0.0.1"
PROXY_BASE_URL = "http://{}:{}".format(PROXY_HOST, PORT)
PROXY_STATUS_URL = PROXY_BASE_URL + "/status"
PROXY_HEALTH_URL = PROXY_BASE_URL + "/health"
PROXY_COUNTRIES_URL = PROXY_BASE_URL + "/countries"
PROXY_REFRESH_URL = PROXY_BASE_URL + "/refresh_token"
PROXY_SHUTDOWN_URL = PROXY_BASE_URL + "/shutdown"

HOST_MAIN = 'https://raw.githubusercontent.com/Belfagor2005/vavoo/main'
HOST_GIT = "https://raw.githubusercontent.com/Belfagor2005"
FLAG_CACHE_DIR = "/tmp/vavoo_flags"
LOG_FILE = "/tmp/vavoo.log"
PRIMARY_BASE_URL = "https://vavoo.to"
FALLBACK_BASE_URL = "https://kool.to"
BASE_SITES = [PRIMARY_BASE_URL, FALLBACK_BASE_URL]
START_PROXY_SCRIPT = os.path.join(PLUGIN_ROOT, "start_proxy.sh")
PY2 = version_info[0] == 2
PY3 = version_info[0] == 3

PluginLanguageDomain = PLUGIN_ID
PluginLanguagePath = 'Extensions/{}/locale'.format(PLUGIN_ID)


def get_enigma2_path():
    barry_active = '/media/ba/active/etc/enigma2'
    if os.path.exists(barry_active):
        return barry_active.rstrip('/')

    possible_paths = [
        '/autofs/sda1/etc/enigma2',
        '/autofs/sda2/etc/enigma2',
        '/etc/enigma2'
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path.rstrip('/')
    return '/etc/enigma2'


ENIGMA_PATH = get_enigma2_path()
CACHE_FILE = os.path.join(ENIGMA_PATH, "vavoo_epg_cache.json")
UNMATCHED_FILE = os.path.join(ENIGMA_PATH, "vavoo_epg_unmatched_cache.json")
SREF_MAP_FILE = os.path.join(ENIGMA_PATH, "vavoo_sref_map.json")
EPGIMPORT_CONF = os.path.join(ENIGMA_PATH, "epgimport.conf")


def _init_log(msg, level="INFO"):
    from datetime import datetime
    line = "[{0}] [{1}] [INIT] {2}".format(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), level, msg)
    try:
        print(line)
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def paypal():
    conthelp = "If you like what I do you\n"
    conthelp += "can contribute with a coffee\n"
    conthelp += "scan the qr code and donate € 1.00"
    return conthelp


isDreamOS = False
if os.path.exists("/usr/bin/apt-get"):
    isDreamOS = True


def localeInit():
    if isDreamOS:
        lang = language.getLanguage()[:2]
        os.environ["LANGUAGE"] = lang
    gettext.bindtextdomain(
        PluginLanguageDomain,
        resolveFilename(
            SCOPE_PLUGINS,
            PluginLanguagePath))


if isDreamOS:
    def _(txt):
        return gettext.dgettext(PluginLanguageDomain, txt) if txt else ""
else:
    def _(txt):
        translated = gettext.dgettext(PluginLanguageDomain, txt)
        if translated:
            return translated
        else:
            _init_log(
                "fallback to default translation for %s" %
                txt, level="DEBUG")
            return gettext.gettext(txt)

localeInit()
language.addCallback(localeInit)

try:
    subprocess.run(["chmod", "+x", START_PROXY_SCRIPT])
except AttributeError:
    subprocess.call(["chmod", "+x", START_PROXY_SCRIPT])
except Exception:
    pass

country_codes = {
    "Albania": "al",
    "Arabia": "sa",
    "Balkans": "bk",
    "Bulgaria": "bg",
    "Croatia": "hr",
    "France": "fr",
    "Germany": "de",
    "Italy": "it",
    "Netherlands": "nl",
    "Poland": "pl",
    "Portugal": "pt",
    "Romania": "ro",
    "Russia": "ru",
    "Spain": "es",
    "Turkey": "tr",
    "United Kingdom": "gb"
}
