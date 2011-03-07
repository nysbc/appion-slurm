import os
import shutil
from appionlib import appiondata
from appionlib import apStack
from appionlib import apEMAN
from appionlib import apParam
from appionlib import apXmipp

formats = ['spider','xmipp','frealign','eman']
appionbasepath = '/ami/data00/appion/'
default_partlist = 'partlist.doc'
stack_exts = {'spider':('.spi',),'frealign':('.hed','.img'),'eman':('.hed','.img')}

def getFormattedStackInfo(stackdata,format):
	sessiondata = apStack.getSessionDataFromStackId(stackdata.dbid)
	stackroot = os.path.splitext(stackdata['name'])[0]
	instackdir = stackdata['path']['path']
	outstackdir = os.path.join(appionbasepath,sessiondata['name'],'stacks',os.path.basename(stackdata['path']['path'])+'_'+format)
	return stackroot,instackdir,outstackdir

def makeStackInFormatFromDefault(stackdata,format='eman'):
	'''
		Function to create the stack in the requested format
		Current default is Imagic format used in EMAN
	'''
	if format not in formats:
		apDisplay.printError('Unknown stack format %s requested' % format)
	stackroot,instackdir,outstackdir = getFormattedStackInfo(stackdata,format)
	instackpath = os.path.join(instackdir,stackroot+'.hed')
	if format == 'eman':
		return stackdata['path']['path']
	apParam.createDirectory(outstackdir)
	rundir = os.getcwd()
	os.chdir(outstackdir)
	if format == 'spider':
		outstackpath = os.path.join(outstackdir,stackroot+stack_exts[format][0])
		emancmd="proc2d %s %s spidersingle"%(instackpath,outstackpath)
		apEMAN.executeEmanCmd(emancmd, showcmd=True)
	if format == 'frealign':
		outstackpath = os.path.join(outstackdir,stackroot+stack_exts[format][0])
		emancmd="proc2d %s %s invert"%(instackpath,outstackpath)
		apEMAN.executeEmanCmd(emancmd, showcmd=True)
	if format == 'xmipp':
		### convert stack into single spider files
		selfile = apXmipp.breakupStackIntoSingleFiles(instackpath)
	os.chdir(rundir)
	return outstackdir

def getFormattedStack(stackdata,format):
	'''
		Appion Script that need to use a particle stack calls this function.
		It searches in the database to find a stack of the right format if exists.
		If so, it returns the path. If not, it creates the stack of the right format
		registered in the database, and return the path of the created stack
	'''
	if format not in formats:
		apDisplay.printError('Unknown stack format %s requested' % format)
	q = appiondata.ApStackFormatData(stack=stackdata)
	results = q.query(results=1)
	if results:
		formatdata = results[0]
		if formatdata[format]:
			return formatdata[format]['path']
		formattedstackdir = makeStackInFormatFromDefault(stackdata,format)
		if formattedstackdir:
			q = appiondata.ApStackFormatData(initializer=formatdata)
			q[format] = appiondata.ApPathData(path=formattedstackdir)
			q.insert()
	else:
		formattedstackdir = makeStackInFormatFromDefault(stackdata,format)
		q = appiondata.ApStackFormatData(stack=stackdata)
		q[format] = appiondata.ApPathData(path=formattedstackdir)
		q.insert()
	return os.path.abspath(formattedstackdir)

def remakeXmippPartlistDoc(formattedstackdir,partlist):
	'''
		Write a new partlist in the current directory updated with
		current database path
	'''
	rundir = os.getcwd()
	copyUpdatedXmippPartlistDoc(formattedstackdir,partlist,rundir,partlist,formattedstackdir)

def copyUpdatedXmippPartlistDoc(indir,inlistfile,outdir,outlistfile,formattedstackdir):
	'''
		The new list is updated with the defined stackdir by this function in 
		case the data has been moved
	'''
	inpartlistpath = os.path.join(indir,inlistfile)
	outpartlistpath = os.path.join(outdir,outlistfile)
	formattedstackdir = os.path.abspath(formattedstackdir)
	inlist = open(inpartlistpath,'r')
	outlist = open(outpartlistpath,'w')
	lines = inlist.readlines()
	for line in lines:
		pieces = line.split('/partfiles/')
		if len(pieces) > 1:
			pieces[0] = formattedstackdir
		newline = '/partfiles/'.join(pieces)
		outlist.write(newline)
	inlist.close()
	outlist.close()

def linkFormattedStack(stackdata, format,linkprefix='start'):
	'''
		Use softlink to the formatted stack to avoid making copies for
		every new runs.  Links make it possible to run Spider and other
		Fortran programs when the absolute path to the stack is long
	'''
	formattedstackdir = getFormattedStack(stackdata, format)
	stackroot = os.path.splitext(stackdata['name'])[0]
	if format == 'xmipp':
		partlist = default_partlist
		remakeXmippPartlistDoc(formattedstackdir,partlist)
		return
	for ext in stack_exts[format]:
		if os.path.islink(linkprefix+ext):
			os.remove(linkprefix+ext)
		filepath = os.path.join(formattedstackdir,stackroot+ext)
		os.symlink(filepath,linkprefix+ext)
	return formattedstackdir,stackroot+ext

def replaceFormattedStack(stackdata, format, sourcedir,sourcefile):
	'''
		copy a formatted stack generated by means other than 
		makeFormattedStackFromDefault to the formatted stack directory
		and insert into the database
		sourcefile is the partlist filename for xmipp not the stack filename
		as for others
	'''
	stackroot,stackdir,formattedstackdir = getFormattedStackInfo(stackdata, format)
	apParam.createDirectory(formattedstackdir)
	if format == 'xmipp':
		copyUpdatedXmippPartlistDoc(sourcedir,sourcefile,formattedstackdir,default_partlist,formattedstackdir)
		partfilesdir = os.path.join(formattedstackdir,'partfiles')
		shutil.rmtree(partfilesdir)
		shutil.copytree('partfiles',os.path.join(formattedstackdir,'partfiles'))
	elif format in stack_exts.keys():
		sourceroot = os.path.splitext(sourcefile)[0]
		for ext in stack_exts[format]:
			shutil.copy(sourceroot+ext,os.path.join(formattedstackdir,stackroot+ext))

