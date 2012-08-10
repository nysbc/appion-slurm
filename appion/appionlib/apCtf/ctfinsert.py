#Part of the new pyappion

#pythonlib
import os
import re
import sys
import math
import shutil
#appion
from appionlib import apFile
from appionlib import apDisplay
from appionlib import appiondata
from appionlib.apCtf import ctfdisplay

debug = False

#====================
#====================
def validateAndInsertCTFData(imgdata, ctfvalues, rundata, rundir):
	"""
	function to insert CTF values in database
	"""
	apDisplay.printMsg("Committing ctf parameters for "
		+apDisplay.short(imgdata['filename'])+" to database")

	if ctfvalues is None or not 'defocus2' in ctfvalues:
		apDisplay.printWarning("No ctf values")
		return False

	### convert to common convention
	ctfvalues = convertDefociToConvention(ctfvalues)

	### check to make sure parameters are valid
	isvalid = checkParams(ctfvalues)
	if isvalid is False:
		apDisplay.printWarning("Bad CTF values NOT committing to database")
		return False

	### run the main CTF display program
	opimagedir = os.path.join(rundir, "opimages")
	ctfvalues = runCTFdisplayTools(imgdata, ctfvalues, opimagedir)

	### clean rundir from all entries:
	if not rundir.endswith("/"):
		rundir += "/"
	for key in ctfvalues.keys():
		if isinstance(ctfvalues[key], str) and ctfvalues[key].startswith(rundir):
			ctfvalues[key] = ctfvalues[key].replace(rundir, "")

	### time to insert
	ctfq = appiondata.ApCtfData()
	ctfq['acerun'] = rundata
	ctfq['image'] = imgdata
	if debug is True:
		apDisplay.printMsg("CTF data values")
	for key in ctfq.keys():
		if key in ctfvalues:
			ctfq[key] = ctfvalues[key]
			if debug is True:
				apDisplay.printMsg("%s :: %s"%(key, ctfvalues[key]))
	ctfq.insert()

	return

#====================
#====================
def runCTFdisplayTools(imgdata, ctfvalues, opimagedir):
	### RUN CTF DISPLAY TOOLS
	ctfdisplaydict = ctfdisplay.makeCtfImages(imgdata, ctfvalues)
	if ctfdisplaydict is None:
		return ctfvalues
	### save the classic images as well
	if 'graph1' in ctfvalues:
		ctfvalues['graph3'] = ctfvalues['graph1']
	if 'graph2' in ctfvalues:
		ctfvalues['graph4'] = ctfvalues['graph2']
	### new powerspec file
	psfile = os.path.join(opimagedir, ctfdisplaydict['powerspecfile'])
	shutil.move(ctfdisplaydict['powerspecfile'], psfile)
	ctfvalues['graph1'] = psfile
	### new 1d plot file
	plotfile = os.path.join(opimagedir, ctfdisplaydict['plotsfile'])
	shutil.move(ctfdisplaydict['plotsfile'], plotfile)
	ctfvalues['graph2'] = plotfile
	ctfvalues['confidence_30_10'] = ctfdisplaydict['conf3010']
	ctfvalues['confidence_5_peak'] = ctfdisplaydict['conf5peak']
	ctfvalues['resolution_80_percent'] = ctfdisplaydict['res80']
	ctfvalues['resolution_50_percent'] = ctfdisplaydict['res50']
	if not 'confidence' in ctfvalues or ctfvalues['confidence'] is None:
		ctfvalues['confidence'] = ctfdisplaydict['conf3010']
	if not 'confidence_d' in ctfvalues or ctfvalues['confidence_d'] is None:
		ctfvalues['confidence_d'] = ctfdisplaydict['conf5peak']
	return ctfvalues

#====================
#====================
def convertDefociToConvention(ctfvalues):
	if debug is True:
		apDisplay.printColor("Final params: def1: %.2e | def2: %.2e | angle: %.1f"%
			(ctfvalues['defocus1'], ctfvalues['defocus2'], ctfvalues['angle_astigmatism']), "cyan")

	# program specific corrections?
	angle = ctfvalues['angle_astigmatism']

	#by convention: abs(ctfvalues['defocus1']) < abs(ctfvalues['defocus2'])
	if abs(ctfvalues['defocus1']) > abs(ctfvalues['defocus2']):
		# incorrect, need to shift angle by 90 degrees
		apDisplay.printWarning("|def1| > |def2|, flipping defocus axes")
		defocus1 = ctfvalues['defocus2']
		defocus2 = ctfvalues['defocus1']
		angle += 90
	else:
		# correct, ratio > 1
		defocus1 = ctfvalues['defocus1']
		defocus2 = ctfvalues['defocus2']
	if defocus1 < 0 and defocus2 < 0:
		apDisplay.printWarning("Negative defocus values, taking absolute value")
		defocus1 = abs(defocus1)
		defocus2 = abs(defocus2)

	# get angle within range -90 < angle <= 90
	while angle > 90:
		angle -= 180
	while angle < -90:
		angle += 180

	if debug is True:
		apDisplay.printColor("Final params: def1: %.2e | def2: %.2e | angle: %.1f"%
			(defocus1, defocus2, angle), "cyan")

		perdiff = abs(defocus1-defocus2)/abs(defocus1+defocus2)
		print ("Defocus Astig Percent Diff %.2f -- %.3e, %.3e"
				%(perdiff*100,defocus1,defocus2))

	ctfvalues['defocus1'] = defocus1
	ctfvalues['defocus2'] = defocus2
	ctfvalues['angle_astigmatism'] = angle

	return ctfvalues

#====================
#====================
def checkParams(ctfvalues):
	"""
	check to see if CTF values exist and are in an appropriate range
	"""
	### set values as local variables
	focus1 = ctfvalues['defocus1']
	focus2 = ctfvalues['defocus2']
	cs = ctfvalues['cs']
	volts = ctfvalues['volts']
	ampcontrast = ctfvalues['amplitude_contrast']
	### print debug
	if debug is True:
		print "  Defocus1 %.2f microns (underfocus is positive)"%(focus1*1e6)
		if focus1 != focus2:
			print "  Defocus2 %.2f microns (underfocus is positive)"%(focus2*1e6)
		print "  C_s %.1f mm"%(cs)
		print "  High tension %.1f kV"%(volts*1e-3)
		print ("  Amp Contrast %.3f (shift %.1f degrees)"
			%(ampcontrast, math.degrees(-math.asin(ampcontrast))))
	### various test of data
	if focus1*1e6 > 25.0 or focus1*1e6 < 0.01:
		msg = "atypical defocus #1 value %.4f microns (underfocus is positve)"%(focus1*1e6)
		apDisplay.printWarning(msg)
		return False
	if focus2*1e6 > 25.0 or focus2*1e6 < 0.01:
		msg = "atypical defocus #2 value %.4f microns (underfocus is positve)"%(focus2*1e6)
		apDisplay.printWarning(msg)
		return False
	if cs > 9.0 or cs < 0.7:
		msg = "atypical C_s value %.4f mm"%(cs)
		apDisplay.printWarning(msg)
		return False
	if volts*1e-3 > 400.0 or volts*1e-3 < 60:
		msg = "atypical high tension value %.4f kiloVolts"%(volts*1e-3)
		apDisplay.printWarning(msg)
		return False
	if ampcontrast < 0.0 or ampcontrast > 0.5:
		msg = "atypical amplitude contrast value %.4f"%(ampcontrast)
		apDisplay.printWarning(msg)
		return False
	### passed all test, return True
	return True