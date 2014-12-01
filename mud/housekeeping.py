# This god is Hestia, greek goddess of hearth and Home. keeper of the flame at
# Mt. Olympus. This char is invisable to all others, and travels room to room
# cleaning up things, making it all tidy.

from mudclasses2 import Mobile


class Hestia(Mobile):
    def __init__(self, *arg, **kwarg):
        Mobile.__init__(self, *arg, **kwarg)
        self.name = "Hestia"
        self.shortDescription = "???"

    def aiHook(self):
        for thing in self.location:
            if thing.isPermanent == False:
                self.tidy(thing)

    def tidy(self, thing):
        self.take(thing)

        # quiet this up a bit
        thing.deathEmote = ""
        thing.destroy()
