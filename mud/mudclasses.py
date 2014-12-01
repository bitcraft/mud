"""
this is the older, non-security based framework
"""

import sys
from math import pow

import english
import event as evt
import message as msg

from types import StringType, TupleType, DictType

global gUser

gUser = 'mike'
gOwner = 'mike'


class MudPermission(object):
    def __init__(self, owner=None):
        self.owner = owner

    def __getattribute__(self, name):
        print self, name
        return object.__getattribute__(self, name)


class MudFunction(MudPermission):
    pass


class Thing(evt.EventClient):
    population = []

    global gOwner
    gOwner = None

    defaults = {
    "isAlive": False, \
    "isHidden": False \
        }

    def __init__(self, name=None, shortDescription="", *arg, **kwarg):
        evt.EventClient.__init__(self)
        self.shortDescription = shortDescription
        self.longDescription = ""
        self.keywords = []
        self.hp = 1
        self.isDebug = True  # unimplimented
        self.isDestroyed = False  # if true, events will be ignored
        self.isPermanent = True  # will not be automatically cleaned up
        self.isUnknown = False  # will default to not being indentified
        self.isDirty = True  # has not been saved since last change
        self.control = None  # hack-ish. for players
        self.location = None  # for emotes and talking, etc
        self.owner = self  # player/object that contains this one
        self.deathEmote = "is destroyed"

        if name == None:
            self.name = "unnamed %s" % type(self).__name__
        else:
            self.name = name

        for key, value in Thing.defaults.items():
            if not hasattr(self, key):
                setattr(self, key, value)

                # kwargList=["owner"]
        #self.argHelper(kwarg,kwargList)

        Thing.population.append(self)
        self.gameID = len(Thing.population)

        Thing.evtHandler.add(self)

        self.Bind(evt.EVT_LOOK, self.on_look)
        self.Bind(evt.EVT_ATTACK, self.on_attack)
        self.Bind(evt.EVT_MESSAGE, self.on_message)

    def _get_classes(self, object):
        classes = [object.__class__]
        all_classes = []

        while classes:
            aclass = classes.pop(0)
            classes = classes + list(aclass.__bases__)
            all_classes.append(aclass)

        all_classes.reverse()

        return all_classes

    def argHelper(self, kwarg, kwargList=[]):
        for kw in kwargList:
            if kw in kwarg.keys():
                self.__dict__[kw] = kwarg[kw]

    def sendEvent(self, event, sendTo=None):
        if self.isDestroyed:
            if self.control:
                msg = evt.TextMessage("you are dead")
                evt.EventClient.sendEvent(self, msg, self.control)
        else:
            evt.EventClient.sendEvent(self, event, sendTo)

    def on_message(self, event):
        if self.control != None:
            event.sendTo = self.control
            Thing.evtHandler.que(event)

    def on_look(self, event):
        response = evt.TextMessage(self.shortDescription)
        self.sendEvent(response, event.viewer)

    def on_attack(self, event):
        dp = event.dp

        self.hp -= dp
        if self.hp <= 0:
            self.evt_die()

        return self.hp

    def aiHook(self):
        """ overload me! """
        pass

    def drop(self, thing, dropTo=None):
        if isinstance(thing, TupleType):
            for thing2 in thing:
                self.drop(thing2, dropTo)
            # bug: this should check each drop, first...
            return True

        if dropTo == None:
            dropTo = self.location

        # we do this to make sure the location gets set properly
        if isinstance(dropTo, mc.Inventory):
            if dropTo.add(thing):
                self.emote(action=english.Action("drop", thing))
                return True

        return False

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

        Thing.population.remove(self)

    def evt_die(self):
        if self.isDestroyed == True:
            return

        if self.isAlive == True:
            self.emote(action=english.Action("die"))
        else:
            self.emote(text=self.deathEmote)
        self.hp = 0
        self.isAlive = False
        self.destroy()

    def evt_examine(self):
        pass

    def __str__(self):
        return object.__repr__(self)

        if hasattr(self, "isHidden"):
            if not self.isHidden:
                if hasattr(self, "name"):
                    return "<%s: (%s) [%s]>" % \
                           (type(self).__name__, self.name, self.gameID)
                else:
                    return object.__str__(self)
            else:
                return "<hidden>"
        else:
            return object.__repr__(self)

    # overload me!
    def update(self, name=None):
        pass

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == "_index" or name == "_size":
            return
        print gOwner, self, name, value

        if name != "isDirty":
            object.__setattr__(self, "isDirty", True)  # mark the "isDirty" flag
            # self.update(name)


class Collection(Thing):
    """
    A Collection is a type of object where the little pieces of it do not matter
    much.  The best example would be money.  They are represented as a
    quantity, while still having all of the features of a regular Thing.
    """

    def __init__(self, q=1, *arg, **kwarg):
        self.quantity = q
        Thing.__init__(self, *arg, **kwarg)

    def desc(self):
        if hasattr(self, "name"):
            return "<%s: (%i %s) [%s]>" % \
                   (type(self).__name__, self.quantity, self.name, self.gameID)
        else:
            return object.__repr__(self)


class Money(Collection):
    pass


class UnknownThing(Thing):
    def __init__(self):
        Thing.__init__(self)
        self.name = "Unidentified"
        self.shortDescription = "An unidentified thing"


class Talker:
    def say(self, text, sayTo=None):
        self.emote(action=english.Action("say", text, False))


class Eye(MudPermission):
    def __init__(self):
        MudPermission.__init__(self)

    def look(self, thing):
        if thing.isUnknown:
            if not self.isIdentified(thing):
                thing = UnknownThing()

        self.sendEvent(evt.LookEvent(self, thing))

    def look2(self, thing):
        """
        This look is called when we just want a string returned without
        raising	a look event.  Currently just used for rooms to print a list of
        things.
        """
        if thing.isUnknown:
            if not self.isIdentified(thing):
                thing = UnknownThing()

        return "%s" % thing

    def examine(self, thing):
        r = thing.longDescription + "\n"
        return r

    def describe(self, thing):
        r = "%s's variables:\n" % thing
        keys = thing.__dict__.keys()
        keys.sort()
        for key in keys:
            if type(thing.__dict__[key]) == DictType:
                text = "  %s:\n" % key
                for key2, value2 in thing.__dict__[key].items():
                    text += "    %s: %s\n" % (key2, value2)
            else:
                text = "  %s: %s\n" % (key, thing.__dict__[key])
            r += text

        r += "\n%s's methods:\n" % thing
        # Inheritance says we have to look in class and
        # base classes; order is not important.
        # returns all methods, not just of TextControl class
        classes = [thing.__class__]
        all_methods = []

        for aclass in self._get_classes(thing):
            if aclass.__bases__:
                r += "  class: %s\n" % aclass
                my_methods = []
                for m in dir(aclass):
                    if m[:1] != "_":
                        if m not in all_methods:
                            my_methods.append(m)
                            all_methods.append(m)
                if my_methods:
                    my_methods.sort()
                    r += PrettyOutput().columnize(my_methods, indent=4)

        self.sendEvent(evt.TextMessage(r), self)

    def identify(self, thing):
        self.identified.append(thing)


class Control(Thing):
    def __init__(self, thing, *arg, **kwarg):
        Thing.__init__(self, *arg, **kwarg)
        self.control = thing

    def link(self, thing):
        self.control = thing

    def unlink(self):
        self.control = None


class Inventory(Thing):
    def __init__(self, *arg, **kwarg):
        Thing.__init__(self, *arg, **kwarg)
        self.maxSize = None

        self._inventory = []
        self._index = -1
        self._size = 0

    def update(self, name):
        pass

    def add(self, thing):
        if self.maxSize != None:
            if self._size + 1 > self.maxSize:
                self.emote(action=english.Statement("is", "full"))
                return False

        if thing.location != None:
            if thing.location.remove(thing) == False:
                return False

        thing.location = self
        self._inventory.append(thing)
        self._size += 1
        self._index = -1
        return True

    def remove(self, thing):
        if thing in self._inventory:
            self._inventory.remove(thing)
            self._size -= 1
            self._index = -1
            return True
        return False

    def clear(self):
        self._inventory = []
        self._index = -1
        self._size = 0

    def evt_die(self):
        drop = []
        for thing in self._inventory:
            drop.append(thing)

        for thing in drop:
            self.drop(thing)

        self.clear()
        Thing.evt_die(self)

    def __getitem__(self, index):
        return self._inventory[index]

    def __contains__(self, thing):
        if thing in self._inventory:
            return True
        return False

    def __len__(self):
        return self._size

    def __iter__(self):
        self._index = -1
        return self

    def next(self):
        self._index += 1
        if self._index >= self._size:
            raise StopIteration
        return self._inventory[self._index]


class RoomExit(Thing):
    def __init__(self, exitsTo=None, magicWord=None, *arg, **kwarg):
        self.exitsTo = exitsTo
        self.isOpen = True
        self._pair = None  # if this door gets opened, then open the pair
        Thing.__init__(self, *arg, **kwarg)

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


class Room(Inventory):
    def __init__(self, *arg, **kwarg):
        Inventory.__init__(self, *arg, **kwarg)
        self._createTalkChannel()

    def addExit(self, exitsTo, magicWord):
        door_here = RoomExit(exitsTo, magicWord)

        self.add(door_here)

        directions = { \
            "north": "south", "east": "west", \
            "south": "north", "west": "east"}
        oppisite = None

        if magicWord in directions.keys():
            oppisite = directions[magicWord]

        if oppisite != None:
            door_there = RoomExit(self, oppisite)
            exitsTo.add(door_there)
            door_here.pair = (door_there)

    def add(self, thing):
        if Inventory.add(self, thing):
            self.channel.addMember(thing)
            return True
        return False

    def remove(self, thing):
        if Inventory.remove(self, thing):
            self.channel.removeMember(thing)
            return True

    def on_look(self, event):
        contents = self.list_contents(event.viewer)
        text = "%s\n\n%s" % (self.longDescription, contents)
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

        i think each id should be a power of two, then the relationship
        can be represented by a simple long integer

        """
        contents = [x for x in self if not x.isHidden]
        if contents:
            class_score = {}
            class_cache = {}
            thing_score = {}
            class_power = 0

            for thing in contents:
                classes = self._get_classes(thing)
                class_cache[thing] = classes

                for aclass in classes:
                    if aclass not in class_score.keys():
                        class_score[aclass] = pow(2, class_power)
                        class_power += 1

            pairs = []
            for thing, class_list in class_cache.items():
                score = 0
                for aclass in class_list:
                    score += class_score[aclass]
                pairs.append([score, thing])

            pairs.sort()
            contents = [x[1] for x in pairs]

            # exits always go last
            # find the exits, then remove them, add at the end
            exits = [x for x in contents if isinstance(x, RoomExit)]
            map(contents.remove, exits)
            contents.extend(exits)

            # types=[type(x).__name__ for x in contents]
            #types.sort()

            if len(contents) == 1:
                if contents[0] == viewer:
                    # this is returned when the only thing in room is viewer
                    return "you do not see anything."
                return "you do not see anything. (this is a bug)"

            text = "You also see:\n"
            for thing in contents:
                if thing != viewer:
                    text = text + "\t%s\n" % viewer.look2(thing)
            return text
        else:
            return "you do not see anything. (this is a bug)"

    def _createTalkChannel(self):
        channel = evt.TalkChannel()
        channel.name = "room channel - %s" % self.name
        self.channel = channel


# bug: gear is incomplete
class Gear(Thing):
    def __init__(self, gearClass=None, *arg, **kwarg):
        Thing.__init__(self, *arg, **kwarg)
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


class Bag(Inventory):
    def __init__(self, *arg, **kwarg):
        Inventory.__init__(self, *arg, **kwarg)
        self.isOpen = True

    def add(self, thing):
        if self.isOpen:
            return Inventory.add(self, thing)

        return False

    def on_open(self):
        self.isOpen = True

    def on_close(self):
        self.isOpen = False

    def on_look(self, event):
        r = self.shortDescription
        if len(self) > 0:
            if self.isOpen:
                r = r + "\nContains:"
                for thing in self:
                    r = r + "%s\n" % thing
            else:
                r = r + "\nclosed."
        else:
            r = "\nis empty"

        self.sendEvent(evt.TextMessage(r), event.sender)


class Mobile(Thing, Talker, Eye):
    """
    Mobiles are capable of gaining experience points and leveling up.
    This also counts for npcs of this class!
    """

    def __init__(self, *arg, **kwarg):
        self.name = "unnamed mobile"
        self.isAlive = True
        self.exp = 0
        self.gear = Inventory(owner=self)
        self.inventory = Inventory(owner=self)
        self.identified = []

        Thing.__init__(self, *arg, **kwarg)

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

    # "call-back" function, called by a thing to decied what to return if
    # printed. not complete.
    # bug: identfication not implimented
    def isIdentified(self, thing):
        if thing in self.identified:
            return True
        else:
            return False

    def teleport(self, room):
        return room.add(self)

    # overloaded this because mobiles have inventories, and we want to check
    def drop(self, thing, dropTo=None):
        if isinstance(thing, TupleType):
            for thing2 in thing:
                self.drop(thing2, dropTo)
            # bug: this should check each drop, first...
            return True

        if thing in self.inventory:
            Thing.drop(self, thing, dropTo)
            return True
        return False

    def put(self, thing, dropTo):
        if dropTo.add(thing):
            a = english.Action("put", thing, dropTo, "into")
            self.emote(action=a)
            return True
        return False

    def take(self, thing, takeFrom=None):
        if takeFrom == None:
            takeFrom = self.location

        if isinstance(thing, Collection):
            pass

        if isinstance(thing, Thing):
            if self.inventory.add(thing):
                self.emote(action=english.Action("take", thing))
                return True
            return False

        if isinstance(thing, TupleType):
            for thing2 in thing:
                self.take(thing2)
            return True

    def addGearSlot(self, slot):
        self.gear.add(slot)

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
            self.inventory.add(test)
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
            self.inventory.add(gear)
            slot.unbind()
            self.emote(action=english.Action("unequip", gear))
            return True

        for slot in self.gear:
            if slot._slot == gear:
                self.inventory.add(gear)
                slot.unbind()
                self.emote(action=english.Action("unequip", gear))
                return True

    def evt_die(self):
        for slot in self.gear:
            self.unequip(slot)

        for thing in self.inventory:
            self.drop(thing)

        Thing.evt_die(self)

    def on_look(self, event):
        r = self.shortDescription
        if len(self.gear) > 0:
            r = r + "\n%s carries:\n" % self
            for slot in self.gear:
                r = r + "%s\n" % slot

        self.sendEvent(evt.TextMessage(r), event.sender)


class Fighter(Mobile):
    def __init__(self, *arg, **kwarg):
        Mobile.__init__(self, *arg, **kwarg)
        self.primaryWeaponSlot = 0
        self.foe = None

    # bug: attack emote not working; cannot combine string & custom emote...
    def attack(self, victim):
        w = self.gear[self.primaryWeaponSlot]._slot
        dp = w.dp

        a = english.Action(w.verb, victim)
        self.emote(action=a)

        attack = evt.AttackEvent(self, victim, w, dp)
        self.sendEvent(attack)

        return True


class ItemSlot(Thing):
    def __init__(self, name="item slot", canEquip=[], default=None, *arg,
                 **kwarg):
        Thing.__init__(self, name, *arg, **kwarg)
        self.shortDescription = name
        self._default = default
        self._slot = default
        self._canEquip = canEquip

    def bind(self, gear):
        self._slot = gear
        self.keywords = gear.keywords
        return True

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


class SpawnPoint(Thing):
    def __init__(self, spawnClass):
        Thing.__init__(self)
        self.name = "unnamed spawn point"
        self.spawnClass = spawnClass

    def spawn(self):
        if self.spawnClass == None:
            return False

        new = self.spawnClass(self)
        self.location.add(new)


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
