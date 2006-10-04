# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/RegionFinder.py,v $
# $Revision: 1.1 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-04 17:26:39 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import wx
import gui.wx.ImageViewer
import gui.wx.Settings
import gui.wx.TargetFinder
import wx.lib.filebrowsebutton as filebrowse
from gui.wx.Entry import Entry, IntEntry, FloatEntry
import gui.wx.TargetTemplate
import gui.wx.ToolBar
import threading

class Panel(gui.wx.TargetFinder.Panel):
	def initialize(self):
		gui.wx.TargetFinder.Panel.initialize(self)
		self.SettingsDialog = gui.wx.TargetFinder.SettingsDialog

		self.imagepanel = gui.wx.ImageViewer.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Original', display=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('Original', True)
		self.imagepanel.addTargetTool('Perimeter', wx.RED,
																	settings=True, target=True, shape='polygon')
		self.imagepanel.addTargetTool('Raster', wx.Color(255,128,0),
																	settings=True, target=True)

		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True,
																	settings=True, shape='polygon')
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True,
																	settings=True, shape='polygon')

		self.imagepanel.selectiontool.setDisplayed('Perimeter', True)
		self.imagepanel.selectiontool.setDisplayed('Raster', True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableCol(0)
		self.szmain.AddGrowableRow(1)

		self.Bind(gui.wx.ImageViewer.EVT_SETTINGS, self.onImageSettings)

	def onImageSettings(self, evt):
		if evt.name == 'Original':
			dialog = OriginalSettingsDialog(self)
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['image filename']
				if filename:
					self.node.readImage(filename)
			dialog.Destroy()
			return

		if evt.name == 'Perimeter':
			dialog = PerimeterSettingsDialog(self)
		elif evt.name == 'Raster':
			dialog = RasterSettingsDialog(self)

		elif evt.name == 'acquisition':
			dialog = FinalSettingsDialog(self)
		elif evt.name == 'focus':
			dialog = FinalSettingsDialog(self)

		dialog.ShowModal()
		dialog.Destroy()

class OriginalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['image filename'] = filebrowse.FileBrowseButton(self, -1)
		self.bok.SetLabel('Load')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['image filename'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Original Image')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class PerimeterSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		szoptions = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Minimum Region Area')
		self.widgets['min region area'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['min region area'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Minimum Region Area')
		self.widgets['max region area'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['max region area'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Vertex Evolution Limit')
		self.widgets['ve limit'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['ve limit'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [szoptions, szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		self.node.testFindRegions()

class RasterSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		szoptions = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Raster Spacing')
		self.widgets['raster spacing'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['raster spacing'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Raster Angle')
		self.widgets['raster angle'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['raster angle'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [szoptions, szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		self.node.testMakeRaster()


class FinalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['ice box size'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice thickness'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice min mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice max mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice max std'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus convolve'] = wx.CheckBox(self, -1, 'Convolve')
		self.widgets['focus convolve template'] = \
							gui.wx.TargetTemplate.Panel(self, 'Convolve Template')
		self.widgets['focus constant template'] = \
							gui.wx.TargetTemplate.Panel(self, 'Constant Template',
																					targetname='Constant target')
		self.widgets['acquisition convolve'] = wx.CheckBox(self, -1, 'Convolve')
		self.widgets['acquisition convolve template'] = \
							gui.wx.TargetTemplate.Panel(self, 'Convolve Template')
		self.widgets['acquisition constant template'] = \
							gui.wx.TargetTemplate.Panel(self, 'Constant Template',
																					targetname='Constant target')

		szice = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Box size:')
		szice.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice box size'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Reference Intensity:')
		szice.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice thickness'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Min. mean:')
		szice.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice min mean'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. mean:')
		szice.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max mean'], (3, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. stdev.:')
		szice.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max std'], (4, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szice.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Ice Analysis')
		sbszice = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszice.Add(szice, 1, wx.EXPAND|wx.ALL, 5)

		szft = wx.GridBagSizer(5, 5)
		szft.Add(self.widgets['focus convolve'], (0, 0), (1, 2),
										wx.ALIGN_CENTER_VERTICAL)
		szft.Add(self.widgets['focus convolve template'], (1, 0), (1, 1),
							wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szft.Add(self.widgets['focus constant template'], (2, 0), (1, 1),
							wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szft.AddGrowableCol(0)

		sb = wx.StaticBox(self, -1, 'Focus Targets')
		sbszft = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszft.Add(szft, 1, wx.EXPAND|wx.ALL, 5)

		szat = wx.GridBagSizer(5, 5)
		szat.Add(self.widgets['acquisition convolve'], (0, 0), (1, 2),
										wx.ALIGN_CENTER_VERTICAL)
		szat.Add(self.widgets['acquisition convolve template'], (1, 0), (1, 1),
							wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szat.Add(self.widgets['acquisition constant template'], (2, 0), (1, 1),
							wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szat.AddGrowableCol(0)

		sb = wx.StaticBox(self, -1, 'Acquisition Targets')
		sbszat = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszat.Add(szat, 1, wx.EXPAND|wx.ALL, 5)

		self.bice = wx.Button(self, -1, 'Analyze Ice')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bice, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		szt = wx.GridBagSizer(5, 5)
		szt.Add(sbszft, (0, 0), (1, 1), wx.EXPAND|wx.ALL)
		szt.Add(sbszat, (0, 1), (1, 1), wx.EXPAND|wx.ALL)

		self.Bind(wx.EVT_BUTTON, self.onAnalyzeIceButton, self.bice)

		return [sbszice, szt, szbutton]

	def onAnalyzeIceButton(self, evt):
		self.setNodeSettings()
		threading.Thread(target=self.node.ice).start()


if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Raster Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

