deckyPy
=======

deckyPy is a simple, terminal-based virtual MIDI keyboard using the RtMidi library. 

because the program reads input with a simple getc implementation, sustained key presses are not supported. to compensate, there are a variety of sustain "pedals" that can be mapped to the keyboard (see "custom keymaps" below).

installation
------------
1. download and install rtmidi (https://pypi.python.org/pypi/python-rtmidi)
2. install a virtual MIDI driver if you do not already have one. (osx 10.5+ comes with one built-in; for windows i recommend LoopBe1 or MIDI-OX.)
3. run decky.py using python 2.6 or 2.7

usage
-----
`python decky.py [options]`  
(wait for "CONTROLLER IS READY" status message before playing)  
**note:** if your system does not support virtual MIDI ports (i.e., if you're on windows), you must run deckyPy using the --showports/-s option.

use -h flag for list of options  
refer to keymaps/sample.py for the built-in keymap

custom keymaps
--------------
a keymap file must contain two python dictionaries: pitchMap and funcMap. when a key is pressed at runtime, deckyPy will first look in pitchMap for a note value mapped to that key. if it succeeds, it will play that note relative to the current octave. if it fails, it will then look in funcMap for a function mapped to the key.

the default pitchMap assumes an american qwerty layout, and treats the "z" and "q" rows as white keys and the "a" and "1" rows as black keys. **note:** key values are case-sensitive.

here is a list of recognized funcMap values:

**"flush":** silence every active note across all channels.  
**"toggleSustain":** toggle sustain. when off, notes will decay as soon as they are played. when on, notes will sustain continuously until one of the *noteOff* or *flush* functions are called.  
**"toggleMonophonic":** toggle monophony. when on, *flushChannel* (see below) will be called for every note played.  
**"toggleVerbose":** toggle verbose. when on, a debug for every midi message will be printed to stdout.  
**"noteOffNewest":** silence the most recently played active note across all channels.  
**"noteOffOldest":** silence the least recently played active note across all channels. (this is useful for melodic lines)  
**"flushChannel":** silence every active note on the current channel.  
**"octaveDown":** decrease the controller's current octave.  
**"octaveUp":** increase the controller's current octave.  
**"velocityDown":** decrease the controller's current velocity.  
**"velocityUp":** increase the controller's current velocity.
**"channelDown":** decrease the controller's current channel.
**"channelUp:** increase the controller's current channel.
