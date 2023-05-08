# PsychosisHCP
Experimental task and data processing code for "The Psychosis Human Connectome Project: Design and rationale for studies of visual neurophysiology"

Code authors: Michael-Paul Schallmo, Andrea N. Grant, and Cheryl A. Olman


System requirements:

AFNI 18.2.04

FreeSurfer 5.3

Matlab 2016a

Matlab 2014a

Matlab 2009a

Python 2.7

PsychoPy 1.85.2

gradunwarp 1.0.3

matspec (matlab toolbox)

Gannet 3.0 (matlab toolbox)

SPM8 (matlab toolbox)

Shell scripts written for and run in tcsh (t-shell)
Tested on Linux Red Hat version 6.10


Installation guide:

Unzip or clone the directory
Most scripts must be edited manually based on your local data paths, look for:
% N.B. paths have been removed, labed by ****, must be replaced to match local directories

Time to install: <5 min


Instructions for use:

Experiment code in the tasks folder should be run in PsychoPy, with a mirrored and luminance calibrated screen. The CSS_psych.py task additionally requires a Bits# stimulus processing device to function properly.

FMRI processing is done by proc_unwarp_GLM.csh -- this typically takes multiple hours to run for a single data sets on our server.

MRS processing is done in 3 stages by single_page_phcp_func.m -- each stage takes about 10 - 30 minutes (to process all data sets) on our server.
Note that to use the "createLCmodel_control_steam7T_phcp_lipids.m file for creating LCModel control files, you will need to add a 'steam_phcp' case to processing_LCmodel.m in the matspec toolbox -- for example:
   case 'steam_phcp'
   P = createLCmodel_control_steam7T_phcp(fullfile(pathstr,filename),l1,l2,l3,preproc_dir)

For full details, see our manuscript entitled "The Psychosis Human Connectome Project: Design and rationale for studies of visual neurophysiology"


This code is made available under the following license: Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) https://creativecommons.org/licenses/by-nc/4.0/
