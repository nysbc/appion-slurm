#!/usr/bin/env python

import os
import sys
import shutil
import subprocess
import time
import leginon.leginondata
import leginon.ddinfo
import pyami.fileutil

next_time_start = 0
mtime = 0
time_expire = 300  # ignore anything older than 5 minutes
expired_names = {} # directories that should not be transferred
check_interval = 20  # seconds between checking for new frames

def parseParams():
	'''
	Use OptionParser to get parameters
	'''
	global check_interval
	if len(sys.argv) == 1 and sys.platform == 'win32':
		try:
			from optparse_gui import OptionParser
			use_gui = True
		except:
			raw_input('Need opparse_gui to enter options on Windows')
			sys.exit()
	else:
		from optparse import OptionParser
		use_gui = False

	parser = OptionParser()

	# options
	parser.add_option("--method", dest="method",
		help="method to transfer, e.g. --method=mv", type="choice", choices=['mv','rsync'], default='rsync' if sys.platform != 'win32' else "mv")
	parser.add_option("--source_path", dest="source_path",
		help="Mounted parent path to transfer, e.g. --source_path=/mnt/ddframes", metavar="PATH")
	parser.add_option("--camera_host", dest="camera_host",
		help="Camera computer hostname in leginondb, e.g. --camera_host=gatank2")
	parser.add_option("--destination_head", dest="dest_path_head",
		help="Specific head destination frame path to transfer if multiple frame transfer is run for one source to frame paths not all mounted on the same computer, e.g. --destination_head=/data1", metavar="PATH", default='')
	parser.add_option("--check_interval", dest="check_interval", help="Seconds between checking for new frames", type="int", default=check_interval)

	# parsing options
	(options, optargs) = parser.parse_args(sys.argv[1:])
	if len(optargs) > 0:
		print "Unknown commandline options: "+str(optargs)
	if not use_gui and len(sys.argv) < 2:
		parser.print_help()
		sys.exit()
	params = {}
	for i in parser.option_list:
		if isinstance(i.dest, str):
			params[i.dest] = getattr(options, i.dest)
	checkOptionConflicts(params)
	check_interval = options.check_interval
	return params

def checkOptionConflicts(params):
	if params['camera_host']:
		r = leginon.leginondata.InstrumentData(hostname=params['camera_host']).query()
		if not r:
			sys.stderr.write('Camera host %s not in Leginon database\n' % (params['camera_host']))
			sys.exit(1)

def getAndValidatePath(params,key):
	pathvalue = params[key]
	if pathvalue and not os.access(pathvalue, os.R_OK):
		sys.stderr.write('%s not exists or not readable\n' % (pathvalue,))
		sys.exit(1)
	return pathvalue

def get_source_path(params):
	return getAndValidatePath(params,'source_path')

def get_dst_head(params):
	return getAndValidatePath(params,'dest_path_head')

image_classes = [
	leginon.leginondata.AcquisitionImageData,
	leginon.leginondata.DarkImageData,
	leginon.leginondata.BrightImageData,
	leginon.leginondata.NormImageData,
]

def query_image_by_frames_name(name,cam_host):
	qccd = leginon.leginondata.InstrumentData(hostname=cam_host)
	qcam = leginon.leginondata.CameraEMData(ccdcamera=qccd)
	qcam['frames name'] = name
	for cls in image_classes:
		qim = cls(camera=qcam)
		results = qim.query()
		if results:
			return results[0]
	return None

def removeEmptyFolders(path):
	if not os.path.isdir(path):
		return

	print 'found', path
	# remove empty subfolders
	files = os.listdir(path)
	if len(files):
		for f in files:
			fullpath = os.path.join(path, f)
			if os.path.isdir(fullpath):
				removeEmptyFolders(fullpath)

	# if folder empty, delete it
	files = os.listdir(path)
	if len(files) == 0:
		print "Removing empty folder:", path
		######filedir operation########
		os.rmdir(path)

def copy_and_delete(src, dst):
	'''
	Use rsync to copy the file.  The sent files are removed
	after copying.
	'''
	cmd = 'rsync -av --remove-sent-files %s %s' % (src, dst)
	print cmd
	p = subprocess.Popen(cmd, shell=True)
	p.wait()

def move(src, dst):
	'''
	Use shutil's move to rename frames
	'''
	######filedir operation########
	print 'moving %s -> %s' % (src, dst)
	shutil.move(src, dst)

def transfer(src, dst, uid, gid, method):
	'''
	This function at minimal organize and rename the time-stamped file
	to match the Leginon session and integrated image.  If the source is
	saved on the local drive of the camera computer, rsync (default) is
  used to copy the file off and the time-stamped file on the camera
	local drive removed to make room for more data collection.
	'''
	# make destination dirs
	dirname,basename = os.path.split(os.path.abspath(dst))
	print('mkdirs %s'%dirname)
	if not os.path.exists(dirname):
		if sys.platform != 'win32':
			# this function preserves umask of the parent directory
			pyami.fileutil.mkdirs(dirname)
		else:
			# use os.makedirs on 'win32' but it does not preserve umask
			os.makedirs(dirname)
	elif os.path.isfile(dirname):
		print("Error %s is a file"%dirname)

	if method == 'rsync' and sys.platform != 'win32':
		# safer method but slower
		copy_and_delete(src, dst)
	else:
		# move does only rename and therefore will be faster if on the same device
		# but could have problem if dropped during the process between devices.
		move(src,dst)

	# change ownership of desintation directory and contents
	if sys.platform != 'win32':
		cmd = 'chown -R %s:%s %s' % (uid, gid, dirname)
		print cmd
		p = subprocess.Popen(cmd, shell=True)
		p.wait()

	if method == 'rsync' and sys.platform != 'win32':
		# remove empty .frames dir from source
		abspath = os.path.abspath(src)
		dirpath,basename = os.path.split(abspath)
		if src.endswith('/'):
			cmd = 'find %s -type d -empty -prune -exec rmdir --ignore-fail-on-non-empty -p \{\} \;' % (basename,)
			print 'cd', dirpath
		print cmd
		p = subprocess.Popen(cmd, shell=True, cwd=dirpath)
		p.wait()
	else:
		removeEmptyFolders(os.path.abspath(src))

def run_once(parent_src_path,cam_host,dest_head,method):
	global next_time_start
	global time_expire
	global mtime
	names = os.listdir(parent_src_path)
	time.sleep(10)  # wait for any current writes to finish
	time_start = next_time_start
	for name in names:
		src_path = os.path.join(parent_src_path, name)
		_, ext = os.path.splitext(name)
		## skip empty directories
		if os.path.isdir(src_path) and not os.listdir(src_path):
			# maybe delete empty dir too?
			continue

		# skip expired dirs, mrcs
		if name in expired_names:
			continue

		# adjust next expiration timer to most recent time
		if mtime > next_time_start:
			next_time_start = mtime

		# ignore irrelevent source files or folders
		# gatan k2 summit data ends with '.mrc'
		# de folder starts with '20'
		if ext != '.mrc' and  ext != '.frames' and not name.startswith('20'):
			continue
		print '**running', src_path

		# query for Leginon image
		if ext == '.mrc':
			frames_name = name[:-4]
			dst_suffix = '.frames.mrc'
		else:
			frames_name = name
			dst_suffix = '.frames'
			## ensure a trailing / on directory
			if src_path[-1] != os.sep:
				src_path = src_path + os.sep
		imdata = query_image_by_frames_name(frames_name,cam_host)
		if imdata is None:
			continue
		image_path = imdata['session']['image path']
		frames_path = imdata['session']['frame path']

		# back compatible to sessions without frame path in database
		if image_path and not frames_path and sys.platform != 'win32':
			frames_path = leginon.ddinfo.getRawFrameSessionPathFromImagePath(image_path)

		# only process destination frames_path starting with chosen head
		if sys.platform != 'win32' and not frames_path.startswith(dest_head):
			print "frames_path = %s"%frames_path
			print '    Destination frame path does not starts with %s. Skipped' % (dest_head)
			continue

		# determine user and group of leginon data
		filename = imdata['filename']
		if sys.platform == 'win32':
			uid, gid = 100, 100
		else:
			stat = os.stat(image_path)
			uid = stat.st_uid
			gid = stat.st_gid
		# make full dst_path
		imname = filename + dst_suffix
		dst_path = os.path.join(frames_path, imname)
		print 'Destination path: %s' %  (dst_path)

		# do actual copy and delete
		transfer(src_path, dst_path, uid, gid,method)
		# de only
		leginon.ddinfo.saveImageDDinfoToDatabase(imdata,os.path.join(dst_path,'info.txt'))

def run():
	params = parseParams()
	src_path = get_source_path(params)
	print 'Source path:  %s' % (src_path,)
	dst_head = get_dst_head(params)
	if dst_head:
		print "Limit processing to destination frame path started with %s" % (dst_head)
	while True:
		print 'Iterating...'
		run_once(src_path,params['camera_host'],dst_head,method=params['method'])
		print 'Sleeping...'
		time.sleep(check_interval)

if __name__ == '__main__':
	run()
