import wx
import threading

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		sb = wx.StaticBox(self, -1, 'Reference Target')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.sz = wx.GridBagSizer(5, 5)

		position = self.createBypassCheckBox((0, 0))
		position = self.createMoveTypeChoice((position[0],0))
		position = self.createPauseTimeEntry((position[0],0))
		position = self.createIntervalTimeEntry((position[0],0))

		sbsz.Add(self.sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

	def createMoveTypeChoice(self, start_position):
		move_types = self.node.calibration_clients.keys()
		move_types.sort()
		self.widgets['move type'] = Choice(self, -1, choices=move_types)
		szmovetype = wx.GridBagSizer(5, 5)
		szmovetype.Add(wx.StaticText(self, -1, 'Use'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(self.widgets['move type'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(wx.StaticText(self, -1, 'to move to the reference target'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(szmovetype, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

	def createPauseTimeEntry(self, start_position):
		self.widgets['pause time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds before performing request'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(szpausetime, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

	def createIntervalTimeEntry(self, start_position):
		self.widgets['interval time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		szintervaltime = wx.GridBagSizer(5, 5)
		szintervaltime.Add(wx.StaticText(self, -1, 'If request performed less than'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szintervaltime.Add(self.widgets['interval time'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szintervaltime.Add(wx.StaticText(self, -1, 'seconds ago, ignore request'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.sz.Add(szintervaltime, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

	def createBypassCheckBox(self,start_position):
		self.widgets['bypass'] = wx.CheckBox(self, -1, 'Bypass Conditioner')
		self.sz.Add(self.widgets['bypass'], start_position, (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		return start_position[0]+1,start_position[1]+1

class ScreenCurrentLoggerPanel(leginon.gui.wx.Reference.ReferencePanel):
	def _SettingsDialog(self,parent):
		# This "private call" ensures that the class in this module is loaded
		# instead of the one in module containing the parent class
		return SettingsDialog(parent)
	
	def onNodeInitialized(self):
		super(ScreenCurrentLoggerPanel,self).onNodeInitialized()

	def onTest(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		threading.Thread(target=self.node.onTest).start()
