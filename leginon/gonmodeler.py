import node
import data
import fftengine
import correlator
import peakfinder
import event
import time
import cameraimage
import camerafuncs
import threading

class GonModeler(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)
		ffteng = fftengine.fftNumeric()
		#ffteng = fftengine.fftFFTW(planshapes=(), estimate=1)
		self.correlator = correlator.Correlator(ffteng)
		self.peakfinder = peakfinder.PeakFinder()
		self.settle = 2.0
		self.threadstop = threading.Event()
		self.threadlock = threading.Lock()

		node.Node.__init__(self, id, nodelocations, **kwargs)
		self.defineUserInterface()

	# calibrate needs to take a specific value
	def loop(self, axis, points, interval):
		## set camera state
		camconfig = self.cam.config()
		camstate = camconfig['state']
		self.cam.state(camstate)

		mag = self.getMagnification()
		self.writeHeader(mag, axis)

		self.oldimagedata = None
		self.acquireNextPosition(axis)
		currentpos = self.getStagePosition()

		for i in range(points):
			if self.threadstop.isSet():
				print 'loop breaking before all points done'
				break
			currentpos['stage position'][axis] += interval
			datalist = self.acquireNextPosition(axis, currentpos)
			self.writeData(mag, axis, datalist)

		print 'loop done'


	def acquireNextPosition(self, axis, state=None):
		## go to state
		if state is not None:
			newemdata = data.EMData('scope', state)
			self.publishRemote(newemdata)
			time.sleep(self.settle)

		## acquire image
		newimagedata = self.cam.acquireCameraImageData(correction=0)
		newnumimage = newimagedata.content['image']

		## insert into correlator
		self.correlator.insertImage(newnumimage)

		## cross correlation if oldimagedata exists
		if self.oldimagedata is not None:
			## cross correlation
			crosscorr = self.correlator.phaseCorrelation()
			
			## subtract auto correlation
			crosscorr -= self.autocorr

			## peak finding
			self.peakfinder.setImage(crosscorr)
			self.peakfinder.subpixelPeak()
			peak = self.peakfinder.getResults()
			peakvalue = peak['subpixel peak value']
			shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)
			binx = newimagedata.content['camera']['binning']['x']
			biny = newimagedata.content['camera']['binning']['y']
			pixelsyx = biny * shift[0], binx * shift[1]
			pixelsx = imageyx[1]
			pixelsy = imageyx[0]
			pixelsh = abs(pixelsx + 1j * pixelsy)

			## calculate stage shift
			avgpos = {}
			pos0 = self.oldimagedata.content['scope']['stage position'][axis]
			pos1 = newimagedata.content['scope']['stage position'][axis]
			deltapos = pos1 - pos0
			avgpos[axis] = (pos0 + pos1) / 2.0

			otheraxis = self.otheraxis(axis)
			otherpos0 = self.oldimagedata.content['scope']['stage position'][otheraxis]
			otherpos1 = newimagedata.content['scope']['stage position'][otheraxis]
			avgpos[otheraxis] = (otherpos0 + otherpos1) / 2.0

			datalist = [avgpos['x'], avgpos['y'], deltapos, pixelsx, pixelsy]

		else:
			datalist = []

		self.correlator.insertImage(newnumimage)
		self.autocorr = self.correlator.phaseCorrelation()
		self.oldimagedata = newimagedata

		return datalist

	def otheraxis(self, axis):
		if axis == 'x':
			return 'y'
		if axis == 'y':
			return 'x'

	def writeHeader(self, mag, axis):
		'''
		header:
			magnification
			axis
		'''
		padmagstr = '%06d' % (int(mag),)
		magstr = str(int(mag))
		filename = padmagstr + axis + '.data'
		f = open(filename, 'a')
		f.write(magstr + '\n')
		f.write(axis + '\n')
		f.close()

	def writeData(self, mag, axis, datalist):
		padmagstr = '%06d' % (int(mag),)
		magstr = str(int(mag))
		filename = padmagstr + axis + '.data'
		strdatalist = []
		for item in datalist:
			strdatalist.append(str(item))
		f = open(filename, 'a')
		datastr = '\t'.join(strdatalist)
		f.write(datastr + '\n')
		f.close()

	def getStagePosition(self):
		dat = self.researchByDataID('stage position')
		return dat.content

	def getMagnificaiton(self):
		dat = self.researchByDataID('magnification')
		return dat.content['magnification']

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		#### parameters for user to set
		self.attempts = 5
		self.range = [1e-7, 1e-6]
		self.correlationthreshold = 0.05
		self.camerastate = {'size': 512, 'binning': 1, 'exposure time': 500}
		try:
			isdata = self.researchByDataID(self.parameter)
			self.base = isdata.content[self.parameter]
		except:
			self.base = {'x': 0.0, 'y':0.0}
		####

		cspec = self.registerUIMethod(self.uiCalibrate, 'Calibrate', ())

		paramchoices = self.registerUIData('paramdata', 'array', default=('image shift', 'stage position'))


		argspec = (
		self.registerUIData('Base', 'struct', default=self.base),
		self.registerUIData('Minimum', 'float', default=self.range[0]),
		self.registerUIData('Maximum', 'float', default=self.range[1]),
		self.registerUIData('Attempts', 'integer', default=self.attempts),
		self.registerUIData('Correlation Threshold', 'integer', default=self.correlationthreshold),
		self.registerUIData('Camera State', 'struct', default=self.camerastate)
		)
		rspec = self.registerUIMethod(self.uiSetParameters, 'Set Parameters', argspec)

		self.validshift = self.registerUIData('Valid Shift', 'struct', permissions='rw')
		self.validshift.set(
			{
			'correlation': {'min': 20.0, 'max': 200.0},
			'calibration': {'min': 20.0, 'max': 200.0}
			}
		)

		argspec = (self.registerUIData('Filename', 'string'),)
		save = self.registerUIMethod(self.save, 'Save', argspec)
		load = self.registerUIMethod(self.load, 'Load', argspec)

		filespec = self.registerUIContainer('File', (save, load))

		self.registerUISpec('Calibration', (nodespec, cspec, rspec, self.validshift, filespec))

	def uiStartMeasuring(self):
		if not self.threadlock.acquire(0):
			return ''
		self.threadstop.clear()
		t = threading.Thread(target=self.loop, args=(axis, points, interval))
		t.setDaemon(1)
		t.start()
		return ''

	def uiStopMeasuring(self):
		self.threadstop.set()
		return ''
