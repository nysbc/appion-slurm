import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Settings
import gui.wx.TargetFinder
import gui.wx.ClickTargetFinder
import gui.wx.ToolBar

class Panel(gui.wx.ClickTargetFinder.Panel):
	icon = 'atlastarget'
	def initialize(self):
		gui.wx.ClickTargetFinder.Panel.initialize(self)

		self.toolbar.InsertTool(2, gui.wx.ToolBar.ID_TILES,
													'tiles',
													shortHelpString='Tiles')
		self.toolbar.InsertTool(3, gui.wx.ToolBar.ID_MOSAIC,
													'atlasmaker',
													shortHelpString='Mosaic')
		self.toolbar.InsertTool(4, gui.wx.ToolBar.ID_REFRESH,
													'refresh',
													shortHelpString='Refresh')
		self.toolbar.InsertTool(5, gui.wx.ToolBar.ID_CURRENT_POSITION,
													'currentposition',
													shortHelpString='Show Position')
		self.toolbar.InsertTool(6, gui.wx.ToolBar.ID_FIND_SQUARES,
													'squarefinder',
													shortHelpString='Find Squares')

		self.rbdisplay = {}
		self.rbdisplay['Original'] = wx.RadioButton(self, -1, 'Originial',
																							style=wx.RB_GROUP)
		self.rbdisplay['Filtered'] = wx.RadioButton(self, -1, 'Filtered')
		self.rbdisplay['Thresholded'] = wx.RadioButton(self, -1, 'Thresholded')

		self.blpfsettings = wx.Button(self, -1, 'Settings...')
		self.bblobsettings = wx.Button(self, -1, 'Settings...')

		sz = self._getStaticBoxSizer('Display', (2, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.rbdisplay['Original'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.rbdisplay['Filtered'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.rbdisplay['Thresholded'], (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.blpfsettings, (1, 1), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.bblobsettings, (2, 1), (1, 1), wx.ALIGN_CENTER)
		self.Bind(gui.wx.TargetFinder.EVT_IMAGE_UPDATED, self.onImageUpdated)

	def onImageUpdated(self, evt):
		if self.rbdisplay[evt.name].GetValue():
			self.imagepanel.setImage(evt.image)
			if evt.targets is not None:
				self.imagepanel.clearTargets()
				for typename, targetlist in evt.targets.items():
					for target in targetlist:
						x, y = target
						self.imagepanel.addTarget(typename, x, y)

	def imageUpdated(self, name, image, targets=None):
		evt = gui.wx.TargetFinder.ImageUpdatedEvent(self, name, image, targets)
		self.GetEventHandler().AddPendingEvent(evt)

	def onDisplayRadioButton(self, evt):
		for key, value in self.rbdisplay.items():
			if value.GetValue():
				try:
					image = self.node.images[key]
				except KeyError:
					image = None
				self.imagepanel.setImage(image)
				break

	def onNodeInitialized(self):
		gui.wx.ClickTargetFinder.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onTilesButton,
											id=gui.wx.ToolBar.ID_TILES)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMosaicButton,
											id=gui.wx.ToolBar.ID_MOSAIC)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshTargetsButton,
											id=gui.wx.ToolBar.ID_REFRESH)
		self.toolbar.Bind(wx.EVT_TOOL, self.onShowPositionButton,
											id=gui.wx.ToolBar.ID_CURRENT_POSITION)
		self.toolbar.Bind(wx.EVT_TOOL, self.onFindSquaresButton,
											id=gui.wx.ToolBar.ID_FIND_SQUARES)

		self.Bind(wx.EVT_BUTTON, self.onLPFSettingsButton, self.blpfsettings)
		self.Bind(wx.EVT_BUTTON, self.onBlobSettingsButton, self.bblobsettings)
		for value in self.rbdisplay.values():
			self.Bind(wx.EVT_RADIOBUTTON, self.onDisplayRadioButton, value)

	def onTilesButton(self, evt):
		choices = self.node.getMosaicNames()
		dialog = TilesDialog(self, choices)
		result = dialog.ShowModal()
		if result == wx.ID_OK:
			selection = self.cmosaic.GetStringSelection()
			if selection:
				self.node.loadMosaicTiles(selection)
		elif result == wx.ID_RESET:
			self.node.clearTiles()
		dialog.Destroy()

	def onMosaicButton(self, evt):
		dialog = MosaicSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onRefreshTargetsButton(self, evt):
		self.node.displayDatabaseTargets()

	def onShowPositionButton(self, evt):
		self.node.refreshCurrentPosition()

	def onLPFSettingsButton(self, evt):
		dialog = LPFSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onBlobSettingsButton(self, evt):
		dialog = BlobSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onFindSquaresButton(self, evt):
		self.node.findSquares()

class TilesDialog(wx.Dialog):
	def __init__(self, parent, choices):
		wx.Dialog.__init__(self, parent, -1, 'Tiles')

		self.cmosaic = wx.Choice(self, -1, choices=choices)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Load tiles from mosaic:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.cmosaic, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		bload = wx.Button(self, wx.ID_OK, 'Load')
		breset = wx.Button(self, -1, 'Reset')
		bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		if not choices:
			self.cmosaic.Enable(False)
			self.cmosaic.Append('(No mosaics)')
			bload.Enable(False)
		self.cmosaic.SetSelection(0)

		szbuttons = wx.GridBagSizer(5, 5)
		szbuttons.Add(bload, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(breset, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(bcancel, (0, 2), (1, 1), wx.ALIGN_CENTER)

		szdialog = wx.GridBagSizer(5, 5)
		szdialog.Add(sz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		szdialog.Add(szbuttons, (1, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)

		self.SetSizerAndFit(szdialog)

		self.Bind(wx.EVT_BUTTON, self.onResetButton, breset)

	def onResetButton(self, evt):
		self.EndModal(wx.ID_RESET)

class MosaicSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		choices = self.node.calclients.keys()
		self.widgets['calibration parameter'] = Choice(self, -1, choices=choices)
		self.widgets['scale image'] = wx.CheckBox(self, -1, 'Scale image to')
		self.widgets['scale size'] = IntEntry(self, -1, min=1, chars=4)
		self.widgets['mosaic image on tile change'] = wx.CheckBox(self, -1,
																	'Create mosaic image when tile list changes')

		self.bcreate = wx.Button(self, -1, 'Create')
		self.bsave = wx.Button(self, -1, 'Save')

		szp = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Calibration parameter')
		szp.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szp.Add(self.widgets['calibration parameter'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		szs = wx.GridBagSizer(5, 5)
		szs.Add(self.widgets['scale image'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		szs.Add(self.widgets['scale size'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'pixels in largest dimension')
		szs.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szb = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Mosaic image:')
		szb.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szb.Add(self.bcreate, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szb.Add(self.bsave, (0, 2), (1, 1), wx.ALIGN_CENTER)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szp, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szs, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['mosaic image on tile change'], (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szb, (3, 0), (1, 1), wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Mosaics')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		self.bcreate.Enable(self.node.mosaic.hasTiles())
		self.bsave.Enable(self.node.hasMosaicImage())

		self.Bind(wx.EVT_BUTTON, self.onCreateButton, self.bcreate)
		self.Bind(wx.EVT_BUTTON, self.onSaveButton, self.bsave)

		return [sbsz]

	def onCreateButton(self, evt):
		self.node.createMosaicImage()
		self.bsave.Enable(self.node.hasMosaicImage())

	def onSaveButton(self, evt):
		self.node.publishMosaicImage()

class LPFSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		self.widgets['size'] = IntEntry(self, -1, min=1, chars=4)
		self.widgets['sigma'] = FloatEntry(self, -1, min=0.0, chars=4)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Size:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['size'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Sigma:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['sigma'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		sz.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Low Pass Filter')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class BlobSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		self.widgets['threshold'] = IntEntry(self, -1, min=0, chars=4)
		self.widgets['border'] = IntEntry(self, -1, min=0, chars=4)
		self.widgets['max blobs'] = IntEntry(self, -1, min=0, chars=4)
		self.widgets['min blob size'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['max blob size'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['min blob mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['max blob mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['min blob stdev'] = FloatEntry(self, -1, chars=6)
		self.widgets['max blob stdev'] = FloatEntry(self, -1, chars=6)

		szrange = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Min.')
		szrange.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Max.')
		szrange.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Blob size:')
		szrange.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER)
		szrange.Add(self.widgets['min blob size'], (1, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange.Add(self.widgets['max blob size'], (1, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Blob mean:')
		szrange.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER)
		szrange.Add(self.widgets['min blob mean'], (2, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange.Add(self.widgets['max blob mean'], (2, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Blob stdev.:')
		szrange.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER)
		szrange.Add(self.widgets['min blob stdev'], (3, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange.Add(self.widgets['max blob stdev'], (3, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Border:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['border'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. number of blobs:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['max blobs'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		sz.Add(szrange, (2, 0), (1, 2), wx.ALIGN_CENTER)
		sz.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Blob Finding')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Mosaic Click Target Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

