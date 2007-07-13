#!/usr/bin/python -O

#pythonlib
import os
import sys
import re
#appion
import particleLoop
import apFindEM
import apImage
import apDisplay
import apTemplate
import apDatabase
import apPeaks
import apParticle
#legacy
#import apViewIt
#import selexonFunctions  as sf1

class TemplateCorrelationLoop(particleLoop.ParticleLoop):

	def preLoopFunctions(self):
		apTemplate.getTemplates(self.params)

	def particleProcessImage(self, imgdata):
		imgname = imgdata['filename']
		apTemplate.rescaleTemplates(self.params)
		### RUN FindEM
		if 'method' in self.params and self.params['method'] == "experimental":
			#ccmaplist = sf2.runCrossCorr(params,imgname)
			#peaktree  = apPeaks.findPeaks(imgdata, ccmaplist, self.params)
			sys.exit(1)
		else:
			ccmaplist = apFindEM.runFindEM(imgdata, self.params)
			peaktree  = apPeaks.findPeaks(imgdata, ccmaplist, self.params)
		return peaktree

	def particleCommitToDatabase(self, imgdata):
		expid = int(imgdata['session'].dbid)
		apParticle.insertSelexonParams(self.params, expid)
#		apParticle.insertSelexonParamsREFLEGINON(self.params, imgdata['session'])

	def particleDefaultParams(self):
		self.params['template']=''
		self.params['templatelist']=[]
		self.params['startang']=0
		self.params['endang']=10
		self.params['incrang']=20
		self.params['templateIds']=''
		self.params['multiple_range']=False
		self.params["ogTmpltInfo"]=[]
		self.params['mapdir']="ccmaxmaps"
		self.params["scaledapix"]={}

	def particleParseParams(self,args):
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			#print elements
			if (elements[0]=='template'):
				self.params['template']=elements[1]
			elif (elements[0]=='range'):
				angs=elements[1].split(',')
				if (len(angs)==3):
					self.params['startang']=int(angs[0])
					self.params['endang']=int(angs[1])
					self.params['incrang']=int(angs[2])
					self.params['startang1']=int(angs[0])
					self.params['endang1']=int(angs[1])
					self.params['incrang1']=int(angs[2])
				else:
					apDisplay.printError("'range' must include 3 angle parameters: start, stop, & increment")
			elif (re.match('range\d+',elements[0])):
				num = re.sub("range(?P<num>[0-9]+)","\g<num>",elements[0])
				#num=elements[0][-1]
				angs=elements[1].split(',')
				if (len(angs)==3):
					self.params['startang'+num]=int(angs[0])
					self.params['endang'+num]=int(angs[1])
					self.params['incrang'+num]=int(angs[2])
					self.params['multiple_range']=True
				else:
	 				apDisplay.printError("'range' must include 3 angle parameters: start, stop, & increment")
			elif (elements[0]=='templateids'):
				templatestring=elements[1].split(',')
				self.params['templateIds']=templatestring
			elif (elements[0]=='method'):
				self.params['method']=str(elements[1])
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

	def particleParamConflicts(self):
		if not self.params['templateIds'] and not self.params['apix']:
			apDisplay.printError("if not using templateIds, you must enter a template pixel size")
		if self.params['templateIds'] and self.params['template']:
			apDisplay.printError("Both template database IDs and mrc file templates are specified,\nChoose only one")

if __name__ == '__main__':
	imgLoop = TemplateCorrelationLoop()
	imgLoop.run()

