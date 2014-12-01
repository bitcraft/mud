#!/usr/bin/python

"""
goals:
	create a metaclass that gives objects the abilty to send signals
	when the object changes state

	an eventmanager singleton class will handle events:
		when an objects state changes, the object only has to send one
		message to an event handler that will notify others on its behalf

		or

		each object has a dictionary of connections
		each one has a key of each interesting attribute
		if it is called or changed, then the callback is done at the end of change

   * a reasonable limitation:
	* objects cannot add their own attributes
"""

from __future__ import nested_scopes
import weakref

# when "frozen", no new attributes can be added!
class Freezable(object):
	def __init__(self):
		object.__setattr__(self, "_frozen", False)
		super(Freezable, self).__init__()

	def set_frozen(self, frozen):
		self._properties = tuple(self.__dict__.keys())
		object.__setattr__(self, "_frozen", frozen)

	def get_frozen(self):
		return self._frozen
	frozen = property(get_frozen, set_frozen)

	# extend __setattr__ to use descriptors...
	def __setattr__(self, key, value):
		if self.frozen:
			if key not in self._properties:
				raise AttributeError("Frozen Object: %s" % self)
		try:
			obj = object.__getattribute__(self, key)
		except AttributeError:
			obj = None

		if obj:
			if hasattr(obj, "__set__"):
				obj.__set__(key, value)
		else:
			object.__setattr__(self, key, value)

# use call backs to manage state change
# should it make autoproperties???
class MetaSignals(type):
	def __init__(cls, name, bases, d):
		super(MetaSignals, cls).__init__(name, bases, d)
		print "meta sig: ", d
		if 'signals' in d:
			pass

# not sure yet...
class MetaMudObject(MetaSignals):
	def __init__(cls, name, bases, d):
		#print "meta mud: ", d
		super(MetaMudObject, cls).__init__(name, bases, d)

class SignalsClient(object):
	def __init__(self):
		super(SignalsClient, self).__init__(self)
		self.connections = {}

	def register(self, observer, name, callback):
		self.connections[name] = callback

	def deregister(self, observer, name):
		del self.connections[name]

	def observe(self, subject, name, callback):
		subject.register(self, name, callback)

	def modified(self, var=None):
		if var:
			self.connections[var]()
		else:
			for callback in self.connections.values():
				callback()

class SignalsClient2(object):
	def __init__(self):
		super(SignalsClient2, self).__init__()
		self.observers = {}

	def register(self, observer, callback):
		self.observers[observer] = callback

	def deregister(self, observer, name):
		del self.observers[name]

	def observe(self, subject, callback):
		subject.register(self, callback)

	def modified(self, var=None):
		for callback in self.observers.values():
			callback()

class Observable(SignalsClient2):
	__slots__ = ["val", "name"]

	def __init__(self, initval=None, name='var'):
		super(Observable, self).__init__()
		self.val = initval
		self.name = name

	def __str__(self):
		return str(self.val)

	def __get__(self, obj, objtype):
		return self.val

	def __set__(self, obj, val):
		self.val = val
		self.modified()

	def __delete__(self):
		raise AttributeError


class MudObject(Freezable, SignalsClient2):
	__metaclass__ = MetaMudObject

class Chatty(MudObject):
	signals = ['id']
	x = Observable(12)

	def __init__(self):
		super(Chatty, self).__init__()
		self.id = None
		self.y = Observable(12)
		self.frozen = True

	def blurt(self):
		print "something happened"

emitter = Chatty()
listener = Chatty()

# this requires that objects call modified() when finished
#listener.observe(emitter, "id", listener.blurt)

#this does not
listener.observe(emitter.y, listener.blurt)

emitter.y = 99
emitter.y = 97

emitter.id = 99
#emitter.modified()



#emitter.testing  = "123"