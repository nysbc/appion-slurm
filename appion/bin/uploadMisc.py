#!/usr/bin/env python


import sys
import os
import shutil
import appionScript
import apDatabase
import apRecon
import apParam
import apDisplay
import appionData
import apFile
import apProject

#=====================
#=====================
class UploadMiscScript(appionScript.AppionScript):
	#==================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --file=<filename> --session=<name> --recon=<#> \n\t "
			+" --description='text' ")
		self.parser.add_option("-f", "--file", dest="file", 
			help="File to upload", metavar="FILE")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with file (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("-r", "--reconid", dest="reconid", type='int',
			help="ReconID associated with file (e.g. --reconid=311)", metavar="RECONID")

	#=====================
	def checkConflicts(self):
		# make sure the necessary parameters are set
		if self.params['file'] is None:
			apDisplay.printError("no file was specified")
		self.oldfile = os.path.abspath(self.params['file'])
		if not os.path.isfile(self.oldfile):
			apDisplay.printError("file does not exist")
		if self.params['description'] is None:
			apDisplay.printError("enter a file description")
		if self.params['session'] is None and self.params['reconid'] is None:
			apDisplay.printError("please enter either session or reconID")

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "misc"

	#=====================
	def insertMisc(self):
		print "inserting into database"
		miscq = appionData.ApMiscData()
		if self.params['reconid'] is not None:
			miscq['refinementRun'] = self.recondata
			sessiondata = apRecon.getSessionDataFromReconId(self.params['reconid'])
			miscq['session'] = sessiondata
			projectid = apProject.getProjectIdFromSessionName(sessiondata['name'])
			miscq['project|projects|project'] = projectid
		elif self.params['session'] is not None:
			miscq['session'] = self.sessiondata
			projectid = apProject.getProjectIdFromSessionName(self.params['session'])
			miscq['project|projects|project'] = projectid
		miscq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		miscq['name'] = self.filename
		miscq['description'] = self.params['description']
		miscq['md5sum'] = apFile.md5sumfile(self.newfile)
		miscq['hidden'] = False

		if self.params['commit'] is True:
			miscq.insert()
		else:
			apDisplay.printWarning("not committing to DB")
	

	#=====================
	def start(self):

		if self.params['reconid'] is not None:
			self.recondata = apRecon.getRefineRunDataFromID(self.params['reconid'])
			print "Associated with",self.recondata['name'],":",self.recondata['path']
		if self.params['session'] is not None:
			self.sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
			self.params['projectId'] = apProject.getProjectIdFromSessionName(self.params['session'])

		self.filename = os.path.basename(self.params['file'])
		self.newfile = os.path.join(self.params['rundir'], self.filename)
		if os.path.isfile(self.newfile):
			apDisplay.printError("File "+self.filename+" already exists in dir "+self.params['rundir'])
		shutil.copy(self.oldfile, self.newfile)

		# insert the info
		self.insertMisc()	


#=====================
#=====================
if __name__ == '__main__':
	uploadMisc = UploadMiscScript()
	uploadMisc.start()
	uploadMisc.close()




