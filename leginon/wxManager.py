import event
import manager
import uiclient
import wx
import wx.lib.intctrl

class ManagerApp(wx.App):
	def __init__(self, session, tcpport=None, xmlrpcport=None, **kwargs):
		self.session = session
		self.tcpport = tcpport
		self.xmlrpcport = xmlrpcport
		self.kwargs = kwargs
		wx.App.__init__(self, 0)

	def OnInit(self):
		self.manager = manager.Manager(self.session, self.tcpport, self.xmlrpcport,
																		**self.kwargs)
		self.SetTopWindow(self.manager.frame)
		self.manager.frame.Show(True)
		return True

	def OnExit(self):
		self.manager.exit()

class ManagerStatusBar(wx.StatusBar):
	def __init__(self, parent):
		wx.StatusBar.__init__(self, parent, -1)

class ManagerFrame(wx.Frame):
	def __init__(self, manager):
		self.manager = manager

		wx.Frame.__init__(self, None, -1, 'Manager', size=(750, 750))

		# menu
		self.menubar = wx.MenuBar()

		# file menu
		filemenu = wx.Menu()
		exit = wx.MenuItem(filemenu, -1, 'E&xit')
		self.Bind(wx.EVT_MENU, self.onExit, exit)
		filemenu.AppendItem(exit)
		self.menubar.Append(filemenu, '&File')

		# launcher menu
		self.launchermenu = wx.Menu()
		addmenuitem = wx.MenuItem(self.launchermenu, -1, '&Add')
		self.launcherkillmenu = wx.Menu()

		self.Bind(wx.EVT_MENU, self.onMenuAdd, addmenuitem)

		self.launchermenu.AppendItem(addmenuitem)
		self.launcherkillmenuitem = self.launchermenu.AppendMenu(-1, '&Kill',
																											self.launcherkillmenu)

		self.launcherkillmenuitem.Enable(False)

		self.menubar.Append(self.launchermenu, '&Launcher')

		# node menu
		self.nodemenu = wx.Menu()

		self.nodecreatemenuitem = wx.MenuItem(self.nodemenu, -1, '&Create')
		self.nodekillmenu = wx.Menu()

		self.Bind(wx.EVT_MENU, self.onMenuCreate, self.nodecreatemenuitem)

		self.nodemenu.AppendItem(self.nodecreatemenuitem)
		self.nodekillmenuitem = self.nodemenu.AppendMenu(-1, '&Kill',
																											self.nodekillmenu)

		self.nodecreatemenuitem.Enable(False)
		self.nodekillmenuitem.Enable(False)

		self.menubar.Append(self.nodemenu, '&Node')

		# event menu
		self.eventmenu = wx.Menu()
		self.bindmenuitem = wx.MenuItem(self.eventmenu, -1, '&Bind')
		self.Bind(wx.EVT_MENU, self.onMenuBind, self.bindmenuitem)
		self.eventmenu.AppendItem(self.bindmenuitem)
		self.bindmenuitem.Enable(False)
		self.menubar.Append(self.eventmenu, '&Event')

		self.SetMenuBar(self.menubar)

		# status bar
		self.statusbar = ManagerStatusBar(self)
		self.SetStatusBar(self.statusbar)

		self.panel = ManagerPanel(self, self.manager.uicontainer.location())

	def onExit(self, evt):
		self.manager.exit()
		self.Close()

	def onMenuCreate(self, evt):
		launchernames = self.manager.getLauncherNames()
		launcherclasses = self.manager.getLauncherClasses()
		nodenames = self.manager.getNodeNames()
		dialog = CreateNodeDialog(self, launchernames, launcherclasses, nodenames)
		if dialog.ShowModal() == wx.ID_OK:
			values = dialog.getValues()
			self.manager.launchNode(*values)
		dialog.Destroy()

	def onMenuAdd(self, evt):
		dialog = AddNodeDialog(self)
		if dialog.ShowModal() == wx.ID_OK:
			values = dialog.getValues()
			self.manager.addLauncher(*values)
		dialog.Destroy()

	def onMenuKill(self, evt):
		item = self.launcherkillmenu.FindItemById(evt.GetId())
		if item is None:
			item = self.nodekillmenu.FindItemById(evt.GetId())
		name = item.GetLabel()
		self.manager.killNode(name)

	def onMenuBind(self, evt):
		nodenames = self.manager.getNodeNames()
		eventio = {}
		for name in nodenames:
			eventio[name] = self.manager.getNodeEventIO(name)
		eventclasses = event.eventClasses()
		dialog = BindEventDialog(self, nodenames, eventio, eventclasses)
		if dialog.ShowModal() == wx.ID_OK:
			print 'ok!'
		dialog.Destroy()

	def onAddNode(self, name):
		# if it's in launcher kill menu don't add here
		if self.manager.getNodeCount() >= 2:
			self.bindmenuitem.Enable(True)
		item = self.launcherkillmenu.FindItem(name)
		if item is wx.NOT_FOUND:
			item = wx.MenuItem(self.nodekillmenu, -1, name)
			self.nodekillmenu.AppendItem(item)
			self.Bind(wx.EVT_MENU, self.onMenuKill, item)
			if not self.nodekillmenuitem.IsEnabled():
				self.nodekillmenuitem.Enable(True)

	def onRemoveNode(self, name):
		if self.manager.getNodeCount() < 2:
			self.bindmenuitem.Enable(False)
		item = self.nodekillmenu.FindItem(name)
		if item is not wx.NOT_FOUND:
			self.nodekillmenu.Delete(item)
			if self.nodekillmenu.GetMenuItemCount() < 1:
				self.nodekillmenuitem.Enable(False)

	def onAddLauncher(self, name):
		if not self.nodecreatemenuitem.IsEnabled():
			self.nodecreatemenuitem.Enable(True)

		item = wx.MenuItem(self.launcherkillmenu, -1, name)
		self.launcherkillmenu.AppendItem(item)
		self.Bind(wx.EVT_MENU, self.onMenuKill, item)
		if not self.launcherkillmenuitem.IsEnabled():
			self.launcherkillmenuitem.Enable(True)

	def onRemoveLauncher(self, name):
		if self.manager.getLauncherCount() < 1:
			self.nodecreatemenuitem.Enable(False)

		item = self.launcherkillmenu.FindItem(name)
		if item is not wx.NOT_FOUND:
			self.launcherkillmenu.Delete(item)
			if self.launcherkillmenu.GetMenuItemCount() < 1:
				self.launcherkillmenuitem.Enable(False)

class ManagerPanel(wx.ScrolledWindow):
	def __init__(self, parent, location):
		self._enabled = True
		self._shown = True
		wx.ScrolledWindow.__init__(self, parent, -1)
		self.SetScrollRate(5, 5)
		containerclass = uiclient.SimpleContainerWidget
		containerclass = uiclient.ClientContainerFactory(containerclass)
		self.container = containerclass('UI Client', self, self, location, {})
		self.SetSizer(self.container)
		self.Fit()

	def layout(self):
		pass

class AddNodeDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, 'Add Node')

		self.dialogsizer = wx.GridBagSizer()

		sizer = wx.GridBagSizer(3, 3)

		sizer.Add(wx.StaticText(self, -1, 'Hostname:'),
							(0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.hostnametextctrl = wx.TextCtrl(self, -1, '')
		sizer.Add(self.hostnametextctrl, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sizer.Add(wx.StaticText(self, -1, 'Port:'),
							(1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.portintctrl = wx.lib.intctrl.IntCtrl(self, -1, 55555,
																							min=0, limited=True)
		sizer.Add(self.portintctrl, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		buttonsizer = wx.GridBagSizer(0, 3)
		addbutton = wx.Button(self, wx.ID_OK, 'Add')
		addbutton.SetDefault()
		buttonsizer.Add(addbutton, (0, 0), (1, 1),
										wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

		cancelbutton = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		buttonsizer.Add(cancelbutton, (0, 1), (1, 1), wx.ALIGN_CENTER)

		buttonsizer.AddGrowableCol(0)

		sizer.Add(buttonsizer, (2, 0), (1, 2), wx.EXPAND)

		self.dialogsizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 10)
		self.SetSizerAndFit(self.dialogsizer)

	def getValues(self):
		return self.hostnametextctrl.GetValue(), self.portintctrl.GetValue()

class CreateNodeDialog(wx.Dialog):
	def __init__(self, parent, launchernames, launcherclasses, nodenames):
		self.launchernames = launchernames
		self.launcherclasses = launcherclasses
		self.nodenames = nodenames

		wx.Dialog.__init__(self, parent, -1, 'Create Node')

		self.dialogsizer = wx.GridBagSizer()

		sizer = wx.GridBagSizer(3, 3)
		sizer.Add(wx.StaticText(self, -1, 'Launcher:'), (0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)

		self.launcherchoice = wx.Choice(self, -1, choices=launchernames)
		self.launcherchoice.SetSelection(0)

		sizer.Add(self.launcherchoice, (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		sizer.Add(wx.StaticText(self, -1, 'Type:'), (1, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)

		# size it, then set it
		choices = self.launcherclasses[self.launcherchoice.GetStringSelection()]
		self.typechoice = wx.Choice(self, -1, choices=choices)
		self.typechoice.SetSelection(0)

		self.Bind(wx.EVT_CHOICE, self.onLauncherChoice, self.launcherchoice)

		sizer.Add(self.typechoice, (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		sizer.Add(wx.StaticText(self, -1, 'Name:'), (2, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)

		self.nametextctrl = wx.TextCtrl(self, -1, '')
		sizer.Add(self.nametextctrl, (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		buttonsizer = wx.GridBagSizer(0, 3)
		createbutton = wx.Button(self, wx.ID_OK, 'Create')
		createbutton.SetDefault()
		buttonsizer.Add(createbutton, (0, 0), (1, 1),
										wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		self.Bind(wx.EVT_BUTTON, self.onCreate, createbutton)

		cancelbutton = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		buttonsizer.Add(cancelbutton, (0, 1), (1, 1), wx.ALIGN_CENTER)

		buttonsizer.AddGrowableCol(0)

		sizer.Add(buttonsizer, (4, 0), (1, 2), wx.EXPAND)

		self.dialogsizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 10)
		self.SetSizerAndFit(self.dialogsizer)

	def onLauncherChoice(self, evt):
		self.Freeze()
		choice = self.typechoice.GetStringSelection()
		self.typechoice.Clear()
		self.typechoice.AppendItems(self.launcherclasses[evt.GetString()])
		selection = self.typechoice.FindString(choice)
		if selection == wx.NOT_FOUND:
			selection = 0
		self.typechoice.SetSelection(selection)
		self.dialogsizer.Layout()
		self.Thaw()

	def getValues(self):
		return (self.launcherchoice.GetStringSelection(),
						self.typechoice.GetStringSelection(),
						self.nametextctrl.GetValue())

	def onCreate(self, evt):
		name = self.nametextctrl.GetValue()
		e = None

		if not name:
			e = 'Invalid node name.'
		elif name in self.nodenames:
			e = 'Node name in use.'

		if e is None:
			evt.Skip()
		else:
			dlg = wx.MessageDialog(self, e, 'Node Create Error', wx.OK|wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()

class BindEventDialog(wx.Dialog):
	def __init__(self, parent, nodenames, eventio, eventclasses):
		self.nodenames = nodenames
		self.eventio = eventio
		self.eventclasses = eventclasses
		wx.Dialog.__init__(self, parent, -1, 'Bind Event')

		self.dialogsizer = wx.GridBagSizer()

		sizer = wx.GridBagSizer(5, 5)

		sizer.Add(wx.StaticText(self, -1, 'From:'), (0, 0), (1, 1),
																									wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(wx.StaticText(self, -1, 'Event:'), (0, 1), (1, 1),
																									wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(wx.StaticText(self, -1, 'To:'), (0, 2), (1, 1),
																									wx.ALIGN_CENTER_VERTICAL)

		self.fromlistbox = wx.ListBox(self, -1, choices=nodenames)
		self.eventlistbox = wx.ListBox(self, -1, choices=eventclasses.keys())
		self.tolistbox = wx.ListBox(self, -1, choices=nodenames)
		sizer.Add(self.fromlistbox, (1, 0), (1, 1), wx.EXPAND)
		sizer.Add(self.eventlistbox, (1, 1), (1, 1), wx.EXPAND)
		sizer.Add(self.tolistbox, (1, 2), (1, 1), wx.EXPAND)
		self.Bind(wx.EVT_LISTBOX, self.onFromSelect, self.fromlistbox)
		self.Bind(wx.EVT_LISTBOX, self.onToSelect, self.tolistbox)

		self.dialogsizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 10)
		self.SetSizerAndFit(self.dialogsizer)

	def getCommonEvents(self, fromname, toname):
		outputs = self.eventio[fromname]['outputs']
		inputs = self.eventio[toname]['inputs']
		events = []
		for output in outputs:
			if output in inputs:
				events.append(output.__name__)
		return events

	def restoreListBox(self, listbox):
		selection = listbox.GetStringSelection()
		listbox.Clear()
		listbox.AppendItems(self.nodenames)
		if listbox.FindString(selection) is not wx.NOT_FOUND:
			listbox.SetStringSelection(selection)

	def onFromSelect(self, evt):
		self.restoreListBox(self.tolistbox)

		name = evt.GetString()

		selection = self.eventlistbox.GetStringSelection()
		toname = self.tolistbox.GetStringSelection()
		if toname:
			events = self.getCommonEvents(name, toname)
		else:
			events = []

		self.eventlistbox.Clear()
		self.eventlistbox.AppendItems(events)
		if self.eventlistbox.FindString(selection) is not wx.NOT_FOUND:
			self.eventlistbox.SetStringSelection(selection)

		n = self.tolistbox.FindString(name)
		if n is not wx.NOT_FOUND:
			self.tolistbox.Delete(n)

	def onToSelect(self, evt):
		self.restoreListBox(self.fromlistbox)

		name = evt.GetString()

		selection = self.eventlistbox.GetStringSelection()
		fromname = self.fromlistbox.GetStringSelection()
		if fromname:
			events = self.getCommonEvents(fromname, name)
		else:
			events = []

		self.eventlistbox.Clear()
		self.eventlistbox.AppendItems(events)
		if self.eventlistbox.FindString(selection) is not wx.NOT_FOUND:
			self.eventlistbox.SetStringSelection(selection)

		n = self.fromlistbox.FindString(name)
		if n is not wx.NOT_FOUND:
			self.fromlistbox.Delete(n)

