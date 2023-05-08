#!/bin/csh
# 
# N.B. paths have been removed, labed by ****, must be replaced to match local directories
# author: mps

if ( $#argv == 3 ) then
    set subj = $argv[1]
    set date = $argv[2]
    set ROI = $argv[3]
else
    echo "Please specify subj (e.g., P1010228), date (e.g., 20180101) and ROI (e.g. OCC) as input variable"
endif

set FS_dir = **** PATH TO 3T T1 ANATOMY GOES HERE ****/HCP-3.22.0/PHCP{$subj}/
set MNI_dir = {$FS_dir}MNINonLinear/
set mri_dir = {$FS_dir}T1w/PHCP{$subj}/mri/
set SUMA_dir = {$FS_dir}T1w/PHCP{$subj}/SUMA/
set MRS_dir = **** PATH TO 7T MRS ANATOMY FILES GOES HERE ****/{$subj}_{$date}/
set sub_MNI_dir = {$MRS_dir}MNI/

if  !(-d {$MRS_dir}) then
    echo 'cannot find folder: '{$MRS_dir}
    exit
endif

if  !(-d {$sub_MNI_dir}) then
    mkdir {$sub_MNI_dir}
endif

cd {$sub_MNI_dir}

# make a copy of the MNI T1
if  !(-f {$sub_MNI_dir}mni_T1w.nii.gz) then
    cp {$MNI_dir}T1w.nii.gz {$sub_MNI_dir}mni_T1w.nii.gz
endif

# make a copy of the SUMA T1
if  !(-f {$sub_MNI_dir}SUMA_T1.nii) then
    cp {$SUMA_dir}anat_SurfVol.nii {$sub_MNI_dir}SUMA_T1.nii
endif

# make a copy of the regular FS T1
if  !(-f {$sub_MNI_dir}FS_T1.nii.gz) then
    mri_convert {$mri_dir}brainmask.mgz {$sub_MNI_dir}FS_T1.nii.gz
endif

# align SUMA brain to FS regular brain
if  !(-f {$sub_MNI_dir}SUMA_T1_alFS.nii.gz) then
    align_epi_anat.py -epi2anat           \
         -anat {$sub_MNI_dir}FS_T1.nii.gz \
         -rigid_body                      \
         -suffix _alFS                    \
         -epi {$sub_MNI_dir}SUMA_T1.nii   \
         -epi_base 0                      \
         -epi_strip 3dSkullStrip          \
         -ginormous_move                  \
         -volreg off                      \
         -tshift off                      \
         -anat_has_skull no               \
         -cost lpa                        \
         -overwrite

    # convert to .nii.gz, clean up
    3dcopy {$sub_MNI_dir}SUMA_T1_alFS+orig {$sub_MNI_dir}SUMA_T1_alFS.nii.gz
    rm -f {$sub_MNI_dir}SUMA_T1_alFS+orig.*
endif


# copy the talairach xform - note that even though this is called Talairach, 
# it is actually MNI305 space: https://surfer.nmr.mgh.harvard.edu/fswiki/CoordinateSystems
if  !(-f {$sub_MNI_dir}talairach.xfm) then
    cp {$mri_dir}transforms/talairach.xfm {$sub_MNI_dir}/.
endif

# check that converting FS T1 to MNI is working
if  !(-f {$sub_MNI_dir}FS_T1_to_mni.nii.gz) then
    mri_convert --apply_transform {$sub_MNI_dir}talairach.xfm \
        {$sub_MNI_dir}FS_T1.nii.gz -oc 0 0 0 {$sub_MNI_dir}FS_T1_to_mni.nii.gz

    # tell afni this is in talairach space
    3drefit -view tlrc -space TLRC {$sub_MNI_dir}FS_T1_to_mni.nii.gz
endif


# check if there is a "crop" alignment, which means manual intervention, if so, use it
if (-f {$MRS_dir}t1_{$ROI}_uni_crop_strip_al_mat.aff12.1D) then
    set use_al = {$MRS_dir}t1_{$ROI}_uni_crop_strip_al_mat.aff12.1D
else
    set use_al = {$MRS_dir}t1_{$ROI}_uni_strip_al_mat.aff12.1D
endif

# now combine the MRS-to-SUMA xform with the SUMA-to-regular FS xform
cat_matvec {$sub_MNI_dir}SUMA_T1_alFS_mat.aff12.1D {$use_al} > \
    {$sub_MNI_dir}{$ROI}_to_FS_xform.1D

# make MRS mask in regular FS space (rather than in SUMA)
3dAllineate                                             \
    -overwrite                                          \
    -1Dmatrix_apply {$sub_MNI_dir}{$ROI}_to_FS_xform.1D \
    -final NN                                           \
    -prefix {$sub_MNI_dir}{$ROI}_mask_FS.nii.gz         \
    -master {$sub_MNI_dir}FS_T1.nii.gz                  \
    -source {$MRS_dir}{$ROI}_mask.nii.gz

# transform the mask from regular FS to MNI space
mri_convert --apply_transform {$sub_MNI_dir}talairach.xfm \
    {$sub_MNI_dir}{$ROI}_mask_FS.nii.gz -oc 0 0 0 {$sub_MNI_dir}{$ROI}_mask_mni.nii.gz

# change header so AFNI knows this is in MNI space
3drefit -view tlrc -space TLRC {$sub_MNI_dir}{$ROI}_mask_mni.nii.gz

