# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/remotecall.py,v $
# $Revision: 1.11 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-23 21:17:32 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import inspect
import datatransport
import types
import threading

class LockingError(Exception):
	pass

class LockError(LockingError):
	pass

class UnlockError(LockingError):
	pass

class NotLockedError(LockingError):
	pass

class TimeoutError(LockingError):
	pass

class Request(object):
	def __init__(self, origin, node, name, attributename, type,
								args=(), kwargs={}):
		self.origin = origin
		self.node = node
		self.name = name
		self.attributename = attributename
		self.type = type
		self.args = args
		self.kwargs = kwargs

class MultiRequest(Request):
	def __init__(self, origin, node, name, attributenames, types,
								args=None, kwargs=None):
		n = len(attributenames)
		if len(types) != n:
			raise ValueError
		if args is None:
			args = [()]*len(attributenames)
		if kwargs is None:
			kwargs = [{}]*len(attributenames)
		if len(args) != n or len(kwargs) != n:
			raise ValueError
		Request.__init__(self, origin, node, name, attributenames, types,
											args, kwargs)

class Object(object):
	def __init__(self):
		self._register()

	def _query(self):
		interface = {}
		for key in dir(self):
			try:
				value = getattr(self, key)
			except Exception, e:
				continue
			if isinstance(value, types.MethodType):
				if key[:1] != '_':
					if key[:3] == 'get':
						name = key[3:]
						if name:
							if name not in interface:
								interface[name] = {}
							interface[name]['r'] = value
					elif key[:3] == 'set':
						name = key[3:]
						if name:
							if name not in interface:
								interface[name] = {}
							interface[name]['w'] = value
					if key not in interface:
						interface[key] = {}
					interface[key]['method'] = value
		return interface

	def _register(self):
		self._types = [c.__name__ for c in inspect.getmro(self.__class__)]
		self._interface = self._query()
		self._description = self._getDescription()

	def _execute(self, origin, name, type, args=(), kwargs={}):
		try:
			result = self._interface[name][type](*args, **kwargs)
		except KeyError:
			result = TypeError('invalid execution name')
		except Exception, result:
			pass
		return result

	def _getDescription(self):
		description = {}
		for name, methods in self._interface.items():
			description[name] = {}
			for method in methods:
				description[name][method] = True
		return description

	def _handleRequest(self, request):
		if isinstance(request, MultiRequest):
			results = []
			for i, attributename in enumerate(request.attributename):
				try:
					results.append(self._execute(request.origin,
																				attributename,
																				request.type[i],
																				request.args[i],
																				request.kwargs[i]))
				except Exception, e:
					results.append(e)
			return results
		else:
			return self._execute(request.origin,
														request.attributename,
														request.type,
														request.args,
														request.kwargs)

class Locker(Object):
	def __init__(self):
		self.locknode = None
		self._lock = threading.Condition()
		Object.__init__(self)

	def _execute(self, origin, name, type, args=(), kwargs={}):
		# handle lock and unlock directly
		self._lock.acquire()
		if self.locknode != origin:
			if self.locknode is not None:
				self._lock.wait()
			self.locknode = origin
		if name in ['lock', 'unlock']:
			result = None
		else:
			result = Object._execute(self, origin, name, type, args, kwargs)
		if name != 'lock':
			self.locknode = None
			self._lock.notify()
		self._lock.release()
		return result

	def lock(self):
		self._lock.acquire()
		if self.locknode != self.node.name:
			if self.locknode is not None:
				self._lock.wait()
			self.locknode = self.node.name
		self._lock.release()

	def unlock(self):
		self._lock.acquire()
		if self.locknode != self.node.name:
			self._lock.release()
			raise UnlockError
		else:
			self.locknode = None
		self._lock.notify()
		self._lock.release()

class ObjectCallProxy(object):
	def __init__(self, call, args):
		self.call = call
		self.args = args

	def __call__(self, *args, **kwargs):
		args = self.args + (args, kwargs)
		self.call(*args)

class ObjectProxy(object):
	def __init__(self, objectservice, nodename, name):
		self.__objectservice = objectservice
		self.__nodename = nodename
		self.__name = name

	def __getattr__(self, name):
		if name == 'multiCall':
			return object.__getattr__(self, name)
		d, t = self.__objectservice.descriptions[self.__nodename][self.__name]
		try:
			description = d[name]
		except KeyError:
			raise ValueError('no method %s in object description' % name)
		if 'method' in description:
			args = (self.__nodename, self.__name, name, 'method')
			return ObjectCallProxy(self.__objectservice._call, args)
		elif 'r' in description:
			return self.__objectservice._call(self.__nodename, self.__name, name, 'r')
		else:
			raise TypeError('attribute %s is not readable' % name)

	def hasAttribute(self, name):
		d, t = self.__objectservice.descriptions[self.__nodename][self.__name]
		if name in d:
			return True
		return False

	def getAttributeTypes(self, name):
		d, t = self.__objectservice.descriptions[self.__nodename][self.__name]
		try:
			return d[name].keys()
		except KeyError:
			return []

	def multiCall(self, names, types, args=None, kwargs=None):
		args = (self.__nodename, self.__name, names, types, args, kwargs)
		return self.__objectservice._multiCall(*args)

#class ObjectService(Object):
class ObjectService(Locker):
	def __init__(self, node):
		self.descriptions = {}
		self.clients = {}
		self.node = node
		self.addhandlers = []
		self.removehandlers = []
		#Object.__init__(self)
		Locker.__init__(self)
		self._addObject('Object Service', self)

	def _addDescriptionHandler(self, add=None, remove=None):
		self.lock()
		if add is not None:
			self.addhandlers.append(add)
			for args in self._getDescriptions():
				add(*args)
		if remove is not None:
			self.removehandlers.append(remove)
		self.unlock()

	def _removeDescriptionHandler(self, add=None, remove=None):
		self.lock()
		if add is not None:
			self.addhandlers.remove(add)
		if remove is not None:
			self.removehandlers.remove(remove)
		self.unlock()

	def _addHandler(self, nodename, name, description, types):
		for handler in self.addhandlers:
			handler(nodename, name, description, types)

	def _removeHandler(self, nodename, name):
		for handler in self.removehandlers:
			handler(nodename, name)

	def _getDescriptions(self):
		args = []
		for nodename in self.descriptions:
			for name in self.descriptions[nodename]:
				args.append((nodename, name) + self.descriptions[nodename][name])
		return args

	def addDescription(self, nodename, name, description, types, location):
		if (nodename not in self.clients or
				self.clients[nodename].serverlocation != location):
			self.clients[nodename] = datatransport.Client(location,
																										self.node.clientlogger)

		if nodename not in self.descriptions:
			self.descriptions[nodename] = {}
		self.descriptions[nodename][name] = (description, types)
		self._addHandler(nodename, name, description, types)

	def removeDescription(self, nodename, name):
		self._removeDescription(self, nodename, name)

	def _removeDescription(self, nodename, name):
		try:
			del self.descriptions[nodename][name]
			self._removeHandler(nodename, name)
		except KeyError:
			pass

	def addDescriptions(self, descriptions):
		for description in descriptions:
			self.addDescription(*description)

	def removeDescriptions(self, descriptions):
		for description in descriptions:
			self.removeDescription(*description)
		
	def _removeDescriptions(self, descriptions):
		for description in descriptions:
			self._removeDescription(*description)

	def removeNode(self, nodename):
		try:
			descriptions = []
			for name in self.descriptions[nodename]:
				descriptions.append((nodename, name))
			self._removeDescriptions(descriptions)
		except KeyError:
			pass
		try:
			del self.clients[nodename]
		except KeyError:
			pass

	def _call(self, node, name, attributename, type, args=(), kwargs={}):
		request = Request(self.node.name, node, name, attributename, type,
											args, kwargs)
		try:
			return self.clients[node].send(request)
		except KeyError:
			raise ValueError('no client for node %s' % node)

	def _multiCall(self, node, name, attributenames, types,
									args=None, kwargs=None):
		request = MultiRequest(self.node.name, node, name, attributenames, types,
														args, kwargs)
		try:
			return self.clients[node].send(request)
		except KeyError:
			raise ValueError('no client for node %s' % node)

	def _addObject(self, name, interface):
		self.node.databinder.addRemoteCallObject(self.node.name, name, interface)

	def _removeObject(self, name):
		self.node.databinder.removeRemoteCallObject(self.node.name, name)

	def getObjectProxy(self, nodename, name):
		return ObjectProxy(self, nodename, name)

	def getObjectsByType(self, type):
		objects = []
		for nodename in self.descriptions:
			for name in self.descriptions[nodename]:
				description, types = self.descriptions[nodename][name]
				if type in types:
					objects.append((nodename, name))
		return objects

	def _exit(self):
		pass

class NodeObjectService(ObjectService):
	def __init__(self, node):
		self.node = node
		ObjectService.__init__(self, node)

	def _addObject(self, name, interface):
		if 'Manager' not in self.clients:
			self.clients['Manager'] = self.node.managerclient
		ObjectService._addObject(self, name, interface)
		location = self.node.location()['data binder']
		args = (self.node.name, name, interface._description,
						interface._types, location)
		self._call('Manager', 'Object Service', 'addDescription', 'method', args)

	def _removeObject(self, name):
		args = (self.node.name, name)
		self._call('Manager', 'Object Service', 'removeDescription', 'method', args)
		ObjectService._removeObject(self, name)

	def _exit(self):
		args = (self.node.name,)
		try:
			self._call('Manager', 'Object Service', 'removeNode', 'method', args)
		except datatransport.TransportError:
			pass

class ManagerObjectService(ObjectService):
	def __init__(self, manager):
		ObjectService.__init__(self, manager)

	def addDescription(self, nodename, name, description, types, location):
		ObjectService.addDescription(self, nodename, name, description, types,
																	location)
		args = (nodename, name, description, types, location)
		descriptions = []
		for nn in self.descriptions:
			if nn == nodename:
				continue
			location = self.node.nodelocations[nodename]['location']
			for n in self.descriptions[nn]:
				d, t = self.descriptions[nn][n]
				if 'ObjectService' in t:
					if 'ObjectService' not in types:
						self._call(nn, n, 'addDescription', 'method', args)
				else:
					descriptions.append((nn, n, d, t, location['data binder']))
		if descriptions and 'ObjectService' in types:
			args = (descriptions,)
			self._call(nodename, name, 'addDescriptions', 'method', args)

	def removeDescription(self, nodename, name):
		args = (nodename, name)
		for nn in self.descriptions:
			if nn == nodename:
				continue
			for n in self.descriptions[nn]:
				d, t = self.descriptions[nn][n]
				if 'ObjectService' in t:
					self._call(nn, n, 'removeDescription', 'method', args)
		ObjectService.removeDescription(self, nodename, name)

	def removeNode(self, nodename):
		args = (nodename,)
		for nn in self.descriptions:
			if nn == nodename:
				continue
			for n in self.descriptions[nn]:
				d, t = self.descriptions[nn][n]
				if 'ObjectService' in t:
					self._call(nn, n, 'removeNode', 'method', args)
		ObjectService.removeNode(self, nodename)

