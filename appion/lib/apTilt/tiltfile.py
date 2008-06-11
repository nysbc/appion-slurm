from apSpider import operations

filetypes = ['text', 'xml', 'spider', 'pickle', 'box', 'pik',]
filetypesel = (
	"Text Files (*.txt)|*.txt" 
	+ "|XML Files (*.xml)|*.xml"
	+ "|Spider Files (*.spi)|*.[a-z][a-z][a-z]" 
	+ "|Python Pickle File (*.pickle)|*.pickle" )
	+ "|EMAN Box File (*.box)|*.box" )
	+ "|Pik File (*.pik)|*.pik" )

#---------------------------------------	
"""
Each file should have at a minimum the following information

1. Theta (tilt) angle
2. Gamma (image 1 rotation) angle
3. Phi (image 2 rotation) angle
4. List of image 1 particles
5. List of image 2 particles

"""
#---------------------------------------	
def saveData(saved):
	"""
		saved = {}
		saved['theta'] = self.data['theta']
		saved['gamma'] = self.data['gamma']
		saved['phi'] = self.data['phi']
		saved['savetime'] = time.asctime()+" "+time.tzname[time.daylight]
		saved['filetype'] = tiltfile.filetypes[self.data['filetypeindex']]
		saved['picks1'] = self.getArray1()
		saved['picks2'] = self.getArray2()
		saved['align1'] = self.getAlignedArray1()
		saved['align2'] = self.getAlignedArray2()
		saved['rmsd'] = self.getRmsdArray()
		saved['filepath'] = os.path.join(self.data['dirname'], self.data['outfile'])
		saved['image1name'] = self.panel1.filename
		saved['image2name'] = self.panel2.filename
	"""

	if saved['filetype'] == 'text':
		savePicksToTextFile(saved)
	elif saved['filetype'] == 'xml':
		savePicksToXMLFile(saved)
	elif saved['filetype'] == 'spider':
		savePicksToSpiderFile(saved)
	elif saved['filetype'] == 'pickle':
		savePicksToPickleFile(saved)
	else:
		return False

#---------------------------------------
def savePicksToTextFile(saved):
	f = open(saved['filepath'], "w")

	f.write( "date: \t%sf\n"  % ( saved['savetime'], ))
	f.write( "theta:\t%.5f\n" % ( saved['theta'], ))
	f.write( "gamma:\t%.5f\n" % ( saved['gamma'], ))
	f.write( "phi:  \t%.5f\n" % ( saved['phi'], ))
	#IMAGE 1
	f.write( "image 1: \t%sf\n"  % ( saved['image1name'], ))
	for i in len(saved['picks1']):
		f.write( '%d,%d, ' % (saved['picks1'][i][0], saved['picks1'][i][1],) )
		if i < len(saved['align1']):
			f.write( '%.1f,%.1f, ' % (saved['align1'][i][0], saved['align1'][i][1],) )
		if i < len(saved['rmsd']):
			f.write(' %.3f, ' % ( saved['rmsd'][i] ) )
		f.write('\n')

	#IMAGE 2
	f.write( "image 2: \t%sf\n"  % ( saved['image2name'], ))
	for i in len(saved['picks2']):
		f.write( '%d,%d, ' % (saved['picks2'][i][0], saved['picks2'][i][1],) )
		if i < len(saved['align2']):
			f.write( '%.1f,%.1f, ' % (saved['align2'][i][0], saved['align2'][i][1],) )
		if i < len(saved['rmsd']):
			f.write(' %.3f, ' % ( saved['rmsd'][i] ) )
		f.write('\n')
	f.close()

	return True

#---------------------------------------
def savePicksToXMLFile(targets1, targets2, data):
	f = open(saved['filepath'], "w")

	data['targets1'] = self.targetsToArray(self.panel1.getTargets('Picked'))
	data['targets2'] = self.targetsToArray(self.panel2.getTargets('Picked'))
	filename = os.path.basename(filepath)
	apXml.writeDictToXml(data, filepath, title='aptiltpicker')
	self.statbar.PushStatusText("Saved "+str(len(data['targets1']))+" particles and parameters to "+data['outfile'], 0)
	return True

#---------------------------------------
def savePicksToSpiderFile(saved):
	f = open(saved['filepath'], "w")

	f.write( " ; particles picked with ApTiltPicker\n")
	f.write( " ; http://appion.org\n")
	f.write( " ; "+saved['savetime']+"\n")
	f.write( " ; mean rmsd: %.3f\n" % ( saved['meanrmsd'],) )
	#PARAMETERS
	f.write(" ; \n; \n; PARAMETERS\n")
	f.write(operations.spiderOutputLine(1, 6, 0.0, 0.0, 0.0, 0.0, 111.0, 1.0))
	f.write(" ; FITTED FLAG\n")
	f.write(operations.spiderOutputLine(2, 6, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0))
	f.write(" ; (X0,Y0) FOR LEFT IMAGE1, (X0s,Y0s) FOR RIGHT IMAGE2, REDUCTION FACTOR\n")
	f.write(operations.spiderOutputLine(3, 6, 
		saved['picks1'][0][0], saved['picks1'][0][1], 
		saved['picks2'][0][0], saved['picks2'][0][1], 
		1.0, 0.0))
	f.write(" ; TILT ANGLE (THETA), LEFT IMAGE1 ROTATION (GAMMA), RIGHT IMAGE2 ROTATION (PHI)\n")
	f.write(operations.spiderOutputLine(4, 6, 
		saved['theta'], saved['gamma'], saved['phi'],
		0.0, 0.0, 0.0))

	#IMAGE 1
	f.write( " ; LEFT IMAGE 1: "+saved['image1name']+"\n" )
	for i in len(saved['picks1']):
		line = operations.spiderOutputLine(i+1, 6, i+1, 
			saved['picks1'][i][0], saved['picks1'][i][1], 
			saved['picks1'][i][0], saved['picks1'][i][1], 1.0)
		f.write(line)

	#IMAGE 2
	f.write( " ; RIGHT IMAGE 2: "+saved['image2name']+"\n" )
	for i in len(saved['picks2']):
		line = operations.spiderOutputLine(i+1, 6, i+1, 
			saved['picks2'][i][0], saved['picks2'][i][1], 
			saved['picks2'][i][0], saved['picks2'][i][1], 1.0)
		f.write(line)

	f.close()

	return True


#---------------------------------------
def savePicksToPickleFile(targets1, targets2, data):
	filepath = os.path.join(data['dirname'], data['outfile'])
	data['targets1'] = self.targetsToArray(self.panel1.getTargets('Picked'))
	data['targets2'] = self.targetsToArray(self.panel2.getTargets('Picked'))
	f = open(filepath, 'w')
	cPickle.dump(data, f)
	f.close()
	self.statbar.PushStatusText("Saved "+str(len(data['targets1']))+" particles and parameters to "+data['outfile'], 0)
	return True

#---------------------------------------
def guessFileType(self, filepath):
	if filepath is None or filepath == "":
		return None
	print filepath
	self.data['outfile'] = os.path.basename(filepath)
	self.data['extension'] = self.data['outfile'][-3:]
	if self.data['extension'] == "txt":
		self.data['filetypeindex'] = 0
	elif self.data['extension'] == "xml":
		self.data['filetypeindex'] = 1
	elif self.data['extension'] == "spi":
		self.data['filetypeindex'] = 2
	elif self.data['extension'] == "pik":
		self.data['filetypeindex'] = 3
	else:
		raise "Could not determine filetype of picks file (argument 3)"
	self.data['filetype'] = self.filetypes[self.data['filetypeindex']]
	return

#---------------------------------------
def getExtension(self):
	if self.data['filetypeindex'] == 0:
		self.data['extension'] = "txt"
	elif self.data['filetypeindex'] == 1:
		self.data['extension'] = "xml"
	elif self.data['filetypeindex'] == 2:
		self.data['extension'] = "spi"
	elif self.data['filetypeindex'] == 3:
		self.data['extension'] = "pik"
	else:
		return "pik"
	return self.data['extension']

#---------------------------------------
def onFileOpen(self, evt):
	dlg = wx.FileDialog(self.frame, "Choose a pick file to open", data['dirname'], "", \
		self.filetypesel, wx.OPEN)
	if 'filetypeindex' in data and data['filetypeindex'] is not None:
		dlg.SetFilterIndex(data['filetypeindex'])
	if dlg.ShowModal() == wx.ID_OK:
		data['outfile'] = dlg.GetFilename()
		data['dirname']  = os.path.abspath(dlg.GetDirectory())
		data['filetypeindex'] = dlg.GetFilterIndex()
		data['filetype'] = self.filetypes[data['filetypeindex']]
		self.openPicks()
	dlg.Destroy()

#---------------------------------------
def openPicks(self, filepath=None):
	if filepath is None or filepath is "":
		filepath = os.path.join(data['dirname'],data['outfile'])
	if filepath is None or filepath is "":
		return None
	if data['filetypeindex'] is None:
		self.guessFileType(filepath)
	if True: #try:
		if data['filetypeindex'] == 0:
			self.openPicksFromTextFile(filepath)
		elif data['filetypeindex'] == 1:
			raise NotImplementedError
		elif data['filetypeindex'] == 2:
			raise NotImplementedError
		elif data['filetypeindex'] == 3:
			self.openPicksFromPickleFile(filepath)
		else:
			raise NotImplementedError
		sys.stderr.write("Opened particles and parameters from '"+data['outfile']+\
			"' of type "+data['filetype']+"\n")
	if False: #except:
		self.statbar.PushStatusText("ERROR: Opening file '"+data['outfile']+"' failed", 0)
		dialog = wx.MessageDialog(self.frame, "Opening file '"+data['outfile']+"' failed", 'Error', wx.OK|wx.ICON_ERROR)
		dialog.ShowModal()
		dialog.Destroy()	
	data['opentime'] = time.asctime()+" "+time.tzname[time.daylight]

#---------------------------------------
def openPicksFromTextFile(self, filepath=None):
	if filepath is None or filepath == "" or not os.path.isfile(filepath):
		return
	f = open(filepath,"r")
	size = int(len(f.readlines())/2-1)
	f.close()
	data['outfile'] = os.path.basename(filepath)
	data['dirname'] = os.path.dirname(filepath)
	f = open(filepath,"r")
	strarrays = ["","",""]
	arrays = [
		numpy.zeros((size,2), dtype=numpy.int32),
		numpy.zeros((size,2), dtype=numpy.int32),
		numpy.zeros((size,2), dtype=numpy.int32),
	]
	i = 0
	for line in f:
		if line[:5] == "image":
			i += 1
			j = 0
			self.statbar.PushStatusText("Reading picks for image "+str(i),0)
		else:
			line = line.strip()
			seps = line.split(",")
			for k in range(len(seps)):
				#print "'"+seps[k]+"'"
				if seps[k]:
					arrays[i][j,k] = int(seps[k])
			j += 1
	#print arrays[1]
	f.close()
	#sys.exit(1)
	a1 = arrays[1]
	a2 = arrays[2]
	self.panel1.setTargets('Picked', a1)
	self.panel2.setTargets('Picked', a2)
	#self.panel1.setTargets('Numbered', a1)
	#self.panel2.setTargets('Numbered', a2)
	self.statbar.PushStatusText("Read "+str(len(a1))+" particles and parameters from file "+filepath, 0)

#---------------------------------------
def openPicksFromPickleFile(self, filepath=None):
	if filepath is None or filepath == "" or not os.path.isfile(filepath):
		return
	f = open(filepath,'r')
	data = cPickle.load(f)
	f.close()
	a1 = data['targets1']
	a2 = data['targets2']
	self.panel1.setTargets('Picked', a1)
	self.panel2.setTargets('Picked', a2)
	self.statbar.PushStatusText("Read "+str(len(a1))+" particles and parameters from file "+filepath, 0)
	return True



