#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import watcher
import event, data
import uidata
import camerafuncs
import correlator
import peakfinder
import calibrationclient
import Numeric
import time
import threading
import presets
import copy
import EM

class DriftManager(watcher.Watcher):
	eventinputs = watcher.Watcher.eventinputs + [event.DriftDetectedEvent, event.AcquisitionImagePublishEvent, event.NeedTargetShiftEvent] + EM.EMClient.eventinputs
	eventoutputs = watcher.Watcher.eventoutputs + [event.DriftDoneEvent, event.ImageTargetShiftPublishEvent, event.ChangePresetEvent] + EM.EMClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		watchfor = [event.DriftDetectedEvent, event.AcquisitionImagePublishEvent]
		watcher.Watcher.__init__(self, id, session, managerlocation, watchfor, **kwargs)

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)
		self.pixsizeclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.presetsclient = presets.PresetsClient(self)
		self.addEventInput(event.NeedTargetShiftEvent, self.handleNeedShift)

		self.references = {}
		self.abortevent = threading.Event()

		self.defineUserInterface()
		self.start()

	def handleNeedShift(self, ev):
		imageid = ev['imageid']
		for key,value in self.references.items():
			imid = value['imageid']
			if imid == imageid:
				im = value['image']
				shift = self.calcShift(im)
				self.references[key]['shift'] = shift
				self.publishImageShifts(requested=True)
				break
		self.confirmEvent(ev)

	def calcShift(self, im):
		## go through preset manager to ensure we follow the right
		## cycle
		pname = im['preset']['name']
		self.logger.info('Preset name %s' % pname)
		self.presetsclient.toScope(pname)

		## set the original state of the image
		emdata = im['scope']
		newemdata = self.fixEM(emdata)
		camdata = im['camera']
		self.emclient.setScope(newemdata)
		self.emclient.setCamera(camdata)

		## acquire new image
		newim = self.acquireImage()

		self.logger.info('Old image, image shift %s, stage position %s'
									% (im['scope']['image shift'], im['scope']['stage position']))
		self.logger.info('New image, image shift %s, stage position %s'
						% (newim['scope']['image shift'], newim['scope']['stage position']))

		## do correlation
		self.correlator.insertImage(im['image'])
		self.correlator.insertImage(newim['image'])
		pc = self.correlator.phaseCorrelate()
		peak = self.peakfinder.subpixelPeak(newimage=pc)
		rows,cols = self.peak2shift(peak, pc.shape)
		self.logger.info('rows %s, columns %s' % (rows, cols))
		return {'rows':rows,'columns':cols}

	def processData(self, newdata):
		self.logger.debug('processData')
		if isinstance(newdata, data.AcquisitionImageData):
			self.logger.debug('AcquisitionImageData')
			self.processImageData(newdata)
		if isinstance(newdata, data.DriftDetectedData):
			self.logger.debug('DriftDetectedData')
			self.monitorDrift(newdata)

	def processImageData(self, imagedata):
		'''
		This should update a dictionary of most recent acquisitions
		For now, this is keyed on the node id from where the image
		came.  So we are keeping track of the lastest acquisition
		from each node.
		'''
		label = imagedata['label']
		imageid = imagedata.dbid
		self.references[label] = {'imageid': imageid, 'image': imagedata, 'shift': {}}

	def uiMonitorDrift(self):
		self.cam.uiApplyAsNeeded()
		## calls monitorDrift in a new thread
		t = threading.Thread(target=self.monitorDrift)
		t.setDaemon(1)
		t.start()

	def fixEM(self, emdata):
		'''
		setting scope not necessary because we don't expect to
		have moved anywhere.
		'''
		emcopy = data.ScopeEMData(initializer=emdata)
		## do not set stage
		emcopy['stage position'] = None
		## do not set focus
		emcopy['focus'] = None
		return emcopy

	def monitorDrift(self, driftdata=None):
		self.logger.info('DriftManager monitoring drift...')
		if driftdata is not None:
			## use driftdata to set up scope and camera
			scopedata = driftdata['scope']
			scopedata = self.fixEM(scopedata)
			cameradata = driftdata['camera']
			self.emclient.setScope(scopedata)
			self.emclient.setCamera(cameradata)
			mag = scopedata['magnification']
		else:
			## use current state
			mag = self.emclient.getScope()['magnification']

		## acquire images, measure drift
		self.abortevent.clear()
		self.acquireLoop(mag)

		## publish ImageTargetShiftData
		self.logger.info('DriftManager publishing image shifts...')
		self.publishImageShifts(requested=False)

		## DriftDoneEvent
		## only output if this was called from another node
		if driftdata is not None:
			self.logger.info('DriftManager sending DriftDoneEvent...')
			ev = event.DriftDoneEvent()
			self.outputEvent(ev)
		self.logger.info('DriftManager done monitoring drift')

	def publishImageShifts(self, requested=False):
		if requested:
			self.logger.info('Publishing requested image shifts...')
		else:
			self.logger.info('Publishing image shifts...')
		to_publish = {}
		for value in self.references.values():
			if not requested:
				value['shift'] = {}
			to_publish[value['imageid']] = value['shift']
		self.logger.info('to publish %s' % to_publish)
		dat = data.ImageTargetShiftData(shifts=to_publish,
																		requested=requested)
		self.publish(dat, pubevent=True)

	def acquireImage(self):
		imagedata = self.cam.acquireCameraImageData()
		self.im.set(imagedata['image'])
		return imagedata

	def acquireLoop(self, mag):

		## acquire first image
		imagedata = self.acquireImage()
		numdata = imagedata['image']
		t0 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)
		pixsize = self.pixsizeclient.retrievePixelSize(mag)
		self.logger.info('Pixel size at %sx is %s' % (mag, pixsize))

		## ensure that loop executes once
		current_drift = self.threshold.get() + 1.0
		while current_drift > self.threshold.get():
			## wait for interval
			time.sleep(self.pausetime.get())

			## acquire next image
			imagedata = self.acquireImage()
			numdata = imagedata['image']
			binning = imagedata['camera']['binning']['x']
			t1 = imagedata['scope']['system time']
			self.correlator.insertImage(numdata)

			## do correlation
			pc = self.correlator.phaseCorrelate()
			peak = self.peakfinder.subpixelPeak(newimage=pc)
			rows,cols = self.peak2shift(peak, pc.shape)
			dist = Numeric.hypot(rows,cols)
			self.logger.info('Pixels drifted %s' % dist)

			## calculate drift 
			meters = dist * binning * pixsize
			rowmeters = rows * binning * pixsize
			colmeters = cols * binning * pixsize
			# rely on system time of EM node
			seconds = t1 - t0
			current_drift = meters / seconds
			self.logger.info('Drift rate: %.4e' % (current_drift,))
			self.driftvalue.set(current_drift)

			d = data.DriftData(rows=rows, cols=cols, interval=seconds, rowmeters=rowmeters, colmeters=colmeters)
			self.publish(d, database=True, dbforce=True)

			## t0 becomes t1 and t1 will be reset for next image
			t0 = t1

			## check for abort
			if self.abortevent.isSet():
				return 'aborted'

		return 'success'

	def abort(self):
		self.abortevent.set()

	def getMag(self):
		mag = self.emclient.getScope()['magnification']
		return mag

	def peak2shift(self, peak, shape):
		shift = list(peak)
		half = shape[0] / 2, shape[1] / 2
		if peak[0] > half[0]:
			shift[0] = peak[0] - shape[0]
		if peak[1] > half[1]:
			shift[1] = peak[1] - shape[1]
		return tuple(shift)

	def uiMeasureDrift(self):
		## configure camera
		self.cam.uiApplyAsNeeded()
		mag = self.getMag()
		pixsize = self.pixsizeclient.retrievePixelSize(mag)
		self.logger.info('Pixel size %s' % (pixsize,))

		## acquire first image
		imagedata = self.acquireImage()
		numdata = imagedata['image']
		t0 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)

		# pause
		time.sleep(self.pausetime.get())
		
		## acquire next image
		imagedata = self.acquireImage()
		numdata = imagedata['image']
		t1 = imagedata['scope']['system time']
		self.correlator.insertImage(numdata)

		## do correlation
		pc = self.correlator.phaseCorrelate()
		peak = self.peakfinder.subpixelPeak(newimage=pc)
		rows,cols = self.peak2shift(peak, pc.shape)
		dist = Numeric.hypot(rows,cols)

		## calculate drift 
		meters = dist * pixsize
		self.logger.info('Pixel distance %s, (%s meters)' % (dist, meters))
		# rely on system time of EM node
		seconds = t1 - t0
		self.logger.info('Seconds %s' % seconds)
		current_drift = meters / seconds
		self.logger.info('Drift rate: %.4f' % (current_drift,))
		self.driftvalue.set(current_drift)

	def targetsToDatabase(self):
		for target in self.targetlist:
			self.publish(target, database=True)

	def defineUserInterface(self):
		watcher.Watcher.defineUserInterface(self)
		# turn on data queue by default
		self.uidataqueueflag.set(False)

		self.threshold = uidata.Float('Threshold (m)', 2e-10, 'rw', persist=True)
		self.pausetime = uidata.Float('Pause Time (s)', 2.0, 'rw', persist=True)
		abortmeth = uidata.Method('Abort', self.abort)

		camconfig = self.cam.uiSetupContainer()
		measuremeth = uidata.Method('Measure Drift Once', self.uiMeasureDrift)
		monitormeth = uidata.Method('Monitor Drift', self.uiMonitorDrift)
		self.driftvalue = uidata.Float('Drift Rate', 0.0, 'r')
		
		self.im = uidata.Image('Drift Image', None, 'r')

		#subcont = uidata.Container('Sub')
		#subcont.addObjects((self.threshold,))

		container = uidata.LargeContainer('Drift Manager')
		container.addObjects((abortmeth, self.threshold,self.pausetime,camconfig, measuremeth, monitormeth, self.driftvalue, self.im))
		self.uicontainer.addObject(container)
