import xmlrpclib
import uiserver
import threading
import time
import sys
from wxPython.wx import *
from wxPython.wxc import wxPyAssertionError
import wxImageViewer
import wxDictTree
import wxOrderedListBox

wxEVT_ADD_WIDGET = wxNewEventType()
wxEVT_SET_WIDGET = wxNewEventType()
wxEVT_REMOVE_WIDGET = wxNewEventType()
wxEVT_SET_SERVER = wxNewEventType()
wxEVT_COMMAND_SERVER = wxNewEventType()

class AddWidgetEvent(wxPyEvent):
	def __init__(self, namelist, typelist, value, read, write):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_ADD_WIDGET)
		self.namelist = namelist
		self.typelist = typelist
		self.value = value
		self.read = read
		self.write = write

class SetWidgetEvent(wxPyEvent):
	def __init__(self, namelist, value):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_SET_WIDGET)
		self.namelist = namelist
		self.value = value

class RemoveWidgetEvent(wxPyEvent):
	def __init__(self, namelist):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_REMOVE_WIDGET)
		self.namelist = namelist

class SetServerEvent(wxPyEvent):
	def __init__(self, namelist, value, thread=True):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_SET_SERVER)
		self.namelist = namelist
		self.value = value
		self.thread = thread

class CommandServerEvent(wxPyEvent):
	def __init__(self, namelist, args=(), thread=True):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_COMMAND_SERVER)
		self.namelist = namelist
		self.args = args
		self.thread = thread

def WidgetClassFromTypeList(typelist):
	if typelist:
		if typelist[0] == 'object':
			if len(typelist) > 1:
				if typelist[1] == 'container':
					if len(typelist) > 2:
						if typelist[2] == 'single select from list':
							return wxComboBoxWidget
						elif typelist[2] == 'select from list':
							return wxOrderedListBoxWidget
						elif typelist[2] == 'select from struct':
							return wxTreeSelectWidget
						elif typelist[2] == 'click image':
							return wxClickImageWidget
						elif typelist[2] == 'target image':
							return wxTargetImageWidget
						elif typelist[2] == 'dialog':
							return wxDialogWidget
						elif typelist[2] == 'medium':
							return wxNotebookContainerWidget
						elif typelist[2] == 'large':
							if len(typelist) > 3:
								if typelist[3] == 'client':
									return wxClientContainerFactory(wxNotebookContainerWidget)
					return wxStaticBoxContainerWidget
				elif typelist[1] == 'method':
					return wxButtonWidget
				elif typelist[1] == 'data':
					if len(typelist) > 2:
						if typelist[2] == 'integer':
							if len(typelist) > 3:
								if typelist[3] == 'progress':
									return wxProgressWidget
						elif typelist[2] == 'boolean':
							return wxCheckBoxWidget
						elif typelist[2] == 'struct':
							return wxTreeCtrlWidget
						elif typelist[2] == 'binary':
							if len(typelist) > 3:
								if typelist[3] == 'image':
									return wxImageWidget
					return wxEntryWidget
	raise ValueError('invalid type for widget')
	
class XMLRPCClient(object):
	def __init__(self, serverhostname, serverport, port=None):
		uri = 'http://%s:%s' % (serverhostname, serverport)
		self.proxy = xmlrpclib.ServerProxy(uri)

	def execute(self, function_name, args=()):
		try:
			return getattr(self.proxy, function_name)(*args)
		except xmlrpclib.ProtocolError:
			# usually return value not correct type
			raise
		except xmlrpclib.Fault:
			# exception during call of the function
			raise

class UIClient(XMLRPCClient, uiserver.XMLRPCServer):
	def __init__(self, serverhostname, serverport, port=None):
		XMLRPCClient.__init__(self, serverhostname, serverport, port)
		uiserver.XMLRPCServer.__init__(self, port)
		self.server.register_function(self.addFromServer, 'ADD')
		self.server.register_function(self.setFromServer, 'SET')
		self.server.register_function(self.removeFromServer, 'DEL')

	def addServer(self):
		self.execute('ADDSERVER', (self.hostname, self.port))

	def setServer(self, namelist, value, thread=False):
		#print 'setServer', namelist, value
		if thread:
			threading.Thread(target=self.execute,
												args=('SET', (namelist, value))).start()
		else:
			self.execute('SET', (namelist, value))

	def commandServer(self, namelist, args, thread=False):
		if thread:
			threading.Thread(target=self.execute,
												args=('COMMAND', (namelist, args))).start()
		else:
			self.execute('COMMAND', (namelist, args))

	def addFromServer(self, namelist, typelist, value, read, write):
		raise NotImplementedError

	def setFromServer(self, namelist, value):
		raise NotImplementedError

	def removeFromServer(self, namelist):
		raise NotImplementedError

class wxUIClient(UIClient):
	def __init__(self, container, serverhostname, serverport, port=None):
		# there are some timing issues to be thought out
		self.container = container
		UIClient.__init__(self, serverhostname, serverport, port)
		threading.Thread(target=self.addServer, args=()).start()

	def addFromServer(self, namelist, typelist, value, read, write):
		#print 'addFromServer', namelist, value
		evt = AddWidgetEvent(namelist, typelist, value, read, write)
		wxPostEvent(self.container.widgethandler, evt)
		return ''

	def setFromServer(self, namelist, value):
		#print 'setFromServer', namelist, value
		evt = SetWidgetEvent(namelist, value)
		wxPostEvent(self.container.widgethandler, evt)
		return ''

	def removeFromServer(self, namelist):
		evt = RemoveWidgetEvent(namelist)
		wxPostEvent(self.container.widgethandler, evt)
		return ''

class UIApp(wxApp):
	def __init__(self, serverhostname, serverport):
		self.serverhostname = serverhostname
		self.serverport = serverport
		wxApp.__init__(self, 0)
		self.MainLoop()

	def OnInit(self):
		self.frame = wxFrame(NULL, -1, 'UI')
		self.panel = wxScrolledWindow(self.frame, -1, size=(600, 700))
		self.panel.SetScrollRate(1, 1)		
		containerclass = wxClientContainerFactory(wxStaticBoxContainerWidget)
		self.container = containerclass('UI Client', self.panel, self,
																		(self.serverhostname, self.serverport))
		if self.container.sizer is not None:
			self.panel.SetSizer(self.container.sizer)
		self.SetTopWindow(self.frame)
		self.panel.Show(true)
		self.frame.Fit()
		self.frame.Show(true)
		return true

	def layout(self):
		self.panel.Refresh()

class wxWidget(object):
	def __init__(self, name, parent, container):
		self.name = name
		self.parent = parent
		self.container = container
		self.widgethandler = wxEvtHandler()
		self.sizer = None

	def setServer(self, value):
		evt = SetServerEvent([self.name], value)
		wxPostEvent(self.container.widgethandler, evt)

	def commandServer(self, args=()):
		evt = CommandServerEvent([self.name], args)
		wxPostEvent(self.container.widgethandler, evt)

class wxContainerWidget(wxWidget):
	def __init__(self, name, parent, container):
		wxWidget.__init__(self, name, parent, container)
		self.children = {}
		self.childparent = self.parent

		self.notebook = None

		self.widgethandler.Connect(-1, -1, wxEVT_ADD_WIDGET, self.onAddWidget)
		self.widgethandler.Connect(-1, -1, wxEVT_SET_WIDGET, self.onSetWidget)
		self.widgethandler.Connect(-1, -1, wxEVT_REMOVE_WIDGET, self.onRemoveWidget)
		self.widgethandler.Connect(-1, -1, wxEVT_SET_SERVER, self.onSetServer)
		self.widgethandler.Connect(-1, -1, wxEVT_COMMAND_SERVER,
																self.onCommandServer)

	def _addWidget(self, name, typelist, value, read, write):
		childclass = WidgetClassFromTypeList(typelist)
		if issubclass(childclass, wxClientContainerWidget):
			child = childclass(name, self.childparent, self, value)
		elif issubclass(childclass, wxDataWidget):
			child = childclass(name, self.childparent, self, value, read, write)
		else:
			child = childclass(name, self.childparent, self)
		self.children[name] = child
		if not isinstance(child, wxNotebookContainerWidget):
			if self.sizer is not None and child.sizer is not None:
				self.sizer.Add(child.sizer, 0, wxALL, 3)

	def _addWidgetToChild(self, evt):
		for name, child in self.children.items():
			if name == evt.namelist[0]:
				evt.namelist = evt.namelist[1:]
				wxPostEvent(child.widgethandler, evt)
				return
		raise ValueError('No such child to add widget')

	def onAddWidget(self, evt):
		if len(evt.namelist) == 1:
			childname = evt.namelist[0]
			self._addWidget(childname, evt.typelist, evt.value, evt.read, evt.write)
		else:
			self._addWidgetToChild(evt)

	def onSetWidget(self, evt):
		for name, child in self.children.items():
			if name == evt.namelist[0]:
				evt.namelist = evt.namelist[1:]
				wxPostEvent(child.widgethandler, evt)
				return
		raise ValueError('No such child to set widget')

	def onRemoveWidget(self, evt):
		for name, child in self.children.items():
			if name == evt.namelist[0]:
				if len(evt.namelist) == 1:
					del self.children[name]
					child.destroy()
					return
				else:
					evt.namelist = evt.namelist[1:]
					wxPostEvent(child.widgethandler, evt)
					return
		raise ValueError('No such child to remove widget')

	def onSetServer(self, evt):
		evt.namelist.insert(0, self.name)
		wxPostEvent(self.container.widgethandler, evt)

	def onCommandServer(self, evt):
		evt.namelist.insert(0, self.name)
		wxPostEvent(self.container.widgethandler, evt)

	def getNotebook(self):
		if self.notebook is None:
			self.notebook = wxNotebook(self.childparent, -1)#, style=wxCLIP_CHILDREN)
			self.notebooksizer = wxNotebookSizer(self.notebook)
			if self.sizer is not None:
				self.sizer.Add(self.notebooksizer, 0,
												wxALIGN_CENTER_HORIZONTAL | wxALL, 5)
			self.layout()
		return self.notebook

	def layout(self):
		if self.sizer is not None:
			self.sizer.Layout()
		if isinstance(self.childparent, wxScrolledWindow):
			self.childparent.FitInside()
		else:
			self.childparent.Fit()
		self.container.layout()

	def destroy(self):
		for name, child in self.children.items():
			del self.children[name]
			child.destroy()
			if not isinstance(child, wxNotebookContainerWidget):
				if self.sizer is not None and child.sizer is not None:
					self.sizer.Remove(child.sizer)
		if self.notebook is not None:
			self.notebook.Destroy()
			self.sizer.Remove(self.notebooksizer)

class wxStaticBoxContainerWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.staticbox = wxStaticBox(self.parent, -1, self.name)
		self.sizer = wxStaticBoxSizer(self.staticbox, wxVERTICAL)

	def destroy(self):
		wxContainerWidget.destroy(self)
		self.staticbox.Destroy()

class wxNotebookContainerWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.parentnotebook = self.container.getNotebook()
		self.panel = wxPanel(self.parentnotebook, -1)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.panel.SetSizer(self.sizer)
		self.panel.Show(true)
		self.childparent = self.panel
		self.parentnotebook.AddPage(self.panel, self.name)
		self.layout()

	def layout(self):
		self.sizer.Layout()
		self.childparent.Fit()
		self.container.notebooksizer.Layout()
		self.container.notebooksizer.Fit(self.parentnotebook)
		self.container.layout()

	def _addWidget(self, namelist, typelist, value, read, write):
		wxContainerWidget._addWidget(self, namelist, typelist, value, read, write)
		self.layout()

	def destroy(self):
		wxContainerWidget.destroy(self)
		self.parentnotebook.DeletePage(self.getPageNumber())

	def getPageNumber(self):
		for i in range(self.parentnotebook.GetPageCount()):
			if self.parentnotebook.GetPage(i) == self.panel:
				return i

class wxClientContainerWidget(object):
	pass

def wxClientContainerFactory(wxcontainerwidget):
	class wxClientContainer(wxClientContainerWidget, wxcontainerwidget):
		def __init__(self, name, parent, container, serverhostnameport):
			wxcontainerwidget.__init__(self, name, parent, container)
			self.uiclient = wxUIClient(self, serverhostnameport[0],
																				serverhostnameport[1])

		def onSetServer(self, evt):
			evt.namelist.insert(0, self.name)
			self.uiclient.setServer(evt.namelist, evt.value, evt.thread)

		def onCommandServer(self, evt):
			evt.namelist.insert(0, self.name)
			self.uiclient.commandServer(evt.namelist, evt.args, evt.thread)

	return wxClientContainer

class wxMethodWidget(wxWidget):
	def __init__(self, name, parent, container):
		wxWidget.__init__(self, name, parent, container)

	def commandFromWidget(self, evt=None):
		wxWidget.commandServer(self)

	def layout(self):
		if self.sizer is not None:
			self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		pass

class wxButtonWidget(wxMethodWidget):
	def __init__(self, name, parent, container):
		wxMethodWidget.__init__(self, name, parent, container)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.button = wxButton(self.parent, -1, self.name)
		EVT_BUTTON(self.parent, self.button.GetId(), self.commandFromWidget)
		self.sizer.Add(self.button, 0, wxALIGN_CENTER | wxALL, 0)
		self.layout()

class wxDataWidget(wxWidget):
	def __init__(self, name, parent, container, value, read, write):
		if read:
			self.read = True
		else:
			self.read = False
		if write:
			self.write = True
		else:
			self.write = False
		wxWidget.__init__(self, name, parent, container)
		self.widgethandler.Connect(-1, -1, wxEVT_SET_WIDGET, self.onSetWidget)

	def onSetWidget(self, evt):
		self.set(evt.value)

	def setWidget(self, value):
		pass

	def setValue(self, value):
		if isinstance(value, xmlrpclib.Binary):
			self.value = value.data
		else:
			self.value = value

	def set(self, value):
		self.setValue(value)
		self.setWidget(value)

	def layout(self):
		if self.sizer is not None:
			self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		pass

class wxProgressWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, read, write):
		wxDataWidget.__init__(self, name, parent, container, value, read, write)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.gauge = wxGauge(self.parent, -1, 100, style=wxGA_HORIZONTAL)
		size = self.gauge.GetSizeTuple()
		self.gauge.SetSize((size[0]*4, size[1]))

		self.set(value)

		self.sizer.Add(self.label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.sizer.Add(self.gauge, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.layout()

	def setWidget(self, value):
		self.gauge.SetValue(value)

	def destroy(self):
		self.label.Destroy()
		self.gauge.Destroy()

class wxEntryWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, read, write):
		wxDataWidget.__init__(self, name, parent, container, value, read, write)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.label = wxStaticText(self.parent, -1, self.name + ':')
		if self.write:
			self.applybutton = wxButton(self.parent, -1, 'Apply')
			self.applybutton.Enable(false)
			EVT_BUTTON(self.applybutton, self.applybutton.GetId(), self.setFromWidget)
			self.entry = wxTextCtrl(self.parent, -1, style=wxTE_PROCESS_ENTER)
			EVT_TEXT(self.entry, self.entry.GetId(), self.onEdit)
			EVT_TEXT_ENTER(self.entry, self.entry.GetId(), self.onEnter)
		else:
			self.entry = wxStaticText(self.parent, -1, '')

		self.set(value)

		self.sizer.Add(self.label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.sizer.Add(self.entry, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		if hasattr(self, 'applybutton'):
			self.sizer.Add(self.applybutton, 0, wxALIGN_CENTER|wxLEFT|wxRIGHT, 3)
		self.layout()

	def destroy(self):
		if hasattr(self, 'applybutton'):
			self.applybutton.Destroy()
		self.entry.Destroy()
		self.label.Destroy()

	def onEdit(self, evt):
		self.applybutton.Enable(true)

	def onEnter(self, evt):
		if self.applybutton.IsEnabled():
			self.setFromWidget(evt)

	def setFromWidget(self, evt):
		value = self.entry.GetValue()
		if type(self.value) is not str:
			try:
				value = eval(value)
			except:
				excinfo = sys.exc_info()
				sys.excepthook(*excinfo)
				return
		else:
			value = str(value)
		if type(self.value) != type(value):
			return
		self.value = value
		self.applybutton.Enable(false)
		self.setServer(self.value)

	def setWidget(self, value):
		if isinstance(self.entry, wxStaticText):
			self.entry.SetLabel(str(self.value))
			entrysize = self.entry.GetSize()
			self.sizer.SetItemMinSize(self.entry, entrysize.GetWidth(),
																						entrysize.GetHeight())
			self.layout()
		else:
			self.entry.SetValue(str(self.value))
		if hasattr(self, 'applybutton'):
			self.applybutton.Enable(false)

class wxCheckBoxWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, read, write):
		wxDataWidget.__init__(self, name, parent, container, value, read, write)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.checkbox = wxCheckBox(self.parent, -1, self.name)
		if not self.write:
			self.checkbox.Enable(false)
		else:
			EVT_CHECKBOX(self.parent, self.checkbox.GetId(), self.setFromWidget)

		self.set(value)

		self.sizer.Add(self.checkbox, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.layout()

	def setFromWidget(self, evt):
		value = self.checkbox.GetValue()
		if value:
			self.value = 1
		else:
			self.value = 0
		self.setServer(self.value)

	def setWidget(self, value):
		self.checkbox.SetValue(self.value)

	def destroy(self):
		self.checkbox.Destroy()

class wxTreeCtrlWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, read, write):
		wxDataWidget.__init__(self, name, parent, container, value, read, write)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		if self.write:
			self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1,
																								self.name, self.setFromWidget)
		else:
			self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1, self.name)

		self.set(value)

		self.sizer.Add(self.tree, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

	def setFromWidget(self):
		self.setServer(self.value)

	def setWidget(self, value):
		self.tree.set(self.value)

	def destroy(self):
		self.tree.Destroy()

class wxImageWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, read, write):
		wxDataWidget.__init__(self, name, parent, container, value, read, write)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.imageviewer = wxImageViewer.ImagePanel(self.parent, -1)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.set(value)
		self.sizer.Add(self.label, 0, wxALIGN_LEFT | wxALL, 5)
		self.sizer.Add(self.imageviewer, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

	def setValue(self, value):
		# not keeping track of image for now
		pass

	def setWidget(self, value):
		if value.data:
			self.imageviewer.setImageFromMrcString(value.data)
			width, height = self.imageviewer.GetSizeTuple()
			self.sizer.SetItemMinSize(self.imageviewer, width, height)
		else:
			self.imageviewer.clearImage()

	def destroy(self):
		self.label.Destroy()
		self.imageviewer.Destroy()

class MessageDialog(wxDialog):
	def __init__(self, parent, id, title, callback):
		wxDialog.__init__(self, parent, id, title)
		self.callback = callback
		panel = wxPanel(self, -1)
		panel.SetAutoLayout(true)
		self.sizer = wxBoxSizer(wxVERTICAL)
		panel.SetSizer(self.sizer)
		self.message = wxStaticText(panel, -1, '')
		self.sizer.Add(self.message, 0, wxALIGN_CENTER | wxALL, 10)
		self.okbutton = wxButton(panel, -1, 'OK')
		EVT_BUTTON(self, self.okbutton.GetId(), self.OnOK)
		self.sizer.Add(self.okbutton, 0, wxALIGN_CENTER | wxALL, 10)
		self.sizer.Layout()
		self.sizer.Fit(self)
		EVT_CLOSE(self, self.OnClose)

	def OnOK(self, evt):
		self.callback()

	def OnClose(self, evt):
		self.callback()

class wxDialogWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.dialog = MessageDialog(self.parent, -1, self.name, self.dialogCallback)
		self.messageflag = False
		self.okflag = False

	def setMessage(self, value):
		self.dialog.message.SetLabel(value)

	def show(self):
		width, height = self.dialog.message.GetSizeTuple()
		self.dialog.sizer.SetItemMinSize(self.dialog.message, width, height)
		self.dialog.sizer.Layout()
		self.dialog.sizer.Fit(self.dialog)
		self.dialog.Show(true)

	def _addWidget(self, name, typelist, value, read, write):
		if name == 'Message':
			self.setMessage(value)
			self.messageflag = True
		elif name == 'OK':
			self.okflag = True
		if self.messageflag and self.okflag:
			self.show()

	def _addWidgetToChild(self, evt):
		pass

	def onSetWidget(self, evt):
		if evt.namelist == ['Message']:
			self.setMessage(evt.value)

	def onRemoveWidget(self, evt):
		pass

	def dialogCallback(self):
		evt = CommandServerEvent([self.name, 'OK'], ())
		wxPostEvent(self.container.widgethandler, evt)

	def layout(self):
		pass

	def destroy(self):
		self.dialog.Destroy()

class wxComboBoxWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.combobox = wxComboBox(self.parent, -1,
																style=wxCB_DROPDOWN | wxCB_READONLY)
		self.combobox.Enable(false)
		EVT_COMBOBOX(self.parent, self.combobox.GetId(), self.onSelect)
		self.label = wxStaticText(self.parent, -1, self.name + ':')
		self.sizer.Add(self.label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.sizer.Add(self.combobox, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.value = {'List': None, 'Selected': None}
		self.layout()

	def onSelect(self, evt):
		value = evt.GetSelection()
		evt = SetServerEvent([self.name, 'Selected'], value)
		wxPostEvent(self.container.widgethandler, evt)

	def setList(self, value):
		self.value['List'] = value
		self.combobox.Clear()
		if value:
			for i in value:
				self.combobox.Append(str(i))
			self.combobox.Enable(true)
		else:
			self.combobox.Enable(false)
		self.combobox.SetSize(self.combobox.GetBestSize())
		width, height = self.combobox.GetSizeTuple()
		self.sizer.SetItemMinSize(self.combobox, width, height)

	def setSelected(self, value):
		self.value['Selected'] = value
		if self.value['List']:
			self.combobox.SetSelection(value)

	def _addWidget(self, name, typelist, value, read, write):
		if name == 'List':
			self.setList(value)
		elif name == 'Selected':
			self.setSelected(value)

	def _addWidgetToChild(self, evt):
		pass

	def onSetWidget(self, evt):
		if evt.namelist == ['List']:
			self.setList(evt.value)
		if evt.namelist == ['Selected']:
			self.setSelected(evt.value)

	def onRemoveWidget(self, evt):
		pass

	def layout(self):
		self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		self.label.Destroy()
		self.combobox.Destroy()

class wxOrderedListBoxWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.orderedlistbox = wxOrderedListBox.wxOrderedListBox(self.parent, -1,
																														self.onSelect)
		self.sizer.Add(self.orderedlistbox, 0, wxALIGN_CENTER)
		self.sizer.Layout()
		self.value = {'List': None, 'Selected': None}
		self.layout()

	def onSelect(self, value):
		evt = SetServerEvent([self.name, 'Selected'], value)
		wxPostEvent(self.container.widgethandler, evt)

	def setList(self, value):
		self.value['List'] = value
		self.orderedlistbox.setList(value)

	def setSelected(self, value):
		self.value['Selected'] = value
		self.orderedlistbox.setSelected(value)

	def _addWidget(self, name, typelist, value, read, write):
		if name == 'List':
			self.setList(value)
		elif name == 'Selected':
			self.setSelected(value)

	def _addWidgetToChild(self, evt):
		pass

	def onSetWidget(self, evt):
		if evt.namelist == ['List']:
			self.setList(evt.value)
		if evt.namelist == ['Selected']:
			self.setSelected(evt.value)

	def onRemoveWidget(self, evt):
		pass

	def layout(self):
		self.orderedlistbox.sizer.Layout()
		self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		self.orderedlistbox.Destroy()

class wxTreeSelectWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1, self.name,
																											None, self.onSelect)
		self.tree.Enable(false)
		self.sizer.Add(self.tree, 0, wxALIGN_CENTER | wxALL, 5)
		self.value = {'Struct': {}, 'Selected': []}
		self.layout()

	def onSelect(self, value):
		evt = SetServerEvent([self.name, 'Selected'], [value])
		wxPostEvent(self.container.widgethandler, evt)

	def setStruct(self, value):
		self.value['Struct'] = value
		self.tree.set(value)
		if self.value['Selected'] is not None:
			self.tree.Enable(true)

	def setSelected(self, value):
		self.value['Selected'] = value
		if self.value['Struct'] and self.value['Selected']:
			self.tree.select(value[0])
			self.tree.Enable(true)

	def _addWidget(self, name, typelist, value, read, write):
		if name == 'Struct':
			self.setStruct(value)
		elif name == 'Selected':
			self.setSelected(value)

	def _addWidgetToChild(self, evt):
		pass

	def onSetWidget(self, evt):
		if evt.namelist == ['Struct']:
			self.setStruct(evt.value)
		if evt.namelist == ['Selected']:
			self.setSelected(evt.value)

	def onRemoveWidget(self, evt):
		pass

	def layout(self):
		self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		self.combobox.Destroy()

class wxClickImageWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.condition = threading.Condition()
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.clickimage = wxImageViewer.ClickImagePanel(self.parent, -1,
																											self.foo)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.sizer.Add(self.label, 0, wxALIGN_LEFT | wxALL, 5)
		self.sizer.Add(self.clickimage, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

	def foo(self, coordinate):
		threading.Thread(target=self.clickCallback, args=(coordinate,)).start()

	def clickCallback(self, coordinate):
		self.condition.acquire()
		evt = SetServerEvent([self.name, 'Coordinates'], coordinate)
		wxPostEvent(self.container.widgethandler, evt)
		self.condition.wait()
		self.condition.release()
		evt = CommandServerEvent([self.name, 'Click'], ())
		wxPostEvent(self.container.widgethandler, evt)

	def setImage(self, value):
		if value:
			self.clickimage.setImageFromMrcString(value.data, True)
			width, height = self.clickimage.GetSizeTuple()
			self.sizer.SetItemMinSize(self.clickimage, width, height)
		else:
			self.clickimage.clearImage()

	def _addWidget(self, name, typelist, value, read, write):
		# should disable until all available
		if name == 'Image':
			self.setImage(value)

	def _addWidgetToChild(self, evt):
		pass

	def onSetWidget(self, evt):
		if evt.namelist == ['Image']:
			self.setImage(evt.value)
		else:
			self.condition.acquire()
			self.condition.notify()
			self.condition.release()

	def onRemoveWidget(self, evt):
		pass

	def layout(self):
		self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		self.label.Destroy()
		self.clickimage.Destroy()

class wxTargetImageWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.targetimage = wxImageViewer.TargetImagePanel(self.parent, -1,
																											self.targetCallback)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.sizer.Add(self.label, 0, wxALIGN_LEFT | wxALL, 5)
		self.sizer.Add(self.targetimage, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

	def targetCallback(self, name, value):
		evt = SetServerEvent([self.name, name], value)
		wxPostEvent(self.container.widgethandler, evt)

	def setImage(self, value):
		if value:
			self.targetimage.setImageFromMrcString(value.data, True)
			width, height = self.targetimage.GetSizeTuple()
			self.sizer.SetItemMinSize(self.targetimage, width, height)
		else:
			self.targetimage.clearImage()

	def setTargets(self, name, value):
		self.targetimage.setTargetTypeValue(name, value)

	def _addWidget(self, name, typelist, value, read, write):
		# should disable until all available
		if name == 'Image':
			self.setImage(value)
		else:
			self.setTargets(name, value)

	def _addWidgetToChild(self, evt):
		pass

	def onSetWidget(self, evt):
		if evt.namelist == ['Image']:
			self.setImage(evt.value)
		else:
			self.setTargets(evt.namelist[0], evt.value)

	def onRemoveWidget(self, evt):
		pass

	def layout(self):
		self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		self.label.Destroy()
		self.targetimage.Destroy()

if __name__ == '__main__':
	import sys
	client = UIApp(sys.argv[1], int(sys.argv[2]))

