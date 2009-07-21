#!/usr/bin/python -O
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ImagePanelTools.py,v $
# $Revision: 1.11 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-19 22:39:23 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $
#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import math
import wx
from wx.lib.buttons import GenBitmapButton, GenBitmapToggleButton
from gui.wx.Entry import FloatEntry, EVT_ENTRY
import icons
import gui.wx.TargetPanelBitmaps

DisplayEventType = wx.NewEventType()
EVT_DISPLAY = wx.PyEventBinder(DisplayEventType)

SettingsEventType = wx.NewEventType()
EVT_SETTINGS = wx.PyEventBinder(SettingsEventType)

MeasurementEventType = wx.NewEventType()
EVT_MEASUREMENT = wx.PyEventBinder(MeasurementEventType)

ImageClickedEventType = wx.NewEventType()
EVT_IMAGE_CLICKED = wx.PyEventBinder(ImageClickedEventType)

##################################
##
##################################

class DisplayEvent(wx.PyCommandEvent):
	def __init__(self, source, name, value):
		wx.PyCommandEvent.__init__(self, DisplayEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.value = value

#--------------------
class SettingsEvent(wx.PyCommandEvent):
	def __init__(self, source, name):
		wx.PyCommandEvent.__init__(self, SettingsEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name

#--------------------
class MeasurementEvent(wx.PyCommandEvent):
	def __init__(self, source, measurement):
		wx.PyCommandEvent.__init__(self, MeasurementEventType, source.GetId())
		self.SetEventObject(source)
		self.measurement = measurement

#--------------------
class ImageClickedEvent(wx.PyCommandEvent):
	def __init__(self, source, xy):
		wx.PyCommandEvent.__init__(self, ImageClickedEventType, source.GetId())
		self.SetEventObject(source)
		self.xy = xy

#--------------------
def getColorMap():
	b = [0] * 512 + range(256) + [255] * 512 + range(255, -1, -1)
	g = b[512:] + b[:512]
	r = g[512:] + g[:512]
	return zip(r, g, b)

colormap = getColorMap()

#--------------------
bitmaps = {}
def getBitmap(filename):
	try:
		return bitmaps[filename]
	except KeyError:
		iconpath = icons.getPath(filename)
		wximage = wx.Image(iconpath)
		wximage.ConvertAlphaToMask()
		bitmap = wx.BitmapFromImage(wximage)
		bitmaps[filename] = bitmap
		return bitmap

##################################
##
##################################

class ContrastTool(object):
	def __init__(self, imagepanel, sizer):
		self.imagepanel = imagepanel
		self.imagemin = 0
		self.imagemax = 0
		self.contrastmin = 0
		self.contrastmax = 0
		self.slidermin = 0
		self.slidermax = 255

		self.minslider = wx.Slider(self.imagepanel, -1, self.slidermin, self.slidermin, self.slidermax, size=(200, -1))
		self.maxslider = wx.Slider(self.imagepanel, -1, self.slidermax, self.slidermin, self.slidermax, size=(200, -1))
		self.minslider.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.onMinSlider)
		self.maxslider.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.onMaxSlider)
		self.minslider.Bind(wx.EVT_SCROLL_ENDSCROLL, self.onMinSlider)
		self.maxslider.Bind(wx.EVT_SCROLL_ENDSCROLL, self.onMaxSlider)
		self.minslider.Bind(wx.EVT_SCROLL_THUMBTRACK, self.onMinSlider)
		self.maxslider.Bind(wx.EVT_SCROLL_THUMBTRACK, self.onMaxSlider)

		self.iemin = FloatEntry(imagepanel, -1, chars=6, allownone=False, value='%g' % self.contrastmin)
		self.iemax = FloatEntry(imagepanel, -1, chars=6, allownone=False, value='%g' % self.contrastmax)
		self.iemin.Enable(False)
		self.iemax.Enable(False)

		self.iemin.Bind(EVT_ENTRY, self.onMinEntry)
		self.iemax.Bind(EVT_ENTRY, self.onMaxEntry)

		self.sizer = wx.GridBagSizer(0, 0)
		self.sizer.Add(self.minslider, (0, 0), (1, 1), wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_BOTTOM)
		self.sizer.Add(self.iemin, (0, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.ALL, 2)
		self.sizer.Add(self.maxslider, (1, 0), (1, 1), wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP)
		self.sizer.Add(self.iemax, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.ALL, 2)
		sizer.Add(self.sizer, 0, wx.ALIGN_CENTER)

	#--------------------
	def _setSliders(self, value):
		if value[0] is not None:
			self.minslider.SetValue(self.getSliderValue(value[0]))
		if value[1] is not None:
			self.maxslider.SetValue(self.getSliderValue(value[1]))

	#--------------------
	def _setEntries(self, value):
		if value[0] is not None:
			self.iemin.SetValue(value[0])
		if value[1] is not None:
			self.iemax.SetValue(value[1])

	#--------------------
	def setSliders(self, value):
		if value[0] is not None:
			self.contrastmin = value[0]
		if value[1] is not None:
			self.contrastmax = value[1]
		self._setSliders(value)
		self._setEntries(value)

	#--------------------
	def updateNumericImage(self):
		self.imagepanel.setBitmap()
		self.imagepanel.setBuffer()
		self.imagepanel.UpdateDrawing()

	#--------------------
	def getRange(self):
		return self.contrastmin, self.contrastmax

	#--------------------
	def getScaledValue(self, position):
		try:
			scale = float(position - self.slidermin)/(self.slidermax - self.slidermin)
		except ZeroDivisionError:
			scale = 1.0
		return (self.imagemax - self.imagemin)*scale + self.imagemin

	#--------------------
	def getSliderValue(self, value):
		try:
			scale = (value - self.imagemin)/(self.imagemax - self.imagemin)
		except ZeroDivisionError:
			scale = 1.0
		return int(round((self.slidermax - self.slidermin)*scale + self.slidermin))

	#--------------------
	def setRange(self, range, value=None):
		if range is None:
			self.imagemin = 0
			self.imagemax = 0
			self.contrastmin = 0
			self.contrastmax = 0
			self.iemin.SetValue(0.0)
			self.iemax.SetValue(0.0)
			self.iemin.Enable(False)
			self.iemax.Enable(False)
			self.minslider.Enable(False)
			self.maxslider.Enable(False)
		else:
			self.imagemin = range[0]
			self.imagemax = range[1]
			if value is None:
				self.contrastmin = self.getScaledValue(self.minslider.GetValue())
				self.contrastmax = self.getScaledValue(self.maxslider.GetValue())
			else:
				self.setSliders(value)
			self.iemin.Enable(True)
			self.iemax.Enable(True)
			self.minslider.Enable(True)
			self.maxslider.Enable(True)

	#--------------------
	def onMinSlider(self, evt):
		position = evt.GetPosition()
		maxposition = self.maxslider.GetValue()
		if position > maxposition:
			self.minslider.SetValue(maxposition)
			self.contrastmin = self.contrastmax
		else:
			self.contrastmin = self.getScaledValue(position)
		self._setEntries((self.contrastmin, None))
		self.updateNumericImage()

	#--------------------
	def onMaxSlider(self, evt):
		position = evt.GetPosition()
		minposition = self.minslider.GetValue()
		if position < minposition:
			self.maxslider.SetValue(minposition)
			self.contrastmax = self.contrastmin
		else:
			self.contrastmax = self.getScaledValue(position)
		self._setEntries((None, self.contrastmax))
		self.updateNumericImage()

	#--------------------
	def onMinEntry(self, evt):
		contrastmin = evt.GetValue()
		if contrastmin < self.imagemin:
			self.contrastmin = self.imagemin
			self.iemin.SetValue(self.contrastmin)
		elif contrastmin > self.contrastmax:
			self.contrastmin = self.contrastmax
			self.iemin.SetValue(self.contrastmin)
		else:
			self.contrastmin = contrastmin
		self._setSliders((self.contrastmin, None))
		self.updateNumericImage()

	#--------------------
	def onMaxEntry(self, evt):
		contrastmax = evt.GetValue()
		if contrastmax > self.imagemax:
			self.contrastmax = self.imagemax
			self.iemax.SetValue(self.contrastmax)
		elif contrastmax < self.contrastmin:
			self.contrastmax = self.contrastmin
			self.iemax.SetValue(self.contrastmax)
		else:
			self.contrastmax = contrastmax
		self._setSliders((None, self.contrastmax))
		self.updateNumericImage()

##################################
##
##################################

class ImageTool(object):
	def __init__(self, imagepanel, sizer, bitmap, tooltip='', cursor=None,
			untoggle=False, button=None):
		self.sizer = sizer
		self.imagepanel = imagepanel
		self.cursor = cursor
		if button is None:
			self.button = GenBitmapToggleButton(self.imagepanel, -1, bitmap, size=(24, 24))
		else:
			self.button = button
		self.untoggle = untoggle
		self.button.SetBezelWidth(1)
		if tooltip:
			self.button.SetToolTip(wx.ToolTip(tooltip))
		self.sizer.Add(self.button, 0, wx.ALIGN_CENTER|wx.ALL, 3)
		self.button.Bind(wx.EVT_BUTTON, self.OnButton)

	#--------------------
	def OnButton(self, evt):
		if self.button.GetToggle():
			if self.untoggle:
				self.imagepanel.UntoggleTools(self)
			if self.cursor is not None:
				self.imagepanel.panel.SetCursor(self.cursor)
			self.OnToggle(True)
		else:
			self.imagepanel.panel.SetCursor(self.imagepanel.defaultcursor)
			self.OnToggle(False)

	#--------------------
	def OnToggle(self, value):
		pass

	#--------------------
	def OnLeftClick(self, evt):
		pass

	#--------------------
	def OnRightClick(self, evt):
		pass

	#--------------------
	def OnMotion(self, evt, dc):
		return False

	#--------------------
	def getToolTipStrings(self, x, y, value):
		return []

	#--------------------
	def Draw(self, dc):
		pass

##################################
##
##################################

class RecordMotionTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('value.png')
		tooltip = 'Toggle Show Value'
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip)
		self.button.SetToggle(False)
		self.start = None
		self.xypath = []
		self.lastx = 0
		self.lasty = 0

	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			if self.start is not None:
				x = evt.m_x #- self.imagepanel.offset[0]
				y = evt.m_y #- self.imagepanel.offset[1]
				x0, y0 = self.start
				self.xypath.append((x,y))
			self.start = self.imagepanel.view2image((evt.m_x, evt.m_y))
			print "start at LeftClick",self.start

	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.start = None
			print self.xypath
			self.xypath = []
			#self.imagepanel.UpdateDrawing()
	
	def DrawPolygon(self, dc, targets):
		color = wx.RED
		dc.SetPen(wx.Pen(color, 3))
		dc.SetBrush(wx.Brush(color, 1))
		scaledpoints = targets
		if len(scaledpoints)>=1:
			p1 = self.imagepanel.image2view(scaledpoints[0])
			dc.DrawCircle(p1[0],p1[1],1)
			
		for i,p1 in enumerate(scaledpoints[:-1]):
			p2 = scaledpoints[i+1]
			p1 = self.imagepanel.image2view(p1)
			p2 = self.imagepanel.image2view(p2)
			dc.DrawCircle(p2[0],p2[1],1)
			dc.DrawLine(p1[0], p1[1], p2[0], p2[1])
		# close it with final edge
		p1 = scaledpoints[-1]
		p2 = scaledpoints[0]
		p1 = self.imagepanel.image2view(p1)
		p2 = self.imagepanel.image2view(p2)
		dc.DrawLine(p1[0], p1[1], p2[0], p2[1])

	#--------------------
	def OnMotion(self, evt, dc):
		if self.button.GetToggle() and self.start is not None:
			x,y = self.imagepanel.view2image((evt.m_x, evt.m_y))
			self.xypath.append((x,y))
			self.DrawPolygon(dc,self.xypath)
			return True
		return False

	#--------------------
	def OnToggle(self, value):
		print "Toggled"
		if not value:
			self.start = None
			self.xypath = []
##################################
##
##################################

class ValueTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('value.png')
		tooltip = 'Toggle Show Value'
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip)
		self.button.SetToggle(False)


	#--------------------
	def valueString(self, x, y, value):
		if value is None:
			valuestr = 'N/A'
		else:
			valuestr = '%g' % value
		print x,y
		return '(%d, %d) %s' % (x, y, valuestr)

	#--------------------
	def getToolTipStrings(self, x, y, value):
		#self.imagepanel.pospanel.set({'x': x, 'y': y, 'value': value})
		if self.button.GetToggle():
			return [self.valueString(x, y, value)]
		else:
			return []

##################################
##
##################################

class CrosshairTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		self.color = wx.Color(0,150,150) #dark teal green
		bitmap = gui.wx.TargetPanelBitmaps.getTargetIconBitmap(self.color, shape='+')
		tooltip = 'Toggle Center Crosshair'
		cursor = None
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, False)

	#--------------------
	def Draw(self, dc):
		if not self.button.GetToggle():
			return
		dc.SetPen(wx.Pen(self.color, 1))
		width = self.imagepanel.bitmap.GetWidth()
		height = self.imagepanel.bitmap.GetHeight()
		if self.imagepanel.scaleImage():
			width /= self.imagepanel.scale[0]
			height /= self.imagepanel.scale[1]
		center = width/2, height/2
		x, y = self.imagepanel.image2view(center)
		width = self.imagepanel.buffer.GetWidth()
		height = self.imagepanel.buffer.GetHeight()
		dc.DrawLine(x, 0, x, height)
		dc.DrawLine(0, y, width, y)

	#--------------------
	def OnToggle(self, value):
		self.imagepanel.UpdateDrawing()

##################################
##
##################################

class ColormapTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('color.png')
		tooltip = 'Show Color'
		cursor = None
		imagepanel.colormap = None
		self.grayscalebitmap = getBitmap('grayscale.png')
		self.colorbitmap = bitmap
		button = GenBitmapButton(imagepanel, -1, bitmap, size=(24, 24))
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, False,
												button=button)

	#--------------------
	def OnButton(self, evt):
		if self.imagepanel.colormap is None:
			self.imagepanel.colormap = colormap
			self.button.SetBitmapLabel(self.grayscalebitmap)
			self.button.SetToolTip(wx.ToolTip('Show Grayscale'))
		else:
			self.imagepanel.colormap = None
			self.button.SetBitmapLabel(self.colorbitmap)
			self.button.SetToolTip(wx.ToolTip('Show Color'))
		self.imagepanel.setBitmap()
		self.imagepanel.UpdateDrawing()

##################################
##
##################################

class RulerTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('ruler.png')
		tooltip = 'Toggle Ruler Tool'
		cursor = wx.CROSS_CURSOR
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.start = None
		self.measurement = None

	#--------------------
	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			if self.start is not None:
				x = evt.m_x #- self.imagepanel.offset[0]
				y = evt.m_y #- self.imagepanel.offset[1]
				x0, y0 = self.start
				dx, dy = x - x0, y - y0
				self.measurement = {
					'from': self.start,
					'to': (x, y),
					'delta': (dx, dy),
					'magnitude': math.hypot(dx, dy),
					'angle': math.degrees(math.atan2(dy, dx)),
				}
				mevt = MeasurementEvent(self.imagepanel, dict(self.measurement))
				self.imagepanel.GetEventHandler().AddPendingEvent(mevt)
			self.start = self.imagepanel.view2image((evt.m_x, evt.m_y))

	#--------------------
	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.start = None
			self.measurement = None
			self.imagepanel.UpdateDrawing()

	#--------------------
	def OnToggle(self, value):
		if not value:
			self.start = None
			self.measurement = None

	#--------------------
	def DrawRuler(self, dc, x, y):
		dc.SetPen(wx.Pen(wx.RED, 2))
		x0, y0 = self.imagepanel.image2view(self.start)
		#x0 -= self.imagepanel.offset[0]
		#y0 -= self.imagepanel.offset[1]
		dc.DrawLine(x0, y0, x, y)

	#--------------------
	def OnMotion(self, evt, dc):
		if self.button.GetToggle() and self.start is not None:
			x = evt.m_x #- self.imagepanel.offset[0]
			y = evt.m_y #- self.imagepanel.offset[1]
			self.DrawRuler(dc, x, y)
			return True
		return False

	#--------------------
	def getToolTipStrings(self, x, y, value):
		if self.button.GetToggle() and self.start is not None:
			x0, y0 = self.start
			dx, dy = x - x0, y - y0
			return ['From (%d, %d) x=%d y=%d d=%.2f a=%.0f' % (x0, y0, dx, dy, math.hypot(dx, dy),math.degrees(math.atan2(dy, dx)))]
		else:
			return []

##################################
##
##################################

class ZoomTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('zoom.png')
		tooltip = 'Toggle Zoom Tool'
		cursor = wx.StockCursor(wx.CURSOR_MAGNIFIER)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.zoomlevels = [0.25, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 32, 128,]
		self.zoomlabels = ['4x', '2x', '1x', '2/3x', '1/2x', '1/3x', '1/4x', '1/6x', '1/8x',
			'1/12x', '1/16x', '1/32x', '1/128x']
		# wx.Choice seems a bit slow, at least on windows
		self.zoomchoice = wx.Choice(self.imagepanel, -1,
			choices=self.zoomlabels)
			#map(self.zoomlabels, self.zoomlevels))
		self.zoom(self.zoomlevels.index(1), (0, 0))
		self.zoomchoice.SetSelection(self.zoomlevel)
		self.sizer.Add(self.zoomchoice, 0, wx.ALIGN_CENTER|wx.ALL, 3)

		self.zoomchoice.Bind(wx.EVT_CHOICE, self.onChoice)

	#--------------------
	def log2str(self, value):
		if value == 1:
			return "1x"
		return '1/' + str(value) + 'x'
		if value < 0:
			return '1/' + str(int(1/2**value)) + 'x'
		else:
			return str(int(2**value)) + 'x'

	#--------------------
	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			self.zoomIn(evt.m_x, evt.m_y)

	#--------------------
	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.zoomOut(evt.m_x, evt.m_y)

	#--------------------
	def zoom(self, level, viewcenter):
		self.zoomlevel = level
		center = self.imagepanel.view2image(viewcenter)
		#scale = 2**self.zoomlevels[self.zoomlevel]
		scale = 1.0/float(self.zoomlevels[self.zoomlevel])
		self.imagepanel.setScale((scale, scale))
		self.imagepanel.center(center)
		self.imagepanel.UpdateDrawing()

	#--------------------
	def zoomIn(self, x, y):
		if self.zoomlevel > 0:
			self.zoom(self.zoomlevel - 1, (x, y))
			self.zoomchoice.SetSelection(self.zoomlevel)

	#--------------------
	def zoomOut(self, x, y):
		if self.zoomlevel < len(self.zoomlevels) - 1:
			self.zoom(self.zoomlevel + 1, (x, y))
			self.zoomchoice.SetSelection(self.zoomlevel)

	#--------------------
	def onChoice(self, evt):
		selection = evt.GetSelection()
		if selection == self.zoomlevel:
			return
		size = self.imagepanel.panel.GetSize()
		viewcenter = (size[0]/2, size[1]/2)
		self.zoom(selection, viewcenter)

##################################
##
##################################

class ClickTool(ImageTool):
	def __init__(self, imagepanel, sizer, disable=False):
		self._disable = disable
		self._disabled = False
		bitmap = getBitmap('arrow.png')
		tooltip = 'Click Tool'
		cursor = wx.StockCursor(wx.CURSOR_BULLSEYE)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)

	#--------------------
	def OnLeftClick(self, evt):
		if not self.button.GetToggle() or self._disabled:
			return
		if self._disable:
			self._disabled = True
		xy = self.imagepanel.view2image((evt.m_x, evt.m_y))
		idcevt = ImageClickedEvent(self.imagepanel, xy)
		self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)

	#--------------------
	def onImageClickDone(self, evt):
		self._disabled = False

##################################
##
##################################

class TypeTool(object):
	def __init__(self, parent, name, display=None, target=None, settings=None):
		self.parent = parent

		self.name = name

		self.label = wx.StaticText(parent, -1, name)

		self.bitmaps = self.getBitmaps()

		self.bitmap = wx.StaticBitmap(parent, -1, self.bitmaps['red'],
			(self.bitmaps['red'].GetWidth(), self.bitmaps['red'].GetHeight()) )

		self.togglebuttons = {}

		if display is not None:
			togglebutton = self.addToggleButton('display', 'Display')
			togglebutton.Bind(wx.EVT_BUTTON, self.onToggleDisplay)

		if settings is not None:
			togglebutton = self.addToggleButton('settings', 'Settings')
			togglebutton.Bind(wx.EVT_BUTTON, self.onSettingsButton)

	#--------------------
	def getBitmaps(self):
		return {
			'red': getBitmap('red.png'),
			'green': getBitmap('green.png'),
			'display': getBitmap('display.png'),
			'settings': getBitmap('settings.png'),
		}

	#--------------------
	def enableToggleButton(self, toolname, enable=True):
		togglebutton = self.togglebuttons[toolname]
		if enable:
			togglebutton.SetBezelWidth(1)
			#togglebutton.SetBackgroundColour(wx.Color(160, 160, 160))
		else:
			togglebutton.SetBezelWidth(0)
			#togglebutton.SetBackgroundColour(wx.WHITE)
		togglebutton.Enable(enable)

	#--------------------
	def addToggleButton(self, toolname, tooltip=None):
		bitmap = self.bitmaps[toolname]
		size = (24, 24)
		togglebutton = GenBitmapToggleButton(self.parent, -1, bitmap, size=size)
		togglebutton.SetBezelWidth(1)
		if tooltip is not None:
			togglebutton.SetToolTip(wx.ToolTip(tooltip))
		self.togglebuttons[toolname] = togglebutton
		return togglebutton

	#--------------------
	def SetBitmap(self, name):
		try:
			self.bitmap.SetBitmap(self.bitmaps[name])
		except KeyError:
			raise AttributeError

	#--------------------
	def onToggleDisplay(self, evt):
		#if self.togglebuttons['display'].GetValue() is True:
		#	self.togglebuttons['display'].SetBackgroundColour(wx.Color(160,160,160))
		#else:
		#	self.togglebuttons['display'].SetBackgroundColour(wx.WHITE)
		evt = DisplayEvent(evt.GetEventObject(), self.name, evt.GetIsDown())
		self.togglebuttons['display'].GetEventHandler().AddPendingEvent(evt)

	#--------------------
	def onSettingsButton(self, evt):
		evt = SettingsEvent(evt.GetEventObject(), self.name)
		self.togglebuttons['settings'].GetEventHandler().AddPendingEvent(evt)


