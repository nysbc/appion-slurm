import leginonconfig
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

# Ignore the following keys right now
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
	'holder type',
	'holder status',
	'stage status',
#	'screen position'
)

def unique(s):
	n = len(s)
	if n == 0:
		return []

	u = {}
	try:
		for x in s:
			u[x] = 1
	except TypeError:
		del u  # move on to the next method
	else:
		return u.keys()

	try:
		t = list(s)
		t.sort()
	except TypeError:
		del t  # move on to the next method
	else:
		assert n > 0
		last = t[0]
		lasti = i = 1
		while i < n:
			if t[i] != last:
				t[lasti] = last = t[i]
				lasti += 1
			i += 1
		return t[:lasti]

	u = []
	for x in s:
		if x not in u:
			u.append(x)
	return u

class DataHandler(node.DataHandler):
	def query(self, id):
		emkey = id[0]
		print 'EM query: acquiring state lock'
		self.node.statelock.acquire()
		print 'EM query: state lock acquired'
		done_event = threading.Event()
		print 'EM query: putting in request for %s' % str([emkey])
		self.node.queue.put(Request(done_event, [emkey],
																self.node.externalstatusupdate.get()))
		print 'EM query: waiting on request'
		done_event.wait()
		print 'EM query: got request'
		stuff = self.node.state
		print 'EM query: creating data, (keys = %s)' % str(stuff.keys())

		if emkey == 'scope':
			result = data.ScopeEMData(id=('scope',))
			result.friendly_update(stuff)
		elif emkey in ('camera', 'camera no image data'):
			result = data.CameraEMData(id=('camera',))
			# this is a fix for the bigger problem of always 
			# setting defocus
			result.friendly_update(stuff)
		elif emkey == 'all em':
			result = data.AllEMData(id=('all em',))
			result.friendly_update(stuff)
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
			# this converts Data to a dict, and deletes items
			# that are None.  This saves us some time because
			# queueHandler will not only setEM, but getEM on
			# all keys we give it, even if values are None
			d = idata.toDict(noNone=True)
			# also delete these, which are not understood by
			# pyScope, or are read only
			for key in ('id','session','system time','em host', 'image data'):
				try:
					del d[key]
				except KeyError:
					pass

			self.node.queue.put(Request(done_event, d,
																	self.node.externalstatusupdate.get()))
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
	def __init__(self, ievent, value, updatestatus=True):
		self.event = ievent
		self.value = value
		self.updatestatus = updatestatus

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
			scope = (leginonconfig.TEM, leginonconfig.TEM)
		if camera is None:
			camera = (leginonconfig.CCD, leginonconfig.CCD)

		node.Node.__init__(self, id, session, nodelocations,
												datahandler=DataHandler, **kwargs)

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

		self.uistate = {}
		self.defineUserInterface()
		self.state = self.getEM(self.uiscopedict.keys() + self.uicameradict.keys())
		self.uiUpdate()

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

	def prunedUpdate(self, source, destination):
		'''
		this replaces update() in cases where we don't want to update
		certain keys
		'''
		for key in source:
			if key not in prunekeys:
				destination[key] = source[key]

	def getEM(self, withkeys=[], withoutkeys=[], updatestatus=True):
		if updatestatus:
			self.uiSetStatus('Getting parameters', 5)
			self.uiSetStatus('Acquiring lock for parameter query', 10)
		self.lock.acquire()
		if updatestatus:
			self.uiSetStatus('Lock acquired, processing request', 15)

		result = {}

		if not withkeys and withoutkeys:
			withkeys = ['all em']

		for key in withkeys:
			if key == 'scope':
				withkeys.remove(key)
				withkeys += self.scope.keys()
			elif key == 'camera':
				withkeys.remove(key)
				withkeys += self.camera.keys()
			elif key == 'camera no image data':
				withkeys.remove(key)
				keys = self.camera.keys()
				try:
					keys.remove('image data')
				except ValueError:
					pass
				withkeys += keys
			elif key == 'all em':
				withkeys.remove(key)
				withkeys += self.scope.keys()
				withkeys += self.camera.keys()

		withkeys = unique(withkeys)

		for key in withoutkeys:
			if key == 'scope':
				withoutkeys.remove(key)
				withoutkeys += self.scope.keys()
			elif key == 'camera':
				withoutkeys.remove(key)
				withoutkeys += self.camera.keys()
			elif key == 'camera no image data':
				withoutkeys.remove(key)
				keys = self.camera.keys()
				try:
					keys.remove('image data')
				except KeyError:
					pass
				withoutkeys += keys
			elif key == 'all em':
				withoutkeys.remove(key)
				withoutkeys += self.scope.keys()
				withoutkeys += self.camera.keys()

		if updatestatus:
			self.uiSetStatus('Refining request', 20)

		for key in withoutkeys:
			try:
				withkeys.remove(key)
			except ValueError:
				pass

		if updatestatus:
			self.uiSetStatus('Sending request to instrument', 25)
			if withkeys:
				percent = 25
				increment = (90-percent)/len(withkeys)

		scopekeys = self.scope.keys()
		camerakeys = self.camera.keys()
		for key in withkeys:
			if updatestatus:
				self.uiSetStatus('Requesting ' + key + ' value', None)
			if key in scopekeys:
				result[key] = self.scope[key]
			elif key in camerakeys:
				result[key] = self.camera[key]
			else:
				pass
			if updatestatus:
				percent += increment
				self.uiSetStatus('Value of ' + key + ' acquired', percent)

		result['system time'] = time.time()
		result['em host'] = self.location()['hostname']

		if updatestatus:
			self.uiSetStatus('Releasing Lock', 90)
		self.lock.release()
		if updatestatus:
			self.uiSetStatus('Lock Released', 95)
			self.uiSetStatus('Parameter get completed', 100)
			self.uiSetStatus('', 0)
		return result

	def sortEMdict(self, emdict):
		'''
		sort items in em dict for proper setting order
		'''
		olddict = copy.deepcopy(emdict)
		newdict = strictdict.OrderedDict()

		# The order of the following keys matters
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

	def setEM(self, emstate, updatestatus=True):
		if updatestatus:
			self.uiSetStatus('Setting parameters', 5)
			self.uiSetStatus('Acquiring lock for parameter modifications', 10)
		self.lock.acquire()
		if updatestatus:
			self.uiSetStatus('Lock acquired, processing request', 15)

		# order the items in emstate
		ordered = self.sortEMdict(emstate)

		if updatestatus:
			self.uiSetStatus('Request processed, sending to instrument', 20)
			if ordered:
				percent = 20
				increment = (90-percent)/len(ordered.keys())

		scopekeys = self.scope.keys()
		camerakeys = self.camera.keys()
		for emkey, emvalue in ordered.items():
			if updatestatus:
				self.uiSetStatus('Requesting modification of ' + emkey, None)
			if emvalue is not None:
				if emkey in scopekeys:
					try:
						self.scope[emkey] = emvalue
					except:	
						print "failed to set '%s' to %s" % (emkey, emvalue)
						self.printException()
				elif emkey in camerakeys:
					try:
						self.camera[emkey] = emvalue
					except:	
						#print "failed to set '%s' to" % EMkey, EMstate[EMkey]
						self.printException()
			if updatestatus:
				percent += increment
				self.uiSetStatus('Value of ' + emkey + ' modified', percent)

		if updatestatus:
			self.uiSetStatus('Releasing Lock', 90)
		self.lock.release()
		if updatestatus:
			self.uiSetStatus('Lock Released', 95)
			self.uiSetStatus('Parameter modifications completed', 100)
			self.uiSetStatus('', 0)

	# needs to have statelock locked
	def uiUpdate(self):
		self.uiSetDictData(self.uiscopedict, self.state)
		self.uistate.update(self.uiGetDictData(self.uiscopedict))
		self.uiSetDictData(self.uicameradict, self.state)
		self.uistate.update(self.uiGetDictData(self.uicameradict))

	def uiSetState(self, setdict):
		request = {}
		for key in setdict:
			if key not in self.uistate or self.uistate[key] != setdict[key]:
				request[key] = setdict[key]

		self.uiSetUIStatus(None, 30)

		if not request:
			return

		self.uiSetUIStatus('Acquiring lock', 40)
		self.statelock.acquire()
		self.uiSetUIStatus('Lock acquired', 50)
		done_event = threading.Event()
		self.uiSetUIStatus('Queuing microscope parameter change request', 60)
		self.queue.put(Request(done_event, request))
		self.uiSetUIStatus('Microscope parameter change request queued', 70)
		done_event.wait()
		self.uiSetUIStatus('Microscope parameter change request completed', 80)
		self.statelock.release()
		self.uiSetUIStatus('Lock released', 90)

	def queueHandler(self):
		while True:
			request = self.queue.get()
			if isinstance(request.value, dict):
				self.setEM(request.value, updatestatus=request.updatestatus)
				self.state = self.getEM(request.value.keys(),
																updatestatus=request.updatestatus)
			else:
				self.state = self.getEM(request.value,
																updatestatus=request.updatestatus)
			self.uiUpdate()
			request.event.set()

	def uiUnlock(self):
		self.locknodeid = None
		self.nodelock.release()

	def uiResetDefocus(self):
		self.uiSetUIStatus('Reseting defocus', 10)
		self.uiSetState({'reset defocus': 1})
		self.uiSetUIStatus('Defocus reset', 90)
		self.uiSetUIStatus('Requesting defocus value', 95)
		self.statelock.acquire()
		done_event = threading.Event()
		self.queue.put(Request(done_event, ['defocus']))
		done_event.wait()
		self.statelock.release()
		self.uiSetUIStatus('Defocus reset request completed', 100)
		self.uiSetUIStatus('', 0)

	def uiToggleMainScreen(self):
		self.uiSetUIStatus('Toggling mainscreen', 10)
		try:
			uiscreenposition = self.uiscopedict['screen position'].get()
		except KeyError:
			return
		if uiscreenposition == 'down':
			self.uiSetUIStatus('Putting mainscreen up', 15)
			self.uiSetState({'screen position': 'up'})
		elif uiscreenposition == 'up':
			self.uiSetUIStatus('Putting mainscreen down', 15)
			self.uiSetState({'screen position': 'down'})
		self.uiSetUIStatus('Main screen toggled', 100)
		self.uiSetUIStatus('', 0)

	def uiRefreshScope(self):
		self.uiSetUIStatus('Getting microscope parameters', 10)
		self.uiSetUIStatus('Acquiring lock', 20)
		self.statelock.acquire()
		done_event = threading.Event()
		request = self.uiGetDictData(self.uiscopedict).keys()
		self.uiSetUIStatus('Queuing microscope parameter query request', 30)
		self.queue.put(Request(done_event, request))
		self.uiSetUIStatus('Microscope parameter query request queued', 40)
		done_event.wait()
		self.uiSetUIStatus('Microscope parameter query request completed', 80)
		self.statelock.release()
		self.uiSetUIStatus('Lock released', 90)
		self.uiSetUIStatus('Refreshed microscope parameters', 100)
		self.uiSetUIStatus('', 0)

	def uiSetUIStatus(self, message, percent):
		if hasattr(self, 'uiprogresslabel') and hasattr(self, 'uiprogress'):
			if message is not None:
				self.uiprogresslabel.set(message)
			if percent is not None:
				self.uiprogress.set(percent)
#			if percent is not None or message is not None:
#				time.sleep(0.25)

	def uiSetStatus(self, message, percent):
		if hasattr(self, 'progresslabel') and hasattr(self, 'progress'):
			if message is not None:
				self.progresslabel.set(message)
			if percent is not None:
				self.progress.set(percent)
#			if percent is not None or message is not None:
#				time.sleep(0.25)

	def uiSetScope(self):
		self.uiSetUIStatus('Setting microscope parameters', 10)
		scopedict = self.uiGetDictData(self.uiscopedict)
		self.uiSetUIStatus(None, 20)
		updatedstate = self.uiSetState(scopedict)
		self.uiSetUIStatus('Microscope parameter change completed', 90)
		self.uiSetUIStatus('', 0)

	def uiSetCamera(self):
		self.uiSetUIStatus('Setting camera parameters', 10)
		cameradict = self.uiGetDictData(self.uicameradict)
		self.uiSetUIStatus(None, 20)
		updatedstate = self.uiSetState(cameradict)
		self.uiSetUIStatus('Camera parameter change completed', 90)
		self.uiSetUIStatus('', 0)

	def uiGetDictData(self, uidict):
		uidictdata = {}
		for key, value in uidict.items():
			if isinstance(value, uidata.Data):
				uidictdata[key] = value.get()
#			elif isinstance(value, dict):
			else:
				uidictdata[key] = self.uiGetDictData(value)
		return uidictdata

	def uiSetDictData(self, uidict, dictdata):
		for key, value in uidict.items():
			if key in dictdata:
				if isinstance(value, uidata.Data):
					value.set(dictdata[key])
#				elif isinstance(value, dict):
				else:
					self.uiSetDictData(value, dictdata[key])

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.progresslabel = uidata.String('State', '', 'r')
		self.progress = uidata.Progress('', 0)
		self.externalstatusupdate = uidata.Boolean(
																					'Update status for external changes',
																					False, 'rw')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObject(self.progresslabel)
		statuscontainer.addObject(self.progress)
		statuscontainer.addObject(self.externalstatusupdate)

		self.uiprogresslabel = uidata.String('State', '', 'r')
		self.uiprogress = uidata.Progress('', 0)
		uistatuscontainer = uidata.Container('User Request Status')
		uistatuscontainer.addObject(self.uiprogresslabel)
		uistatuscontainer.addObject(self.uiprogress)

		self.uiscopedict = {}
		self.uiscopedict['magnification'] = uidata.Float('Magnification', 0.0, 'rw')
		self.uiscopedict['intensity'] = uidata.Float('Intensity', 0.0, 'rw')
		self.uiscopedict['defocus'] = uidata.Float('Defocus', 0.0, 'rw')
		self.uiscopedict['spot size'] = uidata.Integer('Spot Size', 0, 'rw')
		self.uiscopedict['screen position'] = uidata.String('Main Screen', '', 'r')

		togglemainscreen = uidata.Method('Toggle Main Screen',
																			self.uiToggleMainScreen)
		resetdefocus = uidata.Method('Reset Defocus', self.uiResetDefocus)

		self.uiscopedict['stage position'] = {}
		self.uiscopedict['stage position']['x'] = uidata.Float('x', 0.0, 'rw')
		self.uiscopedict['stage position']['y'] = uidata.Float('y', 0.0, 'rw')
		self.uiscopedict['stage position']['z'] = uidata.Float('z', 0.0, 'rw')
		self.uiscopedict['stage position']['a'] = uidata.Float('a', 0.0, 'rw')
#		self.uiscopedict['stage position']['b'] = uidata.Float('b', 0.0, 'rw')
		stagepositioncontainer = uidata.Container('Stage Position')
		stagepositioncontainer.addObjects((self.uiscopedict['stage position']['x'],
																			self.uiscopedict['stage position']['y'],
																			self.uiscopedict['stage position']['z'],
																			self.uiscopedict['stage position']['a']))
#																			self.uiscopedict['stage position']['b']))

		self.uiscopedict['image shift'] = {}
		self.uiscopedict['image shift']['x'] = uidata.Float('x', 0.0, 'rw')
		self.uiscopedict['image shift']['y'] = uidata.Float('y', 0.0, 'rw')
		imageshiftcontainer = uidata.Container('Image Shift')
		imageshiftcontainer.addObjects((self.uiscopedict['image shift']['x'],
																		self.uiscopedict['image shift']['y']))

		self.uiscopedict['beam tilt'] = {}
		self.uiscopedict['beam tilt']['x'] = uidata.Float('x', 0.0, 'rw')
		self.uiscopedict['beam tilt']['y'] = uidata.Float('y', 0.0, 'rw')
		beamtiltcontainer = uidata.Container('Beam Tilt')
		beamtiltcontainer.addObjects((self.uiscopedict['beam tilt']['x'],
																		self.uiscopedict['beam tilt']['y']))

		self.uiscopedict['beam shift'] = {}
		self.uiscopedict['beam shift']['x'] = uidata.Float('x', 0.0, 'rw')
		self.uiscopedict['beam shift']['y'] = uidata.Float('y', 0.0, 'rw')
		beamshiftcontainer = uidata.Container('Beam Shift')
		beamshiftcontainer.addObjects((self.uiscopedict['beam shift']['x'],
																		self.uiscopedict['beam shift']['y']))

		scopeparameterscontainer = uidata.Container('Parameters')

		for item in self.uiscopedict.values():
			if isinstance(item, uidata.Object):
				scopeparameterscontainer.addObject(item)

		scopeparameterscontainer.addObject(togglemainscreen)
		scopeparameterscontainer.addObject(resetdefocus)
		scopeparameterscontainer.addObject(stagepositioncontainer)
		scopeparameterscontainer.addObject(imageshiftcontainer)
		scopeparameterscontainer.addObject(beamtiltcontainer)
		scopeparameterscontainer.addObject(beamshiftcontainer)

		scopecontainer = uidata.MediumContainer('Microscope')
		scopecontainer.addObject(scopeparameterscontainer)

		refreshscope = uidata.Method('Refresh', self.uiRefreshScope)
		setscope = uidata.Method('Set', self.uiSetScope)
		scopecontainer.addObject(refreshscope)
		scopecontainer.addObject(setscope)

		self.uicameradict = {}
		self.uicameradict['exposure time'] = uidata.Integer('Exposure Time',0,'rw')

		self.uicameradict['dimension'] = {}
		self.uicameradict['dimension']['x'] = uidata.Integer('x', 0, 'rw')
		self.uicameradict['dimension']['y'] = uidata.Integer('y', 0, 'rw')
		dimensioncontainer = uidata.Container('Dimension')
		dimensioncontainer.addObjects((self.uicameradict['dimension']['x'],
																		self.uicameradict['dimension']['y']))

		self.uicameradict['offset'] = {}
		self.uicameradict['offset']['x'] = uidata.Integer('x', 0, 'rw')
		self.uicameradict['offset']['y'] = uidata.Integer('y', 0, 'rw')
		offsetcontainer = uidata.Container('Offset')
		offsetcontainer.addObjects((self.uicameradict['offset']['x'],
																self.uicameradict['offset']['y']))

		self.uicameradict['binning'] = {}
		self.uicameradict['binning']['x'] = uidata.Integer('x', 0, 'rw')
		self.uicameradict['binning']['y'] = uidata.Integer('y', 0, 'rw')
		binningcontainer = uidata.Container('Binning')
		binningcontainer.addObjects((self.uicameradict['binning']['x'],
																	self.uicameradict['binning']['y']))

		cameraparameterscontainer = uidata.Container('Parameters')

		for item in self.uicameradict.values():
			if isinstance(item, uidata.Object):
				cameraparameterscontainer.addObject(item)

		cameraparameterscontainer.addObject(dimensioncontainer)
		cameraparameterscontainer.addObject(offsetcontainer)
		cameraparameterscontainer.addObject(binningcontainer)

		cameracontainer = uidata.MediumContainer('Camera')
		cameracontainer.addObject(cameraparameterscontainer)

		setcamera = uidata.Method('Set', self.uiSetCamera)
		cameracontainer.addObject(setcamera)

#		self.statelock.acquire()
#		self.uiUpdate()
#		self.statelock.release()

		container = uidata.MediumContainer('EM')
		container.addObject(statuscontainer)
		container.addObject(uistatuscontainer)
		container.addObjects((scopecontainer, cameracontainer))
		self.uiserver.addObject(container)

