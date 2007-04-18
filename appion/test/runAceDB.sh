#!/bin/sh

rm -f `find .. -name "*.py[oc]"`
rm -fr acedb

pyace.py runid=acedb dbimages=07mar09b,en edgethcarbon=0.8 edgethice=0.6 pfcarbon=0.9 pfice=0.3 \
overlap=2 fieldsize=512 resamplefr=1 tempdir=/tmp/vossman medium=carbon cs=2.0 drange=0 \
outdir=. display=1 stig=0 continue reprocess=0.8 commit
