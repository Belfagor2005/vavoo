#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys
import os
import re
import base64

from enigma import getDesktop
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


def ReloadBouquets():
    from enigma import eDVBDB
    eDVBDB.getInstance().reloadServicelist()
    eDVBDB.getInstance().reloadBouquets()


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


ListAgent = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]


def RequestAgent():
    from random import choice
    RandomAgent = choice(ListAgent)
    return RandomAgent
