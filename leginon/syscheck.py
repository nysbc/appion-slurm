#!/usr/bin/env python
# The line above will attempt to interpret this script in python.
# It uses the current environment, which must define a path to the python
# executable.

########################################################################
#  Leginon Dependency Checker
#  This script will check Python and the Python modules installed
#  on this system to see if all requirements are met.
########################################################################

def versionAtLeast(version, minimum):
	'return True if version is at least minimum'

	# pad shortest one with zeros to make lengths equal
	version = list(version)
	minimum = list(minimum)
	lenv = len(version)
	lenm = len(minimum)
	diff = lenv-lenm
	if diff < 0:
		version = version + [0 for i in range(diff)]
	else:
		minimum = minimum + [0 for i in range(diff)]
	n = max(lenv,lenm)
	for i in range(n):
		if version[i] > minimum[i]:
			return True
		if version[i] < minimum[i]:
			return False
		# else equal, so check next digit
	return True

######################################################################
## Python
######################################################################
print '--------------------------------------------------------------'
print 'Python:'

import sys

## location of executable and module path
print '    Python executable (if wrong, check PATH in your environment):'
print '        %s' % (sys.executable,)
print '    Python module search path (if wrong, check PYTHONPATH):'
for dir in sys.path:
	print '        %s' % (dir,)
if not sys.path:
	print '        (Empty)'

## minimum python version
minpyver = (2, 3, 4)
mypyver = sys.version_info[:3]
mystr = '.'.join(map(str,mypyver))
minstr = '.'.join(map(str,minpyver))
print '    Python version: %s' % (mystr,)
if versionAtLeast(mypyver, minpyver):
	print '        OK (at least %s required)' % (minstr ,)
else:
	print '        *** FAILED (at least %s required)' % (minstr,)
	print '        Upgrade before installing other packages.'

######################################################################
## Python Imaging Library
######################################################################
minpilver = (1, 1, 4)
minstr = '.'.join(map(str,minpilver))
print '--------------------------------------------------------------'
print 'Python Imaging Library (PIL):'
print '    importing Image module...'
try:
	import Image
except:
	print '    *** Could not import Image module.'
	print '      You must install Python Imaging Library version %s or greater' % (minstr,)
else:
	mystr = Image.VERSION
	mypilver = map(int, mystr.split('.'))
	print '    PIL version: %s' % (mystr,)
	if versionAtLeast(mypilver, minpilver):
		print '        OK (at least %s required)' % (minstr ,)
	else:
		print '        *** FAILED (at least %s required)' % (minstr,)

######################################################################
## Python MySQL client module
######################################################################
minmysqlver = (1, 2)
minstr = '.'.join(map(str,minmysqlver))
print '--------------------------------------------------------------'
print 'MySQL Python client (MySQLdb):'
print '    importing MySQLdb module...'
try:
	import MySQLdb
except:
	print '    *** Could not import MySQLdb module.'
	print '      You must install Python MySQL version %s or greater' % (minstr,)
else:
	mystr = MySQLdb.__version__
	mymysqlver = MySQLdb.version_info[:3]
	print '    Python MySQL version: %s' % (mystr,)
	if versionAtLeast(mymysqlver, minmysqlver):
		print '        OK (at least %s required)' % (minstr ,)
	else:
		print '        *** FAILED (at least %s required)' % (minstr,)

######################################################################
## numarray
######################################################################
minnumver = (1, 1)
minstr = '.'.join(map(str, minnumver))
print '--------------------------------------------------------------'
print 'numarray:'
print '    importing numarray module...'
try:
	import numarray
except ImportError:
	print '    *** Failed to import numarray.  Install numarray version %s or greater' % (minstr,)
else:
	mystr = numarray.__version__
	mynumver = map(int, mystr.split('.'))
	print '    numarray version: %s' % (mystr,)
	if versionAtLeast(mynumver, minnumver):
		print '        OK (at least %s required)' % (minstr ,)
	else:
		print '        *** FAILED (at least %s required)' % (minstr,)

######################################################################
## numpy
######################################################################
testednumpy = ('1.0b5',)
print '--------------------------------------------------------------'
print 'numpy:'
print '    importing numpy module...'
try:
	import numpy
except ImportError:
	print '    *** Failed to import numpy.  Install numpy first.'
else:
	mystr = numpy.__version__
	print '    numpy version: %s' % (mystr,)
	if mystr in testednumpy:
		print '        OK'
	else:
		print '        *** WARNING: untested version of numpy.  Tested versions: %s'  % (testednumpy,)

######################################################################
## scipy
######################################################################
print '--------------------------------------------------------------'
print 'scipy:'
print '    importing scipy.optimize module...'
try:
	import scipy.optimize
except ImportError:
	print '    *** Failed to import scipy.optimize.  Install scipy first'
else:
	try:
		print '      testing for leastsq function...'
		scipy.optimize.leastsq
		print '       OK'
	except:
		print '        *** FAILED: need version of scipy.optimize with leastsq'
		
######################################################################
## Python XML module
######################################################################
minxmlver = (0, 8, 2)
minstr = '.'.join(map(str,minxmlver))
print '--------------------------------------------------------------'
print 'Python XML module:'
print '    importing xml module...'
try:
	import xml
except:
	print '    *** Could not import xml module.'
	print '      You must install Python xml version %s or greater' % (minstr,)
else:
	mystr = xml.__version__
	myxmlver = map(int, mystr.split('.'))
	print '    Python XML version: %s' % (mystr,)
	if versionAtLeast(myxmlver, minxmlver):
		print '        OK (at least %s required)' % (minstr ,)
	else:
		print '        *** FAILED (at least %s required)' % (minstr,)

######################################################################
## ImageViewer
######################################################################
print '--------------------------------------------------------------'
print 'ImageViewer module:'
print '    importing ImageViewer module...'
try:
	import ImageViewer
except:
	print '    *** FAILED: Could not import ImageViewer.'
else:
	print '        OK (no version requirement at this time)'

######################################################################
## wxPython
######################################################################
minwxver = (2, 5, 2, 8)
minstr = '.'.join(map(str, minwxver))
print '--------------------------------------------------------------'
print 'wxPython:'
print '    importing wx module...'
try:
	import wx
except ImportError:
	print '    *** Failed to import wx.  Install wxPython version %s or greater' % (minstr,)

else:
	## check version
	try:
		## NEWER VERSIONS
		mystr = wx.__version__
		if mystr[-1] == 'u':
			mystr = mystr[:-1]
		mywxver = map(int, mystr.split('.'))
	except:
		## OLDER VERSIONS
		mywxver = wx.VERSION[:4]
		mystr = '.'.join(map(str, mywxver))

	print '    wxPython version: %s' % (mystr,)
	if not versionAtLeast(mywxver, minwxver):
		print '        *** FAILED (at least %s required)' % (minstr,)

	else:
		print '        OK (at least %s required)' % (minstr ,)

	## test a wx app
		class MyApp(wx.App):
			def OnInit(self):
				frame = wx.Frame(None, -1, 'wxPython test window')
				self.sizer = wx.BoxSizer()

				button = wx.Button(frame, -1, 'TEST')
				button.SetBackgroundColour(wx.RED)
				self.sizer.Add(button, 1, border=50, flag=wx.ALL)
				self.Bind(wx.EVT_BUTTON, self.test, button)

				frame.SetSizerAndFit(self.sizer)
				self.SetTopWindow(frame)
				frame.Show(True)
				return True

			def test(self, evt):
				print 'TEST'
	
		print '    Testing a wxPython application.  Close the window that pops up...'
		try:
			app = MyApp(0)
			app.MainLoop()
		except:
			print '        Failed to start wx application.  This is usually because you do not have display permission'
		print '    wxPython test successful'
