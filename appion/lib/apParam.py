#Part of the new pyappion
import os,sys,re
import time
import data
import dbdatakeeper
import apVersion
import apDisplay
try:
	import mem
except:
	apDisplay.printError("Please load 'usepythoncvs' for CVS leginon code, which includes 'mem.py'")
#import selexonFunctions  as sf1

### TEMPORARY, PLEASE MAKE IT SO NOT REQUIRED HERE
db=dbdatakeeper.DBDataKeeper()
data.holdImages(False)

def createDefaultParams(function=None):
	# create default values for parameters
	params={}

	if(function != None):
		version,datestamp = apVersion.getVersion(function)
		functionpath = os.path.abspath(function)
		functionname = os.path.basename(function)
		functionname = functionname.replace(".py","")
		print "FUNCTION:",apDisplay.color(functionpath,"cyan"),\
			"v",version,"from",datestamp
		params['function']=functionname
		params['version'] =version
	else:
		params['function']="generic"
		params['version'] =None

### COMMON PARAMETERS
	params['mrcfileroot']=None
	params['sessionname']=None
	params['session']=None
	params['preset']=None
	params['runid']="run1"
	params['dbimages']=False
	params['alldbimages']=False
	params['apix']=None
	params['diam']=0
	params['bin']=4
	params['continue']=False
	params['commit']=False
	params['description']=None
	params['outdir']=None
	params['rundir']=None
	params['doneDictName']=None
	params['functionLog']=None
	params['pixdiam']=None
	params['binpixdiam']=None

### SELEXON PARAMETERS
	params['template']=''
	params['templatelist']=[]
	params['startang']=0
	params['endang']=10
	params['incrang']=20
	params['thresh']=0.5
	params['autopik']=0
	params['lp']=30
	params['hp']=600
	params['box']=0
	params['method']="updated"
	params['overlapmult']=1.5
	params['maxpeaks']=1500
	params['defocpair']=False
	params['abspath']=os.path.abspath('.')+'/'
	params['templateIds']=''

### selexonFunctions.py PARAMETERS ONLY
	params['ogTmpltInfo']=[]
	params['crud']=False
	params['crudonly']=False
	params['multiple_range']=False
	params['projectId']=None
	
### PARTICLE INSERTION PARAMETERS
	params['scale']=1
	params['scaledapix']={}

### CRUD PARAMETERS
	params['masktype']='custom'
	params['cdiam']=0
	params['cblur']=3.5
	params['clo']=0.6
	params['chi']=0.95
	params['cstd']=1.0
	params['cschi']=1.0
	params['csclo']=0.0
	params['convolve']=0.0
	params['no_hull']=False
	params['cv']=False
	params['no_length_prune']=False
	params['stdev']=0.0
	params['test']=False

#ACE parameters:
	params['edgethcarbon']=0.8
	params['edgethice']=0.6
	params['pfcarbon']=0.9
	params['pfice']=0.3
	params['overlap']=2
	params['fieldsize']=512
	params['resamplefr']=1
	params['drange']=0
	params['tempdir']=None
	params['medium']="carbon"
	params['cs']=2.0
	params['display']=1
	params['stig']=0
	params['nominal']=None
	params['reprocess']=None
	params['matdir']=None
	params['opimagedir']=None

### DOG PARAMETERS
	params["sizerange"]=0
	params["numslices"]=1
	params["minthresh"]=3
	params["maxthresh"]=7
	params["id"]='picka_'

### MAKE STACK PARAMETERS
	params['selexonId']=None

### DEFOCUS SHIFT
	params['shiftonly']=False

	return params

def createDefaultStats():
	stats={}
	stats['startTime']=time.time()
	stats['count']  = 1
	stats['skipcount'] = 1
	stats['lastcount'] = 0
	stats['startmem'] = mem.active()
	stats['peaksum'] = 0
	stats['lastpeaks'] = None
	stats['imagesleft'] = 1
	stats['peaksumsq'] = 0
	stats['timesum'] = 0
	stats['timesumsq'] = 0
	stats['skipcount'] = 0
	stats['waittime'] = 0
	stats['lastimageskipped'] = False
	stats['notpair'] = 0
	stats['memlist'] = [mem.active()]
	return stats

def writeFunctionLog(commandline, params=None, file=None):
	if(file==None and params!=None and params['functionLog']!=None):
		file = params['functionLog']
	else:
		file = "function.log"
	f=open(file,'aw')
	out=""
	for n in commandline:
		out=out+n+" "
	f.write(out)
	f.write("\n")
	f.close()

def createDirectory(path, mode=0777):
	if os.path.exists(path):
		apDisplay.printWarning("directory \'"+path+"\' already exists.")
		return False
	os.makedirs(path,mode)
	return True


def createOutputDirs(params):
	sessionq=data.SessionData(name=params['sessionname'])
	#sessionq=data.SessionData(name=params['session']['name'])
	sessiondata=db.query(sessionq)
	impath=sessiondata[0]['image path']
	params['imgdir']=impath+'/'

	if params['outdir']:
		pass
	else:
		outdir=os.path.split(impath)[0]
		outdir=os.path.join(outdir,params['function']+"/") #'extract/')
		params['outdir']=outdir

	if not createDirectory(params['rundir']) and params['continue']==False:
		apDisplay.printWarning("continue option is OFF. you WILL overwrite previous run.")
		time.sleep(10)

	if(params['function'] == "pyace"):
		createDirectory(params['matdir'])
		createDirectory(params['opimagedir'])

	if (params['function'] == "pyaceCorrect"):
		createDirectory(params['correctedimdir'])
		#createDirectory(params['ctdIntmdImDir'])

	if(params['sessionname'] != None):
		params['outtextfile']=os.path.join(params['rundir'],(params['sessionname']+'.txt'))

	return params

def checkParamConflicts(params):
	#if not params['templateIds'] and not params['apix']:
	#	print "\nERROR: if not using templateIds, you must enter a template pixel size\n"
	#	sys.exit(1)
	if params['templateIds'] and params['template']:
		print "\nERROR: Both template database IDs and mrc file templates are specified,\nChoose only one\n"
		sys.exit(1)
	if params['crudonly']==True and params['shiftonly']==True:
		print "\nERROR: crudonly and shiftonly can not be specified at the same time\n"
		sys.exit(1)
	if (params['thresh']==0 and params['autopik']==0):
		print "\nERROR: neither manual threshold or autopik parameters are set, please set one.\n"
		sys.exit(1)
	if ((params['function'] == "selexon" or params['function'] == "crudFinder") and params['diam']==0):
		print "\nERROR: please input the diameter of your particle\n"
		sys.exit(1)
	if len(params['mrcfileroot']) > 0 and params['dbimages']==True:
		print params['imagecount']
		print "\nERROR: dbimages can not be specified if particular images have been specified\n"
		sys.exit(1)
	if params['alldbimages'] and params['dbimages']==True:
		print "\nERROR: dbimages and alldbimages can not be specified at the same time\n"
		sys.exit(1)
	if len(params['mrcfileroot']) > 0 and params['alldbimages']:
		print "\nERROR: alldbimages can not be specified if particular images have been specified\n"
		sys.exit(1)


def parseCommandLineInput(args,params):
	# check that there are enough input parameters
	fname = params['function']+".py"
	print "find additional help at for",fname,"at:"
	print "  http://fly.scripps.edu/wiki/index.php/"+fname
	if (len(args)<2 or args[1]=='help' or args[1]=='--help' \
		or args[1]=='-h' or args[1]=='-help'):
		sys.exit(1)
		#sf1.printSelexonHelp()

	lastarg=1

	# save the input parameters into the "params" dictionary

###	SELEXON PARAMETERS

	# first get all images
	mrcfileroot=[]
	for arg in args[lastarg:]:
		# gather all input files into mrcfileroot list
		if '=' in arg:
			break
		elif (arg=='crudonly' or arg=='crud'):
			break
		else:
			mrcfile=arg
			mrcfileroot.append(os.path.splitext(mrcfile)[0])
		lastarg+=1
	params['mrcfileroot']=mrcfileroot

	# next get all selection parameters
	for arg in args[lastarg:]:

		elements=arg.split('=')
		elements[0] = elements[0].lower()
		#print elements
		if (elements[0]=='help' or elements[0]=='--help' \
			or elements[0]=='-h' or elements[0]=='-help'):
			#print "find help at for",fname,"at:"
			#print "  http://ami.scripps.edu/wiki/index.php/"+fname
			sys.exit(1)
		elif (elements[0]=='template'):
			params['template']=elements[1]
		elif (elements[0]=='range'):
			angs=elements[1].split(',')
			if (len(angs)==3):
				params['startang']=int(angs[0])
				params['endang']=int(angs[1])
				params['incrang']=int(angs[2])
			else:
				print "\nERROR: \'range\' must include 3 angle parameters: start, stop, & increment\n"
				sys.exit(1)
		elif (re.match('range\d+',elements[0])):
			num=elements[0][-1]
			angs=elements[1].split(',')
			if (len(angs)==3):
				params['startang'+num]=int(angs[0])
				params['endang'+num]=int(angs[1])
				params['incrang'+num]=int(angs[2])
				params['multiple_range']=True
			else:
 				print "\nERROR: \'range\' must include 3 angle parameters: start, stop, & increment\n"
				sys.exit(1)
		elif (elements[0]=='thresh'):
			params['thresh']=float(elements[1])
		elif (elements[0]=='autopik'):
			params['autopik']=float(elements[1])
		elif (elements[0]=='lp'):
			params['lp']=float(elements[1])
		elif (elements[0]=='hp'):
			params['hp']=float(elements[1])
		elif (elements[0]=='box'):
			params['box']=int(elements[1])
		elif (elements[0]=='templateids'):
			templatestring=elements[1].split(',')
			params['templateIds']=templatestring
		elif arg=='defocpair':
			params['defocpair']=True
		elif arg=='shiftonly':
			params['shiftonly']=True
		elif (elements[0]=='method'):
			params['method']=str(elements[1])
		elif (elements[0]=='overlapmult'):
			params['overlapmult']=float(elements[1])
		elif (elements[0]=='maxpeaks'):
			params['maxpeaks']=int(elements[1])

###	MAKEMASK ONLY PARAMETERS
		elif (elements[0]=='masktype'):
			params['masktype']=elements[1]
		elif (elements[0]=='cruddiam'):
			params['cdiam']=float(elements[1])
		elif (elements[0]=='crudblur'):
			params['cblur']=float(elements[1])
		elif (elements[0]=='crudlo'):
			params['clo']=float(elements[1])
		elif (elements[0]=='crudhi'):
			params['chi']=float(elements[1])
		elif (elements[0]=='crudstd'):
			params['cstd']=float(elements[1])
		elif (elements[0]=='crudschi'):
			params['cschi']=float(elements[1])
		elif (elements[0]=='crudsclo'):
			params['csclo']=float(elements[1])
		elif (elements[0]=='convolve'):
			params['convolve']=float(elements[1])
		elif (elements[0]=='stdev'):
			params['stdev']=float(elements[1])
		elif (arg=='no_hull'):
			params['no_hull']=True
		elif (arg=='cv'):
			params['cv']=True
			params['no_hull']=True
		elif (arg=='no_length_prune'):
			params['no_length_prune']=True
		elif (arg=='test'):
			params['test']=True

###	ACE PARAMETERS

		elif (elements[0]=='edgethcarbon'):
			params['edgethcarbon']=float(elements[1])
		elif (elements[0]=='edgethice'):
			params['edgethice']=float(elements[1])
		elif (elements[0]=='pfcarbon'):
			params['pfcarbon']=float(elements[1])
		elif (elements[0]=='pfice'):
			params['pfice']=float(elements[1])
		elif (elements[0]=='overlap'):
			params['overlap']=int(elements[1])
		elif (elements[0]=='fieldsize'):
			params['fieldsize']=int(elements[1])
		elif (elements[0]=='resamplefr'):
			params['resamplefr']=float(elements[1])
		elif (elements[0]=='drange'):
			drange=int(elements[1])
			if drange == 1 or drange== 0:
				params['drange']=drange
			else:
				print "Error: drange should only be 0 or 1"
				sys.exit()

		elif (elements[0]=='tempdir'):
			params['tempdir']=os.path.abspath(elements[1]+"/")
		elif (elements[0]=='medium'):
			medium=elements[1]
			if medium=='carbon' or medium=='ice':
				params['medium']=medium
			else:
				print "medium can only be 'carbon' or 'ice'"
				sys.exit(1)
		elif (elements[0]=='cs'):
			params['cs']=float(elements[1])
		elif (elements[0]=='display'):
			display=int(elements[1])
			if display==0 or display==1:
				params['display']=display
			else:
				print "display must be 0 or 1"
				sys.exit()		
		elif (elements[0]=='stig'):
			stig=int(elements[1])
			if stig==0 or stig==1:
				params['stig']=stig
			else:
				print "stig must be 0 or 1"
				sys.exit()

		elif (elements[0]=='nominal'):
			params['nominal']=float(elements[1])

		elif (elements[0]=='reprocess'):
			params['reprocess']=float(elements[1])

### MAKE STACK PARAMS
		elif (elements[0]=='prtlrunid' or elements[0]=='selexonid'):
			params["selexonId"]=int(elements[1])

### DOG PICKER PARAMS

		elif (elements[0]=='sizerange'):
			params['sizerange']=float(elements[1])
		elif (elements[0]=='numslices'):
			params['numslices']=float(elements[1])
		elif (elements[0]=='minthresh'):
			params['minthresh']=float(elements[1])
		elif (elements[0]=='maxthresh'):
			params['maxthresh']=float(elements[1])
		elif (elements[0]=='id'):
			params['id']=elements[1]

### GENERAL PARAMETERS
		elif (elements[0]=='outdir'):
			params['outdir']=os.path.abspath(elements[1])
			#if(params['outdir'][0] != "/"):
			#	params['outdir'] = os.path.join(os.getcwd(),params['outdir'])
			#	params['outdir'] = os.path.abspath(params['outdir'])
		elif (elements[0]=='runid'):
			params['runid']=elements[1]
		elif (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='diam'):
			params['diam']=float(elements[1])
		elif (elements[0]=='bin'):
			params['bin']=int(elements[1])
		elif arg=='commit':
			params['commit']=True
			params['display']=1
		elif arg=='continue':
			params['continue']=True
		elif (elements[0]=='dbimages'):
			dbinfo=elements[1].split(',')
			if len(dbinfo) == 2:
				params['sessionname']=dbinfo[0]
				params['preset']=dbinfo[1]
				params['dbimages']=True
				params['continue']=True # continue should be on for dbimages option
			else:
				print "\nERROR: dbimages must include both \'sessionname\' and \'preset\'"+\
					"parameters (ex: \'07feb13a,en\')\n"
				sys.exit(1)
		elif (elements[0]=='alldbimages'):
			params['sessionname']=elements[1]
			params['alldbimages']=True
		else:
			print "\nERROR: undefined parameter \'"+arg+"\'\n"
			sys.exit(1)

	sessionq=data.SessionData(name=params['sessionname'])
	sessiondata=db.query(sessionq)
	impath=sessiondata[0]['image path']
	params['imgdir']=impath+'/'

	if params['outdir']:
		pass
	else:
		outdir=os.path.split(impath)[0]
		params['outdir']=os.path.join(outdir,params['function']+"/")

	params['rundir']=os.path.join(params['outdir'],params['runid'])
	params['matdir']=os.path.join(params['rundir'],"matfiles")
	params['opimagedir']=os.path.join(params['rundir'],"opimages")
	params['correctedimdir']=os.path.join(params['rundir'],"ctdimages")
	#params['ctdIntmdImDir']=os.path.join(params['rundir'],"ctdIntmdImages")
	if params['tempdir'] == None:
		params['tempdir']=os.path.join(params['rundir'],"tmp")
	params['doneDictName']=os.path.join(params['rundir'],"."+params['function']+"donedict")
	params['functionLog']=os.path.join(params['rundir'],params['function']+".log")
	print " ... run directory defined as:",params['rundir']

	if(params['apix'] != None and params['diam'] > 0):
		params['pixdiam'] = params['diam']/params['apix']
		params['binpixdiam'] = params['diam']/params['apix']/params['bin']

	if('debug' in params and params['debug'] == True):
		import pprint
		pprint.pprint(params)

	return params
