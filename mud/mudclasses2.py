"""
todo:
	que:
		evthandler should be used when ever two objects interact

		*everything is a MUDObject
		challanges: can i put this in you?

	about grammar....
	# bug: grammar articles take up too much memory
	# bug: objects are not destroyed when supposed to
	# bug: each instance in an objects heiarcy gets a gameID, do we want this?

	security:
		works on object attributes *only*
		should be a way to make it apply to attribute and function calls (metaclass?)

"""

import sys, new, pprint
from types import StringType, TupleType, DictType, IntType, MethodType

import english
import event as evt
import message as msg
from mudprop import MudProperty, MudPropType


class PermissionError(Exception):
    pass


class MudAtom(evt.EventClient):
    """
    this is a "bare bones" object.
    basically, this is the smallest class which can live in the mud.
    FullObjects and inventories should inherit from this.
    """
    population = []

    def __init__(self, owner=None):
        evt.EventClient.__init__(self)

        # ~ if self in MudAtom.population:
        #~ self.gameID=MudAtom.population.index(self)
        #~ else:
        #~ self.gameID=len(MudAtom.population)
        #~ MudAtom.population.append(self)
        self.gameID = len(MudAtom.population)
        MudAtom.population.append(self)

        self.owner = owner
        self.isDirty = True
        self.isDebug = True
        self.callbacks = {}

    def handle_event(self, event):
        mudfunc.get_handler(event.kind)
        func = MudFunctionDB[name]
        new.instancemethod(func, self, self.__class__)()

    def call_mudfunc_by_name(self, name):
        func = MudFunctionDB[name]
        return new.instancemethod(func, self, self.__class__)

    def __getattribute__(self, name):
        if name[:2] == '__':
            return object.__getattribute__(self, name)

        try:
            mydict = object.__getattribute__(self, "__dict__")
            if type(mydict[name]) == MudPropType:
                return mydict[name].value
            else:
                myrepr = object.__getattribute__(self, "__repr__")
                print "bug!: object attribute not a mud property:", myrepr(), name
                return mydict[name]
        except KeyError:
            try:
                dispatch = object.__getattribute__(self, "call_mudfunc_by_name")
                return dispatch(name)
            except:
                return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name[:2] == "__":
            object.__setattr__(self, name, value)
            return

        mydict = object.__getattribute__(self, "__dict__")

        if mydict.has_key(name):
            if type(mydict[name]) == MudPropType:
                mydict[name].value = value
            else:
                print "bug! caught a attribute that is not a property!", self, name
                p = MudProperty(owner=self, group=[self])
                p.value = value
                self.__dict__[name] = p
        else:
            p = MudProperty(owner=self, group=[self])
            p.value = value
            self.__dict__[name] = p

            # ~ if name == "_index" or name == "_size":
        #~ return
        #~ if name!="isDirty":
        #~ object.__setattr__(self,"isDirty",True)

    def _get_classes(self, obj):
        """
        this function is not placed very well, but is used by the Room class and Describe MudFunc
        """
        classes = [obj.__class__]
        all_classes = []
        while classes:
            aclass = classes.pop(0)
            classes = classes + list(aclass.__bases__)
            all_classes.append(aclass)
        all_classes.reverse()
        return all_classes

# this is lame that this import is stuck here
#import mudfunc
from mudfunc import MudFunctionDB

# this Metaclass doesn't do anything...yet
class MudObjectFactory(type):
    def __init__(cls, name, bases, dict):
        super(MudObjectFactory, cls).__init__(name, bases, dict)

    def __getattribute__(self, name):
        return super(MudObjectFactory, self).__getattribute__(name)


class MudObject(MudAtom):
    """
    this class is used of anything that can be manipulated in the game.
    think of intnaces of this as being "real".  players, npcs, etc all
    maniplulate these.
    """

    def __init__(self, name=None, owner=None):
        super(MudObject, self).__init__(owner=self)

        self.name = name
        self.shortDescription = ""
        self.longDescription = ""
        self.keywords = []  # used to help players ID an object
        self.isDestroyed = False  # if true, events will be ignored
        self.isPermanent = True  # will not be automatically cleaned up
        self.isUnknown = False  # will default to not being indentified
        self.isHidden = False  # will not be listed when a room is looked at
        self.control = None  # if set, events from the value will be listened to
        self.location = None  # what object contains this
        self.deathEmote = "is destroyed"

        super(MudObject, self).Bind(evt.EVT_MESSAGE, self.on_message)

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

    def on_message(self, event):
        if self.control != None:
            event.sendTo = self.control
            MudObject.evtHandler.que(event)

    def on_look(self, event):
        response = evt.TextMessage(self.shortDescription)
        self.sendEvent(response, event.viewer)

    # bug: cannot send emotes to things, only rooms by default
    def emote(self, *arg, **kwarg):
        if self.location != None:
            message = evt.Emote(*arg, **kwarg)
            self.sendEvent(message, self.location.channel)

    # bug: player still is playable after being killed, which causes bug here
    # bug: when things are destroyed...we need to kill its children as well!
    def destroy(self):
        if self.isDestroyed == True:
            return

        if self.location != None:
            self.location.remove(self)

        if self.control != None:
            self.control.unlink()

        for key, value in self.__dict__.items():
            value = None

        # bug: obscure, but only way around the fact that I don't understand
        # python garbage collection.  maybe in future, objects will *really*
        # be destroyed. until now, just mark 'em dead.  :)
        self.isDestroyed = True
        self.isPermanent = False

        MudObject.population.remove(self)

    def __repr__(self):
        repr = ""
        try:
            gameID = object.__getattribute__(self, "gameID")
            name = object.__getattribute__(self, "name")
            repr = "<%s: (%s) [%s]" % (type(self).__name__, name, gameID)
        except:
            return object.__repr__(self)

        try:
            x = object.__getattribute__(self, "__len__")()
            repr += " L:%d" % x
        except AttributeError:
            pass

        repr += ">"
        return repr


class MudList(MudAtom, list):
    def __init__(self, owner=None, maxSize=None):
        super(MudList, self).__init__(owner)
        self.maxSize = maxSize

    def append(self, obj):
        # cannot add self to self
        if obj is self:
            return False

        # check to make sure we don't go over our size limit (if any)
        if self.maxSize != None:
            if ((len(self) + 1) > int(self.maxSize)):
                return False

        # make super do the hard work
        super(MudList, self).append(obj)

        # set the objects location to self
        obj.location = self

        return True

    def remove(self, obj):
        try:
            super(MudList, self).remove(obj)
            return True
        except:
            return False


class MudInventory(MudList):
    """
    A MudInventory is used with Mobiles.
    It differs from normal lists:
        when it contains other lists (or list-like objects), their lenght is added to this one
        when this is iterated, the other lists it contains are iterated with this one

    the idea here is that this is implimeted and attached to a mobile.
    if a mobile has another container object in its primary inventory, then this inventory
        magically merge them together, so it is transparent, and they seem like one
    """

    def __init__(self):
        MudList.__init__(self)
        self.real_index = -1
        self.virtual_index = -1
        self.len = 0
        self.iter_list = False
        self.iter_list_len = None

    def __len__(self):
        x = 0
        while True:
            iter = self.__iter__()
            try:
                iter.next()
                x += 1
            except StopIteration:
                break
        return x

    #~ return self.len
    #~ x = 0
    #~ for obj in self:
    #~ x += 1
    #~ return x

    def append(self, x):
        self.len += 1
        if isinstance(x, MudList):
            self.len += len(x)
        return super(MudInventory, self).append(x)

    def remove(self, x):
        self.len -= 1
        if isinstance(x, MudList):
            self.len -= len(x)
        return super(MudInventory, self).remove(x)

    def __contains__(self, x):
        if super(MudInventory, self).__contains__(x):
            return True

        for ml in [y for y in self if isinstance(y, MudList)]:
            if x in ml:
                return True

        return False

    def __iter__(self):
        return self

    def next(self):
        if self.iter_list:
            self.virtual_index += 1
            #print "V_next: ", self.virtual_index, self.real_index,MudList.__len__(self),self.iter_list_len
            if self.virtual_index < self.iter_list_len:
                return self.iter_list[self.virtual_index]

        try:
            self.real_index = self.real_index + 1
            if isinstance(self[self.real_index], MudList):
                if len(self[self.real_index]) > 0:
                    self.virtual_index = -1
                    self.iter_list_len = len(self[self.real_index])
                    self.iter_list = self[self.real_index]

            return self[self.real_index]
        except IndexError:
            self.real_index = -1
            self.virtual_index = -1
            self.iter_list = False
            self.iter_list_len = None
            raise StopIteration


class Collection(MudObject):
    """
    A Collection is a type of object where the little pieces of it do not matter
    much.  The best example would be money.  They are represented as a
    quantity, while still having all of the features of a regular MudObject.
    """

    def __init__(self, q=1, *arg, **kwarg):
        self.quantity = q
        MudObject.__init__(self, *arg, **kwarg)

    def desc(self):
        if hasattr(self, "name"):
            return "<%s: (%i %s) [%s]>" % \
                   (type(self).__name__, self.quantity, self.name, self.gameID)
        else:
            return object.__repr__(self)


class Control(MudObject):
    def __init__(self, thing, *arg, **kwarg):
        MudObject.__init__(self, *arg, **kwarg)
        self.control = thing

    def link(self, thing):
        self.control = thing

    def unlink(self):
        self.control = None


class UnknownMudObject(MudObject):
    def __init__(self):
        MudObject.__init__(self)
        self.name = "Unidentified"
        self.shortDescription = "An unidentified thing"


class RoomExit(MudObject):
    def __init__(self, exitsTo=None, magicWord=None, *arg, **kwarg):
        MudObject.__init__(self, *arg, **kwarg)
        self.exitsTo = exitsTo
        self.isOpen = True
        self._pair = None  # if this door gets opened, then open the pair

        if magicWord != None:
            self.magicWord = magicWord.lower()
        else:
            self.magicWord = None

    def pair(self, door):
        self._pair = door
        door._pair = self

    def open_state(self, isOpen):
        self.isOpen = isOpen
        if self._pair != None:
            if self._pair.isOpen != isOpen:
                self._pair.open_state(isOpen)

    def desc(self):
        if self.isOpen:
            flag = "[ ]"
        else:
            flag = "[X]"

        if self.exitsTo != None:
            return "%s exit to %s (%s) [%s]" % \
                   (flag, self.exitsTo.name, self.magicWord, self.gameID)
        return "exit to nowhere"


class Room(MudList, MudObject):
    def __init__(self, *arg, **kwarg):
        MudObject.__init__(self)
        MudList.__init__(self, *arg, **kwarg)
        self.channel = evt.TalkChannel("room channel - %s" % self.name)

        super(Room, self).Bind(evt.EVT_LOOK, self.on_look)

    def addExit(self, exitsTo, magicWord):
        door_here = RoomExit(exitsTo, magicWord)

        self.append(door_here)

        directions = { \
            "north": "south", "east": "west", \
            "south": "north", "west": "east"}
        oppisite = None

        if magicWord in directions.keys():
            oppisite = directions[magicWord]

        if oppisite != None:
            door_there = RoomExit(self, oppisite)
            exitsTo.append(door_there)
            door_here.pair = (door_there)

    def append(self, thing):
        ok = super(Room, self).append(thing)
        if ok:
            self.channel.addMember(thing)
            return True
        return False

    def remove(self, thing):
        ok = super(Room, self).remove(thing)
        if ok:
            self.channel.removeMember(thing)
            return True
        return False

    def on_look(self, event):
        contents = self.list_contents(event.viewer)
        text = "%s\n\n%s" % (self.longDescription, contents)
        print "sent: text"
        self.sendEvent(evt.TextMessage(text), event.viewer)

    def list_contents(self, viewer):
        """
        Group together objects that are most related:
            count bases and clump other objects with highest number of common
            base classes

        this something of "fuzzy" matching...step:
            find all the classes represented here
            assign them all a id
            based on a score, clump together the similiar things
        """
        # THIS SHOULD BE CACHED AND ONLY CALLED WHEN SOMETHING ENTERS OR LEAVES
        contents = [x for x in self if not x.isHidden]
        if contents:
            #~ class_score={}
            #~ class_cache={}
            #~ thing_score={}
            #~ class_power=0

            #~ for thing in contents:
            #~ classes=self._get_classes(thing)
            #~ class_cache[thing]=classes

            #~ for aclass in classes:
            #~ if aclass not in class_score.keys():
            #~ class_score[aclass]=pow(2,class_power)
            #~ class_power+=1

            #~ pairs = []
            #~ for thing, class_list in class_cache.items():
            #~ score=0
            #~ for aclass in class_list:
            #~ score+=class_score[aclass]
            #~ pairs.append([score,thing])

            #~ pairs.sort()
            #~ contents=[x[1] for x in pairs]

            # exits always go last
            # find the exits, then remove them, add at the end
            exits = [x for x in contents if isinstance(x, RoomExit)]
            map(contents.remove, exits)
            contents.extend(exits)

            #types=[type(x).__name__ for x in contents]
            #types.sort()
            if len(contents) == 1:
                if contents[0] == viewer:
                    # this is returned when the only thing in room is viewer
                    return "you do not see anything."
                return "you do not see anything. (this is a bug)"

            text = "You also see:\n"
            for obj in contents:
                if obj != viewer:
                    try:
                        d = obj.desc()
                    except:
                        d = "%s" % obj
                    text = text + "\t%s\n" % d
            return text
        else:
            return "you do not see anything. (this is a bug)"


class Zone(MudObject):
    """
    Stub class for a Zone.

    A zone is a list of rooms.  Useful for defining chararestics to share.
    """
    pass


#bug: gear is incomplete
class Gear(MudObject):
    def __init__(self, gearClass=None, *arg, **kwarg):
        MudObject.__init__(self, *arg, **kwarg)
        self.name = "unnamed gear"
        self.gearClass = gearClass


class Weapon(Gear):
    def __init__(self, name=None, weaponClass=None, dp=0, verb=None, *arg,
                 **kwarg):
        Gear.__init__(self, gearClass=weaponClass, *arg, **kwarg)
        self.name = name
        self.dp = dp
        self.attackRatio = 1

        if verb == None:
            verb = english.Verb("attack")
        self.verb = verb


class Bag(MudList, MudObject):
    def __init__(self, *arg, **kwarg):
        super(Bag, self).__init__(*arg, **kwarg)
        self.isOpen = True

    def append(self, thing):
        if self.isOpen:
            return super(Bag, self).append(thing)

        return False

    def on_open(self):
        self.isOpen = True

    def on_close(self):
        self.isOpen = False

    def on_look(self, event):
        r = self.shortDescription
        if len(self) > 0:
            if self.isOpen:
                r = r + "\nContains:\n"
                for thing in self:
                    r = r + "\t%s\n" % thing
            else:
                r = r + "\nclosed."
        else:
            r = "\nis empty"

        self.sendEvent(evt.TextMessage(r), event.viewer)


class Mobile(MudObject):
    """
    Mobiles are capable of gaining experience points and leveling up.
    This also counts for npcs of this class!
    """

    def __init__(self, *arg, **kwarg):
        MudObject.__init__(self, *arg, **kwarg)
        self.primaryWeaponSlot = 0
        self.foe = None
        self.name = "unnamed mobile"
        self.isAlive = True
        self.exp = 0
        self.gear = MudInventory()
        self.inventory = MudList(owner=self)
        self.identified = []

    """
    we emulate a list here.  this is so we can handle situations were the mobile
    has many secondary storage units (bags)
    currently, unimplimented, but here for the future =)
    """

    def __len__(self):
        return len(self.gear)

    def append(self, x):
        self.gear.append(x)

    def remove(self, x):
        self.gear.remove(x)

    def pop(self):
        return self.gear.pop()

    def __add__():
        pass

    def __radd__():
        pass

    def __iadd__():
        pass

    def __mul__():
        pass

    def __rmul__():
        pass

    def __imul__():
        pass

    def __contains__(self, x):
        return self.gear.__contains__(x)

    def __iter__():
        pass

    """
    end list emulation
    """

    def add_exp(self, exp):
        """
        Give mobile exp, also handles level changes)
        """

        self.exp += exp

    def next_level(self):
        """
        Return the amount of exp needed to reach the next level.
        Currently, this value is just computed here.
        """

        exp = int(10 * (self.level + 1) * (self.level + 1)) - int(self.exp)
        if exp < 0: exp = 0
        return exp

    # bug: no checking if doors are open/closed when mobile moves
    def move(self, direction):
        # if we get a RoomExit, just teleport there...no checking!
        if isinstance(direction, RoomExit):
            a = english.Statement("move", direction.magicWord)
            self.emote(action=a)
            return self.teleport(direction.exitsTo)

        if type(direction) == StringType:
            direction.lower()
            for thing in self.location:
                if isinstance(thing, RoomExit):
                    if direction == thing.magicWord:
                        a = english.Statement("move", RoomExit.magicWord)
                        self.emote(action=a)
                        return self.teleport(thing.exitsTo)

    def teleport(self, room):
        return room.append(self)

    def addGearSlot(self, slot):
        self.gear.append(slot)

    def removeGearSlot(self, slot):
        return self.gear.remove(slot)

    def equip(self, gear, slot=None):
        if slot == None:
            for slot in self.gear:
                return self.checkEquip(gear, slot)
        else:
            return self.checkEquip(gear, slot)

    # bug: equip emote is awkward
    # bug: equip method is somewhat awkward.
    # bug: equip...should slots have an inventory?
    def checkEquip(self, gear, slot):
        test = slot.checkBind(gear)

        if test == True:
            if not gear in self.inventory:
                return False
            self.inventory.remove(gear)
            slot.bind(gear)
            self.emote(action=english.Action("equip", gear, slot, "on"))
            return True

        if isinstance(test, Gear):
            self.inventory.append(test)
            slot.unbind()
            return self.checkEquip(gear, slot)

        return test

    def unequip(self, gear, slot=None):
        if isinstance(gear, ItemSlot):
            slot = gear
            gear = gear._slot

        if gear == slot._default:
            return True

        if slot != None:
            self.inventory.append(gear)
            slot.unbind()
            self.emote(action=english.Action("unequip", gear))
            return True

        for slot in self.gear:
            if slot._slot == gear:
                self.inventory.append(gear)
                slot.unbind()
                self.emote(action=english.Action("unequip", gear))
                return True

    def evt_die(self):
        for slot in self.gear:
            self.unequip(slot)

        for thing in self.inventory:
            self.drop(thing)

        MudObject.evt_die(self)

    def on_look(self, event):
        r = self.shortDescription
        if len(self.gear) > 0:
            r = r + "\n%s carries:\n" % self
            for slot in self.gear:
                r = r + "%s\n" % slot

        self.sendEvent(evt.TextMessage(r), event.viewer)


class ItemSlot(MudObject):
    def __init__(self, name="item slot", canEquip=[], default=None, *arg,
                 **kwarg):
        MudObject.__init__(self, name, *arg, **kwarg)
        self.shortDescription = name
        self._default = default
        self._slot = default
        self._canEquip = canEquip

    def bind(self, gear):
        if self.checkBind(gear):
            self._slot = gear
            self.keywords = gear.keywords
            return True
        else:
            return False

    def unbind(self):
        self._slot = self._default
        self.keywords = []
        return True

    def checkBind(self, gear):
        if self._slot != None:
            if self._slot == self._default:
                return True
            return self._slot

        if self._canEquip == "all": return True
        if gear.itemClass in self._canEquip: return True
        return False


class PrettyOutput:
    def __init__(self):
        return

    def columnize(self, list, displaywidth=80, indent=0, sep="  "):
        """Display a list of strings as a compact set of columns.

        Each column is only as wide as necessary.
        """
        if not list:
            return
        nonstrings = [i for i in range(len(list))
                      if not isinstance(list[i], str)]
        if nonstrings:
            raise TypeError, ("list[i] not a string for i in %s" %
                              ", ".join(map(str, nonstrings)))
        size = len(list)
        if size == 1:
            return "%s%s\n" % (" " * indent, str(list[0]))

        displaywidth -= indent

        # Try every row count from 1 upwards
        for nrows in range(1, len(list)):
            ncols = (size + nrows - 1) // nrows
            colwidths = []
            totwidth = 0 - len(sep)
            for col in range(ncols):
                colwidth = indent
                for row in range(nrows):
                    i = row + nrows * col
                    if i >= size:
                        break
                    x = list[i]
                    colwidth = max(colwidth, len(x))
                colwidths.append(colwidth)
                totwidth += colwidth + len(sep)
                if totwidth > displaywidth:
                    break
            if totwidth <= displaywidth:
                break
        else:
            nrows = len(list)
            ncols = 1
            colwidths = [0]

        output = ""
        for row in range(nrows):
            texts = []
            for col in range(ncols):
                i = row + nrows * col
                if i >= size:
                    x = ""
                else:
                    x = list[i]
                texts.append(x)
            while texts and not texts[-1]:
                del texts[-1]
            for col in range(len(texts)):
                texts[col] = texts[col].ljust(colwidths[col])

            output += "%s%s\n" % (" " * indent, str(sep.join(texts)))

        return output
