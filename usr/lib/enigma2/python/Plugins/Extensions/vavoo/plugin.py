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
from twisted.web.client import error
import json
import os
import re
import requests
import six
import ssl
import sys
import time
import traceback
import codecs
global HALIGN
tmlast = None
now = None
_session = None
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


if sys.version_info >= (2, 7, 9):
    try:
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None


# set plugin
currversion = '1.25'
title_plug = 'Vavoo'
desc_plugin = ('..:: Vavoo by Lululla v.%s ::..' % currversion)
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('vavoo'))
pluglogo = os_path.join(PLUGIN_PATH, 'plugin.png')
stripurl = 'aHR0cHM6Ly92YXZvby50by9jaGFubmVscw=='
keyurl = 'aHR0cDovL3BhdGJ1d2ViLmNvbS92YXZvby92YXZvb2tleQ=='
installer_url = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0JlbGZhZ29yMjAwNS92YXZvby9tYWluL2luc3RhbGxlci5zaA=='
developer_url = 'aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9CZWxmYWdvcjIwMDUvdmF2b28='
enigma_path = '/etc/enigma2/'
json_file = '/tmp/vavookey'
HALIGN = RT_HALIGN_LEFT
screenwidth = getDesktop(0).size()
default_font = ''


# log
def trace_error():
    try:
        traceback.print_exc(file=sys.stdout)
        traceback.print_exc(file=open("/tmp/vavoo.log", "a"))
    except:
        pass


myser = [("https://vavoo.to", "vavoo"), ("https://oha.to", "oha"), ("https://kool.to", "kool"), ("https://huhu.to", "huhu")]
modemovie = [("4097", "4097")]
if file_exists("/usr/bin/gstplayer"):
    modemovie.append(("5001", "5001"))
if file_exists("/usr/bin/exteplayer3"):
    modemovie.append(("5002", "5002"))
if file_exists('/var/lib/dpkg/info'):
    modemovie.append(("8193", "8193"))


# back
global BackPath
BackPath = os_path.join(PLUGIN_PATH + "skin")
if screenwidth.width() == 2560:
    BackPath = BackPath + '/images_new'
    skin_path = os_path.join(PLUGIN_PATH, 'skin/wqhd')
elif screenwidth.width() == 1920:
    BackPath = BackPath + '/images_new'
    skin_path = os_path.join(PLUGIN_PATH, 'skin/fhd')
elif screenwidth.width() == 1280:
    BackPath = BackPath + '/images'
    skin_path = os_path.join(PLUGIN_PATH, 'skin/hd')
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
                BakP.append((backNamePath, backName))
except Exception as error:
    trace_error()
print('final folder back: ', BackPath)
# BakP = sorted(BakP, key=lambda x: x[1])
# fonts
FNTPath = os_path.join(PLUGIN_PATH + "/fonts")
fonts = []
try:
    if file_exists(FNTPath):
        for fontName in os.listdir(FNTPath):
            fontNamePath = os_path.join(FNTPath, fontName)
            if fontName.endswith(".ttf") or fontName.endswith(".otf"):
                fontName = fontName[:-4]
                fonts.append((fontNamePath, fontName))
except Exception as error:
    trace_error()


fonts = sorted(fonts, key=lambda x: x[1])

# config section
config.plugins.vavoo = ConfigSubsection()
cfg = config.plugins.vavoo
cfg.autobouquetupdate = ConfigEnableDisable(default=False)
cfg.server = ConfigSelection(default="https://vavoo.to", choices=myser)
cfg.services = ConfigSelection(default='4097', choices=modemovie)
cfg.timetype = ConfigSelection(default="interval", choices=[("interval", _("interval")), ("fixed time", _("fixed time"))])
cfg.updateinterval = ConfigSelectionNumber(default=10, min=5, max=3600, stepwidth=5)
cfg.fixedtime = ConfigClock(default=46800)
cfg.last_update = ConfigText(default="Never")
cfg.stmain = ConfigYesNo(default=True)
cfg.ipv6 = ConfigEnableDisable(default=False)
cfg.fonts = ConfigSelection(default=default_font, choices=fonts)
cfg.back = ConfigSelection(default='oktus', choices=BakP)
FONTSTYPE = cfg.fonts.value
BACKTYPE = str(cfg.back.value)
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


def Sig():
    sig = ''
    if not file_exists(json_file):
        myUrl = vUtils.b64decoder(keyurl)
        vecKeylist = requests.get(myUrl).json()
        vecs = {'time': int(time.time()), 'vecs': vecKeylist}
        with open(json_file, "w") as f:
            json.dump(vecKeylist, f, indent=2)
    else:
        vec = None
        with open(json_file) as f:
            vecs = json.load(f)
            vec = choice(vecs)
            # print('vec=', str(vec))
            headers = {
                # Already added when you pass json=
                'Content-Type': 'application/json',
            }
        json_data = '{"vec": "' + str(vec) + '"}'
        if PY3:
            req = requests.post('https://www.vavoo.tv/api/box/ping2', headers=headers, data=json_data).json()
        else:
            req = requests.post('https://www.vavoo.tv/api/box/ping2', headers=headers, verify=False, data=json_data).json()
        # print('req:', req)
        if req.get('signed'):
            sig = req['signed']
        elif req.get('data', {}).get('signed'):
            sig = req['data']['signed']
        elif req.get('response', {}).get('signed'):
            sig = req['response']['signed']
        # print('res key:', str(sig))
    return sig


def loop_sig():
    while True:
        sig = ''
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


def returnIMDB(text_clear):
    TMDB = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('TMDB'))
    IMDb = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('IMDb'))
    if file_exists(TMDB):
        try:
            from Plugins.Extensions.TMBD.plugin import TMBD
            text = vUtils.html_unescape(text_clear)
            _session.open(TMBD.tmdbScreen, text, 0)
        except Exception as e:
            print("[XCF] Tmdb: ", e)
        return True
    elif file_exists(IMDb):
        try:
            from Plugins.Extensions.IMDb.plugin import main as imdb
            text = vUtils.html_unescape(text_clear)
            imdb(_session, text)
        except Exception as e:
            print("[XCF] imdb: ", e)
        return True
    else:
        text_clear = vUtils.html_unescape(text_clear)
        _session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)
        return True
    return False


# check server
def raises(url):
    try:
        from requests.adapters import HTTPAdapter, Retry
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
    def __init__(self, list):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)

        if screenwidth.width() == 2560:
            self.l.setItemHeight(60)
            textfont = int(38)
            self.l.setFont(0, gFont('Regular', textfont))
        # elif file_exists('/var/lib/dpkg/status'):
        elif screenwidth.width() == 1920:
            self.l.setItemHeight(50)
            textfont = int(34)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(50)
            textfont = int(28)
            self.l.setFont(0, gFont('Regular', textfont))


Panel_list = ("Albania", "Arabia", "Balkans", "Bulgaria",
              "France", "Germany", "Italy", "Netherlands",
              "Poland", "Portugal", "Romania", "Russia",
              "Spain", "Turkey", "United Kingdom")


def show_list(name, link):
    res = [(name, link)]
    pngx = PLUGIN_PATH + '/skin/pics/Internat.png'
    if any(s in name for s in Panel_list):
        pngx = PLUGIN_PATH + '/skin/pics/%s.png' % name
    else:
        pngx = PLUGIN_PATH + '/skin/pics/vavoo_ico.png'
    if os_path.isfile(pngx):
        if screenwidth.width() == 2560:
            res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 10), size=(60, 40), png=loadPNG(pngx)))
            res.append(MultiContentEntryText(pos=(90, 0), size=(750, 60), font=0, text=name, flags=HALIGN | RT_VALIGN_CENTER))
        elif screenwidth.width() == 1920:
            res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 5), size=(60, 40), png=loadPNG(pngx)))
            res.append(MultiContentEntryText(pos=(80, 0), size=(540, 50), font=0, text=name, flags=HALIGN | RT_VALIGN_CENTER))
        else:
            res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 5), size=(60, 40), png=loadPNG(pngx)))
            res.append(MultiContentEntryText(pos=(85, 0), size=(380, 50), font=0, text=name, flags=HALIGN | RT_VALIGN_CENTER))
        return res


# config class
class vavoo_config(Screen, ConfigListScreen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'vavoo_config.xml')
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
        self["green"] = Label(_("Save"))
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'DirectionActions'], {
            "cancel": self.extnok,
            "left": self.keyLeft,
            "right": self.keyRight,
            "up": self.keyUp,
            "down": self.keyDown,
            "red": self.extnok,
            "green": self.save,
            # "blue": self.Import,
            "ok": self.save,
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
        self.list.append(getConfigListEntry(_("Server for Player Used"), cfg.server, _("Server for player.\nNow %s") % cfg.server.value))
        self.list.append(getConfigListEntry(_("Ipv6 State Of Lan (On/Off)"), cfg.ipv6, _("Active or Disactive lan Ipv6.\nNow %s") % cfg.ipv6.value))
        self.list.append(getConfigListEntry(_("Movie Services Reference"), cfg.services, _("Configure service Reference Iptv-Gstreamer-Exteplayer3")))
        self.list.append(getConfigListEntry(_("Select Background"), cfg.back, _("Configure Main Background Image.")))
        self.list.append(getConfigListEntry(_("Select Fonts"), cfg.fonts, _("Configure Fonts.\nEg:Arabic or other language.")))
        self.list.append(getConfigListEntry(_('Link in Main Menu'), cfg.stmain, _("Link in Main Menu")))
        self.list.append(getConfigListEntry(_("Scheduled Bouquet Update:"), cfg.autobouquetupdate, _("Active Automatic Bouquet Update")))
        if cfg.autobouquetupdate.value is True:
            self.list.append(getConfigListEntry(indent + _("Schedule type:"), cfg.timetype, _("At an interval of hours or at a fixed time")))
            if cfg.timetype.value == "interval":
                self.list.append(getConfigListEntry(2 * indent + _("Update interval (minutes):"), cfg.updateinterval, _("Configure every interval of minutes from now")))
            if cfg.timetype.value == "fixed time":
                self.list.append(getConfigListEntry(2 * indent + _("Time to start update:"), cfg.fixedtime, _("Configure at a fixed time")))

        self["config"].list = self.list
        self["config"].l.setList(self.list)
        self.setInfo()

    def setInfo(self):
        try:
            sel = self['config'].getCurrent()[2]
            if sel:
                self['description'].setText(str(sel))
            else:
                self['description'].setText(_('SELECT YOUR CHOICE'))
            return
        except Exception as error:
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

    def save(self):
        if self["config"].isChanged():
            for x in self["config"].list:
                x[1].save()
            if self.v6 != cfg.ipv6.value:
                self.ipv6()
            configfile.save()
            add_skin_font()
            add_skin_back()
            restartbox = self.session.openWithCallback(self.restartGUI, MessageBox, _('Settings saved successfully !\nyou need to restart the GUI\nto apply the new configuration!\nDo you want to Restart the GUI now?'), MessageBox.TYPE_YESNO)
            restartbox.setTitle(_('Restart GUI now?'))
        else:
            self.close()

    def restartGUI(self, answer):
        if answer is True:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close()

    def extnok(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.extnok, MessageBox, _("Really close without saving settings?"))
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
        skin = os.path.join(skin_path, 'Plgnstrt.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        # with open(skin_strt, "r") as f:
            # self.skin = f.read()
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
            # _l = self.picload.PictureData.get()
            # del self.picload
            if file_exists("/var/lib/dpkg/status"):
                self.picload.startDecode(pixmapx, False)
            else:
                self.picload.startDecode(pixmapx, 0, 0, False)
            ptr = self.picload.getData()
            if ptr is not None:
                self['poster'].instance.setPixmap(ptr)
                self['poster'].show()
                self['version'].setText('V.' + currversion)
            # return

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
        global _session
        _session = session
        Screen.__init__(self, session)

        skin = os.path.join(skin_path, 'defaultListScreen.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        # with open(skin_path, "r") as f:
            # self.skin = f.read()
        self.menulist = []
        self['menulist'] = m2list([])
        self['red'] = Label(_('Exit'))
        self['green'] = Label(_('Remove') + ' Fav')
        # self['green'] = Label()
        self['yellow'] = Label(_('Update Me'))
        self["blue"] = Label(_("HALIGN"))
        self['name'] = Label('Loading...')
        self['version'] = Label()
        self.currentList = 'menulist'
        self.loading_ok = False
        self.count = 0
        self.loading = 0
        self.url = vUtils.b64decoder(stripurl)
        self['actions'] = ActionMap(['ButtonSetupActions', 'MenuActions', 'OkCancelActions', 'ColorActions', 'DirectionActions', 'HotkeyActions', 'InfobarEPGActions', 'ChannelSelectBaseActions'], {
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

        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.cat)
        except:
            self.timer.callback.append(self.cat)
        self.timer.start(500, True)
        # self.onShow.append(self.check)

    def arabic(self):
        global HALIGN
        if HALIGN == RT_HALIGN_LEFT:
            HALIGN = RT_HALIGN_RIGHT
        elif HALIGN == RT_HALIGN_RIGHT:
            HALIGN = RT_HALIGN_LEFT
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
            # def __init__(self, session, title='Console', cmdlist=None, finishedCallback=None, closeOnSuccess=False, showStartStopText=True, skin=None
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
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(auswahl))

    def chDown(self):
        for x in range(5):
            self[self.currentList].pageDown()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(auswahl))

    def cat(self):
        self.cat_list = []
        items = []
        self.items_tmp = []
        name = ''
        country = ''
        try:
            content = vUtils.getUrl(self.url)
            if PY3:
                content = six.ensure_str(content)
            regexcat = '"country".*?"(.*?)".*?"id".*?"name".*?".*?"'
            match = re.compile(regexcat, re.DOTALL).findall(content)
            for country in match:
                if country not in self.items_tmp:
                    self.items_tmp.append(country)
                    item = country + "###" + self.url + '\n'
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
                auswahl = self['menulist'].getCurrent()[0][0]
                self['name'].setText(str(auswahl))
        except Exception as error:
            trace_error()
            self['name'].setText('Error')
        self['version'].setText('V.' + currversion)

    def ok(self):
        name = self['menulist'].getCurrent()[0][0]
        url = self['menulist'].getCurrent()[0][1]
        try:
            self.session.open(vavoo, name, url)
        except Exception as error:
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
                trace_error()


class vavoo(Screen):
    def __init__(self, session, name, url):
        self.session = session
        global _session
        _session = session
        Screen.__init__(self, session)
        skin = os.path.join(skin_path, 'defaultListScreen.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        # with open(skin_path, "r") as f:
            # self.skin = f.read()
        self.menulist = []
        global search_ok
        search_ok = False
        self['menulist'] = m2list([])
        self['red'] = Label(_('Back'))
        self['green'] = Label(_('Export') + ' Fav')
        self['yellow'] = Label(_('Search'))
        self["blue"] = Label(_("HALIGN"))
        self['name'] = Label('Loading ...')
        self['version'] = Label()
        self.currentList = 'menulist'
        self.loading_ok = False
        self.count = 0
        self.loading = 0
        self.name = name
        self.url = url
        self['actions'] = ActionMap(['MenuActions', 'OkCancelActions', 'ColorActions', 'EPGSelectActions', 'DirectionActions', 'ChannelSelectBaseActions'], {
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
        elif HALIGN == RT_HALIGN_RIGHT:
            HALIGN = RT_HALIGN_LEFT
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
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(auswahl))

    def chDown(self):
        for x in range(5):
            self[self.currentList].pageDown()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(auswahl))

    def cat(self):
        self.cat_list = []
        items = []
        xxxname = '/tmp/' + self.name + '.m3u'
        svr = cfg.server.value
        server = zServer(0, svr, None)
        global search_ok
        search_ok = False
        try:
            with open(xxxname, 'w') as outfile:
                outfile.write('#NAME %s\r\n' % self.name.capitalize())
                content = vUtils.getUrl(self.url)
                if PY3:
                    content = six.ensure_str(content)
                names = self.name
                regexcat = '"country".*?"(.*?)".*?"id"(.*?)"name".*?"(.*?)"'
                match = re.compile(regexcat, re.DOTALL).findall(content)
                for country, ids, name in match:
                    if country != names:
                        continue
                    ids = ids.replace(':', '').replace(' ', '').replace(',', '')
                    url = str(server) + '/live2/play/' + str(ids) + '.ts'  # + app
                    name = vUtils.decodeHtml(name)
                    name = rimuovi_parentesi(name)
                    item = name + "###" + url + '\n'
                    items.append(item)
                items.sort()
                # use for search
                global itemlist
                itemlist = items
                # use for search end
                for item in items:
                    name = item.split('###')[0]
                    url = item.split('###')[1]
                    url = url.replace('%0a', '').replace('%0A', '').strip("\r\n")
                    self.cat_list.append(show_list(name, url))
                    # make m3u
                    nname = '#EXTINF:-1,' + str(name) + '\n'
                    outfile.write(nname)
                    outfile.write('#EXTVLCOPT:http-user-agent=VAVOO/2.6' + '\n')
                    outfile.write(str(url) + '\n')
                outfile.close()
                # make m3u end
                if len(self.cat_list) < 1:
                    return
                else:
                    self['menulist'].l.setList(self.cat_list)
                    self['menulist'].moveToIndex(0)
                    auswahl = self['menulist'].getCurrent()[0][0]
                    self['name'].setText(str(auswahl))
        except Exception as error:
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
            localtime = time.asctime(time.localtime(time.time()))
            cfg.last_update.value = localtime
            cfg.last_update.save()
            if response is True:
                _session.open(MessageBox, _('bouquets reloaded..\nWith %s channel') % str(ch), MessageBox.TYPE_INFO, timeout=5)
        else:
            _session.open(MessageBox, _('Download Error'), MessageBox.TYPE_INFO, timeout=5)

    def message3(self, name, url, response):
        sig = Sig()
        app = str(sig)
        filename = PLUGIN_PATH + '/list/userbouquet.vavoo_%s.tv' % name.lower()
        filenameout = enigma_path + '/userbouquet.vavoo_%s.tv' % name.lower()
        key = None
        with open(filename, "rt") as fin:
            data = fin.read()
            regexcat = '#SERVICE.*?vavoo_auth=(.+?)#User'
            match = re.compile(regexcat, re.DOTALL).findall(data)
            for key in match:
                key = str(key)

        with open(filename, 'r') as f:
            newlines = []
            for line in f.readlines():
                newlines.append(line.replace(key, app))

        with open(filenameout, 'w') as f:
            for line in newlines:
                f.write(line)
        vUtils.ReloadBouquets()
        localtime = time.asctime(time.localtime(time.time()))
        cfg.last_update.value = localtime
        cfg.last_update.save()
        if response is True:
            _session.open(MessageBox, _('Wait...\nUpdate List Bouquet...\nbouquets reloaded..'), MessageBox.TYPE_INFO, timeout=5)

    def message4(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.message4, MessageBox, _('The favorite channel list exists.\nWant to update it with epg and picons?\n\nYES for Update'))
        elif answer:
            name = self.name
            url = self.url
            # filenameout = enigma_path + '/userbouquet.vavoo_%s.tv' % name.lower()
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
                    auswahl = self['menulist'].getCurrent()[0][0]
                    self['name'].setText(str(auswahl))
            except Exception as error:
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
        self.name = vUtils.decodeHtml(name)
        self.state = self.STATE_PLAYING
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self['actions'] = ActionMap(['MoviePlayerActions', 'MovieSelectionActions', 'MediaPlayerActions', 'EPGSelectActions', 'OkCancelActions',
                                    'InfobarShowHideActions', 'InfobarActions', 'DirectionActions', 'InfobarSeekActions'], {
            'epg': self.showIMDB,
            'info': self.showIMDB,
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

    # def doEofInternal(self, playing):
        # self.close()

    # def __evEOF(self):
        # self.end = True

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

    def showIMDB(self):
        try:
            text_clear = self.name
            if returnIMDB(text_clear):
                print('show imdb/tmdb')
        except Exception as error:
            trace_error()
            print("Error: can't find Playstream2 in live_to_stream")

    def slinkPlay(self):
        url = self.url
        name = self.name
        ref = "{0}:{1}".format(url.replace(":", "%3a"), name.replace(":", "%3a"))
        # print('final reference:   ', ref)
        sref = eServiceReference(ref)
        self.sref = sref
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def openTest(self, servicetype, url):
        # tmlast = int(time.time())
        sig = Sig()
        app = '?n=1&b=5&vavoo_auth=' + str(sig) + '#User-Agent=VAVOO/2.6'
        # print('sig:', str(sig))
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
        self.servicetype = cfg.services.value
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
    from time import sleep
    sig = Sig()
    app = '?n=1&b=5&vavoo_auth={}#User-Agent=VAVOO/2.6'.format(str(sig))
    dir_enigma2 = '/etc/enigma2/'
    files = '/tmp/{}.m3u'.format(name)
    type = 'tv'
    if "radio" in name.lower():
        type = "radio"
    name_file = name.replace('/', '_').replace(',', '')
    cleanName = re.sub(r'[\<\>\:\"\/\\\|\?\*]', '_', str(name_file))
    cleanName = re.sub(r' ', '_', cleanName)
    cleanName = re.sub(r'\d+:\d+:[\d.]+', '_', cleanName)
    name_file = re.sub(r'_+', '_', cleanName)
    with open(PLUGIN_PATH + '/Favorite.txt', 'w') as r:
        r.write(str(name_file) + '###' + str(url))
        r.close()
    bouquetname = 'userbouquet.vavoo_{}.{}'.format(name_file.lower(), type.lower())
    if file_exists(str(files)):
        sleep(5)
        ch = 0
        try:
            if os_path.isfile(files) and os.stat(files).st_size > 0:
                desk_tmp = ''
                in_bouquets = 0
                with open('%s%s' % (dir_enigma2, bouquetname), 'w') as outfile:
                    outfile.write('#NAME %s\r\n' % name_file.capitalize())
                    for line in open(files):
                        if line.startswith('http://') or line.startswith('https'):
                            line = str(line).strip('\n\r') + str(app) + '\n'
                            outfile.write('#SERVICE {}:0:0:0:0:0:0:0:0:0:{}').format(service, line.replace(':', '%3a'))  # % (service, line.replace(':', '%3a')))
                            outfile.write('#DESCRIPTION {}').format(desk_tmp)  # % desk_tmp
                        elif line.startswith('#EXTINF'):
                            # desk_tmp = '%s' % line.split(',')[-1]
                            desk_tmp = '{}'.format(line.split(',')[-1])  # % line.split(',')[-1]
                        ch += 1
                    outfile.close()
                if os_path.isfile('/etc/enigma2/bouquets.tv'):
                    for line in open('/etc/enigma2/bouquets.tv'):
                        if bouquetname in line:
                            in_bouquets = 1
                    if in_bouquets == 0:
                        if os_path.isfile('%s%s' % (dir_enigma2, bouquetname)) and os_path.isfile('/etc/enigma2/bouquets.tv'):
                            vUtils.remove_line('/etc/enigma2/bouquets.tv', bouquetname)
                            with open('/etc/enigma2/bouquets.tv', 'a+') as f:
                                # outfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\r\n' % bouquetname)
                                line = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "{}" ORDER BY bouquet\n'.format(bouquetname)
                                if line not in f:
                                    f.write(line)
                                # outfile.close()
                                in_bouquets = 1
                vUtils.ReloadBouquets()
        except Exception as error:
            trace_error()
        return ch


# autostart
_session = None
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
                trace_error()
        self.update(constant)

    def startMain(self):
        name = url = ''
        if file_exists(PLUGIN_PATH + '/Favorite.txt'):
            with open(PLUGIN_PATH + '/Favorite.txt', 'r') as f:
                line = f.readline()
                name = line.split('###')[0]
                url = line.split('###')[1]
                '''# print('name %s and url %s:' % (name, url))
            # try:'''
            print('session start convert time')
            vid2 = vavoo(_session, name, url)
            # vid2.message2(name, url, False)
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


def add_skin_font():
    from enigma import addFont
    # addFont(filename, name, scale, isReplacement, render)
    addFont((FONTSTYPE), 'cvfont', 100, 1)
    addFont((FNTPath + '/lcd.ttf'), 'xLcd', 100, 1)


def add_skin_back():
    bakk = BACKTYPE
    if file_exists(BACKTYPE):
        cmd = 'cp -f ' + str(BACKTYPE) + ' ' + BackPath + '/default.png'
        print('add_skin_back cmd= ', cmd)
        os.system(cmd)
        os.system('sync')


def cfgmain(menuid, **kwargs):
    return [(_('Vavoo Stream Live'), main, 'Vavoo', 44)] if menuid == "mainmenu" else []


def main(session, **kwargs):
    try:
        if file_exists('/tmp/vavoo.log'):
            os.remove('/tmp/vavoo.log')
        add_skin_font()
        # add_skin_back()
        session.open(startVavoo)
    except Exception as error:
        trace_error()


def Plugins(**kwargs):
    icon = os_path.join(PLUGIN_PATH, 'plugin.png')
    mainDescriptor = PluginDescriptor(name=title_plug, description=_('Vavoo Stream Live'), where=PluginDescriptor.WHERE_MENU, icon=icon, fnc=cfgmain)
    result = [PluginDescriptor(name=title_plug, description=_('Vavoo Stream Live'), where=PluginDescriptor.WHERE_PLUGINMENU, icon=icon, fnc=main)
              # PluginDescriptor(name=title_plug, description="Vavoo Stream Live", where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart, wakeupfnc=get_next_wakeup),
              ]
    if cfg.stmain.value:
        result.append(mainDescriptor)
    return result
