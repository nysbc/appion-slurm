#!/usr/bin/env python
import leginonobject
import copy
import weakref

_id2obj_dict = weakref.WeakValueDictionary()

class Server(leginonobject.LeginonObject):
	def __init__(self, id, dh):
		leginonobject.LeginonObject.__init__(self, id)
		self.datahandler = dh
		self.pythonid = id(self)
		_id2obj_dict[self.pythonid] = self

	def start(self):
		pass

	def location(self):
		loc = leginonobject.LeginonObject.location(self)
		loc['local server python ID'] = self.pythonid
		return loc

class Client(leginonobject.LeginonObject):
	def __init__(self, id, location):
		leginonobject.LeginonObject.__init__(self, id)
		self.serverlocation = location

	def push(self, idata):
		#print "pushing locally..."
		obj = _id2obj_dict[self.serverlocation['local server python ID']]
		if obj is None:
			raise IOError # err...its sort of an IOError
		else:
			return obj.datahandler.insert(copy.deepcopy(idata))

	def pull(self, id):
		#print "pulling locally..."
		obj = _id2obj_dict[self.serverlocation['local server python ID']]
		if obj is None:
			raise IOError
		else:
			return copy.deepcopy(obj.datahandler.query(id))

if __name__ == '__main__':
	pass
