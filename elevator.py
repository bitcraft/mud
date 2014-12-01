import mudclasses2 as mc
import event as evt

class Button(mc.MudObject):
	def __init__(self,*arg,**kwarg):
		mc.MudObject.__init__(self,*arg,**kwarg)
		self.name="button"

	def on_push(self):
		pass

class CallButton(Button):
	def __init__(self,elevator,floor,*arg, **kwarg):
		Button.__init__(self,*arg,**kwarg)
		self.elevator=elevator
		self.floor=floor
		self.keywords=[str(floor)]

	def on_push(self):
		self.elevator.call(self.floor)

class ElevatorDoor(mc.RoomExit):
	"""
	This special door class cannot be opened by players but is never locked.
	"""
	def __init__(self,*arg,**kwarg):
		mc.RoomExit.__init__(self,*arg,**kwarg)
		self.isNoisey=True		# will "ding!" when opens
		self.isOpen=False

	def open_state(self, isOpen):
		if isOpen == self.isOpen:
			return

		mc.RoomExit.open_state(self, isOpen)

		if self.isNoisey and self.isOpen:
			pass
			#self.sendEvent(evt.TextMessage("ding!"),self.location.channel)
		if self.isOpen:
			self.emote(text="slides open.")
		else:
			self.emote(text="slides closed.")

class Elevator(mc.Room):
	"""
	This class is special room that has a button panel.
	You can "push" the buttons to goto a floor, which will change the
	room exit associated with this room.
	"""
	def __init__(self,doors=None,floors=None,*arg,**kwarg):
		mc.Room.__init__(self,*arg,**kwarg)
		self.doors={}
		self.floors={}
		self.doorOpenTime=2
		self.onFloor=None
		self.que=[]
		self.exitDoor=ElevatorDoor(None, "out")
		self.exitDoor.isNoisey=False

		self.name="an elevator"
		self.longDescription="you are standing in an elevator"
		self.keywords=["in"]
		self.append(self.exitDoor)

	def on_look(self, event):
		panel = self.generate_panel()
		contents = self.list_contents(event.viewer)
		text = "%s\n\n%s\n%s" % (self.longDescription, panel, contents)
		self.sendEvent(evt.TextMessage(text), event.viewer)

	def generate_panel(self):
		panel="A panel by the door reads:\n"
		floors = self.floors.keys()
		floors.sort()
		floors.reverse()
		for key in floors:
			if self.onFloor==key:
				panel+="\t%s*\n" % key
			else:
				panel+="\t%s\n" % key
		return panel

	def buildFloors(self, floors):
		self.doors={}
		self.floors = floors

		for floor, room in self.floors.items():
			door = ElevatorDoor(self, "elevator")
			room.append(door)
			room.append(CallButton(self,floor))
			button=CallButton(self, floor)
			button.isHidden=True
			self.append(button)
			self.doors[floor]=door

		self.arrive(floors.keys()[0])

	# "Call" should not be confused with "__call__()"
	def call(self,floor):
		if floor==self.onFloor:
			self.openDoor()
			return
		if floor not in self.que:
			for door in self.doors.values():
				door.open_state(False)

			self.que.append(floor)

	def arrive(self,floor):
		self.onFloor=floor
		self.exitDoor.exitsTo=self.floors[floor]
		self.exitDoor.pair(self.doors[floor])
		self.sendEvent(evt.TextMessage("arrived %s." % floor), self.channel)
		self.openDoor()

	def openDoor(self):
		self.exitDoor.open_state(True)

	def closeDoor(self):
		self.exitDoor.open_state(False)

	def aiHook(self):
		if len(self.que):
			self.arrive(self.que.pop())
