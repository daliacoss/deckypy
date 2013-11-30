"""
deckyPy - a simple virtual MIDI keyboard
by Deckman Coss (cosstropolis.com)
"""

import rtmidi, time
from optparse import OptionParser
from getch import *

#key constants
ESC = 27

#midi constants
DATA_BYTE = 127
NOTE_ON = 144
CHANNELS = 16
PITCHES_PER_OCTAVE = 12

class Controller:
	_activeMsgs = set()

	#defaults
	_defaultPitchMap = {
		"z":0,
		"s":1,
		"x":2,
		"d":3,
		"c":4,
		"v":5,
		"g":6,
		"b":7,
		"h":8,
		"n":9,
		"j":10,
		"m":11,
		",":12,
		"l":13,
		".":14,
		";":15,
		"/":16,
		"q":12,
		"2":13,
		"w":14,
		"3":15,
		"e":16,
		"r":17,
		"5":18,
		"t":19,
		"6":20,
		"y":21,
		"7":22,
		"u":23,
		"i":24,
		"9":25,
		"o":26,
		"0":27,
		"p":28,
	}
	_defaultFuncMap = {
		"\t":"flushChannel"
	}
	_defaultChannel = 0
	_defaultVelocity = 127
	_defaultOctave = 4
	_defaultVerbose = False

	def __init__(self,
		mout,
		pitchMap =_defaultPitchMap,
		funcMap=_defaultFuncMap,
		channel=_defaultChannel,
		velocity=_defaultVelocity,
		octave=_defaultOctave,
		verbose=_defaultVerbose
	):
		self.mout = mout
		self.pitchMap = pitchMap 
		self.funcMap = funcMap
		self.channel = channel
		self.velocity = velocity
		self.octave = octave
		self.verbose = verbose

		self.sustain = False
		self.monophonic = False

	def playNote(self, channel, pitch, velocity=DATA_BYTE, sustain=False):
		"""channel must be 0-indexed"""

		channel = max(0, min(channel,CHANNELS))
		pitch = max(0, min(pitch,DATA_BYTE))
		velocity = max(0, min(velocity,DATA_BYTE))

		if self.monophonic: self.flushChannel()
		msg = (NOTE_ON + channel, pitch, velocity)
		self.mout.send_message(msg)
		self._activeMsgs.add(msg)

		if not sustain: self.stopNote(channel, pitch)
		if self.verbose: print (msg)

	def stopNote(self, channel, pitch):
		msg = (NOTE_ON + channel, pitch, 0)
		self.mout.send_message(msg)

		#remove note from set of active messages
		try:
			self._activeMsgs.remove(msg)
		except KeyError:
			pass

	def close(self):
		self.flush()
		self.mout.close_port()
		del self.mout

	def _flush(self, channel=None):
		for msg in self._activeMsgs:
			if channel != None:
				if msg[0] - NOTE_ON == channel: self.stopNote(msg[0]-NOTE_ON,msg[1])
			else:
				self.stopNote(msg[0]-NOTE_ON,msg[1])

	def flush(self):
		self._flush()

	def flushChannel(self):
		self._flush(self.channel)

	def start(self):
		print ("Controller is ready")
		c = getch()
		while ord(c) != ESC:
			pitch = self.pitchMap.get(c)
			func = self.funcMap.get(c)
			if pitch != None:
				pitch += self.octave*PITCHES_PER_OCTAVE
				self.playNote(self.channel, pitch, self.velocity, self.sustain)
			elif func != None and str(func).isalnum():
				eval("self." + str(func) + "()")
			c = getch()

		self.close()

class Helper:
	"""a helper class to parse command-line arguments and keymap files"""

	def __init__(self):
		parser = OptionParser()
		parser.add_option("-p", "--portname", dest="portName",
			default="deckyPy MIDI-Out",
			help="name to use for virtual MIDI port")
		parser.add_option("-s", "--showports", dest="showPorts",
			action="store_true", default=False,
			help="show available MIDI ports to choose from")
		parser.add_option("-f", "--file", dest="mapFile",
			help="use keymappings in MAP_FILE", metavar="MAP_FILE")
		parser.add_option("-c", "--channel", dest="channel",
			default=1,
			help="default midi channel (1-indexed)")
		parser.add_option("-v", "--verbose", dest="verbose",
			action="store_true", default=False,
			help="print every MIDI message sent")

		self.opts, self.args = parser.parse_args()

	def createController(self):
		print self.opts.portName
		print self.args
		opts = self.opts

		mout = self._getMout(opts.showPorts, opts.portName)
		print (opts.mapFile == None)
		return Controller(mout, channel=opts.channel-int(1), verbose=opts.verbose)

	def _getMout(self, showPorts, portName):
		mout = rtmidi.MidiOut()

		if showPorts:
			ports = mout.get_ports()
			print ("Available ports:")
			for i in range(len(ports)):
				print ("{0}: {1}".format(i, ports[i]))
			# keep trying until p is valid
			while True:
				p = raw_input("Enter port index (leave blank to use '" + portName + "'): ")
				try:
					if p == '' or 0 < int(p) < len(ports): break
				except:
					pass

			#assign the port
			if p != '':
				mout.open_port(int(p))
				print ("Using port '{}'".format(ports[int(p)]))
			else:
				mout.open_virtual_port(portName)
				print ("Using port '{}'".format(portName))
		else:
			mout.open_virtual_port(portName)
			print ("Using port '{}'".format(portName))

		return mout

def main():
	h = Helper()
	controller = h.createController()
	# mout.open_virtual_port("deckydeckydecky")
	# controller = Controller(mout, velocity=96)
	# controller.sustain = True
	# controller.monophonic = True
	controller.start()

main()