# bug: verb tense labeling is inaccurate and confusing

from types import StringType
from string import find


def MakeNounList(nouns):
    if len(nouns) == 2:
        return "%s and %s" % (nouns[0], nouns[1])

    phrase = ""
    if len(nouns) > 2:
        for x in range(len(nouns) - 1):
            phrase += "%s, " % nouns[x]
        phrase += "and %s" % nouns[len(nouns) - 1]
        return phrase

    # bug: should raise exception if noun list is only 1 long
    return nouns


class Word(object):
    def __init__(self):
        self._dirty = True
        self.descriptor = None

    # these from msg.py (poo)
    def add_s(self, s):
        if len(s) < 2: return s + 's'
        if s[-1] == 'y' and find('aeiou', s[-2]) == -1: return s + 'ies'
        if s[-1] == 'o' and find('aeiouy', s[-2]) == -1: return s + 'es'
        if s[-1] in ('s', 'x'): return s + 'es'
        if s[-2:] in ('ch', 'sh'): return s + 'es'
        return s + 's'

    def remove_s(self, s):
        if len(s) <= 3 or s[-1] != 's':    return s
        if s[-2] != 'e': return s[:-1]
        if s[-3] == 'h' and s[-4] in ('c', 's'): return s[:-2]
        if s[-3] in ('o', 'x'): return s[:-2]
        if s[-3] == 's' and find('aeiouy', s[-4]) == -1: return s[:-2]
        if s[-3] == 'i': return s[:-3] + 'y'
        return s[:-1]

    # ====

    # bug: add_ly method works, but sucks
    def add_ly(self, w):
        return w + "ly"

    def __setattr__(self, name, value):
        if name != "_dirty":
            object.__setattr__(self, name, value)
            object.__setattr__(self, "_dirty", True)

    def __str__(self):
        if self._dirty:
            self.fix()

        return self.string


class Verb(Word):
    def __init__(self, word, form=None):
        Word.__init__(self)
        self.word = word
        self.fix()

    def describe(self, word):
        # self.descriptor=self.add_ly(word)
        self.descriptor = word
        self.fix()
        return self

    def fix(self):
        if self.word == "is":
            self.first = self.word
            self.third = self.word
            return

        self.first = self.word
        self.third = self.add_s(self.word)

        if self.descriptor != None:
            self.first = self.descriptor + " " + self.first
            self.third = self.descriptor + " " + self.third

        self.string = "VERB-NOT FIXED"


class Noun(Word):
    def __init__(self, thing=None, gender=None, quantity=None):
        Word.__init__(self)

        self.thing = thing
        self.gender = gender
        self.quantity = quantity
        self.defArticle = None
        self.indefArticle = None

    def describe(self, word):
        self.descriptor = word
        return self

    def fix(self):
        self.string = self.thing.__str__()

        if self.descriptor != None:
            self.string = self.descriptor + " " + self.string

        self._prefixArticle()

    def _prefixArticle(self):
        self.defArticle = "the"

        if self.string[:1].lower() == "a":
            self.indefArticle = "an"
        else:
            self.indefArticle = "a"

        self.string = self.defArticle + " " + self.string


# bug: grammar class works, but is being rewritten... (action is duct tape)
class Grammar(object):
    def __init__(self, sub=None, addressee=None):
        self.speaker = None
        self.grammar = None
        self.addressee = addressee
        self.sub = sub
        self._dirty = True

    def __str__(self):
        if self._dirty:
            self._fixGrammar()

        return self.text

    # overload me!
    def _fixGrammar(self):
        self._dirty = False

    def _conVerb(self, verb):
        if self.sub == self.addressee:
            return verb.first
        else:
            return verb.third

    # substitute the right pronoun if subject refers to the sender of message
    def _checkSubject(self, thing):
        if thing == self.addressee:
            return "you"
        return self._prefixArticle(thing)

    # substitute the right pronoun if word refers to the sender of message
    def _checkWord(self, thing):
        if thing == self.addressee:
            if self.sub == thing:
                return "yourself"
            return "you"
        return self._prefixArticle(thing)

    # this isn't what i want, but works fine for now--
    # shouldn't be creating nouns all the time, just keep them!
    # in future, all of english.py should be working in grammar terms,
    # not mud terms (things)
    def _prefixArticle(self, thing):
        # if we get a string, (we expect a thing), then return a generic article
        if type(thing) == StringType:
            return "(fake) the %s" % thing

        word = Noun(thing)

        return word.__str__()

    def __setattr__(self, name, value):
        if name != "_dirty":
            object.__setattr__(self, name, value)
            object.__setattr__(self, "_dirty", True)


# bug: English.Action does not support modifiers...should be in verbs?
class Action(Grammar):
    def __init__(self, verb=None, do=None, io=None, prep=None, modifier=None):
        Grammar.__init__(self)

        self.do = do
        self.io = io
        self.prep = prep

        # if we get a string here, then just make a new instance of Verb
        if type(verb) == StringType:
            verb = Verb(verb)
        self.verb = verb

        self.text = ""

    def _handle_say(self):
        Grammar._fixGrammar(self)

        sub = self._checkSubject(self.sub)
        verb = self._conVerb(self.verb)
        wo = (sub, verb)

        if self.do:
            do = self.do
            wo = (sub, verb, do)

        self.text = " ".join(wo).rstrip()

    def _fixGrammar(self):
        if self.verb.first == "say":
            return self._handle_say()

        Grammar._fixGrammar(self)

        sub = self._checkSubject(self.sub)
        verb = self._conVerb(self.verb)
        wo = (sub, verb)

        if self.do:
            do = self._checkWord(self.do)
            wo = (sub, verb, do)

        if self.io:
            io = self._checkWord(self.io)
            if self.prep:
                wo = (sub, verb, do, self.prep, io)
            else:
                wo = (sub, verb, io, do)

        self.text = " ".join(wo).rstrip()

        return self.text


class Statement(Grammar):
    def __init__(self, verb, adj=None):
        Grammar.__init__(self)

        if type(verb) == StringType:
            verb = Verb(verb)

        self.verb = verb
        self.adj = adj

    def _fixGrammar(self):
        Grammar._fixGrammar(self)

        sub = self._checkSubject(self.sub)
        verb = self._conVerb(self.verb)
        adj = self.adj

        self.text = " ".join([sub, verb, adj]).rstrip()

        return self.text
