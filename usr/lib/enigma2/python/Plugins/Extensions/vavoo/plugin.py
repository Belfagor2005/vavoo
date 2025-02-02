#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
****************************************
*        coded by Lululla              *
*             26/04/2024               *
* thank's to @oktus for image screen   *
****************************************
# ---- thank's Kiddac for support ---- #
# Info Linuxsat-support.com & corvoboys.org
"""
from __future__ import print_function

# Local application/library-specific imports
from . import _
from . import vUtils
from .Console import Console
# Standard library imports
# Enigma2 components
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import (MultiContentEntryPixmapAlphaTest, MultiContentEntryText)
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import (ServiceEventTracker, InfoBarBase)
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
    NoSave,
)
from Plugins.Plugin import PluginDescriptor
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
from Tools.Directories import (SCOPE_PLUGINS, resolveFilename)
from enigma import (
    RT_VALIGN_CENTER,
    RT_HALIGN_LEFT,
    RT_HALIGN_RIGHT,
    eListboxPythonMultiContent,
    eServiceReference,
    eTimer,
    iPlayableService,
    iServiceInformation,
    getDesktop,
    ePicLoad,
    gFont,
    loadPNG,
)
from datetime import datetime
from os import path as os_path
from os.path import exists as file_exists
from random import choice
from requests.adapters import HTTPAdapter, Retry
from six import text_type
import codecs
import json
import os
import re
import requests
import ssl
import sys
import time
import traceback

global HALIGN
_session = None
tmlast = None
now = None
PY2 = False
PY3 = False
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


if sys.version_info >= (2, 7, 9):
    try:
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None


try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote


def ensure_str(text, encoding='utf-8', errors='strict'):
    if type(text) is str:
        return text
    if PY2:
        if isinstance(text, text_type):
            try:
                return text.encode(encoding, errors)
            except Exception:
                return text.encode(encoding, 'ignore')
    else:
        if isinstance(text, bytes):
            try:
                return text.decode(encoding, errors)
            except Exception:
                return text.decode(encoding, 'ignore')
    return text


# set plugin
currversion = '1.33'
title_plug = 'Vavoo'
desc_plugin = ('..:: Vavoo by Lululla v.%s ::..' % currversion)
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('vavoo'))
pluglogo = os_path.join(PLUGIN_PATH, 'plugin.png')
stripurl = 'aHR0cHM6Ly92YXZvby50by9jaGFubmVscw=='
keyurl = 'aHR0cDovL3BhdGJ1d2ViLmNvbS92YXZvby92YXZvb2tleQ=='
keyurl2 = 'aHR0cDovL3BhdGJ1d2ViLmNvbS92YXZvby92YXZvb2tleTI='
installer_url = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0JlbGZhZ29yMjAwNS92YXZvby9tYWluL2luc3RhbGxlci5zaA=='
developer_url = 'aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9CZWxmYWdvcjIwMDUvdmF2b28='
enigma_path = '/etc/enigma2/'
json_file = '/tmp/vavookey'
HALIGN = RT_HALIGN_LEFT
screenwidth = getDesktop(0).size()
screen_width = screenwidth.width()
regexs = '<a[^>]*href="([^"]+)"[^>]*><img[^>]*src="([^"]+)"[^>]*>'

try:
    from Components.UsageConfig import defaultMoviePath
    downloadfree = defaultMoviePath()
except:
    if os.path.exists("/usr/bin/apt-get"):
        downloadfree = ('/media/hdd/movie/')


# log
def trace_error():
    try:
        traceback.print_exc(file=sys.stdout)
        with open("/tmp/vavoo.log", "a", encoding='utf-8') as log_file:
            traceback.print_exc(file=log_file)
    except Exception as e:
        print("Failed to log the error:", e, file=sys.stderr)


myser = [("https://vavoo.to", "vavoo"), ("https://oha.to", "oha"), ("https://kool.to", "kool"), ("https://huhu.to", "huhu")]
mydns = [("None", "Default"), ("google", "Google"), ("coudfire", "Coudfire"), ("quad9", "Quad9")]
modemovie = [("4097", "4097")]
if file_exists("/usr/bin/gstplayer"):
    modemovie.append(("5001", "5001"))
if file_exists("/usr/bin/exteplayer3"):
    modemovie.append(("5002", "5002"))
if file_exists('/var/lib/dpkg/info'):
    modemovie.append(("8193", "8193"))


# back
global BackPath, FONTSTYPE, FNTPath  # maybe no..
BackfPath = os_path.join(PLUGIN_PATH, "skin")
if screen_width == 2560:
    BackPath = os_path.join(BackfPath, 'images_new')
    skin_path = os_path.join(BackfPath, 'wqhd')
elif screen_width == 1920:
    BackPath = os_path.join(BackfPath, 'images_new')
    skin_path = os_path.join(BackfPath, 'fhd')
elif screen_width <= 1280:
    BackPath = os_path.join(BackfPath, 'images')
    skin_path = os_path.join(BackfPath, 'hd')
else:
    BackPath = None
    skin_path = None

print('folder back: ', BackPath)


BakP = []
try:
    if file_exists(BackPath):
        for backName in os.listdir(BackPath):
            backNamePath = os_path.join(BackPath, backName)
            if backName.endswith(".png"):
                if backName.startswith("default"):
                    continue
                backName = backName[:-4]
                BakP.append((backName, backName))
except Exception as e:
    print(e)
print('final folder back: ', BackPath)
# BakP = sorted(BakP, key=lambda x: x[1])


# fonts
FNTPath = os_path.join(PLUGIN_PATH, "fonts")
fonts = []
try:
    if file_exists(FNTPath):
        for fontName in os.listdir(FNTPath):
            fontNamePath = os_path.join(FNTPath, fontName)
            if fontName.endswith(".ttf") or fontName.endswith(".otf"):
                fontName = fontName[:-4]
                fonts.append((fontName, fontName))
        fonts = sorted(fonts, key=lambda x: x[1])
except Exception as e:
    print(e)

# config section
config.plugins.vavoo = ConfigSubsection()
cfg = config.plugins.vavoo
cfg.autobouquetupdate = ConfigEnableDisable(default=False)
cfg.genm3u = NoSave(ConfigYesNo(default=False))
cfg.server = ConfigSelection(default="https://vavoo.to", choices=myser)
cfg.services = ConfigSelection(default='4097', choices=modemovie)
cfg.timetype = ConfigSelection(default="interval", choices=[("interval", _("interval")), ("fixed time", _("fixed time"))])
cfg.updateinterval = ConfigSelectionNumber(default=10, min=5, max=3600, stepwidth=5)
cfg.fixedtime = ConfigClock(default=46800)
cfg.last_update = ConfigText(default="Never")
cfg.stmain = ConfigYesNo(default=True)
cfg.ipv6 = ConfigEnableDisable(default=False)
cfg.dns = ConfigSelection(default="Default", choices=mydns)
cfg.fonts = ConfigSelection(default='vav', choices=fonts)
cfg.back = ConfigSelection(default='oktus', choices=BakP)
FONTSTYPE = FNTPath + '/' + cfg.fonts.value + '.ttf'
eserv = int(cfg.services.value)

# ipv6
if os_path.islink('/etc/rc3.d/S99ipv6dis.sh'):
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
except:
    lng = 'en'
    pass


def get_external_ip():
    try:
        return os.popen('curl -s ifconfig.me').readline()
    except:
        pass
    try:
        return requests.get('https://v4.ident.me').text
    except:
        pass
    try:
        return requests.get('https://api.ipify.org').text
    except:
        pass
    try:
        return requests.get('https://api.myip.com/').json()["ip"]
    except:
        pass
    try:
        return requests.get('https://checkip.amazonaws.com').text.strip()
    except:
        pass
    return None


def set_cache(key, data, timeout):
    """Salva i dati nella cache."""
    file_path = os_path.join(PLUGIN_PATH, key + '.json')
    try:
        with open(file_path, 'w') as cache_file:
            json.dump(convert_to_unicode(data), cache_file, indent=4)
    except Exception as e:
        print("Error saving cache: ", e)


def get_cache(key):
    file_path = os_path.join(PLUGIN_PATH, key + '.json')
    if os_path.exists(file_path) and os_path.getsize(file_path) > 0:
        try:
            with open(file_path, 'r', encoding='utf-8') as cache_file:
                data = json.load(cache_file)
                if data.get('sigValidUntil', 0) > int(time.time()):
                    if data.get('ip', "") == get_external_ip():
                        return data.get('value')
        except ValueError as e:
            print("Error decoding JSON from :", e)
        except Exception as e:
            print("Unexpected error reading cache file {file_path}:", e)
        os.remove(file_path)
    return None


def getAuthSignature():
    signfile = get_cache('signfile')
    if signfile:
        return signfile
    veclist = get_cache("veclist")
    if not veclist:
        veclist = requests.get("https://raw.githubusercontent.com/michaz1988/michaz1988.github.io/master/data.json").json()
        set_cache("veclist", veclist, timeout=3600)
    sig = None
    i = 0
    while not sig and i < 50:
        i += 1
        vec = {"vec": choice(veclist)}
        req = requests.post('https://www.vavoo.tv/api/box/ping2', data=vec).json()
        sig = req.get('signed') or req.get('data', {}).get('signed') or req.get('response', {}).get('signed')
    if sig:
        set_cache('signfile', convert_to_unicode(sig), timeout=3600)  # Assicurati che sig sia in formato Unicode
    return sig


def convert_to_unicode(data):
    if isinstance(data, str):
        return data.decode('utf-8')
    elif isinstance(data, dict):
        return {convert_to_unicode(k): convert_to_unicode(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_unicode(item) for item in data]
    return data


def Sig():
    '''
    watchedsignfile = get_cache('signfile')
    if watchedsignfile:
        return watchedsignfile
    '''
    sig = None
    xlist = [
        "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"]
    if not file_exists(json_file):
        myUrl = vUtils.b64decoder(keyurl)
        response = requests.get(myUrl)
        try:
            vecKeylist = response.json()
        except ValueError:
            print("Errore nella decodifica JSON, risposta non valida:", response.text)
            return None
        with open(json_file, "w") as f:
            if sys.version_info[0] < 3:
                vecKeylist = vecKeylist
            json.dump(vecKeylist, f, indent=2)

    elif os_path.exists(json_file) and os_path.getsize(json_file) > 0:
        with open(json_file, 'r') as f:
            try:
                vecs = json.load(f)
                vec = choice(vecs)
                headers = {'Content-Type': 'application/json'}
                json_data = '{"vec": "' + str(vec) + '"}'
                if PY3:
                    req = requests.post('https://www.vavoo.tv/api/box/ping2', headers=headers, data=json_data).json()
                else:
                    req = requests.post('https://www.vavoo.tv/api/box/ping2', headers=headers, verify=False, data=json_data).json()
                sig = req.get('signed') or req.get('data', {}).get('signed') or req.get('response', {}).get('signed')
            except ValueError as e:
                print("Error decoding JSON: ", e)
                vecs = []
    elif not sig:
        print('getWatchedSig')
        data = {"x": choice(xlist)}
        headers = {
            "user-agent": "Rokkr/1.8.3 (android)",
            "accept": "application/json",
            "content-type": "application/json; charset=utf-8",
            "accept-encoding": "gzip",
            "cookie": "lng=en"
        }
        if PY3:
            req = requests.post('https://www.rokkr.net/api/box/ping', json=data, headers=headers).json()
        else:
            req = requests.post('https://www.rokkr.net/api/box/ping', json=data, headers=headers, verify=False).json()
        # if PY3:
            # req = requests.post('https://www.vavoo.tv/api/box/ping2', json=data headers=headers).json()
        # else:
            # req = requests.post('https://www.vavoo.tv/api/box/ping2', json=data headers=headers, verify=False).json()
        if req.get('signed'):
            sig = req['signed']
        elif req.get('data', {}).get('signed'):
            sig = req['data']['signed']
        elif req.get('response', {}).get('signed'):
            sig = req['response']['signed']
    return sig


def loop_sig():
    while True:
        sig = None
        now = int(time.time())
        print('now=', str(now))
        last = tmlast
        print('last=', str(last))
        if now > last + 1200:
            print('go to sig....')
            sig = Sig()
        else:
            print('sleep time loop sig....')
            time.sleep(int(last + 1200 - now))
        return sig
    pass


# check server
def raises(url):
    try:
        retries = Retry(total=1, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retries)
        http = requests.Session()
        http.mount("http://", adapter)
        http.mount("https://", adapter)
        r = http.get(url, headers={'User-Agent': vUtils.RequestAgent()}, timeout=10, verify=False, stream=True, allow_redirects=False)
        r.raise_for_status()
        if r.status_code == requests.codes.ok:
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


def rimuovi_parentesi(testo):
    return re.sub(r'\([^)]*\)', '', testo)


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


country_codes = {
    "Albania": "al",
    "Arabia": "sa",
    "Balkans": "bk",
    "Bulgaria": "bg",
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


def show_list(name, link):
    global HALIGN
    HALIGN = HALIGN
    res = [(name, link)]
    default_icon = os_path.join(PLUGIN_PATH, 'skin/pics/vavoo_ico.png')
    country_code = country_codes.get(name, None)
    if country_code:
        country_code = country_code + '.png'
        pngx = os_path.join(PLUGIN_PATH, 'skin/cowntry', country_code)
    else:
        pngx = default_icon
    if not os_path.isfile(pngx):
        pngx = default_icon
    icon_pos = (10, 10) if screen_width == 2560 else (10, 5)
    icon_size = (60, 40)
    if screen_width == 2560:
        text_pos = (90, 0)
        text_size = (750, 60)
    elif screen_width == 1920:
        text_pos = (80, 0)
        text_size = (540, 50)
    else:
        text_pos = (85, 0)
        text_size = (380, 50)
    res.append(MultiContentEntryPixmapAlphaTest(pos=icon_pos, size=icon_size, png=loadPNG(pngx)))
    res.append(MultiContentEntryText(pos=text_pos, size=text_size, font=0, text=name, flags=HALIGN | RT_VALIGN_CENTER))
    return res


# config class
class vavoo_config(Screen, ConfigListScreen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os_path.join(skin_path, 'vavoo_config.xml')
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
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self.createSetup()
        self.v6 = cfg.ipv6.getValue()
        self.showhide()
        self.onLayoutFinish.append(self.layoutFinished)

    def update_status(self):
        if cfg.autobouquetupdate:
            self['statusbar'].setText(_("Last channel update: %s") % cfg.last_update.value)

    def layoutFinished(self):
        self.setTitle(self.setup_title)
        self['version'].setText('V.' + currversion)

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        indent = "- "
        self.list.append(getConfigListEntry(_("Generate .m3u files (Ok for Exec)"), cfg.genm3u, _("Generate .m3u files and save to device %s.") % downloadfree))
        self.list.append(getConfigListEntry(_("Server for Player Used"), cfg.server, _("Server for player.\nNow %s") % cfg.server.value))
        self.list.append(getConfigListEntry(_("Movie Services Reference"), cfg.services, _("Configure service Reference Iptv-Gstreamer-Exteplayer3")))
        self.list.append(getConfigListEntry(_("Select DNS Server"), cfg.dns, _("Configure Dns Server for Box.")))
        self.list.append(getConfigListEntry(_("Select Background"), cfg.back, _("Configure Main Background Image.")))
        self.list.append(getConfigListEntry(_("Select Fonts"), cfg.fonts, _("Configure Fonts.\nEg:Arabic or other language.")))
        self.list.append(getConfigListEntry(_("Ipv6 State Of Lan (On/Off)"), cfg.ipv6, _("Active or Disactive lan Ipv6.\nNow %s") % cfg.ipv6.value))
        self.list.append(getConfigListEntry(_("Scheduled Bouquet Update:"), cfg.autobouquetupdate, _("Active Automatic Bouquet Update")))
        if cfg.autobouquetupdate.value is True:
            self.list.append(getConfigListEntry(indent + _("Schedule type:"), cfg.timetype, _("At an interval of hours or at a fixed time")))
            if cfg.timetype.value == "interval":
                self.list.append(getConfigListEntry(2 * indent + _("Update interval (minutes):"), cfg.updateinterval, _("Configure every interval of minutes from now")))
            if cfg.timetype.value == "fixed time":
                self.list.append(getConfigListEntry(2 * indent + _("Time to start update:"), cfg.fixedtime, _("Configure at a fixed time")))
        self.list.append(getConfigListEntry(_('Link in Main Menu'), cfg.stmain, _("Link in Main Menu")))
        self["config"].list = self.list
        self["config"].l.setList(self.list)
        self.setInfo()

    def gnm3u(self):
        sel = self["config"].getCurrent()[1]
        if sel and sel == cfg.genm3u:
            self.session.openWithCallback(self.generate_m3u, MessageBox, _("Generate .m3u files and save to device %s?") % downloadfree, MessageBox.TYPE_YESNO, timeout=10, default=True)

    def generate_m3u(self, result):
        if result:
            if not os.path.exists(downloadfree):
                os.makedirs(downloadfree)
            cmd = "python {} {}".format(os_path.join(PLUGIN_PATH, 'Vavoo_m3u.py'), downloadfree)
            from enigma import eConsoleAppContainer
            self.container = eConsoleAppContainer()
            try:
                self.container.appClosed.append(self.runFinished)
            except:
                self.container.appClosed_conn = self.container.appClosed.connect(self.runFinished)

            self.container.execute(cmd)

            cfg.genm3u.setValue(0)
            cfg.genm3u.save()

            self.session.open(MessageBox, _("All .m3u files have been generated!"),  MessageBox.TYPE_INFO, timeout=4)

    def runFinished(self, retval):
        self["description"].setText("Generation completed. Files saved to %s." % downloadfree)

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
        if os_path.islink('/etc/rc3.d/S99ipv6dis.sh'):
            self.session.openWithCallback(self.ipv6check, MessageBox, _("Ipv6 [Off]?"), MessageBox.TYPE_YESNO, timeout=5, default=True)
        else:
            self.session.openWithCallback(self.ipv6check, MessageBox, _("Ipv6 [On]?"), MessageBox.TYPE_YESNO, timeout=5, default=True)

    def ipv6check(self, result):
        if result:
            if os_path.islink('/etc/rc3.d/S99ipv6dis.sh'):
                os.unlink('/etc/rc3.d/S99ipv6dis.sh')
                cfg.ipv6.setValue(False)
            else:
                os.system("echo '#!/bin/bash")
                os.system("echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6' > /etc/init.d/ipv6dis.sh")
                os.system("chmod 755 /etc/init.d/ipv6dis.sh")
                os.system("ln -s /etc/init.d/ipv6dis.sh /etc/rc3.d/S99ipv6dis.sh")
                cfg.ipv6.setValue(True)
            cfg.ipv6.save()

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()
        self['green'].instance.setText(_('Save') if self['config'].isChanged() else '- - - -')

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
            FONTSTYPE = os_path.join(str(FNTPath), str(FONTSE))
            print('FONTSTYPE cfg = ', FONTSTYPE)
            add_skin_font()
            bakk = str(cfg.back.getValue()) + '.png'
            add_skin_back(bakk)
            restartbox = self.session.openWithCallback(self.restartGUI, MessageBox, _('Settings saved successfully !\nyou need to restart the GUI\nto apply the new configuration!\nDo you want to Restart the GUI now?'), MessageBox.TYPE_YESNO)
            restartbox.setTitle(_('Restart GUI now?'))
        else:
            self.close()

    def dnsmy(self):
        valuedns = cfg.dns.value
        print(valuedns)
        valdns = False
        if str(valuedns) != 'None':
            self.cmd1 = None
            if 'google' in valuedns:
                self.cmd1 = os_path.join(PLUGIN_PATH + 'resolver/', 'DnsGoogle.sh')
            elif 'couldfire' in valuedns:
                self.cmd1 = os_path.join(PLUGIN_PATH + 'resolver/', 'DnsCloudflare.sh')
            elif 'quad9' in valuedns:
                self.cmd1 = os_path.join(PLUGIN_PATH + 'resolver/', 'DnsQuad9.sh')
            if self.cmd1 is not None:
                try:
                    from os import access, X_OK
                    if not access(self.cmd1, X_OK):
                        os.chmod(self.cmd1, 493)
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
                self.session.openWithCallback(self.extnok, MessageBox, _("Really close without saving settings?"))
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
        skin = os_path.join(skin_path, 'Plgnstrt.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self["poster"] = Pixmap()
        self["version"] = Label()
        self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.clsgo, 'cancel': self.clsgo}, -1)
        self.onLayoutFinish.append(self.loadDefaultImage)

    def decodeImage(self):
        pixmapx = self.fldpng
        if file_exists(pixmapx):
            size = self['poster'].instance.size()
            self.picload = ePicLoad()
            self.scale = AVSwitch().getFramebufferScale()
            self.picload.setPara([size.width(), size.height(), self.scale[0], self.scale[1], 0, 1, '#00000000'])

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
        self.fldpng = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/skin/pics/presplash.png".format('vavoo'))
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
        global _session, HALIGN
        _session = session
        Screen.__init__(self, session)

        skin = os_path.join(skin_path, 'defaultListScreen.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self.menulist = []
        self['menulist'] = m2list([])
        self['red'] = Label(_('Exit'))
        self['green'] = Label(_('Remove') + ' Fav')
        self['yellow'] = Label(_('Update Me'))
        self["blue"] = Label()
        if HALIGN == RT_HALIGN_RIGHT:
            self['blue'].setText(_('Halign Left'))
        else:
            self['blue'].setText(_('Halign Right'))
        self['name'] = Label('Loading...')
        self['version'] = Label()
        self.currentList = 'menulist'
        self.loading_ok = False
        self.count = 0
        self.loading = 0
        self.url = vUtils.b64decoder(stripurl)
        self['actions'] = ActionMap(['ButtonSetupActions', 'MenuActions', 'OkCancelActions', 'DirectionActions', 'ShortcutActions', 'HotkeyActions', 'InfobarEPGActions', 'ChannelSelectBaseActions'], {
            'prevBouquet': self.chDown,
            'nextBouquet': self.chUp,
            'ok': self.ok,
            'menu': self.goConfig,
            'green': self.msgdeleteBouquets,
            'blue': self.arabic,
            'cancel': self.close,
            'info': self.info,
            'showEventInfo': self.info,
            'red': self.close,
            'yellow': self.update_me,
            'yellow_long': self.update_dev,
            'info_long': self.update_dev,
            'infolong': self.update_dev,
            'showEventInfoPlugin': self.update_dev,
        }, -1)
        self.cat()
        '''
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.cat)
        except:
            self.timer.callback.append(self.cat)
        self.timer.start(500, True)
        '''

    def arabic(self):
        global HALIGN
        if HALIGN == RT_HALIGN_LEFT:
            HALIGN = RT_HALIGN_RIGHT
            self['blue'].setText(_('Halign Left'))
        elif HALIGN == RT_HALIGN_RIGHT:
            HALIGN = RT_HALIGN_LEFT
            self['blue'].setText(_('Halign Right'))
        self.cat()

    def update_me(self):
        remote_version = '0.0'
        remote_changelog = ''
        req = vUtils.Request(vUtils.b64decoder(installer_url), headers={'User-Agent': 'Mozilla/5.0'})
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
            self.session.openWithCallback(self.install_update, MessageBox, _("New version %s is available.\n\nChangelog: %s \n\nDo you want to install it now?") % (new_version, new_changelog), MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, _("Congrats! You already have the latest version..."),  MessageBox.TYPE_INFO, timeout=4)

    def update_dev(self):
        req = vUtils.Request(vUtils.b64decoder(developer_url), headers={'User-Agent': 'Mozilla/5.0'})
        page = vUtils.urlopen(req).read()
        data = json.loads(page)
        remote_date = data['pushed_at']
        strp_remote_date = datetime.strptime(remote_date, '%Y-%m-%dT%H:%M:%SZ')
        remote_date = strp_remote_date.strftime('%Y-%m-%d')
        self.session.openWithCallback(self.install_update, MessageBox, _("Do you want to install update ( %s ) now?") % (remote_date), MessageBox.TYPE_YESNO)

    def install_update(self, answer=False):
        if answer:
            self.session.open(Console, 'Upgrading...', cmdlist=('wget -q "--no-check-certificate" ' + vUtils.b64decoder(installer_url) + ' -O - | /bin/sh'), finishedCallback=self.myCallback, closeOnSuccess=False)
        else:
            self.session.open(MessageBox, _("Update Aborted!"),  MessageBox.TYPE_INFO, timeout=3)

    def myCallback(self, result=None):
        print('result:', result)
        return

    def goConfig(self):
        self.session.open(vavoo_config)

    def info(self):
        aboutbox = self.session.open(MessageBox, _('%s\n\n\nThanks:\n@KiddaC\n@oktus\nQu4k3\nAll staff Linuxsat-support.com\nCorvoboys - Forum\n\nThis plugin is free,\nno stream direct on server\nbut only free channel found on the net') % desc_plugin, MessageBox.TYPE_INFO)
        aboutbox.setTitle(_('Info Vavoo'))

    def chUp(self):
        for x in range(5):
            self[self.currentList].pageUp()
        txtsream = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(txtsream))

    def chDown(self):
        for x in range(5):
            self[self.currentList].pageDown()
        txtsream = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(txtsream))

    def cat(self):
        self.cat_list = []
        items = []
        self.items_tmp = []
        name = ''
        country = ''
        try:
            content = vUtils.getUrl(self.url)
            if PY3:
                content = ensure_str(content)
            try:
                data = json.loads(content)
            except ValueError:
                print('Error parsing JSON data')
                self['name'].setText('Error parsing data')
                return
            # data = sorted(data, key=lambda x: x["country"])
            for entry in data:
                country = unquote(entry["country"]).strip("\r\n")
                name = unquote(entry["name"]).strip("\r\n")
                # id = entry["id"]
                if country not in self.items_tmp:
                    self.items_tmp.append(country)
                    item = str(country) + "###" + self.url + '\n'
                    items.append(item)
            items.sort()
            for item in items:
                name = item.split('###')[0]
                url = item.split('###')[1]
                if name not in self.cat_list:
                    self.cat_list.append(show_list(name, url))
            if len(self.cat_list) < 1:
                return
            else:
                self['menulist'].l.setList(self.cat_list)
                self['menulist'].moveToIndex(0)
                txtsream = self['menulist'].getCurrent()[0][0]
                self['name'].setText(str(txtsream))
        except Exception as error:
            print('error as:', error)
            trace_error()
            self['name'].setText('Error')
        self['version'].setText('V.' + currversion)

    def ok(self):
        name = self['menulist'].getCurrent()[0][0]
        url = self['menulist'].getCurrent()[0][1]
        try:
            self.session.open(vavoo, name, url)
        except Exception as error:
            print('error as:', error)
            trace_error()

    def exit(self):
        self.close()

    def msgdeleteBouquets(self):
        self.session.openWithCallback(self.deleteBouquets, MessageBox, _("Remove all Vavoo Favorite Bouquet?"), MessageBox.TYPE_YESNO, timeout=5, default=True)

    def deleteBouquets(self, result):
        if result:
            try:
                for fname in os.listdir(enigma_path):
                    if 'userbouquet.vavoo_' in fname:
                        vUtils.purge(enigma_path, fname)
                    elif 'bouquets.tv.bak' in fname:
                        vUtils.purge(enigma_path, fname)
                os.rename(os_path.join(enigma_path, 'bouquets.tv'), os_path.join(enigma_path, 'bouquets.tv.bak'))
                tvfile = open(os_path.join(enigma_path, 'bouquets.tv'), 'w+')
                bakfile = open(os_path.join(enigma_path, 'bouquets.tv.bak'))
                for line in bakfile:
                    if '.vavoo_' not in line:
                        tvfile.write(line)
                bakfile.close()
                tvfile.close()
                if file_exists(PLUGIN_PATH + '/Favorite.txt'):
                    os.remove(PLUGIN_PATH + '/Favorite.txt')
                self.session.open(MessageBox, _('Vavoo Favorites List have been removed'), MessageBox.TYPE_INFO, timeout=5)
                vUtils.ReloadBouquets()
            except Exception as error:
                print(error)
                trace_error()


class vavoo(Screen):
    def __init__(self, session, name, url):
        self.session = session
        global _session, HALIGN
        _session = session
        Screen.__init__(self, session)
        skin = os_path.join(skin_path, 'defaultListScreen.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()

        self.menulist = []
        global search_ok
        search_ok = False
        self['menulist'] = m2list([])
        self['red'] = Label(_('Back'))
        self['green'] = Label(_('Export') + ' Fav')
        self['yellow'] = Label(_('Search'))
        self["blue"] = Label()
        if HALIGN == RT_HALIGN_RIGHT:
            self['blue'].setText(_('Halign Left'))
        else:
            self['blue'].setText(_('Halign Right'))
        self['name'] = Label('Loading ...')
        self['version'] = Label()
        self.currentList = 'menulist'
        self.loading_ok = False
        self.count = 0
        self.loading = 0
        self.name = name
        self.url = url
        self['actions'] = ActionMap(['ButtonSetupActions', 'MenuActions', 'OkCancelActions', 'ShortcutActions', 'HotkeyActions', 'DirectionActions', 'InfobarEPGActions', 'ChannelSelectBaseActions'], {
            'prevBouquet': self.chDown,
            'nextBouquet': self.chUp,
            'ok': self.ok,
            'green': self.message1,
            'yellow': self.search_vavoo,
            'blue': self.arabic,
            'cancel': self.backhome,
            'menu': self.goConfig,
            'info': self.info,
            'red': self.backhome
        }, -1)
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.cat)
        except:
            self.timer.callback.append(self.cat)
        self.timer.start(500, True)

    def arabic(self):
        global HALIGN
        if HALIGN == RT_HALIGN_LEFT:
            HALIGN = RT_HALIGN_RIGHT
            self['blue'].setText(_('Halign Left'))
        elif HALIGN == RT_HALIGN_RIGHT:
            HALIGN = RT_HALIGN_LEFT
            self['blue'].setText(_('Halign Right'))
        self.cat()

    def backhome(self):
        if search_ok is True:
            self.cat()
        else:
            self.close()

    def goConfig(self):
        self.session.open(vavoo_config)

    def info(self):
        aboutbox = self.session.open(MessageBox, _('%s\n\n\nThanks:\n@KiddaC\n@oktus\nQu4k3\nAll staff Linuxsat-support.com\nCorvoboys - Forum\n\nThis plugin is free,\nno stream direct on server\nbut only free channel found on the net') % desc_plugin, MessageBox.TYPE_INFO)
        aboutbox.setTitle(_('Info Vavoo'))

    def chUp(self):
        for x in range(5):
            self[self.currentList].pageUp()
        txtsream = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(txtsream))

    def chDown(self):
        for x in range(5):
            self[self.currentList].pageDown()
        txtsream = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(txtsream))

    def cat(self):
        self.cat_list = []
        items = []
        xxxname = '/tmp/' + self.name + '.m3u'
        svr = cfg.server.value
        server = zServer(0, svr, None)
        data = None
        global search_ok
        search_ok = False
        try:
            content = vUtils.getUrl(self.url)
            if PY3:
                content = ensure_str(content)
            data = json.loads(content)
        except ValueError:
            print('Error parsing JSON data')
            self['name'].setText('Error parsing data')
            return
        # data = sorted(data, key=lambda x: x["country"])
        try:
            if data is not None:
                for entry in data:
                    country = unquote(entry["country"]).strip("\r\n")
                    name = unquote(entry["name"]).strip("\r\n")
                    ids = entry["id"]
                    if country != self.name:
                        continue
                    ids = str(ids).replace(':', '').replace(' ', '').replace(',', '')
                    url = str(server) + '/live2/play/' + ids + '.ts'
                    name = vUtils.decodeHtml(name)
                    name = rimuovi_parentesi(name)
                    item = name + "###" + url + '\n'
                    items.append(item)
                items.sort()
                # use for search
                global itemlist
                itemlist = items
                # use for search end
                with open(xxxname, 'w') as outfile:
                    for item in items:
                        name1 = item.split('###')[0]
                        url = item.split('###')[1]
                        url = url.replace('%0a', '').replace('%0A', '').strip("\r\n")
                        name = unquote(name1).strip("\r\n")
                        self.cat_list.append(show_list(name, url))
                        # make m3u
                        outfile.write('#NAME %s\r\n' % self.name.capitalize())
                        nname = '#EXTINF:-1,' + str(name) + '\n'
                        outfile.write(nname)
                        outfile.write('#EXTVLCOPT:http-user-agent=VAVOO/2.6' + '\n')
                        outfile.write(str(url) + '\n')
                # make m3u end
                if len(self.cat_list) < 1:
                    return
                else:
                    self['menulist'].l.setList(self.cat_list)
                    self['menulist'].moveToIndex(0)
                    txtsream = self['menulist'].getCurrent()[0][0]
                    self['name'].setText(str(txtsream))
        except Exception as error:
            print('error as:', error)
            trace_error()
            self['name'].setText('Error')
        self['version'].setText('V.' + currversion)

    def ok(self):
        try:
            i = self['menulist'].getSelectedIndex()
            self.currentindex = i
            selection = self['menulist'].l.getCurrentSelection()
            if selection is not None:
                item = self.cat_list[i][0]
                name = item[0]
                url = item[1]
            self.play_that_shit(url, name, self.currentindex, item, self.cat_list)
        except Exception as error:
            print('error as:', error)
            trace_error()

    def play_that_shit(self, url, name, index, item, cat_list):
        self.session.open(Playstream2, name, url, index, item, cat_list)

    def message0(self, name, url, response):
        name = self.name
        url = self.url
        filenameout = enigma_path + '/userbouquet.vavoo_%s.tv' % name.lower()
        if file_exists(filenameout):
            self.message3(name, url, False)
        else:
            self.message2(name, url, False)

    def message1(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.message1, MessageBox, _('Do you want to Convert to favorite .tv ?\n\nAttention!! It may take some time\ndepending on the number of streams contained !!!'))
        elif answer:
            name = self.name
            url = self.url
            filenameout = enigma_path + '/userbouquet.vavoo_%s.tv' % name.lower()
            if file_exists(filenameout):
                self.message4()
            else:
                self.message2(name, url, True)

    def message2(self, name, url, response):
        service = cfg.services.value
        ch = 0
        ch = convert_bouquet(service, name, url)
        if int(ch) > 0:
            if response is True:
                localtime = time.asctime(time.localtime(time.time()))
                cfg.last_update.value = localtime
                cfg.last_update.save()
                _session.open(MessageBox, _('bouquets reloaded..\nWith %s channel') % str(ch), MessageBox.TYPE_INFO, timeout=5)
        else:
            _session.open(MessageBox, _('Download Error'), MessageBox.TYPE_INFO, timeout=5)

    def message3(self, name, url, response):
        sig = Sig()
        app = str(sig)
        if app:
            app = str(app)
        filename = PLUGIN_PATH + '/list/userbouquet.vavoo_%s.tv' % name.lower()
        filenameout = enigma_path + '/userbouquet.vavoo_%s.tv' % name.lower()
        key = None
        ch = 0
        with open(filename, "rt") as fin:
            data = fin.read()
            regexcat = '#SERVICE.*?vavoo_auth=(.+?)#User'
            match = re.compile(regexcat, re.DOTALL).findall(data)
            for key in match:
                key = str(key)
                ch += 1

        with open(filename, 'r') as f:
            newlines = []
            for line in f.readlines():
                newlines.append(line.replace(key, app))

        with open(filenameout, 'w') as f:
            for line in newlines:
                f.write(line)
        vUtils.ReloadBouquets()
        if response is True:
            localtime = time.asctime(time.localtime(time.time()))
            cfg.last_update.value = localtime
            cfg.last_update.save()
            _session.open(MessageBox, _('Wait...\nUpdate List Bouquet...\nbouquets reloaded..\nWith %s channel') % str(ch), MessageBox.TYPE_INFO, timeout=5)

    def message4(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.message4, MessageBox, _('The favorite channel list exists.\nWant to update it with epg and picons?\n\nYES for Update\nelse remove List Favorite first!'))
        elif answer:
            name = self.name
            url = self.url
            self.message3(name, url, True)

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
                for item in itemlist:
                    name = item.split('###')[0]
                    url = item.split('###')[1]
                    if search.lower() in str(name).lower():
                        search_ok = True
                        namex = name
                        urlx = url.replace('%0a', '').replace('%0A', '')
                        self.cat_list.append(show_list(namex, urlx))
                if len(self.cat_list) < 1:
                    _session.open(MessageBox, _('No channels found in search!!!'), MessageBox.TYPE_INFO, timeout=5)
                    return
                else:
                    self['menulist'].l.setList(self.cat_list)
                    self['menulist'].moveToIndex(0)
                    txtsream = self['menulist'].getCurrent()[0][0]
                    self['name'].setText(str(txtsream))
            except Exception as error:
                print(error)
                trace_error()
                self['name'].setText('Error')
                search_ok = False


class TvInfoBarShowHide():
    STATE_HIDDEN = 0
    STATE_HIDING = 1
    STATE_SHOWING = 2
    STATE_SHOWN = 3
    FLAG_CENTER_DVB_SUBS = 2048
    skipToggleShow = False

    def __init__(self):
        self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"],
                                            {"toggleShow": self.OkPressed,
                                             "hide": self.hide}, 0)
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evStart: self.serviceStarted})
        self.__state = self.STATE_SHOWN
        self.__locked = 0
        self.hideTimer = eTimer()
        try:
            self.hideTimer_conn = self.hideTimer.timeout.connect(self.doTimerHide)
        except:
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
    Screen
):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True
    screen_timeout = 5000

    def __init__(self, session, name, url, index, item, cat_list):
        global streaml, _session
        Screen.__init__(self, session)
        self.session = session
        _session = session
        self.skinName = 'MoviePlayer'
        self.currentindex = index
        self.item = item
        self.itemscount = len(cat_list)
        self.list = cat_list
        streaml = False
        for x in InfoBarBase, \
                InfoBarMenu, \
                InfoBarSeek, \
                InfoBarAudioSelection, \
                InfoBarSubtitleSupport, \
                InfoBarNotifications, \
                TvInfoBarShowHide:
            x.__init__(self)
        try:
            self.init_aspect = int(self.getAspect())
        except:
            self.init_aspect = 0
        self.new_aspect = self.init_aspect
        self.service = None
        self.url = url.replace('%0a', '').replace('%0A', '')
        self.name = name
        self.state = self.STATE_PLAYING
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self['actions'] = ActionMap(['MoviePlayerActions', 'MovieSelectionActions', 'MediaPlayerActions', 'EPGSelectActions', 'OkCancelActions',
                                    'InfobarShowHideActions', 'InfobarActions', 'DirectionActions', 'InfobarSeekActions'], {
            # 'epg': self.showIMDB,
            # 'info': self.showIMDB,
            'tv': self.cicleStreamType,
            'stop': self.leavePlayer,
            'cancel': self.cancel,
            'channelDown': self.previousitem,
            'channelUp': self.nextitem,
            'down': self.previousitem,
            'up': self.nextitem,
            'back': self.cancel
        }, -1)

        self.onFirstExecBegin.append(self.cicleStreamType)
        self.onClose.append(self.cancel)

    def nextitem(self):
        currentindex = int(self.currentindex) + 1
        if currentindex == self.itemscount:
            currentindex = 0
        self.currentindex = currentindex
        i = self.currentindex
        item = self.list[i][0]
        self.name = item[0]
        self.url = item[1]
        self.cicleStreamType()

    def previousitem(self):
        currentindex = int(self.currentindex) - 1
        if currentindex < 0:
            currentindex = self.itemscount - 1
        self.currentindex = currentindex
        i = self.currentindex
        item = self.list[i][0]
        self.name = item[0]
        self.url = item[1]
        self.cicleStreamType()

    def doEofInternal(self, playing):
        print('doEofInternal', playing)
        vUtils.MemClean()
        if self.execing and playing:
            self.cicleStreamType()

    def __evEOF(self):
        print('__evEOF')
        self.end = True
        vUtils.MemClean()
        self.cicleStreamType()

    def getAspect(self):
        return AVSwitch().getAspectRatioSetting()

    def getAspectString(self, aspectnum):
        return {0: '4:3 Letterbox',
                1: '4:3 PanScan',
                2: '16:9',
                3: '16:9 always',
                4: '16:10 Letterbox',
                5: '16:10 PanScan',
                6: '16:9 Letterbox'}[aspectnum]

    def setAspect(self, aspect):
        map = {0: '4_3_letterbox',
               1: '4_3_panscan',
               2: '16_9',
               3: '16_9_always',
               4: '16_10_letterbox',
               5: '16_10_panscan',
               6: '16_9_letterbox'}
        config.av.aspectratio.setValue(map[aspect])
        try:
            AVSwitch().setAspectRatio(aspect)
        except:
            pass

    def av(self):
        self.new_aspect += 1
        if self.new_aspect > 6:
            self.new_aspect = 0
        try:
            AVSwitch.getInstance().setAspectRatio(self.new_aspect)
            return VIDEO_ASPECT_RATIO_MAP[self.new_aspect]
        except Exception as error:
            print(error)
            trace_error()
            return _("Resolution Change Failed")

    def nextAV(self):
        message = self.av()
        self.session.open(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=1)

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
            sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
            sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
            message = 'stitle:' + str(sTitle) + '\n' + 'sServiceref:' + str(sServiceref) + '\n' + 'sTagCodec:' + str(sTagCodec) + '\n' + 'sTagVideoCodec:' + str(sTagVideoCodec) + '\n' + 'sTagAudioCodec : ' + str(sTagAudioCodec)
            self.mbox = self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
        except:
            pass
        return

    def openTest(self, servicetype, url):
        sig = Sig()
        app = '?n=1&b=5&vavoo_auth=' + str(sig) + '#User-Agent=VAVOO/2.6'
        name = self.name
        url = url + app
        ref = "{0}:0:0:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        self.sref = sref
        self.sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(self.sref)

    def cicleStreamType(self):
        self.servicetype = '4097'
        if not self.url.startswith('http'):
            self.url = 'http://' + self.url
        url = str(self.url)
        if str(os_path.splitext(self.url)[-1]) == ".m3u8":
            if self.servicetype == "1":
                self.servicetype = "4097"
        self.openTest(self.servicetype, url)

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
        if os_path.isfile('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(self.srefInit)
        if not self.new_aspect == self.init_aspect:
            try:
                self.setAspect(self.init_aspect)
            except:
                pass
        self.close()

    def leavePlayer(self):
        self.close()


VIDEO_ASPECT_RATIO_MAP = {0: "4:3 Letterbox", 1: "4:3 PanScan", 2: "16:9", 3: "16:9 Always", 4: "16:10 Letterbox", 5: "16:10 PanScan", 6: "16:9 Letterbox"}
VIDEO_FMT_PRIORITY_MAP = {"38": 1, "37": 2, "22": 3, "18": 4, "35": 5, "34": 6}


def convert_bouquet(service, name, url):
    sig = Sig()
    app = '?n=1&b=5&vavoo_auth=%s#User-Agent=VAVOO/2.6' % (str(sig))
    files = '/tmp/%s.m3u' % name
    bouquet_type = 'tv'
    if "radio" in name.lower():
        bouquet_type = "radio"
    name_file = re.sub(r'[<>:"/\\|?*, ]', '_', str(name))
    name_file = re.sub(r'\d+:\d+:[\d.]+', '_', name_file)
    name_file = re.sub(r'_+', '_', name_file)
    with open(PLUGIN_PATH + '/Favorite.txt', 'w') as r:
        r.write(str(name_file) + '###' + str(url))
    bouquet_name = 'userbouquet.vavoo_%s.%s' % (name_file.lower(), bouquet_type.lower())
    print("Converting Bouquet %s" % name_file)
    path1 = '/etc/enigma2/' + str(bouquet_name)
    path2 = '/etc/enigma2/bouquets.' + str(bouquet_type.lower())
    ch = 0
    if os_path.exists(files) and os.stat(files).st_size > 0:
        try:
            tplst = []
            tplst.append('#NAME %s (%s)' % (name_file.capitalize(), bouquet_type.upper()))
            tplst.append('#SERVICE 1:64:0:0:0:0:0:0:0:0::%s CHANNELS' % name_file)
            tplst.append('#DESCRIPTION --- %s ---' % name_file)
            namel = ''
            svz = ''
            dct = ''
            with open(files, 'r') as f:
                for line in f:
                    line = str(line)
                    if line.startswith("#EXTINF"):
                        namel = '%s' % line.split(',')[-1]
                        dsna = ('#DESCRIPTION %s' % namel).splitlines()
                        dct = ''.join(dsna)

                    elif line.startswith('http'):
                        line = line.strip('\n\r') + str(app)
                        tag = '1'
                        if bouquet_type.upper() == 'RADIO':
                            tag = '2'

                        svca = ('#SERVICE %s:0:%s:0:0:0:0:0:0:0:%s' % (service, tag, line.replace(':', '%3a')))
                        svz = (svca + ':' + namel).splitlines()
                        svz = ''.join(svz)

                    if svz not in tplst:
                        tplst.append(svz)
                        tplst.append(dct)
                        ch += 1

            with open(path1, 'w+') as f:
                f_content = f.read()
                for item in tplst:
                    if item not in f_content:
                        f.write("%s\n" % item)

            in_bouquets = False
            with open('/etc/enigma2/bouquets.%s' % bouquet_type.lower(), 'r') as f:
                for line in f:
                    if bouquet_name in line:
                        in_bouquets = True
            if not in_bouquets:
                with open(path2, 'a+') as f:
                    bouquetTvString = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + str(bouquet_name) + '" ORDER BY bouquet\n'
                    f.write(bouquetTvString)
            vUtils.ReloadBouquets()
        except Exception as error:
            print('error as:', error)
    return ch


autoStartTimer = None


class AutoStartTimer:
    def __init__(self, session):
        print("*** running AutoStartTimer Vavoo ***")
        self.session = session
        self.timer = eTimer()
        try:
            self.timer.callback.append(self.on_timer)
        except:
            self.timer_conn = self.timer.timeout.connect(self.on_timer)
        self.timer.start(100, True)
        self.update()  # issue loop

    def get_wake_time(self):
        if cfg.autobouquetupdate.value is True:
            if cfg.timetype.value == "interval":
                interval = int(cfg.updateinterval.value)
                nowt = time.time()
                return int(nowt) + interval * 60  # * 60
            if cfg.timetype.value == "fixed time":
                ftc = cfg.fixedtime.value
                now = time.localtime(time.time())
                fwt = int(time.mktime((now.tm_year,
                                       now.tm_mon,
                                       now.tm_mday,
                                       ftc[0],
                                       ftc[1],
                                       now.tm_sec,
                                       now.tm_wday,
                                       now.tm_yday,
                                       now.tm_isdst)))
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
            next = wake - int(nowt)
            if next > 3600:
                next = 3600
            if next <= 0:
                next = 60
            self.timer.startLongTimer(next)
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
        name = url = ''
        favorite_channel = os_path.join(PLUGIN_PATH, 'Favorite.txt')
        if file_exists(favorite_channel):
            with open(favorite_channel, 'r') as f:
                line = f.readline()
                name = line.split('###')[0]
                url = line.split('###')[1]
                '''# print('name %s and url %s:' % (name, url))
            # try:'''
            print('session start convert time')
            vid2 = vavoo(_session, name, url)
            vid2.message0(name, url, False)
            '''# except Exception as e:
                # print('timeredit error vavoo', e)'''


def check_configuring():
    if cfg.autobouquetupdate.value is True:
        """Check for new config values for auto start
        """
        global autoStartTimer
        if autoStartTimer is not None:
            autoStartTimer.update()
        return


def autostart(reason, session=None, **kwargs):
    global autoStartTimer
    global _session
    if reason == 0 and _session is None:
        if session is not None:
            _session = session
            if autoStartTimer is None:
                autoStartTimer = AutoStartTimer(session)
    return


def get_next_wakeup():
    return -1


def add_skin_back(bakk):
    if file_exists(os_path.join(BackPath, str(bakk))):
        baknew = os_path.join(BackPath, str(bakk))
        cmd = 'cp -f ' + str(baknew) + ' ' + BackPath + '/default.png'
        os.system(cmd)
        os.system('sync')


def add_skin_font():
    print('**********addFont')
    from enigma import addFont
    global FONTSTYPE
    addFont(FNTPath + '/Lcdx.ttf', 'Lcdx', 100, 1)
    addFont(str(FONTSTYPE), 'cvfont', 100, 1)
    addFont(os_path.join(str(FNTPath), 'vav.ttf'), 'Vav', 100, 1)  # lcd


def cfgmain(menuid, **kwargs):
    return [(_('Vavoo Stream Live'), main, 'Vavoo', 55)] if menuid == "mainmenu" else []


def main(session, **kwargs):
    try:
        if file_exists('/tmp/vavoo.log'):
            os.remove('/tmp/vavoo.log')
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
        where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART],
        fnc=autostart,
        wakeupfnc=get_next_wakeup
    )

    result = [plugin_menu_descriptor, autostart_descriptor]

    if cfg.stmain.value:
        result.append(main_descriptor)

    return result
