#!/bin/bash

rm -fv `find .. -name "*.py[oc]"`
rm -fv `find . -name "*~"`
runid=basicdoglocal2
rm -frv ${runid}

../bin/basicDogPicker.py \
 06nov29b_b_00031gr_00041sq_v01_00019hl_00002en.mrc \
 06nov29b_b_00031gr_00041sq_v01_00019hl_00003en.mrc \
 06nov29b_b_00031gr_00041sq_v01_00019hl_00004en.mrc \
 06nov29b_b_00031gr_00041sq_v01_00019hl_00005en.mrc \
  diam=180 lp=0 bin=8 overlapmult=2 commit \
  runid=${runid} thresh=0.50 outdir=.
