import calibrator
import calibrationclient
import event, data
import uidata
import node

class PixelSizeCalibrator(calibrator.Calibrator):
	'''
	calibrate the pixel size for different mags
	'''
	def __init__(self, id, session, nodelocations, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, nodelocations, **kwargs)
		self.calclient = calibrationclient.PixelSizeCalibrationClient(self)

		self.defineUserInterface()
		self.start()

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
#		calibrator.Calibrator.defineUserInterface(self)

		self.uilisting = uidata.Sequence('Pixel Size Calibrations', [])
		testmethod = uidata.Method('Test', self.uiGetCalibrations)

		self.uimag = uidata.Integer('Magnification', 62000, 'rw')
		self.uipixsize = uidata.Float('Meters/Pixel', 1e-9, 'rw')
		self.comment = uidata.String('Comment', '', 'rw')
		storemethod = uidata.Method('Store', self.uiStore)
		mycontainer = uidata.MediumContainer('Pixel Size Calibrator')

		mycontainer.addObjects((self.uilisting, testmethod))

		mycontainer.addObjects((self.uimag, self.uipixsize,
														self.comment, storemethod))
		self.uiserver.addObject(mycontainer)

	def uiGetCalibrations(self):
		calibrations = self.research(dataclass=data.PixelSizeCalibrationData)
		calibrationstrings = []
		for calibration in calibrations:
			calibrationstrings.append('Magnification: %.1f Pixel size: %f Comment: %s, Session: %s Instrument: %s' %(calibration['magnification'], calibration['pixelsize'], calibration['comment'], calibration['session']['name'], calibration['session']['instrument']['name']))
		self.uilisting.set(calibrationstrings)

	def uiStore(self):
		self.store()
		return ''

	def store(self):
		caldata = data.PixelSizeCalibrationData()
		caldata['magnification'] = self.uimag.get()
		caldata['pixelsize'] = self.uipixsize.get()
		caldata['comment'] = self.comment.get()
		self.publish(caldata, database=True)
