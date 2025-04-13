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
from six.moves.urllib.request import urlopen

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
packet = ''


def getLastPTS(data, rpid, type="video"):
	ret = None
	currentpost = len(data)
	found = False
	packsize = 188
	spoint = 0

	# Cerca l'ultimo sync byte valido
	while not found:
		ff = data.rfind(b'\x47', 0, currentpost - 1)
		if ff == -1 or ff < 2 * packsize:
			return None
		elif data[ff - packsize] == 0x47 and data[ff - 2 * packsize] == 0x47:
			spoint = ff
			found = True
		else:
			currentpost = ff - 1

	currentpost = spoint
	found = False

	while not found:
		if currentpost + packsize > len(data):
			break

		packet_data = data[currentpost:currentpost + packsize]
		bits = bitstring.ConstBitStream(bytes=packet_data)
		bits.read(8)  # sync
		bits.read(1)  # TEI
		bits.read(1)  # PUSI
		bits.read(1)  # transport_priority
		pid = bits.read(13).uint

		if pid == rpid or rpid == 0:
			try:
				packet = bits.read((packsize - 3) * 8)
				packet.read(2)  # scramble
				adapt = packet.read(2).uint
				packet.read(4)  # continuity counter
			except:
				return None

			decodedpts = None
			av = ""

			if adapt in (1, 3):  # payload o adapt+payload
				if adapt == 3:
					adapt_len = packet.read(8).uint
					packet.pos += adapt_len * 8  # skip adaptation

				if (packet.len - packet.pos) >= 48:
					if packet.peek(24).bytes == b'\x00\x00\x01':
						packet.read(24)  # PES start
						pestype = packet.read(8).uint
						if 224 <= pestype < 240:
							av = "video"
						elif 192 <= pestype < 224:
							av = "audio"
						else:
							av = ""

						packet.read(16)  # PES length
						packet.read(2)   # marker
						ptspresent = packet.read(1).uint
						# dtspresent = packet.read(1).uint
						packet.read(6)   # reserved

						if ptspresent:
							packet.pos += 4
							p1 = packet.read(3).bin
							packet.pos += 1
							p2 = packet.read(15).bin
							packet.pos += 1
							p3 = packet.read(15).bin
							decodedpts = int(p1 + p2 + p3, 2)

			if decodedpts and (type == "" or av == type):
				return decodedpts

		currentpost -= packsize
		if currentpost <= 0:
			found = True

	return ret


def getFirstPTSFrom(data, rpid, initpts, type="video"):
	ret = None
	packsize = 188
	spoint = 0
	currentpos = 0
	found = False

	# Convert to bytes if not already
	if isinstance(data, str):
		data = data.encode("latin-1")

	# Find sync point
	while not found:
		ff = data.find(b'\x47', currentpos)
		if ff == -1:
			return None
		if data[ff + packsize:ff + 2 * packsize] == b'\x47' * 2:
			spoint = ff
			break
		currentpos = ff + 1

	if spoint > len(data) - packsize:
		return None

	currentpos = spoint

	while currentpos + packsize <= len(data):
		ts_packet = data[currentpos:currentpos + packsize]
		try:
			bits = bitstring.ConstBitStream(bytes=ts_packet)
			bits.read(8)  # Sync byte
			bits.read(1)  # TEI
			# pusi = bits.read(1).uint
			bits.read(1)  # Transport priority
			pid = bits.read(13).uint
			if pid != rpid and rpid != 0:
				currentpos += packsize
				continue

			packet = bits.read((packsize - 4) * 8)
			# scramble = packet.read(2).uint
			adapt = packet.read(2).uint
			packet.read(4)  # Continuity counter

			decodedpts = None
			streamtype = ""

			if adapt & 0x02:  # Adaptation field present
				adaptation_size = packet.read(8).uint
				end_of_adapt = packet.pos + (adaptation_size * 8)
				pcrpresent = packet.read(1).uint
				opcrpresent = packet.read(1).uint

				if pcrpresent:
					packet.read(6 * 8)  # Skip PCR
				if opcrpresent:
					packet.read(6 * 8)  # Skip OPCR

				packet.pos = end_of_adapt  # Skip rest of adaptation

			if adapt & 0x01:  # Payload present
				if (packet.len - packet.pos) >= 48:
					if packet.read(24).uint == 1:  # PES start code
						pestype = packet.read(8).uint
						if 224 <= pestype < 240:
							streamtype = "video"
						elif 192 < pestype < 224:
							streamtype = "audio"
						packet.read(16)  # Skip PES flags and header length
						pts_dts_flags = packet.read(2).uint
						if pts_dts_flags & 0x02:
							packet.pos += 4
							p1 = packet.read(3).uint
							packet.pos += 1
							p2 = packet.read(15).uint
							packet.pos += 1
							p3 = packet.read(15).uint
							decodedpts = (p1 << 30) | (p2 << 15) | p3

			if decodedpts is not None and (type == "" or streamtype == type) and streamtype:
				if decodedpts > initpts:
					return decodedpts, currentpos
		except Exception:
			pass

		currentpos += packsize

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
			if not self._downLoading:
				self._downLoading = True

	def play(self):
		if os.path.exists(STREAM_PFILE):
			os.remove(STREAM_PFILE)

		os.system("/usr/bin/mkfifo " + STREAM_PFILE)
		videopipe = open(STREAM_PFILE, "w+b")

		q = queue(1024)
		self.thread = threading.Thread(target=self.player_pipe, args=(q, videopipe))
		self.thread.start()

		fixpid = 256
		lastpts = 0
		default_type = "mpegts"  # oppure impostalo dinamicamente
		i = 0
		firstpts = None
		lastchunk = ""

		while self.thread.is_alive():
			if self._stop:
				break

			i = 0
			starttime = time.time()

			for chunk in self.download_chunks(self.url):
				lastchunk = chunk
				if len(chunk) <= 1:
					continue
				if i == 0:
					try:
						firstpts, _ = getFirstPTSFrom(chunk, fixpid, lastpts)
					except Exception:
						continue
				q.put(chunk, block=True)
				i += 1

			if not lastchunk:
				continue

			lastpts = getLastPTS(lastchunk, fixpid, default_type)
			if not lastpts or lastpts == "None":
				lastpts = 0

			if firstpts is None:
				firstpts = 0

			videotime = (lastpts - firstpts) / 90000.0  # Convert PTS to seconds
			timetaken = time.time() - starttime
			sleeptime = max(videotime - timetaken, 10)

			time.sleep(sleeptime)

		try:
			videopipe.close()
		except Exception:
			pass
		print("Playback thread finished.")

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
