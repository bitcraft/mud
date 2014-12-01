#!/usr/bin/python
import mudclasses2 as mc
import textcontrol as tc
import english
import message as msg
from elevator import CallButton, ElevatorDoor, Elevator
from whiteboard import Whiteboard
from housekeeping import Hestia

"""
Our nifty in-game interface to the command parser
"""
class FunctionVault(mc.MudObject):
	def __init__(self):
		mc.MudObject.__init__(self)
		self.name="function vault"
		#self.contents = mc.MudFunctionDB.keys()

	def on_look(self,event):
		response=evt.TextMessage(self.contents)
		self.sendEvent(response, event.viewer)

w_fist=mc.Weapon("main hand")
w_fist.shortDescription="your two fists"
w_fist.name="unarmed"
w_fist.dp=2
w_fist.keywords=['Unarmed']
w_fist.verb=english.Verb("punch")

cretin=mc.Mobile()
cretin.name="Cretin"
cretin.hp=10
cretin.shortDescription="ugly man"
cretin.keywords=['self','me']
cretin.addGearSlot(mc.ItemSlot("main hand","all",w_fist))

desk=mc.MudObject("Wooden Desk","shabby wooden desk")
desk.keywords=['desk']

backpack=mc.Bag("Backpack","small orange backpack")
backpack.maxSize=2
backpack.keywords=['orange backpack','bag','backpack']

fang=mc.Weapon("main hand","Fang",4)
fang.shortDescription="small knife with a faint glow"
fang.keywords=['knife','dagger']
fang.verb=english.Verb("stab")

r_bedroom=mc.Room("Bedroom")
r_bedroom.longDescription="Your bedroom."
r_apartment=mc.Room("An apartment")
r_apartment.longDescription="Your room, a desk sits in the corner."
r_cy=mc.Room("Courtyard")
r_cy.longDescription="You are standing in front of a large concrete building.\
  There is a small park with concrete benches and countles scooters parked on\
 the side walk.  The guard sits quietly in his little shelter near the steps."
r_lobby=mc.Room("Lobby")
r_lobby.longDescription="A looby.  It smells funny."

elevator=Elevator()
elevator.buildFloors({1:r_lobby,10:r_apartment})

r_apartment.append(mc.Collection(100, "dollars"))
r_apartment.append(cretin)
r_lobby.addExit(r_cy,"south")

r_apartment.append(desk)
r_apartment.append(FunctionVault())
r_apartment.append(backpack)
r_apartment.append(Hestia())
r_apartment.addExit(r_bedroom,"east")

r_bedroom.append(Whiteboard())

player=tc.LocalPlayer(cretin)

# local imput ============================================================

while(True):
	print "="*80
	player.getInput()
	print "."*80
	mc.MudObject.evtHandler.tick()

exit()

# telnet server ===========================================================

from twisted.conch import telnet
from twisted.internet import protocol,reactor

class PlayerProtocol(protocol.Protocol):
	def dataReceived(self,line):
		self.player.onecmd(line)

	def connectionMade(self):
		self.write("welcome!!!\n")
		self.player=tc.NetworkPlayer(self,bob)

	def telnet_Command(self,cmd):
		self.write("command recv'd\n")

	def write(self,data):
		self.transport.write(data)

class PlayerFactory(protocol.Factory):
	protocol=PlayerProtocol

reactor.listenTCP(1100,PlayerFactory())
reactor.run()
