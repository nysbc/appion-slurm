#!/usr/bin/env python

#python
import os
import re
import sys
import time
import math
import subprocess
import shutil
#appion
from appionlib import appionScript
from appionlib import apEMAN
from appionlib import apDisplay
from appionlib import apChimera
from appionlib import apEulerJump
from appionlib import apStack
from appionlib import apModel
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apSymmetry
from appionlib import apRecon
from appionlib import apFrealign
from appionlib import reconUploader

class UploadFrealignScript(reconUploader.generalReconUploader):
	
	def __init__(self):
		###	DEFINE THE NAME OF THE PACKAGE
		self.package = "Frealign"
		self.multiModelRefinementRun = False
		super(UploadFrealignScript, self).__init__()
			
	#=====================
	def findLastCompletedIteration(self):
		recondir = os.path.join(self.params['rundir'], "recon")
		iternum = 0
		stop = False
		while stop is False:
			## check if iteration is complete
			iternum += 1

			imagicvolume = "threed.%03da.mrc"%(iternum)
			imagicvolumepath = os.path.join(recondir,imagicvolume)
			if not os.path.isfile(imagicvolumepath):
				apDisplay.printWarning("Volume file %s is missing"%(imagicvolumepath))
				stop = True
				break

		### set last working iteration
		numiter = iternum-1
		if numiter < 1:
			apDisplay.printError("No iterations were found")
		apDisplay.printColor("Found %d complete iterations"%(numiter), "green")

		return numiter	
	
	#=====================
	def createParticleDataFile(self, iteration, package_database_object):
		''' puts all relevant particle information into a single text file that can be read by the uploader '''
		
		os.chdir(self.projmatchpath)
		
		### read particle info
		paramfile = os.path.join(self.projmatchpath, "params.%03d.par"%(iteration))
		parttree = apFrealign.parseFrealignParamFile(paramfile)

		### write data in appion format to input file for uploading to the database
		partdatafilepath = os.path.join(self.resultspath, "particle_data_%s_it%.3d_vol001.txt" % (self.params['timestamp'], iteration))
		particledataf = open(partdatafilepath, "w")
		particledataf.write("### column info: ")
		particledataf.write("(1) particle number ")
		particledataf.write("(2) phi ")
		particledataf.write("(3) theta ")
		particledataf.write("(4) omega ")
		particledataf.write("(5) shiftx ")
		particledataf.write("(6) shifty ")
		particledataf.write("(7) mirror ")
		particledataf.write("(8) 3D reference # ")
		particledataf.write("(9) 2D class # ")
		particledataf.write("(10) quality factor ")
		particledataf.write("(11) kept particle ")
		particledataf.write("(12) postRefine kept particle \n")				

		### add each particle to the file
		count = 0
		for partdict in parttree:
			count += 1
			if count % 500 == 0:
				apDisplay.printMsg("Wrote %d particles to Particle Data File: %s"%(count,partdatafilepath))

			particledataf.write("%.6d\t" % int(partdict['partnum'])) ### NOTE: IT IS IMPORTANT TO START WITH 1, OTHERWISE STACKMAPPING IS WRONG!!!
			particledataf.write("%.6f\t" % float(partdict['euler1']))
			particledataf.write("%.6f\t" % float(partdict['euler2']))
			particledataf.write("%.6f\t" % float(partdict['euler3']))
			particledataf.write("%.6f\t" % float(partdict['shiftx']))
			particledataf.write("%.6f\t" % float(partdict['shifty']))
			particledataf.write("%.6d\t" % 0)
			particledataf.write("%.6d\t" % 1)
			particledataf.write("%.6d\t" % 0)
			particledataf.write("%.6d\t" % 1)
			if partdict['phase_residual'] > package_database_object['thresh']:
				particledataf.write("%.6f\t" % 1)
			else:
				particledataf.write("%.6f\t" % 1) #TODO: this should be false???
			particledataf.write("%.6f\n" % 1)
			
		### close the new file
		particledataf.close()
		
		os.chdir(self.params['rundir'])
				
		return
	
	#===============
	def convertBool(self, val):
		""" Convert single letter T or F to bool"""
		if val.lower().startswith('f') or val.strip() == '0':
			return False
		return True	

	#=====================
	def readParamsFromCombineFile(self, iternum):
		"""
		read the combine file to get iteration parameters,
		such as symmetry and phase residual cutoff
		"""
		iterparams = {'iternum': iternum,}
		recondir = os.path.join(self.params['rundir'], "recon")

		combinefile = "iter%03d/frealign.iter%03d.proc%03d.sh"%(iternum, iternum, iternum)
		conbinefilepath = os.path.join(recondir, combinefile)
		f = open(conbinefilepath, "r")
		### locate start
		for line in f:
			if line.startswith("### START FREALIGN ###"):
				break

		### parse file
		cards = []
		for line in f:
			cards.append(line.strip())
			if line.startswith("EOF"):
				break
		f.close()

		### get lots of info from card #1
		data = cards[1].split(",")
		#print data
		iterparams['cform'] = data[0]
		iterparams['iflag'] = int(data[1])
		iterparams['fmag'] = self.convertBool(data[2])
		iterparams['fdef'] = self.convertBool(data[3])
		iterparams['fastig'] = self.convertBool(data[4])
		iterparams['fpart'] = self.convertBool(data[5])
		iterparams['iewald'] = float(data[6])
		iterparams['fbeaut'] = self.convertBool(data[7])
		iterparams['fcref'] = self.convertBool(data[8])
		iterparams['fmatch'] = self.convertBool(data[9])
		iterparams['ifsc'] = self.convertBool(data[10])
		iterparams['fstat'] = self.convertBool(data[11])
		iterparams['iblow'] = int(data[12])

		### get lots of info from card #2
		data = cards[2].split(",")
		#print data
		iterparams['mask'] = float(data[0])
		iterparams['imask'] = float(data[1])
		iterparams['wgh'] = float(data[3])
		iterparams['xstd'] = float(data[4])
		iterparams['pbc'] = float(data[5])
		iterparams['boff'] = float(data[6])
		iterparams['dang'] = float(data[7]) ### only used for recon search
		iterparams['itmax'] = int(data[8])
		iterparams['ipmax'] = int(data[9])

		### get symmetry info from card #5
		symmdata = apSymmetry.findSymmetry(cards[5])
		apDisplay.printMsg("Found symmetry %s with id %s"%(symmdata['eman_name'], symmdata.dbid))
		iterparams['symmdata'] = symmdata

		### get threshold info from card #6
		data = cards[6].split(",")
		#print data
		iterparams['target'] = float(data[2])
		iterparams['thresh'] = float(data[3])
		iterparams['cs'] = float(data[4])

		### get limit info from card #7
		data = cards[7].split(",")
		#print data
		iterparams['rrec'] = float(data[0])
		iterparams['highpass'] = float(data[1])
		iterparams['lowpass'] = float(data[2])
		iterparams['rbfact'] = float(data[4])

		#print iterparams
		return iterparams
	
		#=====================
	def parseFileForRunParameters(self):
		''' PACKAGE-SPECIFIC FILE PARSER: if the parameters were not pickled, parse protocols script to determine projection-matching params '''

		"""
		read the combine file to get iteration parameters,
		such as symmetry and phase residual cutoff
		"""
		iternum = 1
		iterparams = self.readParamsFromCombineFile(iternum)
		
		### set global parameters
		runparams = {}
		runparams['numiter'] = self.findLastCompletedIteration()
		runparams['mask'] = int(iterparams['mask'])
		runparams['imask'] = int(iterparams['imask'])
		runparams['symmetry'] = iterparams['symmdata']
		runparams['package_params'] = iterparams
		runparams['remoterundir'] = self.params['rundir']
		runparams['rundir'] = self.params['rundir']
		runparams['NumberOfReferences'] = 1 # assume 1 for now, until frealign does more.

		return runparams

	#=====================
	def instantiateProjMatchParamsData(self, iteration):
		''' fill in database entry for ApFrealignIterData table '''

		### read iteration info
		iterparams = self.readParamsFromCombineFile(iteration)
		
		frealigniterq = appiondata.ApFrealignIterData()
		frealignkeys = ('wgh', 'xstd', 'pbc', 'boff',
			'itmax', 'ipmax', 'target', 'thresh', 'cs',
			'rrec', 'highpass', 'lowpass', 'rbfact')
		for key in frealignkeys:
			frealigniterq[key] = iterparams[key]

		return frealigniterq
	
	#======================	
	def convertFSCFileForIteration(self, iteration):
		'''  Frealign creates FSC files with pixel number in column 1, FSC in column 2, convert this to 3DEM format '''
	
		fscfile = os.path.join(self.projmatchpath, "iter%03d" % iteration, "fsc.eotest.%d" % iteration)

		try: 
			f = open(fscfile, "r")
		except IOError, e:
			apDisplay.printWarning("%s file could not be opened, data will NOT be inserted into the database" % fscfile)
			return False
		
		fsclines = f.readlines()
		f.close()
		split = [l.strip().split() for l in fsclines]
		newfscfile = open(os.path.join(self.resultspath, "recon_%s_it%.3d_vol001.fsc" % (self.params['timestamp'], iteration)), "w")
		newfscfile.write("### column (1) inverse Angstroms, column (2) Fourier Shell Correlation (FSC)")
		for info in split:
			ipixel = float(info[0]) / (self.runparams['boxsize'] * self.runparams['apix'])
			fsc = float(info[1])
			newfscfile.write("%.6f\t%.6f\n" % (ipixel, fsc))
		newfscfile.close()
		
		return True
	
	#=====================
	def start(self):
		
		### database entry parameters
		package_table = 'ApFrealignIterData|frealignParams'
		
		### set projection-matching path
		self.projmatchpath = os.path.abspath(os.path.join(self.params['rundir'], "recon"))
	
		### determine which iterations to upload
		lastiter = self.findLastCompletedIteration()
		uploadIterations = self.verifyUploadIterations(lastiter)	

		for iteration in uploadIterations:
		
			apDisplay.printColor("uploading iteration %d" % iteration, "cyan")
			
			package_database_object = self.instantiateProjMatchParamsData(iteration)
			
			### move FSC file to results directory
			self.FSCExists = self.convertFSCFileForIteration(iteration)
				
			### create a text file with particle information
			self.createParticleDataFile(iteration, package_database_object)
					
			### create mrc file of map for iteration and reference number
			oldvol = os.path.join(self.projmatchpath, "threed.%03da.mrc" % iteration)
			newvol = os.path.join(self.resultspath, "recon_%s_it%.3d_vol001.mrc" % (self.params['timestamp'], iteration))
			if not os.path.isfile(newvol) and not os.path.islink(oldvol):
				try:
					shutil.move(oldvol, newvol)
					os.symlink(newvol, oldvol)
				except IOError, e:
					print e
			
			### make chimera snapshot of volume
			self.createChimeraVolumeSnapshot(newvol, iteration)
			
			### instantiate database objects
			self.insertRefinementRunData(iteration)
			self.insertRefinementIterationData(iteration, package_table, package_database_object)
				
		### calculate Euler jumps
		self.calculateEulerJumpsAndGoodBadParticles(uploadIterations)	
		
		### query the database for the completed refinements BEFORE deleting any files ... returns a dictionary of lists
		### e.g. {1: [5, 4, 3, 2, 1]} means 5 iters completed for refine 1
#		complete_refinements = self.verifyNumberOfCompletedRefinements(multiModelRefinementRun=False)
#		if self.params['cleanup_files'] is True:
#			self.cleanupFiles(complete_refinements)

#=====================
if __name__ == "__main__":
	upload3D = UploadFrealignScript()
	upload3D.start()
	upload3D.close()
	
		