#!/usr/bin/env python

#python
import sys
import os
import shutil
import numpy
#appion
import appionScript
import apStack
import apDisplay
import apDB
import appionData
import apEMAN
import apTilt
from apTilt import apTiltPair

appiondb = apDB.apdb

class subStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --norefclass=ID --exclude=0,1,... [options]")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit stack to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit stack to database")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("-d", "--description", dest="description", default="",
			help="Stack description", metavar="TEXT")
		self.parser.add_option("-n", "--new-stack-name", dest="runname",
			help="Run id name", metavar="STR")
		self.parser.add_option("--norefclass", dest="norefclassid", type="int",
			help="noref class id", metavar="ID")
		self.parser.add_option("--exclude", dest="exclude",
			help="EMAN style classes to EXCLUDE in the new stack (0,5,8)", metavar="0,1,...")
		self.parser.add_option("--include", dest="include",
			help="EMAN style classes to INCLUDE in the new stack (0,2,7)", metavar="0,1,...")

	#=====================
	def checkConflicts(self):
		if self.params['description'] is None:
			apDisplay.printError("substack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")
		if self.params['norefclassid'] is None:
			apDisplay.printError("noref class ID was not defined")
		
		#get the stack ID from the noref class ID
		norefclassdata = appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefclassid'])
		norefRun=norefclassdata['norefRun']
		self.params['stackid'] = norefRun['stack'].dbid

		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['exclude'] is None and self.params['include'] is None:
			apDisplay.printError("noref classes to be included/excluded was not defined")
		if self.params['exclude'] is not None and self.params['include'] is not None:
			apDisplay.printError("both include and exclude were defined, only one is allowed")

	#=====================
	def setOutDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['outdir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def start(self):
		#new stack path
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])
		newstack = os.path.join(self.params['outdir'], stackdata['name'])
		apStack.checkForPreviousStack(newstack)

		### list of classes to be excluded
		excludelist = []
		if self.params['exclude'] is not None:
			excludestrlist = self.params['exclude'].split(",")
			for excld in excludestrlist:
				excludelist.append(int(excld.strip()))
		apDisplay.printMsg("Exclude list: "+str(excludelist))

		### list of classes to be included
		includelist = []
		if self.params['include'] is not None:
			includestrlist = self.params['include'].split(",")
			for incld in includestrlist:
				includelist.append(int(incld.strip()))		
		apDisplay.printMsg("Include list: "+str(includelist))

		#get particles from noref class run
		norefclassdata = appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefclassid'])
		classpartq = appionData.ApNoRefClassParticlesData()
		classpartq['classRun'] = norefclassdata
		classpartdatas = classpartq.query()

		#get stackid and stack particles from the noref run 
		stack = norefclassdata['norefRun']['stack']
		stackid = stack.dbid
		stackparticle = appionData.ApStackParticlesData()
		stackparticle['stack'] = stack
		
		apDisplay.printMsg("Working with stack " + str(stackid) + "")

		includeParticle = []
		excludeParticle = 0
		
		for classpart in classpartdatas:
			#write to text file
			classnum = classpart['classNumber']-1
			stackpartnum = classpart['noref_particle']['particle']['particleNumber']
			if excludelist and not classnum in excludelist:
				try:
					#get the particle number of the tilt pair
					tiltpairdata = ApTiltPair.getStackParticleTiltPair(stackid, stackpartnum)
					tiltpair = tiltpairdata['particleNumber']
					
					#convert to eman numbering for substack function
					emanstackpartnum = tiltpair-1
					includeParticle.append(emanstackpartnum)
				
				except:
					apDisplay.printWarning("Particle " + str(stackpartnum) + " does not have a tilt pair!\n")
				
				#tiltpartdata = appionData.ApTiltParticlePairData()
				#tiltpartdata['particle1'] = classpart['noref_particle']['particle']['particle']
				#try: 
					#tiltpart = tiltpartdata.query()		
					#print tiltpart[0]['particle1']
					#apDisplay.printMsg("The pair of particle "+str(tiltpart[0]['particle1'].dbid)+" is "+str(tiltpart[0]['particle2'].dbid)+".\n")

					#stackparticle['particle'] = tiltpart[0]['particle2']
					#stackparticle2 = stackparticle.query()

					#stackparticle['particle'] = tiltpart[0]['particle1']
					#stackparticle1 = stackparticle.query()
						
				#except:
					#print "particle " + str(classpart['noref_particle']['particle']['particle'].dbid) + " does not have a tilt mate\n" 		
			else:
				excludeParticle += 1

		#if there is no tilt pair of the particles...
		if len(includeParticle) == 0:
			apDisplay.printError("Particles in Stack " + str(stackid) + " do not have tilt pairs!") 

		includeParticle.sort()
		apDisplay.printMsg("Keeping "+str(len(includeParticle))+" and excluding "+str(excludeParticle)+" particles")

		#write kept particles to file
		self.params['keepfile'] = os.path.join(norefclassdata['norefRun']['path']['path'], "keepfile-"+self.timestamp+".list")
		apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
		kf = open(self.params['keepfile'], "w")
		for partnum in includeParticle:
			kf.write(str(partnum)+"\n")
		kf.close()

		#get number of particles
		numparticles = len(includeParticle)
		if excludelist:
			self.params['description'] += ( " ... %d particle substack of norefclassid %d with %s classes excluded" 
				% (numparticles, self.params['norefclassid'], self.params['exclude']))
		elif includelist:
			self.params['description'] += ( " ... %d particle substack of norefclassid %d with %s classes included" 
				% (numparticles, self.params['norefclassid'], self.params['include']))	

		#create the new sub stack
		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'])
		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")

		apStack.commitSubStack(self.params)
		apStack.averageStack(stack=newstack)

#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()

