#!/usr/bin/env python

import pyscope.registry
import numextension

cam = pyscope.registry.getClass('DE12')()

# Measure Dark Noise
cam.setExposureTime(0)
dark_images = []
for i in (0,1):
	cam.setUseFrames((0,))
	cam.setExposureType('dark')
	im = cam.getImage()
	dark_images.append(im)
diff = dark_images[1] - dark_images[0]
std = diff.std()
print 'Dark Noise: ', std

# Measure Leakage Current
# acquire two dark frames, one at 5 fps, on at 20 fps
dark_images = []
exposure_times = []
for fps in (20,5):
	set_exp_time = 1000 * int(1.0 / fps)
	cam.setFrameRate(fps)
	cam.setExposureTime(set_exp_time)  # only one frame
	exp_time = cam.getExposureTime()
	print 'EXPTIME', exp_time
	cam.setUseFrames((0,))   # just to be sure there is only one frame
	cam.setExposureType('dark')
	im = cam.getImage()
	print 'IM MEAN', im.mean()
	dark_images.append(im)
	exposure_times.append(exp_time)

# calculate dark noise
imdiff = dark_images[1] - dark_images[0]
timediff = (exposure_times[1] - exposure_times[0]) / 1000.0
print 
mean = imdiff.mean()
print 'DIFF MEAN', mean
leakage = mean / timediff
print 'Leakage: ', leakage

print ''
raw_input('Enter to quit.')