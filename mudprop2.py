import inspect
from types import *

"""
mudprops seem to work, the unittest is ok, but i think that i would like to
rework them, so that all mudatoms can use the protocol.

then, we could have objects that be be read and modified, just ust their
attributes.
"""

class PermissionError(Exception):
	pass

class SignalsClient(object):
	"""
	each new instance of this should register istelf with the game's
	event handler, or zones, or whatever, maybe its owner's?
	"""
	def __init__(self):
		super(SignalsClient2, self).__init__()
		self.observers = {}

	def register(self, observer, callback):
		# bug: do don't check the type for the callback here
		self.observers[observer] = callback

	def deregister(self, observer, name):
		del self.observers[name]

	def observe(self, subject, callback):
		subject.register(self, callback)

	def modified(self, var=None):
		for callback in self.observers.values():
			callback()

class Observable(SignalsClient):
	"""
	I'm pretty sure only numbers or strings are acceptable for this class.
	"""
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

class PermissionHandler(object):
	# this is a handy way to override security.  :)
	def changeValue(self,victim,name,value):
		victim.__setattr__(name,value)

	def getValue(self,victim,name):
		return self.__getattribute__(victim,name)

	def get_caller(self, frame):
		"""
		this is a very basic way of finding the caller that changes a attribute
		simply get the last call in the stack and find the self variable.
		obviously, this is not robust.
		"""
		try:
			caller = frame.f_back.f_locals['self']
		finally:
			# some thing about garbage collection
			del frame
		return caller

	def get_permission(self,caller):
		"""
		we have to be careful not to directly access any of our own data to
		avoid a recursive loop of calls
		to __getattribute__
		"""
		# we only try here, because the owner may not be set yet...  (may be a bug)
		try:
			owner = object.__getattribute__(self, "owner")
			value = object.__getattribute__(self, "value")
			me = object.__getattribute__(self, "me")
			r = object.__getattribute__(self, "r")
			w = object.__getattribute__(self, "w")
			x = object.__getattribute__(self, "x")

			# we need a copy of group (not ref) here to avoid recursive calls
			# to check permission
			group = []
			group[:] = list(object.__getattribute__(self, "group"))
		except AttributeError:
			return (True, True, True)

		if caller is me:
			return (True, True, x)

		if caller is owner:
			return (True, True, x)

		for obj in group:
			if caller is obj:
				return (True, True, x)

		return (r, w, x)

class MudProperty(PermissionHandler):
	def __init__(self,owner=None,group=[],value=None):
		group.append(self)
		attributes = {
			'owner':owner,
			'group':group,
			'value':value,
			'me':self,
			'r':True,
			'w':False,
			'x':True }
		self.__dict__.update(attributes)

	def permstr(self):
		perm = ''
		for att in self.__dict__.keys():
			if self.__dict__[att]:
				perm += att
			else:
				perm += '-'
		return perm

	def __eq__(self,other):
		caller = super(MudProperty, self).get_caller(inspect.currentframe())
		r, w, x = super(MudProperty, self).get_permission(caller)

		if r == False:
			raise PermissionError("CallerCannotRead", caller, self.__repr__())

		value = object.__getattribute__(self, "value")

		if value == None:
			if other == None:
				return False
			return False
		else:
			if type(value) == StringType:
				return value.__eq__(other)
			#our best way to try... (this way is cheap)
			return other.__eq__(self)

		return NotImplemented

	def __str__(self):
		caller = super(MudProperty, self).get_caller(inspect.currentframe())
		r, w, x = super(MudProperty, self).get_permission(caller)

		if r == False:
			raise PermissionError("CallerCannotRead", caller, self.__repr__())

		return "^%s" % self.value.__str__()

	def __getattribute__(self,name):
		caller = super(MudProperty, self).get_caller(inspect.currentframe())
		r, w, x = super(MudProperty, self).get_permission(caller)

		if r == False:
			raise PermissionError("CallerCannotRead", caller, self.__repr__())

		if name[:2] == '__':
			return object.__getattribute__(self,name)

		#print "get prop:",object.__getattribute__(self,"__repr__")(),name

		if name in ('r','w','x','value'):
			return object.__getattribute__(self,name)
		else:
			value = object.__getattribute__(self,'value')
			if name in dir(value):
				return object.__getattribute__(value,name)
			raise AttributeError, name

	def __setattr__(self,name,value):
		caller = super(MudProperty, self).get_caller(inspect.currentframe())
		r, w, x = super(MudProperty, self).get_permission(caller)

		if w == False:
			raise PermissionError("CallerCannotWrite")

		if name in ('r','w','x','value'):
			object.__setattr__(self,name,value)
		#~ else:
			#~ # test to see if the value is an instance of something else
			#~ try:
				#~ object.__setattr__(self,name,value)
			#~ except AttributeError:
					#~ raise AttributeError, name

MudPropType = type(MudProperty())
