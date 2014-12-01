"""
another rewrite.

trying to perfect the method/mudfunc call system
make distinctions between mud func and methods obsolete
make "on_[whatever]" trigger/callbkack system work, without strange rules
also, writing AI clients should be consistent with other types

"""

import sys, new, pprint
from types import StringType, TupleType, DictType, IntType, MethodType

import english
import event as evt
import message as msg
from base import MudAtom, MudObject
from mudprop2 import *


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
            # print "V_next: ", self.virtual_index, self.real_index,MudList.__len__(self),self.iter_list_len
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
            # ~ class_score={}
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


# bug: gear is incomplete
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
