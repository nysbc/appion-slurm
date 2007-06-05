#Defocus pair functions

import numarray
#leginon
import peakfinder
import data
import correlator
#appion
import appionData
import apDB
import apImage
import apDisplay

leginondb = apDB.db
appiondb  = apDB.apdb

def getShiftFromImage(imgdata, params):
	sibling = getDefocusPair(imgdata)
	if sibling:
		shiftpeak = getShift(imgdata, sibling)
		recordShift(params, imgdata, sibling, shiftpeak)
	return sibling, shiftpeak

def getDefocusPair(imgdata):
	target=imgdata['target']
	qtarget=data.AcquisitionImageTargetData()
	qtarget['image'] = target['image']
	qtarget['number'] = target['number']
	qsibling=data.AcquisitionImageData(target=qtarget)
	origid=imgdata.dbid
	allsiblings = leginondb.query(qsibling, readimages=False)	
	if len(allsiblings) > 1:
		#could be multiple siblings but we are taking only the most recent
		for sib in allsiblings:
			if sib.dbid == origid:
				pass
			else:
				defocpair=sib
				break
	else:
		defocpair=None
	return defocpair

def getShift(imgdata1 ,imgdata2):
	#assumes images are square
	print "Finding shift between", apDisplay.short(imgdata1['filename']), "and", apDisplay.short(imgdata2['filename'])
	dimension1 = imgdata1['camera']['dimension']['x']
	binning1   = imgdata1['camera']['binning']['x']
	dimension2 = imgdata2['camera']['dimension']['x']
	binning2   = imgdata2['camera']['binning']['x']
	finalsize=512
	#test to make sure images are at same mag
	if imgdata1['scope']['magnification'] != imgdata2['scope']['magnification']:
		apDisplay.printWarning("Defocus pairs are at different magnifications, so shift can't be calculated.")
		peak=None
	#test to see if images capture the same area
	elif (dimension1 * binning1) != (dimension2 * binning2):
		apDisplay.printWarning("Defocus pairs do not capture the same imaging area, so shift can't be calculated.")
		peak=None
	#images must not be less than finalsize (currently 512) pixels. This is arbitrary but for good reason
	elif dimension1 < finalsize or dimension2 < finalsize:
		apDisplay.printWarning("Images must be greater than "+finalsize+" pixels to calculate shift.")
		peak=None
	else:
		shrinkfactor1=dimension1/finalsize
		shrinkfactor2=dimension2/finalsize
		binned1 = apImage.binImg(imgdata1['image'], shrinkfactor1)
		binned2 = apImage.binImg(imgdata2['image'], shrinkfactor2)
		pc=correlator.phase_correlate(binned1,binned2,zero=True)
		peak = peakfinder.findSubpixelPeak(pc, lpf=1.5) # this is a temp fix. 
		subpixpeak = peak['subpixel peak']
		shift=correlator.wrap_coord(subpixpeak,pc.shape)
		peak['scalefactor']=dimension2/float(dimension1)
		peak['shift']= numarray.array((shift[0]*shrinkfactor1, shift[1]*shrinkfactor1))
	return peak

def recordShift(params,img,sibling,peak):
	filename=params['session']['name']+'.shift.txt'
	f=open(filename,'a')
	f.write('%s\t%s\t%f\t%f\t%f\t%f\n' % (img['filename'],sibling['filename'],peak['shift'][1],peak['shift'][0],peak['scalefactor'],peak['subpixel peak value']))
	f.close()
	return()

def insertShift(img,sibling,peak):
	shiftq=appionData.ApImageTransformationData()
	shiftq['dbemdata|AcquisitionImageData|image1']=img.dbid
	shiftdata=appiondb.query(shiftq)
	if shiftdata:
		print "Warning: Shift values already in database"
	else:
		shiftq['dbemdata|AcquisitionImageData|image2']=sibling.dbid
		shiftq['shiftx']=peak['shift'][1]
		shiftq['shifty']=peak['shift'][0]
		shiftq['scale']=peak['scalefactor']
		shiftq['correlation']=peak['subpixel peak value']
		print 'Inserting shift beteween', img['filename'], 'and', sibling['filename'], 'into database'
		appiondb.insert(shiftq)
	return()
