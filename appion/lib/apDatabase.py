#Part of the new pyappion

#pythonlib
import sys
import os
import time
import math
import shutil
#leginon
import data
#appion
import apDB
import apLoop
import apDisplay


data.holdImages(False)
db = apDB.db
#db     = dbdatakeeper.DBDataKeeper()
#partdb = dbdatakeeper.DBDataKeeper(db='dbparticledata')
#acedb  = dbdatakeeper.DBDataKeeper(db='dbctfdata')
#projdb = dbdatakeeper.DBDataKeeper(db='project')

def getAllImages(stats,params):
	startt = time.time()
	if 'dbimages' in params and params['dbimages']==True:
		imgtree = getImagesFromDB(params['sessionname'],params['preset'])
	elif 'alldbimages' in params and  params['alldbimages']==True:
		imgtree = getAllImagesFromDB(params['sessionname'])
	elif 'mrcfileroot' in params and len(params['mrcfileroot']) > 0:
		imgtree = getSpecificImagesFromDB(params["mrcfileroot"])
		params['sessionname']=imgtree[0]['session']['name']
	else:
		print len(params['mrcfileroot']),params['alldbimages'],params['dbimages'],params['mrcfileroot']
		apDisplay.printError("no files specified")
	params['session']=imgtree[0]['session']
	stats['imagecount']=len(imgtree)
	print " ... found",stats['imagecount'],"in",apDisplay.timeString(time.time()-startt)
	return imgtree

def getSpecificImagesFromDB(imglist):
	print "Querying database for "+str(len(imglist))+" specific images ... "
	imgtree=[]
	for imgname in imglist:
		imgquery = data.AcquisitionImageData(filename=imgname)
		imgres   = db.query(imgquery, readimages=False, results=1)
		imgtree.append(imgres[0])
	return imgtree

def getImagesFromDB(session,preset):
	"""
	returns list of image names from DB
	"""
	apDisplay.printMsg("Querying database for preset '"+preset+"' images from session '"+session+"' ... ")
	sessionq = data.SessionData(name=session)
	presetq=data.PresetData(name=preset)
	imgquery = data.AcquisitionImageData()
	imgquery['preset']  = presetq
	imgquery['session'] = sessionq
	imgtree = db.query(imgquery, readimages=False)
	"""
	loop through images and make data.holdimages false 	 
	this makes it so that data.py doesn't hold images in memory 	 
	solves a bug where processing quits after a dozen or so images
	"""
	#for img in imgtree: 	 
		#img.holdimages=False
	return imgtree

def getAllImagesFromDB(session):
	"""
	returns list of image data based on session name
	"""
	apDisplay.printMsg("Querying database for all images from session '"+session+"' ... ")
	sessionq= data.SessionData(name=session)
	imgquery = data.AcquisitionImageData()
	imgquery['session'] = sessionq
	imgtree = db.query(imageq, readimages=False)
	return imgtree

def getDBTemplates(params):
	tmptmplt=params['template']
	i=1
	for tid in params['templateIds']:
		# find templateImage row
		tmpltinfo = apDB.apdb.direct_query(data.ApTemplateImageData, tid)
		if not (tmpltinfo):
			apDisplay.printError("TemplateId "+str(tid)+" not found in database. Use 'uploadTemplate.py'\n")
		apix = tmpltinfo['apix']
		# store row data in params dictionary
		params['ogTmpltInfo'].append(tmpltinfo)

		# copy file to current directory
		origtmplpath = os.path.join(tmpltinfo['templatepath'], tmpltinfo['templatename'])
		if os.path.isfile(origtmplpath):
			print "getting image:", origtmplpath
			newtmplpath = os.path.join(params['rundir'],tmptmplt+str(i)+".mrc")
			shutil.copy(origtmplpath, newtmplpath)
		else:
			apDisplay.printError("Template file not found: "+origtmplpath)
		params['scaledapix'][i] = 0
		i+=1
	return

def getImageData(imgname):
	"""
	get image data object from database
	"""
	imgquery = data.AcquisitionImageData(filename=imgname)
	imgtree  = db.query(imgquery, results=1, readimages=False)
	if imgtree:
		#imgtree[0].holdimages=False
		return imgtree[0]
	else:
		apDisplay.printError("Image "+imgname+" not found in database\n")

def getImgDir(sessionname):
	sessionq = data.SessionData(name=sessionname)
	sessiondata = db.query(sessionq)
	imgdir = os.path.abspath(sessiondata[0]['image path'])
	return imgdir

def getSessionName(imgname):
	"""
	get session name from database
	"""
	imgquery = data.AcquisitionImageData(filename=imgname)
	imgtree  = db.query(imgquery, results=1, readimages=False)
	if 'session' in imgtree[0]:
		return imgtree[0]['session']['name']
	else:
		apDisplay.printError("Image "+imgname+" not found in database\n")

def getTiltAngle(img,params):
	return img['scope']['stage position']['a']*180.0/math.pi

def getPixelSize(imgdict):
	"""
	use image data object to get pixel size
	multiplies by binning and also by 1e10 to return image pixel size in angstroms
	shouldn't have to lookup db already should exist in imgdict
	"""
	pixelsizeq=data.PixelSizeCalibrationData()
	pixelsizeq['magnification']=imgdict['scope']['magnification']
	pixelsizeq['tem']=imgdict['scope']['tem']
	pixelsizeq['ccdcamera'] = imgdict['camera']['ccdcamera']
	pixelsizedata=db.query(pixelsizeq, results=1)
	binning=imgdict['camera']['binning']['x']
	pixelsize=pixelsizedata[0]['pixelsize'] * binning
	return(pixelsize*1e10)

def getImgSize(img):
	if 'image' in img:
		return (img['image'].shape)[1]
	fname = img['filename']
	# get image size (in pixels) of the given mrc file
	imageq=data.AcquisitionImageData(filename=fname)
	imagedata=db.query(imageq, results=1, readimages=False)
	if imagedata:
		size=int(imagedata[0]['camera']['dimension']['y'])
		return(size)
	else:
		apDisplay.printError("Image "+fname+" not found in database\n")
	return(size)
