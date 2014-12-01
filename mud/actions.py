from thing import Thing


class Action(object):
    def __init__(self, host):
        self.host = host


class TakeAction(Action):
    def __init__(self, *arg, **kwarg):
        super(TakeAction, self).__init__(self, *arg, **kwarg)

    def do(self, thing, takeFrom=None):
        if takeFrom == None:
            takeFrom = self.host.location.inventory

        if self.host.inventory.add(thing):
            self.host.emote(action=english.Action("take", thing))
            return True
        return False
