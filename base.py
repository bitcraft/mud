from mudprop import MudProperty, MudPropType
import event as evt

global all_atoms

all_atoms = []

class IDServer(object):
	def __init__(self):
		self.high_id = 0

	def next(self):
		self.high_id += 1
		return self.high_id - 1

#===============================================================================
GlobalID = IDServer()
#===============================================================================

class MudAtom(evt.EventClient):
	"""
	this is a "bare bones" object.
	basically, this is the smallest class which can live in the mud.
	FullObjects and inventories should inherit from this.

	any attributes added to this class should be made properties.
	also, attribute creation can be frozen by calling "freeze".
	this will prevent new attributes from being created.
	"""

	def __init__(self,owner=None):
		super(MudAtom, self).__init__()

		# register ourselves with a new ID
		self.gameID = GlobalID.next()
		all_atoms.append(self)

		# used to determine who/what can modify our variables
		self.owner = owner
		self.prototype = None
		self.isDirty = True
		self.isDebug = True
		self.callbacks = {}

	def handle_event(self, event):
		mudfunc.get_handler(event.kind)
		func = MudFunctionDB[name]
		new.instancemethod(func,self,self.__class__)()

	def call_mudfunc_by_name(self, name):
		# emulate method calls
		func = MudFunctionDB[name]
		return new.instancemethod(func,self,self.__class__)

	def __getattribute__(self,name):
		"""
		customize attribute access:
			allow for mudproperties
		"""
		if name[:2] == '__':
			return object.__getattribute__(self,name)

		try:
			mydict = object.__getattribute__(self,"__dict__")
			if type(mydict[name]) == MudPropType:
				return mydict[name].value
			else:
				myrepr = object.__getattribute__(self,"__repr__")
				print "bug!: object attribute not a mud property:",myrepr(), name
				return mydict[name]
		except KeyError:
			try:
				dispatch = object.__getattribute__(self,"call_mudfunc_by_name")
				return dispatch(name)
			except:
				return object.__getattribute__(self,name)

	def __setattr__(self,name,value):
		"""
		customize attribute access:
			allow for mudproperties
		"""
		if name[:2] == "__":
			object.__setattr__(self,name,value)
			return

		mydict = object.__getattribute__(self,"__dict__")

		if mydict.has_key(name):
			if type(mydict[name]) == MudPropType:
				mydict[name].value = value
			else:
				print "bug! caught a attribute that is not a property!",self,name
				p  = MudProperty(owner=self,group=[self])
				p.value = value
				self.__dict__[name] = p
		else:
			p  = MudProperty(owner=self,group=[self])
			p.value = value
			self.__dict__[name] = p

		#~ if name == "_index" or name == "_size":
			#~ return
		#~ if name!="isDirty":
			#~ object.__setattr__(self,"isDirty",True)

	def _get_classes(self, obj):
		"""
		this function is not placed very well,
		but is used by the Room class and Describe MudFunc
		"""
		classes=[obj.__class__]
		all_classes=[]
		while classes:
			aclass=classes.pop(0)
			classes=classes + list(aclass.__bases__)
			all_classes.append(aclass)
		all_classes.reverse()
		return all_classes

#this is lame that this import is stuck here
#import mudfunc
#from mudfunc2 import MudFunctionDB

# this Metaclass doesn't do anything...yet
class MudObjectFactory(type):
	def __init__(cls, name,bases,dict):
		super(MudObjectFactory, cls).__init__(name,bases,dict)

	def __getattribute__(self,name):
		return super(MudObjectFactory,self).__getattribute__(name)

class MudObject(MudAtom):
	"""
	this class is used of anything that can be manipulated in the game.
	think of intnaces of this as being "real".  players, npcs, etc all
	maniplulate these.
	"""

	def __init__(self,name=None,owner=None):
		super(MudObject,self).__init__(owner=self)

		self.name = name
		self.shortDescription = ""
		self.longDescription = ""
		self.keywords = []			# used to help players ID an object
		self.isDestroyed = False	# if true, events will be ignored
		self.isPermanent = True		# will not be automatically cleaned up
		self.isUnknown = False		# will default to not being indentified
		self.isHidden = False		# will not be listed when a room is looked at
		self.control = None			# if set, events from the value will be listened to
		self.location = None		# what object contains this
		self.deathEmote = "is destroyed"

		super(MudObject,self).Bind(evt.EVT_MESSAGE, self.on_message)
		#super(MudObject,self).Bind(, self.on_message)
		#super(MudObject,self).Bind(EVT_LOOK, self.on_look)

	def sendEvent(self, event, sendTo=None):
		if self.isDestroyed:
			if self.control:
				msg = evt.TextMessage("you are dead")
				evt.EventClient.sendEvent(self, msg, self.control)
		else:
			if sendTo == None:
				if self.location == None:
					return
				sendTo = self.location
			evt.EventClient.sendEvent(self, event, sendTo)

	def on_message(self,event):
		if self.control!=None:
			event.sendTo=self.control
			MudObject.evtHandler.que(event)

	def on_look(self, event):
		response=evt.TextMessage(self.shortDescription)
		self.sendEvent(response, event.viewer)

	# bug: player still is playable after being killed, which causes bug here
	# bug: when things are destroyed...we need to kill its children as well!
	def destroy(self):
		if self.isDestroyed == True:
			return

		if self.location != None:
			self.location.remove(self)

		if self.control != None:
			self.control.unlink()

		for key,value in self.__dict__.items():
			value = None

		# bug: obscure, but only way around the fact that I don't understand
		# python garbage collection.  maybe in future, objects will *really*
		# be destroyed. until now, just mark 'em dead.  :)
		self.isDestroyed = True
		self.isPermanent = False

	def __repr__(self):
		repr = ""
		try:
			gameID = object.__getattribute__(self,"gameID")
			name = object.__getattribute__(self,"name")
			repr = "<%s: (%s) [%s]" % (type(self).__name__,name,gameID)
		except:
			return object.__repr__(self)

		try:
			x = object.__getattribute__(self,"__len__")()
			repr += " L:%d" %  x
		except AttributeError:
			pass

		repr += ">"
		return repr
