#!/usr/bin/env python

from Tkinter import *
import Numeric
import Image
import ImageTk

## (Numeric typcode,size) => (PIL mode,  PIL rawmode)
ntype_itype = {
	(Numeric.UnsignedInt8,1) : ('L','L'),
	(Numeric.Int16,2) : ('I','I;16NS'),
	(Numeric.Int,2) : ('I','I;16NS'),
	(Numeric.Int,4) : ('I','I;32NS'),
	(Numeric.Int32,4) : ('I','I;32NS'),
	(Numeric.Float,4) : ('F','F;32NF'),
	(Numeric.Float,8) : ('F','F;64NF'),
	(Numeric.Float32,4) : ('F','F;32NF'),
	(Numeric.Float64,8) : ('F','F;64NF')
	}

class NumericImage(ImageTk.PhotoImage):
	"""extends the PIL PhotoImage to take 2D Numeric data, scaled to
	the clients preference"""

	def __init__(self,*args,**kargs):
		ImageTk.PhotoImage.__init__(self, *args, **kargs)

	def use_array(self, ndata):
		self.array = ndata
		self.array_min = min(min(self.array))
		self.array_max = max(max(self.array))

	def paste_array(self, clip=None):
		"""Paste a Numeric array into photo image.
		'clip' specifies the min and max values of the array
		that should be scaled to the display (0-255)
		If no clip is specified, default is min and max of array"""
		newim = self.array_to_image(clip)
		self.paste(newim)

	def array_to_image(self, clip=None):
		h,w = self.array.shape
		size = (w,h)
		if len(size) != 2:
			return None

		## if no clip specified, use min and max of array
		if clip:
			minval,maxval = clip
		else:
			minval = self.array_min
			maxval = self.array_max

		range = maxval - minval
		scl = 255.0 / range
		off = -255.0 * minval / range
		newdata = scl * self.array + off
		
		type = newdata.typecode()
		itemsize = newdata.itemsize()
		im_mode = ntype_itype[type,itemsize][0]
		im_rawmode = ntype_itype[type,itemsize][1]

		nstr = newdata.tostring()

		stride = 0
		orientation = 1

		im = Image.fromstring( im_mode, size, nstr, "raw",
			        im_rawmode, stride, orientation
				        )
		return im

if __name__ == '__main__':
	root = Tk()
	can = Canvas(width = 512, height = 512, bg='blue')
	can.pack()

	mode = 'I'
	size = (128,256)
	ndata = Numeric.arrayrange(256**2/2)
	ndata = Numeric.reshape(ndata,size)

	numphoto1 = NumericImage(mode, size)
	numphoto1.use_array(ndata)
	numphoto1.paste_array((10000,30000))

	numphoto2 = NumericImage(mode, size)
	numphoto2.use_array(ndata)
	numphoto2.paste_array()

	numphoto3 = NumericImage(mode, size)
	numphoto3.use_array(ndata)
	numphoto3.paste_array()

	numphoto4 = NumericImage(mode, size)
	numphoto4.use_array(ndata)
	numphoto4.paste_array()

	can.create_image(0,0,anchor=NW,image=numphoto1)
	can.create_image(0,256,anchor=NW,image=numphoto2)
	can.create_image(256,0,anchor=NW,image=numphoto3)
	can.create_image(256,256,anchor=NW,image=numphoto4)

	root.mainloop()
