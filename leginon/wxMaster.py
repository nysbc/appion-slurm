from wxPython.wx import *
import wxObjectCanvas

class RenameDialog(wxDialog):
	def __init__(self, parent, id, title='Rename', pos=wxDefaultPosition,
								size=wxDefaultSize, style=wxDEFAULT_DIALOG_STYLE):

		wxDialog.__init__(self, parent, id, title, pos, size, style)
		sizer = wxBoxSizer(wxVERTICAL)

		box = wxBoxSizer(wxHORIZONTAL)
		label = wxStaticText(self, -1, 'New Name:')
		box.Add(label, 0, wxALIGN_CENTER|wxALL, 3)
		self.name_entry = wxTextCtrl(self, -1, '')
		box.Add(self.name_entry, 1, wxALIGN_CENTER|wxALL, 3)
		sizer.AddSizer(box)

		box = wxBoxSizer(wxHORIZONTAL)
		button = wxButton(self, wxID_OK, 'OK')
		button.SetDefault()
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		button = wxButton(self, wxID_CANCEL, 'Cancel')
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		sizer.AddSizer(box)

		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)

	def GetValue(self):
		return self.name_entry.GetValue()

	def SetValue(self, name):
		self.name_entry.SetValue(name)

class BindingConnectionPoint(wxObjectCanvas.wxConnectionPointObject):
	def __init__(self, eventclass, color=wxBLACK):
		self.eventclass = eventclass
		self.setDrawText(False)
		wxObjectCanvas.wxConnectionPointObject.__init__(self, color)

	def getDrawText(self):
		return self.drawtext

	def setDrawText(self, value):
		self.drawtext = value

	def OnStartConnection(self, evt):
		evt.Skip()

	def OnEndConnection(self, evt):
		evt.Skip()

	def OnCancelConnection(self, evt):
		evt.Skip()

	def OnEnter(self, evt):
		self.setDrawText(True)
		self.UpdateDrawing()

	def OnLeave(self, evt):
		self.setDrawText(False)
		self.UpdateDrawing()

class BindingInput(BindingConnectionPoint):
	def __init__(self, eventclass):
		BindingConnectionPoint.__init__(self, eventclass, wxRED)
		self.popupmenu = None

	def Draw(self, dc):
		BindingConnectionPoint.Draw(self, dc)
		if self.getDrawText():
			x, y = self.getCanvasPosition()
			#y = y - self.height
			dc.DrawRotatedText(self.eventclass, x, y, 90)

class BindingOutput(BindingConnectionPoint):
	def __init__(self, eventclass):
		BindingConnectionPoint.__init__(self, eventclass, wxBLUE)

		self.popupmenu = wxMenu()
		self.popupmenu.Append(101, 'Add Binding...')
		EVT_MENU(self.popupmenu, 101, self.menuAddBinding)

	def menuAddBinding(self, evt):
		binding = Binding(self.eventclass, self, None)
		self.ProcessEvent(wxObjectCanvas.StartConnectionEvent(binding))

	def Draw(self, dc):
		BindingConnectionPoint.Draw(self, dc)
		if self.getDrawText():
			x, y = self.getCanvasPosition()
			x = x + self.width
			y = y + self.height
			dc.DrawRotatedText(self.eventclass, x, y, -90)

class Node(wxObjectCanvas.wxRectangleObject):
	def __init__(self, name):
		self.name = name
		wxObjectCanvas.wxRectangleObject.__init__(self, 60, 60, wxColor(128,0,128))
		self.addText(self.name)

		self.popupmenu.Append(101, 'Rename...')
		self.popupmenu.Append(103, 'Delete')
		EVT_MENU(self.popupmenu, 101, self.menuRename)
		EVT_MENU(self.popupmenu, 103, self.menuDelete)

	def getName(self):
		return self.name

	def setName(self, name):
		self.removeText(self.name)
		self.name = name
		self.addText(self.name)

	def menuRename(self, evt):
		dialog = RenameDialog(None, -1)
		dialog.SetValue(self.getName())
		if dialog.ShowModal() == wxID_OK:
			self.setName(dialog.GetValue())
			self.UpdateDrawing()
		dialog.Destroy()

	def menuDelete(self, evt):
		self.removeBindings()
		self.delete()

	def addShapeObject(self, so, x=0, y=0):
		if isinstance(so, BindingConnectionPoint):
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		else:
			raise TypeError('Invalid object type to add')

	def addConnectionInput(self, cpo):
		if isinstance(cpo, BindingInput):
			wxObjectCanvas.wxRectangleObject.addConnectionInput(self, cpo)
		else:
			raise TypeError('Invalid object type for input')

	def addConnectionOutput(self, cpo):
		if isinstance(cpo, BindingOutput):
			wxObjectCanvas.wxRectangleObject.addConnectionOutput(self, cpo)
		else:
			raise TypeError('Invalid object type for output')

	def OnMotion(self, evt):
		wxObjectCanvas.wxRectangleObject.OnMotion(self, evt)
		#evt.Skip()

	def OnEnter(self, evt):
		for i in self.connectioninputs + self.connectionoutputs:
			i.setDrawText(True)
		self.UpdateDrawing()

	def OnLeave(self, evt):
		wxObjectCanvas.wxRectangleObject.OnLeave(self, evt)
		for i in self.connectioninputs + self.connectionoutputs:
			i.setDrawText(False)
		self.UpdateDrawing()

	def removeBindings(self):
		for so in self.shapeobjects:
			self.removeConnectionObjects(so)

	def OnStartConnection(self, evt):
		evt.Skip()

	def OnEndConnection(self, evt):
		evt.Skip()

	def OnCancelConnection(self, evt):
		evt.Skip()

class BindingLabel(wxObjectCanvas.wxRectangleObject):
	def __init__(self, text, color=wxBLACK):
		wxObjectCanvas.wxRectangleObject.__init__(self, 0, 0)
		self.addText(text)

		self.popupmenu.Append(103, 'Delete')
		EVT_MENU(self.popupmenu, 103, self.menuDelete)

	def menuDelete(self, evt):
		self.parent.delete()
		self.delete()

	def OnLeftDragStart(self, evt):
		pass

	def OnMotion(self, evt):
		pass

	def Draw(self, dc):
		width, height = 0, 0
		for text in self.text:
			x, y = self.text[text]
			w, h = dc.GetTextExtent(text)
			if w + x > width:
				width = w + x
			if h + y > height:
				height = h + y
		self.width = width + 3
		self.height = height + 3
		wxObjectCanvas.wxRectangleObject.Draw(self, dc)

class Binding(wxObjectCanvas.wxConnectionObject):
	def __init__(self, name, fromnode=None, tonode=None):
		self.name = name
		wxObjectCanvas.wxConnectionObject.__init__(self, fromnode, tonode)
		self.label = BindingLabel(self.name)
		self.addShapeObject(self.label)

	def _crookedLine(self, dc, so1, x, y):
		x1, y1 = wxObjectCanvas.wxConnectionObject._crookedLine(self, dc, so1, x, y)
		self.setLabelPosition(x1, y1, x, y)

	def crookedLine(self, dc, so1, so2):
		x1, y1, x2, y2 = wxObjectCanvas.wxConnectionObject.crookedLine(self, dc,
																																		so1, so2)
		self.setLabelPosition(x1, y1, x2, y2)

	def setLabelPosition(self, x1, y1, x2, y2):
		xoffset, yoffset = self.getCanvasPosition()
		lx = (x2 - x1)/2 + x1 - xoffset - self.label.width/2
		ly = (y2 - y1)/2 + y1 - yoffset - self.label.height/2
		self.label.setPosition(lx, ly)

class AddNodeDialog(wxDialog):
	def __init__(self, parent, id, title='Add Node', pos=wxDefaultPosition,
								size=wxDefaultSize, style=wxDEFAULT_DIALOG_STYLE):

		wxDialog.__init__(self, parent, id, title, pos, size, style)
		sizer = wxBoxSizer(wxVERTICAL)

		box = wxBoxSizer(wxHORIZONTAL)
		label = wxStaticText(self, -1, 'Alias:')
		box.Add(label, 0, wxALIGN_CENTER|wxALL, 3)
		self.aliasentry = wxTextCtrl(self, -1, '')
		box.Add(self.aliasentry, 1, wxALIGN_CENTER|wxALL, 3)
		sizer.AddSizer(box)

		box = wxBoxSizer(wxHORIZONTAL)
		label = wxStaticText(self, -1, 'Class:')
		box.Add(label, 0, wxALIGN_CENTER|wxALL, 3)
		self.classentry = wxTextCtrl(self, -1, '')
		box.Add(self.classentry, 1, wxALIGN_CENTER|wxALL, 3)
		sizer.AddSizer(box)

		box = wxBoxSizer(wxHORIZONTAL)
		button = wxButton(self, wxID_OK, 'Add')
		button.SetDefault()
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		button = wxButton(self, wxID_CANCEL, 'Cancel')
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		sizer.AddSizer(box)

		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)

	def GetValue(self):
		return self.aliasentry.GetValue(), self.classentry.GetValue()

	def SetValue(self, alias, nodeclass):
		self.aliasentry.SetValue(alias)
		self.classentry.SetValue(nodeclass)

class Launcher(wxObjectCanvas.wxRectangleObject):
	def __init__(self, name):
		self.name = name
		wxObjectCanvas.wxRectangleObject.__init__(self, 150, 150, wxColor(0,128,0))
		self.addText(self.name)

		self.popupmenu.Append(101, 'Rename...')
		self.popupmenu.Append(102, 'Add Node...')
		self.popupmenu.Append(103, 'Delete')
		EVT_MENU(self.popupmenu, 101, self.menuRename)
		EVT_MENU(self.popupmenu, 102, self.menuAddNode)
		EVT_MENU(self.popupmenu, 103, self.menuDelete)

	def getName(self):
		return self.name

	def setName(self, name):
		self.removeText(self.name)
		self.name = name
		self.addText(self.name)

	def menuRename(self, evt):
		dialog = RenameDialog(None, -1)
		dialog.SetValue(self.getName())
		if dialog.ShowModal() == wxID_OK:
			self.setName(dialog.GetValue())
			self.UpdateDrawing()
		dialog.Destroy()

	def menuAddNode(self, evt):
		dialog = AddNodeDialog(None, -1)
		if dialog.ShowModal() == wxID_OK:
			alias, nodeclass = dialog.GetValue()
			self.addShapeObject(Node(alias))
		dialog.Destroy()

	def menuDelete(self, evt):
		for node in self.getNodes():
			node.removeBindings()
		self.delete()

	def addShapeObject(self, so, x=0, y=0):
		if isinstance(so, Node):
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		else:
			raise TypeError('Invalid object type to add')

	def getNodes(self):
		nodes = []
		for node in self.shapeobjects:
			if isinstance(node, Node):
				nodes.append(node)
		return nodes

	def OnStartConnection(self, evt):
		evt.Skip()

	def OnEndConnection(self, evt):
		evt.Skip()

	def OnCancelConnection(self, evt):
		evt.Skip()

class AddLauncherDialog(wxDialog):
	def __init__(self, parent, id, title='Add Launcher', pos=wxDefaultPosition,
								size=wxDefaultSize, style=wxDEFAULT_DIALOG_STYLE):

		wxDialog.__init__(self, parent, id, title, pos, size, style)
		sizer = wxBoxSizer(wxVERTICAL)

		box = wxBoxSizer(wxHORIZONTAL)
		label = wxStaticText(self, -1, 'Alias:')
		box.Add(label, 0, wxALIGN_CENTER|wxALL, 3)
		self.aliasentry = wxTextCtrl(self, -1, '')
		box.Add(self.aliasentry, 1, wxALIGN_CENTER|wxALL, 3)
		sizer.AddSizer(box)

		box = wxBoxSizer(wxHORIZONTAL)
		button = wxButton(self, wxID_OK, 'Add')
		button.SetDefault()
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		button = wxButton(self, wxID_CANCEL, 'Cancel')
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		sizer.AddSizer(box)

		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)

	def GetValue(self):
		return self.aliasentry.GetValue()

	def SetValue(self, alias):
		self.aliasentry.SetValue(alias)

class Application(wxObjectCanvas.wxRectangleObject):
	def __init__(self, name):
		self.name = name
		wxObjectCanvas.wxRectangleObject.__init__(self, 700, 700, wxColor(128,0,0))
		self.addText(self.name)

		self.startedbinding = None

		self.popupmenu.Append(101, 'Rename...')
		self.popupmenu.Append(102, 'Add Launcher...')
		self.popupmenu.Append(103, 'Delete')
		EVT_MENU(self.popupmenu, 101, self.menuRename)
		EVT_MENU(self.popupmenu, 102, self.menuAddLauncher)
		EVT_MENU(self.popupmenu, 103, self.menuDelete)

	def getName(self):
		return self.name

	def setName(self, name):
		self.removeText(self.name)
		self.name = name
		self.addText(self.name)

	def menuRename(self, evt):
		dialog = RenameDialog(None, -1)
		dialog.SetValue(self.getName())
		if dialog.ShowModal() == wxID_OK:
			self.setName(dialog.GetValue())
			self.UpdateDrawing()
		dialog.Destroy()

	def menuAddLauncher(self, evt):
		dialog = AddLauncherDialog(None, -1)
		if dialog.ShowModal() == wxID_OK:
			alias = dialog.GetValue()
			self.addShapeObject(Launcher(alias))
		dialog.Destroy()

	def menuDelete(self, evt):
		self.delete()

	def getLaunchers(self):
		launchers = []
		for shapeobject in self.shapeobjects:
			if isinstance(shapeobject, Launcher):
				launchers.append(shapeobject)
		return launchers

	def getNodes(self):
		nodes = []
		for launcher in self.getLaunchers():
			nodes += launcher.getNodes()
		return nodes

	def OnMotion(self, evt):
		wxObjectCanvas.wxRectangleObject.OnMotion(self, evt)
		evt.Skip(False)

	def addShapeObject(self, so, x=0, y=0):
		if isinstance(so, Launcher):
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		elif isinstance(so, BindingLabel):
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		elif isinstance(so, Binding):
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		else:
			raise TypeError('Invalid object type to add')

	def OnEndConnection(self, evt):
		if self.connection is not None:
			if self.connection.name == evt.toso.eventclass:
				for i in self.connectionobjects:
					if i.getFromShapeObject() == self.connection.getFromShapeObject():
						if i.getToShapeObject() == evt.toso:
							return
				wxObjectCanvas.wxRectangleObject.OnEndConnection(self, evt)

class Master(wxObjectCanvas.wxRectangleObject):
	def __init__(self):
		wxObjectCanvas.wxRectangleObject.__init__(self, 800, 800)
		self.addText('Master')

if __name__ == '__main__':
	import time

	class MasterApp(wxApp):
		def OnInit(self):
			self.frame = wxFrame(NULL, -1, 'Master Application')
			self.SetTopWindow(self.frame)
			self.panel = wxPanel(self.frame, -1)
			self.master = Master()
			self.objectcanvas = wxObjectCanvas.wxObjectCanvas(self.panel, -1,
																												self.master)
			self.objectcanvas.SetSize((800, 800))
			self.panel.Fit()
			self.panel.Show(true)
			self.frame.Fit()
			self.frame.Show(true)
			return true

	class ApplicationApp(wxApp):
		def OnInit(self):
			self.frame = wxFrame(NULL, -1, 'Master Application')
			self.SetTopWindow(self.frame)
			self.panel = wxPanel(self.frame, -1)
			self.master = Application('New Application')
			self.objectcanvas = wxObjectCanvas.wxObjectCanvas(self.panel, -1,
																												self.master)
			self.objectcanvas.SetSize((800, 800))
			self.panel.Fit()
			self.panel.Show(true)
			self.frame.Fit()
			self.frame.Show(true)
			return true

	#app = MasterApp(0)
	app = ApplicationApp(0)
	app.frame.Fit()

	l0 = Launcher('Launcher 0')
	l1 = Launcher('Launcher 1')
	l2 = Launcher('Launcher 2')
	n0 = Node('Node 0')
	n1 = Node('Node 1')
	n2 = Node('Node 2')
	n3 = Node('Node 3')
	n4 = Node('Node 4')
	cpo0 = BindingInput('eventclass 0')
	cpo1 = BindingInput('eventclass 1')
	cpo2 = BindingInput('eventclass 2')
	cpo3 = BindingOutput('eventclass 0')
	cpo4 = BindingOutput('eventclass 1')
	cpo5 = BindingOutput('eventclass 2')
	n1.addConnectionInput(cpo0)
	n2.addConnectionInput(cpo1)
	n1.addConnectionInput(cpo2)
	n0.addConnectionOutput(cpo3)
	n3.addConnectionOutput(cpo4)
	n3.addConnectionOutput(cpo5)

	app.master.addShapeObject(l1)
	app.master.addShapeObject(l0)
	app.master.addShapeObject(l2)
	l0.addShapeObject(n1)
	l2.addShapeObject(n2)
	l0.addShapeObject(n0)
	l1.addShapeObject(n3)
	l2.addShapeObject(n4)
	b0 = Binding('Binding 0', cpo3, cpo0)
	b1 = Binding('Binding 1', cpo4, cpo1)
	b2 = Binding('Binding 2', cpo5, cpo2)
#	app.master.addConnectionObject(b0)
#	app.master.addConnectionObject(b1)
#	app.master.addConnectionObject(b2)
	app.master.addShapeObject(b0)
	app.master.addShapeObject(b1)
	app.master.addShapeObject(b2)

	app.MainLoop()

