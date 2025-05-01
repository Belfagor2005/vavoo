#!/usr/bin/env python3
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

# Standard library imports
# Enigma2 components
try:
	from Components.AVSwitch import AVSwitch
except ImportError:
	from Components.AVSwitch import eAVControl as AVSwitch

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
from datetime import datetime
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
from os import listdir, makedirs, unlink, stat, remove, system, path as os_path
from os.path import exists as file_exists
from re import sub, compile, DOTALL
from requests.adapters import HTTPAdapter, Retry
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

# from six import text_type
import codecs
import json
import os
import requests
import ssl
import sys
import time

# Local application/library-specific imports
from . import _, country_codes
from . import vUtils
from .Console import Console

global HALIGN
_session = None
tmlast = None
now = None
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


if sys.version_info >= (2, 7, 9):
	try:
		ssl_context = ssl._create_unverified_context()
	except:
		ssl_context = None


try:
	from urllib import unquote
except ImportError:
	from urllib.parse import unquote


# set plugin
currversion = '1.36'
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


# log
def trace_error():
	import traceback
	try:
		traceback.print_exc(file=sys.stdout)
		with open("/tmp/vavoo.log", "a", encoding='utf-8') as log_file:
			traceback.print_exc(file=log_file)
	except Exception as e:
		print("Failed to log the error:", e, file=sys.stderr)


# https://www.oha.to/oha-tv/
myser = [("https://vavoo.to", "vavoo"), ("https://oha.tooha-tv", "oha"), ("https://kool.to", "kool"), ("https://huhu.to", "huhu")]
mydns = [("None", "Default"), ("google", "Google"), ("coudfire", "Coudfire"), ("quad9", "Quad9")]
modemovie = [("4097", "4097")]
if file_exists("/usr/bin/gstplayer"):
	modemovie.append(("5001", "5001"))
if file_exists("/usr/bin/exteplayer3"):
	modemovie.append(("5002", "5002"))
if file_exists('/var/lib/dpkg/info'):
	modemovie.append(("8193", "8193"))


# back
global BackPath, FONTSTYPE, FNTPath
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
		for back_name in listdir(BackPath):
			back_name_path = os_path.join(BackPath, back_name)
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
FNT_Path = os_path.join(PLUGIN_PATH, "fonts")
fonts = []
try:
	if file_exists(FNT_Path):
		for font_name in listdir(FNT_Path):
			font_name_path = os_path.join(FNT_Path, font_name)
			if font_name.endswith(".ttf") or font_name.endswith(".otf"):
				font_name = font_name[:-4]
				fonts.append((font_name, font_name))
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
cfg.timerupdate = ConfigSelectionNumber(default=10, min=1, max=60, stepwidth=1)
cfg.timetype = ConfigSelection(default="interval", choices=[("interval", _("interval")), ("fixed time", _("fixed time"))])
cfg.updateinterval = ConfigSelectionNumber(default=10, min=5, max=3600, stepwidth=5)
cfg.fixedtime = ConfigClock(default=46800)
cfg.last_update = ConfigText(default="Never")
cfg.stmain = ConfigYesNo(default=True)
cfg.ipv6 = ConfigEnableDisable(default=False)
cfg.dns = ConfigSelection(default="Default", choices=mydns)
cfg.fonts = ConfigSelection(default='vav', choices=fonts)
cfg.back = ConfigSelection(default='oktus', choices=BakP)
FONTSTYPE = FNT_Path + '/' + cfg.fonts.value + '.ttf'
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
		self.list.append(getConfigListEntry(_("Refresh Player"), cfg.timerupdate, _("Configure Update Timer for player refresh")))
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
			if not os_path.exists(downloadfree):
				makedirs(downloadfree)
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
				unlink('/etc/rc3.d/S99ipv6dis.sh')
				cfg.ipv6.setValue(False)
			else:
				system("echo '#!/bin/bash")
				system("echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6' > /etc/init.d/ipv6dis.sh")
				system("chmod 755 /etc/init.d/ipv6dis.sh")
				system("ln -s /etc/init.d/ipv6dis.sh /etc/rc3.d/S99ipv6dis.sh")
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
			FONTSTYPE = os_path.join(str(FNT_Path), str(FONTSE))
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
					from os import access, X_OK, chmod
					if not access(self.cmd1, X_OK):
						chmod(self.cmd1, 493)
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
		global _session
		_session = session

		Screen.__init__(self, session)

		self._load_skin()
		self._initialize_labels()
		self._initialize_actions()

		self.url = vUtils.b64decoder(stripurl)
		self.currentList = 'menulist'
		self.loading_ok = False
		self.count = 0
		self.loading = 0

		self.cat()

	def _load_skin(self):
		"""Load the skin file."""
		skin = os_path.join(skin_path, 'defaultListScreen.xml')
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

		self._set_alignment_text()

	def _set_alignment_text(self):
		"""Set text for blue label based on horizontal alignment."""
		if HALIGN == RT_HALIGN_RIGHT:
			self['blue'].setText(_('Halign Left'))
		else:
			self['blue'].setText(_('Halign Right'))

	def _initialize_actions(self):
		"""Initialize the actions for buttons."""
		actions = {
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
		}
		actions_list = [
			'ButtonSetupActions', 'MenuActions', 'OkCancelActions', 'DirectionActions',
			'ShortcutActions', 'HotkeyActions', 'InfobarEPGActions', 'ChannelSelectBaseActions'
		]
		self['actions'] = ActionMap(actions_list, actions, -1)

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
			self.session.openWithCallback(
				self.install_update,
				MessageBox,
				_("New version %s is available.\n\nChangelog: %s \n\nDo you want to install it now?") % (
					new_version, new_changelog
				),
				MessageBox.TYPE_YESNO
			)
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
		aboutbox = self.session.open(
			MessageBox,
			_(
				"%s\n\n\nThanks:\n@KiddaC\n@oktus\nQu4k3\nAll staff Linuxsat-support.com\n"
				"Corvoboys - Forum\n\nThis plugin is free,\nno stream direct on server\n"
				"but only free channel found on the net"
			) % desc_plugin,
			MessageBox.TYPE_INFO
		)
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
		self.items_tmp = []

		try:
			content = self._get_content()
			data = self._parse_json(content)
			if data is None:
				return

			items = self._build_country_items(data)
			self._build_cat_list(items)

			if not self.cat_list:
				return

			self._update_ui()
		except Exception as error:
			print("error as:", error)
			trace_error()
			self["name"].setText("Error")

		self["version"].setText("V." + currversion)

	def _get_content(self):
		content = vUtils.getUrl(self.url)
		if PY3:
			content = vUtils.ensure_str(content)
		return content

	def _parse_json(self, content):
		try:
			return json.loads(content)
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

	def _update_ui(self):
		self["menulist"].l.setList(self.cat_list)
		self["menulist"].moveToIndex(0)
		txtsream = self["menulist"].getCurrent()[0][0]
		self["name"].setText(str(txtsream))

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
			from enigma import eDVBDB
			try:
				for fname in listdir(enigma_path):
					if 'userbouquet.vavoo' in fname:
						bouquet_path = os_path.join("/etc/enigma2", fname)
						print("[vavoo plugin] Removing bouquet:", bouquet_path)
						eDVBDB.getInstance().removeBouquet(bouquet_path)
						# If needed, also remove the physical bouquet
						# vUtils.purge(enigma_path, fname)

				if os.path.exists(os_path.join(PLUGIN_PATH, 'Favorite.txt')):
					favorite_path = os_path.join(PLUGIN_PATH, 'Favorite.txt')
					remove(favorite_path)

				self.session.open(MessageBox, _('Vavoo Favorites List has been removed'), MessageBox.TYPE_INFO, timeout=5)

			except Exception as error:
				print(error)
				trace_error()


class vavoo(Screen):
	def __init__(self, session, name, url):
		self.session = session
		global _session
		_session = session

		Screen.__init__(self, session)

		self._load_skin()
		self._initialize_labels()
		self._initialize_actions()
		self.currentList = 'menulist'
		self.name = name
		self.url = url

		self._initialize_timer()

	def _load_skin(self):
		"""Load the skin file."""
		skin = os_path.join(skin_path, 'defaultListScreen.xml')
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

		self._set_alignment_text()

	def _set_alignment_text(self):
		"""Set text for blue label based on horizontal alignment."""
		if HALIGN == RT_HALIGN_RIGHT:
			self['blue'].setText(_('Halign Left'))
		else:
			self['blue'].setText(_('Halign Right'))

	def _initialize_actions(self):
		"""Initialize the actions for buttons."""
		self["actions"] = ActionMap(
			[
				"ButtonSetupActions",
				"MenuActions",
				"OkCancelActions",
				"ShortcutActions",
				"HotkeyActions",
				"DirectionActions",
				"InfobarEPGActions",
				"ChannelSelectBaseActions"
			],
			{
				"prevBouquet": self.chDown,
				"nextBouquet": self.chUp,
				"ok": self.ok,
				"green": self.message1,
				"yellow": self.search_vavoo,
				"blue": self.arabic,
				"cancel": self.backhome,
				"menu": self.goConfig,
				"info": self.info,
				"red": self.backhome
			},
			-1
		)

	def _initialize_timer(self):
		"""Initialize the timer."""
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
		# search_ok = False
		# Retrieve and parse data
		try:
			content = vUtils.getUrl(self.url)
			if PY3:
				content = vUtils.ensure_str(content)
			data = json.loads(content)
		except ValueError:
			print('Error parsing JSON data')
			self['name'].setText('Error parsing data')
			return

		# Process the data
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
					name = vUtils.rimuovi_parentesi(name)

					item = name + "###" + url + '\n'
					items.append(item)

				# Sort items and use them for search
				items.sort()
				self.itemlist = items  # Use for search

				# Create M3U file
				self.create_m3u_file(xxxname, items)

				if len(self.cat_list) < 1:
					return
				else:
					self.update_menu()

		except Exception as error:
			print('Error:', error)
			trace_error()
			self['name'].setText('Error')

		self['version'].setText('V.' + currversion)

	def create_m3u_file(self, filename, items):
		"""Creates an M3U file with the provided items."""
		with open(filename, 'w') as outfile:
			for item in items:
				name1, url = item.split('###')
				url = url.replace('%0a', '').replace('%0A', '').strip("\r\n")
				name = unquote(name1).strip("\r\n")
				self.cat_list.append(show_list(name, url))

				# Write M3U file content
				outfile.write('#NAME %s\r\n' % self.name.capitalize())
				outfile.write('#EXTINF:-1,' + str(name) + '\n')
				outfile.write('#EXTVLCOPT:http-user-agent=VAVOO/2.6' + '\n')
				outfile.write('#EXTVLCOPT:http-referrer=https://vavoo.to/' + '\n')
				outfile.write('#KODIPROP:http-user-agent=VAVOO/2.6' + '\n')
				outfile.write('#KODIPROP:http-referrer=https://vavoo.to/' + '\n')
				outfile.write('#EXTHTTP:{"User-Agent":"VAVOO/1.0","Referer":"https://vavoo.to/"}' + '\n')
				outfile.write(str(url) + '\n')

	def update_menu(self):
		"""Update the menu list."""
		self['menulist'].l.setList(self.cat_list)
		self['menulist'].moveToIndex(0)
		txtstream = self['menulist'].getCurrent()[0][0]
		self['name'].setText(str(txtstream))

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
		self.url = url
		filenameout = enigma_path + '/userbouquet.vavoo_%s.tv' % name.lower()
		if file_exists(filenameout):
			self.message3(name, self.url, False)
		else:
			self.message2(name, self.url, False)

	def message1(self, answer=None):
		if answer is None:
			self.session.openWithCallback(
				self.message1,
				MessageBox,
				_(
					'Do you want to Convert to favorite .tv?\n\n'
					'Attention!! It may take some time\n'
					'depending on the number of streams contained !!!'
				)
			)
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
		sig = vUtils.getAuthSignature()
		app = str(sig)
		if app:
			filename = PLUGIN_PATH + '/list/userbouquet.vavoo_%s.tv' % name.lower()
			filenameout = enigma_path + '/userbouquet.vavoo_%s.tv' % name.lower()
			key = None
			ch = 0
			with open(filename, "rt") as fin:
				data = fin.read()
				regexcat = '#SERVICE.*?vavoo_auth=(.+?)#User'
				match = compile(regexcat, DOTALL).findall(data)
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
				for item in self.itemlist:
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
		self["ShowHideActions"] = ActionMap(
			["InfobarShowHideActions"],
			{
				"toggleShow": self.OkPressed,
				"hide": self.hide
			},
			0
		)
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
		Screen.__init__(self, session)
		self.session = session
		_session = session
		self.skinName = 'MoviePlayer'
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
		for x in InfoBarBase, \
				InfoBarMenu, \
				InfoBarSeek, \
				InfoBarAudioSelection, \
				InfoBarSubtitleSupport, \
				InfoBarNotifications, \
				TvInfoBarShowHide:
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
				'tv': self.cicleStreamType,
				'stop': self.leavePlayer,
				'cancel': self.cancel,
				'channelDown': self.previousitem,
				'channelUp': self.nextitem,
				'down': self.previousitem,
				'up': self.nextitem,
				'back': self.cancel
			},
			-1
		)
		self.onFirstExecBegin.append(self.startStream)
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
			sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
			sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
			message = (
				"stitle: " + str(sTitle) + "\n"
				"sServiceref: " + str(sServiceref) + "\n"
				"sTagCodec: " + str(sTagCodec) + "\n"
				"sTagVideoCodec: " + str(sTagVideoCodec) + "\n"
				"sTagAudioCodec: " + str(sTagAudioCodec)
			)
			self.mbox = self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
		except:
			pass
		return

	def startStream(self):
		# Controlla se lo stream è già in corso
		if self.is_streaming:
			print("Stream is already running, skipping startStream.")
			return
		self.is_streaming = True  # Imposta la flag di stato
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
			self.refreshTimer_conn = self.refreshTimer.timeout.connect(self.refreshStream)
		except:
			self.refreshTimer.callback.append(self.refreshStream)
		self.refreshTimer.start(update_refresh * 60 * 1000)

	def refreshStream(self):
		if self.is_streaming:
			print("Stream already in progress, skipping refreshStream.")
			return

		self.is_streaming = True

		# Get updated token
		sig = vUtils.getAuthSignature()
		app = "?n=1&b=5&vavoo_auth=" + str(sig) + "#User-Agent=VAVOO/2.6"
		url = self.url
		if not url.startswith("http"):
			url = "http://" + url
		full_url = url + app
		ref = "{0}:0:0:0:0:0:0:0:0:0:{1}:{2}".format(
			self.servicetype,
			full_url.replace(":", "%3a"),
			self.name.replace(":", "%3a")
		)
		print("finalreference:   ", ref)
		sref = eServiceReference(ref)
		sref.setName(self.name)
		self.sref = sref
		self.session.nav.playService(self.sref)

	def cicleStreamType(self):
		self.servicetype = "4097"
		if not self.url.startswith("http"):
			self.url = "http://" + self.url
		if str(os_path.splitext(self.url)[-1]) == ".m3u8":
			if self.servicetype == "1":
				self.servicetype = "4097"
		self.refreshStream()

	def openTest(self, servicetype, url):
		sig = vUtils.getAuthSignature()
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

	def showVideoInfo(self):
		if self.shown:
			self.hideInfobar()
		if self.infoCallback is not None:
			self.infoCallback()
		return

	def showAfterSeek(self):
		if isinstance(self, TvInfoBarShowHide):
			self.doShow()

	def stopStream(self):
		if self.is_streaming:
			self.is_streaming = False
			print("Stopping stream and resetting state.")
			self.session.nav.stopService()
			self.session.nav.playService(self.srefInit)
			print("Stream stopped.")

	def cancel(self):
		if hasattr(self, "refreshTimer") and self.refreshTimer:
			self.refreshTimer.stop()
			self.refreshTimer = None

		self.is_streaming = False  # Ripristina la flag quando lo stream è terminato

		if os_path.isfile("/tmp/hls.avi"):
			remove("/tmp/hls.avi")
		self.session.nav.stopService()
		self.session.nav.playService(self.srefInit)

		aspect_manager.restore_aspect()  # Restore aspect on exit
		self.close()

	def leavePlayer(self):
		self.stopStream()
		self.cancel()


def convert_bouquet(service, name, url):
	sig = vUtils.getAuthSignature()
	app = "?n=1&b=5&vavoo_auth=%s#User-Agent=VAVOO/2.6" % str(sig)
	files = "/tmp/%s.m3u" % name
	bouquet_type = "radio" if "radio" in name.lower() else "tv"
	name_file, bouquet_name, path1, path2 = _prepare_bouquet_filenames(name, bouquet_type)

	with open(PLUGIN_PATH + "/Favorite.txt", "w") as r:
		r.write(str(name_file) + "###" + str(url))

	print("Converting Bouquet %s" % name_file)
	ch = 0

	if file_exists(files) and stat(files).st_size > 0:
		try:
			tplst, ch = _parse_m3u_file(files, name_file, bouquet_type, service, app)
			_write_bouquet_files(path1, tplst)
			_ensure_bouquet_listed(path2, bouquet_name, bouquet_type)
			vUtils.ReloadBouquets()
		except Exception as error:
			print("error as:", error)
	return ch


def _prepare_bouquet_filenames(name, bouquet_type):
	name_file = sub(r'[<>:"/\\|?*, ]', '_', str(name))
	name_file = sub(r'\d+:\d+:[\d.]+', '_', name_file)
	name_file = sub(r'_+', '_', name_file)
	bouquet_name = "userbouquet.vavoo_%s.%s" % (name_file.lower(), bouquet_type.lower())
	path1 = "/etc/enigma2/" + bouquet_name
	path2 = "/etc/enigma2/bouquets." + bouquet_type.lower()
	return name_file, bouquet_name, path1, path2


def _parse_m3u_file(filepath, name_file, bouquet_type, service, app):
	tplst = [
		"#NAME %s (%s)" % (name_file.capitalize(), bouquet_type.upper()),
		"#SERVICE 1:64:0:0:0:0:0:0:0:0::%s CHANNELS" % name_file,
		"#DESCRIPTION --- %s ---" % name_file
	]
	ch = 0
	namel, svz, dct = '', '', ''
	with open(filepath, "r") as f:
		for line in f:
			line = str(line).strip()
			if line.startswith("#EXTINF"):
				namel = line.split(",")[-1].strip()
				dct = "#DESCRIPTION %s" % namel
			elif line.startswith("http"):
				full_url = line.strip() + app
				tag = "2" if bouquet_type.upper() == "RADIO" else "1"
				svca = "#SERVICE %s:0:%s:0:0:0:0:0:0:0:%s" % (service, tag, full_url.replace(":", "%3a"))
				svz = svca + ":" + namel
				tplst.append(svz.strip())
				tplst.append(dct.strip())
				ch += 1
	return tplst, ch


def _write_bouquet_files(path1, tplst):
	try:
		with open(path1, "r") as f:
			f_content = f.read()
	except FileNotFoundError:
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
	except FileNotFoundError:
		pass
	if not in_bouquets:
		with open(path2, "a+") as f:
			f.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\n' % bouquet_name)


auto_start_timer = None


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
	if file_exists(os_path.join(BackPath, str(bakk))):
		baknew = os_path.join(BackPath, str(bakk))
		cmd = 'cp -f ' + str(baknew) + ' ' + BackPath + '/default.png'
		system(cmd)
		system('sync')


def add_skin_font():
	print('**********addFont')
	from enigma import addFont
	# global FONTSTYPE
	addFont(FNT_Path + '/Lcdx.ttf', 'Lcdx', 100, 1)
	addFont(str(FONTSTYPE), 'cvfont', 100, 1)
	addFont(os_path.join(str(FNT_Path), 'vav.ttf'), 'Vav', 100, 1)  # lcd


def cfgmain(menuid, **kwargs):
	return [(_('Vavoo Stream Live'), main, 'Vavoo', 55)] if menuid == "mainmenu" else []


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
		where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART],
		fnc=autostart,
		wakeupfnc=get_next_wakeup
	)

	result = [plugin_menu_descriptor, autostart_descriptor]

	if cfg.stmain.value:
		result.append(main_descriptor)

	return result
