#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
'''
'''

import calibrator
try:
	import numarray as Numeric
	import linear_algebra as LinearAlgebra
except:
	import Numeric
	import LinearAlgebra
import data
import calibrationclient
import uidata
import node
import gui.wx.BeamTiltCalibrator

class BeamTiltCalibrator(calibrator.Calibrator):
	'''
	'''
	panelclass = gui.wx.BeamTiltCalibrator.Panel
	settingsclass = data.BeamTiltCalibratorSettingsData
	defaultsettings = {
		'camera settings': None,
		'correlation type': 'cross',
		'defocus beam tilt': 0.01,
		'first defocus': -1e-6,
		'second defocus': -2e-6,
		'stig beam tilt': 0.01,
		'stig delta': 0.2,
	}

	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)

		self.defaultmeasurebeamtilt = 0.01

		self.calclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.euclient = calibrationclient.EucentricFocusClient(self)

		self.start()

	def calibrateAlignment(self, tilt_value):
		self.cam.setCameraDict(self.settings['camera settings'])

		state1 = {'beam tilt': tilt_value}
		state2 = {'beam tilt': -tilt_value}

		matdict = {}

		for axis in ('x','y'):
			self.logger.info('Measuring %s tilt' % (axis,))

			diff1 = self.calclient.measureDispDiff(axis, tilt_value, tilt_value)
			diff2 = self.calclient.measureDispDiff(axis, -tilt_value, tilt_value)

			matcol = self.calclient.eq11(diff1, diff2, 0, 0, tilt_value)
			matdict[axis] = matcol

		self.logger.info('Making matrix...')
		matrix = Numeric.zeros((2,2), Numeric.Float32)
		self.logger.info('Matrix type %s, matrix dict type %s'
											% (matrix.type(), matdict['x'].type()))
		matrix[:,0] = matdict['x']
		matrix[:,1] = matdict['y']

		## store calibration
		self.logger.info('Storing calibration...')
		mag = self.getMagnification()
		ht = self.getHighTension()
		self.calclient.storeMatrix(ht, mag, 'coma-free', matrix)
		self.logger.info('Calibration stored')
		return ''

	def calibrateDefocus(self, tilt_value, defocus1, defocus2):
		self.cam.setCameraDict(self.settings['camera settings'])
		state1 = {'defocus': defocus1}
		state2 = {'defocus': defocus2}
		matdict = {}
		for axis in ('x','y'):
			self.logger.info('Measuring %s tilt' % (axis,))
			shift1, shift2 = self.calclient.measureDisplacements(axis, tilt_value, state1, state2)
			matcol = self.calclient.eq11(shift1, shift2, defocus1, defocus2, tilt_value)
			matdict[axis] = matcol
		self.logger.info('Making matrix...')
		matrix = Numeric.zeros((2,2), Numeric.Float32)
		self.logger.info('Matrix type %s, matrix dict type %s'
											% (matrix.type(), matdict['x'].type()))

		m00 = float(matdict['x'][0])
		m10 = float(matdict['x'][1])
		m01 = float(matdict['y'][0])
		m11 = float(matdict['y'][1])
		matrix = Numeric.array([[m00,m01],[m10,m11]],Numeric.Float32)

		## store calibration
		self.logger.info('Storing calibration...')
		ht = self.getHighTension()
		mag = self.getMagnification()
		self.logger.info('Matrix %s, shape %s, type %s, flat %s'
						% (matrix, matrix.shape, matrix.type(), Numeric.ravel(matrix)))
		self.calclient.storeMatrix(ht, mag, 'defocus', matrix)
		self.logger.info('Calibration stored')
		node.beep()
		return ''

	def calibrateStigmators(self, tilt_value, delta):
		self.cam.setCameraDict(self.settings['camera settings'])

		currentstig = self.getObjectiveStigmator()
		## set up the stig states
		stig = {'x':{}, 'y':{}}
		for axis in ('x','y'):
			for sign in ('+','-'):
				stig[axis][sign] = dict(currentstig)
				if sign == '+':
					stig[axis][sign][axis] += delta/2.0
				elif sign == '-':
					stig[axis][sign][axis] -= delta/2.0

		for stigaxis in ('x','y'):
			self.logger.info('Calculating matrix for stig %s' % (stigaxis,))
			matdict = {}
			for tiltaxis in ('x','y'):
				self.logger.info('Measuring %s tilt' % (tiltaxis,))
				stig1 = stig[stigaxis]['+']
				stig2 = stig[stigaxis]['-']
				state1 = data.ScopeEMData(stigmator={'objective':stig1})
				state2 = data.ScopeEMData(stigmator={'objective':stig2})
				shift1, shift2 = self.calclient.measureDisplacements(tiltaxis, tilt_value, state1, state2)
				self.logger.info('Shift 1 %s' % shift1)
				self.logger.info('Shift 2 %s' % shift2)
				stigval1 = stig1[stigaxis]
				stigval2 = stig2[stigaxis]
				matcol = self.calclient.eq11(shift1, shift2, stigval1, stigval2, tilt_value)
				matdict[tiltaxis] = matcol
			matrix = Numeric.zeros((2,2), Numeric.Float32)
			matrix[:,0] = matdict['x']
			matrix[:,1] = matdict['y']

			## store calibration
			mag = self.getMagnification()
			ht = self.getHighTension()
			type = 'stig' + stigaxis
			self.calclient.storeMatrix(ht, mag, type, matrix)

		## return to original stig
		stigdict = {'stigmator':{'objective':currentstig}}
		stigdata = data.ScopeEMData(initializer=stigdict)
		self.emclient.setScope(stigdata)
		node.beep()
		return ''

	def measureDefocusStig(self, btilt, stig=True):
		self.cam.setCameraDict(self.settings['camera settings'])
		try:
			ret = self.calclient.measureDefocusStig(btilt, stig=stig)
		except:
			self.logger.exception('')
			ret = {}
		self.logger.info('RET %s' % ret)
		return ret

	def getObjectiveStigmator(self):
		emdata = self.emclient.getScope()
		obj = dict(emdata['stigmator']['objective'])
		return obj

	def uiCalibrateDefocus(self):
		self.calibrateDefocus(self.settings['defocus beam tilt'],
													self.settings['first defocus'],
													self.settings['second defocus'])

	def uiCalibrateStigmators(self):
		self.calibrateStigmators(self.settings['stig beam tilt'],
															self.settings['stig delta'])

	def uiMeasureDefocusStig(self, btilt):
		result = self.measureDefocusStig(btilt, stig=True)
		self.resultvalue = result

	def uiMeasureDefocus(self, btilt):
		result = self.measureDefocusStig(btilt, stig=False)
		self.resultvalue = result

	def uiCorrectDefocus(self):
		delta = self.resultvalue
		if not delta:
			self.logger.info('No result, you must measure first')
			return
		current = self.getCurrentValues()	

		newdefocus = current['defocus'] + delta['defocus']
		newdata = data.ScopeEMData(defocus=newdefocus)
		self.emclient.setScope(newdata)

	def uiCorrectStigmator(self):
		delta = self.resultvalue
		if not delta:
			self.logger.info('No result, you must measure first')
			return
		current = self.getCurrentValues()	

		newstigx = current['stigx'] + delta['stigx']
		newstigy = current['stigy'] + delta['stigy']
		stigdict = {'stigmator': {'objective': {'x':newstigx,'y':newstigy}}}
		newdata = data.ScopeEMData(initializer=stigdict)
		self.emclient.setScope(newdata)

	def uiResetDefocus(self):
		newemdata = data.ScopeEMData()
		newemdata['reset defocus'] = True
		self.emclient.setScope(newemdata)

	def getCurrentValues(self):
		emdata = self.emclient.getScope()
		defocus = emdata['defocus']
		stig = emdata['stigmator']['objective']
		stigx = stig['x']
		stigy = stig['y']
		return {'defocus':defocus, 'stigx':stigx, 'stigy':stigy}

	def uiEucToScope(self):
		self.eucToScope()

	def uiEucFromScope(self):
		self.eucFromScope()

	def eucToScope(self):
		scope = self.emclient.getScope()
		ht = scope['high tension']
		mag = scope['magnification']
		eudata = self.euclient.researchEucentricFocus(ht,mag)
		if eudata is None:
			message = 'No eucentric focus has been saved for ht=%s and mag=%s' % (ht,mag)
			self.logger.info(message)
			self.messagelog.information(message)
			return
		focus = eudata['focus']

		scopedata = data.ScopeEMData()
		scopedata['focus'] = focus
		try:
			self.emclient.setScope(scopedata)
		except node.PublishError:
			self.logger.exception('Cannot set instrument parameters')
			self.messagelog.error('Cannot set instrument parameters')

	def eucFromScope(self):
		## get current value of focus
		scope = self.emclient.getScope()
		ht = scope['high tension']
		mag = scope['magnification']
		focus = scope['focus']
		self.euclient.publishEucentricFocus(ht, mag, focus)
		self.eucstatus.information('published:  HT: %s, Mag: %s, Euc. Focus: %s' % (ht, mag, focus))

	def abortCalibration(self):
		raise NotImplementedError

