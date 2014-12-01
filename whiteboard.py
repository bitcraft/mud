
import mudclasses2 as mc
import event as evt

class Whiteboard(mc.MudObject):
	def __init__(self):
		mc.MudObject.__init__(self)
		self.text=""
		self.name="whiteboard"
		self.keywords=["board"]

	def on_write(self,*arg):
		text=" ".join(arg)
		self.text+="%s\n" % text

	def on_erase(self):
		self.text=""

	# bug: on_read doesn twork
	def on_read(self):
		return self.evt_look()

	def on_look(self,event):
		if len(self.text)>0:
			r = self.text
		else:
			r = "empty"

		response=evt.TextMessage(r)
		self.sendEvent(response, event.sender)
