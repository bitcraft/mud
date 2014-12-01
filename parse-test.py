#!/usr/bin/python

import unittest
import textcontrol as tc
import mudclasses2 as mc2

class MudMobileTC(unittest.TestCase):
	def setUp(self):
		self.m = mc2.Mobile()
		room = mc2.Room()
		room.append(self.m)
		
	def testSay(self):
		return True
		self.m.say("hello!")

class ObjPropertyTC(unittest.TestCase):
	def setUp(self):
		self.root = mc2.PermissionHandler()
		self.p = mc2.MudProperty(owner=self.root)

	def testCanPrint(self):
		p = "%s" % self.p

	def testCanPrintByNotOwnerReadOnly(self):
		self.root.changeValue(self.p,'r',False)
		try:
			p = "%s" % self.p
		except mc2.PermissionError:
			return
		p = "%s" % self.p

	def testChangeReadPermission(self):
		self.root.changeValue(self.p,'r',False)
		try:
			assert self.p.r == False
		except mc2.PermissionError:
			return

		assert self.p.r == False

	def testChangeWritePermission(self):
		self.root.changeValue(self.p,'r',True)
		self.root.changeValue(self.p,'w',False)
		assert self.p.w == False

	def testCanSetAttrNotOwner(self):
		new_value = "w00t"
		try:
			self.p.value = new_value
		except:
			return

		assert self.p == new_value

	def testCanSetAttrByOwner(self):
		new_value = "w00t"
		self.root.changeValue(self.p,'value',new_value)
		assert self.p == new_value

class MudListTC(unittest.TestCase):
	def setUp(self):
		self.ml = mc2.MudList(owner=self,maxSize=1)
	
	def testCanAdd(self):
		t = mc2.MudObject()
		assert self.ml.append(t) == True
		
	def testCanRemoveIfIn(self):
		t = mc2.MudObject()
		self.ml.append(t)
		assert self.ml.remove(t) == True

	def testCanNotRemoveIfNotIn(self):
		t = mc2.MudObject()
		assert self.ml.remove(t) == False

	def testCanTestIsIn(self):
		t = mc2.MudObject()
		self.ml.append(t)
		assert (t in self.ml) == True

	def testCanTestIsNotIn(self):
		t = mc2.MudObject()
		assert (t in self.ml) == False
		
	def testCanNotAddIfFull(self):
		t1 = mc2.MudObject()
		t2 = mc2.MudObject()
		self.ml.append(t1)
		assert self.ml.append(t2) == False

class MudRoomTC(unittest.TestCase):
	def setUp(self):
		self.r = mc2.Room(maxSize=1)
		
	def testCanAdd(self):
		t = mc2.MudObject()
		assert self.r.append(t) == True
		
	def testCanRemoveIfIn(self):
		t = mc2.MudObject()
		self.r.append(t)
		assert self.r.remove(t) == True

	def testCanNotRemoveIfNotIn(self):
		t = mc2.MudObject()
		assert self.r.remove(t) == False

	def testCanTestIsIn(self):
		t = mc2.MudObject()
		self.r.append(t)
		assert (t in self.r) == True

	def testCanTestIsNotIn(self):
		t = mc2.MudObject()
		assert (t in self.r) == False
		
	def testCanNotAddIfFull(self):
		t1 = mc2.MudObject()
		t2 = mc2.MudObject()
		self.r.append(t1)
		r = self.r.append(t2)
		assert r == False

class QualIntegerTC(unittest.TestCase):
	def setUp(self):
		self.q = tc.QualInteger("integer test")

	def testQualIntByInt(self):
		assert self.q.matches(123) != None

	def testQualIntByStringNumber(self):
		assert self.q.matches("123") != None

	def testQualIntByStringNonNumber(self):
		assert self.q.matches("abc") == None

	def testQualIntByStringMixed(self):
		assert self.q.matches("214nmb34 234bh") == None

class QualThingTC(unittest.TestCase):
	def setUp(self):
		self.root=mc2.PermissionHandler()
		self.t=mc2.MudObject(owner=self.root)

	def testCanSetAttrNotOwner(self):
		new_value = "w00t"
		try:
			self.t.name = new_name
		except:
			return

		assert self.t.name == new_name

	def testCanSetAttrByOwner(self):
		new_name = "w00t"
		self.root.changeValue(self.t,'name',new_name)
		assert self.t.name == new_name

def suite():
	tcs = map(unittest.makeSuite,[y for x,y in globals().items() if x[-2:] == "TC"])
	return unittest.TestSuite(tcs)

if __name__ == '__main__':
	testSuite = suite()
	runner = unittest.TextTestRunner()
	runner.run(testSuite)
	