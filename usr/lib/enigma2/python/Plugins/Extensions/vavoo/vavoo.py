#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
*        coded by Lululla              *
*             26/04/2024               *
****************************************
# --------------------#
# Info Linuxsat-support.com  corvoboys.org

put to menu.xml this:

<!--  <id val="mainmenu"/>  -->
 
<item weight="11" level="0" text="NSS Vavoo Stream Live" entryID="vavoo">
<code>
from Screens.vavoo import MainVavoo
self.session.open(MainVavoo)  
</code>
</item>


'''
from __future__ import print_function
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest
from Components.MultiContent import MultiContentEntryText
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.config import config
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.InfoBarGenerics import InfoBarSubtitleSupport, \
    InfoBarMenu, InfoBarSeek, InfoBarAudioSelection, InfoBarNotifications
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
from six import unichr, iteritems  # ensure_str
from six.moves import html_entities
import types
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    bytes = bytes
    unicode = str
    from urllib.request import urlopen
    from urllib.request import Request
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
    MAXSIZE = sys.maxsize
else:
    str = str
    from urllib2 import urlopen
    from urllib2 import Request
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str
    if sys.platform.startswith("java"):
        # Jython always uses 32 bits.
        MAXSIZE = int((1 << 31) - 1)
    else:
        # It's possible to have sizeof(long) != sizeof(Py_ssize_t).
        class X(object):

            def __len__(self):
                return 1 << 31
        try:
            len(X())
        except OverflowError:
            # 32-bit
            MAXSIZE = int((1 << 31) - 1)
        else:
            # 64-bit
            MAXSIZE = int((1 << 63) - 1)
        del X

currversion = '1.1'
title_plug = 'Vavoo'
desc_plugin = ('..:: Vavoo by Lululla %s ::.. ' % currversion)
stripurl = 'aHR0cHM6Ly92YXZvby50by9jaGFubmVscw=='
searchurl = 'aHR0cHM6Ly90aXZ1c3RyZWFtLndlYnNpdGUvcGhwX2ZpbHRlci9rb2RpMTkva29kaTE5LnBocD9tb2RlPW1vdmllJnF1ZXJ5PQ=='
_session = None
enigma_path = '/etc/enigma2/'
_UNICODE_MAP = {k: unichr(v) for k, v in iteritems(html_entities.name2codepoint)}
_ESCAPE_RE = re.compile("[&<>\"']")
_UNESCAPE_RE = re.compile(r"&\s*(#?)(\w+?)\s*;")  # Whitespace handling added due to "hand-assed" parsers of html pages
_ESCAPE_DICT = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;"}


def ensure_str(s, encoding='utf-8', errors='strict'):
    """Coerce *s* to `str`.
    For Python 2:
      - `unicode` -> encoded to `str`
      - `str` -> `str`

    For Python 3:
      - `str` -> `str`
      - `bytes` -> decoded to `str`
    """
    # Optimization: Fast return for the common case.
    if type(s) is str:
        return s
    if PY2 and isinstance(s, text_type):
        return s.encode(encoding, errors)
    elif PY3 and isinstance(s, binary_type):
        return s.decode(encoding, errors)
    elif not isinstance(s, (text_type, binary_type)):
        raise TypeError("not expecting type '%s'" % type(s))
    return s


def html_escape(value):
    return _ESCAPE_RE.sub(lambda match: _ESCAPE_DICT[match.group(0)], ensure_str(value).strip())


def html_unescape(value):
    return _UNESCAPE_RE.sub(_convert_entity, ensure_str(value).strip())


def _convert_entity(m):
    if m.group(1) == "#":
        try:
            return unichr(int(m.group(2)[1:], 16)) if m.group(2)[:1].lower() == "x" else unichr(int(m.group(2)))
        except ValueError:
            return "&#%s;" % m.group(2)
    return _UNICODE_MAP.get(m.group(2), "&%s;" % m.group(2))


if sys.version_info >= (2, 7, 9):
    try:
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None


def getserviceinfo(sref):
    try:
        from ServiceReference import ServiceReference
        p = ServiceReference(sref)
        servicename = str(p.getServiceName())
        serviceurl = str(p.getPath())
        return servicename, serviceurl
    except:
        return None, None


if PY3:
    def getUrl(url):
        req = Request(url)
        req.add_header('User-Agent', RequestAgent())
        try:
            response = urlopen(req, timeout=20)
            link = response.read().decode(errors='ignore')
            response.close()
            # return link
        except:
            import ssl
            gcontext = ssl._create_unverified_context()
            response = urlopen(req, timeout=20, context=gcontext)
            link = response.read().decode(errors='ignore')
            response.close()
        return link
else:
    def getUrl(url):
        req = Request(url)
        req.add_header('User-Agent', RequestAgent())
        try:
            response = urlopen(req, timeout=20)
            link = response.read()
            response.close()
            # return link
        except:
            import ssl
            gcontext = ssl._create_unverified_context()
            response = urlopen(req, timeout=20, context=gcontext)
            link = response.read()
            response.close()
        return link


def b64decoder(s):
    '''Add missing padding to string and return the decoded base64 string.'''
    # import base64
    s = str(s).strip()
    try:
        outp = base64.b64decode(s)
        # print('outp1 ', outp)
        if PY3:
            outp = outp.decode('utf-8')
            # print('outp2 ', outp)
        return outp

    except TypeError:
        padding = len(s) % 4
        if padding == 1:
            print('Invalid base64 string: {}'.format(s))
            return ''
        elif padding == 2:
            s += b'=='
        elif padding == 3:
            s += b'='
        outp = base64.b64decode(s)
        # print('outp1 ', outp)
        if PY3:
            outp = outp.decode('utf-8')
            # print('outp2 ', outp)
        return outp


def returnIMDB(text_clear):
    TMDB = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('TMDB'))
    IMDb = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('IMDb'))
    if file_exists(TMDB):
        try:
            from Plugins.Extensions.TMBD.plugin import TMBD
            text = html_unescape(text_clear)
            _session.open(TMBD.tmdbScreen, text, 0)
        except Exception as e:
            print("[XCF] Tmdb: ", e)
        return True
    elif file_exists(IMDb):
        try:
            from Plugins.Extensions.IMDb.plugin import main as imdb
            text = html_unescape(text_clear)
            imdb(_session, text)
        except Exception as e:
            print("[XCF] imdb: ", e)
        return True
    else:
        text_clear = html_unescape(text_clear)
        _session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)
        return True
    return False


class m2list(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)
        self.l.setItemHeight(50)
        textfont = int(34)
        self.l.setFont(0, gFont('Regular', textfont))


Panel_list = ("Albania", "Arabia", "Balkans", "Bulgaria",
              "France", "Germany", "Italy", "Netherlands",
              "Poland", "Portugal", "Romania", "Russia",
              "Spain", "Turkey", "United Kingdom")


def show_(name, link):
    res = [(name, link)]
    cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
    pngx = os_path.dirname(resolveFilename(SCOPE_SKIN, str(cur_skin))) + "/mainmenu/vavoo_ico.png"
    if any(s in name for s in Panel_list):
        pngx = os_path.dirname(resolveFilename(SCOPE_SKIN, str(cur_skin))) + '/vavoo/%s.png' % str(name)
    if os.path.isfile(pngx):
        print('pngx =:', pngx)
    res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 5), size=(60, 40), png=loadPNG(pngx)))
    res.append(MultiContentEntryText(pos=(85, 0), size=(600, 50), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


class MainVavoox(Screen):
    def __init__(self, session):
        self.session = session
        global _session
        _session = session
        Screen.__init__(self, session)
        self.menulist = []
        self['menulist'] = m2list([])
        self['red'] = Label(_('Exit'))
        self['green'] = Label(_('Remove'))
        self['titel'] = Label('X VAVOO')
        self['name'] = Label('')
        self['text'] = Label('Vavoo Stream Live by Lululla')
        self.currentList = 'menulist'
        self.loading_ok = False
        self.count = 0
        self.loading = 0
        self.url = b64decoder(stripurl)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'DirectionActions',
                                     'MovieSelectionActions'], {'up': self.up,
                                                                'down': self.down,
                                                                'left': self.left,
                                                                'right': self.right,
                                                                'ok': self.ok,
                                                                'green': self.msgdeleteBouquets,
                                                                'cancel': self.close,
                                                                'info': self.info,
                                                                'red': self.close}, -1)
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.cat)
        except:
            self.timer.callback.append(self.cat)
        self.timer.start(500, True)

    def info(self):
        aboutbox = self.session.open(MessageBox, _('Vavoo Plugin v.%s\nby Lululla\nThanks:\n@KiddaC #oktus and staff Linuxsat-support.com') % currversion, MessageBox.TYPE_INFO)
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
            content = getUrl(self.url)
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
                        purge(enigma_path, fname)
                    elif 'bouquets.tv.bak' in fname:
                        purge(enigma_path, fname)
                os.rename(os.path.join(enigma_path, 'bouquets.tv'), os.path.join(enigma_path, 'bouquets.tv.bak'))
                tvfile = open(os.path.join(enigma_path, 'bouquets.tv'), 'w+')
                bakfile = open(os.path.join(enigma_path, 'bouquets.tv.bak'))
                for line in bakfile:
                    if '.vavoo_' not in line:
                        tvfile.write(line)
                bakfile.close()
                tvfile.close()
                self.session.open(MessageBox, _('Vavoo Favorites List have been removed'), MessageBox.TYPE_INFO, timeout=5)
                ReloadBouquets()
            except Exception as ex:
                print(str(ex))
                raise


class vavoo(Screen):
    def __init__(self, session, name, url):
        self.session = session
        global _session
        _session = session
        Screen.__init__(self, session)
        self.menulist = []
        self['menulist'] = m2list([])
        self['red'] = Label(_('Back'))
        self['green'] = Label(_('Export'))
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
                                     'EPGSelectActions',
                                     'DirectionActions',
                                     'MovieSelectionActions'], {'up': self.up,
                                                                'down': self.down,
                                                                'left': self.left,
                                                                'right': self.right,
                                                                'ok': self.ok,
                                                                'green': self.message2,
                                                                'cancel': self.close,
                                                                'info': self.info,
                                                                'red': self.close}, -1)
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.cat)
        except:
            self.timer.callback.append(self.cat)
        self.timer.start(500, True)

    def info(self):
        aboutbox = self.session.open(MessageBox, _('Vavoo Plugin v.%s\nby Lululla\nThanks:\n@KiddaC #oktus and staff Linuxsat-support.com') % currversion, MessageBox.TYPE_INFO)
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
        try:
            with open(xxxname, 'w') as outfile:
                outfile.write('#NAME %s\r\n' % self.name.capitalize())
                content = getUrl(self.url)
                if six.PY3:
                    content = six.ensure_str(content)
                names = self.name
                regexcat = '"country".*?"(.*?)".*?"id"(.*?)"name".*?"(.*?)"'
                match = re.compile(regexcat, re.DOTALL).findall(content)
                for country, ids, name in match:
                    if country != names:
                        continue
                    ids = ids.replace(':', '').replace(' ', '').replace(',', '')
                    url = 'http://vavoo.to/play/' + str(ids) + '/index.m3u8'
                    name = decodeHtml(name)
                    item = name + "###" + url + '\n'
                    items.append(item)
                items.sort()
                for item in items:
                    name = item.split('###')[0]
                    url = item.split('###')[1]
                    self.cat_list.append(show_(name, url))
                    # make m3u
                    nname = '#EXTINF:-1,' + str(name) + '\n'
                    outfile.write(nname)
                    outfile.write(str(url))
                outfile.close()
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

    def message2(self, answer=None):
        if answer is None:
            self.session.openWithCallback(self.message2, MessageBox, _('Do you want to Convert to favorite .tv ?\n\nAttention!! It may take some time depending\non the number of streams contained !!!'))
        elif answer:
            print('url: ', self.url)
            service = '4097'
            ch = 0
            ch = self.convert_bouquet(service)
            if ch > 0:
                _session.open(MessageBox, _('bouquets reloaded..\nWith %s channel' % str(ch)), MessageBox.TYPE_INFO, timeout=5)
            else:
                _session.open(MessageBox, _('Download Error'), MessageBox.TYPE_INFO, timeout=5)

    def convert_bouquet(self, service):
        from time import sleep
        dir_enigma2 = '/etc/enigma2/'
        files = '/tmp/' + self.name + '.m3u'
        type = 'tv'
        if "radio" in self.name.lower():
            type = "radio"
        name_file = self.name.replace('/', '_').replace(',', '')
        cleanName = re.sub(r'[\<\>\:\"\/\\\|\?\*]', '_', str(name_file))
        cleanName = re.sub(r' ', '_', cleanName)
        cleanName = re.sub(r'\d+:\d+:[\d.]+', '_', cleanName)
        name_file = re.sub(r'_+', '_', cleanName)
        bouquetname = 'userbouquet.vavoo_%s.%s' % (name_file.lower(), type.lower())
        if os.path.exists(str(files)):
            sleep(5)
            ch = 0
            try:
                if os.path.isfile(files) and os.stat(files).st_size > 0:
                    print('ChannelList is_tmp exist in playlist')
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
                                remove_line('/etc/enigma2/bouquets.tv', bouquetname)
                                with open('/etc/enigma2/bouquets.tv', 'a+') as outfile:
                                    outfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\r\n' % bouquetname)
                                    outfile.close()
                                    in_bouquets = 1
                        ReloadBouquets()
                return ch
            except Exception as e:
                print('error convert iptv ', e)


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
        self.name = decodeHtml(name)
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
            servicename, serviceurl = getserviceinfo(self.sref)
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


def decodeHtml(text):
    text = text.replace('&auml;', 'ä')
    text = text.replace('\u00e4', 'ä')
    text = text.replace('&#228;', 'ä')
    text = text.replace('&Auml;', 'Ä')
    text = text.replace('\u00c4', 'Ä')
    text = text.replace('&#196;', 'Ä')
    text = text.replace('&ouml;', 'ö')
    text = text.replace('\u00f6', 'ö')
    text = text.replace('&#246;', 'ö')
    text = text.replace('&ouml;', 'Ö')
    text = text.replace('&Ouml;', 'Ö')
    text = text.replace('\u00d6', 'Ö')
    text = text.replace('&#214;', 'Ö')
    text = text.replace('&uuml;', 'ü')
    text = text.replace('\u00fc', 'ü')
    text = text.replace('&#252;', 'ü')
    text = text.replace('&Uuml;', 'Ü')
    text = text.replace('\u00dc', 'Ü')
    text = text.replace('&#220;', 'Ü')
    text = text.replace('&szlig;', 'ß')
    text = text.replace('\u00df', 'ß')
    text = text.replace('&#223;', 'ß')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '\"')
    text = text.replace('&gt;', '>')
    text = text.replace('&apos;', "'")
    text = text.replace('&acute;', '\'')
    text = text.replace('&ndash;', '-')
    text = text.replace('&bdquo;', '"')
    text = text.replace('&rdquo;', '"')
    text = text.replace('&ldquo;', '"')
    text = text.replace('&lsquo;', '\'')
    text = text.replace('&rsquo;', '\'')
    text = text.replace('&#034;', '"')
    text = text.replace('&#34;', '"')
    text = text.replace('&#038;', '&')
    text = text.replace('&#039;', '\'')
    text = text.replace('&#39;', '\'')
    text = text.replace('&#160;', ' ')
    text = text.replace('\u00a0', ' ')
    text = text.replace('\u00b4', '\'')
    text = text.replace('\u003d', '=')
    text = text.replace('\u0026', '&')
    text = text.replace('&#174;', '')
    text = text.replace('&#225;', 'a')
    text = text.replace('&#233;', 'e')
    text = text.replace('&#243;', 'o')
    text = text.replace('&#8211;', '-')
    text = text.replace('&#8212;', '—')
    text = text.replace('&mdash;', '—')
    text = text.replace('\u2013', '–')
    text = text.replace('&#8216;', "'")
    text = text.replace('&#8217;', "'")
    text = text.replace('&#8220;', "'")
    text = text.replace('&#8221;', '"')
    text = text.replace('&#8222;', ', ')
    text = text.replace('\u014d', 'ō')
    text = text.replace('\u016b', 'ū')
    text = text.replace('\u201a', '\"')
    text = text.replace('\u2018', '\"')
    text = text.replace('\u201e', '\"')
    text = text.replace('\u201c', '\"')
    text = text.replace('\u201d', '\'')
    text = text.replace('\u2019s', '’')
    text = text.replace('\u00e0', 'à')
    text = text.replace('\u00e7', 'ç')
    text = text.replace('\u00e8', 'é')
    text = text.replace('\u00e9', 'é')
    text = text.replace('\u00c1', 'Á')
    text = text.replace('\u00c6', 'Æ')
    text = text.replace('\u00e1', 'á')
    text = text.replace('&#xC4;', 'Ä')
    text = text.replace('&#xD6;', 'Ö')
    text = text.replace('&#xDC;', 'Ü')
    text = text.replace('&#xE4;', 'ä')
    text = text.replace('&#xF6;', 'ö')
    text = text.replace('&#xFC;', 'ü')
    text = text.replace('&#xDF;', 'ß')
    text = text.replace('&#xE9;', 'é')
    text = text.replace('&#xB7;', '·')
    text = text.replace('&#x27;', "'")
    text = text.replace('&#x26;', '&')
    text = text.replace('&#xFB;', 'û')
    text = text.replace('&#xF8;', 'ø')
    text = text.replace('&#x21;', '!')
    text = text.replace('&#x3f;', '?')
    text = text.replace('&#8230;', '...')
    text = text.replace('\u2026', '...')
    text = text.replace('&hellip;', '...')
    text = text.replace('&#8234;', '')
    return text


ListAgent = [
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
          'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2919.83 Safari/537.36',
          'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.15 (KHTML, like Gecko) Chrome/24.0.1295.0 Safari/537.15',
          'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.14 (KHTML, like Gecko) Chrome/24.0.1292.0 Safari/537.14',
          'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
          'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
          'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1284.0 Safari/537.13',
          'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.8 (KHTML, like Gecko) Chrome/17.0.940.0 Safari/535.8',
          'Mozilla/6.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1',
          'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1',
          'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1',
          'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2',
          'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.16) Gecko/20120427 Firefox/15.0a1',
          'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20120427 Firefox/15.0a1',
          'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:15.0) Gecko/20120910144328 Firefox/15.0.2',
          'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1',
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:9.0a2) Gecko/20111101 Firefox/9.0a2',
          'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0a2) Gecko/20110613 Firefox/6.0a2',
          'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0a2) Gecko/20110612 Firefox/6.0a2',
          'Mozilla/5.0 (Windows NT 6.1; rv:6.0) Gecko/20110814 Firefox/6.0',
          'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0',
          'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
          'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
          'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)',
          'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/4.0; InfoPath.2; SV1; .NET CLR 2.0.50727; WOW64)',
          'Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)',
          'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
          'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0;  it-IT)',
          'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US)'
          'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; chromeframe/13.0.782.215)',
          'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; chromeframe/11.0.696.57)',
          'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0) chromeframe/10.0.648.205',
          'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/4.0; GTB7.4; InfoPath.1; SV1; .NET CLR 2.8.52393; WOW64; en-US)',
          'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; chromeframe/11.0.696.57)',
          'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/4.0; GTB7.4; InfoPath.3; SV1; .NET CLR 3.1.76908; WOW64; en-US)',
          'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; GTB7.4; InfoPath.2; SV1; .NET CLR 3.3.69573; WOW64; en-US)',
          'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)',
          'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; InfoPath.1; SV1; .NET CLR 3.8.36217; WOW64; en-US)',
          'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
          'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; it-IT)',
          'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
          'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16.2',
          'Opera/12.80 (Windows NT 5.1; U; en) Presto/2.10.289 Version/12.02',
          'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00',
          'Opera/9.80 (Windows NT 5.1; U; zh-sg) Presto/2.9.181 Version/12.00',
          'Opera/12.0(Windows NT 5.2;U;en)Presto/22.9.168 Version/12.00',
          'Opera/12.0(Windows NT 5.1;U;en)Presto/22.9.168 Version/12.00',
          'Mozilla/5.0 (Windows NT 5.1) Gecko/20100101 Firefox/14.0 Opera/12.0',
          'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25',
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10',
          'Mozilla/5.0 (iPad; CPU OS 5_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko ) Version/5.1 Mobile/9B176 Safari/7534.48.3',
          ]


def RequestAgent():
    from random import choice
    RandomAgent = choice(ListAgent)
    return RandomAgent


def remove_line(filename, what):
    if os.path.isfile(filename):
        file_read = open(filename).readlines()
        file_write = open(filename, 'w')
        for line in file_read:
            if what not in line:
                file_write.write(line)
        file_write.close()


def ReloadBouquets():
    print('\n----Reloading bouquets----\n')
    try:
        from enigma import eDVBDB
    except ImportError:
        eDVBDB = None
    if eDVBDB:
        db = eDVBDB.getInstance()
        if db:
            db.reloadServicelist()
            db.reloadBouquets()
            print("eDVBDB: bouquets reloaded...")
    else:
        os.system("wget -qO - http://127.0.0.1/web/servicelistreload?mode=2 > /dev/null 2>&1 &")
        os.system("wget -qO - http://127.0.0.1/web/servicelistreload?mode=4 > /dev/null 2>&1 &")
        print("wGET: bouquets reloaded...")


def purge(dir, pattern):
    for f in os.listdir(dir):
        file_path = os.path.join(dir, f)
        if os.path.isfile(file_path):
            if re.search(pattern, f):
                os.remove(file_path)
