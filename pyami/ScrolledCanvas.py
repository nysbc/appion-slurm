#!/usr/bin/env python

from Tkinter import *
from ImageCanvas import ImageCanvas

class ScrolledCanvas(Frame):
	def __init__(self, *args, **kargs):
		Frame.__init__(self, *args, **kargs)

		self._build()
		self.bindings()

	def bindings(self):
		self.canvas.bind('<Configure>', self.configure_callback)
		self.canvas.bind('<Motion>', self.motion_callback)
		self.canvas.bind('<Leave>', self.leave_callback)

	def _build(self):
		bgcolor = self['background']
		can = self.canvas = ImageCanvas(self, bg=bgcolor)
		hs = self.hscroll = Scrollbar(self, orient=HORIZONTAL, background=bgcolor, troughcolor=bgcolor)
		vs = self.vscroll = Scrollbar(self, orient=VERTICAL, background=bgcolor, troughcolor=bgcolor)

		## connect canvas to scrollbars
		can.config(xscrollcommand=hs.set, yscrollcommand=vs.set)
		hs.config(command=can.xview)
		vs.config(command=can.yview)
		can.grid(row=0, column=0, sticky=NSEW)
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)

		self.hscroll_state(ON)
		self.vscroll_state(ON)

	### somehow have to prevent infinite switching loop
	def hscroll_state(self, switch):
		if switch == ON:
			self.hscroll.grid(row=1, column=0, sticky=NSEW)
		elif switch == OFF:
			self.hscroll.grid_remove()
		self.scroll_switched = 1

	def vscroll_state(self, switch):
		if switch == ON:
			self.vscroll.grid(row=0, column=1, sticky=NSEW)
		elif switch == OFF:
			self.vscroll.grid_remove()
		self.scroll_switched = 1

	def leave_callback(self,event):
		pass

	def motion_callback(self,event):
		pass

	def configure_callback(self, event):
		### Check if scrollbar is necessary after a resize.
		### If this configure was a result of a scrollbar toggle
		### do not reset the scrollbar to original state
		if self.canvas.xview() == (0.0,1.0):
			self.hscroll_state(OFF)
		else:
			self.hscroll_state(ON)

		if self.canvas.yview() == (0.0,1.0):
			self.vscroll_state(OFF)
		else:
			self.vscroll_state(ON)
			
	def resize(self, x1, y1, x2, y2):
		self.canvas.resize(x1,y1,x2,y2)

if __name__ == '__main__':
	mycan = ScrolledCanvas(bg='darkgrey')
	mycan.pack(expand=YES,fill=BOTH)


	from Mrc import *
	ndata = mrc_to_numeric('test1.mrc')
	mycan.canvas.use_numeric(ndata)
	mycan.canvas.image_display()

	mycan.canvas.create_oval(0,0,50,50, fill='green')
	mycan.canvas.create_oval(-50,-50,0,0, fill='red')

	#mycan.resize(-100,-100,100,100)
	mycan.mainloop()
