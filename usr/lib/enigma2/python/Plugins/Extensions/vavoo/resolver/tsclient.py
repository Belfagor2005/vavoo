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
    http://nneonneo.bpass#logspot.gr/2010/08/http-live-streaming-client.html

Depends on python-crypto (for secure stream)
Modified for OpenPli enigma2 usage by athoik
Modified for KodiDirect, KodiLite and IPTVworld by pcd
"""
import sys
import threading
import time
import os
# import re
# import operator
# import six
from six.moves.urllib.request import urlopen
# from six.moves.urllib.request import Request
# from six.moves.urllib.error import HTTPError, URLError
# from six.moves.urllib.parse import urlparse
# from six.moves.urllib.parse import quote
# from six.moves.urllib.parse import urlencode
# from six.moves.urllib.parse import unquote
# from six.moves.urllib.parse import quote_plus
# from six.moves.urllib.parse import unquote_plus
# from six.moves.urllib.parse import parse_qs
# from six.moves.urllib.request import urlretrieve
import bitstring
PY3 = sys.version_info.major >= 3
try:
    import queue
except ImportError:
    import Queue as queue


def log(msg):
    f1 = open("/tmp/e.log", "a")
    ms = "\n" + msg
    f1.write(ms)
    f1.close()


SUPPORTED_VERSION = 3
STREAM_PFILE = '/tmp/hls.avi'
defualtype = ""


def getLastPTS(data, rpid, type="video"):
    ret = None
    currentpost = len(data)
    found = False
    packsize = 188
    spoint = 0
    while not found:
        ff = data.rfind('\x47', 0, currentpost - 1)
        if ff == - 1:
            found = True
        elif data[ff - packsize] == '\x47' and data[ff - packsize - packsize] == '\x47':
            spoint = ff
            found = True
        else:
            currentpost = ff - 1
    if spoint <= 0:
        return None

    currentpost = spoint
    found = False
    while not found:
        if len(data) - currentpost >= 188:
            bytes = data[currentpost:currentpost+188]

            bits = bitstring.ConstBitStream(bytes=bytes)
            sign = bits.read(8).uint
            tei = bits.read(1).uint
            pusi = bits.read(1).uint
            transportpri = bits.read(1).uint
            pid = bits.read(13).uint
            if pid == rpid or rpid == 0:
                try:
                    packet = bits.read((packsize-3)*8)
                    scramblecontrol = packet.read(2).uint
                    adapt = packet.read(2).uint
                    concounter = packet.read(4).uint
                except:
                    return None
                decodedpts = None
                av = ""
                if adapt == 3:
                    adaptation_size = packet.read(8).uint
                    discontinuity = packet.read(1).uint
                    random = packet.read(1).uint
                    espriority = packet.read(1).uint
                    pcrpresent = packet.read(1).uint
                    opcrpresent = packet.read(1).uint
                    splicingpoint = packet.read(1).uint
                    transportprivate = packet.read(1).uint
                    adaptation_ext = packet.read(1).uint
                    restofadapt = (adaptation_size+3) - 1
                    if pcrpresent == 1:
                        pcr = packet.read(48)
                        restofadapt -= 6
                    if opcrpresent == 1:
                        opcr = packet.read(48)
                        restofadapt -= 6
                    packet.pos += (restofadapt-3) * 8
                    if ((packet.len - packet.pos)/8) > 5:
                        pesync = packet.read(24)  # .hex
                        if pesync == ('0x000001'):
                            pestype = packet.read(8).uint
                            if pestype > 223 and pestype < 240:
                                av = 'video'
                            if pestype < 223 and pestype > 191:
                                av = 'audio'
                            packet.pos += (3*8)
                            ptspresent = packet.read(1).uint
                            dtspresent = packet.read(1).uint
                            if ptspresent:
                                packet.pos += (14)
                                pts = packet.read(40)
                                pts.pos = 4
                                firstpartpts = pts.read(3)
                                pts.pos += 1
                                secondpartpts = pts.read(15)
                                pts.pos += 1
                                thirdpartpts = pts.read(15)
                                # decodedpts = bitstring.ConstBitArray().join([firstpartpts.bin, secondpartpts.bin, thirdpartpts.bin]).uint
                                decodedpts = int(''.join([firstpartpts.bin, secondpartpts.bin, thirdpartpts.bin]), 2)
                            if dtspresent:
                                dts = packet.read(40)
                                dts.pos = 4
                                firstpartdts = dts.read(3)
                                dts.pos += 1
                                secondpartdts = dts.read(15)
                                dts.pos += 1
                                thirdpartdts = dts.read(15)
                                # decodeddts = bitstring.ConstBitArray().join([firstpartdts.bin, secondpartdts.bin, thirdpartdts.bin]).uint
                                decodeddts = int(''.join([firstpartdts.bin, secondpartdts.bin, thirdpartdts.bin]), 2)
                elif adapt == 2:
                    # if adapt is 2 the packet is only an adaptation field
                    adaptation_size = packet.read(8).uint
                    discontinuity = packet.read(1).uint
                    random = packet.read(1).uint
                    espriority = packet.read(1).uint
                    pcrpresent = packet.read(1).uint
                    opcrpresent = packet.read(1).uint
                    splicingpoint = packet.read(1).uint
                    transportprivate = packet.read(1).uint
                    adaptation_ext = packet.read(1).uint
                    restofadapt = (adaptation_size+3) - 1
                    if pcrpresent == 1:
                        pcr = packet.read(48)
                        restofadapt -= 6
                    if opcrpresent == 1:
                        opcr = packet.read(48)
                        restofadapt -= 6
                elif adapt == 1:
                    pesync = packet.read(24)  # .hex
                    if pesync == ('0x000001'):
                        pestype = packet.read(8).uint
                        if pestype > 223 and pestype < 240:
                            av = 'video'
                        if pestype < 223 and pestype > 191:
                            av = 'audio'
                        packet.pos += 24
                        ptspresent = packet.read(1).uint
                        dtspresent = packet.read(1).uint
                        if ptspresent:
                            packet.pos += (14)
                            pts = packet.read(40)
                            pts.pos = 4
                            firstpartpts = pts.read(3)
                            pts.pos += 1
                            secondpartpts = pts.read(15)
                            pts.pos += 1
                            thirdpartpts = pts.read(15)
                            # decodedpts = bitstring.ConstBitArray().join([firstpartpts.bin, secondpartpts.bin, thirdpartpts.bin]).uint
                            decodedpts = int(''.join([firstpartpts.bin, secondpartpts.bin, thirdpartpts.bin]), 2)
                        if dtspresent:
                            dts = packet.read(40)
                            dts.pos = 4
                            firstpartdts = dts.read(3)
                            dts.pos += 1
                            secondpartdts = dts.read(15)
                            dts.pos += 1
                            thirdpartdts = dts.read(15)
                            # decodeddts = bitstring.ConstBitArray().join([firstpartdts.bin, secondpartdts.bin, thirdpartdts.bin]).uint
                            decodeddts = int(''.join([firstpartdts.bin, secondpartdts.bin, thirdpartdts.bin]), 2)
                if decodedpts and (type == "" or av == type) and len(av) > 0:
                    return decodedpts

        currentpost = currentpost-packsize
        if currentpost < 10:
            found = True
    return ret


def getFirstPTSFrom(data, rpid, initpts, type="video"):
    ret = None
    currentpost = 0  # len(data)
    found = False
    packsize = 188
    spoint = 0
    while not found:
        ff = data.find('\x47', currentpost)
        if ff == - 1:
            found = True
        elif data[ff + packsize] == '\x47' and data[ff + packsize+packsize] == '\x47':
            spoint = ff
            found = True
        else:
            currentpost = ff + 1
    if spoint > len(data) - packsize:
        return None
    currentpost = spoint
    found = False

    while not found:
        if len(data) - currentpost >= 188:
            bytes = data[currentpost:currentpost+188]
            bits = bitstring.ConstBitStream(bytes=bytes)
            sign = bits.read(8).uint
            tei = bits.read(1).uint
            pusi = bits.read(1).uint
            transportpri = bits.read(1).uint
            pid = bits.read(13).uint
            if rpid == pid or rpid == 0:
                try:
                    packet = bits.read((packsize-3)*8)
                    scramblecontrol = packet.read(2).uint
                    adapt = packet.read(2).uint
                    concounter = packet.read(4).uint
                except:
                    return None
                decodedpts = None
                av = ""
                if adapt == 3:
                    adaptation_size = packet.read(8).uint
                    discontinuity = packet.read(1).uint
                    random = packet.read(1).uint
                    espriority = packet.read(1).uint
                    pcrpresent = packet.read(1).uint
                    opcrpresent = packet.read(1).uint
                    splicingpoint = packet.read(1).uint
                    transportprivate = packet.read(1).uint
                    adaptation_ext = packet.read(1).uint
                    restofadapt = (adaptation_size+3) - 1
                    if pcrpresent == 1:
                        pcr = packet.read(48)
                        restofadapt -= 6
                    if opcrpresent == 1:
                        opcr = packet.read(48)
                        restofadapt -= 6
                    packet.pos += (restofadapt-3) * 8
                    if ((packet.len - packet.pos)/8) > 5:
                        pesync = packet.read(24)  # .hex
                        if pesync == ('0x000001'):
                            pestype = packet.read(8).uint
                            if pestype > 223 and pestype < 240:
                                av = 'video'
                            if pestype < 223 and pestype > 191:
                                av = 'audio'
                            packet.pos += (3*8)
                            ptspresent = packet.read(1).uint
                            dtspresent = packet.read(1).uint
                            if ptspresent:
                                packet.pos += (14)
                                pts = packet.read(40)
                                pts.pos = 4
                                firstpartpts = pts.read(3)
                                pts.pos += 1
                                secondpartpts = pts.read(15)
                                pts.pos += 1
                                thirdpartpts = pts.read(15)
                                # decodedpts = bitstring.ConstBitArray().join([firstpartpts.bin, secondpartpts.bin, thirdpartpts.bin]).uint
                                decodedpts = int(''.join([firstpartpts.bin, secondpartpts.bin, thirdpartpts.bin]), 2)
                            if dtspresent:
                                dts = packet.read(40)
                                dts.pos = 4
                                firstpartdts = dts.read(3)
                                dts.pos += 1
                                secondpartdts = dts.read(15)
                                dts.pos += 1
                                thirdpartdts = dts.read(15)
                                # decodeddts = bitstring.ConstBitArray().join([firstpartdts.bin, secondpartdts.bin, thirdpartdts.bin]).uint
                                decodeddts = int(''.join([firstpartdts.bin, secondpartdts.bin, thirdpartdts.bin]), 2)
                elif adapt == 2:
                    # if adapt is 2 the packet is only an adaptation field
                    adaptation_size = packet.read(8).uint
                    discontinuity = packet.read(1).uint
                    random = packet.read(1).uint
                    espriority = packet.read(1).uint
                    pcrpresent = packet.read(1).uint
                    opcrpresent = packet.read(1).uint
                    splicingpoint = packet.read(1).uint
                    transportprivate = packet.read(1).uint
                    adaptation_ext = packet.read(1).uint
                    restofadapt = (adaptation_size+3) - 1
                    if pcrpresent == 1:
                        pcr = packet.read(48)
                        restofadapt -= 6
                    if opcrpresent == 1:
                        opcr = packet.read(48)
                        restofadapt -= 6
                elif adapt == 1:
                    pesync = packet.read(24)  # .hex
                    if pesync == ('0x000001'):
                        pestype = packet.read(8).uint
                        if pestype > 223 and pestype < 240:
                            av = 'video'
                        if pestype < 223 and pestype > 191:
                            av = 'audio'
                        packet.pos += 24
                        ptspresent = packet.read(1).uint
                        dtspresent = packet.read(1).uint
                        if ptspresent:
                            packet.pos += (14)
                            pts = packet.read(40)
                            pts.pos = 4
                            firstpartpts = pts.read(3)
                            pts.pos += 1
                            secondpartpts = pts.read(15)
                            pts.pos += 1
                            thirdpartpts = pts.read(15)
                            # decodedpts = bitstring.ConstBitArray().join([firstpartpts.bin, secondpartpts.bin, thirdpartpts.bin]).uint
                            decodedpts = int(''.join([firstpartpts.bin, secondpartpts.bin, thirdpartpts.bin]), 2)
                        if dtspresent:
                            dts = packet.read(40)
                            dts.pos = 4
                            firstpartdts = dts.read(3)
                            dts.pos += 1
                            secondpartdts = dts.read(15)
                            dts.pos += 1
                            thirdpartdts = dts.read(15)
                            # decodeddts = bitstring.ConstBitArray().join([firstpartdts.bin, secondpartdts.bin, thirdpartdts.bin]).uint
                            decodeddts = int(''.join([firstpartdts.bin, secondpartdts.bin, thirdpartdts.bin]), 2)
                if decodedpts and (type == "" or av == type) and len(av) > 0:
                    if decodedpts > initpts:
                        return decodedpts, currentpost
        else:
            found = True
        currentpost = currentpost+188
        if currentpost >= len(data):
            found = True
    return ret


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
#    def download_chunks(self, downloadUrl, chunk_size=4096):

    def download_chunks(self, downloadUrl, chunk_size=192512):
        conn = urlopen(downloadUrl)
        while 1:
            data = conn.read(chunk_size)
            if not data:
                return
            yield data

    def download_file(self, downloadUrl):
        return ''.join(self.download_chunks(downloadUrl))

    def player_pipe(self, queue, videopipe):
        while not self._stop:
            block = queue.get(block=True)
            if block is None:
                return
            videopipe.write(block)
            # videopipe.flush()
            if not self._downLoading:
                self._downLoading = True

    def play(self):
        # check if pipe exists
        # if os.access(STREAM_PFILE, os.W_OK):
        if os.path.exists(STREAM_PFILE):
            os.remove(STREAM_PFILE)
        # os.mkfifo(STREAM_PFILE)
        cmd = "/usr/bin/mkfifo " + STREAM_PFILE
        os.system(cmd)
        videopipe = open(STREAM_PFILE, "w+b")
        variants = []
        variant = None
        """
        for line in self.gen_m3u(self.url):
            if line.startswith('#EXT'):
                tag, attribs = self.parse_m3u_tag(line)
                if tag == '#EXT-X-STREAM-INF':
                    variant = attribs
            elif variant:
                variants.append((line, variant))
                variant = None
        pass#print "Here in hlsclient-py variants =", variants
        if len(variants) == 1:
            self.url = urlparse.urljoin(self.url, variants[0][0])
        elif len(variants) >= 2:
            pass#print '[hlsclient::play] More than one variant of the stream was provided.'
            autoChoice = {}
            for i, (vurl, vattrs) in enumerate(variants):
                pass#print "i, vurl =", i, vurl
                pass#print "i, vattrs =", i, vattrs
                for attr in vattrs:
                    key, value = attr.split('=')
                    key = key.strip()
                    value = value.strip().strip('"')
                    if key == 'BANDWIDTH':
                        #Limit bandwidth?
                        #if int(value) < 1000000:
                        #    autoChoice[i] = int(value)
                        autoChoice[i] = int(value)
                        pass#print 'bitrate %.2f kbps' % (int(value)/1024.0)
                    elif key == 'PROGRAM-ID':
                        pass#print 'program %s' % value,
                    elif key == 'CODECS':
                        pass#print 'codec %s' % value,
                    elif key == 'RESOLUTION':
                        pass#print 'resolution %s' % value,
                    else:
                        pass
#                        raise ValueError('[hlsclient::play] unknown STREAM-INF attribute %s' % key)
##                        pass#print "Here in hls-py into stop 1"
##                        os.remove(STREAM_PFILE)
##                        self.stop()
#                print
            choice = max(autoChoice.iteritems(), key=operator.itemgetter(1))[0]
            pass#print '[hlsclient::play] Autoselecting %s' % choice
            #Use the first choice for testing
##            choice = 0
            self.url = urlparse.urljoin(self.url, variants[choice][0])
        """
        queue = queue.Queue(1024)  # 1024 blocks of 4K each ~ 4MB buffer
        self.thread = threading.Thread(target=self.player_pipe, args=(queue, videopipe))
        self.thread.start()
#        try:
        fpts = 0
        while self.thread.isAlive():
            if self._stop:
                self.hread._Thread__stop()
            """
            medialist = list(self.handle_basic_m3u(self.url))
            pass#print 'Here in [hlsclient::play] medialist A=', medialist
            if None in medialist:
                # choose to start playback at the start, since this is a VOD stream
                pass
            else:
                # choose to start playback three files from the end, since this is a live stream
                medialist = medialist[-3:]
                pass#print 'Here in [hlsclient::play] medialist =', medialist
            for media in medialist:
              try:
                if media is None:
                    queue.put(None, block=True)
                    return
                seq, enc, duration, targetduration, media_url = media
                pass#print 'Here in [hlsclient::play] media_url =', media_url
                if seq > last_seq:
            """
            lastpts = 0
            fixpid = 256
            lastchunk = ""
#                fpts = 0
            i = 0
            starttime = time.time()
            for chunk in self.download_chunks(self.url):
                lastchunk = chunk
                if len(chunk) > 1:
                    if i == 0:
                        try:
                            firstpts, pos = getFirstPTSFrom(chunk, fixpid, lastpts)
                        except:
                            continue
                    i = i+1
                    queue.put(chunk, block=True)
                else:
                    continue
            lc = len(lastchunk)
            fpts = firstpts
            lastpts = getLastPTS(lastchunk, fixpid, defualtype)
            if (lastpts is None) or (lastpts == "None"):
                lastpts = 0
            videotime = lastpts - firstpts
            videotime = videotime/90000
            starttime = int(float(starttime))
            endtime = time.time()
            endtime = int(float(endtime))
            timetaken = endtime - starttime
            if videotime > timetaken:
                sleeptime = videotime - timetaken
            else:
                sleeptime = 10

            time.sleep(sleeptime)

            """
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
#        except Exception as ex:
#            pass#print '[hlsclient::play] Exception %s; Stopping threads' % ex
#            self._stop = True
#            self_downLoading = False
#            self.thread._Thread__stop()
#            self._Thread__stop()
            """
            pass

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
        if (sys.argv[2]) == '1':
            h.play()
    except:
        os.remove(STREAM_PFILE)
        h.stop()
