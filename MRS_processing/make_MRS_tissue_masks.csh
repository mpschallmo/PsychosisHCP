#!/bin/tcsh -xef
#
# N.B. paths have been removed, labed by ****, must be replaced to match local directories
#
# author: mps

if ( $#argv > 0 ) then
    set subj = $argv[1]
    set date = $argv[2]
    set maskname = $argv[3]
else
    echo "Please set subject, date, and ROI"
    exit
endif

set topDir = '**** PATH TO TOP DIR GOES HERE ****'
set subj_date = {$subj}'_'{$date}'/'
set anatDir = $topDir'anatomy/'
set anatSub = {$anatDir}{$subj_date}
set ext = ".nii.gz"

cd $anatSub

# first make a GM mask from the segmented FreeSurfer data
3dcalc -overwrite                        \
    -prefix rm_${maskname}_GM_mask${ext} \
    -a "${maskname}_mask_al${ext}"       \
    -b "SUMA/lh.ribbon.nii"              \
    -c "SUMA/rh.ribbon.nii"              \
    -expr "a*step(b+c)"

# make a WM mask, remove ventricles, and give any overlap 
# with GM to GM (based on visual inspection)
3dcalc -overwrite                        \
    -prefix ${maskname}_WM_mask${ext}    \
    -a "${maskname}_mask_al${ext}"       \
    -b "SUMA/wm.nii"                     \
    -c "SUMA/aparc+aseg_REN_vent.nii.gz" \
    -d "rm_${maskname}_GM_mask${ext}"    \
    -expr "step( a*( step( step(b) - step(c) ) ) - d)"

# make a combined GM and WM mask
3dcalc -overwrite                          \
    -prefix rm_${maskname}_GMWM_mask${ext} \
    -a "rm_${maskname}_GM_mask${ext}"      \
    -b "${maskname}_WM_mask${ext}"         \
    -expr 'step(a+b)'

# fill the holes in the combined mask, to get rid of weird points getting
# labeled CSF (based on visual inspection)
3dmask_tool -overwrite                          \
    -prefix rm_${maskname}_fill_GMWM_mask${ext} \
    -inputs rm_${maskname}_GMWM_mask${ext}      \
    -fill_holes

# use the filled GM WM mask to give filled points to GM, making the final GM mask...
# remove ventricles, just in case they got filled...
3dcalc -overwrite                            \
    -prefix ${maskname}_GM_mask${ext}        \
    -a "rm_${maskname}_fill_GMWM_mask${ext}" \
    -b "${maskname}_WM_mask${ext}"           \
    -c "SUMA/aparc+aseg_REN_vent.nii.gz"     \
    -expr 'step(a-step(b + c))'

# make a CSF mask, assuming everything that is NOT GM or WM is CSF...
3dcalc -overwrite                      \
    -prefix ${maskname}_CSF_mask${ext} \
    -a "${maskname}_mask_al${ext}"     \
    -b "${maskname}_GM_mask${ext}"     \
    -c "${maskname}_WM_mask${ext}"     \
    -expr "step(a - step(b+c))"

# make a combined mask, just for fun / visualization purposes...
3dcalc -overwrite                       \
    -prefix ${maskname}_comb_mask${ext} \
    -a "${maskname}_WM_mask${ext}"      \
    -b "${maskname}_GM_mask${ext}"      \
    -c "${maskname}_CSF_mask${ext}"     \
    -expr "a+2*b+3*c"

# remove intermediate files
\rm -f ./rm_*
