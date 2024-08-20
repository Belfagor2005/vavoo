#!/usr/bin/python
# -*- coding: utf-8 -*-


from enigma import getDesktop
from six import unichr, iteritems  # ensure_str
from six.moves import html_entities
import base64
# import functools
# import itertools
# import operator
import os
import re
import sys
import types


screenwidth = getDesktop(0).size()
pythonVer = sys.version_info.major


if pythonVer == 3:
    from urllib.request import urlopen, Request
else:
    from urllib2 import urlopen, Request


if pythonVer == 3:
    try:
        import ssl
        sslContext = ssl._create_unverified_context()
    except:
        sslContext = None


if pythonVer:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes

    MAXSIZE = sys.maxsize
else:
    string_types = basestring,
    integer_types = (int, long)
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
    if pythonVer == 3 and isinstance(s, text_type):
        return s.encode(encoding, errors)
    elif pythonVer and isinstance(s, binary_type):
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
        print(e)
        try:
            import ssl
            gcontext = ssl._create_unverified_context()
            response = urlopen(req, timeout=20, context=gcontext)
            if pythonVer == 3:
                link = response.read().decode(errors='ignore')
            else:
                link = response.read()
            response.close()
            return link

        except Exception as e:
            print(e)
            return ""


def purge(dir, pattern):
    for f in os.listdir(dir):
        file_path = os.path.join(dir, f)
        if os.path.isfile(file_path):
            if re.search(pattern, f):
                os.remove(file_path)


def MemClean():
    try:
        os.system('sync')
        os.system('echo 1 > /proc/sys/vm/drop_caches')
        os.system('echo 2 > /proc/sys/vm/drop_caches')
        os.system('echo 3 > /proc/sys/vm/drop_caches')
    except:
        pass


def ReloadBouquets():
    from enigma import eDVBDB
    eDVBDB.getInstance().reloadServicelist()
    eDVBDB.getInstance().reloadBouquets()


def decodeHtml(text):
    charlist = []
    charlist.append(('&#034;', '"'))
    charlist.append(('&#038;', '&'))
    charlist.append(('&#039;', "'"))
    charlist.append(('&#060;', ' '))
    charlist.append(('&#062;', ' '))
    charlist.append(('&#160;', ' '))
    charlist.append(('&#174;', ''))
    charlist.append(('&#192;', '\xc3\x80'))
    charlist.append(('&#193;', '\xc3\x81'))
    charlist.append(('&#194;', '\xc3\x82'))
    charlist.append(('&#196;', '\xc3\x84'))
    charlist.append(('&#204;', '\xc3\x8c'))
    charlist.append(('&#205;', '\xc3\x8d'))
    charlist.append(('&#206;', '\xc3\x8e'))
    charlist.append(('&#207;', '\xc3\x8f'))
    charlist.append(('&#210;', '\xc3\x92'))
    charlist.append(('&#211;', '\xc3\x93'))
    charlist.append(('&#212;', '\xc3\x94'))
    charlist.append(('&#214;', '\xc3\x96'))
    charlist.append(('&#217;', '\xc3\x99'))
    charlist.append(('&#218;', '\xc3\x9a'))
    charlist.append(('&#219;', '\xc3\x9b'))
    charlist.append(('&#220;', '\xc3\x9c'))
    charlist.append(('&#223;', '\xc3\x9f'))
    charlist.append(('&#224;', '\xc3\xa0'))
    charlist.append(('&#225;', '\xc3\xa1'))
    charlist.append(('&#226;', '\xc3\xa2'))
    charlist.append(('&#228;', '\xc3\xa4'))
    charlist.append(('&#232;', '\xc3\xa8'))
    charlist.append(('&#233;', '\xc3\xa9'))
    charlist.append(('&#234;', '\xc3\xaa'))
    charlist.append(('&#235;', '\xc3\xab'))
    charlist.append(('&#236;', '\xc3\xac'))
    charlist.append(('&#237;', '\xc3\xad'))
    charlist.append(('&#238;', '\xc3\xae'))
    charlist.append(('&#239;', '\xc3\xaf'))
    charlist.append(('&#242;', '\xc3\xb2'))
    charlist.append(('&#243;', '\xc3\xb3'))
    charlist.append(('&#244;', '\xc3\xb4'))
    charlist.append(('&#246;', '\xc3\xb6'))
    charlist.append(('&#249;', '\xc3\xb9'))
    charlist.append(('&#250;', '\xc3\xba'))
    charlist.append(('&#251;', '\xc3\xbb'))
    charlist.append(('&#252;', '\xc3\xbc'))
    charlist.append(('&#8203;', ''))
    charlist.append(('&#8211;', '-'))
    charlist.append(('&#8211;', '-'))
    charlist.append(('&#8212;', ''))
    charlist.append(('&#8212;', '—'))
    charlist.append(('&#8216;', "'"))
    charlist.append(('&#8216;', "'"))
    charlist.append(('&#8217;', "'"))
    charlist.append(('&#8217;', "'"))
    charlist.append(('&#8220;', "'"))
    charlist.append(('&#8220;', ''))
    charlist.append(('&#8221;', '"'))
    charlist.append(('&#8222;', ''))
    charlist.append(('&#8222;', ', '))
    charlist.append(('&#8230;', '...'))
    charlist.append(('&#8230;', '...'))
    charlist.append(('&#8234;', ''))
    charlist.append(('&#x21;', '!'))
    charlist.append(('&#x26;', '&'))
    charlist.append(('&#x27;', "'"))
    charlist.append(('&#x3f;', '?'))
    charlist.append(('&#xB7;', '·'))
    charlist.append(('&#xC4;', 'Ä'))
    charlist.append(('&#xD6;', 'Ö'))
    charlist.append(('&#xDC;', 'Ü'))
    charlist.append(('&#xDF;', 'ß'))
    charlist.append(('&#xE4;', 'ä'))
    charlist.append(('&#xE9;', 'é'))
    charlist.append(('&#xF6;', 'ö'))
    charlist.append(('&#xF8;', 'ø'))
    charlist.append(('&#xFB;', 'û'))
    charlist.append(('&#xFC;', 'ü'))
    charlist.append(('&8221;', '\xe2\x80\x9d'))
    charlist.append(('&8482;', '\xe2\x84\xa2'))
    charlist.append(('&Aacute;', '\xc3\x81'))
    charlist.append(('&Acirc;', '\xc3\x82'))
    charlist.append(('&Agrave;', '\xc3\x80'))
    charlist.append(('&Auml;', '\xc3\x84'))
    charlist.append(('&Iacute;', '\xc3\x8d'))
    charlist.append(('&Icirc;', '\xc3\x8e'))
    charlist.append(('&Igrave;', '\xc3\x8c'))
    charlist.append(('&Iuml;', '\xc3\x8f'))
    charlist.append(('&Oacute;', '\xc3\x93'))
    charlist.append(('&Ocirc;', '\xc3\x94'))
    charlist.append(('&Ograve;', '\xc3\x92'))
    charlist.append(('&Ouml;', '\xc3\x96'))
    charlist.append(('&Uacute;', '\xc3\x9a'))
    charlist.append(('&Ucirc;', '\xc3\x9b'))
    charlist.append(('&Ugrave;', '\xc3\x99'))
    charlist.append(('&Uuml;', '\xc3\x9c'))
    charlist.append(('&aacute;', '\xc3\xa1'))
    charlist.append(('&acirc;', '\xc3\xa2'))
    charlist.append(('&acute;', '\''))
    charlist.append(('&agrave;', '\xc3\xa0'))
    charlist.append(('&amp;', '&'))
    charlist.append(('&apos;', "'"))
    charlist.append(('&auml;', '\xc3\xa4'))
    charlist.append(('&bdquo;', '"'))
    charlist.append(('&bdquo;', '"'))
    charlist.append(('&eacute;', '\xc3\xa9'))
    charlist.append(('&ecirc;', '\xc3\xaa'))
    charlist.append(('&egrave;', '\xc3\xa8'))
    charlist.append(('&euml;', '\xc3\xab'))
    charlist.append(('&gt;', '>'))
    charlist.append(('&hellip;', '...'))
    charlist.append(('&iacute;', '\xc3\xad'))
    charlist.append(('&icirc;', '\xc3\xae'))
    charlist.append(('&igrave;', '\xc3\xac'))
    charlist.append(('&iuml;', '\xc3\xaf'))
    charlist.append(('&laquo;', '"'))
    charlist.append(('&ldquo;', '"'))
    charlist.append(('&lsquo;', '\''))
    charlist.append(('&lt;', '<'))
    charlist.append(('&mdash;', '—'))
    charlist.append(('&nbsp;', ' '))
    charlist.append(('&ndash;', '-'))
    charlist.append(('&oacute;', '\xc3\xb3'))
    charlist.append(('&ocirc;', '\xc3\xb4'))
    charlist.append(('&ograve;', '\xc3\xb2'))
    charlist.append(('&ouml;', '\xc3\xb6'))
    charlist.append(('&quot;', '"'))
    charlist.append(('&raquo;', '"'))
    charlist.append(('&rsquo;', '\''))
    charlist.append(('&szlig;', '\xc3\x9f'))
    charlist.append(('&uacute;', '\xc3\xba'))
    charlist.append(('&ucirc;', '\xc3\xbb'))
    charlist.append(('&ugrave;', '\xc3\xb9'))
    charlist.append(('&uuml;', '\xc3\xbc'))
    charlist.append(('\u0026', '&'))
    charlist.append(('\u003d', '='))
    charlist.append(('\u00a0', ' '))
    charlist.append(('\u00b4', '\''))
    charlist.append(('\u00c1', 'Á'))
    charlist.append(('\u00c4', 'Ä'))
    charlist.append(('\u00c6', 'Æ'))
    charlist.append(('\u00d6', 'Ö'))
    charlist.append(('\u00dc', 'Ü'))
    charlist.append(('\u00df', 'ß'))
    charlist.append(('\u00e0', 'à'))
    charlist.append(('\u00e1', 'á'))
    charlist.append(('\u00e4', 'ä'))
    charlist.append(('\u00e7', 'ç'))
    charlist.append(('\u00e8', 'é'))
    charlist.append(('\u00e9', 'é'))
    charlist.append(('\u00f6', 'ö'))
    charlist.append(('\u00fc', 'ü'))
    charlist.append(('\u014d', 'ō'))
    charlist.append(('\u016b', 'ū'))
    charlist.append(('\u2013', '–'))
    charlist.append(('\u2018', '\"'))
    charlist.append(('\u2019s', '’'))
    charlist.append(('\u201a', '\"'))
    charlist.append(('\u201c', '\"'))
    charlist.append(('\u201d', '\''))
    charlist.append(('\u201e', '\"'))
    charlist.append(('\u2026', '...'))
    for repl in charlist:
        text = text.replace(repl[0], repl[1])
    from re import sub as re_sub
    text = re_sub('<[^>]+>', '', text)
    if pythonVer == 3:
        text = text.encode('utf-8').decode('unicode_escape')
    return str(text) # str needed for PLi

def decodeHtml(text):
    if pythonVer == 3:
        import html
        text = html.unescape(text)
    else:
        from six.moves import (html_parser)
        h = html_parser.HTMLParser()
        text = h.unescape(text.decode('utf8')).encode('utf8')
    text = text.replace('&amp;', '&')
    text = text.replace('&apos;', "'")
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&ndash;', '-')
    text = text.replace('&quot;', '"')
    text = text.replace('&ntilde;', '~')
    text = text.replace('&rsquo;', '\'')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&equals;', '=')
    text = text.replace('&quest;', '?')
    text = text.replace('&comma;', ',')
    text = text.replace('&period;', '.')
    text = text.replace('&colon;', ':')
    text = text.replace('&lpar;', '(')
    text = text.replace('&rpar;', ')')
    text = text.replace('&excl;', '!')
    text = text.replace('&dollar;', '$')
    text = text.replace('&num;', '#')
    text = text.replace('&ast;', '*')
    text = text.replace('&lowbar;', '_')
    text = text.replace('&lsqb;', '[')
    text = text.replace('&rsqb;', ']')
    text = text.replace('&half;', '1/2')
    text = text.replace('&DiacriticalTilde;', '~')
    text = text.replace('&OpenCurlyDoubleQuote;', '"')
    text = text.replace('&CloseCurlyDoubleQuote;', '"')
    return text.strip()


def remove_line(filename, what):
    if os.path.isfile(filename):
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

# {
# "serverlist": [
# {
# "name":"Vavoo",
# "mainUrl":"https://www2.vavoo.to",
# "UserAgent": "VAVOO/2.6",
# "StreamUrlType": "http",
# "UpdateTime": 2,
# "mediatype":"api",
# "id":"vavooapi"
# }
# ]
# }



# std_headers = {
               # 'User-Agent': 'VAVOO/2.6',
               # 'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
               # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               # 'Accept-Language': 'en-us,en;q=0.5',
               # }
std_headers = {
               'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
               'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Language': 'en-us,en;q=0.5',
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
]


def RequestAgent():
    from random import choice
    RandomAgent = choice(ListAgent)
    return RandomAgent
