#!/bin/tcsh -xef
#
# N.B. paths have been removed, labed by ****, must be replaced to match local directories
#
# author: mps

if ( $#argv > 0 ) then
    set subj = $argv[1]
    set date = $argv[2]
    set ROI = $argv[3]
else
    echo "Please set subject, date, and ROI"
    exit
endif

if ( $#argv > 3 ) then
    set doCrop = $argv[4]
else
    set doCrop = 0
endif

set doStripMRST1 = 1
set doUnifize = 1

set topDir = '**** PATH TO TOP DIR GOES HERE ****'
set subj_date = {$subj}'_'{$date}'/'
set T1name = 't1_'{$ROI}
set ext = '.nii.gz'
set anatDir = $topDir'anatomy/'
set anatSub = {$anatDir}{$subj_date}
set T1_MRS = {$anatDir}{$subj_date}{$T1name}{$ext}
set name3T = 'anat_SurfVol'
set T1_3T = {$anatDir}{$subj_date}{$name3T}{$ext}
set mask_name = {$ROI}'_mask'
set MRS_mask = {$anatSub}{$mask_name}{$ext}

cd $anatSub

if ( $doUnifize == 1 ) then
    set T1name = {$T1name}_uni
    set uniName = {$anatDir}{$subj_date}{$T1name}{$ext}
    3dUnifize -overwrite -GM -prefix {$uniName} $T1_MRS
    set T1_MRS = $uniName
endif

if ( $doCrop == 1 ) then
    set T1name = {$T1name}_crop
    set cropName = {$anatDir}{$subj_date}{$T1name}{$ext}
    3dZeropad -overwrite -I -15 -prefix {$cropName} $T1_MRS
    set T1_MRS = $cropName # put this here, so we overwrite the crop
    3dZeropad -overwrite -I 15 -prefix {$cropName} $T1_MRS
    3dZeropad -overwrite -A -50 -prefix {$cropName} $T1_MRS
    3dZeropad -overwrite -A 50 -prefix {$cropName} $T1_MRS
    3dZeropad -overwrite -S -10 -prefix {$cropName} $T1_MRS
    3dZeropad -overwrite -S 10 -prefix {$cropName} $T1_MRS
endif

if ( $doStripMRST1 == 1 ) then
    set T1name = {$T1name}_strip
    set stripName = {$anatDir}{$subj_date}{$T1name}{$ext}
    3dSkullStrip -overwrite -surface_coil -input $T1_MRS -prefix $stripName
    set T1_MRS = $stripName
endif

set useSuffix = '_al'

align_epi_anat.py -epi2anat -anat {$T1_3T} \
     -rigid_body                           \
     -suffix $useSuffix                    \
     -epi $T1_MRS                          \
     -epi_base 0                           \
     -epi_strip 3dAutomask                 \
     -ginormous_move                       \
     -volreg off                           \
     -tshift off                           \
     -anat_has_skull yes                   \
     -partial_sagittal                     \
     -cost lpa                             \
     -overwrite

set al_ext = {$useSuffix}_mat.aff12.1D
set trfName = {$anatDir}{$subj_date}{$T1name}{$al_ext}

3dAllineate                                 \
    -overwrite                              \
    -1Dmatrix_apply ${trfName}              \
    -final NN                               \
    -prefix {$anatSub}{$mask_name}_al{$ext} \
    -master {$T1_3T}                        \
    -source {$MRS_mask}
