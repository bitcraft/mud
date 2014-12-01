#!/usr/bin/python

import cmd
from textwrap import TextWrapper, dedent
import re
from types import StringType, IntType

import mudclasses2 as mc
import event as evt


def do_spam(self):
    """
    yeah, don't do it!
    """
    pass


# methods ending with "Command" will always return a Command item, which can
# be called later on.  used for queing.
class Command(object):
    def __init__(self, caller, func, *arg):
        self.caller = caller
        self.func = func
        self.arg = arg

    def do(self):
        return self.func(*self.arg)


class Qualifier:
    def __init__(self, name):
        self.name = name
        self.specificity = 1

    # add to a global thing?

    def matches(self, s, caller=None):
        return s

    def value(self, s, caller=None):
        return s


class QualThing(Qualifier):
    def matches(self, s, caller):
        search = []
        search.append(caller.location)
        search.append(caller.inventory)
        search.append(caller.gear)

        for inventory in search:
            thing = self._findRef(s, inventory)
            if thing != None:
                return thing

        return None

    def _findRef(self, thing, inventory):
        thing = thing.lower()
        # first search is by name of item
        for item in inventory:
            if item.name.lower() == thing:
                return item

        # second search is by keywords
        for item in inventory:
            for kw in item.keywords:
                if kw.lower() == thing:
                    return item

        return None


class QualVerb(Qualifier):
    def matches(self, s, caller=None):
        pass


class QualInteger(Qualifier):
    def __init__(self, name):
        Qualifier.__init__(self, name)
        self.re = re.compile('^\d+$').search

    def matches(self, s, caller=None):
        if type(s) == StringType:
            return self.re(s)

        if type(s) == IntType:
            return str(s)


# class to handle the command-line
# assumes a human.
class TextControl(mc.Control, cmd.Cmd):
    def __init__(self, thing):
        mc.Control.__init__(self, thing)
        cmd.Cmd.__init__(self)
        self.lastReferedTo = []
        self.aliases = []
        self.wrap = 70
        self.do_spam = do_spam  # this is hidden in help

    def blurt(self, text):
        self.sendEvent(evt.SystemMessage(text))

    def onecmd(self, line):
        # onecmd is not used that much, trying to get rid of.

        cmd, arg, line = self.parseline(line)
        if not line:
            return self.emptyline()
        self.lastcmd = line

    def copyList(self, list1):
        return [x for x in list1]

    def findRef(self, thing, inventory):
        thing = thing.lower()
        # first search is by name of item
        for item in inventory:
            try:
                if item.name.lower() == thing:
                    return item
            except:
                pass

        # second search is by keywords
        for item in inventory:
            for kw in item.keywords:
                if kw.lower() == thing:
                    return item

        return None

    def findThing(self, thing):
        if thing != None:
            search = []
            search.append(self.control.location)
            search.append(self.control.inventory)
            search.append(self.control.gear)

            for inventory in search:
                item = self.findRef(thing, inventory)
                if item != None:
                    if item in inventory:
                        return item, inventory

        return None, None

    def get_names(self, item=None):
        # Inheritance says we have to look in class and
        # base classes; order is not important.
        # returns all methods, not just of TextControl class
        if item == None:
            item = self

        names = []
        classes = [item.__class__]
        while classes:
            aclass = classes.pop(0)
            if aclass.__bases__:
                classes = classes + list(aclass.__bases__)
            names = names + dir(aclass)
        return names

    def findThingByID(self, gameID):
        for obj in mc.MudAtom.population:
            if gameID == obj.gameID:
                return obj
        return None

    def getReferedTo(self, words):
        articles = ['a', 'an', 'the']
        referedTo = []
        remove = []

        # find doors that player may refer to
        for thing in self.control.location:
            if isinstance(thing, mc.RoomExit):
                for word in words:
                    if word.lower() == thing.magicWord:
                        referedTo.append(thing)

        # replace words with the items they refer to, should be last step
        # we also remove articles if they are before a thing here
        for x in range(0, len(words)):
            word = words[x]
            if word[:1] == "#":
                thing = self.findThingByID(int(word[1:]))
            else:
                thing, inventory = self.findThing(word)

            if thing != None:
                if x >= 1:
                    if words[x - 1] in articles:
                        remove.append(x - 1)
                words[x] = thing
                referedTo.append(thing)

        # remove words we dont need
        for x in remove:
            words.pop(x)

        # handle "it"
        # if the last command only refered to one thing, then
        # substitute the word it for the last item, do not change words
        # bug: parser is lets "the" get by if input contains "the it"
        # bug: if there is no last refered to, "it" needs an error message
        # ie. "what are you trying to refer to?"

        if "it" in words:
            if len(referedTo) == 0:
                if len(self.lastReferedTo) == 1:
                    referedTo.append(self.lastReferedTo[0])
                    words[words.index("it")] = self.lastReferedTo[0]
                else:
                    print "!!!what are you refering to?"

        """
        Confusingly, "them" can refer to either two or more instances of
        Things, a Collection instance, two or more Collections, or a
        combination.
        """

        # here we just assume we are looking for two Things
        if "them" in words:
            if len(referedTo) == 0:
                if len(self.lastReferedTo) > 1:
                    x = words.index("them")
                    # we need to insert referedTo where "them" is
                    a = words[x + 1:]
                    words = words[:x]
                    words.extend(self.lastReferedTo)
                    words.extend(a)
                    referedTo.extend(self.lastReferedTo)
        # print referedTo

        # save what the player last refered to here
        self.lastReferedTo = referedTo

        print "words: %s" % words
        print "refer: %s" % referedTo

        return referedTo, words

    def findall(self, l, value, start=0):
        r = []
        for i in range(start, len(l)):
            if l[i] == value:
                r.append(i)
        return r

    # bug: punctuation isnt handled, and messes up everything
    # parse can have direct control over the item it handles.
    def parse(self, line):

        if self.control == None:
            self.blurt("your control is unlinked")
            return

        commandQue = []

        if line == "":
            line = self.lastcmd

        self.lastcmd = line

        # slice the input to a managable size
        line = line[0:128]

        # bug: input with multiple commands (\n seperated) are ignored
        if line.rfind("\n") > -1:
            return False

        words = line.split()
        punct = "\' \" , . ? !".split()  # incomplete

        # = special case! this is to remain compatable with cmd.py's do_help ===
        if len(words) > 0:
            if words[0] == "help":
                cmd, arg, line = self.parseline(line)
                return self.do_help(arg)
        # === end special case ===

        # checking to see if ands in words refer to items
        referedTo, words = self.getReferedTo(words)

        ands = self.findall(words, "and")

        group = []
        for i in ands:
            if isinstance(words[i - 1], mc.Thing):
                if isinstance(words[i + 1], mc.Thing):
                    group.append(words[i - 1])
                    group.append(words[i + 1])

        # group is a list of items that were refered to
        if len(group) > 0:
            commandQue = []
            for thing in group:
                cmd = self.getCommand(words, [thing])
                commandQue.append(cmd)

            if None in commandQue:
                return self.default()
            else:
                for cmd in commandQue:
                    cmd.do()
                return True
            return

        if len(ands) > 0:
            start = 0
            chunk = []
            vfyAnd = []
            for i in ands:
                chunk.append(words[start:i])
                start = i + 1

            if len(words[start:]) > 0:
                chunk.append(words[start:])

                # ok, we have some chunks!
            for i in chunk:
                cmd = self.getCommand(i, referedTo)
                vfyAnd.append(cmd)

            # with a reasonable amount of certainty, we can say "and" here
            # is used to split apart multiple actions if getCommand does not
            # return False for any chunk
            #if None not in vfyAnd:

            # bug: this is only temporary...
            commandQue = vfyAnd

        else:
            # simply process words as a single command
            cmd = self.getCommand(words, referedTo)
            commandQue.append(cmd)

        # if we have a unknown or failing command, then fail the whole parse
        if None in commandQue:
            return self.default()
        else:
            for cmd in commandQue:
                cmd.do()
            return True

    # getCommand will take a list of words and attempt to find a command from
    # it. if found, then getCommand will return a Commmand item.
    # words is a simple list of strings that is processed
    # if referedTo is passed on, getCommand will use that, otherwise, it will
    # do another lookup.  pass referedTo if possiable as a performance boost
    # getCommand can currently only handle one single command per list of words
    # returns false if cannot find a command or if a command fails
    def getCommand(self, words, referedTo=None):

        if referedTo == None:
            referedTo, words = self.getReferedTo(words)

        # bug: parseing is wasteful, could cache the method lookup...
        commands = []
        for name in self.get_names(self):
            if name[:3] == "do_":
                cmd = name[3:]
                commands.append(cmd)

        # find the command the player is using
        # bug: the command picker here gets confused with multiple commands
        cmd = None
        for word in words:
            if word in commands:
                cmd = word

        # we didn't find a commnd this player can handle in words
        # so we are looking elsewhere to figure it out
        if cmd == None:
            if len(words) > 0:
                for thing in referedTo:
                    cmd = self.checkitemCommand(words, thing)
                    if cmd != None:
                        return cmd

                    cmd = self.checkExits(words, thing)
                    if cmd != None:
                        return cmd

            return None
        else:
            func = getattr(self, 'do_' + cmd)
            cmd = Command(self, func, words, *referedTo)
            return cmd

    def default(self):
        self.blurt("what?")
        return False

    # bug: checkitemCommand only will handle one command at a time
    # bug: checkitemCommand cannot handle arguments well (only last of line)
    # bug: objcmds is all fucked. returns copies of methods
    # note: when passing words, it should already be processed (referenced)
    def checkitemCommand(self, words, thing):
        # bug: get_names can be wasteful...suggest chaching.
        commands = []
        for name in self.get_names(thing):
            if name[:3] == "on_":
                cmd = name[3:]
                commands.append(cmd)

        cmd = None
        for word in words:
            if word in commands:
                cmd = word

        if cmd != None:
            # arg=self.copyList(words)
            arg = words[words.index(thing) + 1:]
            print "%s arg:%s" % (cmd, arg)
            func = getattr(thing, 'on_' + cmd)
            if len(arg) == 0:
                cmd = Command(self, func)
            else:
                cmd = Command(self, func, arg)
            return cmd
        return None

    def checkExits(self, words, thing=None):
        if isinstance(thing, mc.RoomExit):
            if thing.magicWord in words:
                return Command(self, self.do_go, words, thing)
            return False

    def do_attack(self, words, victim=None):
        if victim != None:
            self.control.attack(victim)

    def do_describe(self, words, thing=None):
        if thing != None:
            self.control.describe(thing)

    def do_take(self, words, *thing):
        if thing != None:
            if not self.control.take(thing):
                self.blurt("take failed.")
        else:
            self.blurt("you dont see that.")

    def do_drop(self, words, *thing):
        if thing != None:
            if not self.control.drop(thing):
                self.blurt("drop failed (check your inventory).")
        else:
            self.blurt("drop what?")

    def do_equip(self, words, thing=None):
        if thing.owner == self.control.location:
            self.do_take(thing)
        self.control.equip(thing)

    def do_insert(self, words, *thing):
        self.control.insert(*thing)

    def do_examine(self, words, thing=None):
        """
        Print a complete list of an items variables and methods
        """
        if thing != None:
            self.blurt(self.control.examine(thing))

    def do_exit(self, words):
        """
        Exit the game.
        """
        exit()

    def do_fuck(self, words, thing=None):
        self.blurt("You dirty little asshole.")

    def do_go(self, words, where=None):
        if where != None:
            if self.control.move(where):
                self.control.look(self.control.location)
                return True
        return False

    def do_inventory(self, words):
        inv = self.control.inventory
        if len(inv) == 0:
            self.blurt("you are carring nothing")
            return
        self.blurt("you are carring:")
        for thing in inv:
            self.blurt("  %s" % thing)

    def do_look(self, words, thing=None):
        if thing == None:
            self.control.look(self.control.location)
        else:
            self.control.look(thing)

    def do_identify(self, words, thing=None):
        if thing != None:
            self.control.identify(thing)

    def do_put(self, words, thing=None, dropTo=None):
        if dropTo == None:
            self.default()
            return

        if thing != None:
            self.control.put(thing, dropTo)

    # bug: cannot say to things. can only make a generic say emote
    def do_say(self, words, sayTo=None):
        words.remove("say")
        text = " ".join(words)

        self.control.say(text, sayTo)

    def do_tell(self, words, sayTo=None):
        pass

    def do_unequip(self, words, gear=None):
        if gear == None:
            self.blurt("you dont see that.")
        else:
            self.control.unequip(gear)

    def do_walk(self, words, walkTo=None):
        pass

    def do_whereami(self, words, referedTo=None):
        self.blurt(self.control.describe(self.control.location))

    def do_place(self, words, *arg):
        self.place(*arg)

    def do_has(self, words, *arg):
        try:
            self.has(*arg)
        except:
            pass

    def formatdoc(self, text):
        text = dedent(text)

        # remove initial newline
        if text[0] == "\n":
            text = text[1:]
        return text

    # overloaded to dedent leading tabs on doc strings
    def do_help(self, arg):
        """
        Get help
        Usage: help [topic]
        """
        if arg:
            # XXX check arg syntax
            try:
                func = getattr(self, 'help_' + arg)
            except AttributeError:
                try:
                    doc = getattr(self, 'do_' + arg).__doc__
                    if doc:
                        doc = self.formatdoc(doc)
                        self.stdout.write("%s\n" % str(doc))
                        return
                except AttributeError:
                    pass
                self.stdout.write("%s\n" % str(self.nohelp % (arg,)))
                return
            func()
        else:
            names = self.get_names()
            cmds_doc = []
            cmds_undoc = []
            help = {}
            for name in names:
                if name[:5] == 'help_':
                    help[name[5:]] = 1
            names.sort()
            # There can be duplicates if routines overridden
            prevname = ''
            for name in names:
                if name[:3] == 'do_':
                    if name == prevname:
                        continue
                    prevname = name
                    cmd = name[3:]
                    if cmd in help:
                        cmds_doc.append(cmd)
                        del help[cmd]
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
            self.stdout.write("%s\n" % str(self.doc_leader))
            self.print_topics(self.doc_header, cmds_doc, 15, self.wrap)
            self.print_topics(self.misc_header, help.keys(), 15, self.wrap)
            self.print_topics(self.undoc_header, cmds_undoc, 15, self.wrap)


class Player(TextControl, evt.EventClient):
    def __init__(self, thing):
        TextControl.__init__(self, thing)
        evt.EventClient.__init__(self)
        thing.control = self
        self.name = 'name'
        self.control = thing
        self.Bind(evt.EVT_MESSAGE, self.on_message)


class LocalPlayer(Player):
    def __init__(self, thing):
        Player.__init__(self, thing)

    def getInput(self):
        line = raw_input('> ')
        self.parse(line)

    def on_message(self, event):
        if event.sender == self.control:
            sender = "[controller]"
        else:
            sender = "%s" % (event.sender)

        print "txt> %s" % (event)


class NetworkPlayer(TextControl):
    def __init__(self, connection, thing):
        TextControl.__init__(self, thing)
        self.connection = connection

    def _recvEvent(self, event):
        if event.sender == self.control:
            sender = "[controller]"
        else:
            sender = "%s" % (event.sender)

        if isinstance(event, evt.TextMessage):
            text = "txt> %s\n" % event
            self.connection.write(text)
