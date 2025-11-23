#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
#########################################################
#                                                       #
#  Vavoo Stream Live Plugin                             #
#  Version: 1.41                                        #
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

# Standard library
import codecs
import ssl
import time
from datetime import datetime
from os import listdir, makedirs, unlink, remove, system
from os.path import exists as file_exists, join, islink, isfile, splitext
from re import compile, DOTALL  # sub
from json import loads
from sys import version_info  # , stdout, stderr

# Third-party libraries
import requests
from requests.adapters import HTTPAdapter, Retry

# Enigma / Components
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
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import SCOPE_PLUGINS, SCOPE_CONFIG, resolveFilename
from Tools.NumericalTextInput import NumericalTextInput
from Plugins.Plugin import PluginDescriptor

# Local application/library-specific imports
from . import _, __author__, __version__, __license__, country_codes
from . import vUtils
from .resolver.Console import Console
from .bouquet_manager import (
    convert_bouquet,
    _update_favorite_file,
    reorganize_all_bouquets_position,
    remove_bouquets_by_name,
    trace_error
)


try:
    unicode
except NameError:
    unicode = str

if version_info >= (2, 7, 9):
    try:
        ssl_context = ssl._create_unverified_context()
    except BaseException:
        ssl_context = None

try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote


try:
    aspect_manager = vUtils.AspectManager()
    current_aspect = aspect_manager.get_current_aspect()
except BaseException:
    pass

try:
    from Components.UsageConfig import defaultMoviePath
    downloadfree = defaultMoviePath()
except BaseException:
    if file_exists("/usr/bin/apt-get"):
        downloadfree = ('/media/hdd/movie/')


def get_enigma2_path():
    barry_active = '/media/ba/active/etc/enigma2'
    if file_exists(barry_active):
        return barry_active.rstrip('/')  # Rimuovi eventuale slash finale

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


# set plugin
title_plug = 'Vavoo'
desc_plugin = ('..:: Vavoo by Lululla v.%s ::..' % __version__)
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('vavoo'))
PLUGLOGO = join(PLUGIN_PATH, 'plugin.png')
CONFIG_FILE = resolveFilename(SCOPE_CONFIG, "settings")
regexs = '<a[^>]*href="([^"]+)"[^>]*><img[^>]*src="([^"]+)"[^>]*>'

global HALIGN, BackPath, FONTSTYPE, FNTPath
auto_start_timer = None
_session = None
tmlast = None
now = None

PY2 = version_info[0] == 2
PY3 = version_info[0] == 3

stripurl = 'aHR0cHM6Ly92YXZvby50by9jaGFubmVscw=='
keyurl = 'aHR0cDovL3BhdGJ1d2ViLmNvbS92YXZvby92YXZvb2tleQ=='
installer_url = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0JlbGZhZ29yMjAwNS92YXZvby9tYWluL2luc3RhbGxlci5zaA=='
developer_url = 'aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9CZWxmYWdvcjIwMDUvdmF2b28='

HALIGN = RT_HALIGN_LEFT
screenwidth = getDesktop(0).size()
screen_width = screenwidth.width()
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
cfg.timerupdate = ConfigSelectionNumber(default=10, min=1, max=60, stepwidth=1)
cfg.timetype = ConfigSelection(
    default="interval", choices=[
        ("interval", _("interval")), ("fixed time", _("fixed time"))])
cfg.updateinterval = ConfigSelectionNumber(
    default=10, min=5, max=3600, stepwidth=5)
cfg.fixedtime = ConfigClock(default=46800)
cfg.last_update = ConfigText(default="Never")
cfg.stmain = ConfigYesNo(default=True)
cfg.ipv6 = ConfigEnableDisable(default=False)
cfg.dns = ConfigSelection(default="Default", choices=mydns)
cfg.fonts = ConfigSelection(default='vav', choices=fonts)
cfg.back = ConfigSelection(default='oktus', choices=BakP)
cfg.default_view = ConfigSelection(
    default="countries",
    choices=[("countries", _("Countries")), ("categories", _("Categories"))]
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
except BaseException:
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
        self.l.setBuildFunc(self.buildEntry)

    def buildEntry(self, entry):
        """Build list entry - entry should be [ (name, link), icon, text ]"""
        return entry


def show_list(name, link, is_category=False):
    global HALIGN
    if any(s in lng for s in locl):
        HALIGN = RT_HALIGN_RIGHT
    else:
        HALIGN = RT_HALIGN_LEFT

    # Il primo elemento deve essere una tupla con i dati
    res = [(name, link)]
    default_icon = join(PLUGIN_PATH, 'skin/pics/vavoo_ico.png')

    pngx = default_icon

    separators = ["➾", "⟾", "->", "→"]
    for sep in separators:
        if sep in name:
            country_name = name.split(sep)[0].strip()
            country_code = country_codes.get(country_name, None)
            if country_code:
                icon_file = country_code + '.png'
                pngx = join(PLUGIN_PATH, 'skin/cowntry', icon_file)
            break
    else:
        country_code = country_codes.get(name, None)
        if country_code:
            icon_file = country_code + '.png'
            pngx = join(PLUGIN_PATH, 'skin/cowntry', icon_file)

    if not isfile(pngx):
        pngx = default_icon

    # Check if file exists
    if not isfile(pngx):
        print("Icon not found: " + pngx)
        pngx = default_icon

    icon_pos = (10, 10) if screen_width == 1920 else (10, 5)
    icon_size = (50, 35) if screen_width == 1920 else (40, 30)

    if screen_width == 2560:
        text_pos = (90, 0)
        text_size = (750, 60)
    elif screen_width == 1920:
        text_pos = (80, 0)
        text_size = (540, 50)
    else:
        text_pos = (85, 0)
        text_size = (380, 50)

    # Aggiungi gli elementi MultiContent
    res.append(
        MultiContentEntryPixmapAlphaTest(
            pos=icon_pos,
            size=icon_size,
            png=loadPNG(pngx)))
    res.append(
        MultiContentEntryText(
            pos=text_pos,
            size=text_size,
            font=0,
            text=str(name),
            flags=HALIGN | RT_VALIGN_CENTER))
    return res


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
        self.list.append(
            getConfigListEntry(
                _("Server for Player Used"),
                cfg.server,
                _("Server for player.\nNow %s") %
                cfg.server.value))
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
        self.list.append(
            getConfigListEntry(
                _("Refresh Player"),
                cfg.timerupdate,
                _("Configure Update Timer for player refresh")))
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
        self.list.append(
            getConfigListEntry(
                _("Select Fonts"),
                cfg.fonts,
                _("Configure Fonts.\nEg:Arabic or other language.")))
        self.list.append(
            getConfigListEntry(
                _("Ipv6 State Of Lan (On/Off)"),
                cfg.ipv6,
                _("Active or Disactive lan Ipv6.\nNow %s") %
                cfg.ipv6.value))
        self.list.append(
            getConfigListEntry(
                _("Scheduled Bouquet Update:"),
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
            if not file_exists(downloadfree):
                makedirs(downloadfree)
            cmd = "python {} {}".format(
                join(
                    PLUGIN_PATH,
                    'Vavoo_m3u.py'),
                downloadfree)
            from enigma import eConsoleAppContainer
            self.container = eConsoleAppContainer()
            try:
                self.container.appClosed.append(self.runFinished)
            except BaseException:
                self.container.appClosed_conn = self.container.appClosed.connect(
                    self.runFinished)

            self.container.execute(cmd)

            cfg.genm3u.setValue(0)
            cfg.genm3u.save()

            self.session.open(
                MessageBox,
                _("All .m3u files have been generated!"),
                MessageBox.TYPE_INFO,
                timeout=4)

    def runFinished(self, retval):
        self["description"].setText(
            "Generation completed. Files saved to %s." %
            downloadfree)

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

    def ipv6(self):
        if islink('/etc/rc3.d/S99ipv6dis.sh'):
            self.session.openWithCallback(
                self.ipv6check,
                MessageBox,
                _("Ipv6 [Off]?"),
                MessageBox.TYPE_YESNO,
                timeout=5,
                default=True)
        else:
            self.session.openWithCallback(
                self.ipv6check,
                MessageBox,
                _("Ipv6 [On]?"),
                MessageBox.TYPE_YESNO,
                timeout=5,
                default=True)

    def ipv6check(self, result):
        if result:
            if islink('/etc/rc3.d/S99ipv6dis.sh'):
                unlink('/etc/rc3.d/S99ipv6dis.sh')
                cfg.ipv6.setValue(False)
            else:
                system("echo '#!/bin/bash")
                system(
                    "echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6' > /etc/init.d/ipv6dis.sh")
                from os import chmod
                chmod("/etc/init.d/ipv6dis.sh", 0o700)
                system("ln -s /etc/init.d/ipv6dis.sh /etc/rc3.d/S99ipv6dis.sh")
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
        sel = self["config"].getCurrent()[1]
        if sel and sel == cfg.genm3u:
            self.gnm3u()
        self.createSetup()
        self.showhide()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        sel = self["config"].getCurrent()[1]
        if sel and sel == cfg.genm3u:
            self.gnm3u()
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
                self.ipv6()

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

    def dnsmy(self):
        valuedns = cfg.dns.value
        print(valuedns)
        valdns = False
        if str(valuedns) != 'None':
            self.cmd1 = None
            if 'google' in valuedns:
                self.cmd1 = join(
                    PLUGIN_PATH + 'resolver/', 'DnsGoogle.sh')
            elif 'couldfire' in valuedns:
                self.cmd1 = join(
                    PLUGIN_PATH + 'resolver/', 'DnsCloudflare.sh')
            elif 'quad9' in valuedns:
                self.cmd1 = join(
                    PLUGIN_PATH + 'resolver/', 'DnsQuad9.sh')
            if self.cmd1 is not None:
                try:
                    from os import access, X_OK, chmod
                    if not access(self.cmd1, X_OK):
                        chmod(self.cmd1, 0o755)
                    import subprocess
                    subprocess.check_output(['bash', self.cmd1])
                    valdns = True
                    print('Dns Updated!\nRestart your device ...')
                except subprocess.CalledProcessError as e:
                    print(e.output)
        return valdns

    def restartGUI(self, answer):
        if answer is True:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close()

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
            self.timer_conn = self.timer.timeout.connect(self.decodeImage)
        else:
            self.timer.callback.append(self.decodeImage)
        self.timer.start(500, True)
        self.timerx = eTimer()
        if isfile('/var/lib/dpkg/status'):
            self.timerx_conn = self.timerx.timeout.connect(self.clsgo)
        else:
            self.timerx.callback.append(self.clsgo)
        self.timerx.start(2000, True)

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
        self._load_skin()
        self._initialize_labels()
        self._initialize_actions()
        self["menulist"].onSelectionChanged.append(self._update_selection_name)
        self.url = vUtils.b64decoder(stripurl)
        self.currentList = 'menulist'
        self.loading_ok = False
        self.count = 0
        self.loading = 0
        self.current_view = "categories"
        self.cat()

    def _load_skin(self):
        """Load the skin file."""
        skin = join(skin_path, 'defaultListScreen.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

    def _initialize_labels(self):
        """Initialize the labels on the screen."""
        self.menulist = []
        self['menulist'] = m2list([])
        self['red'] = Label(_('Exit'))
        self['green'] = Label(_('Remove') + ' Fav')
        self['yellow'] = Label(_('Update Me'))
        self["blue"] = Label(_('Reload Bouqet'))
        self['name'] = Label('Loading...')
        self['version'] = Label()

    def _initialize_actions(self):
        """Initialize the actions for buttons."""
        actions = {
            'prevBouquet': self.chDown,
            'nextBouquet': self.chUp,
            'ok': self.ok,
            'menu': self.goConfig,
            'green': self.msgdeleteBouquets,
            'blue': self._reload_services_after_delay,
            'cancel': self.closex,
            'exit': self.closex,
            'info': self.info,
            'showEventInfo': self.info,
            'red': self.closex,
            'yellow': self.update_me,
            'yellow_long': self.update_dev,
            'info_long': self.update_dev,
            'infolong': self.update_dev,
            'showEventInfoPlugin': self.update_dev,
        }
        actions_list = [
            'MenuActions',
            'OkCancelActions',
            'DirectionActions',
            'ColorActions',
            'InfobarEPGActions',
            'EPGSelectActions'
        ]
        self['actions'] = ActionMap(actions_list, actions, -1)

    def _reload_services_after_delay(self, delay=3000):
        """Reload services after a manual edit"""
        try:
            def do_reload():
                try:
                    db = eDVBDB.getInstance()
                    if db:
                        db.reloadBouquets()
                        self.session.open(
                            MessageBox,
                            _("Bouquets have been successfully reloaded!"),
                            MessageBox.TYPE_INFO,
                            timeout=5)
                    else:
                        print("Could not get eDVBDB instance for reload")
                except Exception as e:
                    print("Error during service reload: " + str(e))
                finally:
                    reload_timer.stop()

            reload_timer = eTimer()
            reload_timer.callback.append(do_reload)
            reload_timer.start(delay, True)

        except Exception as e:
            print("Error setting up service reload: " + str(e))

    def closex(self):
        print("DEBUG: Exit from plugin Calling ReloadBouquets after export")
        self._reload_services_after_delay()
        self.close()

    def cat(self):
        self.cat_list = []
        self.items_tmp = []

        try:
            content = self._get_content()
            data = self._parse_json(content)
            if data is None:
                return

            self.all_data = data

            if cfg.default_view.value == "countries":
                self.show_countries_view()
            else:
                self.show_categories_view()

            self._update_ui()
        except Exception as error:
            print("error:", error)
            trace_error()
            self["name"].setText("Error")

        self["version"].setText("V." + __version__)

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
        content = vUtils.getUrl(self.url)
        if PY3:
            content = vUtils.ensure_str(content)
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
        name = self['menulist'].getCurrent()[0][0]
        url = self['menulist'].getCurrent()[0][1]

        # Handle view options
        if name == "View by Countries":
            self.show_countries_view()
            return
        elif name == "View by Categories":
            self.show_categories_view()
            return

        try:
            self.session.open(vavoo, name, url)
        except Exception as error:
            print('error as:', error)
            trace_error()

    def msgdeleteBouquets(self):
        self.session.openWithCallback(
            self.deleteBouquets,
            MessageBox,
            _("Remove ALL Vavoo bouquets?\nThis will remove:\n- Country bouquets\n- Category bouquets\n- Container bouquets"),
            MessageBox.TYPE_YESNO,
            timeout=10,
            default=False)

    def deleteBouquets(self, result):
        """Delete all Vavoo bouquets"""
        if result:
            try:
                removed_count = remove_bouquets_by_name()  # None = tutti

                # Remove Favorite.txt
                favorite_path = join(PLUGIN_PATH, 'Favorite.txt')
                if isfile(favorite_path):
                    remove(favorite_path)
                    print("✓ Removed Favorite.txt")

                # Show success message
                self.session.open(
                    MessageBox, _('Vavoo bouquets removed successfully!\n(%s files deleted)') %
                    removed_count, MessageBox.TYPE_INFO, timeout=5)

                self._reload_services_after_delay()

            except Exception as error:
                print("Error in deleteBouquets: " + str(error))

    def goConfig(self):
        self.session.open(vavoo_config)

    def info(self):
        """Display professional plugin information"""
        info_text = _(
            "%s\n\n"
            "📊 **Plugin Information**\n"
            "• Version: %s\n"
            "• Author: %s\n"
            "• License: %s\n\n"
            "🛠️ **Technical Details**\n"
            "• Streaming protocol: HTTP Live Streaming\n"
            "• Supported formats: TS, M3U8\n"
            "• Service reference: 4097, 5001, 5002\n"
            "• Bouquet generation: Automatic\n\n"
            "👥 **Credits & Acknowledgments**\n"
            "• Graphics: @oktus\n"
            "• Technical support: Qu4k3 - @KiddaC - @giorbak \n"
            "• Community: Linuxsat-support.com- Corvoboys Forum\n\n"
            "📝 **Important Notes**\n"
            "• This plugin provides FREE content only\n"
            "• Streams are aggregated from public sources\n"
            "• No direct server hosting\n"
            "• For personal use only\n\n"
            "⚖️ **License Information**\n"
            "This software is licensed under CC BY-NC-SA 4.0\n"
            "Redistribution must maintain attribution\n"
            "Commercial use is strictly prohibited"
        ) % (desc_plugin, __version__, __author__, __license__)

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
            if self.cat_list:
                self["menulist"].l.setList(self.cat_list)
                # self["menulist"].moveToIndex(0)
                self._update_selection_name()
            else:
                self["name"].setText("No items found")
        except Exception as error:
            print("Error updating UI:", error)
            self["name"].setText("Error")

    def _update_selection_name(self):
        """Update the name label with current selection"""
        try:
            current = self['menulist'].getCurrent()
            if current and len(current) > 0:
                name = current[0][0]
                self['name'].setText(str(name))
                print("MainVavoo _update_selection_name: " + str(name))
        except Exception as e:
            print("Error in MainVavoo _update_selection_name:", e)

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
            self.session.openWithCallback(
                self.install_update,
                MessageBox,
                _("New version %s is available.\n\nChangelog: %s\n\nDo you want to install it now?") %
                (new_version,
                    new_changelog),
                MessageBox.TYPE_YESNO)
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
        self._initialize_timer()

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

    def _initialize_actions(self):
        """Initialize the actions for buttons."""
        self["actions"] = ActionMap(
            [
                "MenuActions",
                "OkCancelActions",
                "DirectionActions",
                "ColorActions"
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
        except BaseException:
            self.timer_conn = self.timer.timeout.connect(self.cat)
        self.timer.start(500, True)

    def cat(self):
        self.cat_list = []
        items = []
        svr = cfg.server.value
        server = zServer(0, svr, None)
        try:
            content = vUtils.getUrl(self.url)
            if PY3:
                content = vUtils.ensure_str(content)
            all_data = loads(content)

            if all_data is not None:
                total_channels = 0
                matched_channels = 0
                for entry in all_data:
                    country = unquote(entry["country"]).strip("\r\n")
                    ids = entry["id"]
                    total_channels += 1
                    if self._matches_selection(country, self.name):
                        matched_channels += 1
                        ids = str(ids).replace(
                            ':',
                            '').replace(
                            ' ',
                            '').replace(
                            ',',
                            '')
                        url = str(server) + '/live2/play/' + ids + '.ts'
                        name_channel = unquote(entry["name"]).strip("\r\n")
                        name_channel = vUtils.decodeHtml(
                            name_channel)          # 1° - Decodifica HTML
                        name_channel = vUtils.rimuovi_parentesi(
                            name_channel)   # 2° - Remove (2023)
                        name_channel = vUtils.sanitizeFilename(
                            name_channel)    # 3° - Clean filesystem
                        item = name_channel + "###" + url + '\n'
                        items.append(item)

                print(
                    "DEBUG: Total channels: %s, Matched: %s for selection: %s" %
                    (total_channels, matched_channels, self.name))
                items.sort()
                self.itemlist = items
                self._create_list_directly(items)
                self.update_menu()

        except Exception as error:
            print('Error:', error)
            trace_error()
            self['name'].setText('Error')

    def _create_list_directly(self, items):
        self.cat_list = []
        for item in items:
            name1, url = item.split('###')
            url = url.replace('%0a', '').replace('%0A', '').strip("\r\n")
            name = unquote(name1).strip("\r\n")
            self.cat_list.append(show_list(name, url))

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

    def _reload_services_after_delay(self, delay=3000):
        """Reload services after a manual edit"""
        try:
            def do_reload():
                try:
                    db = eDVBDB.getInstance()
                    if db:
                        db.reloadBouquets()
                        self.session.open(
                            MessageBox,
                            _("Bouquets have been successfully reloaded!"),
                            MessageBox.TYPE_INFO,
                            timeout=5)
                    else:
                        print("Could not get eDVBDB instance for reload")
                except Exception as e:
                    print("Error during service reload: " + str(e))
                finally:
                    reload_timer.stop()

            reload_timer = eTimer()
            reload_timer.callback.append(do_reload)
            reload_timer.start(delay, True)

        except Exception as e:
            print("Error setting up service reload: " + str(e))

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
        self.session.open(Playstream2, name, url, index, item, cat_list)

    def message1(self, answer=None):
        if answer is None:
            # Show confirmation message before export
            self.session.openWithCallback(
                self.message1,
                MessageBox,
                _("Do you want to export this bouquet?\n%s") % self.name,
                MessageBox.TYPE_YESNO
            )
        elif answer is True:
            self.message2(self.name, self.url, True)
        elif answer is False:
            print("Export cancelled by user")

    def message2(self, name, url, response):
        # Determine export type based on content AND view
        separators = ["➾", "⟾", "->", "→"]
        has_separator = any(sep in name for sep in separators)

        if has_separator:
            # Single category - always flat
            export_type = "flat"
            print("DEBUG: Exporting single category as FLAT")
        else:
            # Main country - use the SAVED current_view
            if hasattr(self, 'current_view'):
                if self.current_view == "categories":
                    export_type = "hierarchical"  # Categories view = hierarchical
                else:
                    export_type = "flat"  # Countries view = SINGLE FILE
            else:
                export_type = "flat"  # Default = single file

        print("FINAL export_type: %s" % export_type)

        _update_favorite_file(name, url, export_type)
        ch = convert_bouquet(
            cfg.services.value,
            name,
            url,
            export_type,
            cfg.server.value,
            cfg.list_position.value)

        if int(ch) > 0:
            print("Bouquet created with %s channels" % ch)

        print("DEBUG: Calling ReloadBouquets after export")
        self._reload_services_after_delay()

    def search_vavoo(self):
        self.saved_itemlist = self.itemlist
        self.session.openWithCallback(
            self.onSearchResult, VavooSearch, self, self.itemlist)

    def onSearchResult(self, selected_item=None):
        """Callback con il canale selezionato dalla ricerca"""
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
                name = current[0][0]  # First tuple, first element (name)
                self['name'].setText(str(name))
                print("MainVavoo _update_selection_name: " + str(name))
        except Exception as e:
            print("Error in MainVavoo _update_selection_name:", e)

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
        if screen_width == 2560:
            self.skin = """
                <screen name="VavooSearch" position="center,center" size="1200,900" title="Vavoo Search">
                    <widget name="search_label" position="20,20" size="1160,60" font="Regular;40" halign="left" valign="center" />
                    <widget name="search_text" position="20,100" size="1160,80" font="Regular;40" halign="left" valign="center" backgroundColor="darkblue" />
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
                    <widget name="search_text" position="20,70" size="960,60" font="Regular;32" halign="left" valign="center" backgroundColor="darkblue" />
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
            self.searchTimer_conn = self.searchTimer.timeout.connect(
                self.updateFilteredList)
        except BaseException:
            self.searchTimer.callback.append(self.updateFilteredList)

        self.numericalInput = NumericalTextInput(
            nextFunc=self.searchWithString, mode="Search")
        self.input_active = False
        self.upper_case = False
        self.last_key = None
        self.search_text = ""
        self.last_key_time = 0
        self.key_timer = eTimer()
        try:
            self.key_timer_conn = self.key_timer.timeout.connect(
                self.finishKeyInput)
        except BaseException:
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
            title=_("Search"),
            text=self.search_text)

    def onKeyboardClosed(self, result):
        if result is not None:
            self.search_text = result
            self["search_text"].setText(self.search_text)
            self.updateFilteredList()

    def toggleCase(self):
        """Toggle between uppercase and lowercase"""
        self.upper_case = not self.upper_case
        case_text = _("UPPERCASE") if self.upper_case else _("lowercase")
        self["status"].setText(_("Case: {}").format(case_text))

    def updateStatusText(self):
        """Update status text"""
        if self.search_text:
            self["status"].setText(_('Search: "{}" - Found: {} channels').format(
                self.search_text, len(self.filteredList)))
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
                except BaseException:
                    continue

            if self.filteredList:
                self["status"].setText(_('Search: "{}" - Found: {} channels').format(
                    self.search_text, len(self.filteredList)))
            else:
                self["status"].setText(
                    _('Search: "{}" - No channels found').format(self.search_text))

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
            except BaseException:
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
            if hasattr(self, 'numericalInput'):
                self.numericalInput.nextKey()
        except BaseException:
            pass
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
        self.hideTimer = eTimer()
        try:
            self.hideTimer_conn = self.hideTimer.timeout.connect(
                self.doTimerHide)
        except BaseException:
            self.hideTimer.callback.append(self.doTimerHide)
        self.hideTimer.start(3000, True)
        self.onShow.append(self.__onShow)
        self.onHide.append(self.__onHide)

    def OkPressed(self):
        self.toggleShow()

    def __onShow(self):
        self.__state = self.STATE_SHOWN
        self.startHideTimer()

    def __onHide(self):
        self.__state = self.STATE_HIDDEN

    def serviceStarted(self):
        if self.execing:
            self.doShow()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            self.hideTimer.stop()
            self.hideTimer.start(3000, True)
        elif hasattr(self, "pvrStateDialog"):
            self.hideTimer.stop()
        self.skipToggleShow = False

    def doShow(self):
        self.hideTimer.stop()
        self.show()
        self.startHideTimer()

    def doTimerHide(self):
        self.hideTimer.stop()
        if self.__state == self.STATE_SHOWN:
            self.hide()

    def toggleShow(self):
        if self.skipToggleShow:
            self.skipToggleShow = False
            return
        if self.__state == self.STATE_HIDDEN:
            self.show()
            self.hideTimer.stop()
        else:
            self.hide()
            self.startHideTimer()

    def lockShow(self):
        try:
            self.__locked += 1
        except BaseException:
            self.__locked = 0
        if self.execing:
            self.show()
            self.hideTimer.stop()
            self.skipToggleShow = False

    def unlockShow(self):
        try:
            self.__locked -= 1
        except BaseException:
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
    Screen
):
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
        """Initialize infobar components."""
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

        """Initialize the actions for buttons."""
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
                "tv": self.cicleStreamType,
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
        self.onFirstExecBegin.append(lambda: self.startStream(force=True))
        self.onClose.append(self.cancel)

    def nextitem(self):
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
        print('doEofInternal', playing)
        vUtils.MemClean()
        if self.execing and playing:
            self.startStream()

    def __evEOF(self):
        print('__evEOF')
        self.end = True
        vUtils.MemClean()
        self.startStream()

    def showinfo(self):
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
        except BaseException:
            pass
        return

    def startStream(self, force=False):
        if self.stream_running and not force:
            trace_error()
            return

        self.stream_running = True
        self.is_streaming = True
        self.cicleStreamType()
        self.startAutoRefresh()

    def startAutoRefresh(self):
        update_refresh = int(cfg.timerupdate.value)
        if update_refresh < 1:
            update_refresh = 10

        if hasattr(self, "refreshTimer"):
            self.refreshTimer.stop()
        self.refreshTimer = eTimer()
        try:
            self.refreshTimer_conn = self.refreshTimer.timeout.connect(
                self.refreshStream)
        except BaseException:
            self.refreshTimer.callback.append(self.refreshStream)
        self.refreshTimer.start(update_refresh * 60 * 1000)

    def refreshStream(self):
        print("Starting new stream...")
        self.stream_running = True
        self.is_streaming = True

        # Obtain a new authentication token
        sig = vUtils.getAuthSignature()
        app = '?n=1&b=5&vavoo_auth=' + str(sig) + '#User-Agent=VAVOO/2.6'
        url = self.url
        if not url.startswith("http"):
            url = "http://" + url
        full_url = url + app
        ref = "{0}:0:0:0:0:0:0:0:0:0:{1}:{2}".format(
            self.servicetype,
            full_url.replace(":", "%3a"),
            self.name.replace(":", "%3a")
        )
        print("final reference:", ref)
        sref = eServiceReference(ref)
        sref.setName(self.name)
        self.sref = sref
        self.session.nav.stopService()
        self.session.nav.playService(self.sref)

    def stopStream(self):
        if self.stream_running:
            self.stream_running = False
            self.is_streaming = False  # Reset here as well
            print("Stream stopped and state reset.")
            self.session.nav.stopService()
            self.session.nav.playService(self.srefInit)

            # Stop the refresh timer when the stream is stopped
            if hasattr(self, "refreshTimer") and self.refreshTimer:
                self.refreshTimer.stop()
        else:
            print("No active stream to stop.")

    def cicleStreamType(self):
        self.servicetype = "4097"
        if not self.url.startswith("http"):
            self.url = "http://" + self.url
        if str(splitext(self.url)[-1]) == ".m3u8":
            if self.servicetype == "1":
                self.servicetype = "4097"
        self.refreshStream()

    def openTest(self, servicetype, url):
        sig = vUtils.getAuthSignature()
        app = '?n=1&b=5&vavoo_auth=' + str(sig) + '#User-Agent=VAVOO/2.6'
        name = self.name
        url = url + app
        ref = "{0}:0:0:0:0:0:0:0:0:0:{1}:{2}".format(
            servicetype, url.replace(
                ":", "%3a"), name.replace(
                ":", "%3a"))
        print('final reference:', ref)
        sref = eServiceReference(ref)
        self.sref = sref
        self.sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(self.sref)

    def showVideoInfo(self):
        if self.shown:
            self.hideInfobar()
        if self.infoCallback is not None:
            self.infoCallback()
        return

    def showAfterSeek(self):
        if isinstance(self, TvInfoBarShowHide):
            self.doShow()

    def cancel(self):
        if hasattr(self, "refreshTimer") and self.refreshTimer:
            self.refreshTimer.stop()
            self.refreshTimer = None

        self.stream_running = False
        self.is_streaming = False

        if isfile("/tmp/hls.avi"):
            remove("/tmp/hls.avi")
        self.session.nav.stopService()
        self.session.nav.playService(self.srefInit)

        aspect_manager.restore_aspect()
        self.close()

    def leavePlayer(self):
        self.stopStream()
        self.close()


class AutoStartTimer:
    def __init__(self, session):
        print("*** running AutoStartTimer Vavoo ***")
        self.session = session
        self.timer = eTimer()
        try:
            self.timer.callback.append(self.on_timer)
        except BaseException:
            self.timer_conn = self.timer.timeout.connect(self.on_timer)
        self.timer.start(100, True)
        self.update()

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
                    wake += interval * 60  # * 60
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

    def on_timer(self):
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
                print(error)
                trace_error()
        self.update(constant)

    def startMain(self):
        favorite_channel = join(PLUGIN_PATH, 'Favorite.txt')

        if not isfile(favorite_channel):
            print("Favorite.txt not found - no bouquets to update")
            return

        try:
            bouquets_to_update = []

            # Read bouquets from Favorite.txt
            with open(favorite_channel, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            name = parts[0]
                            url = parts[1]
                            export_type = parts[2]
                            bouquets_to_update.append((name, url, export_type))

            if not bouquets_to_update:
                print("No bouquets found in Favorite.txt")
                return

            print("Scheduled update for " +
                  str(len(bouquets_to_update)) + " bouquets")

            # Update each bouquet
            for name, url, export_type in bouquets_to_update:
                print("Updating bouquet: " + name +
                      " (type: " + export_type + ")")

                # Remove existing bouquet before recreating
                self._remove_bouquet_by_name(name)

                # Recreate bouquet
                ch = convert_bouquet(
                    cfg.services.value,
                    name,
                    url,
                    export_type,
                    cfg.server.value,
                    cfg.list_position.value)

                if ch > 0:
                    print("Successfully updated: " + name +
                          " (" + str(ch) + " channels)")
                    # Update Favorite.txt timestamp
                    _update_favorite_file(name, url, export_type)
                else:
                    print("Failed to update: " + name)

            # Update last update timestamp
            localtime = time.asctime(time.localtime(time.time()))
            cfg.last_update.value = localtime
            cfg.last_update.save()

        except Exception as e:
            print("Error during scheduled update:", e)


def check_configuring():
    """Check for new config values for auto start"""
    if cfg.autobouquetupdate.value is True:
        if auto_start_timer is not None:
            auto_start_timer.update()
        return


def autostart(reason, session=None, **kwargs):
    global auto_start_timer
    global _session

    if reason == 0 and _session is None:
        if session is not None:
            _session = session
            if auto_start_timer is None:
                auto_start_timer = AutoStartTimer(session)
    return


def get_next_wakeup():
    return -1


def add_skin_back(bakk):
    if isfile(join(BackPath, str(bakk))):
        baknew = join(BackPath, str(bakk))
        cmd = 'cp -f ' + str(baknew) + ' ' + BackPath + '/default.png'
        system(cmd)
        system('sync')


def add_skin_font():
    print('**********addFont')
    from enigma import addFont
    addFont(FNT_Path + '/Lcdx.ttf', 'Lcdx', 100, 1)
    addFont(str(FONTSTYPE), 'cvfont', 100, 1)
    addFont(join(str(FNT_Path), 'vav.ttf'), 'Vav', 100, 1)  # lcd


def cfgmain(menuid, **kwargs):
    if menuid == "mainmenu":
        return [(_('Vavoo Stream Live'), main, 'Vavoo', 55)]
    else:
        return []


def main(session, **kwargs):
    try:
        if isfile('/tmp/vavoo.log'):
            remove('/tmp/vavoo.log')
        add_skin_font()
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
