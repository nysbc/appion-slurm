
import threading
import time
from leginon import leginondata
import calibrationclient
import event
import instrument
import reference
import gui.wx.ReferenceTimer
import gui.wx.AlignZLP

class ReferenceTimer(reference.Reference):
	panelclass = gui.wx.ReferenceTimer.ReferenceTimerPanel
	settingsclass = leginondata.ReferenceTimerSettingsData
	eventinputs = reference.Reference.eventinputs
	eventoutputs = reference.Reference.eventoutputs

	defaultsettings = reference.Reference.defaultsettings
	defaultsettings.update (
		{'interval time': 0.0}
	)
	requestdata = None

	def __init__(self, *args, **kwargs):
		super(ReferenceTimer,self).__init__(*args, **kwargs)
		#self.last_processed = time.time()

		if self.__class__ == ReferenceTimer:
			self.start()

	def _processRequest(self, request_data):
		# This is the function that would be different between Timer and Counter
		interval_time = self.settings['interval time']
		if interval_time is not None and self.last_processed is not None:
			interval = time.time() - self.last_processed
			if interval < interval_time:
				message = '%d second(s) since last request, ignoring request'
				self.logger.info(message % interval)
				return
		self.moveAndExecute(request_data)
		self.last_processed = time.time()

	def uiResetTimer(self):
		self.logger.info('Reset Request Process Timer')
		self.last_processed = time.time()


class AlignZeroLossPeak(ReferenceTimer):
	settingsclass = leginondata.AlignZLPSettingsData
	# defaultsettings are not the same as the parent class.  Therefore redefined.
	defaultsettings = {
		'bypass': True,
		'move type': 'stage position',
		'pause time': 3.0,
		'interval time': 900.0,
		'check preset': '',
		'threshold': 0.0,
	}
	eventinputs = ReferenceTimer.eventinputs + [event.AlignZeroLossPeakPublishEvent]
	panelclass = gui.wx.AlignZLP.AlignZeroLossPeakPanel
	requestdata = leginondata.AlignZeroLossPeakData

	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.AlignZeroLossPeakPublishEvent]
		ReferenceTimer.__init__(self, *args, **kwargs)
		self.start()

	def moveAndExecute(self, request_data):
		check_preset_name = self.settings['check preset']
		self.checkpreset = self.presets_client.getPresetFromDB(check_preset_name)
		preset_name = request_data['preset']
		pause_time = self.settings['pause time']
		try:
			self.moveToTarget(preset_name)
		except Exception, e:
			self.logger.error('Error moving to target, %s' % e)
			return

		if pause_time is not None:
			time.sleep(pause_time)
		if self.settings['threshold'] >= 0.1:
			try:
				self.moveToTarget(check_preset_name)
			except Exception, e:
				self.logger.error('Error moving to target, %s' % e)
				return
			need_align = self.checkShift()
			self.moveToTarget(preset_name)
			
		else:
			need_align = True
		if need_align:
			try:
				self.execute(request_data)
			except Exception, e:
				self.logger.error('Error executing request, %s' % e)
				return
	
	def execute(self, request_data=None):
		ccd_camera = self.instrument.ccdcamera
		if not ccd_camera.EnergyFiltered:
			self.logger.warning('No energy filter on this instrument.')
			return
		before_shift = None
		after_shift = None
		try:
			if not ccd_camera.EnergyFilter:
				self.logger.warning('Energy filtering is not enabled.')
				return
			before_shift = ccd_camera.getInternalEnergyShift()
			m = 'Energy filter internal shift: %g.' % before_shift
			self.logger.info(m)
		except AttributeError:
			m = 'Energy filter methods are not available on this instrument.'
			self.logger.warning(m)
		except Exception, e:
			s = 'Energy internal shift query failed: %s.'
			self.logger.error(s % e)

		try:
			if not ccd_camera.EnergyFilter:
				self.logger.warning('Energy filtering is not enabled.')
				return
			ccd_camera.alignEnergyFilterZeroLossPeak()
			m = 'Energy filter zero loss peak aligned.'
			self.logger.info(m)
		except AttributeError:
			m = 'Energy filter methods are not available on this instrument.'
			self.logger.warning(m)
		except Exception, e:
			s = 'Energy filter align zero loss peak failed: %s.'
			self.logger.error(s % e)

		try:
			if not ccd_camera.EnergyFilter:
				self.logger.warning('Energy filtering is not enabled.')
				return
			after_shift = ccd_camera.getInternalEnergyShift()
			m = 'Energy filter internal shift: %g.' % after_shift
			self.logger.info(m)
		except AttributeError:
			m = 'Energy filter methods are not available on this instrument.'
			self.logger.warning(m)
		except Exception, e:
			s = 'Energy internal shift query failed: %s.'
			self.logger.error(s % e)

		shift_data = leginondata.InternalEnergyShiftData(session=self.session, before=before_shift, after=after_shift)
		self.publish(shift_data, database=True, dbforce=True)
		if self.settings['threshold'] >= 0.1:
			self.resetZeroLossCheck()

	def checkShift(self):
		ccd_camera = self.instrument.ccdcamera
		if not ccd_camera.EnergyFiltered:
			self.logger.warning('No energy filter on this instrument.')
			return False
		imagedata = self.acquireCorrectedCameraImageData()
		image = imagedata['image']
		stageposition = imagedata['scope']['stage position']
		lastresetq = leginondata.ZeroLossCheckData(session=self.session, preset=self.checkpreset)
		result = lastresetq.query(readimages=False, results=1)

		if result is None:
			self.publishZeroLossCheck(image)
		else:
			if result:
				# compare the standard deviation with that from last alignment
				if result[0]['std'] * self.settings['threshold'] > image.std():
					self.logger.info('Energe filter slit has not shifted significantly')
					return False
		return True

	def publishZeroLossCheck(self,image):
		resetdata = leginondata.ZeroLossCheckData()
		resetdata['session'] = self.session
		resetdata['reference'] = self.reference_target
		resetdata['preset'] = self.checkpreset
		resetdata['mean'] = image.mean()
		self.logger.info('published zero-loss check data')
		resetdata['std'] = image.std()
		self.publish(resetdata, database=True, dbforce=True)

	def resetZeroLossCheck(self):
		try:
			self.moveToTarget(self.checkpreset['name'])
		except Exception, e:
			self.logger.error('Error moving to target, %s' % e)
			return
		self.logger.info('reset zero-loss check data')
		imagedata = self.acquireCorrectedCameraImageData()
		stageposition = imagedata['scope']['stage position']
		image = imagedata['image']
		self.publishZeroLossCheck(image)

class MeasureDose(ReferenceTimer):
	defaultsettings = {
		'move type': 'stage position',
		'pause time': 3.0,
		'interval time': 900.0,
		'bypass': True,
	}
	# relay measure does events
	eventinputs = ReferenceTimer.eventinputs + [event.MeasureDosePublishEvent]
	eventoutputs = ReferenceTimer.eventoutputs
	panelclass = gui.wx.ReferenceTimer.MeasureDosePanel
	requestdata = leginondata.MeasureDoseData
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.MeasureDosePublishEvent]
		ReferenceTimer.__init__(self, *args, **kwargs)
		self.start()

	# override move to measure dose...
	def moveToTarget(self, preset_name):
		em_target_data = self.getEMTargetData(preset_name)

		self.publish(em_target_data, database=True)

		self.presets_client.measureDose(preset_name, em_target_data)

	def execute(self, request_data=None):
		if request_data:
			preset_name = request_data['preset']
			preset = self.presets_client.getPresetByName(preset_name)
		else:
			preset = self.presets_client.getCurrentPreset()
			if preset is None:
				return
			preset_name = preset['name']
		if preset['dose'] is None:
			self.logger.warning('Failed measuring dose for preset \'%s\'' % preset_name)
			return
		dose = preset['dose']/1e20
		exposure_time = preset['exposure time']/1000.0
		try:
			dose_rate = dose/exposure_time
		except ZeroDivisionError:
			dose_rate = 0
		self.logger.info('Measured dose for preset \'%s\'' % preset_name)
		self.logger.info('Dose: %g e-/A^2, rate: %g e-/A^2/s' % (dose, dose_rate))

