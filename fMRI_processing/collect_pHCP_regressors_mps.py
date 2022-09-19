#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Aug  9 10:13:58 2017

@author: caolman, edits by tes, mps

TES version updated 1/16/2018 to use task as an argument variable and direct 
regressors directly into subject's directory
MPS version (from TES) updated 20180322 to run from other python functions...
MPS 20180917 updated to work in the behavioral_data_X folders

N.B. paths have been removed, labed by ****, must be replaced to match local directories

Goal here is to create all the regressors for GLM-based analysis for 7T pHCP
scanning session, using the new file formats saved out on 30Aug2017.  

To do this, we need to:
  - load pickle files from COP task and create 4 stim timing files for each scan
  - look at pRF output and write ...
      ... motor task
      ... tone regressors (+ .py file for figuring it out ...)
      ... visual category regressors
      ... temporal frequency regressors (interested in interaction w/ pRF reg.)
      ... quadrant pRF regressors, after we figure out which scan-type it was
  - look at CSS output and write ...
      ... regressors for each condition
      ... .py file with information for Fourier analysis

"""

import pickle, glob, os, sys
from shutil import copyfile

gitClone = '**** PATH TO THE GIT REPO GOES HERE ****'
prfRegressorDir = '**** PATH TO THE REGRESSOR DIR GOES HERE ****'

if __name__ == '__main__':
    # sys.argv[0] is name of function
    if len(sys.argv) < 3:
        # help is required
        print("""
        Usage:  python collect_pHCP_regresors.py subjID task scanLetter
        
        takes 3 arguments ... the ID of the participant, the task, and the scan letter (e.g., B, Z)
        
        Will look in behavioral_data_X/ for fMRI behavioral files.
                
        Will then create a sub-directory (regressors) that has:
          1) regressors for AFNI with standardized names
              for COP, these are:  copX_loc, _cont, bg_scr, nb_cont, nb_scr
              for pRF, these are: upper/lower_right/left (copied from right qRF file)
                                  left/right_toes/fingers, tongue
                                  toneX00Hz 
                                  visualXHz
                                  visual category
              for CSS, these are:  localizer (tgt/surr)
                                  ns10, 20, 40, 80
                                  ss10, 20, 40, 80
          2) FSL versions of all of the above
          3) .py files with dictionaries that will define Fourier analyses for
              pRF_auditory
              COP_localizer
              CSS_localizer
              CSS_ns10, 20, 40, 80, ss10, 20, 40, 80 ...
                                  
        """)
        sys.exit()
    subjID = sys.argv[1]
    task = sys.argv[2]
    scanLetter = sys.argv[3]

def col_reg(subjID, task, scanLetter):
    if task == "css" or task == "cop" or task == "prf":
        print ("Task variable must be in capital letters")
    regressorDir = '****PATH TO THE DATA ANALYSIS DIR GOES HERE ***/behavioral_data_%s' %(subjID, scanLetter)
    # figure out output location
    outDir = regressorDir
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    for subDir in ['afni', 'fsl']:
        if not os.path.exists(os.path.join(outDir, subDir)):
            os.makedirs(os.path.join(outDir, subDir))

    # figure out inputs (Updated 9/11/2017 by TES to reflect new changed file names and elimination of pRFoutput folder)
    if task == "COP":
        copDir = regressorDir 
        copFiles = glob.glob(os.path.join(copDir, '%s*COP_fMRI*.pickle' %subjID)) 
        copFiles.sort()

        if len(copFiles) < 1:
            print('Did not find any %s*COP_fMRI* files in %s.' %(subjID, copDir))
        else:
            # create COP regressors
            afniFiles = []
            fslFiles = []
            # afni first ...
            for iRun, pFile in enumerate(copFiles):
                if sys.version_info.major == 3:
                    p = pickle.load(open(pFile, 'rb'), fix_imports=True, encoding='latin1')
                else:
                    p = pickle.load(open(pFile, 'rb'))
                    
                afniFids = []
                fslFids = []
                for condition in ['bg_scr', 'bg_cont', 'nb_scr', 'nb_cont']:
                    cFile = os.path.join(outDir, 'afni', 'cop%d_%s.txt' %(iRun+1, condition))
                    afniFids.append(open(cFile, 'w'))
                    cFile = os.path.join(outDir, 'fsl', 'cop%d_%s.txt' %(iRun+1, condition))
                    fslFids.append(open(cFile, 'w'))
                    
                for stim in p['stimOnsetTimes']:
                    afniFids[stim[1]].write(' %4.1f' %stim[2])
                    fslFids[stim[1]].write(' %4.1f 1. 1.\n' %stim[2])

                if p['localizerBlockOrder']:
                    cFile = os.path.join(outDir, 'afni', 'cop%d_tgt.txt' %(iRun+1))
                    afniFids.append(open(cFile, 'w'))
                    cFile = os.path.join(outDir, 'fsl', 'cop%d_tgt.txt' %(iRun+1))
                    fslFids.append(open(cFile, 'w'))
                    for tgt in range(13, 144, 24): # hard coding timing...
                        afniFids[4].write(' %4.1f' %(tgt))
                        fslFids[4].write(' %4.1f 1. 1.\n' %(tgt))

                for f in afniFids:
                    f.write('\n')
                for f in afniFids + fslFids:
                    f.close()
            lines = ['fourier = []',
                 "fourier.append({'name': 'cop_loc',",
                 "                'scanList': [%d]," %0,
                 "                'discardFrames': [%d]," %12,
                 "                'keepFrames': %d," %(144),
                 "                'nCycles': 6})\n"]
            copFourierFile = os.path.join(outDir, 'cop_fourier.py')
            with open(copFourierFile, 'w') as fid:
                for line in lines:
                    fid.write('%s\n' %line)
                for iScan in range(len(copFiles)):
                    copGLMFile = []
                    scanStr = str(iScan+1) 
                    lines = ['GLM = []',
                             "GLM.append({'name': 'cop%s'," %scanStr,
                             "   'labels': ['cop%s_bg_scr', 'cop%s_bg_cont', 'cop%s_nb_scr', 'cop%s_nb_cont']," %(scanStr, scanStr,
                                                                                                                 scanStr, scanStr),
                             "   'scans': [%d]," %iScan,
                             "   'model': 'GAM',",
                             "   'verbose': False})\n"]
                    copGLMFile = os.path.join(outDir, 'cop%s_glm.py' %scanStr)
                    with open(copGLMFile, 'w') as fid:
                        for line in lines:
                            fid.write('%s\n' %line)


    elif task == "pRF":
        prfDir = regressorDir 
        prfFiles = glob.glob(os.path.join(prfDir, '%s*pRF_fMRI*.txt' %subjID)) 
        prfFiles.sort()
         # now look into pRF
        if len(prfFiles) < 1:
            print('Did not find %s*pRF_fMRI* files in %s.' %(subjID, prfDir))
        else:
            # regressor namess
            motor = ['right_fingers', 'left_fingers', 'right_toes', 'left_toes', 'tongue']
            tones = [250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000]
            visualCategories = ['human faces',
                                'animal faces',
                                'human bodies',
                                'animal bodies',
                                'food',
                                'objects',
                                'places',
                                'noise']
            temporalFreq = ['2Hz', '12Hz']
            for iRun, p in enumerate(prfFiles):
                with open(p, 'r') as f:
                    header = f.readline()
                    events = f.readlines()
                    eventList = []
                    for e in events:
                        eventList.append(e.strip().split('\t'))
                
                    # fix the fact that pRF code didn't write down events if we got
                    # back-to-back blocks of a motor cue
                    motorCues = []
                    nCues = {cue: 0 for cue in motor}
                    for iE, e in enumerate(eventList):
                        if e[0] in motor:
                            motorCues.append({'cue': e[0], 'onset': float(e[1])})
                            nCues[e[0]] += 1
                    print(nCues)
                    lastCue = False
                    iM = 0
                    while not lastCue:
                        try:
                            duration = motorCues[iM+1]['onset'] - motorCues[iM]['onset']
                            if duration < 14.:
                                motorCues[iM]['duration'] = duration
                                iM += 1
                            else:
                                motorCues[iM]['duration'] = 13.
                                motorCues.insert(iM+1, {'cue': motorCues[iM]['cue'],
                                                        'onset': motorCues[iM]['onset'] + 13.,
                                                        'duration': 13.})
                                iM += 2
                                nCues[motorCues[iM]['cue']] += 1
                            nCues[motorCues[iM]['cue']] += 1
                        except:
                            lastCue = True
                    # fill in that last one with an assumption
                    motorCues[-1]['duration'] = 13.
                    # go back through and count to be sure we got it right, and make
                    # a motorList that's formatted the same as the eventList, to use
                    # below in creating the regressors
                    nCues = {cue: 0 for cue in motor}
                    motorList = []
                    for m in motorCues:
                        nCues[m['cue']] += 1
                        motorList.append([m['cue'],
                                          '%2.2f' %m['onset'],
                                          '%2.2f' %m['duration']])
                    print(nCues)
                    #------------# end new additions

                # figure out which type of pRF run it was
                categoryOrder = []
                for e in eventList:
                    cat = e[0].split(',')[0].strip()
                    categoryOrder += [iC for iC, c in enumerate(visualCategories) if cat == c]
                if categoryOrder == [1,4,3,5,0,6,3,2,0,7,2,4,6,5,1,7]:
                    prfType = 'a'
                elif categoryOrder == [0,7,5,4,7,3,4,0,3,5,2,2,6,1,1,6]:
                    prfType = 'b'
                elif categoryOrder == [4,4,7,6,3,2,0,5,7,3,5,1,0,2,1,6]:
                    prfType = 'c'
                elif categoryOrder == [4,5,0,6,2,6,4,7,3,1,0,3,2,7,5,1]:
                    prfType = 'd'
                else:
                    print('Oops!  Did not recognize category order for visual stim!')
                    print('Not copying over any regressors ...')
                    prfType = 'X'
                for m in motor:
                    cFile = os.path.join(outDir, 'afni', 'prf%d_%s_%s.txt' %(iRun+1,prfType, m)) 
                    with open(cFile, 'w') as fid: 
                        for e in motorList:
                            if e[0] == m:
                                fid.write('%2.1f ' %float(e[1]))
                        fid.write('\n')
                    cFile = os.path.join(outDir, 'fsl', 'prf%d_%s_%s.txt' %(iRun+1,prfType, m))
                    with open(cFile, 'w') as fid: 
                        for e in motorList: 
                            if e[0] == m:
                                fid.write('%2.1f %2.1f 1 \n' %(float(e[1]), float(e[2])))
                for t in tones:
                    cFile = os.path.join(outDir, 'afni', 'prf%d_%s_%dHzTone.txt' %(iRun+1,prfType, t))
                    with open(cFile, 'w') as fid:
                        for e in eventList:
                            if e[0] == str(t):
                                fid.write('%2.1f ' %float(e[1]))
                        fid.write('\n')
                    cFile = os.path.join(outDir, 'fsl', 'prf%d_%s_%dHzTone.txt' %(iRun+1,prfType, t))
                    with open(cFile, 'w') as fid:
                        for e in eventList:
                            if e[0] == str(t):
                                fid.write('%2.1f %2.1f 1 \n' %(float(e[1]), float(e[2])))
                for h in temporalFreq:
                    cFile = os.path.join(outDir, 'afni', 'prf%d_%s_%sVisual.txt' %(iRun+1,prfType, h))
                    with open(cFile, 'w') as fid:
                        for e in eventList:
                            try:
                                if e[0].split(',')[1].strip() == h:
                                    fid.write('%2.1f ' %float(e[1]))
                            except:
                                pass
                        fid.write('\n')
                    cFile = os.path.join(outDir, 'fsl', 'prf%d_%s_%sVisual.txt' %(iRun+1,prfType, h))
                    with open(cFile, 'w') as fid:
                        for e in eventList:
                            try:
                                if e[0].split(',')[1].strip() == h:
                                    fid.write('%2.1f %2.1f 1 \n' %(float(e[1]), float(e[2])))
                            except:
                                pass
                for c in visualCategories:
                    categoryOrder = []
                    cFile = os.path.join(outDir, 'afni', 'prf%d_%s_%s.txt' %(iRun+1,prfType, c.replace(' ', '_')))
                    with open(cFile, 'w') as fid:
                        for e in eventList:
                            try:
                                if e[0].split(',')[0].strip() == c:
                                    fid.write('%2.1f ' %float(e[1]))
                            except:
                                pass
                        fid.write('\n')
                    cFile = os.path.join(outDir, 'fsl', 'prf%d_%s_%s.txt' %(iRun+1,prfType, c.replace(' ', '_')))
                    with open(cFile, 'w') as fid:
                        for e in eventList:
                            try:
                                if e[0].split(',')[0].strip() == c:
                                    fid.write('%2.1f %2.1f 1 \n' %(float(e[1]), float(e[2])))
                            except:
                                pass
                # get the inputs for AFNI's pRF analysis
                stackIn = os.path.join(prfRegressorDir, 'stack%s.nii' %prfType.upper())
                stackOut = os.path.join(outDir, 'stack%s.nii' %prfType.upper())
                cmd = copyfile(stackIn, stackOut)
                # qRF regressors 
                # we don't really want these for analysis, but we do want them for running
                # an initial 3dDeconvolve command that will absorb stimulus-driven 
                # variance to get a more accurate estimate of tSNR
                inPatterns = ['r0.00t0.00', 'r6.00t0.79', 'r6.00t2.36', 'r6.00t3.93', 'r6.00t5.50']
                outPatterns = ['fovea', 'vfURquad', 'vfLRquad', 'vfLLquad', 'vfULquad']
                for iP, inp in enumerate(inPatterns):
                    with open(os.path.join(prfRegressorDir, 'qRF%s_%s.txt' %(prfType, inp)), 'r') as fid:
                        scanTimes = [float(t) for t in fid.readline().strip().split(' ')]
                    cFile = os.path.join(outDir, 'afni', 'prf%d_%s_%s.txt' %(iRun+1, prfType, outPatterns[iP]))
                    with open(cFile, 'w') as fid:
                        for t in scanTimes:
                            fid.write('%2.1f ' %t)
                        fid.write('\n')
                    cFile = os.path.join(outDir, 'fsl', 'prf%d_%s_%s.txt' %(iRun+1, prfType, outPatterns[iP]))
                    with open(cFile, 'w') as fid:
                        for t in scanTimes:
                            fid.write('%2.1f 1. 1. \n' %t)
        #       and, now that everything is written, use the 200Hz tone to create a
        #       fourier analysis file for auditory stuff
            cFile = os.path.join(outDir, 'afni', 'prf%d_%s_250HzTone.txt' %(iRun+1,prfType))
            with open(cFile, 'r') as fid:
                times = fid.readline().strip().split(' ')
            firstTime = float(times[0])
            lastTime = float(times[-1])
            if firstTime < 20.:
                # we went up/down
                lines = ['fourier = []',
                     "fourier.append({'name': 'aRF%s'," %prfType,
                     "                'scanList': [0, 0],",
                     "                'discardFrames': [%d, %d]," %(firstTime,
                                                                    lastTime-120),
                     "                'keepFrames': 120,",
                     "                'nCycles': 8,",
                     "                'shiftFrames': [4, 4],",
                     "                'reverse': [0, 1]})"]
            else:
                 # we went down, up
                lines = ['fourier = []',
                     "fourier.append({'name': 'aRF%s'," %prfType,
                     "                'scanList': [0, 0],",
                     "                'discardFrames': [%d, %d]," %(firstTime-15,
                                                                    lastTime-105),
                     "                'keepFrames': 120,",
                     "                'nCycles': 8,",
                     "                'shiftFrames': [4, 4],",
                     "                'reverse': [1, 0]})"]
            audFourierFile = os.path.join(outDir, 'auditory_fourier.py')
            with open(audFourierFile, 'w') as fid:
                for line in lines:
                    fid.write('%s\n' %line)
        
        
    elif task == "CSS":
        cssDir = regressorDir 
        cssFiles = glob.glob(os.path.join(cssDir, '%s*CSS_fMRI*.txt' %subjID)) 
        cssFiles.sort()

        # now look into CSS
        if len(cssFiles) < 1:
            print('Did not find %s*CSS_fMRI* files in %s.' %(subjID, cssDir))
        else:
            # regressor namess
            conditions = ['tgt',
                          'ns00',
                          'ss00',
                          'ns10',
                          'ss10',
                          'ns20',
                          'ss20',
                          'ns40',
                          'ss40',
                          'ns80',
                          'ss80']
            for iRun, cssFile in enumerate(cssFiles):
                with open(cssFile, 'r') as f:
                    headers = f.readline()
                    events = f.readlines()
                    eventList = []
                    for e in events:
                        eventList.append(e.strip().split('\t'))
                for iC, c in enumerate(conditions):
                    onsets = []
                    durations = []
                    # we're looking to only write down the 1st of eacon condition
                    lastC = -1
                    for e in eventList:
                        if int(e[0]) == iC:
                            if lastC != iC:
                                onsets.append(float(e[1]))
                                durations.append(9.)
                        lastC = int(e[0])
                    if onsets:
                        cFile = os.path.join(outDir, 'afni', 'css%d_%s.txt' %(iRun, c))
                        with open(cFile, 'w') as fid:
                            for o in onsets:
                                fid.write('%2.2f ' %o)
                            fid.write('\n')
                        cFile = os.path.join(outDir, 'fsl', 'css%d_%s.txt' %(iRun, c))
                        with open(cFile, 'w') as fid:
                            for iO, o in enumerate(onsets):
                                fid.write('%2.1f %2.1f 1 \n' %(o, durations[iO]))
            conditions = ['ns10',
                      'ss10',
                      'ns20',
                      'ss20',
                      'ns40',
                      'ss40',
                      'ns80',
                      'ss80']

        lines = ['fourier = []',
             "fourier.append({'name': 'css_loc',",
             "                'scanList': [%d]," %0,
             "                'discardFrames': [%d]," %9,
             "                'keepFrames': %d," %(18*5),
             "                'nCycles': 5})\n"]
        cssFourierFile = os.path.join(outDir, 'css_fourier.py')
        with open(cssFourierFile, 'w') as fid:
            for line in lines:
                fid.write('%s\n' %line)
        for cond in conditions:
            regFiles = glob.glob(os.path.join(outDir, 'afni', 'css*'))
            whichFile = [f for f in regFiles if cond in f][0]
            with open(whichFile, 'r') as fid:
                times = fid.readline()
            onset = float(times.strip().split(' ')[0])
            p, fileName = os.path.split(whichFile)
            whichScan = int(fileName[3])
            lines = ["fourier.append({'name': '%s'," %cond,
                     "                'scanList': [%d]," %(0+whichScan),
                     "                'discardFrames': [%d]," %(int(onset+9)),
                     "                'keepFrames': %d," %(18*5),
                     "                'nCycles': 5})\n"]
            with open(cssFourierFile, 'a') as fid:
                for line in lines:
                    fid.write('%s\n' %line)

if __name__ == '__main__':
    col_reg(subjID, task, scanLetter) 