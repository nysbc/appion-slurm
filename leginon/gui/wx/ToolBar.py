# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ToolBar.py,v $
# $Revision: 1.25 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-24 21:35:53 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import icons
import wx

ID_SETTINGS = 10001
ID_ACQUIRE = 10002
ID_PLAY = 10003
ID_PAUSE = 10004
ID_STOP = 10005
ID_CALIBRATE = 10006
ID_MEASURE = 10007
ID_ABORT = 10008
ID_SUBMIT = 10009
ID_ACQUISITION_TYPE = 10010
ID_MEASURE_DRIFT = 10011
ID_DECLARE_DRIFT = 10012
ID_CHECK_DRIFT = 10013
ID_REFRESH = 10014
ID_PAUSES = 10015
ID_AUTOFOCUS = 10016
ID_MANUAL_FOCUS = 10017
ID_MODEL = 10018
ID_GRID = 10019
ID_TILES = 10020
ID_MOSAIC = 10021
ID_CURRENT_POSITION = 10022
ID_FIND_SQUARES = 10023
ID_ATLAS = 10024
ID_STAGE_LOCATIONS = 10025
ID_PARAMETER_SETTINGS = 10026
ID_GET_INSTRUMENT = 10027
ID_SET_INSTRUMENT = 10028
ID_CALCULATE = 10029
ID_PLUS = 10030
ID_MINUS = 10031
ID_VALUE = 10032
ID_RESET = 10033
ID_SIMULATE_TARGET = 10034
ID_ABORT_DRIFT = 10035
ID_INSERT = 10036
ID_EXTRACT = 10037
ID_SIMULATE_TARGET_LOOP = 10038
ID_SIMULATE_TARGET_LOOP_STOP = 10039
ID_BROWSE_IMAGES = 10040

class ToolBar(wx.ToolBar):
	def __init__(self, parent):
#		pre = wx.PreToolBar()
#		pre.Show(False)
#		pre.Create(parent, -1, style=wx.TB_HORIZONTAL|wx.NO_BORDER)
#		self.this = pre.this
#		self._setOORInfo(self)
		wx.ToolBar.__init__(self, parent, -1, style=wx.TB_HORIZONTAL|wx.NO_BORDER)
		#self.spacer = wx.StaticText(self, -1, '')
		self.spacer = wx.Control(self, -1, style=wx.NO_BORDER)
		self.AddControl(self.spacer)

	def AddTool(self, id, bitmap, **kwargs):
		bitmap = '%s.png' % bitmap
		image = wx.Image(icons.getPath(bitmap))
		image.ConvertAlphaToMask(64)
		bitmap = wx.BitmapFromImage(image)
		wx.ToolBar.AddTool(self, id, bitmap, **kwargs)

	def InsertTool(self, pos, id, bitmap, **kwargs):
		bitmap = '%s.png' % bitmap
		bitmap = wx.BitmapFromImage(wx.Image(icons.getPath(bitmap)))
		wx.ToolBar.InsertTool(self, pos, id, bitmap, **kwargs)
