# events.  basically, i want to make sure that objects do not directly
# mangle eachother's variables, and must go through the approipriate methods
# to do stuff.  basically, the event system will package a message into an easy
# to use thingy that makes requesting information from a object easy
# also, if one object needs to change variables, (such as attacks) then it can
# use this!

# the veto system.  basically, when an event is fired, then it sends a
# to everyone interested.  by default this is any object in the room, including
# the sender.  other objects can be interested if they attach them selves as
# listeners.
# each interested party has a chance to veto the event.  if veto'd, then the
# event will not complete.

"""
how will this tie into the observable pattern?

"""

import random, re


def shortenText(text):
    text = re.sub(r'[aeiou]', '', text)
    text = re.sub(r'ck', 'k', text)
    text = re.sub(r'\t', ' ', text)
    return text


class EventHandler():
    currentEventID = 0
    currentState = 0

    def __init__(self, name="none"):
        self._que = []
        self.objDB = []
        self.name = name

    def que(self, event, priority=False):
        if priority:
            return

        self._que.insert(0, event)

    def get_names(self, obj):
        names = []
        classes = [obj.__class__]
        while classes:
            aclass = classes.pop(0)
            if aclass.__bases__:
                classes = classes + list(aclass.__bases__)
            names = names + dir(aclass)
        return names

    def handle(self, event):
        # print shortenText(event.__str__())

        if event.kind == EVT_UPDATE:
            self.currentState += 1
            print EventHandler, ": NEW STATE #", self.currentState

        elif event.kind == EVT_MUDFUNC:
            print event
            func_name = event.callback.__class__.__name__.lower()
            for name in self.get_names(event.sendTo):
                if name[:3] == 'on_':
                    if name[3:] == func_name:
                        event.callback
                        print "match"

        if event.kind in event.sendTo._bind_dict.keys():
            event.sendTo._bind_dict[event.kind](event)
        else:
            # the object doesn't know how to handle this type
            event.sendTo.handle_event(event)

    def deque(self):
        while len(self._que) > 0:
            event = self._que.pop()
            self.handle(event)

    def tick(self):
        for thing in self.objDB:
            remove = []
            if thing.isDestroyed:
                remove.append(thing)
            else:
                try:
                    thing.aiHook()
                except:
                    pass

            for thing in remove:
                self.objDB.remove(thing)

        self.deque()

    def add(self, thing):
        self.objDB.append(thing)


class EventClient(object):
    evtHandler = EventHandler("all clients")

    def __init__(self):
        if not hasattr(self, "_bind_dict"):
            self._bind_dict = {}

    def Bind(self, event, function):
        if not hasattr(self, "_bind_dict"):
            self._bind_dict = {}
        bd = self._bind_dict
        bd[event] = function

    def Unbind(self, event):
        if not hasattr(self, "_bind_dict"):
            return

        self._bind_dict.remove(event)

    def sendEventRaw(self, sender, sendTo, event_type):
        sendTo.evtHandler.que(Event(sender, sendTo, event_type))

    def sendEvent(self, event, sendTo=None):
        event.sender = self

        if event.sendTo == None:
            event.sendTo = sendTo

        if event.sendTo != None:
            event.sendTo.evtHandler.que(event)


class Event(object):
    def __init__(self, sender=None, sendTo=None, event_type=None):
        self.kind = event_type
        self.sender = sender
        self.sendTo = sendTo
        self.veto = False
        self.isCopy = False

    def __str__(self):
        r = "Event:"
        for key, value in self.__dict__.items():
            text = "  %s: %s\n" % (key, value)
            r += text
        return "<condensed>" + shortenText(r)

    def copy(self):
        """ this is a very simple way to copy events.  expanded later? """
        new = type(self)()
        new.__dict__ = self.__dict__.copy()
        new.isCopy = True
        return new

    def veto(self, veto=True):
        self.veto = veto

    # alias for calling the instance, not implimented
    def realize(self):
        self.__call__()

    def __call__(self):
        pass


class UpdateEvent(Event):
    def __init__(self, sender, sendTo):
        Event.__init__(self, sender, sendTo)
        event.kind = EVT_UPDATE


# bug: ObjectEvent is protocol for custom methods (ie: shake), incomplete
class ObjectEvent(Event):
    def __init__(self, sender, sendTo):
        Event.__init__(self, sender, sendTo)


class MudFuncEvent(Event):
    def __init__(self, sender, target, callback):
        super(MudFuncEvent, self).__init__(sender, target)
        self.kind = EVT_MUDFUNC
        self.callback = callback


class AttackEvent(Event):
    def __init__(self, sender, target, weapon, dp):
        Event.__init__(self, sender, target)
        self.kind = EVT_ATTACK
        self.dp = dp
        self.weapon = weapon


class LookEvent(Event):
    def __init__(self, viewer, thing):
        Event.__init__(self, viewer, thing)
        self.kind = EVT_LOOK
        self.viewer = viewer
        self.thing = thing


class SetVar(Event):
    def __init__(self, caller, thing, name, value):
        Event.__init__(self, caller)
        self._varThing = thing
        self._varName = name
        self._varValue = value

    def __call__(self):
        Event.__call__(self)
        self._varThing.__dict__[self._varName] = self._varValue


class CallFunc(Event):
    def __init__(self, caller, thing, func, args):
        Event.__init__(self, caller)
        self._funcThing = thing
        self._funcName = func
        self._funcArgs = args

    def __call__(self):
        Event.__call__(self)
        try:
            return getattr(self._funcThing, self._funcName)
        except:
            print "bug: cannot call func"


class DestroyThing(Event):
    def __init__(self, caller, thing):
        Event.__init__(self, caller)
        self._destroyThing = thing

    def __call__(self):
        Event.__call__(self)
        if self._destroyThing.owner != None:
            self._destroyThing.owner.remove(self.thing)

        if self._destroyThing in objDB:
            pass


def GetNewEventID():
    EventHandler.currentEventID = EventHandler.currentEventID + 1
    return EventHandler.currentEventID


class Message(Event):
    def __init__(self, *arg, **kwarg):
        Event.__init__(self, *arg, **kwarg)
        self.kind = EVT_MESSAGE


class TextMessage(Message):
    def __init__(self, text=None, *arg, **kwarg):
        Message.__init__(self, *arg, **kwarg)
        self.text = text

    def __str__(self):
        return self.text


class SystemMessage(TextMessage):
    def __init__(self, text, sender="hermes", sendTo=None):
        TextMessage.__init__(self, text, sender, sendTo)


# emotes are becomming generic ways objects express themselves. this is ok,
# but we need to make more generic, and less ties to English.action
class Emote(TextMessage):
    def __init__(self, sender=None, grammar=None, text=None, action=None):

        # ## self.emote(action=english.Action("say",text))   ###
        ### self.emote(action=english.Action("take",thing)) ###

        TextMessage.__init__(self, sender, text)
        self.emoteText = text
        self.action = action
        self._dirty = True

    def _cacheText(self):
        from english import Action

        if self.emoteText == None:
            action = self.action
            action.sub = self.sender
            action.addressee = self.sendTo

            self.text = "%s" % action

        else:
            if self.sender == self.sendTo:
                sender = "you"
            else:
                sender = "%s" % (self.sender)

            self.text = "%s %s" % (sender, self.emoteText)

        self._dirty = False

    def __str__(self):
        if self._dirty:
            self._cacheText()

        return TextMessage.__str__(self)

    def __setattr__(self, name, value):
        if name != "_dirty":
            object.__setattr__(self, name, value)
            object.__setattr__(self, "_dirty", True)


# bug: the tell system is all fucked up.
class Tell(Emote):
    def __init__(self, sender=None, text=""):
        Emote.__init__(self, sender, text)


class EventChannel(EventClient):
    """
    A broadcast channel for events.

    Members and be added and removed.  Any message sent here will be resent
    to all its members.  Copies are made of each event.  (I don't remember why)
    Interestingly enough, any game event can be relayed (try to attck this!)
    """

    def __init__(self, name, echo=True):
        super(EventChannel, self).__init__()
        super(EventChannel, self).Bind(EVT_MESSAGE, self.on_message)
        self.echo = echo
        self.name = name
        self.members = []

    def addMember(self, thing):
        self.members.append(thing)

    def removeMember(self, thing):
        self.members.remove(thing)

    def on_message(self, event):
        self._broadcast(event)

    def sendEvent(self, event):
        event.sendTo.evtHandler.que(event)

    def _broadcast(self, event):
        for talker in self.members:
            if talker != event.sender:
                new = event.copy()
                new.sendTo = talker
                self.sendEvent(new)

        if self.echo:
            new = event.copy()
            new.sendTo = event.sender
            self.sendEvent(new)


class TalkChannel(EventChannel):
    """
    Accepts TextMessages.  Typically used in a room, or topic channel.

    bug: preamble/postamble on emotes doesn't work
    bug: whenever sendTo is changed, then the grammar is recached, bad?

    #event.text=self.preamble+event.text+self.postamble
    """

    def __init__(self, name, echo=True, preamble="", postamble=""):
        super(TalkChannel, self).__init__(name, echo)
        self.preamble = preamble
        self.postamble = preamble


EVT_LOOK = GetNewEventID()
EVT_ATTACK = GetNewEventID()
EVT_MESSAGE = GetNewEventID()
EVT_UPDATE = GetNewEventID()
EVT_MUDFUNC = GetNewEventID()
