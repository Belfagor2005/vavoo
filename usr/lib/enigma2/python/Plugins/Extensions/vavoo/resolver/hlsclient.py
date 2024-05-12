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
import re
import operator
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
        except:
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
        except:
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
            pass  # print "Here in getUrl response =", response
            link = response.read()
            response.close()
            return link
        except:
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
        except:
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
        self.play()

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
            refr = self.header[(n2+1):n3]
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
            refr = self.header[(n2+1):n3]
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
        for i, c in enumerate(attribstr+','):
            if c == '"':
                quote = not quote
            if quote:
                continue
            if c == ',':
                attribs.append(attribstr[last:i])
                last = i+1
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
        base_key_url = re.sub('playlist-.*?.m3u8', '', hlsUrl)
        seq = 1
        enc = None
        nextlen = 5
        duration = 5
        for line in self.gen_m3u(hlsUrl):
            if line.startswith('#EXT'):
                tag, attribs = self.parse_m3u_tag(line)
                if tag == '#EXTINF':
                    duration = float(attribs[0])
                elif tag == '#EXT-X-TARGETDURATION':
                    assert len(attribs) == 1, '[hlsclient::handle_basic_m3u] too many attribs in EXT-X-TARGETDURATION'
                    targetduration = int(attribs[0])
                    pass
                elif tag == '#EXT-X-MEDIA-SEQUENCE':
                    assert len(attribs) == 1, '[hlsclient::handle_basic_m3u] too many attribs in EXT-X-MEDIA-SEQUENCE'
                    seq = int(attribs[0])
                elif tag == '#EXT-X-KEY':
                    attribs = self.parse_kv(attribs, ('METHOD', 'URI', 'IV'))
                    assert 'METHOD' in attribs, '[hlsclient::handle_basic_m3u] expected METHOD in EXT-X-KEY'
                    if attribs['METHOD'] == 'NONE':
                        assert 'URI' not in attribs, '[hlsclient::handle_basic_m3u] EXT-X-KEY: METHOD=NONE, but URI found'
                        assert 'IV' not in attribs, '[hlsclient::handle_basic_m3u] EXT-X-KEY: METHOD=NONE, but IV found'
                        enc = None
                    elif attribs['METHOD'] == 'AES-128':
                        from Crypto.Cipher import AES
                        assert 'URI' in attribs, '[hlsclient::handle_basic_m3u] EXT-X-KEY: METHOD=AES-128, but no URI found'
                        if 'https://' in attribs['URI']:
                            key = self.download_file(attribs['URI'].strip('"'))  # key = self.download_file(base_key_url+attribs['URI'].strip('"'))
                            print(attribs['URI'].strip('"'))
                        else:
                            # key = self.download_file(base_key_url+attribs['URI'].strip('"'))
                            key = self.download_file('m3u8http://hls.fra.rtlnow.de/hls-vod-enc-key/vodkey.bin')

                        assert len(key) == 16, '[hlsclient::handle_basic_m3u] EXT-X-KEY: downloaded key file has bad length'
                        if 'IV' in attribs:
                            assert attribs['IV'].lower().startswith('0x'), '[hlsclient::handle_basic_m3u] EXT-X-KEY: IV attribute has bad format'
                            iv = attribs['IV'][2:].zfill(32).decode('hex')
                            assert len(iv) == 16, '[hlsclient::handle_basic_m3u] EXT-X-KEY: IV attribute has bad length'
                        else:
                            iv = '\0'*8 + struct.pack('>Q', seq)
                        enc = AES.new(key, AES.MODE_CBC, iv)
                    else:
                        assert False, '[hlsclient::handle_basic_m3u] EXT-X-KEY: METHOD=%s unknown' % attribs['METHOD']
                elif tag == '#EXT-X-PROGRAM-DATE-TIME':
                    assert len(attribs) == 1, '[hlsclient::handle_basic_m3u] too many attribs in EXT-X-PROGRAM-DATE-TIME'
                    # TODO parse attribs[0] as ISO8601 date/time
                    pass
                elif tag == '#EXT-X-ALLOW-CACHE':
                    # XXX deliberately ignore
                    pass
                elif tag == '#EXT-X-ENDLIST':
                    assert not attribs
                    yield None
                    return
                elif tag == '#EXT-X-STREAM-INF':
                    # raise ValueError('[hlsclient::handle_basic_m3u] dont know how to handle EXT-X-STREAM-INF in basic playlist')
                    os.remove(STREAM_PFILE)
                    self.stop()
                elif tag == '#EXT-X-DISCONTINUITY':
                    assert not attribs
                    pass  # print '[hlsclient::handle_basic_m3u] discontinuity in stream'
                elif tag == '#EXT-X-VERSION':
                    assert len(attribs) == 1
                    if int(attribs[0]) > SUPPORTED_VERSION:
                        pass  # print '[hlsclient::handle_basic_m3u] file version %s exceeds supported version %d; some things might be broken' % (attribs[0], SUPPORTED_VERSION)
                else:
                    os.remove(STREAM_PFILE)
                    self.stop()
            else:
                yield (seq, enc, duration, targetduration, line)
                seq += 1

    def handle_basic_m3u(self, hlsUrl):
        seq = 1
        enc = None
        nextlen = 5
        duration = 5
        for line in self.gen_m3u(hlsUrl):
            if "#EXT-X-PLAYLIST-TYPE:VOD" in line:
                line.replace("#EXT-X-PLAYLIST-TYPE:VOD", "")
                continue
            if line.startswith('#EXT'):
                tag, attribs = self.parse_m3u_tag(line)
                if tag == '#EXTINF':
                    duration = float(attribs[0])
                elif tag == '#EXT-X-TARGETDURATION':
                    assert len(attribs) == 1, '[hlsclient::handle_basic_m3u] too many attribs in EXT-X-TARGETDURATION'
                    targetduration = int(attribs[0])
                    pass
                elif tag == '#EXT-X-MEDIA-SEQUENCE':
                    assert len(attribs) == 1, '[hlsclient::handle_basic_m3u] too many attribs in EXT-X-MEDIA-SEQUENCE'
                    seq = int(attribs[0])
                elif tag == '#EXT-X-KEY':
                    attribs = self.parse_kv(attribs, ('METHOD', 'URI', 'IV'))
                    assert 'METHOD' in attribs, '[hlsclient::handle_basic_m3u] expected METHOD in EXT-X-KEY'
                    if attribs['METHOD'] == 'NONE':
                        assert 'URI' not in attribs, '[hlsclient::handle_basic_m3u] EXT-X-KEY: METHOD=NONE, but URI found'
                        assert 'IV' not in attribs, '[hlsclient::handle_basic_m3u] EXT-X-KEY: METHOD=NONE, but IV found'
                        enc = None
                    elif attribs['METHOD'] == 'AES-128':
                        from Crypto.Cipher import AES
                        assert 'URI' in attribs, '[hlsclient::handle_basic_m3u] EXT-X-KEY: METHOD=AES-128, but no URI found'
                        key = self.download_file(attribs['URI'].strip('"'))
                        assert len(key) == 16, '[hlsclient::handle_basic_m3u] EXT-X-KEY: downloaded key file has bad length'
                        if 'IV' in attribs:
                            assert attribs['IV'].lower().startswith('0x'), '[hlsclient::handle_basic_m3u] EXT-X-KEY: IV attribute has bad format'
                            iv = attribs['IV'][2:].zfill(32).decode('hex')
                            assert len(iv) == 16, '[hlsclient::handle_basic_m3u] EXT-X-KEY: IV attribute has bad length'
                        else:
                            iv = '\0'*8 + struct.pack('>Q', seq)
                        enc = AES.new(key, AES.MODE_CBC, iv)
                    else:
                        assert False, '[hlsclient::handle_basic_m3u] EXT-X-KEY: METHOD=%s unknown' % attribs['METHOD']
                elif tag == '#EXT-X-PROGRAM-DATE-TIME':
                    assert len(attribs) == 1, '[hlsclient::handle_basic_m3u] too many attribs in EXT-X-PROGRAM-DATE-TIME'
                    pass
                elif tag == '#EXT-X-ALLOW-CACHE':
                    # XXX deliberately ignore
                    pass
                elif tag == '#EXT-X-ENDLIST':
                    assert not attribs
                    yield None
                    return
                elif tag == '#EXT-X-STREAM-INF':
                    os.remove(STREAM_PFILE)
                    self.stop()
                    # raise ValueError('[hlsclient::handle_basic_m3u] dont know how to handle EXT-X-STREAM-INF in basic playlist')
                elif tag == '#EXT-X-DISCONTINUITY':
                    assert not attribs
                elif tag == '#EXT-X-VERSION':
                    assert len(attribs) == 1
                    if int(attribs[0]) > SUPPORTED_VERSION:
                        pass  # print '[hlsclient::handle_basic_m3u] file version %s exceeds supported version %d; some things might be broken' % (attribs[0], SUPPORTED_VERSION)
                else:
                    # raise ValueError('[hlsclient::handle_basic_m3u] tag %s not known' % tag)
                    pass
                    # os.remove(STREAM_PFILE)
                    # self.stop()
            else:
                pass  # print "Here in hls-py line final=", line
                yield (seq, enc, duration, targetduration, line)
                seq += 1

    def player_pipe(self, queue, videopipe):
        while not self._stop:
            block = queue.get(block=True)
            if block is None:
                return
            videopipe.write(block)
            # videopipe.flush()
            if not self._downLoading:
                self._downLoading = True

    def play(self, header):
        # check if pipe exists
        # if os.access(STREAM_PFILE, os.W_OK):
        self.header = header
        if os.path.exists(STREAM_PFILE):
            os.remove(STREAM_PFILE)
        # os.mkfifo(STREAM_PFILE)
        cmd = "/usr/bin/mkfifo " + STREAM_PFILE
        os.system(cmd)
        videopipe = open(STREAM_PFILE, "w+b")
        variants = []
        variant = None
        for line in self.gen_m3u(self.url):
            if line.startswith('#EXT'):
                tag, attribs = self.parse_m3u_tag(line)
                if tag == '#EXT-X-STREAM-INF':
                    variant = attribs
            elif variant:
                variants.append((line, variant))
                variant = None
        if len(variants) == 1:
            self.url = urlparse.urljoin(self.url, variants[0][0])
        elif len(variants) >= 2:
            pass  # print '[hlsclient::play] More than one variant of the stream was provided.'
            autoChoice = {}
            for i, (vurl, vattrs) in enumerate(variants):
                for attr in vattrs:
                    key, value = attr.split('=')
                    key = key.strip()
                    value = value.strip().strip('"')
                    if key == 'BANDWIDTH':
                        # Limit bandwidth?
                        # if int(value) < 1000000:
                        #    autoChoice[i] = int(value)
                        autoChoice[i] = int(value)
                    elif key == 'PROGRAM-ID':
                        pass  # print 'program %s' % value,
                    elif key == 'CODECS':
                        pass  # print 'codec %s' % value,
                    elif key == 'RESOLUTION':
                        pass  # print 'resolution %s' % value,
                    else:
                        pass
            choice = max(autoChoice.iteritems(), key=operator.itemgetter(1))[0]
            self.url = urlparse.urljoin(self.url, variants[choice][0])

        queue = queue.Queue(1024)  # 1024 blocks of 4K each ~ 4MB buffer
        self.thread = threading.Thread(target=self.player_pipe, args=(queue, videopipe))
        self.thread.start()
        last_seq = -1
        targetduration = 5
        changed = 0
#        try:
        while self.thread.isAlive():
            if self._stop:
                self.thread._Thread__stop()
            medialist = list(self.handle_basic_m3u(self.url))
            if None in medialist:
                # choose to start playback at the start, since this is a VOD stream
                pass
            else:
                # choose to start playback three files from the end, since this is a live stream
                medialist = medialist[-3:]
                pass  # print 'Here in [hlsclient::play] medialist =', medialist
            for media in medialist:
                try:
                    if media is None:
                        queue.put(None, block=True)
                        return
                    seq, enc, duration, targetduration, media_url = media
                    if seq > last_seq:
                        for chunk in self.download_chunks(urlparse.urljoin(self.url, media_url)):
                            if enc:
                                chunk = enc.decrypt(chunk)
                            queue.put(chunk, block=True)
                        last_seq = seq
                        changed = 1
                except:
                    pass
            self._sleeping = True
            if changed == 1:
                # initial minimum reload delay
                time.sleep(duration)
            elif changed == 0:
                # first attempt
                time.sleep(targetduration*0.5)
            elif changed == -1:
                # second attempt
                time.sleep(targetduration*1.5)
            else:
                # third attempt and beyond
                time.sleep(targetduration*3.0)
            self._sleeping = False
            changed -= 1

    def stop(self):
        self._stop = True
        self._downLoading = False
        if self.thread:
            self.thread._Thread__stop()
        self._Thread__stop()


if __name__ == '__main__':
    pass  # print "Here in sys.argv =", sys.argv
    try:
        h = hlsclient()
        h.setUrl(sys.argv[1])
        header = sys.argv[3]
        if (sys.argv[2]) == '1':
            # h.start()
            h.play(header)
    except:
        os.remove(STREAM_PFILE)
        h.stop()
