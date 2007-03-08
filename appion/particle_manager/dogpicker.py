#!/usr/bin/python -O

import os, re, sys
import data
import time
import libcv2
import Mrc
from selexonFunctions  import *
from selexonFunctions2 import *

donename = '.doneimages.py'

def createDefaults():
	
	params={}
	params["apix"]=1
	params["diam"]=0
	params["bin"]=4
	params["range"]=0
	params["sample"]=1
	params["mint"]=3
	params["maxt"]=7
	params["sessionname"]=None
	params["preset"]=None
	params["id"]='picka_'
	
	return params
	

def parseInput(args,params):

	for arg in args[1:]:
		elements=arg.split('=')
		if (elements[0]=='bin'):
			params['bin']=float(elements[1])
		elif (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='diam'):
			params['diam']=float(elements[1])
		elif (elements[0]=='range'):
			params['range']=float(elements[1])
		elif (elements[0]=='sample'):
			params['sample']=float(elements[1])
		elif (elements[0]=='mint'):
			params["mint"]=float(elements[1])
		elif (elements[0]=='maxt'):
			params["maxt"]=float(elements[1])
		elif (elements[0]=='id'):
			params["id"]=elements[1]
		elif (elements[0]=='dbimages'):
			dbinfo=elements[1].split(',')
			if len(dbinfo) == 2:
				params['sessionname']=dbinfo[0]
				params['preset']=dbinfo[1]
			else:
				print "dbimages must include both session and preset parameters"
				sys.exit()
		else:
			print "undefined parameter '"+arg+"'\n"
			sys.exit(1)


def getDoneDict(donename):
	if os.path.exists(donename):
		f=open(donename,'r')
		donedict=cPickle.load(f)
		f.close()
		return donedict
	else:
		donedict={}
		return (donedict)

def writeDoneDict(donedict,donename):
	f=open(donename,'w')
	cPickle.dump(donedict,f)
	f.close()
	


if __name__ == '__main__':

	params=createDefaults()

	parseInput(sys.argv,params)
	
	scale          = params['apix']
	estimated_size = params['diam']
	search_range   = params['range']
	sampling       = params['sample']
	mintreshold    = params['mint']
	maxtreshold    = params['maxt']
	bin            = params['bin']
	
	#estimated_size = estimated_size / ( scale * bin )
	#search_range   =  search_range  / ( scale * bin )
	
	images=getImagesFromDB(params['sessionname'],params['preset'])

	params['session']=images[0]['session']
	
	donedict=getDoneDict(donename)

	for img in images:
		
		imagename = img['filename']
		doneCheck(donedict,imagename)
		if donedict[imagename]: 
			print 'skipping' + imagename
			continue
		
		imgpath = img['session']['image path'] + '/' + imagename + '.mrc'
		image = Mrc.mrc_to_numeric(imgpath)
		
		peaks = libcv2.dogDetector(image,bin,estimated_size,search_range,sampling,mintreshold,maxtreshold)
		
		expid = int(img['session'].dbid)
		legimgid = int(img.dbid)
		legpresetid =int(img['preset'].dbid)
		
		if peaks is None: continue
		
		imgq = particleData.image()
		imgq['dbemdata|SessionData|session'] = expid
		imgq['dbemdata|AcquisitionImageData|image'] = legimgid
		imgq['dbemdata|PresetData|preset'] = legpresetid
		imgids = partdb.query(imgq,results=1)
		
		if not (imgids):
			partdb.insert(imgq)
			imgq=None
			imgq = particleData.image()
			imgq['dbemdata|SessionData|session']=expid
			imgq['dbemdata|AcquisitionImageData|image']=legimgid
			imgq['dbemdata|PresetData|preset']=legpresetid
			imgids=partdb.query(imgq, results=1)
		
		if not (imgids):
			continue
			
		for i in range(peaks.shape[0]):
			
			row = peaks[i,0] * bin
			col = peaks[i,1] * bin
			sca = peaks[i,2]
			
			runq=particleData.run()
			runq['name']=params['id']+'_'+str(sca)
			runq['dbemdata|SessionData|session']=expid
			
			particle = particleData.particle()
			particle['runId'] = runq
			particle['imageId'] = imgids[0]
			particle['selectionId'] = None
			particle['xcoord'] = col
			particle['ycoord'] = row
			particle['correlation'] = sca
			partdb.insert(particle)
		
		
		print imagename + ' is done'
		donedict[imagename] = True
		writeDoneDict(donedict,donename)
		

                                                                                                                                                                       
