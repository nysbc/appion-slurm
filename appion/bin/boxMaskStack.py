#!/usr/bin/env python

#python
import os
import re
import shutil
import subprocess
import sys
import time
#appion
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apDisplay
from appionlib import apEMAN
from appionlib import apStack
from appionlib import apFile
from appionlib import spyder

class boxMaskScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack-id=ID --align-id=ID [options]")
		self.parser.add_option("-s", "--stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("-a", "--align-stack-id", dest="alignstackid", type="int",
			help="aligned stack database id", metavar="ID")
		self.parser.add_option("--new-stack-name", dest="runname",
			help="New stack name", metavar="STR")
		self.parser.add_option("-m", "--mask", dest="mask", type="int",
			help="outer mask radius in Angstroms")
		self.parser.add_option("-i", "--imask", dest="imask", type="int", default=0,
			help="inner mask radius in Angstroms")
		self.parser.add_option("-l", "--len", dest="length", type="int", default=240,
			help="length of mask along filament in Angstroms")
		self.parser.add_option("--falloff", dest="falloff", type="int", default=90,
			help="falloff for edges in Angstroms")
		self.parser.add_option("--vertical", dest="vertical", action="store_true", default=False,
			help="particles are already aligned vertically")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['alignstackid'] is None and self.params['vertical'] is False:
			apDisplay.printError("alignstackid was not defined")
		if self.params['description'] is None:
			apDisplay.printError("substack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])
		if self.params['vertical'] is not True:
			self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])

	#=====================
	def convertStackToSpider(self, stackfile):
		### convert imagic stack to spider
		emancmd  = "proc2d %s "%stackfile
		spiderstack = os.path.join(self.params['rundir'], "tmpspistack"+self.timestamp+".spi")
		apFile.removeFile(spiderstack, warn=True)
		emancmd += spiderstack+" "

		emancmd += "spiderswap edgenorm"
		starttime = time.time()
		apDisplay.printColor("Running spider stack conversion this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		time.sleep(1) # wait a sec, for things to finish
		apDisplay.printColor("finished proc2d in "+apDisplay.timeString(time.time()-starttime), "cyan")

		if not os.path.isfile(spiderstack):
			apDisplay.printError("Failed to create a spider stack")

		return spiderstack
	
	#=====================
	def findRotation(self,avgimg):
		# use radon transform in SPIDER to find rotation to orient the average image vertical
		if os.path.isfile("angle.spi"):
			os.remove("angle.spi")

		box=self.alignstackdata['boxsize']
		mySpi = spyder.SpiderSession(dataext=".spi", logo=False, log=False)
		# circular mask the average
		mySpi.toSpider("MA",
			spyder.fileFilter(avgimg)+"@1",
			"_1",
			"%i,0"%((box/2)-2),
			"C",
			"E",
			"0",
			"%i,%i"%((box/2)+1,(box/2)+1),
			"3")
		# get power spectrum
		mySpi.toSpider("PW","_1","_2")
		# Radon transform
		mySpi.toSpider("RM 2DN",
			"_2",
			"1",
			"_3",
			"%i"%box,
			"%i"%(box/2),
			"0,0",
			"N")
		# mask in the X direction to only include equator
		mySpi.toSpider("MA X",
			"_3",
			"_4",
			"6,0",
			"D",
			"E",
			"0",
			"%i,%i"%((box/2),(box/2)))
		# find peak
		mySpi.toSpider("PK x20,x21,x22","_4","1,0")
		# save the angles to a file
		mySpi.toSpider("SD 1, x21","angle")
		mySpi.toSpider("SD E","angle")
		mySpi.close()

		f = open("angle.spi")
		for line in f:
			d=line.strip().split()
			if d[0][0]==";" or len(d) < 3:
				continue
			rot = float(d[2])

		os.remove("angle.spi")
		os.remove(avgimg)
		return rot

	#=====================
	def getInplaneRotations(self):
		# get all the particle rotations
		apDisplay.printMsg("reading alignment data from database")
		alignpartq = appiondata.ApAlignParticleData()
		alignpartq['alignstack'] = self.alignstackdata
		alignpartdatas = alignpartq.query()
		rotationlist = [None]*len(alignpartdatas)
		for part in alignpartdatas:
			rotationlist[part['partnum']-1] = -part['rotation']		

		return rotationlist

	#=====================
	def createRotationSpiList(self,rotationlist,rot):
		# create a SPIDER-formatted file for masking
		f = open("spirots.spi",'w')
		f.write(";           angle\n")
		for part in range(len(rotationlist)):	
			spiline = "%5d%2d%10.2f\n" % (part+1,1,rot+rotationlist[part])
			f.write(spiline)
		f.close()
		return "spirots.spi"

	#=====================
	def boxMask(self,infile,outfile,spirots=None):
		# boxmask the particles
		apDisplay.printMsg("masking the particles with a rectangular box")

		nump = apStack.getNumberStackParticlesFromId(self.params['stackid'])
		box = self.stackdata['boxsize']
		apix = self.stackdata['pixelsize']*1e10
		if self.params['mask'] is None:
			mask = box/2-2
		else:
			mask = int(self.params['mask']/apix)
		imask = int(self.params['imask']/apix)
		length = int(self.params['length']/apix)
		falloff = self.params['falloff']/apix

		mask -= falloff/2
		length = (length/2)-(falloff/2)
		
		mySpi = spyder.SpiderSession(dataext=".spi", logo=False, log=False)
		# create blank image for mask
		mySpi.toSpiderQuiet("BL","_1","%i,%i"%(box,box),"N","1")
		# mask it in X
		mySpi.toSpiderQuiet("MA X",
			"_1",
			"_2",
			"%i"%mask,
			"C",
			"E",
			"0",
			"%i,%i"%(box/2,box/2),
			"%.2f"%falloff)
		# inner mask in X
		mySpi.toSpiderQuiet("MA X",
			"_2",
			"_3",
			"%i,%i"%(box/2,imask),
			"C",
			"E",
			"0",
			"%i,%i"%(box/2,box/2),
			"%.2f"%(falloff/4))
		# mask in Y
		mySpi.toSpiderQuiet("MA Y",
			"_3",
			"_4",
			"%i"%length,
			"C",
			"E",
			"0",
			"%i,%i"%(box/2,box/2),
			"%.2f"%falloff)
		mySpi.toSpider("do x10=1,%i"%nump)
		if self.params['vertical'] is not True:
			mySpi.toSpider("UD IC x10,x30",
				spyder.fileFilter(spirots),
				"x30 = -1*x30",
				"RT B",
				"_4",
				"_9",
				"(x30)",
				"(0)",
				"MU",
				spyder.fileFilter(infile)+"@{******x10}",
				"_9")
		else:
			mySpi.toSpider("MU",
				spyder.fileFilter(infile)+"@{******x10}",
				"_4")
	
		mySpi.toSpider(spyder.fileFilter(outfile)+"@{******x10}",
			"*",
			"enddo")
		if self.params['vertical'] is not True:
			mySpi.toSpider("UD ICE",spyder.fileFilter(spirots))
		mySpi.close()

		sys.exit()

	#=====================
	def start(self):
		# Path of the stack
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'])
		fn_oldstack = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])

		rotfile = None
		if self.params['vertical'] is not True:
			# get averaged image:
			self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])
			avgimg = os.path.join(self.alignstackdata['path']['path'], self.alignstackdata['avgmrcfile'])

			# Convert averaged aligned mrcfile to spider
			spiavg = os.path.join(self.params['rundir'],"avg.spi")
			emancmd = "proc2d %s %s spiderswap edgenorm"%(avgimg,spiavg)
			apEMAN.executeEmanCmd(emancmd, verbose=True)

			# find rotation for vertical alignment
			rot = self.findRotation(spiavg)
			apDisplay.printMsg("found average rotation: %.2f"%rot)

			rotlist = self.getInplaneRotations()
			rotfile = self.createRotationSpiList(rotlist,rot)

		# Convert the original stack to spider
		spistack = self.convertStackToSpider(fn_oldstack)
		# boxmask the particles
		self.boxMask(spistack,"masked.spi",rotfile)

		# Create average MRC
		apStack.averageStack("sorted.hed")

		# Upload results
		self.uploadResults()

		time.sleep(1)
		return

	#=====================
	def uploadResults(self):
		if self.params['commit'] is False:
			return

		# Get the new file order
		fh=open("sort_junk.sel",'r')
		lines=fh.readlines()
		i=0;
		fileorder={};
		for line in lines:
			args=line.split()
			if (len(args)>1):
				match=re.match('[A-Za-z]+([0-9]+)\.[A-Za-z]+',
				   (args[0].split('/'))[-1])
				if (match):
					filenumber=int(match.groups()[0])
					fileorder[i]=filenumber
					i+=1
		fh.close()

		# Produce a new stack
		oldstack = apStack.getOnlyStackData(self.params['stackid'],msg=False)
		newstack = appiondata.ApStackData()
		newstack['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		newstack['name'] = "sorted.hed"
		if newstack.query(results=1):
			apDisplay.printError("A stack with these parameters already exists")

		# Fill in data and submit
		newstack['oldstack'] = oldstack
		newstack['hidden'] = False
		newstack['substackname'] = self.params['runname']
		newstack['description'] = self.params['description']
		newstack['pixelsize'] = oldstack['pixelsize']
		newstack['boxsize'] = oldstack['boxsize']		
		newstack['junksorted'] = True
		newstack.insert()

		# Insert stack images
		apDisplay.printMsg("Inserting stack particles")
		count=0
		total=len(fileorder.keys())
		if total==0:
			apDisplay.printError("No particles can be inserted in the sorted stack")
		for i in fileorder.keys():
			count += 1
			if count % 100 == 0:
				sys.stderr.write("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b")
				sys.stderr.write(str(count)+" of "+(str(total))+" complete")

			# Get particle from the old stack
			oldparticle = apStack.getStackParticle(self.params['stackid'], fileorder[i]+1)

			# Insert particle
			newparticle = appiondata.ApStackParticleData()
			newparticle['particleNumber'] = i+1
			newparticle['stack'] = newstack
			newparticle['stackRun'] = oldparticle['stackRun']
			newparticle['particle'] = oldparticle['particle']
			newparticle['mean'] = oldparticle['mean']
			newparticle['stdev'] = oldparticle['stdev']
			newparticle.insert()
		apDisplay.printMsg("\n"+str(total)+" particles have been inserted into the sorted stack")

		# Insert runs in stack
		apDisplay.printMsg("Inserting Runs in Stack")
		runsinstack = apStack.getRunsInStack(self.params['stackid'])
		for run in runsinstack:
			newrunsq = appiondata.ApRunsInStackData()
			newrunsq['stack'] = newstack
			newrunsq['stackRun'] = run['stackRun']
			newrunsq.insert()

		apDisplay.printMsg("finished")
		return

#=====================
if __name__ == "__main__":
	sortJunk = boxMaskScript()
	sortJunk.start()
	sortJunk.close()


