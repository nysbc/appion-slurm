#!/usr/bin/env python

import node
import event
import data

class Navigator(node.Node):
	def __init__(self, id, nodelocations):
		self.shift_types = {
			'image shift': event.ImageShiftPixelShiftEvent,
			'stage': event.StagePixelShiftEvent,
			'no preference': event.PixelShiftEvent
		}

		## by default, use the generic PixelShiftEvent
		self.shiftType('image shift')

		node.Node.__init__(self, id, nodelocations)

		self.addEventInput(event.ImageClickEvent, self.handleImageClick)
		self.addEventInput(event.ImageAcquireEvent, self.handleImageAcquire)
		self.addEventOutput(event.ImagePublishEvent)
		self.addEventOutput(event.PixelShiftEvent)

	def die(self, killevent):
		self.exit()

	def shiftType(self, shift_type=None):
		'''
		this sets the event to be generated for a move
		it must be a subclass of PixelShiftEvent
		'''
		if shift_type is None:
			return self.current_shift_type
		
		if shift_type not in self.shift_types:
			raise RuntimeError('no such shift type: %s' % shift_type)
		self.current_shift_type = shift_type
		self.shiftEventClass = self.shift_types[shift_type]

	def handleImageClick(self, clickevent):
		print 'handling image click'
		clickinfo = clickevent.content
		## get relavent info from click event
		clickrow = clickinfo['array row']
		clickcol = clickinfo['array column']
		clickshape = clickinfo['array shape']

		print 'clickinfo', clickinfo
		## calculate delta from image center
		deltarow = clickrow - clickshape[0] / 2
		deltacol = clickcol - clickshape[1] / 2

		## to shift clicked point to center...
		deltarow = -deltarow
		deltacol = -deltacol

		deltarowcol = {'row':deltarow, 'column':deltacol}
		print 'deltarowcol', deltarowcol

		## do pixel shift
		e = self.shiftEventClass(self.ID(), deltarowcol)
		print 'e', e
		self.outputEvent(e)
		print 'outputEvent done'

		## acquire image
		self.acquireImage()

	def handleImageAcquire(self, acqevent):
		self.acquireImage()

	def acquireImage(self):
		print 'acquiring image'
		image = self.researchByDataID('image data')
		image = image.content['image data']
		imagedata = data.ImageData(self.ID(), image)
		print 'publishing image'
		self.publish(imagedata, event.ImagePublishEvent)
		print 'image published'

	def defineUserInterface(self):
		nodeui = node.Node.defineUserInterface(self)

		shift_types = self.shift_types.keys()
		temparam = self.registerUIData('temparam', 'array', default=shift_types)
		movetype = self.registerUIData('TEM Parameter', 'string', choices=temparam, permissions='rw')
		movetype.set(self.shiftType)

		self.registerUISpec('Navigator', (movetype, nodeui))


if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
