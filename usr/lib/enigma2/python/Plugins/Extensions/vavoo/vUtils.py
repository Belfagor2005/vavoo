#!/usr/bin/python
# -*- coding: utf-8 -*-

from Tools.Directories import (SCOPE_PLUGINS, resolveFilename)
from enigma import getDesktop
from os.path import join, isfile
from os import listdir, path as os_path, popen, remove as os_remove, system
from random import choice
from re import split
from re import sub
from six import unichr, iteritems
from six.moves import html_entities
from time import time
from unicodedata import normalize
import base64
import json
import re
import requests
import ssl
import sys
import types
import six

PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('vavoo'))

screenwidth = getDesktop(0).size()
pythonVer = sys.version_info.major


try:
	from Components.AVSwitch import AVSwitch
except ImportError:
	from Components.AVSwitch import eAVControl as AVSwitch


class AspectManager:
	def __init__(self):
		self.init_aspect = self.get_current_aspect()
		print("[INFO] Initial aspect ratio:", self.init_aspect)

	def get_current_aspect(self):
		"""Restituisce l'aspect ratio attuale del dispositivo."""
		try:
			return int(AVSwitch().getAspectRatioSetting())
		except Exception as e:
			print("[ERROR] Failed to get aspect ratio:", str(e))
			return 0

	def restore_aspect(self):
		"""Ripristina l'aspect ratio originale all'uscita del plugin."""
		try:
			print("[INFO] Restoring aspect ratio to:", self.init_aspect)
			AVSwitch().setAspectRatio(self.init_aspect)
		except Exception as e:
			print("[ERROR] Failed to restore aspect ratio:", str(e))


aspect_manager = AspectManager()


if pythonVer == 3:
	from urllib.request import urlopen, Request
else:
	from urllib2 import urlopen, Request


if pythonVer == 3:
	try:
		sslContext = ssl._create_unverified_context()
	except:
		sslContext = None

class_types = (type,) if six.PY3 else (type, types.ClassType)
text_type = six.text_type  # unicode in Py2, str in Py3
binary_type = six.binary_type  # str in Py2, bytes in Py3
MAXSIZE = sys.maxsize  # Compatibile con entrambe le versioni

_UNICODE_MAP = {k: unichr(v) for k, v in iteritems(html_entities.name2codepoint)}
_ESCAPE_RE = re.compile("[&<>\"']")
_UNESCAPE_RE = re.compile(r"&\s*(#?)(\w+?)\s*;")
_ESCAPE_DICT = {
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	'"': "&quot;",
	"'": "&apos;",
}


def ensure_str(s, encoding="utf-8", errors="strict"):
	if isinstance(s, str):
		return s
	if isinstance(s, binary_type):
		return s.decode(encoding, errors)
	raise TypeError("not expecting type '%s'" % type(s))


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


def b64decoder(s):
	s = str(s).strip()
	try:
		output = base64.b64decode(s)
		if pythonVer == 3:
			output = output.decode('utf-8')
		return output

	except Exception:
		padding = len(s) % 4
		if padding == 1:
			print('Invalid base64 string: {}'.format(s))
			return ""
		elif padding == 2:
			s += b'=='
		elif padding == 3:
			s += b'='
		else:
			return ""

		output = base64.b64decode(s)
		if pythonVer == 3:
			output = output.decode('utf-8')

		return output


def getUrl(url):
	req = Request(url)
	req.add_header('User-Agent', RequestAgent())

	try:
		response = urlopen(req, timeout=20)
		if pythonVer == 3:
			link = response.read().decode(errors='ignore')
		else:
			link = response.read()
		response.close()
		return link

	except Exception as e:
		print("Error in first attempt:", e)
		try:
			gcontext = ssl._create_unverified_context()
			response = urlopen(req, timeout=20, context=gcontext)
			if pythonVer == 3:
				link = response.read().decode(errors='ignore')
			else:
				link = response.read()
			response.close()
			return link

		except Exception as e:
			print("Error in second attempt:", e)
			return ""


def get_external_ip():
	try:
		return popen('curl -s ifconfig.me').readline()
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
		if not isinstance(data, dict):
			data = {"value": data}

		if pythonVer < 3:
			import io
			with io.open(file_path, 'w', encoding='utf-8') as cache_file:
				json.dump(convert_to_unicode(data), cache_file, indent=4, ensure_ascii=False)
		else:
			with open(file_path, 'w', encoding='utf-8') as cache_file:
				json.dump(convert_to_unicode(data), cache_file, indent=4, ensure_ascii=False)
	except Exception as e:
		print("Error saving cache:", e)


def get_cache(key):
	file_path = os_path.join(PLUGIN_PATH, key + '.json')
	if not (os_path.exists(file_path) and os_path.getsize(file_path) > 0):
		return None

	try:
		data = _read_json_file(file_path)

		if isinstance(data, str):
			data = {"value": data}
			_write_json_file(file_path, data)

		if not isinstance(data, dict):
			print("Unexpected data format in {}: Expected a dict, got {}".format(file_path, type(data)))
			os_remove(file_path)
			return None

		if _is_cache_valid(data):
			return data.get('value')

	except ValueError as e:
		print("Error decoding JSON from", file_path, ":", e)
	except Exception as e:
		print("Unexpected error reading cache file {}:".format(file_path), e)
		os_remove(file_path)

	return None


def _read_json_file(file_path):
	if pythonVer < 3:
		import io
		with io.open(file_path, 'r', encoding='utf-8') as f:
			return json.load(f)
	else:
		with open(file_path, 'r', encoding='utf-8') as f:
			return json.load(f)


def _write_json_file(file_path, data):
	with open(file_path, 'w', encoding='utf-8') as f:
		json.dump(data, f, indent=4, ensure_ascii=False)


def _is_cache_valid(data):
	return (
		data.get('sigValidUntil', 0) > int(time())
		and data.get('ip', "") == get_external_ip()
	)


def getAuthSignature():
	signfile = get_cache('signfile')
	if signfile:
		return signfile

	veclist = get_cache("veclist")
	if not veclist:
		veclist = requests.get("https://raw.githubusercontent.com/Belfagor2005/vavoo/refs/heads/main/data.json").json()
		set_cache("veclist", veclist, timeout=3600)

	sig = None
	i = 0
	while not sig and i < 50:
		i += 1
		vec = {"vec": choice(veclist)}
		req = requests.post('https://www.vavoo.tv/api/box/ping2', data=vec).json()
		sig = req.get('signed') or req.get('data', {}).get('signed') or req.get('response', {}).get('signed')

	if sig:
		set_cache('signfile', convert_to_unicode(sig), timeout=3600)
	return sig


def convert_to_unicode(data):
	"""
	In Python 3 le stringhe sono già Unicode, quindi:
	- Se data è bytes, decodificalo.
	- Se è str, restituiscilo così com'è.
	"""
	if isinstance(data, bytes):
		return data.decode('utf-8')
	elif isinstance(data, str):
		return data  # Già Unicode in Python 3
	elif isinstance(data, dict):
		return {convert_to_unicode(k): convert_to_unicode(v) for k, v in data.items()}
	elif isinstance(data, list):
		return [convert_to_unicode(item) for item in data]
	return data


def rimuovi_parentesi(testo):
	return sub(r'\s*\([^)]*\)\s*', ' ', testo).strip()


def purge(directory, pattern):
	for f in listdir(directory):
		file_path = join(directory, f)
		if isfile(file_path):
			if re.search(pattern, f):
				os_remove(file_path)


def MemClean():
	try:
		system('sync')
		system('echo 1 > /proc/sys/vm/drop_caches')
		system('echo 2 > /proc/sys/vm/drop_caches')
		system('echo 3 > /proc/sys/vm/drop_caches')
	except:
		pass


def ReloadBouquets():
	from enigma import eDVBDB
	eDVBDB.getInstance().reloadServicelist()
	eDVBDB.getInstance().reloadBouquets()


def sanitizeFilename(filename):
	filename = _remove_unsafe_chars(filename)
	filename = _handle_reserved_and_empty(filename)
	filename = _truncate_if_too_long(filename)
	return filename


def _remove_unsafe_chars(filename):
	blacklist = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\0", "(", ")", " "]
	filename = "".join(c for c in filename if c not in blacklist)
	filename = "".join(c for c in filename if 31 < ord(c))  # Remove control chars
	filename = normalize("NFKD", filename)
	filename = filename.rstrip(". ")  # Windows does not allow trailing dot or space
	return filename.strip()


def _handle_reserved_and_empty(filename):
	reserved = [
		"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
		"COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
		"LPT6", "LPT7", "LPT8", "LPT9"
	]
	if all(c == "." for c in filename) or filename in reserved:
		return "__" + filename
	if not filename:
		return "__"
	return filename


def _truncate_if_too_long(filename):
	if len(filename) <= 255:
		return filename

	parts = split(r"/|\\", filename)[-1].split(".")
	if len(parts) > 1:
		ext = "." + parts.pop()
		filename = filename[:-len(ext)]
	else:
		ext = ""
	if not filename:
		filename = "__"
	if len(ext) > 254:
		ext = ext[:254]
	maxl = 255 - len(ext)
	filename = filename[:maxl] + ext
	filename = filename.rstrip(". ")
	return filename or "__"


def decodeHtml(text):
	if pythonVer == 3:
		import html
		text = html.unescape(text)
	else:
		from six.moves import html_parser
		h = html_parser.HTMLParser()
		text = h.unescape(text.decode('utf8')).encode('utf8')

	html_replacements = {
		'&amp;': '&', '&apos;': "'", '&lt;': '<', '&gt;': '>', '&ndash;': '-',
		'&quot;': '"', '&ntilde;': '~', '&rsquo;': "'", '&nbsp;': ' ',
		'&equals;': '=', '&quest;': '?', '&comma;': ',', '&period;': '.',
		'&colon;': ':', '&lpar;': '(', '&rpar;': ')', '&excl;': '!',
		'&dollar;': '$', '&num;': '#', '&ast;': '*', '&lowbar;': '_',
		'&lsqb;': '[', '&rsqb;': ']', '&half;': '1/2', '&DiacriticalTilde;': '~',
		'&OpenCurlyDoubleQuote;': '"', '&CloseCurlyDoubleQuote;': '"'
	}

	for key, val in html_replacements.items():
		text = text.replace(key, val)
	return text.strip()


def remove_line(filename, what):
	if os_path.isfile(filename):
		file_read = open(filename).readlines()
		file_write = open(filename, 'w')
		for line in file_read:
			if what not in line:
				file_write.write(line)
		file_write.close()


# this def returns the current playing service name and stream_url from give sref
def getserviceinfo(sref):
	try:
		from ServiceReference import ServiceReference
		p = ServiceReference(sref)
		servicename = str(p.getServiceName())
		serviceurl = str(p.getPath())
		return servicename, serviceurl
	except:
		return None, None


std_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en-us,en;q=0.5'
}

ListAgent = [
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
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
	'Mozilla/5.0 (iPad; CPU OS 5_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko ) Version/5.1 Mobile/9B176 Safari/7534.48.3'
]


def RequestAgent():
	from random import choice
	RandomAgent = choice(ListAgent)
	return RandomAgent
