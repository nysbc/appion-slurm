#!/usr/bin/env python

from Tkinter import *
import array, base64
import threading
import Numeric
import signal, time

from ImageViewer import ImageViewer
import watcher
reload(watcher)
import node, event, data
import Mrc
import cameraimage
import camerafuncs
reload(camerafuncs)
import xmlrpclib

class ImViewer(watcher.Watcher, camerafuncs.CameraFuncs):
	def __init__(self, id, nodelocations):
		watchfor = event.ImagePublishEvent
		lockblocking = 0
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking)

		self.addEventOutput(event.ImageClickEvent)

		self.iv = None
		self.numarray = None
		self.viewer_ready = threading.Event()
		self.start_viewer_thread()

	def die(self, killevent=None):
		self.close_viewer()
		self.exit()

	def start_viewer_thread(self):
		if self.iv is not None:
			return
		self.viewerthread = threading.Thread(name='image viewer thread', target=self.open_viewer)
		self.viewerthread.setDaemon(1)
		self.viewerthread.start()
		#print 'thread started'

	def clickEvent(self, tkevent):
		clickinfo = self.iv.eventXYInfo(tkevent)
		clickinfo['image id'] = self.imageid
		#print 'clickinfo', clickinfo
		## prepare for xmlrpc
		c = {}
		for key,value in clickinfo.items():
			if value is not None:
				c[key] = value
		#print 'c', c
		e = event.ImageClickEvent(self.ID(), c)
		#print 'sending ImageClickEvent'
		self.outputEvent(e)
		#print 'sent ImageClickEvent'

	def open_viewer(self):
		#print 'root...'
		root = self.root = Tk()
		#root.wm_sizefrom('program')
		root.wm_geometry('=450x400')

		#print 'acqbut'
		buttons = Frame(root)
		self.acqrawbut = Button(buttons, text='Acquire Raw', command=self.acquireRaw)
		self.acqrawbut.pack(side=LEFT)
		self.acqcorbut = Button(buttons, text='Acquire Corrected', command=self.acquireCorrected)
		self.acqcorbut.pack(side=LEFT)
		self.acqeventbut = Button(buttons, text='Acquire Event', command=self.acquireEvent)
		self.acqeventbut.pack(side=LEFT)
		buttons.pack(side=TOP)

		#print 'iv'
		self.iv = ImageViewer(root, bg='#488')
		self.iv.bindCanvas('<Double-1>', self.clickEvent)
		#print 'iv pack'
		self.iv.pack()

		#print 'viewer_ready.set'
		self.viewer_ready.set()
		#print 'mainloop'
		root.mainloop()

		##clean up if window destroyed
		self.viewer_ready.clear()
		self.iv = None

	def close_viewer(self):
		try:
			self.root.destroy()
		except TclError:
			pass

	def acquireRaw(self):
		self.acqrawbut['state'] = DISABLED
		self.acquireAndDisplay(0)
		self.acqrawbut['state'] = NORMAL

	def uiAcquireRaw(self):
		imarray = self.acquireArray(0)
		if imarray is None:
			mrcstr = ''
		else:
			mrcstr = Mrc.numeric_to_mrcstr(imarray)
		return xmlrpclib.Binary(mrcstr)

	def acquireCorrected(self):
		self.acqcorbut['state'] = DISABLED
		self.acquireAndDisplay(1)
		self.acqcorbut['state'] = NORMAL

	def uiAcquireCorrected(self):
		im = self.acquireArray(1)
		if im is None:
			mrcstr = ''
		else:
			mrcstr = Mrc.numeric_to_mrcstr(im)
		return xmlrpclib.Binary(mrcstr)

	def acquireArray(self, corr=0):
		defaultsize = (512,512)
		camerasize = (2048,2048)
		offset = cameraimage.centerOffset(camerasize,defaultsize)
		camstate = self.camconfig.get()
		imarray = self.cameraAcquireArray(camstate, correction=corr)
		return imarray

	def acquireAndDisplay(self, corr=0):
		print 'acquireArray'
		imarray = self.acquireArray(corr)
		print 'displayNumericArray'
		if imarray is None:
			self.iv.displayMessage('NO IMAGE ACQUIRED')
		else:
			self.displayNumericArray(imarray)
		print 'acquireAndDisplay done'

	def acquireEvent(self):
		self.acqeventbut['state'] = DISABLED
		#print 'sending ImageAcquireEvent'
		e = event.ImageAcquireEvent(self.ID())
		#print 'e', e
		self.outputEvent(e)
		#print 'sent ImageAcquireEvent'
		self.acqeventbut['state'] = NORMAL
		return ''

	def processData(self, imagedata):
		#camdict = imagedata.content
		#imarray = array.array(camdict['datatype code'], base64.decodestring(camdict['image data']))
		#width = camdict['x dimension']
		#height = camdict['y dimension']
		#numarray = Numeric.array(imarray)
		#numarray.shape = (height,width)

		## self.im must be 2-d numeric data

		self.numarray = imagedata.content
		self.imageid = imagedata.id
		self.displayNumericArray(self.numarray)

	def displayNumericArray(self, numarray):
		self.start_viewer_thread()
		self.viewer_ready.wait()
		self.iv.import_numeric(numarray)
		self.iv.update()

	def defineUserInterface(self):
		watcherspec = watcher.Watcher.defineUserInterface(self)

		argspec = (
		self.registerUIData('Filename', 'string'),
		)
		loadspec = self.registerUIMethod(self.uiLoadImage, 'Load MRC', argspec)
		savespec = self.registerUIMethod(self.uiSaveImage, 'Save MRC', argspec)
		filespec = self.registerUIContainer('File', (loadspec,savespec))

		acqret = self.registerUIData('Image', 'binary')

		acqraw = self.registerUIMethod(self.uiAcquireRaw, 'Acquire Raw', (), returnspec=acqret)
		acqcor = self.registerUIMethod(self.uiAcquireCorrected, 'Acquire Corrected', (), returnspec=acqret)
		acqev = self.registerUIMethod(self.acquireEvent, 'Acquire Event', ())

		self.camconfig = self.cameraConfigUISpec()

		self.registerUISpec(`self.id`, (acqraw, acqcor, acqev, self.camconfig, filespec, watcherspec))

	def uiLoadImage(self, filename):
		im = Mrc.mrc_to_numeric(filename)
		self.displayNumericArray(im)
		return ''

	def uiSaveImage(self, filename):
		numarray = self.iv.imagearray
		Mrc.numeric_to_mrc(numarray, filename)
		return ''

if __name__ == '__main__':
	id = ('ImViewer',)
	i = ImViewer(id, {})
	signal.pause()


