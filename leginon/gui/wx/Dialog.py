# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Dialog.py,v $
# $Revision: 1.6 $
# $Name: not supported by cvs2svn $
# $Date: 2007-10-17 18:36:54 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import wx

class Dialog(wx.Dialog):
	def __init__(self, parent, title, subtitle='',
			style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER,pos=wx.DefaultPosition):
		wx.Dialog.__init__(self, parent, -1, title, style=style,pos=pos)

		self.sz = wx.GridBagSizer(5, 5)

		self.buttons = {}

		self.szbuttons = wx.GridBagSizer(5, 5)
		self.szbuttons.AddGrowableCol(0)

		if subtitle:
			sb = wx.StaticBox(self, -1, subtitle)
			self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
			self.sbsz.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)
			sz = self.sbsz
		else:
			sz = self.sz

		self.szdialog = wx.GridBagSizer(5, 5)
		self.szdialog.Add(sz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.szdialog.Add(self.szbuttons, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.szdialog.AddGrowableRow(0)
		self.szdialog.AddGrowableCol(0)

		self.onInitialize()

		self.SetSizerAndFit(self.szdialog)

	def onInitialize(self):
		pass

	def addButton(self, label, id=-1, flags=None):
		col = len(self.buttons)
		self.buttons[label] = wx.Button(self, id, label)
		if flags is None:
			if col > 0:
				flags = wx.ALIGN_CENTER
			else:
				flags = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
		self.szbuttons.Add(self.buttons[label], (0, col), (1, 1), flags)
		return self.buttons[label]

