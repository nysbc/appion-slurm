import node
import datahandler
import scopedict
import cameradict
import threading
import data
import event
import sys
import imp
import cPickle
import dbdatakeeper
import strictdict
import copy
import time
import uidata
import Queue

if sys.platform == 'win32':
	sys.coinit_flags = 0
	import pythoncom

#class DataHandler(datahandler.DataBinder):
class DataHandler(node.DataHandler):
	def query(self, id):
		emkey = id[0]
		print 'EM query: acquiring state lock'
		self.node.statelock.acquire()
		print 'EM query: state lock acquired'
		done_event = threading.Event()
		print 'EM query: putting in request for %s' % str([emkey])
		self.node.queue.put(Request(done_event, [emkey]))
		print 'EM query: waiting on request'
		done_event.wait()
		print 'EM query: got request'
		stuff = self.node.state
		print 'EM query: creating data, (keys = %s)' % str(stuff.keys())

		if emkey == 'scope':
			result = data.ScopeEMData(id=('scope',), initializer=stuff)
		elif emkey in ('camera', 'camera no image data'):
			result = data.CameraEMData(id=('camera',))
			# this is a fix for the bigger problem of always 
			# setting defocus
			result.friendly_update(stuff)
		elif emkey == 'all em':
			result = data.AllEMData(id=('all em',), initializer=stuff)
		else:
			### could be either CameraEMData or ScopeEMData
			newid = self.ID()
			trydatascope = data.ScopeEMData(id=('scope',))
			trydatacamera = data.CameraEMData(id=('camera',))
			for trydata in (trydatascope, trydatacamera):
				try:
					trydata.update(stuff)
					result = trydata
					break
				except KeyError:
					result = None

		print 'EM query: UI update'
		self.node.uiUpdate()
		print 'EM query: data created, releaseing statelock'
		self.node.statelock.release()
		print 'EM query: returning'
		return result

	def insert(self, idata):
		print 'EM insert: testing instance of EMData'
		if isinstance(idata, data.EMData):
			print 'EM insert: is instance of EMData, acquiring statelock'
			#print idata['id'][:-1], 'attempting to set EM'
			self.node.statelock.acquire()
			print 'EM insert: statelock acquired'
			done_event = threading.Event()
			#self.node.queue.put(Request(done_event, idata['em']))
			print 'EM insert: requesting set (idata = %s)' % str(idata)
			self.node.queue.put(Request(done_event, idata))
			print 'EM insert: waiting for request to complete'
			done_event.wait()
			print 'EM insert: updating UI'
			self.node.uiUpdate()
			print 'EM insert: releasing state lock'
			self.node.statelock.release()
		else:
			node.DataHandler.insert(self, idata)

		print 'EM insert: done'

class Request(object):
	def __init__(self, ievent, value):
		self.event = ievent
		self.value = value

class EM(node.Node):
	eventinputs = node.Node.eventinputs + [event.LockEvent, event.UnlockEvent]
	eventoutputs = node.Node.eventoutputs + [event.ListPublishEvent]
	def __init__(self, id, session, nodelocations,
								scope = None, camera = None, **kwargs):
		# internal
		self.lock = threading.Lock()
		# external
		self.nodelock = threading.Lock()
		self.locknodeid = None

		# should have preferences
		if scope is None:
			scope = ('tecnai', 'tecnai')
		if camera is None:
			camera = ('gatan', 'gatan')

		node.Node.__init__(self, id, session, nodelocations, datahandler=DataHandler, **kwargs)

		self.addEventInput(event.LockEvent, self.doLock)
		self.addEventInput(event.UnlockEvent, self.doUnlock)

		self.queue = Queue.Queue()
		self.state = {}
		self.statelock = threading.RLock()

		self.handlerthread = threading.Thread(name='EM handler thread',
																					target=self.handler,
																					args=(scope, camera))
		self.handlerthread.setDaemon(1)
		self.handlerthread.start()


		self.start()

	def handler(self, scope, camera):
		self.scope = self.camera = {}
		if scope[0]:
			fp, pathname, description = imp.find_module(scope[0])
			scopemodule = imp.load_module(scope[0], fp, pathname, description)
			if scope[1]:
				self.scope = scopedict.factory(scopemodule.__dict__[scope[1]])()
		if camera[0]:
			fp, pathname, description = imp.find_module(camera[0])
			cameramodule = imp.load_module(camera[0], fp, pathname, description)
			if camera[1]:
				self.camera = cameradict.factory(cameramodule.__dict__[camera[1]])()

		self.addEventOutput(event.ListPublishEvent)

		ids = ['scope', 'camera', 'camera no image data', 'all em']
		ids += self.scope.keys()
		ids += self.camera.keys()
		for i in range(len(ids)):
			ids[i] = (ids[i],)

		self.uistate = self.getEM(withoutkeys=['image data'])
		self.defineUserInterface()

		e = event.ListPublishEvent(id=self.ID(), idlist=ids)
		self.outputEvent(e, wait=True)
		self.outputEvent(event.NodeInitializedEvent(id=self.ID()))

		self.queueHandler()

	def main(self):
		pass

	def exit(self):
		node.Node.exit(self)
		self.scope.exit()
		self.camera.exit()

	def doLock(self, ievent):
		print 'EM do lock'
		if ievent['id'][:-1] != self.locknodeid:
			self.nodelock.acquire()
			self.locknodeid = ievent['id'][:-1]
			print self.locknodeid, 'acquired EM lock'
		self.confirmEvent(ievent)

	def doUnlock(self, ievent):
		print 'EM do unlock'
		if ievent['id'][:-1] == self.locknodeid:
			print self.locknodeid, 'releasing EM lock'
			self.locknodeid = None
			self.nodelock.release()
		self.confirmEvent(ievent)

	### now this is handled by EMData
	def pruneEMdict(self, emdict):
		'''
		restrict access to certain scope parameters
		'''
		prunekeys = (
			'gun shift',
			'gun tilt',
			'high tension',
			'beam blank',
			'dark field mode',
			'diffraction mode',
			'low dose',
			'low dose mode',
			'screen current',
		)

		for key in prunekeys:
			try:
				del emdict[key]
			except KeyError:
				pass

	def getEM(self, withkeys=None, withoutkeys=None):
		self.lock.acquire()
		result = {}
		if withkeys is not None:
			for EMkey in withkeys:
				if EMkey in self.scope:
					try:
						result[EMkey] = self.scope[EMkey]
						## always get defocus
						result['defocus'] = self.scope['defocus']
					except:	
						print "failed to get '%s'" % EMkey
						self.printException()
				elif EMkey in self.camera:
					try:
						result[EMkey] = self.camera[EMkey]
					except:	
						print "failed to get '%s'" % EMkey
						self.printException()
				elif EMkey == 'scope':
					result.update(self.scope)
				elif EMkey == 'camera no image data':
					for camerakey in self.camera:
						if camerakey != 'image data':
							result[camerakey] = self.camera[camerakey]
				elif EMkey == 'camera':
					result.update(self.camera)
				elif EMkey == 'all em':
					result.update(self.scope)
					result.update(self.camera)
		elif withoutkeys is not None:
			if not ('scope' in withoutkeys or 'all em' in withoutkeys):
				for EMkey in self.scope:
					if not EMkey in withoutkeys:
						try:
							result[EMkey] = self.scope[EMkey]
						except:	
							print "failed to get '%s'" % EMkey
							self.printException()
				## always get defocus
				result['defocus'] = self.scope['defocus']
			if not ('camera' in withoutkeys or 'all em' in withoutkeys):
				for EMkey in self.camera:
					if not EMkey in withoutkeys:
						try:
							result[EMkey] = self.camera[EMkey]
						except:	
							print "failed to get '%s'" % EMkey
							self.printException()
		else:
			result.update(self.scope)
			result.update(self.camera)

		## getting defocus no matter what, since it changes if reset
		## defocus was called
		#result['defocus'] = self.scope['defocus']
		self.pruneEMdict(result)
		result['system time'] = time.time()

		self.lock.release()
		return result

	def sortEMdict(self, emdict):
		'''
		sort items in em dict for proper setting order
		'''
		olddict = copy.deepcopy(emdict)
		newdict = strictdict.OrderedDict()

		# I care about these, the rest don't matter
		order = (
			'magnification',
			'spot size',
			'image shift',
			'beam shift',
			'defocus',
			'reset defocus',
			'intensity',
		)
		for key in order:
			try:
				newdict[key] = olddict[key]
				del olddict[key]
			except KeyError:
				pass

		# the rest don't matter
		newdict.update(olddict)
		return newdict

	def setEM(self, emstate):
		self.lock.acquire()

		# order the items in emstate
		ordered = self.sortEMdict(emstate)

		#for emkey, emvalue in emstate.items():
		for emkey, emvalue in ordered.items():
			if emvalue is None:
				continue
			if emkey in self.scope:
				try:
					self.scope[emkey] = emvalue
				except:	
					print "failed to set '%s' to %s" % (emkey, emvalue)
					self.printException()
			elif emkey in self.camera:
				try:
					self.camera[emkey] = emvalue
				except:	
					#print "failed to set '%s' to" % EMkey, EMstate[EMkey]
					self.printException()
		self.lock.release()

	def save(self, filename):
		print "Saving state to file: %s..." % filename,
		try:
			f = file(filename, 'w')
			savestate = self.getEM(withoutkeys=['image data'])
			cPickle.dump(savestate, f)
			f.close()
		except:
			print "Error: failed to save EM state"
			raise
		else:
			print "done."
		return ''

	def load(self, filename):
		print "Loading state from file: %s..." % filename,
		try:
			f = file(filename, 'r')
			loadstate = cPickle.load(f)
			self.setEM(loadstate)
			f.close()
		except:
			print "Error: failed to load EM state"
			raise
		else:
			print "done."
		return ''

	# needs to have statelock locked
	def uiUpdate(self):
		self.uistate.update(self.state)
		try:
			del self.uistate['image data']
		except KeyError:
			pass
		self.statestruct.set(self.uistate)

	def uiCallback(self, value):
		#request = data.AllEMData()
		request = {}
		for key in value:
			if self.uistate[key] != value[key]:
				request[key] = value[key]

		#dorequest = False
		#for value in request.values():
		#	if value is not None:
		#		dorequest = True
		#if not dorequest:
		if not request:
			return value

		self.statelock.acquire()
		done_event = threading.Event()
		self.queue.put(Request(done_event, request))
		done_event.wait()
		self.uistate.update(self.state)
		try:
			del self.uistate['image data']
		except KeyError:
			pass
		self.statelock.release()
		return self.uistate

	def queueHandler(self):
		while True:
			request = self.queue.get()
			#if isinstance(request.value,data.EMData):
			if isinstance(request.value, dict):
				self.setEM(request.value)
				self.state = self.getEM(request.value.keys())
			else:
				self.state = self.getEM(request.value)
			request.event.set()

	def uiUnlock(self):
		self.locknodeid = None
		self.nodelock.release()

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		self.twostep = uidata.Boolean('Two Step Stage Move', False, 'rw', persist=True)
		self.statestruct = uidata.Struct('Instrument State', {},
																				'rw', self.uiCallback)
		self.statestruct.set(self.uistate, callback=False)
		updatemethod = uidata.Method('Update', self.uiUpdate)
		unlockmethod = uidata.Method('Unlock', self.uiUnlock)
		container = uidata.MediumContainer('EM')
		container.addObjects((self.twostep, self.statestruct, updatemethod, unlockmethod))
		self.uiserver.addObject(container)

