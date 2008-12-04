#!/usr/bin/env python

#python
import sys
import os
import shutil
import numpy
import time
import threading
import math
#appion
import appionScript
import apStack
import apDisplay
import appionData
import apEMAN
import apFile
import apRecon
import apParam
from apTilt import apTiltPair
from apSpider import operations, backproject, alignment

class otrVolumeScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --norefclass=ID --tilt-stack=# --classnums=#,#,# [options]")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit OTR run to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit OTR run to database")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("--classnum", "--classnums", dest="classnums", type="str",
			help="Class numbers to use for otr volume, e.g. 0,1,2", metavar="#")
		self.parser.add_option("--tilt-stack", dest="tiltstackid", type="int",
			help="Tilted Stack ID", metavar="#")
		self.parser.add_option("--norefclass", dest="norefclassid", type="int",
			help="Noref class id", metavar="ID")
		self.parser.add_option("--runname", dest="runname",
			help="Run name", metavar="ID")
		self.parser.add_option("--num-iters", dest="numiters", type="int", default=6, 
			help="Number of tilted image shift refinement iterations", metavar="#")
		self.parser.add_option("--mask-rad", dest="radius", type="int",
			help="Particle mask radius (in pixels)", metavar="ID")
		self.parser.add_option("--lowpassvol", dest="lowpassvol", type="float", default=10.0,
			help="Low pass volume filter (in Angstroms)", metavar="#")
		self.parser.add_option("--highpasspart", dest="highpasspart", type="float", default=600.0,
			help="High pass particle filter (in Angstroms)", metavar="#")
		self.parser.add_option("--description", dest="description", type="str",
			help="Description of OTR run", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['classnums'] is None:
			apDisplay.printError("class number was not defined")
		rawclasslist = self.params['classnums'].split(",")
		self.classlist = []	
		for cnum in rawclasslist:
			try:
				self.classlist.append(int(cnum))
			except:
				apDisplay.printError("could not parse: "+cnum)
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")
		if self.params['norefclassid'] is None:
			apDisplay.printError("noref class ID was not defined")
		if self.params['tiltstackid'] is None:
			apDisplay.printError("tilt stack ID was not defined")
		if self.params['radius'] is None:
			apDisplay.printError("particle mask radius was not defined")
		if self.params['description'] is None:
			apDisplay.printError("enter a description")
		
		#get the stack ID from the noref class ID
		self.norefclassdata = self.appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefclassid'])
		norefRun = self.norefclassdata['norefRun']
		self.params['notstackid'] = norefRun['stack'].dbid
		if self.params['notstackid'] is None:
			apDisplay.printError("untilted stackid was not defined")
		boxsize = apStack.getStackBoxsize(self.params['tiltstackid'])
		if self.params['radius']*2 > boxsize-2:
			apDisplay.printError("particle radius is too big for stack boxsize")	

	#=====================
	def setOutDir(self):
		stackdata = apStack.getOnlyStackData(self.params['tiltstackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.dirname(os.path.abspath(path)))
		tempstr = ""
		for cnum in self.classlist:
			tempstr += str(cnum)+"-"
		classliststr = tempstr[:-1]

		self.params['outdir'] = os.path.join(uppath, "otrvolume", 
			self.params['runname'], "class"+str(classliststr) )
			
		

		### check if path exists in db already
		otrrunq = appionData.ApOtrRunData()
		otrrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		otrdata = otrrunq.query()
		if otrdata:
			apDisplay.printError("otr data already exists in database")

	#=====================
	def getParticleNoRefInPlaneRotation(self, stackpartdata):
		notstackpartdata = apTiltPair.getStackParticleTiltPair(self.params['tiltstackid'], 
			stackpartdata['particleNumber'], self.params['notstackid'])
		classpartq = appionData.ApNoRefClassParticlesData()
		classpartq['classRun'] = self.norefclassdata
		norefpartq = appionData.ApNoRefAlignParticlesData()
		norefpartq['particle'] = notstackpartdata
		classpartq['noref_particle'] = norefpartq
		classpartdatas = classpartq.query(results=1)
		if not classpartdatas or len(classpartdatas) != 1:
			apDisplay.printError("could not get inplane rotation")
		inplane = classpartdatas[0]['noref_particle']['rotation']
		return inplane

	#=====================
	def convertStackToSpider(self, emanstackfile, classnum):
		"""
		takes the stack file and creates a spider file ready for processing
		"""
		if not os.path.isfile(emanstackfile):
			apDisplay.printError("stackfile does not exist: "+emanstackfile)

		### first high pass filter particles
		apDisplay.printMsg("pre-filtering particles")
		apix = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])
		emancmd = ("proc2d "+emanstackfile+" "+emanstackfile
			+" apix="+str(apix)+" hp="+str(self.params['highpasspart'])
			+" inplace")
		apEMAN.executeEmanCmd(emancmd, verbose=True)

		### convert imagic stack to spider
		emancmd  = "proc2d "
		emancmd += emanstackfile+" "
		spiderstack = os.path.join(self.params['outdir'], str(classnum), "otrstack"+self.timestamp+".spi")
		apFile.removeFile(spiderstack, warn=True)
		emancmd += spiderstack+" "

		emancmd += "spiderswap edgenorm"
		starttime = time.time()
		apDisplay.printColor("Running spider stack conversion this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return spiderstack

	#=====================
	def sortTiltParticlesData(self, a, b):
		if a['particleNumber'] > b['particleNumber']:
			return 1
		return -1

	#=====================
	def insertOtrRun(self, volfile):
		### insert otr run data
		otrrunq = appionData.ApOtrRunData()
		otrrunq['runname']    = self.params['runname']
		tempstr = ""
		for cnum in self.classlist:
			tempstr += str(cnum)+","
		classliststr = tempstr[:-1]
		otrrunq['classnums']  = classliststr
		if len(self.classlist) == 1:
			otrrunq['classnum']  = self.classlist[0]
		otrrunq['numiter']    = self.params['numiters']
		otrrunq['maskrad']    = self.params['radius']
		otrrunq['lowpassvol'] = self.params['lowpassvol']
		otrrunq['highpasspart'] = self.params['highpasspart']
		otrrunq['description'] = self.params['description']
		otrrunq['path']  = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		otrrunq['norefclass'] = self.appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefclassid'])
		otrrunq['tiltstack']  = apStack.getOnlyStackData(self.params['tiltstackid'])
		if self.params['commit'] is True:
			otrrunq.insert()

		### insert 3d volume density
		densq = appionData.Ap3dDensityData()
		densq['otrrun'] = otrrunq
		densq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.abspath(volfile)))
		densq['name'] = os.path.basename(volfile)
		densq['hidden'] = False
		densq['norm'] = True
		densq['symmetry'] = self.appiondb.direct_query(appionData.ApSymmetryData, 25)
		densq['pixelsize'] = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])
		densq['boxsize'] = apStack.getStackBoxsize(self.params['tiltstackid'])
		densq['lowpass'] = self.params['lowpassvol']
		densq['highpass'] = self.params['highpasspart']
		densq['mask'] = self.params['radius']
		#densq['iterid'] = self.params['numiters']
		densq['description'] = self.params['description']
		#densq['resolution'] = float
		densq['session'] = apStack.getSessionDataFromStackId(self.params['tiltstackid'])
		densq['md5sum'] = apFile.md5sumfile(volfile)
		if self.params['commit'] is True:
			densq.insert()

		return

	#=====================
	def processVolume(self, spivolfile, cnum, iternum=0):
		### set values
		apix = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])
		boxsize = apStack.getStackBoxsize(self.params['tiltstackid'])
		rawspifile = os.path.join(self.params['outdir'], str(cnum),"rawvolume%s-%03d.spi"%(self.timestamp, iternum))
		emanvolfile = os.path.join(self.params['outdir'], str(cnum), "volume%s-%03d.mrc"%(self.timestamp, iternum))
		lowpass = self.params['lowpassvol']
		### copy original to raw file
		shutil.copy(spivolfile, rawspifile)
		### process volume files
		emancmd = ("proc3d "+spivolfile+" "+emanvolfile+" center norm=0,1 apix="
			+str(apix)+" lp="+str(lowpass))
		apEMAN.executeEmanCmd(emancmd, verbose=False)
		emancmd = "proc3d "+emanvolfile+" "+emanvolfile+" origin=0,0,0 "
		apEMAN.executeEmanCmd(emancmd, verbose=False)
		emancmd = "proc3d "+emanvolfile+" "+emanvolfile+" mask="+str(self.params['radius'])
		apEMAN.executeEmanCmd(emancmd, verbose=False)
		### convert to spider
		apFile.removeFile(spivolfile)
		emancmd = "proc3d "+emanvolfile+" "+spivolfile+" spidersingle"
		apEMAN.executeEmanCmd(emancmd, verbose=False)
		### image with chimera
		chimerathread = threading.Thread(target=apRecon.renderSnapshots, 
			args=(emanvolfile, 30, None, 1.5, 0.9, apix, 'c1', boxsize, False))
		chimerathread.setDaemon(1)
		chimerathread.start()

		return emanvolfile

	#=====================
	def getGoodParticles(self, classpartdatas, norefclassnum):
		includeParticle = []
		tiltParticlesData = []
		nopairParticle = 0
		excludeParticle = 0
		apDisplay.printMsg("sorting particles")
		for classpart in classpartdatas:
			#write to text file
			classnum = classpart['classNumber']-1
			if classnum == norefclassnum:
				notstackpartnum = classpart['noref_particle']['particle']['particleNumber']
				tiltstackpartdata = apTiltPair.getStackParticleTiltPair(self.params['notstackid'], 
					notstackpartnum, self.params['tiltstackid'])
				if tiltstackpartdata is None:
					nopairParticle += 1
				else:
					emantiltstackpartnum = tiltstackpartdata['particleNumber']-1
					includeParticle.append(emantiltstackpartnum)
					tiltParticlesData.append(tiltstackpartdata)
			else:
				excludeParticle += 1
		includeParticle.sort()
		apDisplay.printMsg("Keeping "+str(len(includeParticle))+" and excluding \n\t"
			+str(excludeParticle)+" particles with "+str(nopairParticle)+" unpaired particles")
		if len(includeParticle) < 1:
			apDisplay.printError("No particles were kept")
		#print includeParticle
		return includeParticle, tiltParticlesData

	#=====================
	def makeEulerDoc(self, tiltParticlesData, classnum):
		count = 0
		eulerfile = os.path.join(self.params['outdir'], str(classnum), "eulersdoc"+self.timestamp+".spi")
		eulerf = open(eulerfile, "w")
		apDisplay.printMsg("creating Euler doc file")
		starttime = time.time()
		tiltParticlesData.sort(self.sortTiltParticlesData)
		for stackpartdata in tiltParticlesData:
			count += 1
			if count%100 == 0:
				sys.stderr.write(".")
				eulerf.flush()
			gamma, theta, phi, tiltangle = apTiltPair.getParticleTiltRotationAngles(stackpartdata)
			inplane = self.getParticleNoRefInPlaneRotation(stackpartdata)
			psi = -1.0*(gamma + inplane)
			while psi < 0:
				psi += 360.0
			### this is the original eman part num; count is new part num
			partnum = stackpartdata['particleNumber']-1
			line = operations.spiderOutLine(count, [phi, tiltangle, psi])
			eulerf.write(line)
		eulerf.close()
		apDisplay.printColor("finished Euler doc file in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return eulerfile

	#=====================
	def projMatchRefine(self, classnum, volfile, alignstack, eulerfile, boxsize, numpart, pixrad):
		
		backproject.alignAPSH(volfile, alignstack, eulerfile, classnum, boxsize, numpart, pixrad, self.timestamp)
	
		### check APSH output
		APSHout = os.path.join(self.params['outdir'], str(classnum), "APSHout%s.spi"%(self.timestamp))
		if (os.path.isfile(APSHout) is False):
			apDisplay.printError("AP SH alignment did not generate a valid output file. Please check parameters and rerun!")
		
		apsh = open(APSHout, "r")
		
		neweulerdoc = os.path.join(self.params['outdir'], str(classnum),"newEulersdoc%s.spi"%(self.timestamp))
		neweulerfile = open(neweulerdoc, "w")
		rotshiftdoc = os.path.join(self.params['outdir'], str(classnum),"roShiftdoc%s.spi"%(self.timestamp))
		rotshiftfile = open(rotshiftdoc, "w")
		
		for line in apsh.readlines():
			value = line.split() 
			try:
				int(value[0])
			except:
				#apDisplay.printMsg(line)
				continue
			key = int(float(value[6]))
			rot = float(value[7])
			cumX = float(value[8])
			cumY = float(value[9])
			psi = float(value[2])
			theta = float(value[3])
			phi = float(value[4])
			
			### rotate and shift particle
			backproject.rotshiftParticle(alignstack, key, rot, cumX, cumY, self.timestamp, str(classnum))
			
			### write out new euler file
			eulerline = operations.spiderOutLine(key, [phi, theta, psi])
			neweulerfile.write(eulerline)
			
			rotshiftline = operations.spiderOutLine(key, [rot, 1.00, cumX, cumY])
			rotshiftfile.write(rotshiftline)
			
		neweulerfile.close()
		rotshiftfile.close()
		return

	#=====================
	def cccAPSH(self, APSHout, classnum):	
		### Calculate absolute shifts
		absshifts=[]
		
		APSHout = os.path.join(self.params['outdir'], str(classnum), "APSHout%s.spi"%(self.timestamp))
		apsh = open(APSHout, "r")
		
		for line in apsh.readlines():
			value = line.split() 
			try:
				int(value[0])
			except:
				#apDisplay.printMsg(line)
				continue
			
			### absshift = sqrt(x^2 + y^2)	
			absshift = math.sqrt((float(value[8])*float(value[8]))+(float(value[9])*float(value[9])))
			absshifts.append(absshift)

		apsh.close()
			
		### calculate the mean, variance and stdev of the absolute shift of the dataset	
		APSHmean = (numpy.array(absshifts)).mean()
		APSHvar = (numpy.array(absshifts)).var()
		APSHstd = (numpy.array(absshifts)).std()
		
		### calculate the weighted cross correlation values
		
		####################################################################
		##
		##								1
		## prob(shift) = ------------------ * e^[-1/2*(shift-mean)/stdev]**2
		##						stdev*sqrt(2*pi)
		##
		####################################################################
		const = APSHstd*math.sqrt(2*math.pi)
		probs=[]
		
		for absshift in absshifts:
		
			### probability for each particle
			prob = (1/const)*math.exp((-1/2)*((absshift-APSHmean)/APSHstd)*((absshift-APSHmean)/APSHstd))
			probs.append(prob)
			
		### output file for APSH with weighted CC values 
		APSHout_weighted = os.path.join(self.params['outdir'], str(classnum), "APSHout_weighted.spi")
		
		apsh = open(APSHout, "r")
		apshCCC = open(APSHout_weighted, "w")
		
		notline=0
		
		for i,line in enumerate(apsh.readlines()):
			value = line.split() 
			try:
				int(value[0])
			except:
				#apDisplay.printMsg(line)
				notline+=1
				continue
			
			key = int(float(value[6]))
			weightedCCvalue = float(value[12])*probs[i-notline]
			
			psi = float(value[2])
			theta = float(value[3])
			phi = float(value[4])
			ref = float(value[5])
			partnum =  float(value[6])
			rot = float(value[7])
			cumX = float(value[8])
			cumY = float(value[9])
			proj = float(value[10])
			diff = float(value[11])
			inplane = float(value[13])
			sx = float(value[14])
			sy = float(value[15])
			mirror = float(value[16])
						
			
			### write out new APSH file
			APSHline = operations.spiderOutLine(key, [psi, theta, phi, ref, partnum, rot, cumX, cumY, proj, diff, weightedCCvalue, inplane, sx, sy, mirror])
			apshCCC.write(APSHline)
			
		apshCCC.close()
		apsh.close()
		
		return APSHout_weighted

	#=====================
	def makecccAPSHselectFile(self, APSHout, factor, classnum):

		if (os.path.isfile(APSHout) is False):
			apDisplay.printError("File "+ APSHout +" does not exist!")
				
		apshFile = open(APSHout, "r")
		corrValues = []

		for line in apshFile.readlines():
			value = line.split()
			
			try:
				int(value[0])
			except:
				#apDisplay.printMsg(line)
				continue
			
			corrValues.append(float(value[12]))

		apshFile.close()

		corrmean = (numpy.array(corrValues)).mean()
		corrvar = (numpy.array(corrValues)).var()
		corrstd = (numpy.array(corrValues)).std()
		
		threshold = corrmean + (factor*corrstd)
		
		count = 1
		part = 1

		corrSelect = os.path.join(self.params['outdir'], str(classnum), "APSHcorrSelect.spi")
		corrSelectFile = open(corrSelect, "w")
		 

		for i,corrValue in enumerate(corrValues):
	
			if corrValue >= threshold:
				line = operations.spiderOutLine(count, [i])
				corrSelectFile.write(line)
				count+=1
	 
	 	corrSelectFile.close()
	 	
	 	return corrSelect
	 
	#=====================
	def splitOddEven(self, classnum, select):
	
		if (os.path.isfile(select) is False):
			apDisplay.printError("File "+ select +" does not exist!")
		
		selectFile = open(select, "r")
		selectFilename = os.path.splitext(os.path.basename(select))[0]
		
		selectOdd = os.path.join(self.params['outdir'], str(classnum), selectFilename+"Odd%s.spi"%(self.timestamp))
		selectOddFile = open(selectOdd, "w")
		
		selectEven = os.path.join(self.params['outdir'], str(classnum), selectFilename+"Even%s.spi"%(self.timestamp))
		selectEvenFile = open(selectEven, "w")
		
		for line in selectFile.readlines():
			value = line.split()
			
			try:
				int(value[0])
			except:
				#apDisplay.printMsg(line)
				continue
			
			if float(value[0])%2.0 == 1.0:
				sline = operations.spiderOutLine(count, [value[0]])
				selectOddFile.write(line)
			else:
				sline = operations.spiderOutLine(count, [value[0]])
				selectEvenFile.write(line)

		selectOddFile.close()
		selectEvenFile.close()
		
		return
		
	#=====================NEEDS LOTS OF WORK
	def APSHbackProject(self, cnum, selectFile):
		"""
			# file that stores the number of iteration for BPRP
			BPRPcount = os.path.join(self.params['outdir'], str(cnum), "numiter.spi")
			
			if (os.path.isfile(BPRPcount)):
				apDisplay.printMsg("BP RP counter file exists: "+BPRPcount+"! File will be deleted.")
				apFile.removeFile(BPRPcount)

			BPRPlambda=2e-5
			backproject.backprojectRP(spiderstack, eulerfile, volfile,
				pixrad=self.params['radius'], classnum=cnum, lambDa=BPRPlambda, selfile=selectFile)
						
			count = 0
			rounds = 0
			
			### repeat BPRP for 100 times with different values of lambda or until BPRP manages to do 50 iterations
			while count < 50 and rounds < 100:
				if (os.path.isfile(BPRPcount)):
					bc = open(BPRPcount, "r")
					for line in bc.readlines():
						value = line.split() 
						if value[0]=="1":
							count = int(float(value[2]))
							if count < 50:
								apDisplay.printMsg("BPRP iteration is "+str(count)+" (less than 50)... redoing BPRP")
								bc.close()
								apFile.removeFile(BPRPcount)
								BPRPlambda = BPRPlambda/2
								backproject.backprojectRP(spiderstack, eulerfile, volfile,
									pixrad=self.params['radius'], classnum=cnum, lambDa=BPRPlambda, numpart=len(includeParticle))
				else: 
					apDisplay.printWarning("numiter is missing")
					continue
				rounds+=1
			
			### print warning if BPRP reaches 100 rounds
			if rounds >=100:
				apDisplay.printWarning("BPRP attempted 100 times but iteration is still less than 50. Check BPRP params.")
			

		
			backproject.backprojectRP(spiderstack, eulerfile, volfile,
				pixrad=self.params['radius'], classnum=cnum, lambDa=BPRPlambda, selfile=)
			
			# file that stores the number of iteration for BPRP
			BPRPcount = os.path.join(self.params['outdir'], str(cnum), "numiter.spi")
		"""
		return

	#=====================
	def computeClassVolPair(self):
		done=[]
		pairlist=[]
		
		for i in self.classlist:
			for j in self.classlist:
				done.append(i)
				if j not in done:
					pair=[]
					pair.append(i)
					pair.append(j)
					pairlist.append(pair)
		return pairlist

	#=====================
	def start(self):
	
		### get stack data
		notstackdata = apStack.getOnlyStackData(self.params['notstackid'])
		tiltstackdata = apStack.getOnlyStackData(self.params['tiltstackid'])
		pixelsize = tiltstackdata['pixelsize']*1e10
		boxsize = apStack.getStackBoxsize(self.params['tiltstackid'])

		### get particles from noref class run
		classpartq = appionData.ApNoRefClassParticlesData()
		classpartq['classRun'] = self.norefclassdata
		classpartdatas = classpartq.query()
		apDisplay.printMsg("Found "+str(len(classpartdatas))+" particles in the norefRun")

		for cnum in self.classlist:
			
			print "\n"
			apDisplay.printMsg("###########################")
			apDisplay.printMsg("Processing stack of class "+str(cnum)+"")
			apDisplay.printMsg("###########################")
			print "\n"
			
			### get good particle numbers
			includeParticle, tiltParticlesData = self.getGoodParticles(classpartdatas, cnum)
			
			### write kept particles to file
			apParam.createDirectory(os.path.join(self.params['outdir'], str(cnum)))
			self.params['keepfile'] = os.path.join(self.params['outdir'], str(cnum), "keepfile"+self.timestamp+".lst")
			apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
			kf = open(self.params['keepfile'], "w")
			for partnum in includeParticle:
				kf.write(str(partnum)+"\n")
			kf.close()

			### make new stack of tilted particle from that run
			tiltstackfile = os.path.join(tiltstackdata['path']['path'], tiltstackdata['name'])
			otrstackfile = os.path.join(self.params['outdir'], str(cnum), "otrstack"+self.timestamp+".hed")
			#otrstackfile = os.path.join(self.params['outdir'], str(cnum), "otrstack08nov12p40.hed")
			apFile.removeStack(otrstackfile)
			apStack.makeNewStack(tiltstackfile, otrstackfile, self.params['keepfile'])
			spiderstack = self.convertStackToSpider(otrstackfile, cnum)
			#spiderstack = os.path.join(self.params['outdir'], str(cnum), "otrstack08nov12p40.spi")

			### make doc file of Euler angles
			eulerfile = self.makeEulerDoc(tiltParticlesData, cnum)
			#eulerfile = "/ami/data15/appion/08aug02a/otrvolume/otr1/class0-1/0/eulersdoc08nov12p40.spi"
			
			### iterations over volume creation
			looptime = time.time()
			### back project particles into filter volume
			volfile = os.path.join(self.params['outdir'], str(cnum), "volume%s-%03d.spi"%(self.timestamp, 0))

			# file that stores the number of iteration for BPRP
			BPRPcount = os.path.join(self.params['outdir'], str(cnum), "numiter.spi")
			
			if (os.path.isfile(BPRPcount)):
				apDisplay.printMsg("BP RP counter file exists: "+BPRPcount+"! File will be deleted.")
				apFile.removeFile(BPRPcount)

			BPRPlambda=2e-5
			backproject.backprojectRP(spiderstack, eulerfile, volfile,
				pixrad=self.params['radius'], classnum=cnum, lambDa=BPRPlambda, numpart=len(includeParticle))
						
			count = 0
			rounds = 0
			
			### repeat BPRP for 100 times with different values of lambda or until BPRP manages to do 50 iterations
			while count < 50 and rounds < 100:
				if (os.path.isfile(BPRPcount)):
					bc = open(BPRPcount, "r")
					for line in bc.readlines():
						value = line.split() 
						if value[0]=="1":
							count = int(float(value[2]))
							if count < 50:
								apDisplay.printMsg("BPRP iteration is "+str(count)+" (less than 50)... redoing BPRP")
								bc.close()
								apFile.removeFile(BPRPcount)
								BPRPlambda = BPRPlambda/2
								backproject.backprojectRP(spiderstack, eulerfile, volfile,
									pixrad=self.params['radius'], classnum=cnum, lambDa=BPRPlambda, numpart=len(includeParticle))
				else: 
					apDisplay.printWarning("numiter is missing")
					continue
				rounds+=1
			
			### print warning if BPRP reaches 100 rounds
			if rounds >=100:
				apDisplay.printWarning("BPRP attempted 100 times but iteration is still less than 50. Check BPRP params.")
			
			### filter the volume (low-pass Butterworth)
			backproject.butterworthLP(volfile, pixelsize)
			
			### need work... filtered volume has a different name
			backproject.normalizeVol(volfile)
			
			alignstack = spiderstack
			
			### center/convert the volume file
			emanvolfile = self.processVolume(volfile, cnum, 0)

			for i in range(5):
				iternum = i+1
				apDisplay.printMsg("running backprojection iteration "+str(iternum))
				### xy-shift particles to volume projections
				alignstack = backproject.otrParticleShift(volfile, alignstack, eulerfile, iternum, 
					numpart=len(includeParticle), pixrad=self.params['radius'], timestamp=self.timestamp, classnum=cnum)
				apDisplay.printColor("finished volume refinement in "
					+apDisplay.timeString(time.time()-looptime), "cyan")
					
				### back project particles into better volume
				volfile = os.path.join(self.params['outdir'], str(cnum), "volume%s-%03d.spi"%(self.timestamp, iternum))
				backproject.backproject3F(alignstack, eulerfile, volfile,
					numpart=len(includeParticle))

				### filter the volume (low-pass Butterworth)
				backproject.butterworthLP(volfile, pixelsize)
				
				### need work... filtered volume has a different name
				backproject.normalizeVol(volfile)

				### center/convert the volume file
				emanvolfile = self.processVolume(volfile, cnum, iternum)
			
			#volfile = "/ami/data15/appion/08aug02a/otrvolume/otr2/class0-1/0/volume08nov17f42-005.spi"
			#alignstack = "/ami/data15/appion/08aug02a/otrvolume/otr2/class0-1/0/alignstack08nov17f42-005.spi"
			#eulerfile =  "/ami/data15/appion/08aug02a/otrvolume/otr2/class0-1/0/eulersdoc08nov17f42.spi"
				
			### projection-matching refinement/XMIPP
			self.projMatchRefine(cnum, volfile, alignstack, eulerfile, boxsize, len(includeParticle), self.params['radius'])
					
			APSHout = os.path.join(self.params['outdir'], str(cnum), "APSHout%s.spi"%(self.timestamp))

			self.cccAPSH(APSHout, cnum)
	
			factor=0.1
			corrSelect = self.makecccAPSHselectFile(APSHout, factor, cnum)
			
			self.splitOddEven(cnum, corrSelect)

			#run BPRP on selected particles
			
			#calculate FSC
			
			
			
		sys.exit(1)





		if len(self.classlist) > 1:
			#get a list of all unique combinations of volumes
			pairlist = self.computeClassVolPair()	
			


		### optimize Euler angles
		#NOT IMPLEMENTED YET

		### insert volumes into DB
		self.insertOtrRun(emanvolfile)

#=====================
if __name__ == "__main__":
	otrVolume = otrVolumeScript()
	otrVolume.start()
	otrVolume.close()

