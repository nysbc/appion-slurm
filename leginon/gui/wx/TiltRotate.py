# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar
from gui.wx.Entry import Entry

class Panel(gui.wx.Node.Panel):
	icon = 'targetfilter'
	def __init__(self, *args, **kwargs):
		gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS, 'settings', shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY, 'play', shortHelpString='Submit')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ABORT, 'stop', shortHelpString='Abort')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, False)

		self.toolbar.Realize()

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, True)
		self.node.onContinue()

	def onStopTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)
		self.node.player.stop()

	def onNodeInitialized(self):
		self.Bind(gui.wx.Events.EVT_PLAYER, self.onPlayer)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool, id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=gui.wx.ToolBar.ID_ABORT)

	def onPlayer(self, evt):
		if evt.state == 'play':
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, True)
		if evt.state == 'pause':
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, False)
		elif evt.state == 'stop':
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, False)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Tilt Rotate Target Repeater')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['bypass'] = wx.CheckBox(self, -1, 'Bypass Repeater')
		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['bypass'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['tilts'] = Entry(self, -1, chars=15, style=wx.ALIGN_RIGHT)
		sz.Add(self.widgets['tilts'], (1, 0), (1, 1), wx.EXPAND)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		

		return [sbsz]

