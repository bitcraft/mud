#!/usr/bin/python
import mudclasses2 as mc
import textcontrol as tc
import english
import message as msg
from elevator import CallButton, ElevatorDoor, Elevator
from whiteboard import Whiteboard
from housekeeping import Hestia

# set up our little world...
class Bob(mc.Fighter):
	def __init__(self,*arg,**kwarg):
		mc.Fighter.__init__(self,"bob",*arg,**kwarg)
		self.hp=10
		self.shortDescription="grubby looking man"
		self.keywords=['person','man']

	def aiHook(self):
		if self.foe:
			self.attack(self.foe)
			if self.foe.isAlive==False:
				self.foe=None

	def on_attack(self,event):
		foe=event.sender

		self.say("ouch!")
		mc.Fighter.on_attack(self,event)
		if foe!=None:
			self.foe=foe

	def on_shake(self):
		fang=mc.Weapon("main hand")
		fang.name="Fang"
		fang.dp=4
		fang.shortDescription="small knife with a faint glow"
		fang.keywords=['knife','dagger']
		fang.verb=english.Verb("stab")
		self.inventory.add(fang)
		self.equip(fang)

class Slivers(mc.Thing):
	def __init__(self,*arg,**kwarg):
		mc.Thing.__init__(self,*arg,**kwarg)
		self.name="slivers"
		self.shortDescription="pile of slivers"
		self.keywords=["pile"]
		self.isPermanent=False

class Stick(mc.Weapon):
	def __init__(self,*arg,**kwarg):
		mc.Weapon.__init__(self,"main hand")
		self.name="Stick"
		self.dp=2
		self.shortDescription="stick"
		self.keywords=['stick']
		self.deathEmote="explodes into little slivers"

	def on_shake(self):
		# bug: no print!
		print "more bugs than you can shake a stick at..."

	def destroy(self):
		mc.Weapon.destroy(self)
		self.drop(Slivers())

class SnowGlobe(mc.Thing):
	def __init__(self,*arg,**kwarg):
		mc.Thing.__init__(self,"Snow Globe",*arg,**kwarg)
		self.shortDescription="a beautiful snow globe"
		self.keywords=['thing','globe']
		self.isUnknown=True

w_fist=mc.Weapon("main hand")
w_fist.shortDescription="your two fists"
w_fist.name="unarmed"
w_fist.dp=2
w_fist.keywords=['Unarmed']
w_fist.verb=english.Verb("punch")

cretin=mc.Fighter()
cretin.name="Cretin"
cretin.hp=10
cretin.shortDescription="ugly man"
cretin.keywords=['self','me']
cretin.addGearSlot(mc.ItemSlot("main hand","all",w_fist))

desk=mc.Thing("Wooden Desk","shabby wooden desk")
desk.keywords=['desk']

backpack=mc.Bag("Backpack","small orange backpack")
backpack.maxSize=1
backpack.keywords=['orange backpack','bag','backpack']

fang=mc.Weapon("main hand","Fang",4)
fang.shortDescription="small knife with a faint glow"
fang.keywords=['knife','dagger']
fang.verb=english.Verb("stab")

bob=Bob()
canEquip=("unarmed","dagger","misc")
bob.addGearSlot(mc.ItemSlot("main hand",canEquip,w_fist))
bob.inventory.add(fang)
bob.equip(fang)

sg=SnowGlobe()

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
elevator.buildFloors({1:r_lobby,2:r_apartment})
elevator.add(mc.Collection(100, "dollars"))

r_apartment.add(cretin)
r_lobby.addExit(r_cy,"south")

r_apartment.add(desk)
r_apartment.add(backpack)
r_apartment.add(Hestia())
r_apartment.addExit(r_bedroom,"east")

r_bedroom.add(sg)
r_bedroom.add(Whiteboard())

r_cy.add(bob)
r_cy.add(Stick())

player=tc.LocalPlayer(cretin)

# local imput ============================================================

while(True):
	print "="*80
	player.getInput()
	print "."*80
	mc.Thing.evtHandler.tick()

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
