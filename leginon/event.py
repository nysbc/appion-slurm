## defines the Event and EventHandler classes

import leginonobject
import clientpush
import data
import datahandler


class Event(data.Data):
	def __init__(self, content=None):
		data.Data.__init__(self, content)


class EventClient(clientpush.Client):
	def __init__(self, hostname, port):
		clientpush.Client.__init__(self, hostname, port)

	def push(self, event):
		if isinstance(event, Event):
			clientpush.Client.push(self, event)
		else:
			raise InvalidEventError('event must be Event instance')


class EventServer(clientpush.Server):
	def __init__(self):
		clientpush.Server.__init__(self, datahandler.DataBinder)

	def bind(self, eventclass, func):
		if issubclass(eventclass, Event):
			self.datahandler.setBinding(eventclass, func)
		else:
			raise InvalidEventError('eventclass must be Event subclass')


class EventHandler(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.server = EventServer()
		self.port = self.server.location()['datatcp port']
		self.clients = {}
		self.distmap = {}
		self.registry = {'outputs':[], 'inputs':[]}

	def addClient(self, newid, hostname, port):
		self.clients[newid] = EventClient(hostname, port)

	def delClient(self, newid):
		if newid in self.clients:
			del self.clients[newid]

	def addInput(self, eventclass, func):
		self.server.bind(eventclass, func)
		if eventclass not in self.registry['inputs']:
			self.registry['inputs'].append(eventclass)

	def delInput(self, eventclass):
		self.server.bind(eventclass, None)
		if eventclass in self.registry['inputs']:
			self.registry['inputs'].remove(eventclass)

	def addOutput(self, eventclass):
		if eventclass not in self.registry['outputs']:
			self.registry['outputs'].append(eventclass)
		
	def delOutput(self, eventclass):
		if eventclass in self.registry['outputs']:
			self.registry['outputs'].remove(eventclass)

	def addDistmap(self, eventclass, from_node=None, to_node=None):
		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def distribute(self, event):
		'''push event to eventclients based on event class and source'''
		#print 'DIST', event.origin
		eventclass = event.__class__
		from_node = event.origin['id']
		done = []
		for distclass,fromnodes in self.distmap.items():
		  if issubclass(eventclass, distclass):
		    for fromnode in (from_node, None):
		      if fromnode in fromnodes:
		        for to_node in fromnodes[from_node]:
		          if to_node:
			    if to_node not in done:
		              self.push(to_node, event)
		              done.append(to_node)
			      print 'DISTRIBUTE:  %s, %s' % (to_node,event)
		          else:
			    for to_node in self.handler.clients:
			      if to_node not in done:
		                self.push(to_node, event)
		                done.append(to_node)
			        print 'DISTRIBUTE:  %s, %s' % (to_node,event)

	def push(self, client, event):
		self.clients[client].push(event)

## Standard Event Types:
##
## Event
##	NodeReadyEvent
##		NodeLauncherReadyEvent
##	PublishEvent
##	ControlEvent
##		NumericControlEvent
##		LaunchNodeEvent
##
##

### generated by a node to notify manager that node is ready
class NodeReadyEvent(Event):
	'Event sent by a node to the manager to indicate a successful init'
	def __init__(self):
		Event.__init__(self, content=None)

class NodeLauncherReadyEvent(NodeReadyEvent):
	'Event sent by a node to the manager to indicate a successful init'
	def __init__(self):
		NodeReadyEvent.__init__(self)

class PublishEvent(Event):
	'Event indicating data was published'
	def __init__(self, dataid):
		Event.__init__(self, content=dataid)


class ControlEvent(Event):
	'Event that passes a value with it'
	def __init__(self, content):
		Event.__init__(self, content)


class NumericControlEvent(ControlEvent):
	'ControlEvent that allows only numeric values to be passed'
	def __init__(self, content):
		allowedtypes = (int, long, float)
		if type(content) in allowedtypes:
			ControlEvent.__init__(self, content)
		else:
			raise TypeError('NumericControlEvent content type must be in %s' % allowedtypes)

class LaunchNodeEvent(ControlEvent):
	'ControlEvent sent to a NodeLauncher specifying a node to launch'
	def __init__(self, nodeid, nodeclass, ):
		nodeinfo = {'id':nodeid, 'class':nodeclass}
		Event.__init__(self, content=nodeinfo)



###########################################################
## event related exceptions

class InvalidEventError(TypeError):
	pass

