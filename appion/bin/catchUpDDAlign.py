#!/usr/bin/env python

#pythonlib
import os
import shutil
import subprocess
import time
#leginon
from leginon import leginondata
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apDDprocess
from appionlib import apFile
from appionlib import appiondata

class CatchUpFrameAlignmentLoop(appionScript.AppionScript):
	#=======================
	def setupParserOptions(self):
		self.parser.add_option("--ddstackid", dest="ddstackid", type="int",
			help="ID for dd frame stack run", metavar="INT")
		self.parser.add_option("--no-wait", dest="wait", default=True,
			action="store_false", help="Do not wait for frame stack to finish creation")

	#=======================
	def checkConflicts(self):
		# make sure program exist
		exename = 'dosefgpu_driftcorr'
		driftcorrexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(driftcorrexe):
			apDisplay.printError('Drift correction program not available')
		# make sure ddstack exists
		ddstackrun = appiondata.ApDDStackRunData().direct_query(self.params['ddstackid'])
		if ddstackrun:
			apDisplay.printMsg('Found dd frame stack run')
			# set self.rundata in this function because we may need it if rundir is not set in params
			self.rundata = ddstackrun
		else:
			apDisplay.printError('DD Frame Stack id %d does not exist' % self.params['ddstackid'])
		if not self.rundata['params']['align']:
			apDisplay.printError('DD Frame Stack id %d was not meant to be aligned' % self.params['ddstackid'])

	#=====================
	def setRunDir(self):
		self.params['rundir'] = self.rundata['path']['path']

	#=======================
	def onInit(self):
		if 'sessionname' not in self.params.keys():
			self.params['sessionname'] = leginondata.SessionData().direct_query(self.params['expid'])['name']
		self.dd = apDDprocess.initializeDDprocess(self.params['sessionname'],self.params['wait'])
		self.dd.setRunDir(self.params['rundir'])
		self.dd.setNewBinning(self.rundata['params']['bin'])
		self.has_new_image = False

	def hasDDAlignedImagePair(self, imgdata):
		q = appiondata.ApDDAlignImagePairData(source=imgdata,ddstackrun=self.rundata)
		return len(q.query()) > 0

	#=======================
	def processImage(self, imgdata):
		# initialize aligned_imagedata as if not aligned
		self.aligned_imagedata = None
		# need to avoid non-frame saved image for proper caching
		if imgdata is None or imgdata['camera']['save frames'] != True:
			apDisplay.printWarning('%s skipped for no-frame-saved\n ' % imgdata['filename'])
			return
		if self.hasDDAlignedImagePair(imgdata):
			apDisplay.printWarning('aligned image %d from this run is already in the database. Skipped....' % imgdata.dbid)
			return

		self.has_new_image = True
		### set processing image
		try:
			self.dd.setImageData(imgdata)
		except Exception, e:
			apDisplay.printWarning(e.message)
			return

		if not self.dd.isReadyForAlignment():
			apDisplay.printWarning('unaligned frame stack not created. Skipped....')
			return

		self.dd.setAlignedCameraEMData()
		self.dd.alignCorrectedFrameStack()
		if os.path.isfile(self.dd.aligned_stackpath):
			self.aligned_imagedata = self.dd.makeAlignedImageData()
			apDisplay.printMsg(' Replacing unaligned stack with the aligned one....')
			apFile.removeFile(self.dd.framestackpath)
			shutil.move(self.dd.aligned_stackpath,self.dd.framestackpath)

	def commitToDatabase(self, imgdata):
		if self.aligned_imagedata != None:
			apDisplay.printMsg('Uploading aligned image as %s' % self.aligned_imagedata['filename'])
			q = appiondata.ApDDAlignImagePairData(source=imgdata,result=self.aligned_imagedata,ddstackrun=self.rundata)
			q.insert()

	def loopCheckAndProcess(self):
		allfiles = os.listdir(os.getcwd())
		images = []
		for filename in allfiles:
			if os.path.isfile(filename) and '_st.mrc' in filename:
				imagedata = leginondata.AcquisitionImageData(session=self.rundata['session'],filename=filename[:-7]).query()[0]
				images.append(imagedata)
		self.num_stacks = len(images)
		for imagedata in images:
			apDisplay.printMsg('---------------------------------------------------------')
			apDisplay.printMsg('  Processing %s' % imagedata['filename'])
			apDisplay.printMsg('---------------------------------------------------------')
			self.processImage(imagedata)
			if self.params['commit']:
				self.commitToDatabase(imagedata)
			apDisplay.printMsg('\n')

	def start(self):
		print 'wait=',self.params['wait']
		max_loop_num_trials = 3
		wait_time = 20
		self.last_num_stacks = 0
		if self.params['wait']:
			num_trials = 0
			while True:
				self.loopCheckAndProcess()
				if self.num_stacks == self.last_num_stacks:
					if num_trials >= max_loop_num_trials:
						apDisplay.printColor('Checked for stack file %d times. Finishing....' % max_loop_num_trials,'magenta')
						apDisplay.printMsg('Rerun this script if you know more are coming')
						break
					else:
						num_trials += 1
				else:
					# reset trial number if new stack is found
					num_trials = 0
				apDisplay.printColor('Finished stack file checking in rundir. Will check again in %d seconds' % wait_time,'magenta')
				time.sleep(wait_time)
				self.last_num_stacks = self.num_stacks
		else:				
			self.loopCheckAndProcess()

if __name__ == '__main__':
	makeStack = CatchUpFrameAlignmentLoop()
	makeStack.start()


