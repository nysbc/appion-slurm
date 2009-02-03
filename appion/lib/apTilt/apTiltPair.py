#python
import re
import numpy
import time
import math
#leginon
import leginondata
#appion
import appionData
import apImage
import apDisplay
import apStack
import apDatabase
import apTiltTransform
import sinedon
import MySQLdb

"""
Denis's query
$q="select "
	."a2.DEF_id, a2.`MRC|image` as filename "
	."from AcquisitionImageData a1 "
	."left join AcquisitionImageData a2 "
	."on (a1.`REF|TiltSeriesData|tilt series`=a2.`REF|TiltSeriesData|tilt series` "
	."and a1.`REF|PresetData|preset`=a2.`REF|PresetData|preset` "
	."and a1.DEF_id<>a2.DEF_id) "
	."where a1.DEF_id=$imageId";
"""

"""
	sessionq = leginondata.SessionData(name=session)
	presetq=leginondata.PresetData(name=preset)
	imgquery = leginondata.AcquisitionImageData()
	imgquery['preset']  = presetq
	imgquery['session'] = sessionq
	imgtree = imgquery.query(readimages=False)
"""

#===============================
def getTiltPair(imgdata):
	imageq  = leginondata.AcquisitionImageData()
	imageq['tilt series'] = imgdata['tilt series']
	if imgdata['preset'] is None:
		return None
	presetq = leginondata.PresetData()
	presetq['name'] = imgdata['preset']['name']
	imageq['preset'] = presetq
	#if beam changed between tilting, presets would be different
	origid=imgdata.dbid
	alltilts = imageq.query(readimages=False)
	tiltpair = None
	if len(alltilts) > 1:
		#could be multiple tiltpairs but we are taking only the most recent
		for tilt in alltilts:
			if tilt.dbid != origid:
				tiltpair = tilt
				break
	return tiltpair

#===============================
def tiltPickerToDbNames(tiltparams):
	#('image1', leginondata.AcquisitionImageData),
	#('image2', leginondata.AcquisitionImageData),
	#('shiftx', float),
	#('shifty', float),
	#('correlation', float),
	#('scale', float),
	#('tilt', float),
	#('image1_rotation', float),
	#('image2_rotation', float),
	#('rmsd', float),
	newdict = {}
	if 'theta' in tiltparams:
		newdict['tilt_angle'] = tiltparams['theta']
	if 'gamma' in tiltparams:
		newdict['image1_rotation'] = tiltparams['gamma']
	if 'phi' in tiltparams:
		newdict['image2_rotation'] = tiltparams['phi']
	if 'rmsd' in tiltparams:
		newdict['rmsd'] = tiltparams['rmsd']
	if 'scale' in tiltparams:
		newdict['scale_factor'] = tiltparams['scale']
	if 'point1' in tiltparams:
		newdict['image1_x'] = tiltparams['point1'][0]
		newdict['image1_y'] = tiltparams['point1'][1]
	if 'point2' in tiltparams:
		newdict['image2_x'] = tiltparams['point2'][0]
		newdict['image2_y'] = tiltparams['point2'][1]
	if 'overlap' in tiltparams:
		newdict['overlap'] = tiltparams['overlap']
	return newdict

#===============================
def insertTiltTransform(imgdata1, imgdata2, tiltparams, params):
	#First we need to sort imgdata
	#'07aug30b_a_00013gr_00010sq_v01_00002sq_v01_00016en_00'
	#'07aug30b_a_00013gr_00010sq_v01_00002sq_01_00016en_01'
	#last two digits confer order, but then the transform changes...
	bin = params['bin']

	### first find the runid
	runq = appionData.ApSelectionRunData()
	runq['name'] = params['runname']
	runq['session'] = imgdata1['session']
	rundatas = runq.query(results=1)
	if not rundatas:
		apDisplay.printError("could not find runid in database")

	### the order is specified by 1,2; so don't change it let makestack figure it out
	for imgdata in (imgdata1, imgdata2):
		for index in ("1","2"):
			transq = appionData.ApImageTiltTransformData()
			transq["image"+index] = imgdata
			transq['tiltrun'] = rundatas[0]
			transdata = transq.query()
			if transdata:
				apDisplay.printWarning("Transform values already in database for "+imgdata['filename'])
				return transdata[0]

	### prepare the insertion
	transq = appionData.ApImageTiltTransformData()
	transq['image1'] = imgdata1
	transq['image2'] = imgdata2
	transq['tiltrun'] = rundatas[0]
	dbdict = tiltPickerToDbNames(tiltparams)
	if dbdict is None:
		return None
	#Can I do for key in appionData.ApImageTiltTransformData() ro transq???
	for key in ('image1_x','image1_y','image1_rotation','image2_x','image2_y','image2_rotation','scale_factor','tilt_angle', 'overlap'):
		if key not in dbdict:
			apDisplay.printError("Key: "+key+" was not found in transformation data")

	for key,val in dbdict.items():
		#print key
		if re.match("image[12]_[xy]", key):
			transq[key] = round(val*bin,2)
		else:
			transq[key] = val
		#print i,v


	### this overlap is wrong because the images are binned by 'bin' and now we give it the full image
	"""
	imgShape1 = numpy.asarray(imgdata1['image'].shape, dtype=numpy.int8)/params['bin']
	image1 = numpy.ones(imgShape1)
	imgShape2 = numpy.asarray(imgdata2['image'].shape, dtype=numpy.int8)/params['bin']
	image2 = numpy.ones(imgShape2)
	bestOverlap, tiltOverlap = apTiltTransform.getOverlapPercent(image1, image2, tiltparams)
	print "image overlaps", bestOverlap, tiltOverlap
	transq['overlap'] = round(bestOverlap,5)
	"""

	apDisplay.printMsg("Inserting transform between "+apDisplay.short(imgdata1['filename'])+\
		" and "+apDisplay.short(imgdata2['filename'])+" into database")
	transq.insert()
	apDisplay.printMsg("done")
	return transq

#===============================
def getStackParticleTiltPair(stackid, partnum, tiltstackid=None):
	"""
	takes a stack id and particle number (1+) spider-style
	returns the stack particle number for the tilt pair
	"""
	#print stackid, partnum
	if tiltstackid is None:
		tiltstackid = stackid

	t0 = time.time()

	stackpartdata1 = apStack.getStackParticle(stackid, partnum)

	partdata = stackpartdata1['particle']

	#print partdata

	### figure out if its particle 1 or 2
	tiltpartq1 = appionData.ApTiltParticlePairData()
	tiltpartq1['particle1'] = partdata
	tiltpartdatas1 = tiltpartq1.query(results=1)

	tiltpartq2 = appionData.ApTiltParticlePairData()
	tiltpartq2['particle2'] = partdata
	tiltpartdatas2 = tiltpartq2.query(results=1)

	if not tiltpartdatas1 and tiltpartdatas2:
		#print "image1"
		otherpart = tiltpartdatas2[0]['particle1']
	elif tiltpartdatas1 and not tiltpartdatas2:
		#print "image2"
		otherpart = tiltpartdatas1[0]['particle2']
	else:
		print partdata
		print tiltpartdatas1
		print tiltpartdatas2
		apDisplay.printError("failed to get tilt pair data")

	### get tilt stack particle
	tiltstackdata = apStack.getOnlyStackData(tiltstackid, msg=False)
	stackpartq = appionData.ApStackParticlesData()
	stackpartq['stack'] = tiltstackdata
	stackpartq['particle'] = otherpart
	stackpartdatas2 = stackpartq.query(results=1)
	if not stackpartdatas2:
		#print otherpart.dbid
		#apDisplay.printError("particle "+str(partnum)+" has no tilt pair in stackid="+str(tiltstackid))
		return None
	stackpartdata = stackpartdatas2[0]

	#print partnum,"-->",stackpartnum
	if time.time()-t0 > 0.7:
		print "getStackParticleTiltPair1", apDisplay.timeString(time.time()-t0)
	return stackpartdata

#===============================
def getTiltTransformFromParticleId(partid):
	dbconf = sinedon.getConfig('appionData')
	db     = MySQLdb.connect(**dbconf)
	cursor = db.cursor()

	query = (
		"SELECT \n"
		+"  tiltpair.`REF|ApImageTiltTransformData|transform` AS transformid,  \n"
		+"  tiltpair.`REF|ApParticleData|particle1` AS part1,  \n"
		+"  tiltpair.`REF|ApParticleData|particle2` AS part2  \n"
		+"FROM `ApTiltParticlePairData` as tiltpair \n"
		+"WHERE "
		+"  tiltpair.`REF|ApParticleData|particle1` = "+str(partid)+" \n" 
		+"OR \n"
		+"  tiltpair.`REF|ApParticleData|particle2` = "+str(partid)+" \n" 
		+"LIMIT 1 \n"
	)
	t0 = time.time()
	cursor.execute(query)
	result = cursor.fetchone()
	if time.time()-t0 > 0.3:
		print partid, "trans query", apDisplay.timeString(time.time()-t0)
	if not result:
		apDisplay.printError("Transform data not found")
	if len(result) < 3:
		apDisplay.printError("Transform data not found")	
	#print partid, result
	transid = int(result[0])
	partid1 = int(result[1])
	partid2 = int(result[2])
	if partid1 == partid:
		imgnum = 1
		otherpartid = partid2
	elif  partid2 == partid:
		imgnum = 2
		otherpartid = partid1
	else:
		apDisplay.printError("Transform data not found")
	t0 = time.time()
	transformdata = appionData.ApImageTiltTransformData.direct_query(transid)
	if time.time()-t0 > 0.3:
		print partid, "data conversion", apDisplay.timeString(time.time()-t0)
	if not transformdata:
		apDisplay.printError("Transform data not found")
	return imgnum, transformdata, otherpartid


#===============================
def getParticleTiltRotationAngles(stackpartdata):
	partdata = stackpartdata['particle']
	partid = partdata.dbid
	imgnum, transformdata, otherpartid = getTiltTransformFromParticleId(partid)
	t0 = time.time()
	imgid1, imgid2 = getTransformImageIds(transformdata)
	if time.time()-t0 > 0.3:
		print partid, "db queries", apDisplay.timeString(time.time()-t0)
	tiltangle1 = getTiltAngleDeg(imgid1, 1)
	tiltangle2 = getTiltAngleDeg(imgid2, 2)
	if time.time()-t0 > 0.3:
		print partid, "angle queries", apDisplay.timeString(time.time()-t0)

	if imgnum == 1:
		tiltrot = transformdata['image1_rotation']
		theta = transformdata['tilt_angle']
		notrot   = transformdata['image2_rotation']
		tiltangle = tiltangle1 - tiltangle2
	elif imgnum == 2:
		tiltrot = transformdata['image2_rotation']
		theta = transformdata['tilt_angle']
		notrot   = transformdata['image1_rotation']
		tiltangle = tiltangle2 - tiltangle1
	else:
		#no particle pair info was found
		print partdata
		apDisplay.printError("failed to get tilt pair data")

	if tiltangle < 0:
		#swap angles
		return notrot, -1.0*theta, tiltrot, -1.0*tiltangle
	return tiltrot, theta, notrot, tiltangle


#===============================
def getTiltAngleDeg(imgid, imgnum):
	t0 = time.time()
	#return imgdata['scope']['stage position']['a']*180.0/math.pi
	dbconf = sinedon.getConfig('leginondata')
	db     = MySQLdb.connect(**dbconf)
	cursor = db.cursor()
	query = (
		"SELECT \n"
		+"  scope.`SUBD|stage position|a` AS angle  \n"
		+"FROM `AcquisitionImageData` as img \n"
		+"LEFT JOIN ScopeEMData AS scope \n"
		+"  ON scope.`DEF_id` = img.`REF|ScopeEMData|scope` \n" 
		+"WHERE \n"
		+"  img.`DEF_id` = "+str(imgid)+" \n" 
		+"LIMIT 1 \n"
	)
	cursor.execute(query)
	#results = sinedon.directq.complexMysqlQuery('leginondata',q)
	result = cursor.fetchone()
	radians = float(result[0])
	degrees = radians*180.0/math.pi
	if time.time()-t0 > 0.3:
		print query
		print imgnum, partid, "angle query", apDisplay.timeString(time.time()-t0)
	return degrees


#===============================
def getTransformImageIds2(transformid):
	t0 = time.time()
	#return imgdata['scope']['stage position']['a']*180.0/math.pi
	dbconf = sinedon.getConfig('appionData')
	db     = MySQLdb.connect(**dbconf)
	cursor = db.cursor()
	query = (
		"SELECT \n"
		+"  trans.`REF|leginondata|AcquisitionImageData|image1` AS img1,  \n"
		+"  trans.`REF|leginondata|AcquisitionImageData|image2` AS img2  \n"
		+"FROM `ApImageTiltTransformData` as trans \n"
		+"WHERE \n"
		+"  trans.`DEF_id` = "+str(transformid)+" \n" 
		+"LIMIT 1 \n"
	)
	cursor.execute(query)
	result = cursor.fetchone()
	img1 = int(result[0])
	img2 = int(result[1])
	if time.time()-t0 > 0.3:
		print query
		print transformid, "image query", apDisplay.timeString(time.time()-t0)
	return img1, img2


#===============================
def getTransformImageIds(transformdata):
	t0 = time.time()
	img1 = transformdata.special_getitem('image1', dereference=False).dbid
	img2 = transformdata.special_getitem('image2', dereference=False).dbid
	if time.time()-t0 > 0.3:
		print "image query", apDisplay.timeString(time.time()-t0)
	return img1, img2

#===============================
def getStackParticleTiltPair2(stackid, partnum, tiltstackid=None):
	"""
	takes a stack id and particle number (1+) spider-style
	returns the stack particle number for the tilt pair
	"""
	#print stackid, partnum
	if tiltstackid is None:
		tiltstackid = stackid

	t0 = time.time()
	#dbconf = sinedon.getConfig('appionData')
	#db     = MySQLdb.connect(**dbconf)
	#cursor = db.cursor()

	stackpartdata1 = apStack.getStackParticle(stackid, partnum)
	partdata = stackpartdata1['particle']
	partid = partdata.dbid
	if time.time()-t0 > 0.3:
		print "sinedon", apDisplay.timeString(time.time()-t0)

	imgnum, transformdata, otherpartid = getTiltTransformFromParticleId(partid)
	otherpartdata = appionData.ApParticleData.direct_query(otherpartid)

	### get tilt stack particle
	tiltstackdata = apStack.getOnlyStackData(tiltstackid, msg=False)
	stackpartq = appionData.ApStackParticlesData()
	stackpartq['stack'] = tiltstackdata
	stackpartq['particle'] = otherpartdata
	stackpartdatas2 = stackpartq.query(results=1)
	if not stackpartdatas2:
		#print otherpart.dbid
		#apDisplay.printError("particle "+str(partnum)+" has no tilt pair in stackid="+str(tiltstackid))
		return None
	stackpartdata = stackpartdatas2[0]

	#print partnum,"-->",stackpartnum
	if time.time()-t0 > 0.7:
		print "getStackParticleTiltPair2", apDisplay.timeString(time.time()-t0)

	return stackpartdata

