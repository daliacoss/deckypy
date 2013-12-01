"""
deckyPy - a simple virtual MIDI keyboard
by Deckman Coss (cosstropolis.com)
"""

import rtmidi, os, imp
from optparse import OptionParser
from getch import *

CWD = os.path.dirname(os.path.realpath(__file__))

#key constants
ESC = 27

#midi constants
DATA_BYTE = 127
NOTE_ON = 144
CHANNELS = 16
PITCHES_PER_OCTAVE = 12

class Controller:
	_activeMsgs = []

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
		"\t":"flush",
		"'":"toggleSustain",
		"\"":"toggleMonophonic",
		"`":"toggleVerbose",
		"[":"noteOffNewest",
		"]":"noteOffOldest",
		"\\":"flushChannel",
		"-":"octaveDown",
		"=":"octaveUp",
		"{":"velocityDown",
		"}":"velocityUp",
		"_":"channelDown",
		"+":"channelUp"
	}
	_defaultChannel = 0
	_defaultVelocity = 127
	_defaultOctave = 4
	_defaultVerbose = False
	_defaultSustain = False
	_defaultMonophonic = False

	def __init__(self,
		mout,
		pitchMap =_defaultPitchMap,
		funcMap=_defaultFuncMap,
		channel=_defaultChannel,
		velocity=_defaultVelocity,
		octave=_defaultOctave,
		verbose=_defaultVerbose,
		sustain=_defaultSustain,
		monophonic=_defaultMonophonic
	):
		self.mout = mout
		self.pitchMap = pitchMap 
		self.funcMap = funcMap
		self.channel = channel
		self.velocity = velocity
		self.octave = octave
		self.verbose = verbose
		self.sustain = sustain
		self.monophonic = monophonic

		print "Channel " + str(self.channel+1)
		print "Sustain " + ("ON" if self.sustain else "OFF")
		print "Monophony " + ("ON" if self.monophonic else "OFF")
		print "Octave " + str(self.octave)

	def playNote(self, channel, pitch, velocity=DATA_BYTE, sustain=False, monophonic=False):
		"""channel must be 0-indexed"""

		channel = max(0, min(channel,CHANNELS))
		pitch = max(0, min(pitch,DATA_BYTE))
		velocity = max(0, min(velocity,DATA_BYTE))

		if monophonic:
			self.flushChannel()
		msg = (NOTE_ON + channel, pitch, velocity)
		self.mout.send_message(msg)
		if not self._activeMsgs.count(msg[:2]):
			#only append the channel and pitch
			self._activeMsgs.append(msg[:2])
		if not sustain:
			self.stopNote(channel, pitch)

		if self.verbose:
			print ("note on: {0} {1}".format(msg[0],msg[1]))

	def stopNote(self, channel, pitch):
		msg = (NOTE_ON + channel, pitch, 0)
		self.mout.send_message(msg)

		#remove note from set of active messages
		try:
			#only look for the channel and pitch
			self._activeMsgs.remove(msg[:2])
			if self.verbose:
				print ("note off: {0} {1}".format(msg[0],msg[1]))
		except ValueError:
			pass

	def close(self):
		"""close the midi port (call at end of program)"""
		self.flush()
		self.mout.close_port()
		del self.mout

	def _flush(self, channel=None, i=0):
		
		if i<len(self._activeMsgs):
			msg = self._activeMsgs[i]
			if channel != None:
				print msg[0] - NOTE_ON, channel
				if msg[0] - NOTE_ON == channel:
					self.stopNote(msg[0]-NOTE_ON,msg[1])
				#keep searching through _activeMsgs for channel
				else:
					i += 1
				self._flush(channel, i)
			else:
				self.stopNote(msg[0]-NOTE_ON,msg[1])
				#no need to increment i if we're flushing all channels
				self._flush()

	def flush(self):
		self._flush()

	def flushChannel(self):
		self._flush(self.channel)

	def toggleSustain(self):
		self.sustain = not self.sustain
		print "Sustain " + ("ON" if self.sustain else "OFF")

	def toggleMonophonic(self):
		self.monophonic = not self.monophonic
		print "Monophony " + ("ON" if self.monophonic else "OFF")

	def toggleVerbose(self):
		self.verbose = not self.verbose
		print "Verbose " + ("ON" if self.verbose else "OFF")

	def octaveUp(self):
		#prevent octave from going above 10
		self.octave = min(self.octave+1, 10)
		print "Octave " + str(self.octave)

	def octaveDown(self):
		#prevent octave from going below 0
		self.octave = max(self.octave-1, 0)
		print "Octave " + str(self.octave)

	def velocityUp(self):
		self.velocity = min(self.velocity+16, DATA_BYTE)
		print "Velocity " + str(self.velocity)

	def velocityDown(self):
		self.velocity = max(self.velocity-16, 0)
		print "Velocity " + str(self.velocity)

	def _noteOffOne(self, direction, channel=None):
		"""if direction > 0, search from the front (oldest)"""

		#direction must be negative or positive
		if not direction: return

		numMsg = len(self._activeMsgs)

		if numMsg:
			#if no channel specified, grab the last (newest) or first (oldest)
			if channel == None:
				msg = self._activeMsgs[-1 if direction < 0 else 0]
			#else go through messages in specified direction
			else:
				a = 0 if direction > 0 else numMsg
				b = numMsg * (not a) #0 if a is numMsg
				for i in range(a, b, direction):
					msg = self._activeMsgs[i]
					if msg[0]-NOTE_ON == channel: break

			self.stopNote(msg[0]-NOTE_ON,msg[1])

	def noteOffOldestChannel(self):
		self._noteOffOne(1,self.channel)

	def noteOffNewestChannel(self):
		self._noteOffOne(-1,self.channel)

	def noteOffOldest(self, channel=None):
		self._noteOffOne(1)
		# if len(self._activeMsgs):
		# 	msg = self._activeMsgs[0]
		# 	self.stopNote(msg[0]-NOTE_ON,msg[1])

	def noteOffNewest(self):
		self._noteOffOne(-1)

	def channelUp(self):
		self.channel = min(self.channel+1, CHANNELS-1)
		print "Using channel " + str(self.channel+1)

	def channelDown(self):
		self.channel = max(self.channel-1, 0)
		print "Using channel " + str(self.channel+1)

	def start(self):
		print ("CONTROLLER IS READY")
		c = getch()
		while ord(c) != ESC:
			pitch = self.pitchMap.get(c)
			func = self.funcMap.get(c)
			if pitch != None:
				pitch += self.octave*PITCHES_PER_OCTAVE
				self.playNote(self.channel, pitch, self.velocity, self.sustain, self.monophonic)
			elif func != None and str(func).isalnum():
				eval("self." + str(func) + "()")
			c = getch()

		self.close()

class Helper:
	"""a helper class to parse command-line arguments and keymap files"""

	def __init__(self):
		print ("Initializing deckyPy...")

		parser = OptionParser()
		parser.add_option("-p", "--portname", dest="portName",
			default="deckyPy MIDI-Out",
			help="name to use for virtual MIDI port",
			metavar="PORT_NAME")
		parser.add_option("-s", "--showports", dest="showPorts",
			action="store_true", default=False,
			help="show available MIDI ports to choose from")
		parser.add_option("-f", "--file", dest="mapFile",
			help="use keymappings in MAP_FILE (will look in keymaps/)",
			metavar="MAP_FILE")
		parser.add_option("-c", "--channel", dest="channel",
			default=1,
			help="default midi channel (1-indexed)")
		parser.add_option("-o", "--octave", dest="octave",
			default=4,
			help="default octave")
		parser.add_option("-v", "--verbose", dest="verbose",
			action="store_true", default=False,
			help="print every MIDI message sent")
		parser.add_option('-u', "--sustain", dest="sustain",
			action="store_true", default=False,
			help="start in sustain mode")
		parser.add_option('-m', "--monophonic", dest="monophonic",
			action="store_true", default=False,
			help="start in monophony")

		self.opts, self.args = parser.parse_args()

	def createController(self):
		opts = self.opts
		mout = self._getMout(opts.showPorts, opts.portName)
		return self._controllerFromArgs(opts, mout)

	def loadKeyMap(self, fname, folder="keymaps"):
		"""attempt to return keymap from file, else return exception type"""
		try:
			km = imp.load_source('decky_keymap', os.path.join(CWD,folder,fname))
			return km.pitchMap, km.funcMap
		except (IOError, AttributeError) as e:
			return e
				
	def _controllerFromArgs(self, opts, mout):
		if opts.mapFile == None:
			return Controller(mout,
				channel=int(opts.channel)-1,
				octave=int(opts.octave),
				verbose=opts.verbose,
				sustain=opts.sustain,
				monophonic=opts.monophonic)
		else:
			keymap = self.loadKeyMap(opts.mapFile)
			if type(keymap) == IOError:
				print ("Error: could not find {}. Using defaults...".format(opts.mapFile))
				opts.mapFile = None
				return self._controllerFromArgs(opts, mout)
			elif type(keymap) == AttributeError:
				print ("Error: file improperly formatted. Using defaults...")
				opts.mapFile = None
				return self._controllerFromArgs(opts, mout)
			else:
				return Controller(mout,
					pitchMap=keymap[0],
					funcMap=keymap[1],
					channel=int(opts.channel)-1,
					octave=int(opts.octave),
					verbose=opts.verbose,
					sustain=opts.sustain,
					monophonic=opts.monophonic)

	def _getMout(self, showPorts, portName):
		mout = rtmidi.MidiOut()

		if showPorts:
			ports = mout.get_ports()
			print ("Available ports:")
			for i in range(len(ports)):
				print ("{0}: {1}".format(i, ports[i]))
			# keep asking until p is valid
			while True:
				p = raw_input("Enter port index (leave blank to use '" + portName + "'): ")
				try:
					if (p == '') or (0 <= int(p) < len(ports)): break
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
	controller.start()

main()
