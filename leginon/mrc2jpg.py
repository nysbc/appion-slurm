#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import Mrc
import Image
import NumericImage
import re


"""
Convert MRC -> JPEG
"""

def mrc2jpeg(filename, quality=100):
	'Convert MRC -> JPEG [quality]'
	nfile = re.sub('\.mrc$','.jpg',file)
	ndata = Mrc.mrc_to_numeric(file)
	num_img = NumericImage.NumericImage(ndata)
	num_img.jpeg(nfile, quality)
	
if __name__ == '__main__':
	import sys

	for file in sys.argv[1:]:
		mrc2jpeg(file)
