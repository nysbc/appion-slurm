import acquisition
import node, data
import calibrationclient
import camerafuncs
import uidata
import threading
import event

class Focuser(acquisition.Acquisition):
	eventinputs = acquisition.Acquisition.eventinputs+[event.DriftDoneEvent]
	eventoutputs = acquisition.Acquisition.eventoutputs+[event.DriftDetectedEvent]
	def __init__(self, id, sesison, nodelocations, **kwargs):
		self.focus_methods = {
			'None': self.correctNone,
			'Stage Z': self.correctZ,
			'Defocus': self.correctDefocus
		}

		self.cam = camerafuncs.CameraFuncs(self)


		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.abortfail = threading.Event()
		acquisition.Acquisition.__init__(self, id, sesison, nodelocations, targetclass=data.FocusTargetData, **kwargs)

	def acquire(self, preset, target=None, trial=False):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we do autofocus
		'''
		info = {}
		self.abortfail.clear()
		btilt = self.btilt.get()
		pub = self.publishimages.get()

		## Need to melt only once per target, event though
		## this method may be called multiple times on the same
		## target.
		## To be sure, we flag a target as having been melted.
		## This is only safe if we can be sure that we don't
		## use different copies of the same target each time.
		melt_time = self.melt.get()
		if melt_time and not target['pre_exposure']:
			melt_time_ms = int(round(melt_time * 1000))
			camstate = self.cam.currentCameraEMData()
			current_exptime = camstate['exposure time']
			camstate['exposure time'] = melt_time_ms
			camstate = self.cam.currentCameraEMData(camstate)

			print 'Melting for %s seconds' % (melt_time,)
			self.cam.acquireCameraImageData()
			print 'Done melting, resetting exposure time'

			camstate['exposure time'] = current_exptime
			camstate = self.cam.currentCameraEMData(camstate)
			target['pre_exposure'] = True

		if self.drifton.get():
			driftthresh = self.driftthresh.get()
		else:
			driftthresh = None

		try:
			correction = self.btcalclient.measureDefocusStig(btilt, pub, drift_threshold=driftthresh, image_callback=self.ui_image.set)
		except calibrationclient.Abort:
			print 'measureDefocusStig was aborted'
			return 'abort'
		except calibrationclient.Drifting:
			self.driftDetected()
			return 'repeat'

		print 'MEASURED DEFOCUS AND STIG', correction
		defoc = correction['defocus']
		stigx = correction['stigx']
		stigy = correction['stigy']
		min = correction['min']

		info.update({'defocus':defoc, 'stigx':stigx, 'stigy':stigy, 'min':min})

		### validate defocus correction
		# possibly use min (value minimized during least square fit)
		#   mag: 50000, tilt: 0.02, defoc: 30e-6
		#     84230 was bad
		#   mag: 50000, tilt: 0.02, defoc: 25e-6
		#     5705 was bad
		#   mag: 50000, tilt: 0.02, defoc: 22e-6
		#     4928 was maybe
		#   mag: 50000, tilt: 0.02, defoc: 20e-6
		#     3135 was maybe
		#   mag: 50000, tilt: 0.02, defoc: 18e-6
		#     1955 was maybe
		#   mag: 50000, tilt: 0.02, defoc: 14e-6
		#      582 was good
		# for now, assum it is valid
		validdefocus = 1

		### validate stig correction
		# stig is only valid for large defocus
		if validdefocus and (abs(defoc) > self.stigfocthresh.get()):
			validstig = True
		else:
			validstig = False
		
		if validstig and self.stigcorrection.get():
			print 'Stig correction'
			self.correctStig(stigx, stigy)
			info['stig correction'] = 1
		else:
			info['stig correction'] = 0

		if validdefocus:
			print 'Defocus correction'
			try:
				focustype = self.focustype.getSelectedValue()
				focusmethod = self.focus_methods[focustype]
			except (IndexError, KeyError):
				print 'no method selected for correcting defocus'
			else:
				info['defocus correction'] = focustype
				focusmethod(defoc)

		## add target to this sometime
		frd = data.FocuserResultData(initializer=info)
		self.publish(frd, database=True)

		return 'ok'

	def correctStig(self, deltax, deltay):
		stig = self.researchByDataID(('stigmator',))
		stig['stigmator']['objective']['x'] += deltax
		stig['stigmator']['objective']['y'] += deltay
		emdata = data.ScopeEMData(id=('scope',), initializer=stig)
		print 'correcting stig by %s,%s' % (deltax,deltay)
		self.publishRemote(emdata)

	def correctDefocus(self, delta):
		defocus = self.researchByDataID(('defocus',))
		defocus['defocus'] += delta
		defocus['reset defocus'] = 1
		emdata = data.ScopeEMData(id=('scope',), initializer=defocus)
		print 'correcting defocus by %s' % (delta,)
		self.publishRemote(emdata)

	def correctZ(self, delta):
		stage = self.researchByDataID(('stage position',))
		newz = stage['stage position']['z'] + delta
		newstage = {'stage position': {'z': newz }}
		newstage['reset defocus'] = 1
		emdata = data.ScopeEMData(id=('scope',), initializer=newstage)
		print 'correcting stage Z by %s' % (delta,)
		self.publishRemote(emdata)

	def correctNone(self, delta):
		print 'not applying defocus correction'

	def uiTest(self):
		self.acquire(None)

	def uiAbortFailure(self):
		self.btcalclient.abortevent.set()

	def defineUserInterface(self):
		acquisition.Acquisition.defineUserInterface(self)

		self.melt = uidata.Float('Melt Time (s) CHANGE ME!!!!!!', 0.0, 'rw', persist=True)

		self.drifton = uidata.Boolean('Check Drift', True, 'rw', persist=True)
		self.driftthresh = uidata.Float('Drift Threshold (pixels)', 2, 'rw', persist=True)

		self.btilt = uidata.Float('Beam Tilt', 0.02, 'rw', persist=True)
		self.stigfocthresh = uidata.Float('Stig Threshold', 1e-6, 'rw', persist=True)


		focustypes = self.focus_methods.keys()
		focustypes.sort()
		self.focustype = uidata.SingleSelectFromList('Focus Correction Type', focustypes, 0, persist=True)
		self.stigcorrection = uidata.Boolean('Stigmator Correction', False, 'rw', persist=True)
		self.publishimages = uidata.Boolean('Publish Images', True, 'rw', persist=True)
		abortfailmethod = uidata.Method('Abort With Failure', self.uiAbortFailure)
		testmethod = uidata.Method('Test Autofocus (broken)', self.uiTest)
		container = uidata.MediumContainer('Focuser')
		container.addObjects((self.melt, self.drifton, self.driftthresh, self.btilt, self.stigfocthresh, self.focustype, self.stigcorrection, self.publishimages, abortfailmethod, testmethod))
		self.uiserver.addObject(container)

