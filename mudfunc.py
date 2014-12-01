import mudclasses2 as mc
import event as evt

"""
all funtions should include a "check", and "realize"
function for proper execution in a scripted environment.

makes feedback to scripts and the user much easier
"""

MudFunctionDB = {}

class MudFunction(mc.MudAtom):
	def __init__(self,cmd=None,owner=None):
		super(MudFunction, self).__init__(owner=self)
		if cmd == None:
			print "print cannot create function, no name!"
			return
		self.cmd = cmd
		self._callers = []
		MudFunctionDB[self.cmd] = self

	def checkPermission(self,caller):
		return True

		if caller in self._callers:
			return True
		else:
			return False

	"""
	here a func event will be sent out, and the event handler will dispatch it.
	if the handler gets a veto, then we need to cancel the func.

	not implimented
	"""
	def __call__(self,caller,*arg,**kwarg):
		print arg, kwarg
		if self.checkPermission(caller):
			#self.sendEvent(evt.MudFuncEvent(self,*arg,**kwarg))
			self.realize(caller,*arg,**kwarg)
		else:
			return False

class MudFunctionFactory(type):
	def __new__(cls,*arg,**kwarg):
		new_class = super(MudFunctionFactory, cls).__new__(cls,*arg,**kwarg)
		print new_class
		print arg, kwarg
		return new_class

	def __init__(cls,name,bases,dict):
		super(MudFunctionFactory, cls).__init__(name,bases,dict)
		me = cls(name.lower())
		# Make a new event
		print cls
		event_name = "EVT_" + name.upper()
		cls.event = evt.GetNewEventID()

"""
we should code two functions for each mud command:
the action, and the handler

we can have default handlers.  the individual objects has decide to overload.
when a mudfunc is called, it checked the victim to see if it is handled,
if it isn't, then we call our default handler

this can make spells pretty easy to impliment!
"""

# Make some very basic commands
class Look(MudFunction):
	__metaclass__ = MudFunctionFactory

	def check(self,caller,victim):
		return True

	def realize(self,caller,victim):
		print self.event
		if victim.isUnknown:
			if not self.isIdentified(victim):
				victim = UnknownMudObject()

		# this basically says:
		# hey, victim, call my callback as if it were attached to you.
		self.sendEvent(evt.MudFuncEvent(caller, victim, self))

	def callback(self):
		print "looks at you"

class Describe(MudFunction):
	__metaclass__ = MudFunctionFactory

	def do(self,caller,thing):
		r="%s's variables:\n" % thing
		keys=thing.__dict__.keys()
		keys.sort()
		for key in keys:
			if type(thing.__dict__[key])==DictType:
				text="  %s:\n" % key
				for key2, value2 in thing.__dict__[key].items():
					text+="    %s: %s\n" % (key2,value2)
			else:
				text="  %s: %s\n" % (key,thing.__dict__[key])
			r+=text

		r+="\n%s's methods:\n" % thing
		# Inheritance says we have to look in class and
		# base classes; order is not important.
		# returns all methods, not just of TextControl class
		classes=[thing.__class__]
		all_methods=[]

		for aclass in self._get_classes(thing):
			if aclass.__bases__:
				r+="  class: %s\n" % aclass
				my_methods=[]
				for m in dir(aclass):
					if m[:1]!="_":
						if m not in all_methods:
							my_methods.append(m)
							all_methods.append(m)
				if my_methods:
					my_methods.sort()
					r+=PrettyOutput().columnize(my_methods,indent=4)

		self.sendEvent(evt.TextMessage(r), caller)

class Say(MudFunction):
	__metaclass__ = MudFunctionFactory

	def do(self,caller,what=None,sendTo=None):
		print caller, "says",  what

class Place(MudFunction):
	__metaclass__ = MudFunctionFactory

	def do(self,caller,what,where):
		old_location = what.location
		what.location.remove(what)
		if not where.append(what):
			old_location.append(what)

class Take(MudFunction):
	__metaclass__ = MudFunctionFactory

	def do(self,caller,target):
		for obj in target:
			old_location=obj.location
			obj.location.remove(obj)
			try:
				caller.append(obj)
			except:
				old_location.append(obj)

class Drop(MudFunction):
	__metaclass__ = MudFunctionFactory

	def do(self,caller,target):
		for obj in target:
			caller.remove(obj)
			caller.location.append(obj)

class Has(MudFunction):
	__metaclass__ = MudFunctionFactory

	def do(self,caller,where,what):
		if what in where:
			r = "True"
		else:
			r = "False"

		self.sendEvent(evt.TextMessage(r), caller)
