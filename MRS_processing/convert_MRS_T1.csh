#!/bin/tcsh -xef
#
# N.B. paths have been removed, labed by ****, must be replaced to match local directories
#
# author: mps

if ( $#argv > 0 ) then
    set subj = $argv[1]
    set date = $argv[2]
    set ROI = $argv[3]
    set T1folder = $argv[4]
else
    echo "Please set subject, date, ROI, and T1 folder"
    exit
endif

set topDir = '**** PATH TO TOP DIR GOES HERE ****'
set dicomDir = $topDir'dicom_data/'
set subj_date = {$subj}'_'{$date}'/'
set T1name = 't1_'{$ROI}
set ext = '.nii.gz'
set fullDicom = {$dicomDir}{$subj_date}{$T1folder}
set anatDir = $topDir'anatomy/'
set anatSub = {$anatDir}{$subj_date}
set anatDicom = {$anatSub}{$T1name}'_dicom'
set anatSUMA = {$anatSub}'SUMA'

set dir3T = '**** PATH TO 3T ANATOY DIR GOES HERE ****/HCP-3.22.0/PHCP'{$subj}'/T1w/PHCP'{$subj}'/SUMA/'
set file3T = 'anat_SurfVol'
set ext3T = '.nii'

# mkdir $anatSub
ln -s $fullDicom $anatDicom
if ( -d $dir3T ) then
    echo SUMA directory "$dir3T" already exists, skipping...
else
    @SUMA_Make_Spec_FS -fspath **** PATH TO 3T ANATOY DIR GOES HERE ****/HCP-3.22.0/PHCP$subj/T1w/PHCP$subj -sid anat
    3dcopy **** PATH TO 3T ANATOY DIR GOES HERE ****/HCP-3.22.0/PHCP$subj/T1w/PHCP$subj/SUMA/anat_SurfVol+orig. **** PATH TO 3T ANATOY DIR GOES HERE ****/HCP-3.22.0/PHCP$subj/T1w/PHCP$subj/SUMA/anat_SurfVol.nii
endif
if ( -d $anatSUMA ) then
    echo link to SUMA directory "$anatSUMA" already exists, skipping...
else
    ln -s $dir3T $anatSUMA
endif
chmod -R ug+wx $anatSub

to3d -overwrite -prefix {$T1name}{$ext} -session {$anatSub} {$anatDicom}/*.dcm

3dcopy -overwrite {$dir3T}{$file3T}{$ext3T} {$anatSub}{$file3T}{$ext}
