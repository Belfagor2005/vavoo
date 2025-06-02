"""
Simple HTTP Live Streaming client.

References:
    http://tools.ietf.org/html/draft-pantos-http-live-streaming-08

This program is free software. It comes without any warranty, to
the extent permitted by applicable law. You can redistribute it
and/or modify it under the terms of the Do What The Fuck You Want
To Public License, Version 2, as published by Sam Hocevar. See
http://sam.zoy.org/wtfpl/COPYING for more details.

Last updated: July 22, 2012

Original Code From:
    http://nneonneo.blogspot.gr/2010/08/http-live-streaming-client.html

Depends on python-crypto (for secure stream)
Modified for OpenPli enigma2 usage by athoik
Modified for KodiDirect and IPTVworld by pcd
"""
# updated by pcd@xtrend-alliance 20140906##
# 20180829 - back to v4.0 last version for mobdro (startecmob##
# recoded lululla 20220922
import sys
import threading
import time
import os
from random import choice
from six.moves.urllib.request import urlopen
from six.moves.urllib.request import Request
from six.moves.urllib.parse import urlparse
try:
    import queue
except ImportError:
    import Queue as queue


PY3 = sys.version_info.major >= 3

SUPPORTED_VERSION = 3
STREAM_PFILE = '/tmp/hls.avi'


ListAgent = [
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
]


def RequestAgent():
    RandomAgent = choice(ListAgent)
    return RandomAgent


if PY3:
    def getUrl(url):
        req = Request(url)
        req.add_header('User-Agent', RequestAgent())
        try:
            response = urlopen(req)
            link = response.read().decode(errors='ignore')
            response.close()
            return link
        except BaseException:
            import ssl
            gcontext = ssl._create_unverified_context()
            response = urlopen(req, context=gcontext)
            link = response.read().decode(errors='ignore')
            response.close()
            return link

    def getUrl2(url, referer):
        req = Request(url)
        req.add_header('User-Agent', RequestAgent())
        req.add_header('Referer', referer)
        try:
            response = urlopen(req)
            link = response.read().decode()
            response.close()
            return link
        except BaseException:
            import ssl
            gcontext = ssl._create_unverified_context()
            response = urlopen(req, context=gcontext)
            link = response.read().decode()
            response.close()
            return link

else:
    def getUrl(url):
        req = Request(url)
        req.add_header('User-Agent', RequestAgent())
        try:
            response = urlopen(req)
            link = response.read()
            response.close()
            return link
        except BaseException:
            import ssl
            gcontext = ssl._create_unverified_context()
            response = urlopen(req, context=gcontext)
            link = response.read()
            response.close()
            return link

    def getUrl2(url, referer):
        req = Request(url)
        req.add_header('User-Agent', RequestAgent())
        req.add_header('Referer', referer)
        try:
            response = urlopen(req)
            link = response.read()
            response.close()
            return link
        except BaseException:
            import ssl
            gcontext = ssl._create_unverified_context()
            response = urlopen(req, context=gcontext)
            link = response.read()
            response.close()
            return link


class hlsclient(threading.Thread):

    def __init__(self):
        self._stop = False
        self.thread = None
        self._downLoading = False
        threading.Thread.__init__(self)

    def setUrl(self, url):
        self.url = url
        self._stop = False
        self.thread = None
        self._downLoading = False

    def isDownloading(self):
        return self._downLoading

    def run(self):
        # Check if self.header is initialized before calling play
        if not hasattr(self, 'header') or not self.header:
            raise ValueError("Header is not initialized.")
        self.play(self.header)

    def download_chunks(self, downloadUrl, chunk_size=4096):
        """
        req = urllib2.Request(downloadUrl)
        pass#print "Here in hlsclient-py self.header =", self.header
        #        if self.header != "":
        hdr = 'User-Agent=ONLINETVCLIENT_X60000_X25000_X4000MEGA_V1770'
        req.add_header('User-Agent', 'User-Agent=ONLINETVCLIENT_X60000_X25000_X4000MEGA_V1770')
        conn = urllib2.urlopen(req)
        pass#print "Here in hlsclient-py downloadUrl done"
        """
        if "Referer" in self.header:
            n1 = self.header.find("Referer", 0)
            n2 = self.header.find("=", n1)
            n3 = self.header.find("&", n2)
            refr = self.header[(n2 + 1):n3]
        else:
            refr = ""
        conn = getUrl2(downloadUrl, refr)
        while 1:
            data = conn.read(chunk_size)
            if not data:
                return
            yield data

    def download_file(self, downloadUrl):
        return ''.join(self.download_chunks(downloadUrl))

    def validate_m3u(self, conn):
        ''' make sure file is an m3u, and returns the encoding to use. '''
        mime = conn.headers.get('Content-Type', '').split(';')[0].lower()
        if mime == 'application/vnd.apple.mpegurl':
            enc = 'utf8'
        elif mime == 'audio/mpegurl':
            enc = 'iso-8859-1'
        elif conn.url.endswith('.m3u8'):
            enc = 'utf8'
        elif conn.url.endswith('.m3u'):
            enc = 'iso-8859-1'
        else:
            os.remove(STREAM_PFILE)
            self.stop()
        if conn.readline().rstrip('\r\n') != '#EXTM3U':
            os.remove(STREAM_PFILE)
            self.stop()
        return enc

    def gen_m3u(self, url, skip_comments=True):
        """
                req = urllib2.Request(url)
                if self.header = "":
                        req = urllib2.Request(url)
                req.add_header('User-Agent', str(self.header))
                conn = urllib2.urlopen(req)
        """
        if "Referer" in self.header:
            n1 = self.header.find("Referer", 0)
            n2 = self.header.find("=", n1)
            n3 = self.header.find("&", n2)
            refr = self.header[(n2 + 1): n3]
        else:
            refr = ""
        conn = getUrl2(url, refr)
        enc = 'utf8'
        for line in conn:
            line = line.rstrip('\r\n').decode(enc)
            if not line:
                continue
            elif line.startswith('#EXT'):
                # tag
                yield line
            elif line.startswith('#'):
                # comment
                if skip_comments:
                    continue
                else:
                    yield line
            else:
                # media file
                yield line

    def parse_m3u_tag(self, line):
        if ':' not in line:
            return line, []
        tag, attribstr = line.split(':', 1)
        attribs = []
        last = 0
        quote = False
        for i, c in enumerate(attribstr + ','):
            if c == '"':
                quote = not quote
            if quote:
                continue
            if c == ',':
                attribs.append(attribstr[last:i])
                last = i + 1
        return tag, attribs

    def parse_kv(self, attribs, known_keys=None):
        d = {}
        for item in attribs:
            k, v = item.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"')
            if known_keys is not None and k not in known_keys:
                os.remove(STREAM_PFILE)
                self.stop()
            d[k] = v
        return d

    def handle_basic_m3uX(self, hlsUrl):
        seq = 1
        self.enc = None
        self.duration = 5
        self.targetduration = 5

        for line in self.gen_m3u(hlsUrl):
            if line.startswith("#EXT"):
                result = self._handle_ext_tag(line, seq)
                if result is None:
                    continue
                if result is False:
                    return
                seq = result
            else:
                yield (seq, self.enc, self.duration, self.targetduration, line)
                seq += 1

    def _handle_ext_tag(self, line, seq):
        tag, attribs = self.parse_m3u_tag(line)

        if tag == "#EXTINF":
            self.duration = float(attribs[0])
        elif tag == "#EXT-X-TARGETDURATION":
            self._assert_single_attribute(attribs, tag)
            self.targetduration = int(attribs[0])
        elif tag == "#EXT-X-MEDIA-SEQUENCE":
            self._assert_single_attribute(attribs, tag)
            return int(attribs[0])
        elif tag == "#EXT-X-KEY":
            self.enc = self._parse_encryption_key(attribs, seq)
        elif tag == "#EXT-X-ENDLIST":
            yield None
            return False
        elif tag == "#EXT-X-STREAM-INF":
            os.remove(STREAM_PFILE)
            self.stop()
            return False
        elif tag == "#EXT-X-DISCONTINUITY":
            pass
        elif tag == "#EXT-X-VERSION":
            self._assert_single_attribute(attribs, tag)
            version = int(attribs[0])
            if version > SUPPORTED_VERSION:
                pass  # unsupported version warning
        elif tag == "#EXT-X-ALLOW-CACHE" or tag == "#EXT-X-PROGRAM-DATE-TIME":
            pass
        else:
            os.remove(STREAM_PFILE)
            self.stop()
            return False

        return seq

    def _parse_encryption_key(self, attribs, seq):
        import struct
        from Crypto.Cipher import AES

        attribs = self.parse_kv(attribs, ("METHOD", "URI", "IV"))
        method = attribs.get("METHOD")

        if method == "NONE":
            assert "URI" not in attribs and "IV" not in attribs
            return None

        if method == "AES-128":
            uri = attribs["URI"].strip('"')
            if "https://" in uri:
                key = self.download_file(uri)
            else:
                key = self.download_file(
                    "m3u8http://hls.fra.rtlnow.de/hls-vod-enc-key/vodkey.bin")

            assert len(key) == 16

            if "IV" in attribs:
                iv = attribs["IV"][2:].zfill(32).decode("hex")
                assert len(iv) == 16
            else:
                iv = "\0" * 8 + struct.pack(">Q", seq)

            return AES.new(key, AES.MODE_CBC, iv)

        raise ValueError(
            "[hlsclient::_parse_encryption_key] Unknown METHOD: " +
            method)

    def _assert_single_attribute(self, attribs, tag):
        assert len(
            attribs) == 1, "[hlsclient::_handle_ext_tag] too many attribs in " + tag

    def handle_basic_m3u(self, hlsUrl):
        seq = 1
        enc = None
        duration = 5
        targetduration = 5

        for line in self.gen_m3u(hlsUrl):
            if "#EXT-X-PLAYLIST-TYPE:VOD" in line:
                continue
            if line.startswith("#EXT"):
                result = self._handle_m3u_tag(line, seq, enc)
                if result is None:
                    yield None
                    return
                seq, enc, duration, targetduration = result
            else:
                yield (seq, enc, duration, targetduration, line)
                seq += 1

    def _handle_m3u_tag(self, line, seq, enc):
        tag, attribs = self.parse_m3u_tag(line)

        if tag == "#EXTINF":
            return seq, enc, float(attribs[0]), None
        if tag == "#EXT-X-TARGETDURATION":
            assert len(attribs) == 1
            return seq, enc, None, int(attribs[0])
        if tag == "#EXT-X-MEDIA-SEQUENCE":
            assert len(attribs) == 1
            return int(attribs[0]), enc, None, None
        if tag == "#EXT-X-KEY":
            enc = self._handle_ext_key(attribs, seq)
            return seq, enc, None, None
        if tag == "#EXT-X-PROGRAM-DATE-TIME":
            assert len(attribs) == 1
        elif tag == "#EXT-X-ALLOW-CACHE":
            pass
        elif tag == "#EXT-X-ENDLIST":
            return None
        elif tag == "#EXT-X-STREAM-INF":
            os.remove(STREAM_PFILE)
            self.stop()
            return None
        elif tag == "#EXT-X-DISCONTINUITY":
            assert not attribs
        elif tag == "#EXT-X-VERSION":
            assert len(attribs) == 1
            if int(attribs[0]) > SUPPORTED_VERSION:
                pass
        return seq, enc, None, None

    def _handle_ext_key(self, attribs, seq):
        import struct
        from Crypto.Cipher import AES

        attribs = self.parse_kv(attribs, ("METHOD", "URI", "IV"))
        method = attribs["METHOD"]

        if method == "NONE":
            assert "URI" not in attribs and "IV" not in attribs
            return None

        assert method == "AES-128"
        assert "URI" in attribs
        key = self.download_file(attribs["URI"].strip('"'))
        assert len(key) == 16

        if "IV" in attribs:
            assert attribs["IV"].lower().startswith("0x")
            iv = attribs["IV"][2:].zfill(32).decode("hex")
            assert len(iv) == 16
        else:
            iv = "\0" * 8 + struct.pack(">Q", seq)

        return AES.new(key, AES.MODE_CBC, iv)

    def player_pipe(self, queue, videopipe):
        while not self._stop:
            block = queue.get(block=True)
            if block is None:
                return
            videopipe.write(block)
            # videopipe.flush()
            if not self._downLoading:
                self._downLoading = True

    def play(self, header=None):
        if header is None:
            header = self.header
        if not header:
            raise ValueError("Header must be provided or initialized.")

        self._prepare_fifo()
        videopipe = open(STREAM_PFILE, "w+b")

        self.url = self._choose_variant()

        q = queue(1024)
        self.thread = threading.Thread(
            target=self.player_pipe, args=(
                q, videopipe))
        self.thread.start()

        self._play_loop(q)

    def _prepare_fifo(self):
        if os.path.exists(STREAM_PFILE):
            os.remove(STREAM_PFILE)
        os.system("/usr/bin/mkfifo " + STREAM_PFILE)

    def _choose_variant(self):
        variants = []
        variant = None
        for line in self.gen_m3u(self.url):
            if line.startswith("#EXT"):
                tag, attribs = self.parse_m3u_tag(line)
                if tag == "#EXT-X-STREAM-INF":
                    variant = attribs
            elif variant:
                variants.append((line, variant))
                variant = None

        if len(variants) == 1:
            return urlparse.urljoin(self.url, variants[0][0])

        if len(variants) >= 2:
            import operator
            autoChoice = {}
            for i, (vurl, vattrs) in enumerate(variants):
                for attr in vattrs:
                    if "=" not in attr:
                        continue
                    key, value = attr.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"')
                    if key == "BANDWIDTH":
                        autoChoice[i] = int(value)
            choice = max(autoChoice.iteritems(), key=operator.itemgetter(1))[0]
            return urlparse.urljoin(self.url, variants[choice][0])

        return self.url

    def _play_loop(self, q):
        last_seq = -1
        targetduration = 5
        changed = 0

        while self.thread.isAlive():
            if self._stop:
                self.thread._Thread__stop()
            medialist = list(self.handle_basic_m3u(self.url))
            medialist = medialist[-3:] if None not in medialist else medialist

            for media in medialist:
                try:
                    if media is None:
                        q.put(None, block=True)
                        return
                    seq, enc, duration, targetduration, media_url = media
                    if seq > last_seq:
                        for chunk in self.download_chunks(
                                urlparse.urljoin(self.url, media_url)):
                            if enc:
                                chunk = enc.decrypt(chunk)
                            q.put(chunk, block=True)
                        last_seq = seq
                        changed = 1
                except BaseException:
                    pass

            self._sleeping = True
            if changed == 1:
                time.sleep(duration)
            elif changed == 0:
                time.sleep(targetduration * 0.5)
            elif changed == -1:
                time.sleep(targetduration * 1.5)
            else:
                time.sleep(targetduration * 3.0)
            self._sleeping = False
            changed -= 1

    def stop(self):
        self._stop = True
        self._downLoading = False
        if self.thread:
            self.thread._Thread__stop()
        self._Thread__stop()


if __name__ == '__main__':
    try:
        h = hlsclient()
        h.setUrl(sys.argv[1])
        header = sys.argv[3]
        if (sys.argv[2]) == '1':
            # h.start()
            h.play(header)
    except BaseException:
        os.remove(STREAM_PFILE)
        h.stop()
