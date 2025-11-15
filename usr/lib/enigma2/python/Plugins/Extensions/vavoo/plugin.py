#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
#########################################################
#                                                       #
#  Vavoo Stream Live Plugin                             #
#  Version: 1.39                                        #
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: CC BY-NC-SA 4.0                             #
#  https://creativecommons.org/licenses/by-nc-sa/4.0    #
#  Last Modified: 20251114                              #
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
__version__ = "1.39"
__license__ = "CC BY-NC-SA 4.0"
# Standard library imports
# Enigma2 components
# Standard library
import codecs
import ssl
import time
from datetime import datetime
from os import listdir, makedirs, unlink, remove, system
from os.path import exists as file_exists, join, dirname, islink, isfile, splitext
from re import sub, compile, DOTALL
from json import loads
from sys import version_info, stdout, stderr

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
from Tools.Directories import SCOPE_PLUGINS, resolveFilename
from Plugins.Plugin import PluginDescriptor

# Local application/library-specific imports
from . import _
from . import vUtils
from .resolver.Console import Console


global HALIGN
_session = None
tmlast = None
now = None
PY2 = version_info[0] == 2
PY3 = version_info[0] == 3


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


# set plugin
currversion = '1.39'
title_plug = 'Vavoo'
desc_plugin = ('..:: Vavoo by Lululla v.%s ::..' % currversion)
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('vavoo'))
pluglogo = join(PLUGIN_PATH, 'plugin.png')
stripurl = 'https://vavoo.to/channels=='
keyurl = 'aHR0cDovL3BhdGJ1d2ViLmNvbS92YXZvby92YXZvb2tleQ=='
keyurl2 = 'aHR0cDovL3BhdGJ1d2ViLmNvbS92YXZvby92YXZvb2tleTI='
installer_url = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0JlbGZhZ29yMjAwNS92YXZvby9tYWluL2luc3RhbGxlci5zaA=='
developer_url = 'aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9CZWxmYWdvcjIwMDUvdmF2b28='
# ENIGMA_PATH = '/etc/enigma2/'
json_file = '/tmp/vavookey'
HALIGN = RT_HALIGN_LEFT
screenwidth = getDesktop(0).size()
screen_width = screenwidth.width()
regexs = '<a[^>]*href="([^"]+)"[^>]*><img[^>]*src="([^"]+)"[^>]*>'
auto_start_timer = None


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


# log
def trace_error():
    import traceback
    try:
        traceback.print_exc(file=stdout)
        with open("/tmp/vavoo.log", "a", encoding='utf-8') as log_file:
            traceback.print_exc(file=log_file)
    except Exception as e:
        print("Failed to log the error:", e, file=stderr)


def _reload_services_after_delay(delay=4000):
    """Reload Enigma2 bouquets and service lists"""
    try:
        def do_reload():
            try:
                eDVBDB.getInstance().reloadServicelist()
                eDVBDB.getInstance().reloadBouquets()
            except Exception as e:
                print("Service reload error: " + str(e))

        reload_timer = eTimer()
        try:
            reload_timer.callback.append(do_reload)
        except BaseException:
            reload_timer.timeout.connect(do_reload)
        reload_timer.start(delay, True)

    except Exception as e:
        print("Error setting up service reload: " + str(e))


# https://www.oha.to/oha-tv/
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


# back
global BackPath, FONTSTYPE, FNTPath
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
# BakP = sorted(BakP, key=lambda x: x[1])


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
            return path.rstrip('/')  # Rimuovi eventuale slash finale

    return '/etc/enigma2'


ENIGMA_PATH = get_enigma2_path()


# config section
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
FONTSTYPE = FNT_Path + '/' + cfg.fonts.value + '.ttf'
eserv = int(cfg.services.value)

# ipv6
if islink('/etc/rc3.d/S99ipv6dis.sh'):
    cfg.ipv6.setValue(True)
    cfg.ipv6.save()


# language
locl = "ar", "ae", "bh", "dz", "eg", "in", "iq", "jo", "kw", "lb", "ly", "ma", "om", "qa", "sa", "sd", "ss", "sy", "tn", "ye"
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
    try:
        retries = Retry(total=1, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retries)
        http = requests.Session()
        http.mount("http://", adapter)
        http.mount("https://", adapter)

        r = http.get(
            url,
            headers={'User-Agent': vUtils.RequestAgent()},
            timeout=10,
            verify=True,
            stream=True,
            allow_redirects=False
        )
        r.raise_for_status()

        if r.status_code == requests.codes.ok:
            # Consume il contenuto per chiudere correttamente la connessione
            for xc in r.iter_content(1024):
                pass
            r.close()
            return True

    except Exception as error:
        print(error)
        trace_error()
    return False


def zServer(opt=0, server=None, port=None):
    try:
        from urllib.error import HTTPError
    except ImportError:
        from urllib2 import HTTPError
    try:
        if raises(server):
            print('server is raise:', str(server))
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


def show_list(name, link, is_category=False):
    global HALIGN
    if any(s in lng for s in locl):
        HALIGN = RT_HALIGN_RIGHT
    else:
        HALIGN = RT_HALIGN_LEFT

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
        print("Icon not found:", pngx)
        pngx = default_icon

    icon_pos = (10, 10) if screen_width == 2560 else (10, 5)
    icon_size = (60, 40) if screen_width == 2560 else (50, 35)

    if screen_width == 2560:
        text_pos = (90, 0)
        text_size = (750, 60)
    elif screen_width == 1920:
        text_pos = (80, 0)
        text_size = (540, 50)
    else:
        text_pos = (85, 0)
        text_size = (380, 50)

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
            text=name,
            flags=HALIGN | RT_VALIGN_CENTER))
    return res


# config class
class vavoo_config(Screen, ConfigListScreen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = join(skin_path, 'vavoo_config.xml')
        if file_exists('/var/lib/dpkg/status'):
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
        self['version'].setText('V.' + currversion)

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

    def save(self):
        if self["config"].isChanged():
            for x in self["config"].list:
                x[1].save()
            if self.v6 != cfg.ipv6.value:
                self.ipv6()
            configfile.save()
            if self.dnsmy():
                print('DNS CHECK')
            global FONTSTYPE
            FONTSE = str(cfg.fonts.getValue()) + '.ttf'
            FONTSTYPE = join(str(FNT_Path), str(FONTSE))
            print('FONTSTYPE cfg = ', FONTSTYPE)
            add_skin_font()
            bakk = str(cfg.back.getValue()) + '.png'
            add_skin_back(bakk)
            restartbox = self.session.openWithCallback(
                self.restartGUI,
                MessageBox,
                _(
                    "Settings saved successfully!\n"
                    "You need to restart the GUI\n"
                    "to apply the new configuration!\n"
                    "Do you want to Restart the GUI now?"
                ),
                MessageBox.TYPE_YESNO
            )
            restartbox.setTitle(_('Restart GUI now?'))
        else:
            self.close()

        configfile.load()

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
        if file_exists(pixmapx):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()
            self.picload.setPara(
                [size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])

            if file_exists("/var/lib/dpkg/status"):
                self.picload.startDecode(pixmapx, False)
            else:
                self.picload.startDecode(pixmapx, 0, 0, False)
            ptr = self.picload.getData()
            if ptr is not None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
                self['version'].setText('V.' + currversion)

    def loadDefaultImage(self):
        self.fldpng = resolveFilename(
            SCOPE_PLUGINS,
            "Extensions/{}/skin/pics/presplash.png".format('vavoo'))
        self.timer = eTimer()
        if file_exists('/var/lib/dpkg/status'):
            self.timer_conn = self.timer.timeout.connect(self.decodeImage)
        else:
            self.timer.callback.append(self.decodeImage)
        self.timer.start(500, True)
        self.timerx = eTimer()
        if file_exists('/var/lib/dpkg/status'):
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
        self["blue"] = Label()
        self['name'] = Label('Loading...')
        self['version'] = Label()

        # self._set_alignment_text()

    def _initialize_actions(self):
        """Initialize the actions for buttons."""
        actions = {
            'prevBouquet': self.chDown,
            'nextBouquet': self.chUp,
            'ok': self.ok,
            'menu': self.goConfig,
            'green': self.msgdeleteBouquets,
            # 'blue': self.arabic,
            'cancel': self.closex,
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
        ]
        self['actions'] = ActionMap(actions_list, actions, -1)

    def closex(self):
        print("DEBUG: Exit from plugin Calling ReloadBouquets after export")
        _reload_services_after_delay()
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

        self["version"].setText("V." + currversion)

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

    def _build_category_items(self, data):
        """Builds the category list"""
        categories = {}
        for entry in data:
            country = unquote(entry["country"]).strip("\r\n")
            name = unquote(entry["name"]).strip("\r\n")

            category_name = country + " -> " + self._extract_category(name)
            if category_name not in categories:
                categories[category_name] = country

        category_items = []
        for cat_name, country in categories.items():
            item = cat_name + "###" + self.url + "\n"
            category_items.append(item)

        category_items.sort()
        return category_items

    def _extract_category(self, channel_name):
        """Extracts the category from the channel name"""
        categories = {
            'Documentary': ['doc', 'documentar', 'history', 'science'],
            'Kids': ['kids', 'cartoon', 'disney', 'nickelodeon', 'baby'],
            'LifeStyle': ['lifestyle', 'fashion', 'cooking', 'travel', 'home'],
            'Movie': ['movie', 'film', 'cinema', 'premiere'],
            'Music': ['music', 'mtv', 'vh1', 'radio', 'hit'],
            'Nature': ['nature', 'animal', 'wild', 'national geographic'],
            'News': ['news', 'cnn', 'bbc', 'sky news', 'reuters'],
            'Sports': ['sport', 'football', 'futbol', 'tennis', 'f1', 'nba'],
            'Food': ['food', 'cooking', 'recipe'],
            'Football': ['football', 'futbol', 'soccer', 'premier league'],
            'Motor Sports': ['motor', 'f1', 'motogp', 'nascar']
        }

        channel_lower = channel_name.lower()
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in channel_lower:
                    return category

        return 'General'

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

    def _build_country_items(self, data):
        items = []
        for entry in data:
            country = unquote(entry["country"]).strip("\r\n")
            if country not in self.items_tmp:
                self.items_tmp.append(country)
                item = str(country) + "###" + self.url + "\n"
                items.append(item)
        items.sort()
        return items

    def _build_cat_list(self, items):
        for item in items:
            parts = item.split("###")
            if len(parts) != 2:
                continue
            name, url = parts
            if name not in self.cat_list:
                self.cat_list.append(show_list(name, url))

    def show_categories_view(self):
        """Show only categories (without main countries)"""
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
            _("Remove all Vavoo Favorite Bouquet?"),
            MessageBox.TYPE_YESNO,
            timeout=5,
            default=True)

    def deleteBouquets(self, result):
        if result:
            try:
                removed_count = 0
                db = eDVBDB.getInstance()

                for fname in listdir(ENIGMA_PATH):
                    # Cerca TUTTI i file vavoo, inclusi cowntry
                    is_vavoo_file = (fname.startswith('userbouquet.vavoo_') or
                                     fname.startswith('subbouquet.vavoo_') or
                                     'vavoo' in fname.lower())

                    if is_vavoo_file and (
                            fname.endswith('.tv') or fname.endswith('.radio')):
                        bouquet_path = join(ENIGMA_PATH, fname)
                        print("[vavoo] Removing bouquet:", fname)

                        if fname.startswith('userbouquet.'):
                            try:
                                db.removeBouquet(bouquet_path)
                                removed_count += 1
                            except Exception as e:
                                print("Error with eDVBDB removal:", e)
                        else:
                            try:
                                remove(bouquet_path)
                                removed_count += 1
                            except Exception as e:
                                print("Error removing file:", e)

                self._clean_main_bouquet_files()

                favorite_path = join(PLUGIN_PATH, 'Favorite.txt')
                if file_exists(favorite_path):
                    remove(favorite_path)
                    print("Removed Favorite.txt")

                print("DEBUG: deleteBouquets Calling ReloadBouquets after export")
                _reload_services_after_delay()

                self.session.open(
                    MessageBox, _('Vavoo bouquets removed successfully!\n(%s files deleted)') %
                    removed_count, MessageBox.TYPE_INFO, timeout=5)

            except Exception as error:
                print("Error in deleteBouquets:", error)
                self.session.open(
                    MessageBox,
                    _('Error during removal process'),
                    MessageBox.TYPE_ERROR,
                    timeout=5)

    def _clean_main_bouquet_files(self):
        """Remove vavoo references from all bouquet files"""
        try:
            # Clean main bouquet files
            for fname in listdir(ENIGMA_PATH):
                if fname.startswith('bouquets.') and (
                        fname.endswith('.tv') or fname.endswith('.radio')):
                    bouquet_file = join(ENIGMA_PATH, fname)

                    if file_exists(bouquet_file):
                        with open(bouquet_file, 'r') as f:
                            content = f.read()

                        # Remove lines containing vavoo
                        lines = content.split('\n')
                        new_lines = [
                            line for line in lines if 'vavoo' not in line.lower()]

                        if len(new_lines) != len(lines):
                            with open(bouquet_file, 'w') as f:
                                f.write('\n'.join(new_lines))
                            print("Cleaned vavoo from:", fname)
        except Exception as e:
            print("Error in _clean_main_bouquet_files:", e)

    def goConfig(self):
        self.session.open(vavoo_config)

    def info(self):
        aboutbox = self.session.open(
            MessageBox, _(
                "%s\n\n\nThanks:\n@KiddaC\n@oktus\nQu4k3\nAll staff Linuxsat-support.com\n"
                "Corvoboys - Forum\n\nThis plugin is free,\nno stream direct on server\n"
                "but only free channel found on the net") %
            desc_plugin, MessageBox.TYPE_INFO)
        aboutbox.setTitle(_('Info Vavoo'))

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

        if float(currversion) < float(remote_version):
            new_version = remote_version
            new_changelog = remote_changelog
            self.session.openWithCallback(
                self.install_update,
                MessageBox,
                _("New version %s is available.\n\nChangelog: %s \n\nDo you want to install it now?") %
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
        self["blue"] = Label()
        self['name'] = Label('Loading ...')
        self['version'] = Label()

        # self._set_alignment_text()

    def _initialize_actions(self):
        """Initialize the actions for buttons."""
        self["actions"] = ActionMap(
            [
                "MenuActions",
                "OkCancelActions",
                "DirectionActions",
                "InfobarEPGActions",
                "ColorActions"
            ],
            {
                "prevBouquet": self.chDown,
                "nextBouquet": self.chUp,
                "ok": self.ok,
                "green": self.message1,
                "yellow": self.search_vavoo,
                # "blue": self.arabic,
                "cancel": self.backhome,
                "menu": self.goConfig,
                "info": self.info,
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
                for entry in all_data:
                    country = unquote(entry["country"]).strip("\r\n")
                    name_channel = unquote(entry["name"]).strip("\r\n")
                    ids = entry["id"]

                    if not self._matches_selection(country, self.name):
                        continue

                    ids = str(ids).replace(
                        ':',
                        '').replace(
                        ' ',
                        '').replace(
                        ',',
                        '')
                    url = str(server) + '/live2/play/' + ids + '.ts'
                    name_channel = vUtils.decodeHtml(name_channel)
                    name_channel = vUtils.rimuovi_parentesi(name_channel)

                    item = name_channel + "###" + url + '\n'
                    items.append(item)

                items.sort()
                self.itemlist = items

                self._create_list_directly(items)

                self.update_menu()

        except Exception as error:
            print('Error:', error)
            trace_error()
            self['name'].setText('Error')

        self['version'].setText('V.' + currversion)

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
        # If user selected main country (without ➾)
        if "➾" not in selected_name:
            # Show all channels from that country, including categories
            return country_field.startswith(selected_name)
        else:
            # User selected specific category
            return country_field == selected_name

    def _matches_category(self, channel_name, category):
        """Checks whether a channel belongs to a category"""
        channel_lower = channel_name.lower()
        category_lower = category.lower()

        category_keywords = {
            'documentary': ['doc', 'documentar', 'history', 'science'],
            'kids': ['kids', 'cartoon', 'disney', 'nickelodeon', 'baby'],
            'lifestyle': ['lifestyle', 'fashion', 'cooking', 'travel', 'home'],
            'movie': ['movie', 'film', 'cinema', 'premiere'],
            'music': ['music', 'mtv', 'vh1', 'radio', 'hit'],
            'nature': ['nature', 'animal', 'wild', 'national geographic'],
            'news': ['news', 'cnn', 'bbc', 'sky news', 'reuters'],
            'sports': ['sport', 'football', 'futbol', 'tennis', 'f1', 'nba'],
            'food': ['food', 'cooking', 'recipe'],
            'football': ['football', 'futbol', 'soccer', 'premier league'],
            'motor sports': ['motor', 'f1', 'motogp', 'nascar']
        }

        if category_lower in category_keywords:
            for keyword in category_keywords[category_lower]:
                if keyword in channel_lower:
                    return True

        return category_lower in channel_lower

    def ok(self):
        try:
            i = self['menulist'].getSelectedIndex()
            self.currentindex = i
            selection = self['menulist'].l.getCurrentSelection()
            if selection is not None:
                item = self.cat_list[i][0]
                name = item[0]
                url = item[1]
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

    def message0(self, name, url, response):
        name = self.name
        self.url = url
        filenameout = ENIGMA_PATH + '/userbouquet.vavoo_%s.tv' % name.lower()
        if file_exists(filenameout):
            self.message3(name, self.url, False)
        else:
            self.message2(name, self.url, False)

    def message1(self, answer=None):
        if answer is None:
            name = self.name
            # Check both normal bouquet and container bouquet
            filename_normal = join(
                ENIGMA_PATH,
                'userbouquet.vavoo_%s.tv' %
                name.lower().replace(
                    ' ',
                    '_'))
            filename_container = join(
                ENIGMA_PATH,
                'userbouquet.vavoo_%s_cowntry.tv' %
                name.lower().replace(
                    ' ',
                    '_'))

            # Check if at least one exists
            bouquet_exists = file_exists(
                filename_normal) or file_exists(filename_container)

            if bouquet_exists:
                # Bouquet exists, ask user what to do
                self.session.openWithCallback(
                    self.message4,
                    MessageBox,
                    _(
                        'Bouquet already exists!\n\n'
                        'Do you want to:\n'
                        '• UPDATE existing bouquet (Yes)\n'
                        '• REMOVE and create new (No)\n'
                        '• CANCEL operation (Cancel)'
                    ),
                    MessageBox.TYPE_YESNOCANCEL
                )
            else:
                # New bouquet, proceed directly
                self.message2(self.name, self.url, True)
        elif answer is True:
            # Yes - update existing bouquet
            self.message3(self.name, self.url, True)
        elif answer is False:
            # No - remove existing and create new
            self._remove_existing_bouquet()
            self.message2(self.name, self.url, True)
        # If answer is None (Cancel), do nothing

    def message2(self, name, url, response):
        # Get the main instance to check current view
        main_instance = None
        try:
            for screen in self.session.dialog_stack:
                if hasattr(screen, 'current_view'):
                    main_instance = screen
                    break
        except BaseException:
            pass

        print("DEBUG message2:")
        print("   name:", name)
        print("   main_instance:", main_instance is not None)
        if main_instance:
            print(
                "   current_view:",
                getattr(
                    main_instance,
                    'current_view',
                    'NOT FOUND'))

        # Determine export type based on current view AND content
        if "➾" in name:
            # Single category - always flat
            export_type = "flat"
        else:
            # Main country - check if we want hierarchical or flat
            if main_instance and hasattr(main_instance, 'current_view'):
                if main_instance.current_view == "categories":
                    export_type = "hierarchical"
                else:
                    export_type = "flat"
            else:
                # Fallback
                export_type = "flat"

        print("   FINAL export_type:", export_type)

        _update_favorite_file(name, url, export_type)

        ch = convert_bouquet(cfg.services.value, name, url, export_type)

        if int(ch) > 0:
            if response is True:
                localtime = time.asctime(time.localtime(time.time()))
                cfg.last_update.value = localtime
                cfg.last_update.save()
                print("DEBUG: message2 Calling ReloadBouquets after export")
                _reload_services_after_delay()
                self.last_export_time = time.time()

            _session.open(
                MessageBox,
                _('bouquets reloaded..\nWith %s channel') %
                str(ch),
                MessageBox.TYPE_INFO,
                timeout=10)

        else:
            _session.open(
                MessageBox,
                _('Download Error'),
                MessageBox.TYPE_INFO,
                timeout=5)

    def message3(self, name, url, response):
        """Update existing bouquet"""
        sig = vUtils.getAuthSignature()
        app = str(sig)
        if app:
            # Try first with normal bouquet, then with container
            name_safe = name.lower().replace(' ', '_')
            filename_normal = join(
                PLUGIN_PATH,
                'list/userbouquet.vavoo_%s.tv' %
                name_safe)
            filenameout_normal = join(
                ENIGMA_PATH,
                'userbouquet.vavoo_%s.tv' %
                name_safe)

            filename_container = join(
                PLUGIN_PATH,
                'list/userbouquet.vavoo_%s_cowntry.tv' %
                name_safe)
            filenameout_container = join(
                ENIGMA_PATH,
                'userbouquet.vavoo_%s_cowntry.tv' %
                name_safe)

            # Determine which file exists
            source_file = None
            dest_file = None

            if file_exists(filename_normal):
                source_file = filename_normal
                dest_file = filenameout_normal
                print("Updating normal bouquet: " + name)
            elif file_exists(filename_container):
                source_file = filename_container
                dest_file = filenameout_container
                print("Updating container bouquet: " + name)
            else:
                # If none exists, create new
                print("Source bouquet file not found, creating new one...")
                self.message2(name, url, response)
                return

            key = None
            ch = 0

            try:
                with open(source_file, "rt") as fin:
                    data = fin.read()
                    regexcat = '#SERVICE.*?vavoo_auth=(.+?)#User'
                    match = compile(regexcat, DOTALL).findall(data)
                    for found_key in match:
                        key = str(found_key)
                        ch += 1

                with open(source_file, 'r') as f:
                    newlines = []
                    for line in f.readlines():
                        newlines.append(line.replace(key, app))

                # Ensure the directory exists before writing
                makedirs(dirname(dest_file), exist_ok=True)

                with open(dest_file, 'w') as f:
                    for line in newlines:
                        f.write(line)

                if response is True:
                    localtime = time.asctime(time.localtime(time.time()))
                    cfg.last_update.value = localtime
                    cfg.last_update.save()
                    self.session.open(
                        MessageBox, _('Bouquet updated successfully!\nWith %s channels') %
                        str(ch), MessageBox.TYPE_INFO, timeout=5)

            except Exception as e:
                print("Error updating bouquet:", e)
                # Fallback to normal export
                self.message2(name, url, response)

            print("DEBUG: message3 Calling ReloadBouquets after export")
            _reload_services_after_delay()

    def message4(self, answer=None):
        # This method might not be needed anymore with the simplified flow above
        # You can remove it or keep it for backward compatibility
        if answer is None:
            self.session.openWithCallback(self.message4, MessageBox, _(
                'The bouquet already exists. Update it with current channels?'))
        elif answer:
            self.message3(self.name, self.url, True)
        else:
            # User doesn't want to update, do nothing
            pass

    def _remove_existing_bouquet(self):
        """Remove existing bouquet files for both normal and container bouquets"""
        name = self.name
        try:
            # Remove normal bouquet
            bouquet_file_normal = join(
                ENIGMA_PATH, 'userbouquet.vavoo_%s.tv' %
                name.lower().replace(
                    ' ', '_'))
            if file_exists(bouquet_file_normal):
                remove(bouquet_file_normal)
                print(
                    "Removed normal bouquet: userbouquet.vavoo_%s.tv" %
                    name.lower())

            # Remove container bouquet
            bouquet_file_container = join(
                ENIGMA_PATH,
                'userbouquet.vavoo_%s_cowntry.tv' %
                name.lower().replace(
                    ' ',
                    '_'))
            if file_exists(bouquet_file_container):
                remove(bouquet_file_container)
                print(
                    "Removed container bouquet: userbouquet.vavoo_%s_cowntry.tv" %
                    name.lower())

            # Remove all related subbouquets
            country_safe = name.lower().replace(' ', '_')
            for fname in listdir(ENIGMA_PATH):
                if fname.startswith(
                    'subbouquet.vavoo_%s_' %
                        country_safe) and fname.endswith('.tv'):
                    subbouquet_file = join(ENIGMA_PATH, fname)
                    remove(subbouquet_file)
                    print("Removed subbouquet: " + fname)

            # Clean main bouquet files from references
            self._clean_main_bouquet_files()

            # Remove from favorites list
            favorite_file = join(PLUGIN_PATH, 'Favorite.txt')
            if file_exists(favorite_file):
                remove(favorite_file)

            print("Removed all existing bouquet files for: " + name)

        except Exception as e:
            print("Error removing bouquet: " + str(e))

    def search_vavoo(self):
        self.session.openWithCallback(
            self.filterM3u,
            VirtualKeyBoard,
            title=_("Filter this category..."),
            text='')

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

    def info(self):
        aboutbox = self.session.open(
            MessageBox,
            _('%s\n\n\nThanks:\n@KiddaC\n@oktus\nQu4k3\nAll staff Linuxsat-support.com\nCorvoboys - Forum\n\nThis plugin is free,\nno stream direct on server\nbut only free channel found on the net') %
            desc_plugin,
            MessageBox.TYPE_INFO)
        aboutbox.setTitle(_('Info Vavoo'))

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

        print("DEBUG: backhome Calling ReloadBouquets after export")
        _reload_services_after_delay()
        self.close()


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
            # if config.usage.show_infobar_on_zap.value:
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
        self.is_streaming = False  # Added here
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
        self.is_streaming = True  # Added here
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
        self.is_streaming = False  # Reset here

        if isfile("/tmp/hls.avi"):
            remove("/tmp/hls.avi")
        self.session.nav.stopService()
        self.session.nav.playService(self.srefInit)

        aspect_manager.restore_aspect()  # Restore aspect on exit
        self.close()

    def leavePlayer(self):
        self.stopStream()
        self.close()


def _add_to_main_bouquet(bouquet_name, bouquet_type):
    """Add bouquet reference to main bouquet file"""
    main_bouquet_path = join(ENIGMA_PATH, "bouquets.%s" % bouquet_type.lower())

    # Check if already exists
    try:
        with open(main_bouquet_path, 'r') as f:
            content = f.read()
    except BaseException:
        content = ""

    bouquet_line = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet' % bouquet_name

    if bouquet_line not in content:
        with open(main_bouquet_path, 'a') as f:
            f.write(bouquet_line + '\n')
        print("✓ Added %s to main bouquet file" % bouquet_name)

        # Reload bouquets after adding to main bouquet
        print("DEBUG: _add_to_main_bouquet Calling ReloadBouquets after export")
        _reload_services_after_delay()


def convert_bouquet(service, name, url, export_type="flat"):
    """
    Convert bouquet with choice between flat or hierarchical structure
    """
    sig = vUtils.getAuthSignature()
    app = "?n=1&b=5&vavoo_auth=%s#User-Agent=VAVOO/2.6" % str(sig)
    bouquet_type = "radio" if "radio" in name.lower() else "tv"
    separators = ["➾", "⟾", "->", "→"]
    has_separator = any(sep in name for sep in separators)
    bouquet_type = "radio" if "radio" in name.lower() else "tv"
    sig = vUtils.getAuthSignature()
    app = "?n=1&b=5&vavoo_auth=%s#User-Agent=VAVOO/2.6" % str(sig)

    if has_separator:
        print("CREATING SINGLE CATEGORY + PARENT:", name)

        # 1. Create sub-bouquet for the category
        ch_count = _create_category_bouquet(
            name, url, service, app, bouquet_type)

        # 2. Create/update parent bouquet with ONLY this category
        country_name = None
        for sep in separators:
            if sep in name:
                parts = name.split(sep)
                if len(parts) >= 1:
                    country_name = parts[0].strip()
                    break

        if country_name:
            # Pass only the current category, not all categories
            _create_or_update_container_bouquet(
                country_name, [name], bouquet_type)

        # Reload bouquets at the end
        print("DEBUG: convert_bouquet Calling ReloadBouquets after export")
        _reload_services_after_delay()

        return ch_count
    else:
        print("CREATING HIERARCHICAL FOR COUNTRY:", name)
        result = _create_hierarchical_bouquet(
            name, url, service, app, bouquet_type)

        # Reload bouquets at the end
        print("DEBUG: convert_bouquet Calling ReloadBouquets after export")
        _reload_services_after_delay()

        return result


def _prepare_bouquet_filenames(name, bouquet_type):
    name_file = sub(r'[<>:"/\\|?*, ]', '_', str(name))
    name_file = sub(r'\d+:\d+:[\d.]+', '_', name_file)
    name_file = sub(r'_+', '_', name_file)
    # Remove any remaining special characters
    name_file = sub(r'[^a-zA-Z0-9_]', '', name_file)
    bouquet_name = "userbouquet.vavoo_%s.%s" % (
        name_file.lower(), bouquet_type.lower())
    return name_file, bouquet_name


def _write_bouquet_files(path1, tplst):
    try:
        with open(path1, "r") as f:
            f_content = f.read()
    except (IOError, OSError):
        f_content = ""
    with open(path1, "a+") as f:
        for item in tplst:
            if item not in f_content:
                f.write("%s\n" % item)


def _ensure_bouquet_listed(path2, bouquet_name, bouquet_type):
    in_bouquets = False
    try:
        with open("/etc/enigma2/bouquets.%s" % bouquet_type.lower(), "r") as f:
            for line in f:
                if bouquet_name in line:
                    in_bouquets = True
    except (IOError, OSError):
        pass
    if not in_bouquets:
        with open(path2, "a+") as f:
            f.write(
                '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\n' %
                bouquet_name)


def _create_flat_bouquet(name, url, service, app, bouquet_type):
    """Create flat bouquet directly from JSON data (no .m3u files)"""
    try:
        content = vUtils.getUrl(url)
        if PY3:
            content = vUtils.ensure_str(content)
        all_data = loads(content)

        separators = ["➾", "⟾", "->", "→"]
        has_separator = any(sep in name for sep in separators)

        if has_separator:
            for sep in separators:
                if sep in name:
                    country_part = name.split(sep)[0].strip()
                    category_part = name.split(sep)[1].strip()
                    safe_name = "%s_%s" % (country_part.lower().replace(
                        ' ', '_'), category_part.lower().replace(' ', '_'))
                    bouquet_name = "subbouquet.vavoo_%s.%s" % (
                        safe_name, bouquet_type)
                    display_name = "%s - %s" % (country_part, category_part)
                    break
        else:
            safe_name = name.lower().replace(' ', '_')
            bouquet_name = "userbouquet.vavoo_%s.%s" % (
                safe_name, bouquet_type)
            display_name = name

        bouquet_path = join(ENIGMA_PATH, bouquet_name)
        main_bouquet_path = join(
            ENIGMA_PATH,
            "bouquets." +
            bouquet_type.lower())

        with open(PLUGIN_PATH + "/Favorite.txt", "w") as r:
            r.write(str(name) + "###" + str(url))

        print("Creating Bouquet from JSON: %s" % name)

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
            print("No channels found for: %s" % name)
            return 0

        content_lines = [
            "#NAME %s (%s)" % (display_name, bouquet_type.upper()),
            "#SERVICE 1:64:0:0:0:0:0:0:0:0::%s" % display_name,
            "#DESCRIPTION --- %s ---" % display_name
        ]

        ch_count = 0
        for entry in filtered_data:
            name_channel = unquote(entry["name"]).strip("\r\n")
            ids = str(
                entry["id"]).replace(
                ':',
                '').replace(
                ' ',
                '').replace(
                ',',
                '')

            url_channel = "http://vavoo.to/live2/play/" + ids + '.ts' + app
            name_channel = vUtils.decodeHtml(name_channel)
            name_channel = vUtils.rimuovi_parentesi(name_channel)

            tag = "2" if bouquet_type.upper() == "RADIO" else "1"
            url_encoded = url_channel.replace(":", "%3a")

            service_line = "#SERVICE %s:0:%s:0:0:0:0:0:0:0:%s:%s" % (
                service, tag, url_encoded, name_channel)
            desc_line = "#DESCRIPTION %s" % name_channel

            content_lines.append(service_line)
            content_lines.append(desc_line)
            ch_count += 1

        # Write bouquet file
        with open(bouquet_path, 'w') as f:
            f.write('\n'.join(content_lines))

        # Add to main bouquet if it's a userbouquet (not subbouquet)
        if bouquet_name.startswith("userbouquet."):
            _ensure_bouquet_listed(
                main_bouquet_path, bouquet_name, bouquet_type)

        # Reload bouquets after creation
        # _reload_services_after_delay()

        print(
            "Created bouquet: %s with %s channels" %
            (bouquet_name, ch_count))
        return ch_count

    except Exception as error:
        print("Error creating bouquet:", error)
        trace_error()
        return 0


def _create_hierarchical_bouquet(
        country_name,
        url,
        service,
        app,
        bouquet_type):
    """Create hierarchical bouquet structure with only exported categories"""
    try:
        # Get all data to find categories for this country
        content = vUtils.getUrl(url)
        if PY3:
            content = vUtils.ensure_str(content)
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
                country_name, url, service, app, bouquet_type)

        # Create category sub-bouquets (CHILDREN) and track which ones were
        # actually created
        exported_categories = []
        total_ch = 0
        for category in sorted(all_categories):
            ch_count = _create_category_bouquet(
                category, url, service, app, bouquet_type)
            if ch_count > 0:  # Only add categories that were successfully exported
                exported_categories.append(category)
                total_ch += ch_count

        # Create container bouquet (PARENT) with ONLY exported categories
        if exported_categories:
            container_ch_count = _create_or_update_container_bouquet(
                country_name, exported_categories, bouquet_type)
        else:
            container_ch_count = 0

        return total_ch + container_ch_count

    except Exception as error:
        print("Error creating hierarchical bouquet:", error)
        trace_error()
        return _create_flat_bouquet(
            country_name, url, service, app, bouquet_type)


def _create_or_update_container_bouquet(
        country_name,
        exported_categories,
        bouquet_type):
    """Create or update the parent bouquet with only exported categories"""
    print("DEBUG: _create_or_update_container_bouquet called")
    print("DEBUG: country_name = " + country_name)
    print("DEBUG: exported_categories = " + str(exported_categories))

    container_name = "userbouquet.vavoo_%s_cowntry.%s" % (
        country_name.lower().replace(' ', '_'), bouquet_type)
    container_path = join(ENIGMA_PATH, container_name)

    separators = ["➾", "⟾", "->", "→"]

    # Read existing content or create new
    if file_exists(container_path):
        with open(container_path, 'r') as f:
            existing_content = f.read().splitlines()

        # Keep header lines and avoid duplicates
        content = []
        existing_subbouquets = set()

        for line in existing_content:
            if line.startswith(
                    '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "subbouquet.vavoo_'):
                import re
                match = re.search(r'FROM BOUQUET "([^"]+)"', line)
                if match:
                    existing_subbouquets.add(match.group(1))
                    content.append(line)
            else:
                content.append(line)
    else:
        # Create new content
        content = [
            "#NAME %s - Cowntry" % country_name,
            "#SERVICE 1:64:0:0:0:0:0:0:0:0::%s Categories" % country_name,
            "#DESCRIPTION --- %s Categories ---" % country_name
        ]
        existing_subbouquets = set()

    # Add ONLY exported categories
    for category in sorted(exported_categories):
        print("DEBUG: Processing category: " + category)
        category_part = None

        for sep in separators:
            if sep in category:
                parts = category.split(sep)
                if len(parts) >= 2:
                    category_part = parts[1].strip()
                    break

        if category_part is None:
            continue

        country_safe = country_name.lower().replace(' ', '_')
        category_safe = category_part.lower().replace(' ', '_')
        subbouquet_ref = "subbouquet.vavoo_%s_%s.%s" % (
            country_safe, category_safe, bouquet_type)

        if subbouquet_ref not in existing_subbouquets:
            content.append(
                '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet' %
                subbouquet_ref)
            print("DEBUG: Added subbouquet reference: " + subbouquet_ref)

    print("DEBUG: Final content lines: " + str(len(content)))

    # Write the updated content
    try:
        with open(container_path, 'w') as f:
            f.write('\n'.join(content))

        # Add container to main bouquet file (if not already present)
        _add_to_main_bouquet(container_name, bouquet_type)

        # Reload bouquets after creation/update
        print(
            "DEBUG: _create_or_update_container_bouquet Calling ReloadBouquets after export")
        _reload_services_after_delay()

        return 1
    except Exception as error:
        print("Error updating container bouquet:", error)
        return 0


def _create_category_bouquet(category_name, url, service, app, bouquet_type):
    """Create a sub-bouquet for a specific category directly from JSON"""
    try:
        content = vUtils.getUrl(url)
        if PY3:
            content = vUtils.ensure_str(content)
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

        country_safe = country_part.lower().replace(' ', '_')
        category_safe = category_part.lower().replace(' ', '_')
        subbouquet_name = "subbouquet.vavoo_%s_%s.%s" % (
            country_safe, category_safe, bouquet_type)
        subbouquet_path = join(ENIGMA_PATH, subbouquet_name)

        display_name = "%s - %s" % (country_part, category_part)

        content_lines = [
            "#NAME %s (%s)" % (display_name, bouquet_type.upper()),
            "#SERVICE 1:64:0:0:0:0:0:0:0:0::%s" % display_name,
            "#DESCRIPTION --- %s ---" % display_name
        ]

        ch_count = 0
        for entry in filtered_data:
            name_channel = unquote(entry["name"]).strip("\r\n")
            ids = str(
                entry["id"]).replace(
                ':',
                '').replace(
                ' ',
                '').replace(
                ',',
                '')

            # FIX: Use the configured server instead of the hardcoded
            # "http://vavoo.to"
            server_url = cfg.server.value
            if not server_url.startswith('http'):
                server_url = 'https://' + server_url

            url_channel = server_url + "/live2/play/" + ids + '.ts' + app
            name_channel = vUtils.decodeHtml(name_channel)
            name_channel = vUtils.rimuovi_parentesi(name_channel)

            tag = "2" if bouquet_type.upper() == "RADIO" else "1"
            url_encoded = url_channel.replace(":", "%3a")

            service_line = "#SERVICE %s:0:%s:0:0:0:0:0:0:0:%s:%s" % (
                service, tag, url_encoded, name_channel)
            desc_line = "#DESCRIPTION %s" % name_channel

            content_lines.append(service_line)
            content_lines.append(desc_line)
            ch_count += 1

            # Debug: print every 10 channels
            if ch_count % 10 == 0:
                print("   Added " + str(ch_count) + " channels so far...")

        # Write file
        with open(subbouquet_path, 'w') as f:
            f.write('\n'.join(content_lines))

        print(
            "Created sub-bouquet: " +
            subbouquet_name +
            " with " +
            str(ch_count) +
            " channels")

        try:
            from enigma import eServiceReference, eServiceCenter
            service_handler = eServiceCenter.getInstance()
            bouquet_ref = eServiceReference(
                eServiceReference.idFile,
                eServiceReference.isDirectory,
                "file://" + subbouquet_path
            )
            list = service_handler.list(bouquet_ref)
            if list:
                service_count = list.getNumberOfServices()
                print(
                    "DEBUG CRITICAL: Enigma2 reads " +
                    str(service_count) +
                    " services from bouquet")
            else:
                print("DEBUG CRITICAL: ERROR - Enigma2 CANNOT read the bouquet file!")

            return ch_count

        except Exception as e:
            print("DEBUG CRITICAL: Error testing bouquet: " + str(e))

    except Exception as e:
        print("DEBUG CRITICAL: Error2 testing bouquet: " + str(e))


def _update_favorite_file(name, url, export_type):
    """Update Favorite.txt with all exported bouquets and their settings"""
    favorite_path = join(PLUGIN_PATH, 'Favorite.txt')

    # Read existing bouquets
    existing_bouquets = {}
    if file_exists(favorite_path):
        try:
            with open(favorite_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            bouq_name = parts[0]
                            # Save all fields: name|url|export_type|timestamp
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
        # if wake - now < 60:
        if abs(wake - now) < 60:
            try:
                self.startMain()
                constant = 60
                # self.update()
                localtime = time.asctime(time.localtime(time.time()))
                cfg.last_update.value = localtime
                cfg.last_update.save()
            except Exception as error:
                print(error)
                trace_error()
        self.update(constant)

    def startMain(self):
        favorite_channel = join(PLUGIN_PATH, 'Favorite.txt')

        if not file_exists(favorite_channel):
            print("Favorite.txt not found - no bouquets to update")
            return

        try:
            bouquets_to_update = []
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

            # Update all bouquets using their export_type
            for name, url, export_type in bouquets_to_update:
                print("Updating bouquet: " + name +
                      " (type: " + export_type + ")")
                ch = convert_bouquet(
                    cfg.services.value, name, url, export_type)
                if ch > 0:
                    print("Successfully updated: " + name +
                          " (" + str(ch) + " channels)")
                    # Update timestamp
                    _update_favorite_file(name, url, export_type)
                else:
                    print("Failed to update: " + name)

            localtime = time.asctime(time.localtime(time.time()))
            cfg.last_update.value = localtime
            cfg.last_update.save()

        except Exception as e:
            print('Error during scheduled update:', e)


def check_configuring():
    """Check for new config values for auto start"""
    if cfg.autobouquetupdate.value is True:
        if auto_start_timer is not None:
            auto_start_timer.update()  # Call update on the instance
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
    if file_exists(join(BackPath, str(bakk))):
        baknew = join(BackPath, str(bakk))
        cmd = 'cp -f ' + str(baknew) + ' ' + BackPath + '/default.png'
        system(cmd)
        system('sync')


def add_skin_font():
    print('**********addFont')
    from enigma import addFont
    # global FONTSTYPE
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
        if file_exists('/tmp/vavoo.log'):
            remove('/tmp/vavoo.log')
        add_skin_font()
        session.open(startVavoo)
    except Exception as error:
        print('error as:', error)
        trace_error()


def Plugins(**kwargs):
    plugin_name = title_plug
    plugin_description = _('Vavoo Stream Live')
    plugin_icon = pluglogo

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
