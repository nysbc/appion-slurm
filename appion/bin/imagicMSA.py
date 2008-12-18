#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import shutil
import time
import sys
import re

import appionScript
import appionData
import apParam
import apRecon
import apDisplay
import apEMAN
import apFile
import apUpload
import apDatabase
import apStack
import apProject
import apIMAGIC

#=====================
#=====================
class imagicMultivariateStatisticalAnalysisScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --rundir=<dir> "
			+"[options]")

		self.parser.add_option("--alignid", dest="alignid",
			help="ID of particle stack", metavar="int")
		self.parser.add_option("--lpfilt", dest="lpfilt", type="int",
			help="low-pass filter value (in angstroms)", metavar="INT")
		self.parser.add_option("--hpfilt", dest="hpfilt", type="int", 
			help="high-pass filter value (in angstroms)", metavar="INT")
		self.parser.add_option("--mask_radius", dest="mask_radius", type="float", default=1.0,
			help="radius of mask for MSA (in pixels or fraction of radius)", metavar="FLOAT")
                self.parser.add_option("--mask_dropoff", dest="mask_dropoff", type="float", 
                        help="dropoff (softness) of mask for MSA (in pixels or fraction of radius)", metavar="FLOAT")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="binning of the image (power of 2)", metavar="INT")
		self.parser.add_option("--numiters", dest="numiters", type="int", default=50,
			help="number of iterations for MSA run", metavar="INT")
		self.parser.add_option("--overcorrection", dest="overcorrection", type="float", default=0.8,
			help="overcorrection factor for MSA program (determines its convergence speed)", metavar="FLOAT")
		self.parser.add_option("--MSAmethod", dest="MSAmethod", type="str",
			help="distance criteria that will be used in MSA", metavar="STR")

		return 

	#=====================
	def checkConflicts(self):
		if self.params['alignid'] is None:
			apDisplay.printError("There is no stack ID specified")
		if self.params['runname'] is None:
			apDisplay.printError("enter a run ID")
		if self.params['MSAmethod'] is None:
			apDisplay.printError("enter distance criteria for MSA program (i.e. eulidean, chisquare, modulation)")
		
		return

	#=====================
	def setRunDir(self):
		# get reference-free classification and reclassification parameters
		if self.params['alignid'] is not None:
                	self.alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignid'])
                	path = self.alignstackdata['path']['path']
                	uppath = os.path.abspath(os.path.join(path, "../.."))
                	self.params['rundir'] = os.path.join(uppath, "imagicmsa", self.params['runname'])

        #=====================
        def checkAnalysisRun(self):
                # create a norefParam object
                analysisrunq = appionData.ApAlignAnalysisRunData()
                analysisrunq['runname'] = self.params['runname']
                analysisrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
                # ... path makes the run unique:
                uniquerun = analysisrunq.query(results=1)
                if uniquerun:
                        apDisplay.printError("Run name '"+self.params['runname']+"' for stackid="+\
                                str(self.params['alignid'])+"\nis already in the database")

	#=====================
	def createImagicBatchFile(self):
                # IMAGIC batch file creation    
                filename = os.path.join(self.params['rundir'], "imagicMultivariateStatisticalAnalysis.batch")
                f = open(filename, 'w')
                f.write("#!/bin/csh -f\n")
                f.write("setenv IMAGIC_BATCH 1\n")
                if self.params['bin'] > 1:
                        f.write("/usr/local/IMAGIC/stand/coarse.e <<EOF > imagicMultivariateStatisticalAnalysis.log\n")
                        f.write("start\n")
                        f.write("start_coarse\n")
                        f.write(str(self.params['bin'])+"\n")
                        f.write("EOF\n")
                        f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagicMultivariateStatisticalAnalysis.log\n")
                        f.write("start_coarse\n")
                        f.write("start\n")
                        f.write("EOF\n")
                if self.params['hpfilt_imagic'] and self.params['lpfilt_imagic'] is not None:
                        f.write("/usr/local/IMAGIC/incore/incband.e OPT BAND-PASS <<EOF")
                        if  os.path.isfile("imagicMultivariateStatisticalAnalysis.log"):
                                f.write(" >> imagicMultivariateStatisticalAnalysis.log\n")
                        else:
                                f.write(" > imagicMultivariateStatisticalAnalysis.log\n")
                        f.write("start\n")
                        f.write("start_filt\n")
                        f.write(str(self.params['hpfilt_imagic'])+"\n")
                        f.write("0\n")
                        f.write(str(self.params['lpfilt_imagic'])+"\n")
                        f.write("NO\n")
                        f.write("EOF\n")
                        f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF")
                        if  os.path.isfile("imagicMultivariateStatisticalAnalysis.log"):
                                f.write(" >> imagicMultivariateStatisticalAnalysis.log\n")
                        else:
                                f.write(" > imagicMultivariateStatisticalAnalysis.log\n")
                        f.write("start_filt\n")
                        f.write("start\n")
                        f.write("EOF\n")
                if self.params['mask_radius'] and self.params['mask_dropoff'] is not None:
                        f.write("/usr/local/IMAGIC/stand/arithm.e <<EOF")
                        if  os.path.isfile("imagicMultivariateStatisticalAnalysis.log"):
                                f.write(" >> imagicMultivariateStatisticalAnalysis.log\n")
                        else:
                                f.write(" > imagicMultivariateStatisticalAnalysis.log\n")
                        f.write("start\n")
                        f.write("start_masked\n")
                        f.write("SOFT\n")
                        f.write(str(self.params['mask_radius'])+"\n")
                        f.write(str(self.params['mask_dropoff'])+"\n")
                        f.write("EOF\n")
                        f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagicMultivariateStatisticalAnalysis.log\n")
                        f.write("start_masked\n")
                        f.write("start\n")
                        f.write("EOF\n")
                f.write("/usr/local/IMAGIC/stand/testim.e <<EOF")
                if  os.path.isfile("imagicMultivariateStatisticalAnalysis.log"):
                        f.write(" >> imagicMultivariateStatisticalAnalysis.log\n")
                else:
                        f.write(" > imagicMultivariateStatisticalAnalysis.log\n")
                f.write("msamask\n")
                f.write(str(self.params['boxsize'])+","+str(self.params['boxsize'])+"\n")
                f.write("REAL\n")
                f.write("DISC\n")
                f.write(str(self.params['mask_radius'])+"\n")
                f.write("EOF\n")
                f.write("/usr/local/IMAGIC/msa/msa.e <<EOF >> imagicMultivariateStatisticalAnalysis.log\n")
                f.write("FRESH_MSA\n")
                f.write(str(self.params['MSAmethod'])+"\n")
                f.write("start\n")
                f.write("NO\n")
                f.write("msamask\n")
                f.write("eigenimages\n")
                f.write("pixcoos\n")
                f.write("eigenpixels\n")
                f.write(str(self.params['numiters'])+"\n")
                f.write("69\n")
                f.write(str(self.params['overcorrection'])+"\n")
                f.write("my_msa\n")
                f.write("EOF\n")
                f.close()
		
		return filename	

	#=========================
	def insertAnalysis(self, imagicstack, insert=False):
		### create MSAParam object
		msaq = appionData.ApImagicAlignAnalysisData()
		msaq['runname'] = self.params['runname']
                msaq['bin'] = self.params['bin']
                msaq['hp_filt'] = self.params['hpfilt']
                msaq['lp_filt'] = self.params['lpfilt']
		msaq['mask_radius'] = self.params['mask_radius']
		msaq['mask_dropoff'] = self.params['mask_dropoff']
		msaq['numiters'] = self.params['numiters']
		msaq['overcorrection'] = self.params['overcorrection']
		msaq['MSAmethod'] = self.params['MSAmethod']
		msaq['eigenimages'] = "eigenimages"

		### finish analysis run
		analysisrunq = appionData.ApAlignAnalysisData()
		analysisrunq['runname'] = self.params['runname']
		analysisrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		analysisrunq['imagicMSArun'] = msaq
		analysisrunq['alignstack'] = self.alignstackdata
		analysisrunq['hidden'] = False
                analysisrunq['description'] = self.params['description']
                analysisrunq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['alignid'])

		apDisplay.printMsg("inserting Align Analysis Run parameters into database")
		if insert is True:
			analysisrunq.insert()

		return 

	#=====================
	def start(self):
		t0 = time.time()
		
		self.checkAnalysisRun()
		
		# get stack parameters
		if self.params['alignid'] is not None:
                        self.alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignid'])
			stackpixelsize = self.alignstackdata['pixelsize']
			stack_box_size = self.alignstackdata['boxsize']
			self.params['boxsize'] = stack_box_size / int(self.params['bin'])
			self.params['apix'] = stackpixelsize * int(self.params['bin'])
			orig_path = self.alignstackdata['path']['path']
			orig_file = self.alignstackdata['imagicfile']
			linkingfile = orig_path+"/"+orig_file
			linkingfile = linkingfile.replace(".hed", "")
		else:
			apDisplay.printError("stack not in the database")
		
		# copy stack file to working directory	
                if not os.path.isfile(linkingfile+".hed"):
                        apDisplay.printError("stackfile does not exist: "+linkingfile+".img")
                else:
			apDisplay.printMsg("copying aligned stack into working directory for operations with IMAGIC")
                        shutil.copyfile(linkingfile+".img", str(self.params['rundir'])+"/start.img")
                        shutil.copyfile(linkingfile+".hed", str(self.params['rundir'])+"/start.hed")
	
		### NEED TO CONVERT FILTERING PARAMETERS TO IMAGIC FORMAT BETWEEN 0-1
                if self.params['lpfilt'] is not None:
			self.params['lpfilt_imagic'] = 2 * float(self.params['apix']) / int(self.params['lpfilt'])
		else:
			self.params['lpfilt_imagic'] = False
                if float(self.params['lpfilt_imagic']) > 1:
                        self.params['lpfilt_imagic'] = 1	# imagic cannot perform job when lowpass > 1
                if self.params['hpfilt'] is not None:
			self.params['hpfilt_imagic'] = 2 * float(self.params['apix']) / int(self.params['hpfilt'])
		else:
			self.params['hpfilt_imagic'] = False

		print self.params
		print "... aligned stack pixel size: "+str(self.params['apix'])
		print "... aligned stack box size: "+str(self.params['boxsize'])	
		apDisplay.printColor("Running IMAGIC .batch file: See imagicMultivariateStatisticalAnalysis.log for details", "cyan")
	
		### create imagic batch file
		filename = self.createImagicBatchFile()
		### execute batch file that was created
		aligntime = time.time()
		os.system('chmod 755 '+filename)
		apIMAGIC.executeImagicBatchFile(filename)
		apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-aligntime), "cyan")
		aligntime = time.time() - aligntime
	
		### upload alignment
		imagicstack = os.path.join(self.params['rundir'], "start.hed")
                inserttime = time.time()
                if self.params['commit'] is True:
                        self.insertAlignment(imagicstack, insert=True)
                else:
                        apDisplay.printWarning("not committing results to DB")
                inserttime = time.time() - inserttime

                apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))
                apDisplay.printMsg("Database Insertion time: "+apDisplay.timeString(inserttime))

	
	
	
#=====================
#=====================
if __name__ == '__main__':
	imagicMSA = imagicMultivariateStatisticalAnalysisScript()
	imagicMSA.start()
	imagicMSA.close()

	
