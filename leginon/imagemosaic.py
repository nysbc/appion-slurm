import watcher
import data
import event
import Numeric
import fftengine
import correlator
import peakfinder
reload(fftengine)
reload(correlator)
reload(peakfinder)

class ImageMosaic(watcher.Watcher):
	def __init__(self, id, nodelocations):
		# needs own event?
		watchfor = event.PublishEvent
		lockblocking = 1
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking)

		self.imagemosaic = {}

		self.correlator = correlator.Correlator(fftengine.fftNumeric())
		self.peakfinder = peakfinder.PeakFinder()

		self.start()

	def main(self):
		pass

	def getPeak(self, image1, image2):
		self.correlator.setImage(0, image1)
		self.correlator.setImage(1, image2)
		pcimage = self.correlator.phaseCorrelate()
		self.peakfinder.setImage(pcimage)
		self.peakfinder.pixelPeak()
		peak = self.peakfinder.getResults()
		return peak['pixel peak value']

	def testimages(self, t1, t2):
		import Image
		import time
		Image.fromstring('L', (t1.shape[1], t1.shape[0]), t1.tostring()).show()
		time.sleep(2.0)
		Image.fromstring('L', (t2.shape[1], t2.shape[0]), t2.tostring()).show()

	def compareShifts(self, unwrappedshift, wrappedshift, image1, image2):
		# if both shift values disagree, we must check all four of the possible
		# correct shift pairs
		if unwrappedshift[0] != wrappedshift[0] \
											and unwrappedshift[1] != wrappedshift[1]:
			# holds peak values for the four cases for comparison at the end
			peakmatrix = Numeric.zeros((2,2), Numeric.Float32)

			# tests if both unwrapped shift values are valid
			peakmatrix[0, 0] = self.getPeak(
				image2[unwrappedshift[0]:, unwrappedshift[1]:],
				image1[:image2.shape[0] - unwrappedshift[0],
								:image2.shape[1] - unwrappedshift[1]])

			# tests if unwrappedshift[0] is valid and wrappedshift[1] is valid 
			peakmatrix[0, 1] = self.getPeak(
				image2[unwrappedshift[0]:, :image1.shape[1] + wrappedshift[1]],
				image1[:image2.shape[0] - unwrappedshift[0], -wrappedshift[1]:])

			# tests if wrappedshift[0] is valid and unwrappedshift[1] is valid 
			peakmatrix[1, 0] = self.getPeak(
				image2[:image1.shape[0] + wrappedshift[0], unwrappedshift[1]:],
				image1[-wrappedshift[0]:, :image2.shape[1] - unwrappedshift[1]])

			# tests if both wrapped shift values are valid
			peakmatrix[1, 1] = self.getPeak(
				image2[:image1.shape[0] + wrappedshift[0],
								:image1.shape[1] + wrappedshift[1]],
				image1[-wrappedshift[0]:, -wrappedshift[1]:])

			# finds the biggest peak in the matrix
			maxvalue = 0.0
			for i in range(len(peakmatrix)):
				for j in range(len(peakmatrix[i])):
					if peakmatrix[i, j] > maxvalue:
						maxvalue = peakmatrix[i, j]
						maxpeak = (i, j)

			# assigns the correct shift based on the matrix
			if maxpeak[0] == 1:
				shift0 = wrappedshift[0]
			else:
				shift0 = unwrappedshift[0]
			if maxpeak[1] == 1:
				shift1 = wrappedshift[1]
			else:
				shift1 = unwrappedshift[1]

		# unwrappedshift[1] and wrappedshift[1] agree,
		# unwrappedshift[0] and wrappedshift[0] do not
		elif unwrappedshift[0] != wrappedshift[0]:
			unwrappedshiftpeak = self.getPeak(
				image2[unwrappedshift[0]:, unwrappedshift[1]:],
				image1[:image2.shape[0] - unwrappedshift[0],
								:image2.shape[1] - unwrappedshift[1]])
			wrappedshiftpeak = self.getPeak(
				image2[:image1.shape[0] + wrappedshift[0], wrappedshift[1]:],
				image1[-wrappedshift[0]:, :image2.shape[1] - wrappedshift[1]])

			# use the shift[0] with the biggest peak
			if unwrappedshiftpeak < wrappedshiftpeak:
				shift0 = wrappedshift[0]
			else:
				shift0 = unwrappedshift[0]
			shift1 = unwrappedshift[1]

		# unwrappedshift[0] and wrappedshift[0] agree,
		# unwrappedshift[1] and wrappedshift[1] do not
		elif unwrappedshift[1] != wrappedshift[1]:
			unwrappedshiftpeak = self.getPeak(
				image2[unwrappedshift[0]:, unwrappedshift[1]:],
				image1[:image2.shape[0]-unwrappedshift[0],
								:image2.shape[1]-unwrappedshift[1]])
			wrappedshiftpeak = self.getPeak(
				image2[wrappedshift[0]:, :image1.shape[1] + wrappedshift[1]],
				image1[:image2.shape[0] - wrappedshift[0], -wrappedshift[1]:])

			shift0 = unwrappedshift[0]
			# use the shift[1] with the biggest peak
			if unwrappedshiftpeak < wrappedshiftpeak:
				shift1 = wrappedshift[1]
			else:
				shift1 = unwrappedshift[1]
		else:
			# unwrappedshift and wrappedshift agree, no need to check
			shift0 = unwrappedshift[0]
			shift1 = unwrappedshift[1]

		return (shift0, shift1)

	def processData(self, idata):
		if len(idata.content['neighbor tiles']) == 0:
			if len(self.imagemosaic) == 0:
				self.imagemosaic[idata.id] = {'image': idata.content['image'],
																'position': (0, 0)}
			else:
				# it doesn't have and neighbors, start a new mosaic?
				print 'Error: starting tile already placed'
		else:
			newposition = {}
			positionvotes = ({}, {})
			peakvalue = 0.0
			# calculate the tile's position based on shift from each of the neighbors
			for neighbor in idata.content['neighbor tiles']:
				if neighbor not in self.imagemosaic:
					# we don't know about its neighbors, wait for them?
					print 'Error: starting tile already placed'
					break
				# phase correlate the tile image with the neighbors
				self.correlator.setImage(0, idata.content['image'])
				self.correlator.setImage(1, self.imagemosaic[neighbor]['image'])
				pcimage = self.correlator.phaseCorrelate()
				self.peakfinder.setImage(pcimage)
				self.peakfinder.pixelPeak()
				peak = self.peakfinder.getResults()

				# determine which of the shifts is valid
				unwrappedshift = peak['pixel peak']
				wrappedshift = correlator.wrap_coord(peak['pixel peak'], pcimage.shape)
				shift = self.compareShifts(unwrappedshift, wrappedshift,
						idata.content['image'], self.imagemosaic[neighbor]['image'])

				# use the shift and the neighbor position to get tile position
				newposition[neighbor] = {}
				position = (self.imagemosaic[neighbor]['position'][0] + shift[0],
										self.imagemosaic[neighbor]['position'][1] + shift[1])
				peakvalue = peak['pixel peak value']

				# add a vote for this position per axis
				# add the peak value to the sum of peak values for the position per axis
				for i in [0, 1]:
					if position[i] in positionvotes[i]:
						positionvotes[i][position[i]]['votes'] += 1
						positionvotes[i][position[i]]['peaks value'] += peakvalue
					else:
						positionvotes[i][position[i]] = {'votes': 1,
							'peaks value': peakvalue}

			# which ever position has the most votes wins per axis
			# the sum of the peak values for the position breaks ties
			position = [0, 0]
			for i in [0, 1]:
				maxvotes = 0
				maxpeakvalue = 0.0
				for p in positionvotes[i]:
					if positionvotes[i][p]['votes'] > maxvotes:
						position[i] = p
						maxvotes = positionvotes[i][p]['votes']
						maxpeakvalue = positionvotes[i][p]['peaks value']
					elif positionvotes[i][p]['votes'] == maxvotes:
						if positionvotes[i][p]['peaks value'] > maxpeakvalue:
							position[i] = p
							maxvotes = positionvotes[i][p]['votes']
							maxpeakvalue = positionvotes[i][p]['peaks value']

			# add the tile image and position to the mosaic
			self.imagemosaic[idata.id] = {}
			self.imagemosaic[idata.id]['image'] = idata.content['image']
			self.imagemosaic[idata.id]['position'] = tuple(position)

	def uiShow(self):
		import Image
		i = self.makeImage(self.imagemosaic)
		Image.fromstring('L', (i.shape[1], i.shape[0]), i.tostring()).show()
		return ''

	def makeImage(self, mosaic):
		# could be Inf
		mincoordinate = [0, 0]
		maxcoordinate = [0, 0]
		for tileid in mosaic:
			for i in [0, 1]:
				min = mosaic[tileid]['position'][i]
				max = mosaic[tileid]['position'][i] + mosaic[tileid]['image'].shape[i]
				if min < mincoordinate[i]:
					mincoordinate[i] = min
				if max > maxcoordinate[i]:
					maxcoordinate[i] = max
		imageshape = (maxcoordinate[0] - mincoordinate[0], 
									maxcoordinate[1] - mincoordinate[1]) 
		image = Numeric.zeros(imageshape, Numeric.UnsignedInt8)
		for tileid in mosaic:
			row = mosaic[tileid]['position'][0]
			column = mosaic[tileid]['position'][1]
			iti = mosaic[tileid]['image']
			image[row:row + iti.shape[0], column:column + iti.shape[1]] = iti
		return image

	def defineUserInterface(self):
		watcherspec = watcher.Watcher.defineUserInterface(self)
		showspec = self.registerUIMethod(self.uiShow, 'Show', ())
		self.registerUISpec('Image Mosaic', (watcherspec, showspec))

