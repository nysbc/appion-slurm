import xmlrpcnode
import dataserver
import urllib
import cPickle
import location
import registry
import event

class Node(xmlrpcnode.xmlrpcserver):
	def __init__(self, manageraddress):
		xmlrpcnode.xmlrpcserver.__init__(self)

		self.datahandler = DataHandler(self)

		# it might be better to change NodeLocation to take
		# and instance of Location as part of the constructor
		# or the whole thing could be a dictionary
		self.location = location.NodeLocation(self.location.hostname,
							self.location.rpcport,
							self.location.pid,
							self.datahandler.port)

		self.init_events()

		if manageraddress:
			self.managerlocation = location.Location(manageraddress[0],
							manageraddress[1], None)
			self.id = self.register()

	def init_events(self):
		raise NotImplementedError()

	def __del__(self):
		self.manager_close()

	def register(self):

		meths = self.EXPORT_methods()

		eventinfo = {}
		eventinfo['inputs'] = self.events.inputmap.keys()
		eventinfo['outputs'] = self.events.outputs

		locpickle = cPickle.dumps(self.location)
		eventpickle = cPickle.dumps(eventinfo)

		nodeinfo = {'location pickle' : locpickle, 'methods' : 'meths', 'events pickle': eventpickle}

		id = self.managerlocation.rpc('addNode', (nodeinfo,))
		return id

	def manager_close(self):
		print 'manager_close'
		try:
			self.managerlocation.rpc('deleteNode', (self.id,))
		except:
			pass

	def announce(self, eventinst):
		### this sends an outgoing event to the manager
		eventrepr = eventinst.xmlrpc_repr()
		print 'ANNOUNCEeventrepr', eventrepr
		args = (self.id, eventrepr)
		print 'ARGS', args
		ret = self.managerlocation.rpc('notify', args)
		print 'return', ret

	def EXPORT_event_dispatch(self, eventrepr):
		### this decides what to do with incoming events

		eventpickle = eventrepr['pickle']
		eventinst = cPickle.loads(eventpickle)
		eventclass = eventinst.__class__
		meth = self.events.inputmap[eventclass]
		apply(meth, (event,))

	def publish(self, dataid, data):
		self.datahandler.put(dataid, data)

	def research(self, dataid):
		data = self.datahandler.get(dataid)
		return data

class DataHandler(object):
	def __init__(self, mynode):
		self.mynode = mynode
		self.mydata = {}
		self.dataserver = dataserver.DataServer(self)
		self.port = self.dataserver.port

	def __getattr__(self, name):
		if name in self.mydata:
			return self.mydata[name]
		else:
			return None

	def put(self, dataid, data):
		### do something with the data
		###   to DB
		###   to file
		###   to server

		## this makes it accessable to the http server

		self.mydata[dataid] = data


		## notify manager of the new location
		location = self.mynode.location.getURI() + '/' + dataid
		args = (dataid, location)
		self.mynode.managerlocation.rpc('addLocation', args)

	def get(self, dataid):
		args = (dataid,)
		location = self.mynode.managerlocation.rpc('locate', args)
		urlfile = urllib.urlopen(location)
		data = cPickle.load(urlfile)

		return data

class Manager(xmlrpcnode.xmlrpcserver):
	def __init__(self, *args, **kwargs):
		xmlrpcnode.xmlrpcserver.__init__(self)
		self.registry = registry.Registry()
		self.distributor = event.EventDistributor(self.registry)
		self.locations = {}

	def EXPORT_addNode(self, node):

		id = self.registry.addEntry(
			registry.NodeRegistryEntry(node['methods'],
				cPickle.loads(node['events pickle']),
				cPickle.loads(node['location pickle'])))

		print 'node %s has been added' % id
		#self.print_nodes()
		return id

	def EXPORT_deleteNode(self, id):
		self.registry.delEntry(id)
		print 'node %s has been deleted' % id

	def EXPORT_nodes(self):
		nodes = self.registry.xmlrpc_repr()
		print 'XMLRPCRPER', nodes
		return nodes

	def EXPORT_notify(self, sourceid, eventrepr):
		eventinst = cPickle.loads(eventrepr['pickle'])
		print 'received %s from node %s' % (eventrepr['class'],sourceid)
		self.distributor.insert(sourceid, eventinst)
		return 'OK'


	def EXPORT_bindings(self):
		return self.distributor.bindings.xmlrpc_repr()

	def EXPORT_addBinding(self, sourceid, targetid, eventclassrepr):
		eventclass = cPickle.loads(eventclassrepr['pickle'])
		self.distributor.addBinding(sourceid, targetid, eventclass)

	def EXPORT_deleteBinding(self, sourceid, targetid, eventclassrepr):
		eventclass = cPickle.loads(eventclassrepr['pickle'])
		self.distributor.deleteBinding(sourceid, targetid, eventclass)

	def EXPORT_locate(self, dataid):
		######### I think this is replaced by the registry stuff
		## find the uri of the data referenced by dataid

		location = ''
		try:
			location = self.locations[dataid][0]
		except KeyError:
			pass
		except ValueError:
			pass
		return location

	def EXPORT_addLocation(self, dataid, location):
		##### same here
		if dataid not in self.locations:
			self.locations[dataid] = []
		self.locations[dataid].append(location)
		print 'new data location: ', dataid, location

	def EXPORT_deleteLocation(self, dataid, location):
		###### same here
		try:
			self.locations[dataid].remove(location)
		except KeyError:
			pass
		except ValueError:
			pass

if __name__ == '__main__':
	pass

