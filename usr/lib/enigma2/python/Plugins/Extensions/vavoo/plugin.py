#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
****************************************
*        coded by Lululla              *
*             26/04/2024               *
* thank's to @oktus for image screen   *
****************************************
# ----- thank's Kiddac for support ---- #
# Info Linuxsat-support.com & corvoboys.org
"""


# Standard library imports
import os
import re
import six
import ssl
import sys
import codecs
from os.path import exists as file_exists
# Enigma2 components
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import (MultiContentEntryPixmapAlphaTest, MultiContentEntryText)
from Components.ServiceEventTracker import (ServiceEventTracker, InfoBarBase)
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.InfoBarGenerics import (InfoBarSubtitleSupport, InfoBarMenu, InfoBarSeek, InfoBarAudioSelection, InfoBarNotifications)
from Tools.Directories import (SCOPE_PLUGINS, resolveFilename)
from enigma import (RT_VALIGN_CENTER, RT_HALIGN_LEFT, eListboxPythonMultiContent, eServiceReference, eTimer, gFont, iPlayableService, iServiceInformation, loadPNG, getDesktop)
from Components.config import ConfigSubsection
from Components.config import ConfigEnableDisable
from Components.config import ConfigSelectionNumber, ConfigClock
from Components.config import ConfigSelection, getConfigListEntry
from Components.config import ConfigText
from Components.ConfigList import ConfigListScreen
import time

# Local application/library-specific imports
from . import _
from . import vUtils



PY3 = sys.version_info.major >= 3

if sys.version_info >= (2, 7, 9):
    try:
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None


currversion = '1.5'
title_plug = 'Vavoo'
desc_plugin = ('..:: Vavoo by Lululla %s ::..' % currversion)
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('vavoo'))
pluglogo = os.path.join(PLUGIN_PATH, 'plugin.png')
stripurl = 'aHR0cHM6Ly92YXZvby50by9jaGFubmVscw=='
_session = None
enigma_path = '/etc/enigma2/'
screenwidth = getDesktop(0).size()
url1 = 'https://huhu.to'
url2 = 'https://oha.to'
url3 = 'https://www.kool.to'
url4 = 'https://vavoo.to'

# config section
config.plugins.vavoo = ConfigSubsection()
cfg = config.plugins.vavoo
cfg.autobouquetupdate = ConfigEnableDisable(default=False)
cfg.timetype = ConfigSelection(default="interval", choices=[("interval", _("interval")), ("fixed time", _("fixed time"))])
cfg.updateinterval = ConfigSelectionNumber(default=24, min=1, max=48, stepwidth=1)
cfg.fixedtime = ConfigClock(default=46800)
cfg.last_update = ConfigText(default="Never")
cfg.ipv6 = ConfigEnableDisable(default=False)
if os.path.islink('/etc/rc3.d/S99ipv6dis.sh'):
    cfg.ipv6.setValue(True)
    cfg.ipv6.save()

# set screen section
if screenwidth.width() == 2560:
    skin_path = os.path.join(PLUGIN_PATH, 'skin/skin/defaultListScreen_wqhd.xml')
    skin_config = os.path.join(PLUGIN_PATH, 'skin/skin/vavoo_config_wqhd.xml')
    # if os.path.exists('/var/lib/dpkg/status'):
        # skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_cvs/defaultListScreen_uhd.xml')
elif screenwidth.width() == 1920:
    skin_path = os.path.join(PLUGIN_PATH, 'skin/skin/defaultListScreen_fhd.xml')
    skin_config = os.path.join(PLUGIN_PATH, 'skin/skin/vavoo_config_fhd.xml')
    # if os.path.exists('/var/lib/dpkg/status'):
        # skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_cvs/defaultListScreen_new.xml')
else:
    skin_path = os.path.join(PLUGIN_PATH, 'skin/skin/defaultListScreen.xml')
    skin_config = os.path.join(PLUGIN_PATH, 'skin/skin/vavoo_config.xml')
    # if os.path.exists('/var/lib/dpkg/status'):
        # skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_cvs/defaultListScreen.xml')


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


def add_skin_font():
    from enigma import addFont
    font_path = PLUGIN_PATH + '/resolver/'
    addFont(font_path + 'Questrial-Regular.ttf', 'cvfont', 100, 0)
    addFont(font_path + 'lcd.ttf', 'Lcd', 100, 0)


def raises(url):
    try:
        import requests
        from requests.adapters import HTTPAdapter, Retry
        retries = Retry(total=1, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retries)
        http = requests.Session()
        http.mount("http://", adapter)
        http.mount("https://", adapter)
        r = http.get(url, headers={'User-Agent': vUtils.RequestAgent()}, timeout=10, verify=False)  # , stream=True)
        r.raise_for_status()
        if r.status_code == requests.codes.ok:
            return True
    except Exception as e:
        print('error requests -----------> ', e)
    return False


def zServer(opt=0, server=None, port=None):
    url = []
    import requests
    try:
        from urllib.error import HTTPError
    except ImportError:
        from urllib2 import HTTPError
    try:
        if raises(url1):
            return str(url1)
        elif raises(url2):
            return str(url2)
        elif raises(url3):
            return str(url3)
        elif raises(url4):
            return str(url4)
        else:
            return None
    except HTTPError as err:
        print(err.code)


class m2list(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)

        if screenwidth.width() == 2560:
            self.l.setItemHeight(60)
            textfont = int(44)
            self.l.setFont(0, gFont('Regular', textfont))
        elif os.path.exists('/var/lib/dpkg/status'):
            self.l.setItemHeight(50)
            textfont = int(45)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(50)
            textfont = int(28)
            self.l.setFont(0, gFont('Regular', textfont))


Panel_list = ("Albania", "Arabia", "Balkans", "Bulgaria",
              "France", "Germany", "Italy", "Netherlands",
              "Poland", "Portugal", "Romania", "Russia",
              "Spain", "Turkey", "United Kingdom")


def show_(name, link):
    res = [(name, link)]

    pngx = PLUGIN_PATH + '/skin/pics/Internat.png'
    if any(s in name for s in Panel_list):
        pngx = PLUGIN_PATH + '/skin/pics/%s.png' % name
    else:
        pngx = PLUGIN_PATH + '/skin/pics/vavoo_ico.png'
        print('pngx =:', pngx)
    if os.path.isfile(pngx):
        # print('pngx =:', pngx)
        if screenwidth.width() == 2560:
            res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 10), size=(60, 40), png=loadPNG(pngx)))
            res.append(MultiContentEntryText(pos=(90, 0), size=(800, 60), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
        elif screenwidth.width() == 1920:
            res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 5), size=(60, 40), png=loadPNG(pngx)))
            res.append(MultiContentEntryText(pos=(85, 0), size=(600, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
        else:
            res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 5), size=(60, 40), png=loadPNG(pngx)))
            res.append(MultiContentEntryText(pos=(85, 0), size=(500, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
        return res


class vavoo_config(Screen, ConfigListScreen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        with codecs.open(skin_config, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.setup_title = ('Vavoo Config')
        self.list = []
        self.onChangedEntry = []
        self["version"] = Label(currversion)
        self['statusbar'] = Label()
        self["description"] = Label("")
        self["red"] = Label(_("Back"))
        self["green"] = Label(_("Save"))
        # self["blue"] = Label(_("Import") + " txt")
        # self["yellow"] = Label(_("Import") + " sh")
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'DirectionActions'], {
            "cancel": self.extnok,
            "left": self.keyLeft,
            "right": self.keyRight,
            "up": self.keyUp,
            "down": self.keyDown,
            # "yellow": self.iptv_sh,
            "green": self.save,
            # "blue": self.ImportInfosServer,
            # "showVirtualKeyboard": self.KeyText,
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

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        indent = "- "

        self.list.append(getConfigListEntry(_("Ipv6 state lan (On/Off), now is:"), cfg.ipv6, (_("Active or Disactive lan Ipv6, now is: %s") % cfg.ipv6.value)))
        self.list.append(getConfigListEntry(_("Automatic bouquet update (schedule):"), cfg.autobouquetupdate, (_("Active Automatic Bouquet Update"))))
        if cfg.autobouquetupdate.getValue():
            self.list.append(getConfigListEntry(indent + (_("Schedule type:")), cfg.timetype, (_("At an interval of hours or at a fixed time"))))
            if cfg.timetype.value == "interval":
                self.list.append(getConfigListEntry(2 * indent + (_("Update interval (hours):")), cfg.updateinterval, (_("Configure every interval of hours from now"))))
            if cfg.timetype.value == "fixed time":
                self.list.append(getConfigListEntry(2 * indent + (_("Time to start update:")), cfg.fixedtime, (_("Configure at a fixed time"))))
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
        except Exception as e:
            print("Error ", e)

    def ipv6(self):
        if os.path.islink('/etc/rc3.d/S99ipv6dis.sh'):
            self.session.openWithCallback(self.ipv6check, MessageBox, _("Ipv6 [Off]?"), MessageBox.TYPE_YESNO, timeout=5, default=True)
        else:
            self.session.openWithCallback(self.ipv6check, MessageBox, _("Ipv6 [On]?"), MessageBox.TYPE_YESNO, timeout=5, default=True)

    def ipv6check(self, result):
        if result:
            if os.path.islink('/etc/rc3.d/S99ipv6dis.sh'):
                os.unlink('/etc/rc3.d/S99ipv6dis.sh')
                cfg.ipv6.setValue(False)
                # self['blue'].setText('IPV6 Off')
            else:
                os.system("echo '#!/bin/bash")
                os.system("echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6' > /etc/init.d/ipv6dis.sh")
                os.system("chmod 755 /etc/init.d/ipv6dis.sh")
                os.system("ln -s /etc/init.d/ipv6dis.sh /etc/rc3.d/S99ipv6dis.sh")
                cfg.ipv6.setValue(True)
                # self['blue'].setText('IPV6 On')
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
            # self.xml_plugin()
            self.session.open(MessageBox, _("Settings saved successfully !"), MessageBox.TYPE_INFO, timeout=5)
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


class MainVavoo(Screen):
    def __init__(self, session):
        self.session = session
        global _session
        _session = session
        Screen.__init__(self, session)
        with codecs.open(skin_path, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.menulist = []
        self['menulist'] = m2list([])
        self['red'] = Label(_('Exit'))
        self['green'] = Label(_('Remove') + ' Fav')
        self['yellow'] = Label()
        self['blue'] = Label('IPV6 Off')
        if os.path.islink('/etc/rc3.d/S99ipv6dis.sh'):
            self['blue'].setText('IPV6 On')
        self['name'] = Label('Loading...')
        self['version'] = Label(currversion)
        self.currentList = 'menulist'
        self.loading_ok = False
        self.count = 0
        self.loading = 0
        self.url = vUtils.b64decoder(stripurl)
        self['actions'] = ActionMap(['MenuActions', 'OkCancelActions', 'ColorActions', 'EPGSelectActions', 'DirectionActions',  'MovieSelectionActions'], {
            'up': self.up,
            'down': self.down,
            'left': self.left,
            'right': self.right,
            'ok': self.ok,
            'menu': self.goConfig,
            'green': self.msgdeleteBouquets,
            # 'blue': self.ipv6,
            'cancel': self.close,
            'info': self.info,
            'red': self.close
        }, -1)

        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.cat)
        except:
            self.timer.callback.append(self.cat)
        self.timer.start(500, True)
        self.onShow.append(self.check)

    def check(self):
        if os.path.islink('/etc/rc3.d/S99ipv6dis.sh'):
            self['blue'].setText('IPV6 On')
        else:
            self['blue'].setText('IPV6 Off')

    def goConfig(self):
        self.session.open(vavoo_config)

    def info(self):
        aboutbox = self.session.open(MessageBox, _('%s\n\n\nThanks:\n@KiddaC\n@oktus\nAll staff Linuxsat-support.com\nCorvoboys - Forum\n\nThis plugin is free,\nno stream direct on server\nbut only free channel found on the net') % desc_plugin, MessageBox.TYPE_INFO)
        aboutbox.setTitle(_('Info Vavoo'))

    def up(self):
        self[self.currentList].up()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(auswahl))

    def down(self):
        self[self.currentList].down()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(auswahl))

    def left(self):
        self[self.currentList].pageUp()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(auswahl))

    def right(self):
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
            if six.PY3:
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
                    self.cat_list.append(show_(name, url))
            if len(self.cat_list) < 1:
                return
            else:
                self['menulist'].l.setList(self.cat_list)
                self['menulist'].moveToIndex(0)
                auswahl = self['menulist'].getCurrent()[0][0]
                self['name'].setText(str(auswahl))
        except Exception as e:
            self['name'].setText('Error')
            print(e)

    def ok(self):
        name = self['menulist'].getCurrent()[0][0]
        url = self['menulist'].getCurrent()[0][1]
        try:
            self.session.open(vavoo, name, url)
        except Exception as e:
            print(e)

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
                os.rename(os.path.join(enigma_path, 'bouquets.tv'), os.path.join(enigma_path, 'bouquets.tv.bak'))
                tvfile = open(os.path.join(enigma_path, 'bouquets.tv'), 'w+')
                bakfile = open(os.path.join(enigma_path, 'bouquets.tv.bak'))
                for line in bakfile:
                    if '.vavoo_' not in line:
                        tvfile.write(line)
                bakfile.close()
                tvfile.close()
                self.session.open(MessageBox, _('Vavoo Favorites List have been removed'), MessageBox.TYPE_INFO, timeout=5)
                vUtils.ReloadBouquets()
            except Exception as ex:
                print(str(ex))
                raise


class vavoo(Screen):
    def __init__(self, session, name, url):
        self.session = session
        global _session
        _session = session
        Screen.__init__(self, session)
        with codecs.open(skin_path, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.menulist = []
        global search_ok
        search_ok = False
        self['menulist'] = m2list([])
        self['red'] = Label(_('Back'))
        self['green'] = Label(_('Export') + ' Fav')
        self['yellow'] = Label(_('Search'))
        self['blue'] = Label('IPV6 Off')
        if os.path.islink('/etc/rc3.d/S99ipv6dis.sh'):
            self['blue'].setText('IPV6 On')
        self['name'] = Label('Loading ...')
        self['version'] = Label(currversion)
        self.currentList = 'menulist'
        self.loading_ok = False
        self.count = 0
        self.loading = 0
        self.name = name
        self.url = url
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'EPGSelectActions', 'DirectionActions', 'MovieSelectionActions', 'VirtualKeyboardActions'], {
            'up': self.up,
            'down': self.down,
            'left': self.left,
            'right': self.right,
            'ok': self.ok,
            'green': self.message1,
            'yellow': self.search_vavoo,
            # 'blue': self.ipv6,
            'cancel': self.backhome,
            'info': self.info,
            'red': self.backhome
        }, -1)

        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.cat)
        except:
            self.timer.callback.append(self.cat)
        self.timer.start(500, True)
        self.onShow.append(self.check)

    def check(self):
        if os.path.islink('/etc/rc3.d/S99ipv6dis.sh'):
            self['blue'].setText('IPV6 On')
        else:
            self['blue'].setText('IPV6 Off')

    def backhome(self):
        if search_ok is True:
            # global search_ok
            # search_ok = False
            self.cat()
        else:
            self.close()

    def info(self):
        aboutbox = self.session.open(MessageBox, _('%s\n\n\nThanks:\n@KiddaC\n@oktus\nAll staff Linuxsat-support.com\nCorvoboys - Forum\n\nThis plugin is free,\nno stream direct on server\nbut only free channel found on the net') % desc_plugin, MessageBox.TYPE_INFO)
        aboutbox.setTitle(_('Info Vavoo'))

    def up(self):
        self[self.currentList].up()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(auswahl))

    def down(self):
        self[self.currentList].down()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(auswahl))

    def left(self):
        self[self.currentList].pageUp()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(auswahl))

    def right(self):
        self[self.currentList].pageDown()
        auswahl = self['menulist'].getCurrent()[0][0]
        self['name'].setText(str(auswahl))

    def cat(self):
        self.cat_list = []
        items = []
        xxxname = '/tmp/' + self.name + '.m3u'
        server = zServer(0, None, None)
        global search_ok
        search_ok = False
        try:
            with open(xxxname, 'w') as outfile:
                outfile.write('#NAME %s\r\n' % self.name.capitalize())
                content = vUtils.getUrl(self.url)
                if six.PY3:
                    content = six.ensure_str(content)
                names = self.name
                regexcat = '"country".*?"(.*?)".*?"id"(.*?)"name".*?"(.*?)"'
                match = re.compile(regexcat, re.DOTALL).findall(content)
                for country, ids, name in match:
                    if country != names:
                        continue
                    ids = ids.replace(':', '').replace(' ', '').replace(',', '')
                    # url = 'http://vavoo.to/play/' + str(ids) + '/index.m3u8'
                    url = str(server) + '/play/' + str(ids) + '/index.m3u8'
                    name = vUtils.decodeHtml(name)
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
                    self.cat_list.append(show_(name, url))
                    # make m3u
                    nname = '#EXTINF:-1,' + str(name) + '\n'
                    outfile.write(nname)
                    outfile.write(str(url))
                outfile.close()
                if len(self.cat_list) < 1:
                    return
                else:
                    self['menulist'].l.setList(self.cat_list)
                    self['menulist'].moveToIndex(0)
                    auswahl = self['menulist'].getCurrent()[0][0]
                    self['name'].setText(str(auswahl))
        except Exception as e:
            self['name'].setText('Error')
            print(e)

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
                        urlx = url
                        self.cat_list.append(show_(namex, urlx))
                # print('N. channel=', len(self.cat_list))
                if len(self.cat_list) < 1:
                    _session.open(MessageBox, _('No channels found in search!!!'), MessageBox.TYPE_INFO, timeout=5)
                    return
                else:
                    self['menulist'].l.setList(self.cat_list)
                    self['menulist'].moveToIndex(0)
                    auswahl = self['menulist'].getCurrent()[0][0]
                    self['name'].setText(str(auswahl))
            except Exception as e:
                self['name'].setText('Error')
                search_ok = False
                print(e)

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
        except Exception as e:
            print(e)

    def play_that_shit(self, url, name, index, item, cat_list):
        self.session.open(Playstream2, name, url, index, item, cat_list)

    def message1(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.message1, MessageBox, _('Do you want to Convert to favorite .tv ?\n\nAttention!! It may take some time depending\non the number of streams contained !!!'))
        elif answer:
            name = self.name
            url = self.url
            self.message2(name, url)

    def message2(self, name, url):
        # print('url: ', url)
        service = '4097'
        ch = 0
        ch = convert_bouquet(service, name, url)
        if ch > 0:
            localtime = time.asctime(time.localtime(time.time()))
            cfg.last_update.value = localtime
            cfg.last_update.save()
            _session.open(MessageBox, _('bouquets reloaded..\nWith %s channel' % str(ch)), MessageBox.TYPE_INFO, timeout=5)
        else:
            _session.open(MessageBox, _('Download Error'), MessageBox.TYPE_INFO, timeout=5)


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
        self.url = url
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

        if '8088' in str(self.url):
            self.onFirstExecBegin.append(self.slinkPlay)
        else:
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
        except Exception as e:
            print(e)
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
        except Exception as ex:
            print(str(ex))
            print("Error: can't find Playstream2 in live_to_stream")

    def slinkPlay(self):
        url = self.url
        name = self.name
        ref = "{0}:{1}".format(url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        self.sref = sref
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def openTest(self, servicetype, url):
        name = self.name
        ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('reference:   ', ref)
        if streaml is True:
            url = 'http://127.0.0.1:8088/' + str(url)
            ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
            print('streaml reference:   ', ref)
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        self.sref = sref
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def cicleStreamType(self):
        self.servicetype = '4097'
        print('servicetype1: ', self.servicetype)
        url = str(self.url)
        if str(os.path.splitext(self.url)[-1]) == ".m3u8":
            if self.servicetype == "1":
                self.servicetype = "4097"
        print('servicetype2: ', self.servicetype)
        self.openTest(self.servicetype, url)

    def doEofInternal(self, playing):
        self.close()

    def __evEOF(self):
        self.end = True

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
        if os.path.isfile('/tmp/hls.avi'):
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
    dir_enigma2 = '/etc/enigma2/'
    files = '/tmp/' + name + '.m3u'
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
    bouquetname = 'userbouquet.vavoo_%s.%s' % (name_file.lower(), type.lower())
    if os.path.exists(str(files)):
        sleep(5)
        ch = 0
        try:
            if os.path.isfile(files) and os.stat(files).st_size > 0:
                # print('ChannelList is_tmp exist in playlist')
                desk_tmp = ''
                in_bouquets = 0
                with open('%s%s' % (dir_enigma2, bouquetname), 'w') as outfile:
                    outfile.write('#NAME %s\r\n' % name_file.capitalize())
                    for line in open(files):
                        if line.startswith('http://') or line.startswith('https'):
                            outfile.write('#SERVICE %s:0:1:1:0:0:0:0:0:0:%s' % (service, line.replace(':', '%3a')))
                            outfile.write('#DESCRIPTION %s' % desk_tmp)
                        elif line.startswith('#EXTINF'):
                            desk_tmp = '%s' % line.split(',')[-1]
                        elif '<stream_url><![CDATA' in line:
                            outfile.write('#SERVICE %s:0:1:1:0:0:0:0:0:0:%s\r\n' % (service, line.split('[')[-1].split(']')[0].replace(':', '%3a')))
                            outfile.write('#DESCRIPTION %s\r\n' % desk_tmp)
                        elif '<title>' in line:
                            if '<![CDATA[' in line:
                                desk_tmp = '%s\r\n' % line.split('[')[-1].split(']')[0]
                            else:
                                desk_tmp = '%s\r\n' % line.split('<')[1].split('>')[1]
                        ch += 1
                    outfile.close()
                if os.path.isfile('/etc/enigma2/bouquets.tv'):
                    for line in open('/etc/enigma2/bouquets.tv'):
                        if bouquetname in line:
                            in_bouquets = 1
                    if in_bouquets == 0:
                        if os.path.isfile('%s%s' % (dir_enigma2, bouquetname)) and os.path.isfile('/etc/enigma2/bouquets.tv'):
                            vUtils.remove_line('/etc/enigma2/bouquets.tv', bouquetname)
                            with open('/etc/enigma2/bouquets.tv', 'a+') as outfile:
                                outfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\r\n' % bouquetname)
                                outfile.close()
                                in_bouquets = 1
                    vUtils.ReloadBouquets()
            return ch
        except Exception as e:
            print('error convert iptv ', e)


_session = None
autoStartTimer = None
_firstStart = True


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
        # self.update()  # issue loop

    def get_wake_time(self):
        if cfg.autobouquetupdate.value is True:
            if cfg.timetype.value == "interval":
                interval = int(cfg.updateinterval.value)
                nowt = time.time()
                return int(nowt) + interval * 60 * 60
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
        now = int(nowt)
        if wake > 0:
            if wake < now + constant:
                if cfg.timetype.value == "interval":
                    interval = int(cfg.updateinterval.value)
                    wake += interval * 60 * 60
                elif cfg.timetype.value == "fixed time":
                    wake += 86400
            next = wake - now
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
        if wake - now < 60:
            try:
                self.startMain()
                self.update()
                localtime = time.asctime(time.localtime(time.time()))
                cfg.last_update.value = localtime
                cfg.last_update.save()
            except Exception as e:
                print(e)
        self.update(constant)

    def startMain(self):
        name = url = ''
        if os.path.exists(PLUGIN_PATH + '/Favorite.txt'):
            with open(PLUGIN_PATH + '/Favorite.txt', 'r') as f:
                line = f.readline()
                name = line.split('###')[0]
                url = line.split('###')[1]
                # print('name %s and url %s:' % (name, url))
            # try:
            print('session start convert time')
            vid2 = vavoo(_session, name, url)
            vid2.message2(name, url)
            # except Exception as e:
                # print('timeredit error vavoo', e)


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


def main(session, **kwargs):
    try:
        add_skin_font()
        session.open(MainVavoo)
        # session.openWithCallback(check_configuring, MainVavoo)
    except:
        import traceback
        traceback.print_exc()


def Plugins(**kwargs):
    icon = os.path.join(PLUGIN_PATH, 'plugin.png')
    result = [PluginDescriptor(name=title_plug, description="Vavoo Stream Live", where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart, wakeupfnc=get_next_wakeup),
              PluginDescriptor(name=title_plug, description=_('Vavoo Stream Live'), where=PluginDescriptor.WHERE_PLUGINMENU, icon=icon, fnc=main)]
    return result
