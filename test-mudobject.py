#!/usr/bin/python

import unittest
import mudclasses3 as mc

class ObjPropertyTC(unittest.TestCase):
	def setUp(self):
		self.root = mc.PermissionHandler()
		self.p = mc.MudProperty(owner=self.root)

	def testCanPrint(self):
		p = "%s" % self.p

	def testCanPrintByNotOwnerReadOnly(self):
		self.root.changeValue(self.p,'r',False)
		try:
			p = "%s" % self.p
		except mc.PermissionError:
			return
		p = "%s" % self.p

	def testChangeReadPermission(self):
		self.root.changeValue(self.p,'r',False)
		try:
			assert self.p.r == False
		except mc.PermissionError:
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
		self.ml = mc.MudList(owner=self,maxSize=1)

	def testCanAdd(self):
		t = mc.MudObject()
		assert self.ml.append(t) == True

	def testCanRemoveIfIn(self):
		t = mc.MudObject()
		self.ml.append(t)
		assert self.ml.remove(t) == True

	def testCanNotRemoveIfNotIn(self):
		t = mc.MudObject()
		assert self.ml.remove(t) == False

	def testCanTestIsIn(self):
		t = mc.MudObject()
		self.ml.append(t)
		assert (t in self.ml) == True

	def testCanTestIsNotIn(self):
		t = mc.MudObject()
		assert (t in self.ml) == False

	def testCanNotAddIfFull(self):
		t1 = mc.MudObject()
		t2 = mc.MudObject()
		self.ml.append(t1)
		assert self.ml.append(t2) == False

def suite():
	tcs = map(unittest.makeSuite,[y for x,y in globals().items() if x[-2:] == "TC"])
	return unittest.TestSuite(tcs)

if __name__ == '__main__':
	testSuite = suite()
	runner = unittest.TextTestRunner()
	runner.run(testSuite)
