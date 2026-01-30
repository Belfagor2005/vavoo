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

import codecs
import ssl
import time
import threading
from datetime import datetime
from os import listdir, unlink, remove, chmod, system as os_system
from os.path import exists as file_exists, join, islink, isfile, getsize
from re import compile, DOTALL
from json import loads
from sys import version_info

import requests
from requests.adapters import HTTPAdapter, Retry

try:
    from Components.AVSwitch import AVSwitch
except ImportError:
    from Components.AVSwitch import eAVControl as AVSwitch

from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest, MultiContentEntryText
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.config import (
    ConfigSelection,
    getConfigListEntry,
    ConfigSelectionNumber,
    ConfigClock,
    ConfigText,
    configfile,
    config,
    ConfigYesNo,
    ConfigEnableDisable,
    ConfigSubsection,
    NoSave
)
from enigma import (
    RT_HALIGN_LEFT,
    RT_HALIGN_RIGHT,
    RT_VALIGN_CENTER,
    eDVBDB,
    eListboxPythonMultiContent,
    ePicLoad,
    eServiceReference,
    eTimer,
    gFont,
    getDesktop,
    iPlayableService,
    iServiceInformation,
    loadPNG,
)

from Screens.InfoBarGenerics import (
    InfoBarSubtitleSupport,
    InfoBarMenu,
    InfoBarSeek,
    InfoBarAudioSelection,
    InfoBarNotifications,
)
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import SCOPE_PLUGINS, SCOPE_CONFIG, resolveFilename
from Tools.NumericalTextInput import NumericalTextInput
from Plugins.Plugin import PluginDescriptor

# Local application/library-specific imports
from . import _, __author__, __version__, __license__, PORT
from . import vUtils
from .Console import Console
from .bouquet_manager import (
    convert_bouquet,
    _update_favorite_file,
    reorganize_all_bouquets_position,
    remove_bouquets_by_name
)
from .vUtils import (
    # load_flag_to_widget,
    # preload_country_flags,
    # download_flag_with_size,
    # get_proxy_status,
    cleanup_old_temp_files,
    decodeHtml,
    download_flag_online,
    ensure_str,
    getUrl,
    get_country_code,
    initialize_cache_with_local_flags,
    is_proxy_ready,
    is_proxy_running,
    rimuovi_parentesi,
    trace_error
)
from .vavoo_proxy import run_proxy_in_background

PY2 = version_info[0] == 2
PY3 = version_info[0] == 3


try:
    # Python 3
    from urllib.parse import quote
except ImportError:
    # Python 2
    from urllib import quote


try:
    unicode
except NameError:
    unicode = str


if version_info >= (2, 7, 9):
    try:
        ssl_context = ssl._create_unverified_context()
    except:
        ssl_context = None


try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote


try:
    aspect_manager = vUtils.AspectManager()
    current_aspect = aspect_manager.get_current_aspect()
except:
    pass


try:
    from Components.UsageConfig import defaultMoviePath
    downloadfree = defaultMoviePath()
except:
    if file_exists("/usr/bin/apt-get"):
        downloadfree = ('/media/hdd/movie/')


try:
    unicode
except NameError:
    unicode = str


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


# set plugin
global HALIGN, BackPath, FONTSTYPE, FNTPath
global search_ok, screen_width
global proxy_instance, proxy_thread

title_plug = 'Vavoo'
desc_plugin = ('..:: Vavoo by Lululla v.%s ::..' % __version__)
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('vavoo'))
PLUGLOGO = join(PLUGIN_PATH, 'plugin.png')
ENIGMA_PATH = get_enigma2_path()
CONFIG_FILE = resolveFilename(SCOPE_CONFIG, "settings")
regexs = '<a[^>]*href="([^"]+)"[^>]*><img[^>]*src="([^"]+)"[^>]*>'

_session = None
auto_start_timer = None
now = None
proxy_instance = None
proxy_thread = None
search_ok = False
tmlast = None

# screen
HALIGN = RT_HALIGN_LEFT
screen_real = getDesktop(0).size()
screen_width = screen_real.width()
BackfPath = join(PLUGIN_PATH, "skin")

if screen_width == 2560:
    BackPath = join(BackfPath, 'images_new')
    skin_path = join(BackfPath, 'wqhd')
elif screen_width == 1920:
    BackPath = join(BackfPath, 'images_new')
    skin_path = join(BackfPath, 'fhd')
elif screen_width <= 1280:
    BackPath = join(BackfPath, 'images')
    skin_path = join(BackfPath, 'hd')
else:
    BackPath = None
    skin_path = None

print('folder back: ', BackPath)


# system
stripurl = 'aHR0cHM6Ly92YXZvby50by9jaGFubmVscw=='
keyurl = 'aHR0cDovL3BhdGJ1d2ViLmNvbS92YXZvby92YXZvb2tleQ=='
installer_url = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0JlbGZhZ29yMjAwNS92YXZvby9tYWluL2luc3RhbGxlci5zaA=='
developer_url = 'aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9CZWxmYWdvcjIwMDUvdmF2b28='

myser = [("https://vavoo.to", "vavoo"), ("https://oha.tooha-tv", "oha"),
         ("https://kool.to", "kool"), ("https://huhu.to", "huhu")]
mydns = [("None", "Default"), ("google", "Google"),
         ("coudfire", "Coudfire"), ("quad9", "Quad9")]
modemovie = [("4097", "4097")]
if file_exists("/usr/bin/gstplayer"):
    modemovie.append(("5001", "5001"))
if file_exists("/usr/bin/exteplayer3"):
    modemovie.append(("5002", "5002"))
if file_exists('/var/lib/dpkg/info'):
    modemovie.append(("8193", "8193"))


BakP = []
try:
    if file_exists(BackPath):
        for back_name in listdir(BackPath):
            back_name_path = join(BackPath, back_name)
            if back_name.endswith(".png"):
                if back_name.startswith("default"):
                    continue
                back_name = back_name[:-4]
                BakP.append((back_name, back_name))
except Exception as e:
    print(e)

print('final folder back: ', BackPath)


# Helper function for string conversion
def to_string(text):
    """Convert any input to proper string format for Enigma2 widgets"""
    if text is None:
        return ""

    # If it's already a unicode string (Python 2) or str (Python 3)
    if isinstance(text, unicode):
        return text.encode('utf-8', 'ignore') if PY2 else text

    # If it's bytes (Python 3)
    if PY3 and isinstance(text, bytes):
        return text.decode('utf-8', 'ignore')

    # For other types, convert to string
    return str(text)


# fonts
FNT_Path = join(PLUGIN_PATH, "fonts")
fonts = []
try:
    if file_exists(FNT_Path):
        for font_name in listdir(FNT_Path):
            font_name_path = join(FNT_Path, font_name)
            if font_name.endswith(".ttf") or font_name.endswith(".otf"):
                font_name = font_name[:-4]
                fonts.append((font_name, font_name))
        fonts = sorted(fonts, key=lambda x: x[1])
except Exception as e:
    print(e)


# config section
# --- Live search input field integrated in plugin config ---
class ConfigSearchText(ConfigText):
    def __init__(self, default=""):
        ConfigText.__init__(self, default=default)


config.plugins.vavoo = ConfigSubsection()
cfg = config.plugins.vavoo
cfg.autobouquetupdate = ConfigEnableDisable(default=False)
cfg.genm3u = NoSave(ConfigYesNo(default=False))
cfg.server = ConfigSelection(default="https://vavoo.to", choices=myser)
cfg.services = ConfigSelection(default='4097', choices=modemovie)
cfg.timerupdate = ConfigSelectionNumber(default=5, min=1, max=60, stepwidth=1)
cfg.timetype = ConfigSelection(
    default="interval", choices=[
        ("interval", _("interval")), ("fixed time", _("fixed time"))])
cfg.updateinterval = ConfigSelectionNumber(
    default=5, min=5, max=3600, stepwidth=5)
cfg.fixedtime = ConfigClock(default=46800)
cfg.last_update = ConfigText(default="Never")
cfg.stmain = ConfigYesNo(default=True)
cfg.ipv6 = ConfigEnableDisable(default=False)
cfg.dns = ConfigSelection(default="Default", choices=mydns)
cfg.fonts = ConfigSelection(default='vav', choices=fonts)
cfg.back = ConfigSelection(default='oktus', choices=BakP)
"""
cfg.default_view = ConfigSelection(
    default="countries",
    choices=[("countries", _("Countries")), ("categories", _("Categories"))]
)
"""
cfg.default_view = ConfigSelection(
    default="countries",
    choices=[("countries", _("Countries"))]
)
cfg.list_position = ConfigSelection(
    default="bottom",
    choices=[("bottom", _("Bottom")), ("top", _("Top"))]
)
cfg.search_text = ConfigSearchText(default="")

FONTSTYPE = FNT_Path + '/' + cfg.fonts.value + '.ttf'
eserv = int(cfg.services.value)

# ipv6
if islink('/etc/rc3.d/S99ipv6dis.sh'):
    cfg.ipv6.setValue(True)
    cfg.ipv6.save()

# language
locl = (
    "ar", "ae", "bh", "dz", "eg", "in", "iq", "jo",
    "kw", "lb", "ly", "ma", "om", "qa", "sa", "sd",
    "ss", "sy", "tn", "ye", "hr"
)

global lngx
lngx = 'en'
try:
    from Components.config import config
    lng = config.osd.language.value
    lng = lng[:-3]
    if any(s in lngx for s in locl):
        HALIGN = RT_HALIGN_RIGHT
except:
    lng = 'en'
    pass


# check server
def raises(url):
    """Attempts to fetch a URL with retries and error handling"""
    try:
        retries = Retry(total=1, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retries)
        http = requests.Session()
        http.mount("http://", adapter)
        http.mount("https://", adapter)

        r = http.get(
            url,
            headers={'User-Agent': vUtils.RequestAgent()},
            timeout=(3, 10),
            verify=True,
            stream=True,
            allow_redirects=False
        )
        r.raise_for_status()

        if r.status_code == requests.codes.ok:
            for xc in r.iter_content(1024):
                pass
            r.close()
            return True

    except Exception as error:
        print("Server check failed:", error)
        trace_error()
    return False


def zServer(opt=0, server=None, port=None):
    """Checks if a server is reachable and returns it, fallback to default"""
    try:
        from urllib.error import HTTPError
    except ImportError:
        from urllib2 import HTTPError

    try:
        if raises(server):
            print('server is reachable:', str(server))
            return str(server)
    except HTTPError as err:
        print(err.code)
        return 'https://vavoo.to'


# menulist
class m2list(MenuList):
    def __init__(self, items):
        super(m2list, self).__init__(items, False, eListboxPythonMultiContent)
        if screen_width == 2560:
            item_height = 60
            text_font_size = 38
        elif screen_width == 1920:
            item_height = 50
            text_font_size = 34
        else:
            item_height = 50
            text_font_size = 28
        self.l.setItemHeight(item_height)
        self.l.setFont(0, gFont('Regular', text_font_size))

    def buildEntry(self, entry):
        """Build list entry - entry should be [ (name, link), icon, text ]"""
        return entry


def show_list(name, link, is_category=False, is_channel=False):
    """Build a MultiContent entry with icon and text."""

    global HALIGN

    # Text alignment based on language
    if any(s in lng for s in locl):
        HALIGN = RT_HALIGN_RIGHT
    else:
        HALIGN = RT_HALIGN_LEFT

    safe_name = to_string(name)
    safe_link = to_string(link)

    res = [(safe_name, safe_link)]

    # Default icon
    default_icon = join(PLUGIN_PATH, 'skin/pics/vavoo_ico.png')
    icon_path = default_icon

    if not is_channel and not is_category:
        country_name = safe_name.split('➾')[0].split(
            '⟾')[0].split('→')[0].split('->')[0].strip()
        if country_name:
            try:
                country_code = get_country_code(country_name)
                if country_code:
                    cache_file = "/tmp/vavoo_flags/%s.png" % country_code.lower()

                    # Use cache if exists and valid
                    if file_exists(cache_file):
                        try:
                            if getsize(cache_file) > 100:
                                icon_path = cache_file
                            else:
                                unlink(cache_file)
                        except Exception:
                            pass

                    # If not in cache, use default icon (don't download here - use preloading)
                    # Download will happen in
                    # preload_flags_for_visible_countries()

            except Exception:
                pass

    if screen_width >= 2560:
        icon_size = (80, 60)
        icon_pos = (10, 10)
        text_size = (750, 60)
        text_pos = (icon_size[0] + 20, 0)
    elif screen_width >= 1920:
        icon_size = (60, 45)
        icon_pos = (10, 10)
        text_size = (540, 50)
        text_pos = (icon_size[0] + 20, 0)
    else:
        icon_size = (40, 30)
        icon_pos = (10, 5)
        text_size = (380, 50)
        text_pos = (icon_size[0] + 20, 0)

    # Load PNG
    try:
        png_data = loadPNG(icon_path)
    except Exception:
        try:
            png_data = loadPNG(default_icon)
        except Exception:
            png_data = None

    if png_data:
        res.append(MultiContentEntryPixmapAlphaTest(
            pos=icon_pos,
            size=icon_size,
            png=png_data
        ))

    res.append(MultiContentEntryText(
        pos=text_pos,
        size=text_size,
        font=0,
        text=safe_name,
        flags=HALIGN | RT_VALIGN_CENTER
    ))

    return list(res)


# proxy
"""
def start_proxy_at_boot():
    try:
        # Check if proxy is already running
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex(('127.0.0.1', 4323))
        s.close()

        if result != 0:  # Port not in use
            print("[Vavoo] Starting proxy at system boot...")
            # Start proxy
            proxy_script = "/usr/lib/enigma2/python/Plugins/Extensions/vavoo/vavoo_proxy.py"
            cmd = ["python", proxy_script, "&"]
            subprocess.Popen(cmd, shell=False)
            time.sleep(2)
        else:
            print("[Vavoo] Proxy already running at boot")
    except:
        pass


# start_proxy_at_boot()
"""


def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def get_proxy_stream_url(channel_id):
    """Get the stream URL via proxy"""
    local_ip = "127.0.0.1"
    # port = 4323
    return "http://" + str(local_ip) + ":" + str(PORT) + \
        "/resolve?id=" + str(channel_id)


def keep_proxy_alive():
    """Keep proxy alive by periodically checking it"""
    import threading

    def monitor_proxy():
        while True:
            try:
                if not is_proxy_running():
                    print(
                        "[Proxy Monitor] Proxy not running, attempting to restart...")
                    run_proxy_in_background()
                elif not is_proxy_ready():
                    print("[Proxy Monitor] Proxy running but not ready")
                # else: proxy is running and ready

            except Exception as e:
                print("[Proxy Monitor] Error: " + str(e))

            time.sleep(60)

    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_proxy, daemon=True)
    monitor_thread.start()
    return monitor_thread


class vavoo_config(Screen, ConfigListScreen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = join(skin_path, 'vavoo_config.xml')
        if isfile('/var/lib/dpkg/status'):
            skin = skin.replace('.xml', '_cvs.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Vavoo Config')
        self.list = []
        self.onChangedEntry = []
        self["version"] = Label()
        self['statusbar'] = Label()
        self["description"] = Label("")
        self["red"] = Label(_("Back"))
        self["green"] = Label(_("- - - -"))
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'DirectionActions'], {
            "cancel": self.extnok,
            "left": self.keyLeft,
            "right": self.keyRight,
            "up": self.keyUp,
            "down": self.keyDown,
            "red": self.extnok,
            "green": self.save,
            "ok": self.gnm3u,
        }, -1)
        self.update_status()
        ConfigListScreen.__init__(
            self,
            self.list,
            session=self.session,
            on_change=self.changedEntry)
        self.createSetup()
        self.v6 = cfg.ipv6.getValue()
        self.showhide()
        self.onLayoutFinish.append(self.layoutFinished)

    def update_status(self):
        if cfg.autobouquetupdate:
            self['statusbar'].setText(
                _("Last channel update: %s") %
                cfg.last_update.value)

    def layoutFinished(self):
        self.setTitle(self.setup_title)
        self['version'].setText('V.' + __version__)

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        indent = "- "
        self.list.append(
            getConfigListEntry(
                _("Generate .m3u files (Ok for Exec)"),
                cfg.genm3u,
                _("Generate .m3u files and save to device %s.") %
                downloadfree))
        self.list.append(
            getConfigListEntry(
                _("Default View"),
                cfg.default_view,
                _("Default view when opening the plugin")))
        help_text = _("Server for player.") + "\n" + \
            _("Now %s") % cfg.server.value
        self.list.append(
            getConfigListEntry(
                _("Server for Player Used"),
                cfg.server,
                help_text
            )
        )
        self.list.append(
            getConfigListEntry(
                _("Movie Services Reference"),
                cfg.services,
                _("Configure service Reference Iptv-Gstreamer-Exteplayer3")))
        self.list.append(
            getConfigListEntry(
                _("Bouquet Position in List"),
                cfg.list_position,
                _("Position of Vavoo bouquets in the main list"))
        )
        help_line1 = _("Refresh stream every X minutes (1-15)")
        help_line2 = _("Recommended: 5-8 minutes")
        help_line3 = _("Lower = less interruption but more refreshes")
        help_text = help_line1 + "\n" + help_line2 + "\n" + help_line3

        self.list.append(
            getConfigListEntry(
                _("Auto-refresh stream (minutes):"),
                cfg.timerupdate,
                help_text
            )
        )
        self.list.append(
            getConfigListEntry(
                _("Select DNS Server"),
                cfg.dns,
                _("Configure Dns Server for Box.")))
        self.list.append(
            getConfigListEntry(
                _("Select Background"),
                cfg.back,
                _("Configure Main Background Image.")))
        help_text2 = _("Configure Fonts.") + "\n" + \
            _("Eg: Arabic or other language.")
        self.list.append(
            getConfigListEntry(
                _("Select Fonts"),
                cfg.fonts,
                help_text2
            )
        )
        help_part1 = _("Active or Disactive lan Ipv6.")
        help_part2 = _("Now %s") % cfg.ipv6.value
        help_text3 = help_part1 + "\n" + help_part2

        self.list.append(
            getConfigListEntry(
                _("Ipv6 State Of Lan (On/Off)"),
                cfg.ipv6,
                help_text3
            )
        )
        self.list.append(
            getConfigListEntry(
                _("Scheduled List Update:"),
                cfg.autobouquetupdate,
                _("Active Automatic Bouquet Update")))
        if cfg.autobouquetupdate.value is True:
            self.list.append(
                getConfigListEntry(
                    indent + _("Schedule type:"),
                    cfg.timetype,
                    _("At an interval of hours or at a fixed time")))
            if cfg.timetype.value == "interval":
                self.list.append(
                    getConfigListEntry(
                        2 * indent + _("Update interval (minutes):"),
                        cfg.updateinterval,
                        _("Configure every interval of minutes from now")))
            if cfg.timetype.value == "fixed time":
                self.list.append(
                    getConfigListEntry(
                        2 * indent + _("Time to start update:"),
                        cfg.fixedtime,
                        _("Configure at a fixed time")))

        self.list.append(
            getConfigListEntry(
                _('Link in Main Menu'),
                cfg.stmain,
                _("Link in Main Menu")))
        self["config"].list = self.list
        self["config"].l.setList(self.list)
        self.setInfo()

    def gnm3u(self):
        sel = self["config"].getCurrent()[1]
        if sel and sel == cfg.genm3u:
            self.session.openWithCallback(
                self.generate_m3u,
                MessageBox,
                _("Generate .m3u files and save to device %s?") %
                downloadfree,
                MessageBox.TYPE_YESNO,
                timeout=10,
                default=True)

    def generate_m3u(self, result):
        if result:
            # 1. Check if the proxy is active
            if not self.check_and_start_proxy():
                self.session.open(
                    MessageBox,
                    _("Proxy not active. Unable to generate M3U file."),
                    MessageBox.TYPE_ERROR,
                    timeout=5
                )
                cfg.genm3u.setValue(0)
                cfg.genm3u.save()
                return

            # 2. Get country list from proxy
            try:
                countries = self.get_countries_from_proxy()
                if not countries:
                    raise Exception("No countries available")

                # 3. ASK MODE: single country or all?
                from Screens.ChoiceBox import ChoiceBox

                choices = [
                    (_("All countries (%d)") % len(countries), "all"),
                    (_("Only one specific country"), "single"),
                    (_("Cancel"), "cancel")
                ]

                self.session.openWithCallback(
                    self.on_m3u_mode_selected,
                    ChoiceBox,
                    title=_("Select M3U export mode:"),
                    list=choices
                )

            except Exception as e:
                print("[M3U Export] Error: %s" % str(e))
                self.session.open(
                    MessageBox,
                    _("Error: %s") % str(e),
                    MessageBox.TYPE_ERROR,
                    timeout=5
                )

                cfg.genm3u.setValue(0)
                cfg.genm3u.save()

    def on_m3u_mode_selected(self, result):
        """Callback for M3U mode selection"""
        if result is None or result[1] == "cancel":
            cfg.genm3u.setValue(0)
            cfg.genm3u.save()
            return

        mode = result[1]

        try:
            countries = self.get_countries_from_proxy()
            if not countries:
                raise Exception("No countries available")

            if mode == "all":
                # Generate for all countries
                self.session.openWithCallback(
                    lambda confirm: self.generate_all_m3u_files(
                        confirm,
                        countries),
                    MessageBox,
                    _("Generate .m3u files for ALL %d countries?") %
                    len(countries),
                    MessageBox.TYPE_YESNO)
            elif mode == "single":
                # Show country list for single selection
                self.show_country_selection(countries)

        except Exception as e:
            print("[M3U Export] Error in mode selection: %s" % str(e))
            self.session.open(
                MessageBox,
                _("Error: %s") % str(e),
                MessageBox.TYPE_ERROR,
                timeout=5
            )

            cfg.genm3u.setValue(0)
            cfg.genm3u.save()

    def show_country_selection(self, countries):
        """Show country list for single selection"""
        from Screens.ChoiceBox import ChoiceBox

        # Create choice list
        choices = []
        for country in sorted(countries):
            choices.append((country, country))

        choices.append((_("Cancel"), "cancel"))

        self.session.openWithCallback(
            self.on_country_selected,
            ChoiceBox,
            title=_("Select country to export M3U:"),
            list=choices
        )

    def on_country_selected(self, result):
        """Callback for selected country"""
        if result is None or result[1] == "cancel":
            cfg.genm3u.setValue(0)
            cfg.genm3u.save()
            return

        selected_country = result[1]

        # Get channels for the selected country
        channels = self.get_channels_for_country(selected_country)

        if not channels or len(channels) == 0:
            self.session.open(
                MessageBox,
                _("No channels found for: %s") % selected_country,
                MessageBox.TYPE_WARNING,
                timeout=5
            )
            cfg.genm3u.setValue(0)
            cfg.genm3u.save()
            return

        # Ask confirmation for single country
        part1 = _("Generate .m3u file for:")
        part2 = str(selected_country)
        part3 = _("(%d channels)?") % len(channels)
        message = part1 + "\n" + part2 + "\n" + part3
        self.session.openWithCallback(
            lambda confirm: self.generate_single_country_m3u(
                confirm,
                selected_country,
                channels),
            MessageBox,
            message,
            MessageBox.TYPE_YESNO)

    def generate_single_country_m3u(self, confirm, country_name, channels):
        """Generate M3U for a single country"""
        if not confirm:
            cfg.genm3u.setValue(0)
            cfg.genm3u.save()
            return

        try:
            # Generate .m3u file
            m3u_count = self.generate_single_m3u(country_name, channels)

            if m3u_count > 0:
                msg_parts = []
                msg_parts.append(_("M3U file generated successfully!"))
                msg_parts.append("")
                msg_parts.append(_("Country: %s") % country_name)
                msg_parts.append(_("Channels: %d") % m3u_count)
                msg_parts.append(_("Saved in: %s") % downloadfree)
                msg = "\n".join(msg_parts)
                self.session.open(
                    MessageBox,
                    msg,
                    MessageBox.TYPE_INFO,
                    timeout=5
                )
            else:
                self.session.open(
                    MessageBox,
                    _("No valid channels for: %s") % country_name,
                    MessageBox.TYPE_WARNING,
                    timeout=5
                )

        except Exception as e:
            print("[M3U Export] Error for %s: %s" % (country_name, str(e)))
            self.session.open(
                MessageBox,
                _("M3U generation error: %s") % str(e),
                MessageBox.TYPE_ERROR,
                timeout=5
            )

        cfg.genm3u.setValue(0)
        cfg.genm3u.save()

    def generate_all_m3u_files(self, confirm, countries):
        """Generate .m3u files for all countries"""
        if not confirm:
            cfg.genm3u.setValue(0)
            cfg.genm3u.save()
            return

        try:
            total_channels = 0
            generated = 0
            failed = 0

            for country in countries:
                try:
                    # Get channels for this country
                    channels = self.get_channels_for_country(country)
                    if not channels:
                        failed += 1
                        continue

                    # Generate .m3u file
                    m3u_count = self.generate_single_m3u(country, channels)

                    if m3u_count > 0:
                        total_channels += m3u_count
                        generated += 1
                        print(
                            "[M3U Export] OK %s: %d channels" %
                            (country, m3u_count))
                    else:
                        failed += 1
                        print("[M3U Export] FAIL %s: no channels" % country)

                except Exception as e:
                    failed += 1
                    print("[M3U Export] Error %s: %s" % (country, str(e)))

            # Show detailed result
            msg = _("M3U generation completed!")
            msg += ""
            msg += _("Countries: %(generated)d/%(total)d") % {
                'generated': generated, 'total': len(countries)}
            msg += ""
            msg += _("Failed: %(failed)d") % {'failed': failed}
            msg += ""
            msg += _("Total channels: %(total_channels)d") % {
                'total_channels': total_channels}
            msg += ""
            msg += _("Saved in: %(path)s") % {'path': downloadfree}

            self.session.open(
                MessageBox,
                msg,
                MessageBox.TYPE_INFO,
                timeout=7
            )

        except Exception as e:
            print("[M3U Export] General error: %s" % str(e))
            self.session.open(
                MessageBox,
                _("M3U generation error: %s") % str(e),
                MessageBox.TYPE_ERROR,
                timeout=5
            )

        cfg.genm3u.setValue(0)
        cfg.genm3u.save()

    def generate_single_m3u(self, country_name, channels):
        """Generate a single .m3u file for a country"""
        try:
            # Sanitize filename
            safe_name = country_name.lower()
            safe_name = safe_name.replace(' ', '_')
            safe_name = safe_name.replace('➾', '_').replace('⟾', '_')
            safe_name = safe_name.replace('->', '_').replace('→', '_')

            m3u_filename = "vavoo_%s.m3u" % safe_name
            m3u_path = join(downloadfree, m3u_filename)

            # M3U header
            m3u_content = "#EXTM3U\n"

            channel_count = 0
            for channel in channels:
                try:
                    if isinstance(channel, dict):
                        channel_name = channel.get('name', 'Unknown')
                        channel_url = channel.get('url', '')

                        # Clean channel name
                        channel_name = decodeHtml(channel_name)
                        channel_name = rimuovi_parentesi(channel_name)

                        # Write M3U entry
                        m3u_content += "#EXTINF:-1,%s\n" % channel_name
                        m3u_content += "%s\n" % channel_url
                        channel_count += 1

                except Exception as e:
                    print("[M3U] Error processing channel: %s" % str(e))
                    continue

            if channel_count == 0:
                print("[M3U] No valid channels for %s" % country_name)
                return 0

            # Write file
            try:
                with open(m3u_path, 'w', encoding='utf-8') as f:
                    f.write(m3u_content)
                print(
                    "[M3U] File created: %s (%d channels)" %
                    (m3u_path, channel_count))
            except Exception as e:
                print("[M3U] Error writing file: %s" % str(e))
                with open(m3u_path, 'w') as f:
                    f.write(m3u_content)

            return channel_count

        except Exception as e:
            print(
                "[M3U] Error generating M3U for %s: %s" %
                (country_name, str(e)))
            return 0

    def get_channels_for_country(self, country_name):
        """Get channels for a country from the proxy"""
        try:
            encoded_country = quote(country_name)
            proxy_url = "http://127.0.0.1:%d/channels?country=%s" % (
                PORT, encoded_country)

            response = getUrl(proxy_url, timeout=15)
            if not response:
                print("[M3U] No response for %s" % country_name)
                return []

            channels = loads(response)
            return channels

        except Exception as e:
            print("[M3U] Error getting channels: %s" % str(e))
            return []

    def check_and_start_proxy(self):
        """Check and start the proxy if needed"""
        try:
            if not is_proxy_running():
                print("[M3U Export] Starting proxy...")
                if not run_proxy_in_background():
                    return False

            # Wait until the proxy is ready
            for i in range(10):
                if is_proxy_ready():
                    return True
                time.sleep(1)

            return False

        except Exception as e:
            print("[M3U Export] Proxy error: %s" % str(e))
            return False

    def get_countries_from_proxy(self):
        """Get country list from the proxy"""
        try:
            response = getUrl("http://127.0.0.1:4323/countries", timeout=10)
            if response:
                return loads(response)

        except Exception as e:
            print("[M3U Export] Countries error: %s" % str(e))

        return []

    def setInfo(self):
        try:
            sel = self['config'].getCurrent()[2]
            if sel:
                self['description'].setText(str(sel))
            else:
                self['description'].setText(_('SELECT YOUR CHOICE'))
            return
        except Exception as error:
            print('error as:', error)
            trace_error()

    def ipv6check(self, result):
        if result:
            if islink('/etc/rc3.d/S99ipv6dis.sh'):
                unlink('/etc/rc3.d/S99ipv6dis.sh')
                cfg.ipv6.setValue(False)
            else:
                os_system("echo '#!/bin/bash")
                os_system(
                    "echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6' > /etc/init.d/ipv6dis.sh")
                chmod("/etc/init.d/ipv6dis.sh", 0o700)
                os_system(
                    "ln -s /etc/init.d/ipv6dis.sh /etc/rc3.d/S99ipv6dis.sh")
                cfg.ipv6.setValue(True)
            cfg.ipv6.save()

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()
        self['green'].instance.setText(
            _('Save') if self['config'].isChanged() else '- - - -')

    def getCurrentEntry(self):
        return self["config"].getCurrent()[0]

    def showhide(self):
        pass

    def getCurrentValue(self):
        return str(self["config"].getCurrent()[1].getText())

    def createSummary(self):
        from Screens.Setup import SetupSummary
        return SetupSummary

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.createSetup()
        self.showhide()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.createSetup()
        self.showhide()

    def keyDown(self):
        self['config'].instance.moveSelection(self['config'].instance.moveDown)
        self.createSetup()
        self.showhide()

    def keyUp(self):
        self['config'].instance.moveSelection(self['config'].instance.moveUp)
        self.createSetup()
        self.showhide()

    def _reorganize_bouquets_position(self):
        """Reorganize all Vavoo bouquets to the new position"""
        if reorganize_all_bouquets_position(cfg.list_position.value):
            self.session.open(
                MessageBox,
                _("Bouquets reorganized successfully!"),
                MessageBox.TYPE_INFO,
                timeout=3)

    def save(self):
        if self["config"].isChanged():
            old_position = getattr(cfg, 'list_position', None)
            if old_position:
                old_position = old_position.value

            for x in self["config"].list:
                x[1].save()

            if old_position and old_position != cfg.list_position.value:
                self._reorganize_bouquets_position()

            for x in self["config"].list:
                x[1].save()

            if self.v6 != cfg.ipv6.value:
                # Se il valore di ipv6 è cambiato, applica i cambiamenti
                if islink('/etc/rc3.d/S99ipv6dis.sh'):
                    unlink('/etc/rc3.d/S99ipv6dis.sh')
                if cfg.ipv6.value:
                    os_system("echo '#!/bin/bash")
                    os_system(
                        "echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6' > /etc/init.d/ipv6dis.sh")
                    chmod("/etc/init.d/ipv6dis.sh", 0o700)
                    os_system(
                        "ln -s /etc/init.d/ipv6dis.sh /etc/rc3.d/S99ipv6dis.sh")

            configfile.save()

            try:
                config.loadFromFile(configfile.CONFIG_FILE)
            except Exception as e:
                print("Config reload error (safe mode): " + str(e))
                self._safe_config_reload()

            global FONTSTYPE
            FONTSE = str(cfg.fonts.getValue()) + '.ttf'
            FONTSTYPE = join(str(FNT_Path), str(FONTSE))
            add_skin_font()
            bakk = str(cfg.back.getValue()) + '.png'
            add_skin_back(bakk)

            self.session.open(
                MessageBox,
                _("Configuration saved successfully!"),
                MessageBox.TYPE_INFO,
                timeout=5
            )

            self.close()

    def _safe_config_reload(self):
        """Safe configuration reload"""
        try:
            if not hasattr(config.plugins, 'vavoo'):
                config.plugins.vavoo = ConfigSubsection()
                print("Recreated vavoo config section")

            config.loadFromFile(configfile.CONFIG_FILE)
        except Exception as e:
            print("Safe config reload failed: " + str(e))

    def extnok(self, answer=None):
        if answer is None:
            if self['config'].isChanged():
                self.session.openWithCallback(
                    self.extnok, MessageBox, _("Really close without saving settings?"))
            else:
                self.close()
        elif answer:
            for x in self["config"].list:
                x[1].cancel()
            self.close()
        else:
            return


class startVavoo(Screen):
    def __init__(self, session):
        self.session = session
        global _session, first
        _session = session
        first = True
        Screen.__init__(self, session)
        skin = join(skin_path, 'Plgnstrt.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self["poster"] = Pixmap()
        self["version"] = Label()
        self['actions'] = ActionMap(
            ['OkCancelActions'], {
                'ok': self.clsgo, 'cancel': self.clsgo}, -1)
        self.onLayoutFinish.append(self.loadDefaultImage)

    def decodeImage(self):
        pixmapx = self.fldpng
        if isfile(pixmapx):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()
            self.picload.setPara(
                [size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])

            if isfile("/var/lib/dpkg/status"):
                self.picload.startDecode(pixmapx, False)
            else:
                self.picload.startDecode(pixmapx, 0, 0, False)
            ptr = self.picload.getData()
            if ptr is not None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
                self['version'].setText('V.' + __version__)

    def loadDefaultImage(self):
        self.fldpng = resolveFilename(
            SCOPE_PLUGINS,
            "Extensions/{}/skin/pics/presplash.png".format('vavoo'))
        self.timer = eTimer()
        if isfile('/var/lib/dpkg/status'):
            self.timer.timeout.connect(self.decodeImage)
        else:
            self.timer.callback.append(self.decodeImage)
        self.timer.start(500, True)
        self.timerx = eTimer()
        if isfile('/var/lib/dpkg/status'):
            self.timerx.timeout.connect(self.clsgo)
        else:
            self.timerx.callback.append(self.clsgo)
        self.timerx.start(2000, True)
        self["version"].setText(to_string("V." + __version__))

    def clsgo(self):
        if first is True:
            self.session.openWithCallback(self.passe, MainVavoo)
        else:
            self.close()

    def passe(self, rest=None):
        global first
        first = False
        self.close()


class MainVavoo(Screen):
    def __init__(self, session):
        self.session = session
        global _session
        _session = session

        Screen.__init__(self, session)
        skin = join(skin_path, 'defaultListScreen.xml')
        if isfile('/var/lib/dpkg/status'):
            skin = skin.replace('.xml', '_cvs.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self._initialize_labels()
        self._initialize_actions()
        self["menulist"].onSelectionChanged.append(self._update_selection_name)
        self.url = vUtils.b64decoder(stripurl)
        self.currentList = 'menulist'
        self.loading_ok = False
        self.count = 0
        self.loading = 0
        self.current_view = "categories"
        self.flag_refresh_timer = eTimer()
        try:
            self.flag_refresh_timer.callback.append(self.refresh_list_with_flags)
        except Exception:
            # Fallback in case the callback attribute does not exist
            self.flag_refresh_timer.timeout.connect(self.refresh_list_with_flags)

        self.start_vavoo_proxy()
        # self.monitor_thread = keep_proxy_alive()
        """
        self.check_proxy_timer = eTimer()
        try:
            self.check_proxy_timer_conn = self.check_proxy_timer.timeout.connect(self.check_proxy_status)
        except:
            self.check_proxy_timer.callback.append(self.check_proxy_status)
        self.check_proxy_timer.start(5000, True)  # Check after 5 seconds

        self.proxy_status_timer = eTimer()
        try:
            self.proxy_status_timer_conn = self.proxy_status_timer.timeout.connect(
                self.update_proxy_status
            )
        except Exception:
            self.proxy_status_timer.callback.append(self.update_proxy_status)

        self.proxy_status_timer.start(30000)
        """
        self.proxy_watchdog_timer = eTimer()
        try:
            self.proxy_watchdog_timer.timeout.connect(self._proxy_watchdog_check)
        except:
            self.proxy_watchdog_timer.callback.append(self._proxy_watchdog_check)
        self.proxy_watchdog_timer.start(60000)  # Check ogni 60 secondi

        # No need for monitor thread - proxy stays alive automatically
        # Just check if it's ready
        self.proxy_monitor_timer = eTimer()
        try:
            self.proxy_monitor_timer.timeout.connect(self._check_and_update_proxy_status)
        except:
            self.proxy_monitor_timer.callback.append(self._check_and_update_proxy_status)
        self.proxy_monitor_timer.start(10000)  # Ogni 10 secondi
        self.cat()

    def _initialize_labels(self):
        """Initialize the labels on the screen."""
        self.menulist = []
        global search_ok
        search_ok = False
        self['menulist'] = m2list([])
        self['red'] = Label(_('Exit'))
        self['green'] = Label(_('Remove') + ' Fav')
        self['yellow'] = Label(_('Update Me'))
        self["blue"] = Label(_('Reload Bouqet'))
        self['name'] = Label('Loading...')
        self['version'] = Label()
        self['proxy_status'] = Label('Wait...')

    def _initialize_actions(self):
        """Initialize the actions for buttons."""
        actions = {
            'prevBouquet': self.chDown,
            'nextBouquet': self.chUp,
            'ok': self.ok,
            'mainMenu': self.goConfig,
            'menu': self.goConfig,
            'green': self.msgdeleteBouquets,
            'blue': lambda: self._reload_services(showMsg=True),
            'cancel': lambda: self._reload_services(showMsg=False),
            # 'exit': lambda: self._reload_services(showMsg=False),
            'red': lambda: self._reload_services(showMsg=False),
            'info': self.info,
            'InfoPressed': self.info,
            'yellow': self.update_me,
            'yellow_long': self.update_dev,
            'info_long': self.update_dev,
            'infolong': self.update_dev,
            'showEventInfoPlugin': self.update_dev,
            'text': self.refresh_proxy,
        }
        actions_list = [
            'MenuActions',
            'OkCancelActions',
            'ButtonSetupActions',
            'InfobarEPGActions',
            'EPGSelectActions'
        ]
        self['actions'] = ActionMap(actions_list, actions, -1)

    def _reload_services(self, showMsg=True):
        print("[DEBUG] Reload services | showMsg =", showMsg)

        eDVBDB.getInstance().reloadBouquets()
        eDVBDB.getInstance().reloadServicelist()

        if showMsg:
            try:
                self.session.open(
                    MessageBox,
                    "Bouquets reloaded successfully.",
                    MessageBox.TYPE_INFO,
                    timeout=5
                )
            except Exception as e:
                print("[MessageBox] Error:", e)

        if not showMsg:
            self.close()

    def closex(self):
        print("[DEBUG] Exit from plugin. Calling _reload_services_after_delay...")
        # Clean up temp files
        try:
            cleaned = cleanup_old_temp_files(
                max_age_hours=0)  # Clean ALL temp files
            print("[Cleanup] Removed %d temporary files" % cleaned)
        except Exception as e:
            print("[Cleanup] Error: %s" % str(e))

        self._reload_services(showMsg=False)
        self.close()

    def preload_flags_for_visible_countries(self):
        """Pre-carica le bandiere per i paesi visibili"""
        try:
            if not hasattr(self, 'all_data'):
                return

            # Estrai lista paesi
            countries = set()
            for entry in self.all_data:
                country = unquote(entry["country"]).strip("\r\n")
                if "➾" not in country:
                    countries.add(country)

            countries_list = sorted(list(countries))

            print(
                "[MainVavoo] Preloading flags for %d countries" %
                len(countries_list))

            # Preload first 8 flags SYNCHRONOUSLY
            downloaded = 0
            for i, country in enumerate(countries_list[:8]):  # First 8
                try:
                    success, _ = download_flag_online(
                        country, screen_width=screen_width)
                    if success:
                        downloaded += 1
                        print("[Preload] OK: %s" % country)
                except Exception as e:
                    print("[Preload] Error %s: %s" % (country, str(e)))

            print("[MainVavoo] Downloaded %d flags synchronously" % downloaded)

            # Start timer for refresh after 1 second
            if downloaded > 0:
                self.flag_refresh_timer.start(1000, True)

            # Download remaining in background
            if len(countries_list) > 8:

                def download_rest():
                    for country in countries_list[8:]:
                        try:
                            download_flag_online(
                                country, screen_width=screen_width)
                        except:
                            pass

                    print("[Background] Finished downloading remaining flags")
                thread = threading.Thread(target=download_rest)
                thread.daemon = True
                thread.start()

        except Exception as e:
            print("[MainVavoo] Error preloading flags: %s" % str(e))

    def refresh_list_with_flags(self):
        """Refresh list to show downloaded flags (Python 2/3 compatible)"""
        try:
            print("[MainVavoo] Refreshing list to show downloaded flags")

            # Recreate the list
            if cfg.default_view.value == "countries":
                self.show_countries_view()
            else:
                self.show_categories_view()

            self._update_ui()

            # Stop the timer
            self.flag_refresh_timer.stop()

        except Exception as e:
            print("[MainVavoo] Error refreshing list: %s" % str(e))

    def _proxy_watchdog_check(self):
        """Watchdog per verificare se il proxy è ancora vivo"""
        try:
            if not is_proxy_running():
                print("[Watchdog] Proxy not running, attempting restart...")
                self['proxy_status'].setText("⚠ Restarting...")

                # Try restart
                success = run_proxy_in_background()

                if success:
                    print("[Watchdog] Proxy restarted successfully")
                    self['proxy_status'].setText("✓ Restarted")
                else:
                    print("[Watchdog] Proxy restart failed")
                    self['proxy_status'].setText("✗ Restart Failed")

        except Exception as e:
            print("[Watchdog] Error: " + str(e))

    def _check_and_update_proxy_status(self):
        """Unified method to check proxy status and update display"""
        try:
            # 1. Check proxy health
            if not is_proxy_ready(timeout=2):
                print("[MainVavoo] Proxy check: proxy not ready")
                self.proxy_needs_attention = True
                self['proxy_status'].setText("⚠ Proxy Issue")
            else:
                self.proxy_needs_attention = False

            # 2. Update status display
            self._update_proxy_status_display()

        except Exception as e:
            print("[MainVavoo] Error in proxy monitor: " + str(e))
            self['proxy_status'].setText("✗ Proxy Error")

    def update_proxy_status(self):
        """Public method to update proxy status (can be called manually)"""
        self._update_proxy_status_display()

    def _update_proxy_status_display(self):
        """Internal method to update proxy status display"""
        try:
            if is_proxy_running():
                try:
                    response = getUrl(
                        "http://127.0.0.1:4323/status", timeout=2)
                    if response:
                        status_data = loads(response)

                        if status_data.get(
                                "initialized", False) and status_data.get(
                                "addon_sig_valid", False):
                            token_age = status_data.get("addon_sig_age", 0)

                            if token_age < 300:
                                status_text = "✓ Proxy OK"
                            elif token_age < 540:
                                ttl = 600 - token_age
                                status_text = "✓ Proxy (" + \
                                    str(int(ttl)) + "s)"
                            else:
                                status_text = "⚠ Proxy (expiring)"
                        else:
                            status_text = "✗ Proxy Error"
                    else:
                        status_text = "? Proxy Unknown"
                except Exception:
                    status_text = "✓ Proxy Running"
            else:
                status_text = "✗ Proxy Offline"

            self['proxy_status'].setText(status_text)

        except Exception as e:
            print("[MainVavoo] Error updating proxy status: " + str(e))

    def refresh_proxy(self):
        """Force proxy refresh"""
        try:
            self.session.openWithCallback(
                self._refresh_proxy_callback,
                MessageBox,
                "Force proxy refresh?\nThis will refresh the authentication token.",
                MessageBox.TYPE_YESNO)
        except Exception as e:
            print("[MainVavoo] Refresh proxy error: " + str(e))

    def _refresh_proxy_callback(self, result):
        """Callback for proxy refresh"""
        if result:
            try:
                response = getUrl(
                    "http://127.0.0.1:4323/refresh_token",
                    timeout=5
                )
                if response:
                    self.session.open(
                        MessageBox,
                        "Proxy token refreshed successfully",
                        MessageBox.TYPE_INFO,
                        timeout=3
                    )
                    self.update_proxy_status()
            except Exception as e:
                self.session.open(
                    MessageBox,
                    "Failed to refresh proxy: " + str(e),
                    MessageBox.TYPE_ERROR,
                    timeout=3
                )

    def start_vavoo_proxy(self):
        """Start the proxy only if it is not already running"""
        try:
            if is_proxy_running():
                print("[MainVavoo] Proxy already running")
                return True

            print("[MainVavoo] Starting proxy...")
            success = run_proxy_in_background()

            if success:
                print("[MainVavoo] Proxy started")
                return True
            else:
                print("[MainVavoo] Proxy start error")
                return False

        except Exception as e:
            print("[MainVavoo] Error: {0}".format(e))
            return False

    def _restart_proxy(self):
        """Restart the proxy if it is stuck"""
        try:
            # Try to stop the existing proxy
            try:
                requests.get("http://127.0.0.1:4323/shutdown", timeout=2)
                time.sleep(3)
            except:
                pass

            # Kill python processes that could be the proxy
            os_system("pkill -f 'python.*vavoo_proxy' 2>/dev/null")
            time.sleep(2)

            # Restart
            return run_proxy_in_background()

        except:
            return False

    def _reload_services_after_delay(self):
        eDVBDB.getInstance().reloadBouquets()
        eDVBDB.getInstance().reloadServicelist()

    def cat(self):
        self.cat_list = []
        self.items_tmp = []

        try:
            # === 1. LOAD DATA ONLY FROM ORIGINAL METHOD (vavoo.to) ===
            print("[MainVavoo] Loading countries from original source...")
            content = self._get_content()
            if PY3:
                content = vUtils.ensure_str(content)

            if not content:
                self["name"].setText(to_string("Error: No data received"))
                return

            data = self._parse_json(content)
            if data is None:
                self["name"].setText(to_string("Error: Invalid data format"))
                return

            self.all_data = data
            print(
                "[MainVavoo] Loaded %d channels from original source" % len(
                    self.all_data))

            # === 2. EXTRACT AND DISPLAY COUNTRIES (NO PROXY DEPENDENCY) ===
            if cfg.default_view.value == "countries":
                # Extract ONLY main countries (exclude ➾ categories)
                countries = set()
                for entry in self.all_data:
                    country = unquote(entry["country"]).strip("\r\n")
                    # CRITICAL FILTER: exclude "default" and problematic
                    # strings
                    if "➾" not in country and country.lower() != "default" and len(country) > 1:
                        countries.add(country)

                countries_list = sorted(list(countries))
                print(
                    "[MainVavoo] Found %d valid countries" %
                    len(countries_list))

                # Preload flags for first countries
                for country in countries_list[:5]:
                    try:
                        country_code = get_country_code(country)
                        if country_code:
                            success, _ = download_flag_online(
                                country,
                                cache_dir="/tmp/vavoo_flags",
                                screen_width=1920
                            )
                            if success:
                                print("✓ Preloaded flag for: %s" % country)
                    except Exception as e:
                        print(
                            "Flag preload error for %s: %s" %
                            (country, str(e)))

                # Show countries view
                self.show_countries_view()
            else:
                # Show categories view
                self.show_categories_view()

            # === 3. UPDATE INTERFACE ===
            self._update_ui()

            # === 4. START PROXY IN BACKGROUND (ONLY FOR NEXT PHASE) ===
            # Does NOT block UI, handles its own errors internally
            if not hasattr(self, '_proxy_bg_started'):
                def start_bg_proxy():
                    try:
                        print(
                            "[BG] Starting proxy for future channel resolution...")
                        # Important: do not call initialize_for_country("default")!
                        # Let the proxy start with its base configuration.
                        self.start_vavoo_proxy()
                    except Exception as bg_e:
                        print(
                            "[BG] Proxy background start non-critical: %s" %
                            str(bg_e))

                import threading
                bg_thread = threading.Thread(
                    target=start_bg_proxy, daemon=True)
                bg_thread.start()
                self._proxy_bg_started = True

        except Exception as error:
            print("[MainVavoo] Critical error in cat(): %s" % str(error))
            trace_error()
            self["name"].setText(to_string("Error loading data"))

        self["version"].setText(to_string("V." + __version__))

    def _fallback_to_original_countries(self):
        """Fallback to the original method of getting countries"""
        try:
            content = getUrl(self.url)
            if PY3:
                content = ensure_str(content)

            if not content:
                self["name"].setText(to_string("Error: No data received"))
                return

            data = loads(content)
            self.all_data = data

            countries = set()
            for entry in self.all_data:
                country = unquote(entry["country"]).strip("\r\n")
                if "➾" not in country:
                    countries.add(country)

            countries_list = sorted(list(countries))

            for country in countries_list:
                self.cat_list.append(show_list(country, country))

            self._update_ui()

        except Exception as error:
            print("[MainVavoo] Error in fallback: %s" % error)
            self["name"].setText(to_string("Error loading data"))

    def _parse_select_options(self, html_content):
        """Parses options from the HTML select menu"""
        options = []

        # Regex to find the select menu and its options
        select_pattern = r'<select[^>]*>(.*?)</select>'
        option_pattern = r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>'

        select_match = compile(select_pattern, DOTALL).search(html_content)
        if select_match:
            select_content = select_match.group(1)
            option_matches = compile(
                option_pattern, DOTALL).findall(select_content)
            for value, text in option_matches:
                if value and text and text != "All countries":
                    options.append((text.strip(), value))

        return options

    def _get_content(self):
        """Get data directly from vavoo.to"""
        content = getUrl(self.url)
        if PY3:
            content = ensure_str(content)
        return content

    def _parse_json(self, content):
        try:
            return loads(content)
        except ValueError:
            print("Error parsing JSON data")
            self["name"].setText("Error parsing data")
            return None

    def show_categories_view(self):
        """Show only categories (without main countries) - SINGLE FILE EXPORT"""
        self.current_view = "categories"
        self.cat_list = []

        if not hasattr(self, 'all_data'):
            return

        categories = set()
        for entry in self.all_data:
            country = unquote(entry["country"]).strip("\r\n")
            if "➾" in country:
                categories.add(country)

        categories_list = sorted(list(categories))

        for category in categories_list:
            self.cat_list.append(show_list(category, self.url, True))

        self._update_ui()

    def show_countries_view(self):
        """Show only main countries"""
        self.current_view = "countries"
        self.cat_list = []

        if not hasattr(self, 'all_data'):
            return

        countries = set()
        for entry in self.all_data:
            country = unquote(entry["country"]).strip("\r\n")
            if "➾" not in country:
                countries.add(country)

        countries_list = sorted(list(countries))

        for country in countries_list:
            self.cat_list.append(show_list(country, self.url))

        self._update_ui()

    def ok(self):
        try:
            current_item = self['menulist'].getCurrent()
            if not current_item or len(current_item) == 0:
                print("DEBUG: No current item selected or item is empty")
                return

            name = current_item[0][0]  # Country name (e.g., "Italy")

            print("[MainVavoo] Selected: " + str(name))

            # Pass ONLY the country name to the vavoo class
            # The vavoo class will handle the proxy internally
            try:
                self.session.open(vavoo, name, None)  # URL is no longer needed
            except Exception as error:
                print("Error opening vavoo screen: " + str(error))
                trace_error()

        except Exception as error:
            print("Error in ok method: " + str(error))
            trace_error()

    def msgdeleteBouquets(self):
        message_parts = []
        message_parts.append(_("Remove ALL Vavoo bouquets?"))
        message_parts.append(_("This will remove:"))
        message_parts.append(_("- Country bouquets"))
        message_parts.append(_("- Category bouquets"))
        message_parts.append(_("- Container bouquets"))
        message = "\n".join(message_parts)

        self.session.openWithCallback(
            self.deleteBouquets,
            MessageBox,
            message,
            MessageBox.TYPE_YESNO,
            timeout=10,
            default=False)

    def deleteBouquets(self, result):
        """Delete all Vavoo bouquets"""
        if result:
            try:
                removed_count = remove_bouquets_by_name()

                # Remove Favorite.txt
                favorite_path = join(PLUGIN_PATH, 'Favorite.txt')
                if isfile(favorite_path):
                    remove(favorite_path)
                    print("✓ Removed Favorite.txt")

                # Build message safely for translation
                message = _("Vavoo bouquets removed successfully!")
                message += ""
                message += _("(%s files deleted)") % removed_count

                self.session.open(
                    MessageBox,
                    message,
                    MessageBox.TYPE_INFO,
                    timeout=5
                )
                self._reload_services_after_delay()

            except Exception as error:
                print("Error in deleteBouquets: " + str(error))

    def goConfig(self):
        self.session.open(vavoo_config)

    def info(self):
        """Display plugin information"""
        message_parts = []
        message_parts.append("=" * 40)
        message_parts.append(_("Vavoo Stream Live Plugin"))
        message_parts.append("=" * 40)
        message_parts.append("")

        message_parts.append(_("Version: ") + str(__version__))
        message_parts.append(_("Author: ") + str(__author__))
        message_parts.append(_("License: ") + str(__license__))
        message_parts.append("")

        message_parts.append(_("Technical Features:"))
        message_parts.append(_("- HTTP Live Streaming"))
        message_parts.append(_("- TS/M3U8 formats"))
        message_parts.append(_("- Service references: 4097, 5001, 5002"))
        message_parts.append(_("- Automatic bouquet generation"))
        message_parts.append(_("- Integrated proxy system"))
        message_parts.append(_("- Auto token refresh every 9 minutes"))
        message_parts.append("")

        message_parts.append(_("Credits:"))
        message_parts.append(_("- Graphics: @oktus"))
        message_parts.append(
            _("- Technical support: Qu4k3, @KiddaC, @giorbak"))
        message_parts.append(
            _("- Community: Linuxsat-support.com, Corvoboys Forum"))
        message_parts.append("")

        message_parts.append(_("Important Notes:"))
        message_parts.append(_("- Free content only"))
        message_parts.append(_("- Streams from public sources"))
        message_parts.append(_("- No direct server hosting"))
        message_parts.append(_("- For personal use only"))
        message_parts.append("")

        message_parts.append(_("License: CC BY-NC-SA 4.0"))
        message_parts.append(_("- Redistribution must maintain attribution"))
        message_parts.append(_("- Commercial use is strictly prohibited"))

        info_text = "\n".join(message_parts)

        aboutbox = self.session.open(
            MessageBox,
            info_text,
            MessageBox.TYPE_INFO
        )
        aboutbox.setTitle(_('Vavoo Stream Live - Information'))

    def chUp(self):
        """Handle page up and update name"""
        try:
            if self.cat_list:
                self['menulist'].pageUp()
                print("DEBUG chUp: " + self['name'].getText())
        except Exception as e:
            print("Error in chUp:", e)

    def chDown(self):
        """Handle page down and update name"""
        try:
            if self.cat_list:
                self['menulist'].pageDown()
                print("DEBUG chDown: " + self['name'].getText())
        except Exception as e:
            print("Error in chDown:", e)

    def _update_ui(self):
        """Update the UI with current list"""
        try:
            if self.cat_list and len(self.cat_list) > 0:
                self["menulist"].l.setList(self.cat_list)
                self._update_selection_name()
            else:
                self["name"].setText("No items available")
                self.cat_list = []
        except Exception as error:
            print("Error updating UI:", error)
            self["name"].setText("Error")
            self.cat_list = []

    def _update_selection_name(self):
        """Update the name label with current selection"""
        try:
            current = self['menulist'].getCurrent()
            if current and len(current) > 0:
                name = current[0][0]
                self['name'].setText(to_string(name))
                print("MainVavoo _update_selection_name: " + to_string(name))
            else:
                self['name'].setText("No selection")  # Testo di fallback
        except Exception as e:
            print("Error in MainVavoo _update_selection_name:", e)
            self['name'].setText("Error")

    def update_me(self):
        remote_version = '0.0'
        remote_changelog = ''
        req = vUtils.Request(
            vUtils.b64decoder(installer_url), headers={
                'User-Agent': 'Mozilla/5.0'})
        page = vUtils.urlopen(req).read()
        if PY3:
            data = page.decode("utf-8")
        else:
            data = page.encode("utf-8")
        if data:
            lines = data.split("\n")
            for line in lines:
                if line.startswith("version"):
                    remote_version = line.split("=")
                    remote_version = line.split("'")[1]
                if line.startswith("changelog"):
                    remote_changelog = line.split("=")
                    remote_changelog = line.split("'")[1]
                    break

        if float(__version__) < float(remote_version):
            new_version = remote_version
            new_changelog = remote_changelog
            part1 = _("New version {version} is available.").format(
                version=new_version)
            part2 = _("Changelog: {changelog}").format(changelog=new_changelog)
            part3 = _("Do you want to install it now?")
            update_message = part1 + "\n\n" + part2 + "\n\n" + part3
            formatted_message = update_message
            self.session.openWithCallback(
                self.install_update,
                MessageBox,
                formatted_message,
                MessageBox.TYPE_YESNO
            )
            formatted_message = update_message.format(
                version=new_version,
                changelog=new_changelog
            )
            self.session.openWithCallback(
                self.install_update,
                MessageBox,
                formatted_message,
                MessageBox.TYPE_YESNO
            )
        else:
            self.session.open(
                MessageBox,
                _("Congrats! You already have the latest version..."),
                MessageBox.TYPE_INFO,
                timeout=4)

    def update_dev(self):
        req = vUtils.Request(
            vUtils.b64decoder(developer_url), headers={
                'User-Agent': 'Mozilla/5.0'})
        page = vUtils.urlopen(req).read()
        data = loads(page)
        remote_date = data['pushed_at']
        strp_remote_date = datetime.strptime(remote_date, '%Y-%m-%dT%H:%M:%SZ')
        remote_date = strp_remote_date.strftime('%Y-%m-%d')
        self.session.openWithCallback(
            self.install_update,
            MessageBox,
            _("Do you want to install update ( %s ) now?") %
            (remote_date),
            MessageBox.TYPE_YESNO)

    def install_update(self, answer=False):
        if answer:
            self.session.open(
                Console,
                'Upgrading...',
                cmdlist=(
                    'wget -q "--no-check-certificate" ' +
                    vUtils.b64decoder(installer_url) +
                    ' -O - | /bin/sh'),
                finishedCallback=self.myCallback,
                closeOnSuccess=False)
        else:
            self.session.open(
                MessageBox,
                _("Update Aborted!"),
                MessageBox.TYPE_INFO,
                timeout=3)

    def myCallback(self, result=None):
        print('result:', result)
        return


class vavoo(Screen):
    def __init__(self, session, name, url, option_value=None):
        self.session = session
        global _session
        _session = session

        Screen.__init__(self, session)
        self._load_skin()
        self._initialize_labels()
        self._initialize_actions()
        self["menulist"].onSelectionChanged.append(self._update_selection_name)
        self.currentList = 'menulist'

        # Store country name properly
        self.country_name = name
        self.name = name
        self.url = url
        self.option_value = option_value

        self.current_view = "countries"  # default
        try:
            for screen in self.session.dialog_stack:
                if hasattr(screen, 'current_view'):
                    self.current_view = screen.current_view
                    print(
                        "DEBUG: Got current_view from main screen: " +
                        self.current_view)
                    break
        except Exception as e:
            print("DEBUG: Error getting current_view: " + str(e))

        # Do NOT try to initialize proxy here - it should already be running
        # Just verify it's ready
        self._verify_proxy_ready()

        self._initialize_timer()

    def _verify_proxy_ready(self):
        """Verify that the proxy is ready without attempting to start it"""
        try:
            if not is_proxy_ready(timeout=2):
                print(
                    "[vavoo] Warning: Proxy not ready for %s" %
                    self.country_name)
                # Do not start the proxy here – let the cat() method handle the
                # fallback
        except Exception as e:
            print("[vavoo] Error checking proxy: %s" % str(e))

    def _load_skin(self):
        """Load the skin file."""
        skin = join(skin_path, 'defaultListScreen.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

    def _initialize_labels(self):
        """Initialize the labels on the screen."""
        self.menulist = []
        global search_ok
        search_ok = False
        self['menulist'] = m2list([])
        self['red'] = Label(_('Back'))
        self['green'] = Label(_('Export') + ' Fav')
        self['yellow'] = Label(_('Search'))
        self["blue"] = Label(_('Reload Bouqet'))
        self['name'] = Label('Loading ...')
        self['version'] = Label()
        self['proxy_status'] = Label('...')

    def _initialize_actions(self):
        """Initialize the actions for buttons."""
        self["actions"] = ActionMap(
            [
                'MenuActions',
                'OkCancelActions',
                'ButtonSetupActions',
                'InfobarEPGActions',
                'EPGSelectActions'
            ],
            {
                "prevBouquet": self.chDown,
                "nextBouquet": self.chUp,
                "ok": self.ok,
                "green": self.message1,
                "yellow": self.search_vavoo,
                "blue": self._reload_services_after_delay,
                "cancel": self.backhome,
                "menu": self.goConfig,
                # "info": self.info,
                "red": self.backhome
            },
            -1
        )

    def _initialize_timer(self):
        """Initialize the timer with proper timeout handling"""
        self.timer = eTimer()
        try:
            self.timer.callback.append(self.cat)
        except:
            self.timer.timeout.connect(self.cat)
        self.timer.start(500, True)

    def _initialize_proxy_for_country(self):
        """Initialize the proxy for the selected country"""
        try:
            print("[vavoo] Initializing proxy for country: " +
                  str(self.country_name))

            # URL to initialize the proxy for the specific country
            init_url = "http://127.0.0.1:4323/initialize_country?country=" + \
                str(self.country_name)

            content = getUrl(init_url, timeout=10)
            if content:
                if PY3:
                    content = ensure_str(content)

                result = loads(content)
                if result.get("status") == "ok":
                    print("[vavoo] Proxy initialized for " +
                          str(self.country_name))
                    self.proxy_initialized = True
                    return True

        except Exception as e:
            print("[vavoo] Proxy initialization error: " + str(e))

        return False

    def debug_proxy_state(self):
        """Debug function to check proxy state"""
        try:
            print("=" * 60)
            print(
                "[DEBUG] Checking proxy state for country: " +
                self.country_name)

            # 1. Check status
            status_url = "http://127.0.0.1:4323/status"
            status = getUrl(status_url, timeout=3)
            if status:
                print("[DEBUG] Proxy Status: " + status[:200])

            # 2. Check countries list
            countries_url = "http://127.0.0.1:4323/countries"
            countries = getUrl(countries_url, timeout=3)
            if countries:
                print("[DEBUG] Available countries: " + countries[:200])

            # 3. Try to get channels
            test_url = "http://127.0.0.1:4323/channels?country=Italy"
            channels = getUrl(test_url, timeout=5)
            print("[DEBUG] Channels response length: " +
                  str(len(channels) if channels else 0))
            if channels and len(channels) < 500:
                print("[DEBUG] Channels data: " + channels)

            print("=" * 60)
        except Exception as e:
            print("[DEBUG] Error checking proxy: " + str(e))

    def cat(self):
        """Load channels for selected country with proxy verification"""
        print("[DEBUG] vavoo.cat() called for country: " + str(self.country_name))

        try:
            # 1. CHECK PROXY STATUS
            proxy_status = self._check_and_ensure_proxy_ready()
            if not proxy_status["ready"]:
                self._show_proxy_error(proxy_status)
                return

            # 2. GET CHANNELS FROM PROXY
            country_encoded = quote(self.country_name)
            proxy_url = "http://127.0.0.1:" + \
                str(PORT) + "/channels?country=" + country_encoded
            print("[DEBUG] Fetching from proxy: " + proxy_url)

            content = getUrl(proxy_url, timeout=10)

            if not content or content.strip() == "" or content == "null":
                print("[ERROR] Proxy returned empty response for " +
                      str(self.country_name))

                # Recovery attempt
                if self._try_proxy_recovery():
                    self.cat()  # Retry
                    return

                self['name'].setText("No channels for " +
                                     str(self.country_name))
                return

            # 3. PROCESS CHANNELS
            channels_data = loads(content)
            self._build_channel_list(channels_data)

        except Exception as e:
            print("[ERROR] CRITICAL in cat(): " + str(e))
            trace_error()
            self._handle_cat_error(e)

    def _build_channel_list(self, channels_data):
        """Build channel list from proxy data"""
        self.cat_list = []

        if not isinstance(channels_data, list):
            print("[vavoo] Invalid channels data type: " +
                  str(type(channels_data)))
            return

        for channel in channels_data:
            if isinstance(channel, dict):
                channel_name = channel.get("name", "Unknown")
                channel_url = channel.get("url", "")

                self.cat_list.append(
                    show_list(channel_name, channel_url, is_channel=True)
                )

        if not self.cat_list:
            self['name'].setText(to_string("No proxy URLs built."))
            return

        self.itemlist = [
            item[0][0] + "###" + item[0][1] for item in self.cat_list
        ]
        self.update_menu()
        print("[DEBUG] List built with " + str(len(self.cat_list)) + " items.")

    def _handle_cat_error(self, error):
        """Handle cat() method errors"""
        print("[vavoo] Handling cat error: " + str(error))
        self['name'].setText(to_string("Error: " + str(error)))

        # Show message to user
        try:
            self.session.open(
                MessageBox,
                "Error loading channels: " + str(error)[:100],
                MessageBox.TYPE_ERROR,
                timeout=5
            )
        except Exception:
            pass

    def _check_and_ensure_proxy_ready(self):
        """Check proxy status and try to fix issues if needed"""
        status = {
            "ready": False,
            "message": "",
            "needs_restart": False
        }

        if not is_proxy_running():
            status["message"] = "Proxy not running"
            status["needs_restart"] = True
            return status

        try:
            proxy_response = getUrl("http://127.0.0.1:4323/status", timeout=3)
            if not proxy_response:
                status["message"] = "Cannot get proxy status"
                status["needs_restart"] = True
                return status

            proxy_data = loads(proxy_response)

            if not proxy_data.get("initialized", False):
                status["message"] = "Proxy not initialized"
                status["needs_restart"] = True
                return status

            if not proxy_data.get("addon_sig_valid", False):
                status["message"] = "Token not valid"
                status["needs_restart"] = True
                return status

            token_age = proxy_data.get("addon_sig_age", 0)
            if token_age > 540:
                print(
                    "[vavoo] Token old (" +
                    str(token_age) +
                    "s), forcing refresh...")
                try:
                    refresh_url = "http://127.0.0.1:" + \
                        str(PORT) + "/refresh_token"
                    getUrl(refresh_url, timeout=3)
                except Exception:
                    pass

            status["ready"] = True
            status["message"] = "Proxy ready"
            return status

        except Exception as e:
            status["message"] = "Error checking proxy: " + str(e)
            status["needs_restart"] = True
            return status

    def _try_proxy_recovery(self):
        """Try to recover proxy connection"""
        try:
            print("[vavoo] Attempting proxy recovery...")

            # 1. Try token refresh
            try:
                refresh_url = "http://127.0.0.1:" + \
                    str(PORT) + "/refresh_token"
                getUrl(refresh_url, timeout=3)
                print("[vavoo] Token refresh attempted")
            except Exception:
                pass

            # 2. Try proxy restart
            if not is_proxy_ready(timeout=2):
                print("[vavoo] Restarting proxy...")
                success = run_proxy_in_background()

                if success:
                    # Wait for initialization
                    for i in range(5):
                        if is_proxy_ready(timeout=2):
                            print("[vavoo] Proxy restarted successfully")
                            return True
                        time.sleep(1)

            return False

        except Exception as e:
            print("[vavoo] Recovery error: " + str(e))
            return False

    def _show_proxy_error(self, status):
        """Show proxy error message"""
        error_msg = "Proxy Error: " + status["message"]
        print("[vavoo] " + error_msg)
        self['name'].setText(error_msg)

        # Offer restart option
        if status["needs_restart"]:
            self.session.openWithCallback(
                self._restart_proxy_callback,
                MessageBox,
                "Proxy needs restart: " + status["message"] + "\nRestart now?",
                MessageBox.TYPE_YESNO
            )

    def _restart_proxy_callback(self, result):
        """Callback for proxy restart"""
        if result:
            print("[vavoo] User requested proxy restart")
            run_proxy_in_background()

            # Wait and retry
            self.session.open(MessageBox, "Proxy restarting... Please wait", MessageBox.TYPE_INFO, timeout=3)

            # Retry loading after 3 seconds
            self.timer = eTimer()
            try:
                self.timer.callback.append(self.cat)
            except Exception:
                self.timer.timeout.connect(self.cat)
            self.timer.start(3000, True)

    def start_vavoo_proxy(self):
        """Start the proxy only if it is not already running"""
        try:
            if is_proxy_running():
                print("[MainVavoo] Proxy already running")
                return True

            print("[MainVavoo] Starting proxy...")
            success = run_proxy_in_background()

            if success:
                print("[MainVavoo] Proxy started")
                return True
            else:
                print("[Vavoo] Proxy start error")
                return False

        except Exception as e:
            print("[MainVavoo] Error: {0}".format(e))
            return False

    def _matches_selection(self, country_field, selected_name):
        """
        Check if a channel matches the selection
        country_field: country field from JSON (ex: "France" or "France ➾ Sports")
        selected_name: what user selected (ex: "France" or "France ➾ Sports")
        """
        country_field = unquote(country_field).strip("\r\n")
        selected_name = selected_name.strip()

        # If user selected main country (without ➾)
        if "➾" not in selected_name:
            # Show ALL channels from that country, including subcategories
            # Match exact country OR country with any subcategory
            return country_field == selected_name or country_field.startswith(
                selected_name + " ➾")
        else:
            # User selected specific category - exact match only
            return country_field == selected_name

    def _reload_services_after_delay(self):
        eDVBDB.getInstance().reloadBouquets()
        eDVBDB.getInstance().reloadServicelist()
        try:
            self.session.open(
                MessageBox,
                "Bouquets reloaded successfully.",
                MessageBox.TYPE_INFO,
                timeout=5
            )
        except Exception as e:
            print("[AutoStartTimer] Failed to show MessageBox: " + str(e))

    def ok(self):
        try:
            i = self['menulist'].getSelectedIndex()
            self.currentindex = i
            selection = self['menulist'].l.getCurrentSelection()
            if selection is not None:
                item = self.cat_list[i][0]
                name = item[0]
                url = item[1]
            else:
                print("No selection available")
                return

            self.play_that_shit(
                url,
                name,
                self.currentindex,
                item,
                self.cat_list)
        except Exception as error:
            print('error as:', error)
            trace_error()

    def play_that_shit(self, url, name, index, item, cat_list):
        """Start channel playback"""
        try:
            print("[vavoo] ======== START PLAYBACK DEBUG ========")
            print("[vavoo] Channel: " + str(name))
            print("[vavoo] URL: " + str(url))
            print("[vavoo] URL Type: " + str(type(url)))
            """
            # DEBUG: controlla se è un URL del proxy
            if isinstance(url, str):
                if "127.0.0.1:4323" in url or "/resolve?id=" in url:
                    print("[vavoo] ✓ This is a PROXY URL!")
                    print("[vavoo] Should use playDirectStream()")
                else:
                    print("[vavoo] ✗ This is NOT a proxy URL")
                    print("[vavoo] It's: " + url[:80])
            """
            self.session.open(Playstream2, name, url, index, item, cat_list)
        except Exception as error:
            print("Error in play_that_shit: {}".format(error))
            trace_error()
            self.session.open(
                MessageBox,
                _("Error starting channel"),
                MessageBox.TYPE_ERROR,
                timeout=3
            )

    def message1(self, answer=None):
        if answer is None:
            # Show confirmation message before export
            self.session.openWithCallback(
                self.message1,
                MessageBox,
                _("Do you want to export this bouquet?") + "\n" + self.name,
                MessageBox.TYPE_YESNO
            )
        elif answer is True:
            self.message2(self.name, self.url, True)
        elif answer is False:
            print("Export cancelled by user")

    def message2(self, name, url, response):
        """Export bouquet for selected country/category"""
        try:
            # Determine export_type
            separators = ["➾", "⟾", "->", "→"]
            has_separator = any(sep in name for sep in separators)

            if has_separator:
                # Category - hierarchical export
                export_type = "hierarchical"
                print("[Export] Category '%s' -> hierarchical" % name)
            else:
                # Country - flat export
                export_type = "flat"
                print("[Export] Country '%s' -> flat" % name)

            # Check proxy
            if not is_proxy_ready():
                print("[Export] Proxy not ready, attempting to start...")
                self.start_vavoo_proxy()
                time.sleep(3)

            # Export bouquet
            from .bouquet_manager import convert_bouquet
            ch = convert_bouquet(
                cfg.services.value,
                name,
                "",  # URL not needed with proxy
                export_type,
                cfg.server.value,
                cfg.list_position.value
            )

            if int(ch) > 0:
                print(
                    "[Export] Bouquet created: %s (%s channels)" %
                    (name, ch))

                # Update Favorite.txt
                from .bouquet_manager import _update_favorite_file
                _update_favorite_file(name, "", export_type)

                # Show confirmation
                message_part1 = _("Bouquet '%(name)s' created successfully!") % {
                    'name': name}
                message_part2 = _("(%(count)d channels)") % {'count': ch}
                message = message_part1 + "\n" + message_part2

                self.session.open(
                    MessageBox,
                    message,
                    MessageBox.TYPE_INFO,
                    timeout=3
                )
                # Reload services
                self._reload_services_after_delay()
            else:
                print("[Export] No channels for %s" % name)
                self.session.open(
                    MessageBox,
                    _("No channels found for '%(name)s'") % {'name': name},
                    MessageBox.TYPE_WARNING,
                    timeout=3
                )

        except Exception as e:
            print("[Export] Error: %s" % str(e))
            trace_error()
            self.session.open(
                MessageBox,
                _("Bouquet creation error: %s") % str(e),
                MessageBox.TYPE_ERROR,
                timeout=3
            )

    def search_vavoo(self):
        self.saved_itemlist = self.itemlist
        self.session.openWithCallback(
            self.onSearchResult, VavooSearch, self, self.itemlist)

    def onSearchResult(self, selected_item=None):
        """Callback with the channel selected by the search"""
        if selected_item:
            name, url = selected_item
            self.session.open(
                Playstream2,
                name,
                url,
                0,
                [name, url],
                [[[name, url]]]
            )

    def filterM3u(self, result):
        global search_ok
        if result:
            try:
                self.cat_list = []
                search = result
                for item in self.itemlist:
                    name = item.split('###')[0]
                    url = item.split('###')[1]
                    if search.lower() in str(name).lower():
                        search_ok = True
                        namex = name
                        urlx = url.replace('%0a', '').replace('%0A', '')
                        self.cat_list.append(show_list(namex, urlx))
                if len(self.cat_list) < 1:
                    _session.open(
                        MessageBox,
                        _('No channels found in search!!!'),
                        MessageBox.TYPE_INFO,
                        timeout=5)
                    return
                else:
                    self['menulist'].l.setList(self.cat_list)
                    # self['menulist'].moveToIndex(0)
                    txtsream = self['menulist'].getCurrent()[0][0]
                    self['name'].setText(str(txtsream))
            except Exception as error:
                print(error)
                trace_error()
                self['name'].setText('Error')
                search_ok = False

    def goConfig(self):
        self.session.open(vavoo_config)

    def chUp(self):
        """Handle page up and update name"""
        try:
            if self.cat_list:
                self['menulist'].pageUp()
                print("vavoo chUp: " + str(self['name'].getText()))
        except Exception as e:
            print("Error in vavoo chUp:", e)

    def chDown(self):
        """Handle page down and update name"""
        try:
            if self.cat_list:
                self['menulist'].pageDown()
                print("vavoo chDown: " + str(self['name'].getText()))
        except Exception as e:
            print("Error in vavoo chDown:", e)

    def _update_selection_name(self):
        """Update the name label with current selection"""
        try:
            current = self['menulist'].getCurrent()
            if current and len(current) > 0:
                name = current[0][0]
                self['name'].setText(to_string(name))
                print("vavoo _update_selection_name: " + to_string(name))
        except Exception as e:
            print("Error in vavoo _update_selection_name:", e)
            self['name'].setText("")

    def update_menu(self):
        try:
            if self.cat_list:
                self['menulist'].l.setList(self.cat_list)
                # self['menulist'].moveToIndex(0)
            else:
                self['name'].setText("No channels found")
        except Exception as error:
            print("Error updating menu:", error)
            self['name'].setText("Error")

    def close(self, *args, **kwargs):
        try:
            self.timer.stop()
            try:
                if hasattr(self.timer, 'callback'):
                    self.timer.callback.remove(self.cat)
            except AttributeError:
                pass
            try:
                if hasattr(self.timer, 'timeout'):
                    self.timer.timeout.disconnect(self.cat)
            except AttributeError:
                pass
        except Exception as e:
            print("Error stopping timer: " + str(e))
        return Screen.close(self, *args, **kwargs)

    def backhome(self):
        if search_ok:
            self.cat()
        self.close()


# --- Live search screen ---
class VavooSearch(Screen):
    def __init__(self, session, parentScreen, itemlist):
        self.session = session
        self.parentScreen = parentScreen
        self.itemlist = itemlist
        self.filteredList = []
        self.selectedIndex = 0
        self.search_text = ""
        self.current_input = ""
        if isfile('/var/lib/dpkg/status'):
            if screen_width == 2560:
                self.skin = """
                    <screen name="VavooSearch" position="center,center" size="1200,900" title="Vavoo Search">
                        <widget name="search_label" position="20,20" size="1160,60" font="Regular;40" halign="left" valign="center" />
                        <widget name="search_text" position="20,100" size="1160,80" font="Regular;40" halign="left" valign="center" backgroundColor="#00008B" />
                        <widget name="input_info" position="20,190" size="1160,40" font="Regular;30" halign="center" />
                        <widget name="channel_list" position="20,250" size="1160,510" itemHeight="60" scrollbarMode="showOnDemand" />
                        <widget name="status" position="20,795" size="1160,40" font="Regular;30" halign="center" />
                        <widget name="key_red" position="20,845" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="red" foregroundColor="white" />
                        <widget name="key_green" position="210,845" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="green" foregroundColor="white" />
                        <widget name="key_yellow" position="400,845" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="yellow" foregroundColor="black" />
                        <widget name="key_blue" position="590,844" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="blue" foregroundColor="white" />
                    </screen>
                """
            elif screen_width == 1920:
                self.skin = """
                    <screen name="VavooSearch" position="center,center" size="1000,700" title="Vavoo Search">
                        <widget name="search_label" position="20,20" size="960,40" font="Regular;32" halign="left" valign="center" />
                        <widget name="search_text" position="20,70" size="960,60" font="Regular;32" halign="left" valign="center" backgroundColor="#00008B" />
                        <widget name="input_info" position="20,140" size="960,30" font="Regular;24" halign="center" />
                        <widget name="channel_list" position="20,180" size="960,380" itemHeight="50" scrollbarMode="showOnDemand" />
                        <widget name="status" position="20,615" size="960,30" font="Regular;24" halign="center" />
                        <widget name="key_red" position="20,655" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="red" foregroundColor="white" />
                        <widget name="key_green" position="210,655" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="green" foregroundColor="white" />
                        <widget name="key_yellow" position="400,655" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="yellow" foregroundColor="black" />
                        <widget name="key_blue" position="590,654" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="blue" foregroundColor="white" />
                    </screen>
                """
            else:
                self.skin = """
                    <screen name="VavooSearch" position="center,center" size="800,600" title="Vavoo Search">
                        <widget name="search_label" position="20,20" size="760,30" font="Regular;24" halign="left" valign="center" />
                        <widget name="search_text" position="20,60" size="760,40" font="Regular;24" halign="left" valign="center" backgroundColor="#000080" />
                        <widget name="input_info" position="20,475" size="760,25" font="Regular;18" halign="center" />
                        <widget name="channel_list" position="20,120" size="760,349" itemHeight="50" scrollbarMode="showOnDemand" />
                        <widget name="status" position="20,500" size="760,30" font="Regular;20" halign="center" />
                        <widget name="key_red" position="20,540" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="red" foregroundColor="white" />
                        <widget name="key_green" position="210,540" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="green" foregroundColor="white" />
                        <widget name="key_yellow" position="400,540" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="yellow" foregroundColor="black" />
                        <widget name="key_blue" position="590,539" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="blue" foregroundColor="white" />
                    </screen>
                    """

        else:
            if screen_width == 2560:
                self.skin = """
                    <screen name="VavooSearch" position="center,center" size="1200,900" title="Vavoo Search">
                        <widget name="search_label" position="20,20" size="1160,60" font="Regular;40" halign="left" valign="center" />
                        <widget name="search_text" position="20,100" size="1160,80" font="Regular;40" halign="left" valign="center" backgroundColor="#00008B" />
                        <widget name="input_info" position="20,190" size="1160,40" font="Regular;30" halign="center" />
                        <widget name="channel_list" position="20,250" size="1160,510" font="Regular;36" itemHeight="60" scrollbarMode="showOnDemand" />
                        <widget name="status" position="20,795" size="1160,40" font="Regular;30" halign="center" />
                        <widget name="key_red" position="20,845" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="red" foregroundColor="white" />
                        <widget name="key_green" position="210,845" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="green" foregroundColor="white" />
                        <widget name="key_yellow" position="400,845" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="yellow" foregroundColor="black" />
                        <widget name="key_blue" position="590,844" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="blue" foregroundColor="white" />
                    </screen>
                """
            elif screen_width == 1920:
                self.skin = """
                    <screen name="VavooSearch" position="center,center" size="1000,700" title="Vavoo Search">
                        <widget name="search_label" position="20,20" size="960,40" font="Regular;32" halign="left" valign="center" />
                        <widget name="search_text" position="20,70" size="960,60" font="Regular;32" halign="left" valign="center" backgroundColor="#00008B" />
                        <widget name="input_info" position="20,140" size="960,30" font="Regular;24" halign="center" />
                        <widget name="channel_list" position="20,180" size="960,380" font="Regular;28" itemHeight="50" scrollbarMode="showOnDemand" />
                        <widget name="status" position="20,615" size="960,30" font="Regular;24" halign="center" />
                        <widget name="key_red" position="20,655" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="red" foregroundColor="white" />
                        <widget name="key_green" position="210,655" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="green" foregroundColor="white" />
                        <widget name="key_yellow" position="400,655" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="yellow" foregroundColor="black" />
                        <widget name="key_blue" position="590,654" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="blue" foregroundColor="white" />
                    </screen>
                """
            else:
                self.skin = """
                    <screen name="VavooSearch" position="center,center" size="800,600" title="Vavoo Search">
                        <widget name="search_label" position="20,20" size="760,30" font="Regular;24" halign="left" valign="center" />
                        <widget name="search_text" position="20,60" size="760,40" font="Regular;24" halign="left" valign="center" backgroundColor="#000080" />
                        <widget name="input_info" position="20,475" size="760,25" font="Regular;18" halign="center" />
                        <widget name="channel_list" position="20,120" size="760,349" font="Regular;22" itemHeight="50" scrollbarMode="showOnDemand" />
                        <widget name="status" position="20,500" size="760,30" font="Regular;20" halign="center" />
                        <widget name="key_red" position="20,540" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="red" foregroundColor="white" />
                        <widget name="key_green" position="210,540" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="green" foregroundColor="white" />
                        <widget name="key_yellow" position="400,540" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="yellow" foregroundColor="black" />
                        <widget name="key_blue" position="590,539" size="180,30" font="Regular;20" halign="center" valign="center" backgroundColor="blue" foregroundColor="white" />
                    </screen>
                    """

        Screen.__init__(self, session)
        self["search_label"] = Label(_("Search Channels:"))
        self["search_text"] = Label("")
        self["input_info"] = Label(
            _("Press TEXT button to type, BACKSPACE to delete"))
        self["channel_list"] = m2list([])
        self["status"] = Label(_("Enter text to search..."))
        self["key_red"] = Label(_("Clear All"))
        self["key_green"] = Label(_("Keyboard"))
        self["key_yellow"] = Label(_("Backspace"))
        self["key_blue"] = Label(_("Space"))
        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "ColorActions", "NumberActions"],
            {
                "ok": self.onOk,
                "cancel": self.onCancel,
                "up": self.moveUp,
                "down": self.moveDown,
                "left": self.moveLeft,
                "right": self.moveRight,
                "red": self.clearSearch,
                "green": self.openKeyboard,
                "yellow": self.deleteChar,
                "blue": self.addSpace,
                "1": lambda: self.keyNumber(1),
                "2": lambda: self.keyNumber(2),
                "3": lambda: self.keyNumber(3),
                "4": lambda: self.keyNumber(4),
                "5": lambda: self.keyNumber(5),
                "6": lambda: self.keyNumber(6),
                "7": lambda: self.keyNumber(7),
                "8": lambda: self.keyNumber(8),
                "9": lambda: self.keyNumber(9),
                "0": lambda: self.keyNumber(0),
            }, -1)

        self.searchTimer = eTimer()
        try:
            self.searchTimer.timeout.connect(self.updateFilteredList)
        except:
            self.searchTimer.callback.append(self.updateFilteredList)

        self.numericalInput = NumericalTextInput(
            nextFunc=self.searchWithString)
        self.input_active = False
        self.upper_case = False
        self.last_key = None
        self.search_text = ""
        self.last_key_time = 0
        self.key_timer = eTimer()
        try:
            self.key_timer.timeout.connect(self.finishKeyInput)
        except:
            self.key_timer.callback.append(self.finishKeyInput)

        self.updateFilteredList()

    def keyNumber(self, number):
        key_chars = {
            2: "abc2", 3: "def3", 4: "ghi4", 5: "jkl5", 6: "mno6",
            7: "pqrs7", 8: "tuv8", 9: "wxyz9", 0: " 0", 1: "1"
        }
        if number in key_chars:
            chars = key_chars[number]
            current_time = time.time()
            if hasattr(
                    self,
                    'last_key') and self.last_key == number and current_time - self.last_key_time < 1.0:
                if self.search_text and self.search_text[-1] in chars:
                    current_index = chars.index(self.search_text[-1])
                    next_index = (current_index + 1) % len(chars)
                    self.search_text = self.search_text[:-
                                                        1] + chars[next_index]
                else:
                    self.search_text += chars[0]
            else:
                self.search_text += chars[0]

            self["search_text"].setText(self.search_text)
            self.updateFilteredList()

            self.last_key = number
            self.last_key_time = current_time

    def searchWithString(self):
        """Callback called by NumericalTextInput - nothing to do"""
        pass

    def deleteChar(self):
        """Delete the last character"""
        if self.search_text:
            self.search_text = self.search_text[:-1]
            self["search_text"].setText(self.search_text)
            self.numericalInput.nextKey()  # Reset NumericalTextInput
            self.updateFilteredList()

    def clearSearch(self):
        """Clear the entire search"""
        self.search_text = ""
        self["search_text"].setText("")
        self.numericalInput.nextKey()
        self.updateFilteredList()

    def addSpace(self):
        """Add a space"""
        self.search_text += " "
        self["search_text"].setText(self.search_text)
        self.updateFilteredList()

    def finishKeyInput(self):
        """Reset key state after inactivity"""
        self.last_key = None

    def openKeyboard(self):
        self.session.openWithCallback(
            self.onKeyboardClosed,
            VirtualKeyBoard,
            title=_("Search..."),
            text=self.search_text)

    def onKeyboardClosed(self, result):
        if result is not None:
            self.search_text = result
            self["search_text"].setText(self.search_text)
            self.updateFilteredList()

    def onSearchResult(self, selected_item=None):
        """Callback with the channel selected from the search"""
        if selected_item:
            name, url = selected_item
            self.session.open(
                Playstream2,
                name,
                url,
                0,
                [name, url],
                [[[name, url]]]
            )
        else:
            # Return to the channel list without doing anything
            print("[Search] Search cancelled, returning to channel list")

    def toggleCase(self):
        """Toggle between uppercase and lowercase"""
        self.upper_case = not self.upper_case
        case_text = _("UPPERCASE") if self.upper_case else _("lowercase")
        self["status"].setText(_("Case: {}").format(case_text))

    def updateStatusText(self):
        """Update status text"""
        if self.search_text:
            # Separa in parti senza virgolette
            part1 = _("Search:")
            part2 = _('Found: {} channels').format(len(self.filteredList))
            message = f'{part1} "{self.search_text}" - {part2}'
            self["status"].setText(message)
        else:
            self["status"].setText(
                _("Showing all channels: {}").format(len(self.filteredList)))

    def updateFilteredList(self):
        text = self.search_text.lower().strip()

        if not text:
            self.filteredList = self.itemlist[:]
            self["status"].setText(
                _("Showing all channels: {}").format(len(self.filteredList)))
        else:
            self.filteredList = []
            for item in self.itemlist:
                try:
                    name = item.split('###')[0].lower()
                    if text in name:
                        self.filteredList.append(item)
                except:
                    continue

            if self.filteredList:
                # Separa in parti senza virgolette
                part1 = _("Search:")
                part2 = _("Found: {} channels").format(len(self.filteredList))
                message = f'{part1} "{self.search_text}" - {part2}'
                self["status"].setText(message)
            else:
                # Separa in parti senza virgolette
                part1 = _("Search:")
                part2 = _("No channels found")
                message = f'{part1} "{self.search_text}" - {part2}'
                self["status"].setText(message)

        self.updateChannelList()

        if self.filteredList:
            self.selectedIndex = 0
            self["channel_list"].moveToIndex(self.selectedIndex)
        else:
            self.selectedIndex = -1

    def updateChannelList(self):
        display_list = []
        for item in self.filteredList:
            try:
                name = item.split('###')[0]
                url = item.split('###')[1].replace(
                    '%0a', '').replace(
                    '%0A', '').strip("\r\n")
                display_list.append(show_list(name, url))
            except:
                continue
        self["channel_list"].l.setList(display_list)

    def moveUp(self):
        if self.filteredList:
            self.selectedIndex = max(0, self.selectedIndex - 1)
            self["channel_list"].moveToIndex(self.selectedIndex)

    def moveDown(self):
        if self.filteredList:
            self.selectedIndex = min(
                len(self.filteredList) - 1, self.selectedIndex + 1)
            self["channel_list"].moveToIndex(self.selectedIndex)

    def moveLeft(self):
        self.moveUp()

    def moveRight(self):
        self.moveDown()

    def onOk(self):
        if self.filteredList and 0 <= self.selectedIndex < len(
                self.filteredList):
            channel_item = self.filteredList[self.selectedIndex]
            name = channel_item.split('###')[0]
            url = channel_item.split('###')[1].replace(
                '%0a', '').replace('%0A', '').strip("\r\n")
            self.close((name, url))
        else:
            self.close(None)

    def onPlayerClosed(self, result=None):
        """Callback called when the player is closed"""
        print("DEBUG: Player closed, returning to Vavoo main screen")
        self.close()

    def onCancel(self):
        """Return to the Vavoo screen without opening the player"""
        print("DEBUG: Search cancelled, returning to Vavoo main screen")
        self.close()

    def close(self, *args, **kwargs):
        """Cleanup when the screen is closed"""
        try:
            # Stop timers
            if hasattr(self, 'searchTimer'):
                self.searchTimer.stop()
                try:
                    if hasattr(self.searchTimer, 'callback'):
                        self.searchTimer.callback.remove(
                            self.updateFilteredList)
                except:
                    pass

            if hasattr(self, 'key_timer'):
                self.key_timer.stop()

            # Reset input
            if hasattr(self, 'numericalInput'):
                self.numericalInput.nextKey()
        except Exception as e:
            print("[VavooSearch] Error in close: {0}".format(e))

        return Screen.close(self, *args, **kwargs)


class TvInfoBarShowHide():
    """ InfoBar show/hide control, accepts toggleShow and hide actions, might start
    fancy animations. """
    STATE_HIDDEN = 0
    STATE_HIDING = 1
    STATE_SHOWING = 2
    STATE_SHOWN = 3
    FLAG_CENTER_DVB_SUBS = 2048
    skipToggleShow = False

    def __init__(self):
        self["ShowHideActions"] = ActionMap(
            ["InfobarShowHideActions"],
            {
                "toggleShow": self.OkPressed,
                "hide": self.hide
            },
            0
        )
        self.__event_tracker = ServiceEventTracker(
            screen=self, eventmap={
                iPlayableService.evStart: self.serviceStarted})
        self.__state = self.STATE_SHOWN
        self.__locked = 0
        self.helpOverlay = Label("")
        self.helpOverlay.skinAttributes = [
            ("position", "0,0"),
            ("size", "1280,50"),
            ("font", "Regular;28"),
            ("halign", "center"),
            ("valign", "center"),
            ("foregroundColor", "#FFFFFF"),
            ("backgroundColor", "#666666"),
            ("transparent", "0"),
            ("zPosition", "100")
        ]

        self["helpOverlay"] = self.helpOverlay
        self["helpOverlay"].hide()
        self.hideTimer = eTimer()
        try:
            self.hideTimer.timeout.connect(self.doTimerHide)
        except:
            self.hideTimer.callback.append(self.doTimerHide)
        self.hideTimer.start(5000, True)
        self.onShow.append(self.__onShow)
        self.onHide.append(self.__onHide)

    def show_help_overlay(self):
        help_text = (
            "OK = Info | CH-/CH+ = Prev/Next | PLAY/PAUSE = Toggle | STOP = Stop | EXIT = Exit | by Lululla"
        )
        self["helpOverlay"].setText(help_text)
        self["helpOverlay"].show()

        if not hasattr(self, 'help_timer'):
            self.help_timer = eTimer()
            try:
                self.help_timer.timeout.connect(self.hide_help_overlay)
            except:
                self.help_timer.callback.append(self.hide_help_overlay)

        self.help_timer.start(5000, True)

    def hide_help_overlay(self):
        if self["helpOverlay"].visible:
            self["helpOverlay"].hide()

    def OkPressed(self):
        if self.__state == self.STATE_SHOWN:
            if self["helpOverlay"].visible:
                self.help_timer.stop()
                self.hide_help_overlay()
            else:
                self.show_help_overlay()

        self.toggleShow()

    def __onShow(self):
        self.__state = self.STATE_SHOWN
        self.startHideTimer()

    def __onHide(self):
        self.__state = self.STATE_HIDDEN

    def doShow(self):
        self.hideTimer.stop()
        self.show()
        self.startHideTimer()

    def doHide(self):
        self.hideTimer.stop()
        self.hide()
        if self["helpOverlay"].visible:
            self.help_timer.stop()
            self.hide_help_overlay()
        self.startHideTimer()

    def serviceStarted(self):
        if self.execing and config.usage.show_infobar_on_zap.value:
            self.doShow()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            self.hideTimer.stop()
            self.hideTimer.start(3000, True)
        elif hasattr(self, "pvrStateDialog"):
            self.hideTimer.stop()
        self.skipToggleShow = False

    def doTimerHide(self):
        self.hideTimer.stop()
        if self.__state == self.STATE_SHOWN:
            self.hide()
            if self["helpOverlay"].visible:
                self.help_timer.stop()
                self.hide_help_overlay()

    def toggleShow(self):
        if not self.skipToggleShow:
            if self.__state == self.STATE_HIDDEN:
                self.doShow()
                self.show_help_overlay()
            else:
                self.doHide()
                if self["helpOverlay"].visible:
                    self.help_timer.stop()
                    self.hide_help_overlay()
        else:
            self.skipToggleShow = False

    def lockShow(self):
        try:
            self.__locked += 1
        except:
            self.__locked = 0
        if self.execing:
            self.show()
            self.hideTimer.stop()
            self.skipToggleShow = False

    def unlockShow(self):
        try:
            self.__locked -= 1
        except:
            self.__locked = 0
        if self.__locked < 0:
            self.__locked = 0
        if self.execing:
            self.startHideTimer()


class Playstream2(
        InfoBarBase,
        InfoBarMenu,
        InfoBarSeek,
        InfoBarAudioSelection,
        InfoBarSubtitleSupport,
        InfoBarNotifications,
        TvInfoBarShowHide,
        Screen):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True
    screen_timeout = 5000

    def __init__(self, session, name, url, index, item, cat_list):
        Screen.__init__(self, session)
        self.session = session
        self.skinName = 'MoviePlayer'

        self.stream_running = False
        self.is_streaming = False
        self.currentindex = index
        self.item = item
        self.itemscount = len(cat_list)
        self.list = cat_list
        self.name = name
        self.url = url.replace('%0a', '').replace('%0A', '')
        self.state = self.STATE_PLAYING
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()

        for x in (
            InfoBarBase,
            InfoBarMenu,
            InfoBarSeek,
            InfoBarAudioSelection,
            InfoBarSubtitleSupport,
            InfoBarNotifications,
            TvInfoBarShowHide
        ):
            x.__init__(self)

        self['actions'] = ActionMap(
            [
                'MoviePlayerActions',
                'MovieSelectionActions',
                'MediaPlayerActions',
                'EPGSelectActions',
                'OkCancelActions',
                'InfobarShowHideActions',
                'InfobarActions',
                'DirectionActions',
                'InfobarSeekActions'
            ],
            {
                "stop": self.leavePlayer,
                "cancel": self.cancel,
                "channelDown": self.previousitem,
                "channelUp": self.nextitem,
                "down": self.previousitem,
                "up": self.nextitem,
                "back": self.cancel
            },
            -1
        )

        self.__event_tracker = ServiceEventTracker(
            screen=self,
            eventmap={
                iPlayableService.evEOF: self.__evEOF,
                # iPlayableService.evStart: self.__serviceStarted,
                # iPlayableService.evStopped: self.__evStopped,
            }
        )
        self.eof_recovery_timer = eTimer()
        self.onFirstExecBegin.append(lambda: self.startStream())
        self.onClose.append(self.cancel)

    def nextitem(self):
        """Switch to next channel"""
        self.stopStream()
        currentindex = int(self.currentindex) + 1
        if currentindex == self.itemscount:
            currentindex = 0
        self.currentindex = currentindex
        i = self.currentindex
        item = self.list[i][0]
        self.name = item[0]
        self.url = item[1]
        self.startStream()

    def previousitem(self):
        """Switch to previous channel"""
        self.stopStream()
        currentindex = int(self.currentindex) - 1
        if currentindex < 0:
            currentindex = self.itemscount - 1
        self.currentindex = currentindex
        i = self.currentindex
        item = self.list[i][0]
        self.name = item[0]
        self.url = item[1]
        self.startStream()

    def doEofInternal(self, playing):
        """Handle end of file (stream ended)"""
        print('[Playstream2] doEofInternal, playing:', playing)
        if self.execing and playing:
            # Clean memory
            vUtils.MemClean()

            # Check if this is a real EOF or temporary issue
            current_time = time.time()

            # Add EOF counter to prevent loops
            if not hasattr(self, 'eof_count'):
                self.eof_count = 0
                self.last_eof_time = 0

            # Check time between EOFs
            time_since_last_eof = current_time - self.last_eof_time
            self.last_eof_time = current_time

            if time_since_last_eof < 10:  # Less than 10 seconds between EOFs
                self.eof_count += 1
                print(
                    "[Playstream2] Frequent EOF #" +
                    str(self.eof_count) +
                    ", time: " +
                    "%.1f" % time_since_last_eof +
                    "s"
                )
            else:
                self.eof_count = 1

            # Restart based on EOF frequency
            if self.eof_count <= 3:  # Allow up to 3 quick retries
                delay = 2 + (self.eof_count * 2)  # 2, 4, 6 seconds
                print(
                    "[Playstream2] Restarting stream in " +
                    str(delay) +
                    " seconds (EOF #" +
                    str(self.eof_count) +
                    ")"
                )
                self.restartStreamDelayed(delay * 1000)
            else:
                print("[Playstream2] Too many EOFs, stopping auto-restart")
                error_msg = _("Stream ended. Too many connection issues.") + \
                    "\n" + _("Please try another channel.")
                self.session.open(
                    MessageBox,
                    error_msg,
                    MessageBox.TYPE_ERROR,
                    timeout=5
                )

    def __evEOF(self):
        """Event: End of file reached"""
        print('[Playstream2] __evEOF')
        self.end = True
        vUtils.MemClean()

        # Use same logic as doEofInternal
        current_time = time.time()
        if not hasattr(self, 'eof_count'):
            self.eof_count = 0
            self.last_eof_time = 0

        time_since_last_eof = current_time - self.last_eof_time
        self.last_eof_time = current_time

        if time_since_last_eof < 10:
            self.eof_count += 1
            print(
                "[Playstream2] __evEOF #" +
                str(self.eof_count) +
                ", time: " +
                "%.1f" % time_since_last_eof +
                "s"
            )
        else:
            self.eof_count = 1

        if self.eof_count <= 3:
            delay = 2 + (self.eof_count * 2)
            print(f"[Playstream2] Restarting from __evEOF in {delay} seconds")
            self.restartStreamDelayed(delay * 1000)
        else:
            print("[Playstream2] Too many EOFs in __evEOF")

    def __serviceStarted(self):
        """Service started playing"""
        print("Playback started successfully")
        self.state = self.STATE_PLAYING

    """
    # def __evStopped(self):
        # print("[Playstream2] Playback stopped - checking if should restart")
        # if self.execing and self.is_streaming:
            # print("[Playstream2] Attempting restart after stop")
            # self.restartAfterEOF()
    """

    def startStream(self, force=False):
        """Start the stream - proxy handles authentication"""
        if self.stream_running and not force:
            return

        print("[Playstream2] Starting stream: " + str(self.name))
        print("[Playstream2] URL: " + str(self.url))

        self.stream_running = True
        self.is_streaming = True

        # Clean up URL
        if "/live2/play/" in self.url and self.url.endswith(".ts"):
            print("[Playstream2] Converting to proxy format")
            channel_id = self.url.split("/live2/play/")[1].replace(".ts", "")
            self.url = "http://127.0.0.1:4323/vavoo?channel=" + channel_id

        # Determine playback method - FIXED LOGIC
        print("[Playstream2] DEBUG URL: " + self.url)

        # Check if it's ANY proxy URL (localhost or network IP)
        if ":4323/vavoo" in self.url or ":4323/resolve" in self.url:
            print("[Playstream2] Proxy URL detected")
            self.playProxyStream()
        else:
            print("[Playstream2] Non-proxy URL, using old system")
            self.playOldSystem()

    def restartStreamDelayed(self, delay_ms):
        """Restart stream after a delay"""
        try:
            # Stop any existing timer
            if hasattr(self, 'eof_recovery_timer'):
                self.eof_recovery_timer.stop()

            self.eof_recovery_timer = eTimer()
            try:
                self.eof_recovery_timer.callback.append(self.restartAfterEOF)
            except:
                self.eof_recovery_timer.timeout.connect(self.restartAfterEOF)

            self.eof_recovery_timer.start(delay_ms, True)
        except Exception as e:
            print('[Playstream2] Error setting up restart timer:', e)
            # Immediate restart as fallback
            self.restartAfterEOF()

    def restartAfterEOF(self):
        """Callback to restart stream after EOF"""
        try:
            print("[Playstream2] Restarting stream after EOF")
            self.stopStream()
            time.sleep(0.5)
            self.startStream(force=True)
        except Exception as e:
            print("[Playstream2] Error restarting after EOF: " + str(e))

    def showinfo(self):
        """Show stream information"""
        sTitle = ''
        sServiceref = ''
        try:
            servicename, serviceurl = vUtils.getserviceinfo(self.sref)
            if servicename is not None:
                sTitle = servicename
            else:
                sTitle = ''
            if serviceurl is not None:
                sServiceref = serviceurl
            else:
                sServiceref = ''
            currPlay = self.session.nav.getCurrentService()
            sTagCodec = currPlay.info().getInfoString(iServiceInformation.sTagCodec)
            sTagVideoCodec = currPlay.info().getInfoString(
                iServiceInformation.sTagVideoCodec)
            sTagAudioCodec = currPlay.info().getInfoString(
                iServiceInformation.sTagAudioCodec)
            message = (
                "stitle: " + str(sTitle) + "\n"
                "sServiceref: " + str(sServiceref) + "\n"
                "sTagCodec: " + str(sTagCodec) + "\n"
                "sTagVideoCodec: " + str(sTagVideoCodec) + "\n"
                "sTagAudioCodec: " + str(sTagAudioCodec)
            )
            self.mbox = self.session.open(
                MessageBox, message, MessageBox.TYPE_INFO)
        except:
            pass
        return

    def playProxyStream(self):
        """Play via proxy - token management is handled by proxy"""
        try:
            # Extract channel ID from URL
            channel_id = None

            if "/vavoo?channel=" in self.url:
                channel_id = self.url.split("/vavoo?channel=")[1]
            elif "/resolve?id=" in self.url:
                channel_id = self.url.split("/resolve?id=")[1]

            # Clean up any extra parameters
            if channel_id and '?' in channel_id:
                channel_id = channel_id.split('?')[0]

            if not channel_id:
                print("[Playstream2] Could not extract channel ID")
                self.playOldSystem()
                return

            # Get proxy host from URL or use default
            proxy_host = "127.0.0.1:4323"
            if "://" in self.url:
                import re
                match = re.search(r'://([^/]+)', self.url)
                if match:
                    proxy_host = match.group(1)

            # Build proxy URL WITHOUT extra parameters
            proxy_url = "http://" + \
                str(proxy_host) + "/vavoo?channel=" + str(channel_id)
            print("[Playstream2] Clean proxy URL: " + proxy_url)

            # Add User-Agent as fragment
            stream_url_with_ua = proxy_url + "#User-Agent=VAVOO/2.6"

            # Encode for Enigma2
            encoded_url = stream_url_with_ua.replace(":", "%3a")
            encoded_name = self.name.replace(":", "%3a")

            ref = (
                "4097:0:0:0:0:0:0:0:0:0:" +
                encoded_url +
                ":" +
                encoded_name
            )
            print("[Playstream2] Service reference: " + ref)

            sref = eServiceReference(ref)
            sref.setName(self.name)
            self.sref = sref

            # Reset EOF counter
            self.eof_count = 0
            self.last_eof_time = 0

            # Play the stream
            self.session.nav.stopService()
            self.session.nav.playService(self.sref)

            print("[Playstream2] Proxy stream started successfully")

        except Exception as e:
            error_msg = str(e)
            print("[Playstream2] playProxyStream error: " + error_msg)

            # Fallback to old system
            trace_error()
            self.playOldSystem()

    def playOldSystem(self):
        """Fallback to old playback system"""
        try:
            sig = vUtils.getAuthSignature()
            app = '?n=1&b=5&vavoo_auth=' + str(sig) + '#User-Agent=VAVOO/2.6'
            url = self.url
            if not url.startswith("http"):
                url = "http://" + url

            full_url = url + app
            ref = "{0}:0:0:0:0:0:0:0:0:0:{1}:{2}".format(
                "4097",
                full_url.replace(":", "%3a"),
                self.name.replace(":", "%3a")
            )

            print("[Playstream2] Old system ref: " + ref)

            sref = eServiceReference(ref)
            sref.setName(self.name)
            self.sref = sref
            self.session.nav.stopService()
            self.session.nav.playService(self.sref)

        except Exception as e:
            print("[Playstream2] playOldSystem error: " + str(e))
            trace_error()

    def stopStream(self):
        """Stop the stream and cleanup"""
        if self.stream_running:
            self.stream_running = False
            self.is_streaming = False
            print("[Playstream2] Stream stopped")

        # Stop recovery timer
        if hasattr(self, 'eof_recovery_timer'):
            self.eof_recovery_timer.stop()

        # Stop current service
        try:
            self.session.nav.stopService()
            if self.srefInit:
                self.session.nav.playService(self.srefInit)
        except:
            pass

    def cancel(self):
        """Close the player"""
        print("[Playstream2] Closing player...")
        self.stopStream()

        # Reset EOF counter
        if hasattr(self, 'eof_count'):
            self.eof_count = 0

        # Cleanup temp files
        if isfile("/tmp/hls.avi"):
            remove("/tmp/hls.avi")

        # Restore aspect ratio
        try:
            aspect_manager.restore_aspect()
        except:
            pass

        self.close()

    def leavePlayer(self):
        """Alternative close method"""
        self.stopStream()
        self.close()


class AutoStartTimer:
    def __init__(self):
        print("*** AutoStartTimer Vavoo ***")

        # Check if there are bouquets to update
        favorite_channel = join(PLUGIN_PATH, 'Favorite.txt')

        if not isfile(favorite_channel):
            print("[AutoStartTimer] No Favorite.txt - nothing to update")
            return  # Exit, timer not needed

        print("[AutoStartTimer] Favorite.txt found, starting timer...")

        self.timer = eTimer()
        try:
            self.timer.callback.append(self.on_timer)
        except:
            self.timer.timeout.connect(self.on_timer)

        self.timer.start(100, True)
        self.update()

    def on_timer(self):
        """Timer callback - triggered when timer expires"""
        print("[AutoStartTimer] Timer triggered")
        self.timer.stop()

        now = int(time.time())
        wake = now
        constant = 0

        if cfg.timetype.value == "fixed time":
            wake = self.get_wake_time()

        if abs(wake - now) < 60:
            try:
                self.startMain()
                constant = 60
                localtime = time.asctime(time.localtime(time.time()))
                cfg.last_update.value = localtime
                cfg.last_update.save()
            except Exception as error:
                print("[AutoStartTimer] Error in startMain:", error)
                trace_error()

        self.update(constant)

    def get_wake_time(self):
        if cfg.autobouquetupdate.value is True:
            if cfg.timetype.value == "interval":
                interval = int(cfg.updateinterval.value)
                nowt = time.time()
                return int(nowt) + interval * 60
            if cfg.timetype.value == "fixed time":
                ftc = cfg.fixedtime.value
                now = time.localtime(time.time())
                fwt = int(time.mktime((
                    now.tm_year,
                    now.tm_mon,
                    now.tm_mday,
                    ftc[0],
                    ftc[1],
                    now.tm_sec,
                    now.tm_wday,
                    now.tm_yday,
                    now.tm_isdst
                )))
                return fwt
        else:
            return -1

    def update(self, constant=0):
        self.timer.stop()
        wake = self.get_wake_time()
        nowt = time.time()
        if wake > 0:
            if wake < nowt + constant:
                if cfg.timetype.value == "interval":
                    interval = int(cfg.updateinterval.value)
                    wake += interval * 60
                elif cfg.timetype.value == "fixed time":
                    wake += 86400
            next_time = wake - int(nowt)
            if next_time > 3600:
                next_time = 3600
            if next_time <= 0:
                next_time = 60
            self.timer.startLongTimer(next_time)
        else:
            wake = -1
        return wake

    def startMain(self):
        favorite_channel = join(PLUGIN_PATH, 'Favorite.txt')
        if not isfile(favorite_channel):
            print("Favorite.txt not found - no bouquets to update")
            return

        try:
            # 1. Read bouquets
            bouquets_to_update = []
            with open(favorite_channel, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3 and parts[0].strip(
                        ) and parts[2].strip():
                            name = parts[0].strip()
                            url = parts[1].strip() if len(
                                parts) > 1 and parts[1].strip() else ""
                            export_type = parts[2].strip()
                            bouquets_to_update.append((name, url, export_type))

            if not bouquets_to_update:
                print("No valid bouquets found in Favorite.txt")
                return

            print("[AutoStartTimer] Updating " +
                  str(len(bouquets_to_update)) + " bouquets")

            # 2. Ensure proxy is running
            if not is_proxy_running():
                print("[AutoStartTimer] Starting proxy...")
                if not run_proxy_in_background():
                    print("[AutoStartTimer] Failed to start proxy")
                    return

            # 3. Wait for proxy to be ready
            for i in range(10):
                if is_proxy_ready(timeout=3):
                    break
                print("[AutoStartTimer] Waiting for proxy (" + str(i + 1) + "/10)")
                time.sleep(1)

            # 4. Update each bouquet
            successful_updates = 0
            for name, url, export_type in bouquets_to_update:
                print("[AutoStartTimer] Updating: " + name)

                # Remove old bouquet
                removed = remove_bouquets_by_name(name)
                if removed > 0:
                    print(
                        "[AutoStartTimer] Removed " +
                        str(removed) +
                        " old bouquet files")

                # Create new bouquet (proxy only)
                ch = convert_bouquet(
                    cfg.services.value,
                    name,
                    url,  # Can be empty
                    export_type,
                    cfg.server.value,
                    cfg.list_position.value
                )

                if ch > 0:
                    successful_updates += 1
                    print("[AutoStartTimer] ✓ Updated: " +
                          name + " (" + str(ch) + " channels)")
                    _update_favorite_file(name, url, export_type)
                else:
                    print("[AutoStartTimer] ✗ Failed: " + name)

            # 5. Update timestamp and show MessageBox
            if successful_updates > 0:
                localtime = time.asctime(time.localtime(time.time()))
                cfg.last_update.value = localtime
                cfg.last_update.save()
                print("[AutoStartTimer] Updated " +
                      str(successful_updates) +
                      "/" +
                      str(len(bouquets_to_update)) +
                      " bouquets")

        except Exception as e:
            print("[AutoStartTimer] Error: " + str(e))
            import traceback
            traceback.print_exc()


def autostart(reason, session=None, **kwargs):
    global auto_start_timer
    global _session

    if reason == 0 and _session is None:
        if session is not None:
            _session = session

            # ONLY IF auto-update is enabled in the config
            if cfg.autobouquetupdate.value is True:
                print("[Vavoo] Auto-update enabled, starting services...")

                # 1. Start proxy
                try:
                    from .vUtils import is_proxy_running
                    from .vavoo_proxy import run_proxy_in_background
                    if not is_proxy_running():
                        print("[Vavoo] Starting proxy...")
                        success = run_proxy_in_background()
                        if success:
                            print("[Vavoo] Proxy started successfully")
                        else:
                            print("[Vavoo] Failed to start proxy")
                            return  # If proxy fails, exit
                    else:
                        print("[Vavoo] Proxy is already running")

                except Exception as e:
                    print("[Vavoo] Error starting proxy: " + str(e))
                    return

                # 2. Wait for the proxy to be ready (if necessary)
                time.sleep(2)

                # 3. Start AutoStartTimer
                if auto_start_timer is None:
                    auto_start_timer = AutoStartTimer()
                    print("[Vavoo] AutoStartTimer started")

            else:
                print("[Vavoo] Auto-update disabled, no services started at boot")
    return


def check_configuring():
    """Check for new config values for auto start"""
    if cfg.autobouquetupdate.value is True:
        if auto_start_timer is not None:
            auto_start_timer.update()
        return


def get_next_wakeup():
    return -1


def add_skin_back(bakk):
    if isfile(join(BackPath, str(bakk))):
        baknew = join(BackPath, str(bakk))
        cmd = 'cp -f ' + str(baknew) + ' ' + BackPath + '/default.png'
        os_system(cmd)
        os_system('sync')


def add_skin_font():
    print('**********addFont')
    from enigma import addFont
    addFont(FNT_Path + '/Lcdx.ttf', 'Lcdx', 100, 1)
    addFont(str(FONTSTYPE), 'cvfont', 100, 1)
    addFont(join(str(FNT_Path), 'vav.ttf'), 'Vav', 100, 1)  # lcd


def cfgmain(menuid, **kwargs):
    if menuid == "mainmenu":
        return [(_('Vavoo Stream Live'), main, 'Vavoo', 11)]
    else:
        return []


def main(session, **kwargs):
    try:
        if isfile('/tmp/vavoo.log'):
            remove('/tmp/vavoo.log')
        add_skin_font()
        try:
            initialize_cache_with_local_flags()
            cleanup_old_temp_files()
        except Exception as e:
            print("Cache initialization error: %s" % str(e))
        session.open(startVavoo)
    except Exception as error:
        print('error as:', error)
        trace_error()


def Plugins(**kwargs):
    plugin_name = title_plug
    plugin_description = _('Vavoo Stream Live')
    plugin_icon = PLUGLOGO

    main_descriptor = PluginDescriptor(
        name=plugin_name,
        description=plugin_description,
        where=PluginDescriptor.WHERE_MENU,
        icon=plugin_icon,
        fnc=cfgmain
    )

    plugin_menu_descriptor = PluginDescriptor(
        name=plugin_name,
        description=plugin_description,
        where=PluginDescriptor.WHERE_PLUGINMENU,
        icon=plugin_icon,
        fnc=main
    )

    autostart_descriptor = PluginDescriptor(
        name=plugin_name,
        description=plugin_description,
        where=[
            PluginDescriptor.WHERE_AUTOSTART,
            PluginDescriptor.WHERE_SESSIONSTART],
        fnc=autostart,
        wakeupfnc=get_next_wakeup)

    result = [plugin_menu_descriptor, autostart_descriptor]

    if cfg.stmain.value:
        result.append(main_descriptor)

    return result
