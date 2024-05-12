#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
*        coded by Lululla              *
*             26/04/2024               *
****************************************
# --------------------#
# Info Linuxsat-support.com  corvoboys.org
'''
from __future__ import print_function
from . import Utils
from . import html_conv
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest
from Components.MultiContent import MultiContentEntryText
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import Standby
from Screens.InfoBarGenerics import InfoBarSubtitleSupport, InfoBarSummarySupport, \
    InfoBarNumberZap, InfoBarMenu, InfoBarEPG, InfoBarSeek, InfoBarMoviePlayerSummarySupport, \
    InfoBarAudioSelection, InfoBarNotifications, InfoBarServiceNotifications
from Tools.Directories import SCOPE_PLUGINS
try:
    from Tools.Directories import SCOPE_GUISKIN as SCOPE_SKIN
except ImportError:
    from Tools.Directories import SCOPE_SKIN
from Tools.Directories import resolveFilename
from enigma import RT_VALIGN_CENTER
from enigma import RT_HALIGN_LEFT
from enigma import eListboxPythonMultiContent
from enigma import eServiceReference
from enigma import eTimer
from enigma import gFont
from enigma import iPlayableService
from enigma import iServiceInformation
from enigma import loadPNG
from os.path import exists as file_exists
from os import path as os_path
import base64
import os
import re
import six
import ssl
import sys

PY3 = sys.version_info.major >= 3

if sys.version_info >= (2, 7, 9):
    try:
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None

currversion = '1.0'
title_plug = 'Vavoo '
desc_plugin = ('..:: Vavoo by Lululla %s ::.. ' % currversion)
PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('vavoo'))
pluglogo = os.path.join(PLUGIN_PATH, 'res/pics/logo.png')
stripurl = 'aHR0cHM6Ly92YXZvby50by9jaGFubmVscw=='
searchurl = 'aHR0cHM6Ly90aXZ1c3RyZWFtLndlYnNpdGUvcGhwX2ZpbHRlci9rb2RpMTkva29kaTE5LnBocD9tb2RlPW1vdmllJnF1ZXJ5PQ=='
_session = None

if Utils.isFHD():
    skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_pli/defaultListScreen_new.xml')
    if Utils.DreamOS():
        skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_cvs/defaultListScreen_new.xml')
else:
    skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_pli/defaultListScreen.xml')
    if Utils.DreamOS():
        skin_path = os.path.join(PLUGIN_PATH, 'skin/skin_cvs/defaultListScreen.xml')


def returnIMDB(text_clear):
    TMDB = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('TMDB'))
    IMDb = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('IMDb'))
    if file_exists(TMDB):
        try:
            from Plugins.Extensions.TMBD.plugin import TMBD
            text = html_conv.html_unescape(text_clear)
            _session.open(TMBD.tmdbScreen, text, 0)
        except Exception as e:
            print("[XCF] Tmdb: ", e)
        return True
    elif file_exists(IMDb):
        try:
            from Plugins.Extensions.IMDb.plugin import main as imdb
            text = html_conv.html_unescape(text_clear)
            imdb(_session, text)
        except Exception as e:
            print("[XCF] imdb: ", e)
        return True
    else:
        text_clear = html_conv.html_unescape(text_clear)
        _session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)
        return True
    return False


class m2list(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)
        if Utils.isFHD():
            self.l.setItemHeight(50)
            textfont = int(28)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(50)
            textfont = int(24)
            self.l.setFont(0, gFont('Regular', textfont))


def show_(name, link):
    res = [(name, link)]
    if Utils.isFHD():
        res.append(MultiContentEntryText(pos=(0, 0), size=(1900, 50), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryText(pos=(0, 0), size=(1200, 50), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def cat_(letter, link):
    res = [(letter, link)]
    if Utils.isFHD():
        res.append(MultiContentEntryText(pos=(0, 0), size=(1900, 50), font=0, text=letter, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryText(pos=(0, 0), size=(1200, 50), font=0, text=letter, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def rvoneListEntry(name):
    res = [name]
    pngx = os.path.join(PLUGIN_PATH, 'skin/pics/plugin.png')
    if Utils.isFHD():
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 12), size=(34, 25), png=loadPNG(pngx)))
        res.append(MultiContentEntryText(pos=(60, 0), size=(1900, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 12), size=(34, 25), png=loadPNG(pngx)))
        res.append(MultiContentEntryText(pos=(60, 0), size=(1000, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def showlist(data, list):
    icount = 0
    plist = []
    for line in data:
        name = data[icount]
        plist.append(rvoneListEntry(name))
        icount += 1
        list.setList(plist)


Panel_list = [
    ('Albania'),
    ('Arabia'),
    ('Balkans'),
    ('Bulgaria'),
    ('France'),
    ('Germany'),
    ('Italy'),
    ('Netherlands'),
    ('Poland'),
    ('Portugal'),
    ('Romania'),
    ('Russia'),
    ('Spain'),
    ('Turkey'),
    ('United Kingdom'),
    # ('SEARCH'),
    ]


class MainVavoo(Screen):
    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        with open(skin_path, 'r') as f:
            self.skin = f.read()
        self.menulist = []
        self['menulist'] = m2list([])
        self['red'] = Label(_('Exit'))
        # self['green'] = Label(_('Export'))
        self['Title'] = Label(title_plug)
        self['name'] = Label('')
        self['text'] = Label('Vavoo Stream Live by Lululla')
        self.currentList = 'menulist'
        self.loading_ok = False
        self.count = 0
        self.loading = 0
        self.url = Utils.b64decoder(stripurl)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'DirectionActions',
                                     'MovieSelectionActions'], {'up': self.up,
                                                                'down': self.down,
                                                                'left': self.left,
                                                                'right': self.right,
                                                                'ok': self.ok,
                                                                # 'green': self.message2,
                                                                'cancel': self.close,
                                                                'red': self.close}, -1)
        self.timer = eTimer()
        if Utils.DreamOS():
            self.timer_conn = self.timer.timeout.connect(self.cat)
        else:
            self.timer.callback.append(self.cat)
        self.timer.start(500, True)

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
            content = Utils.getUrl(self.url)
            if six.PY3:
                content = six.ensure_str(content)
            # print('content: ', content)
            # "country": "Balkans", "id": 1572002411, "name": "RTS 1 (7)", "p": 0
            regexcat = '"country".*?"(.*?)".*?"id".*?"name".*?".*?"'
            match = re.compile(regexcat, re.DOTALL).findall(content)
            for country in match:
                if country not in self.items_tmp:
                    # print(country + ' I\n')
                    self.items_tmp.append(country)
                    item = country + "###" + self.url + '\n'
                    items.append(item)
            # print('self.items_tmp:', self.items_tmp)
            items.sort()
            for item in items:
                name = item.split('###')[0]
                url = item.split('###')[1]
                if name not in self.cat_list:
                    # print('country III =', name)
                    self.cat_list.append(show_(name, url))
            if len(self.cat_list) < 0:
                return
            else:
                self['menulist'].l.setList(self.cat_list)
                self['menulist'].moveToIndex(0)
                auswahl = self['menulist'].getCurrent()[0][0]
                self['name'].setText(str(auswahl))
        except Exception as e:
            print(e)

    def ok(self):
        self.keyNumberGlobalCB(self['menulist'].getSelectedIndex())

    def keyNumberGlobalCB(self, idx):
        global namex
        namex = ''
        sel = self.menu_list[idx]
        if sel:
            namex = sel
            lnk = Utils.b64decoder(stripurl)
            self.session.open(vavoo, namex, lnk)
        else:
            return

    def exit(self):
        self.close()


class vavoo(Screen):
    def __init__(self, session, name, url):
        self.session = session
        Screen.__init__(self, session)
        with open(skin_path, 'r') as f:
            self.skin = f.read()
        self.menulist = []
        self['menulist'] = m2list([])
        self['red'] = Label(_('Back'))
        # self['green'] = Label(_('Export'))
        self['Title'] = Label(title_plug)
        self['name'] = Label('')
        self['text'] = Label('Vavoo Stream Live by Lululla')
        self.currentList = 'menulist'
        self.loading_ok = False
        self.count = 0
        self.loading = 0
        self.name = name
        self.url = url
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'DirectionActions',
                                     'MovieSelectionActions'], {'up': self.up,
                                                                'down': self.down,
                                                                'left': self.left,
                                                                'right': self.right,
                                                                'ok': self.ok,
                                                                # 'green': self.message2,
                                                                'cancel': self.close,
                                                                'red': self.close}, -1)
        self.timer = eTimer()
        if Utils.DreamOS():
            self.timer_conn = self.timer.timeout.connect(self.cat)
        else:
            self.timer.callback.append(self.cat)
        self.timer.start(500, True)

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
        try:
            content = Utils.getUrl(self.url)
            if six.PY3:
                content = six.ensure_str(content)
            print('content: ', content)
            # "country": "Balkans", "id": 1572002411, "name": "RTS 1 (7)", "p": 0
            names = self.name
            print('country=', names)
            regexcat = '"country".*?"(.*?)".*?"id"(.*?)"name".*?"(.*?)"'
            match = re.compile(regexcat, re.DOTALL).findall(content)
            for country, ids, name in match:
                if country != names:
                    continue
                print(country + '\n' + name + '\n' + str(ids))
                ids = ids.replace(':', '').replace(' ', '').replace(',', '')
                url = 'http://vavoo.to/play/' + str(ids) + '/index.m3u8'
                name = Utils.decodeHtml(name)
                item = name + "###" + url + '\n'
                items.append(item)
            items.sort()
            for item in items:
                name = item.split('###')[0]
                url = item.split('###')[1]

                self.cat_list.append(show_(name, url))
            print('country=', self.name)
            if len(self.cat_list) < 0:
                return
            else:
                self['menulist'].l.setList(self.cat_list)
                self['menulist'].moveToIndex(0)
                auswahl = self['menulist'].getCurrent()[0][0]
                self['name'].setText(str(auswahl))
        except Exception as e:
            print(e)

    def ok(self):
        name = self['menulist'].getCurrent()[0][0]
        url = self['menulist'].getCurrent()[0][1]
        try:
            self.play_that_shit(url, name)
        except Exception as e:
            print(e)

    def play_that_shit(self, url, name):
        self.session.open(Playstream2, name, url)


class TvInfoBarShowHide():
    """ InfoBar show/hide control, accepts toggleShow and hide actions, might start
    fancy animations. """
    STATE_HIDDEN = 0
    STATE_HIDING = 1
    STATE_SHOWING = 2
    STATE_SHOWN = 3
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
        self.hideTimer.start(5000, True)
        self.onShow.append(self.__onShow)
        self.onHide.append(self.__onHide)

    def OkPressed(self):
        self.toggleShow()

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

    def serviceStarted(self):
        if self.execing:
            if config.usage.show_infobar_on_zap.value:
                self.doShow()

    def __onShow(self):
        self.__state = self.STATE_SHOWN
        self.startHideTimer()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            self.hideTimer.stop()
            idx = config.usage.infobar_timeout.index
            if idx:
                self.hideTimer.start(idx * 1500, True)

    def __onHide(self):
        self.__state = self.STATE_HIDDEN

    def doShow(self):
        self.hideTimer.stop()
        self.show()
        self.startHideTimer()

    def doTimerHide(self):
        self.hideTimer.stop()
        if self.__state == self.STATE_SHOWN:
            self.hide()

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

    def debug(obj, text=""):
        print(text + " %s\n" % obj)


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

    def __init__(self, session, name, url):
        global streaml, _session
        Screen.__init__(self, session)
        self.session = session
        _session = session
        self.skinName = 'MoviePlayer'
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
        self.name = Utils.decodeHtml(name)
        self.state = self.STATE_PLAYING
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self['actions'] = ActionMap(['MoviePlayerActions',
                                     'MovieSelectionActions',
                                     'MediaPlayerActions',
                                     'EPGSelectActions',
                                     'MediaPlayerSeekActions',
                                     'ColorActions',
                                     'OkCancelActions',
                                     'InfobarShowHideActions',
                                     'InfobarActions',
                                     'InfobarSeekActions'], {'epg': self.showIMDB,
                                                             'info': self.showIMDB,
                                                             # 'info': self.cicleStreamType,
                                                             'tv': self.cicleStreamType,
                                                             'stop': self.leavePlayer,
                                                             'cancel': self.cancel,
                                                             'back': self.cancel}, -1)
        if '8088' in str(self.url):
            # self.onLayoutFinish.append(self.slinkPlay)
            self.onFirstExecBegin.append(self.slinkPlay)
        else:
            # self.onLayoutFinish.append(self.cicleStreamType)
            self.onFirstExecBegin.append(self.cicleStreamType)
        self.onClose.append(self.cancel)

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
        temp = int(self.getAspect())
        temp = temp + 1
        if temp > 6:
            temp = 0
        self.new_aspect = temp
        self.setAspect(temp)

    def showinfo(self):
        # debug = True
        sTitle = ''
        sServiceref = ''
        try:
            servicename, serviceurl = Utils.getserviceinfo(self.sref)
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
        global streml
        streaml = False
        # from itertools import cycle, islice
        self.servicetype = '4097'
        print('servicetype1: ', self.servicetype)
        url = str(self.url)
        if str(os.path.splitext(self.url)[-1]) == ".m3u8":
            if self.servicetype == "1":
                self.servicetype = "4097"
        # currentindex = 0
        # streamtypelist = ["4097"]
        # if "youtube" in str(self.url):
            # self.mbox = self.session.open(MessageBox, _('For Stream Youtube coming soon!'), MessageBox.TYPE_INFO, timeout=5)
            # return
        # if Utils.isStreamlinkAvailable():
            # streamtypelist.append("5002")
            # streaml = True
        # if os.path.exists("/usr/bin/gstplayer"):
            # streamtypelist.append("5001")
        # if os.path.exists("/usr/bin/exteplayer3"):
            # streamtypelist.append("5002")
        # if os.path.exists("/usr/bin/apt-get"):
            # streamtypelist.append("8193")
        # for index, item in enumerate(streamtypelist, start=0):
            # if str(item) == str(self.servicetype):
                # currentindex = index
                # break
        # nextStreamType = islice(cycle(streamtypelist), currentindex + 1, None)
        # self.servicetype = str(next(nextStreamType))
        print('servicetype2: ', self.servicetype)
        self.openTest(self.servicetype, url)

    def up(self):
        pass

    def down(self):
        self.up()

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
        streaml = False
        self.close()

    def leavePlayer(self):
        self.close()


def main(session, **kwargs):
    try:
        session.open(MainVavoo)
    except:
        import traceback
        traceback.print_exc()


def Plugins(**kwargs):
    icona = os.path.join(PLUGIN_PATH, 'plugin.png')
    result = [PluginDescriptor(name=title_plug, description=_('Vavoo Stream Live'), where=PluginDescriptor.WHERE_PLUGINMENU, icon=icona, fnc=main)]
    return result
