#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# author: caolman, edits by mps

"""
Overall design:
    8 types of bars -- 4 orientations x 2 directions
        Each appears twice, pseudo-random order
        Once in 1st half of scan, once in 2nd
    Bar duration + rest in between controls scan duration
        16 bars x 16s each + 4s flanking every sweep = 324 sec
    8 categories of objects (Kriegeskorte 2008)
        Subjective division into:
            Animals, animal faces, human body parts, human faces
            Pink noise, objects, food, places
        2 different refresh rates:  2 Hz and 12 Hz
            Potentially useful for mapping magno/parvo
        So each category appears with each refresh rate
            Not constrained to appear in 1st or 2nd half of scan, so,
            e.g., both animal blocks might be early or late in scan
    Motor mapping cues (5 body parts) are presented at fixation
        Timing is independent of sweeping bars
        Each body part gets moved 4x, w/ rest at beginning and end
    Auditory cues are presented in tone sweeps
        8 cycles of 13 500msec tones in third-octaves with 1s ISI rising during 1st half of scan
        8 cycles of 13 500msec tones in third-octaves with 1s ISI rising during 1st half of scan
        Set to 70dB SPL as long as the Sensimetric knob is a bit below the lowest dot
        10s rest at beginning and end means 324 - 2*10 - 2*104 = 96 sec quiet in middle
    If premade = True, uses premade stim from A, B, C or D directory, depending
        on date and run number entered in GUI
    If premade = False and saveFrames = True, runs through and saves full-screen grabs in
        premad dir determined by date + runNo (so be careful ... will overwrite!)
    If premade = False and saveFrames = False, creates a once-in-a-lifetime experience
    If premade = True and saveFrames = True ... you're wasting time

Output file format:
    one .txt file per run
    a tab-delimited table with the following column headers:
        Condition
        Onset time
        Duration

Participants are asked to press buttons during motor task, and
    since there's not a 1:1 mapping between cue and response,
    we'll just record that as an event in a big long trial.
    
Erratum: in Summer 2020 we noticed that the .txt file written by the previous
    version of the code did not correctly handle the 4 times that a body part is
    repeated in the motor task. It wrote one event marker indicating a 13s
    block, when it should have written two event markers indicating two 13 s blocks.
    As of 2021.01.21, we have corrected this error, using code written by cao
    on 2020.08.26. Older .txt files will be corrected retroactively.
    
Notes on GLM analysis:
    The visual stimuli were designed for a population receptive field-style
    analysis, which is done after an initial GLM detrends the data. To support
    a good GLM that absorbs as much variance as possible, "qRF" regressors were
    generated. qRF stands for "quadrant receptive field", although 5 regressors
    were actually generated -- a Gaussian centered on the fovea, and then a 
    large Gaussian in each visual quadrant. These generic regressors can be 
    used in a GLM to do a coarse job of absorbing variance due to visual 
    stimuli -- they use a contrast energy model to indicate when the stimuli
    were sweepeing through their respective "receptive fields". There are 4
    sets of 5 regressors -- 1 set for each of the possible sweep orders (ABCD).
    These regressors are provided in AFNI format -- lists of 'onset' times,
    with a temporal resolution of 1s, indicating all the timepoints at which
    the stimulus was inside the specified 'quadrant'. The file names indicate
    eccentricity and polar angle of the center of a Gaussian with 2-degree 
    sigma (e.g., r0.00_t0.00 is the fovea, r6.00_t0.79 is centered at 6 degrees
    eccentriciy in the upper right visual quadrant).
    

"""
from __future__ import division
from psychopy.iohub.client import launchHubServer
from psychopy import visual, event, core, gui, monitors
from psychopy.contrib import mseq
from psychopy import prefs
prefs.general['audioLib'] = ['pygame']
from psychopy import sound
from glob import glob
import os
import numpy as np
import datetime
from ctypes import *
import shutil
# geta run number and a subject ID
# and use that to pick 1 of 4 possible scans ...
subjInfo = {'ID': 'P', 'runNo': 1, 'eyetracking':['Eyelink','none','Avotec']}
infoDlg=gui.DlgFromDict(dictionary=subjInfo,
                        title='Scan Parameters',
                        order=['ID', 'runNo', 'eyetracking'],
                        tip={'ID': 'subject ID',
                             'runNo': 'first (1) or second (2) run today ...'})
premadeDirs = [os.path.join('pRFinputs', 'premadeFramesA'),
               os.path.join('pRFinputs', 'premadeFramesB'),
               os.path.join('pRFinputs', 'premadeFramesC'),
               os.path.join('pRFinputs', 'premadeFramesD')]
if infoDlg.OK:
    today = datetime.datetime.now()
    dirNo = int(((subjInfo['runNo']-1)%4 + today.day%4)%4)
    premadeDir = premadeDirs[dirNo]
    motorOrder = mseq.mseq(5, 2, 1, dirNo) + 1
else:
    print('user cancelled')
    core.quit()

dateStr = '%.4d%.2d%.2d' %(today.year, today.month, today.day)
timeStamp = '%02d%02d' %(today.hour, today.minute)
outFile = os.path.join('subjectResponseFiles', '%s_%s_%s_pRF_fMRI_run%.2d.txt' %(subjInfo['ID'],
                                                                          dateStr,
                                                                          timeStamp,
                                                                          int(subjInfo['runNo'])))

# Open outFile and write column headers to it
with open(outFile, 'w') as fid:
    fid.write('Condition\tOnset\tDuration\n')

#have to initiate iohub BEFORE opening visual.Window
#https://discourse.psychopy.org/t/iohub-doesnt-work-when-theres-a-fullscreen-window/2923/4
if subjInfo['eyetracking'] is 'Eyelink':
    #set up eyetracker communications
    iohub_tracker_class_path = 'eyetracker.hw.sr_research.eyelink.EyeTracker'
    eyetracker_config = dict()
    eyetracker_config['name'] = 'tracker'
    eyetracker_config['model_name'] = 'EYELINK 1000 REMOTE'
    eyetracker_config['runtime_settings'] = dict(sampling_rate=500,track_eyes='BOTH')
    subjInfo['io'] = launchHubServer(**{iohub_tracker_class_path: eyetracker_config})


# need a window and clock:
win = visual.Window([1024, 768],
                    fullscr=True,
                    monitor='LocalLinear',
                    allowStencil=True,
                    units='deg',
                    screen=0, # n.b. mirror the screen
                    allowGUI=False)
clock = core.Clock()
nowTime = clock.getTime()
trigger = ['5', 't']
quitKeys = ['escape']
responseKeys = ['r', 'g', 'b', 'y', '1', '2', '3', '4']
minR = 1.
maxR = 8. # this is an approximate size, selected to create stimuli
          # that nicely fill a 1024x768 image and a made-up monitor
          # calibration
frameRate = 12 # Hz ... fastest we'll see

preMade =True
if preMade:
    print('Reading frames from %s' %premadeDir)
saveFrames = False
if saveFrames:
#    print('Saving frames to %s' %premadeDir)
    print("We have passed the point where we're willing to re-make frames!")
    core.exit()

# for now, we want flexibility for all sorts of stim
if not preMade:
    # cao Aug 30, 2017
    print("We have passed the point where we're willing to re-make frames!")
    core.exit()
    barDur = 16.
    stimSpec = [{'type': 'rest', 'w': 1., 'a':  0, 'dur': 4, 'dir': 0},
                {'type': 'bar', 'w': 1., 'a':  0, 'dur': barDur, 'dir': 1},
                {'type': 'bar', 'w': 1., 'a': 45, 'dur': barDur, 'dir': 1},
                {'type': 'bar', 'w': 1., 'a': 90, 'dur': barDur, 'dir': 1},
                {'type': 'bar', 'w': 1., 'a': 135, 'dur': barDur, 'dir': 1},
                {'type': 'bar', 'w': 1., 'a':  0, 'dur': barDur, 'dir': -1},
                {'type': 'bar', 'w': 1., 'a': 45, 'dur': barDur, 'dir': -1},
                {'type': 'bar', 'w': 1., 'a': 90, 'dur': barDur, 'dir': -1},
                {'type': 'bar', 'w': 1., 'a': 135, 'dur': barDur, 'dir': -1}]

    # we're going to control timing of the stim at the frame level
    # where frame rate is an integer divisor of the different frame
    # rates used in the experiment
    rate = [2, 12] # Hz ... had better be integer divisor of fastest
    # bar type / category / frequency
    bars = np.concatenate((np.random.permutation(8),
                           np.random.permutation(8)),
                           axis=0) + 1 # 1-8
    # category and frequency need same random order, so every
    # category appears fast and slow
    catOrder = np.random.permutation(16)
    c = []
    f = []
    for iC in range(8):
        for iF in np.random.permutation(2):
            c.append(iC)
            f.append(int(iF))
    freqs = [f[iC] for iC in catOrder]
    cats = [c[iC] for iC in catOrder]
    # create frameList, which will define the scan duration and
    # guide the stimulus drawing.
    frameList = []
    for iStim in range(len(bars)):
        # add a rest
        for iF in range(int(frameRate*stimSpec[0]['dur'])):
            frameList.append({'flip': True,
                              'stim': 0,
                              'cat':  0,
                              'phNo': iF})
        # and then the stim
        for iF in range(int(frameRate*stimSpec[int(bars[iStim])]['dur'])):
            flip = np.remainder(iF, frameRate/rate[int(freqs[iStim])]) == 0.
            frameList.append({'flip': flip,
                              'stim': int(bars[iStim]),
                              'cat':  int(cats[iStim]),
                              'phNo': iF})
    # one more rest at the end ...
    for iF in range(int(frameRate*stimSpec[0]['dur'])):
        frameList.append({'flip': True,
                          'stim': 0,
                          'cat':  0,
                          'phNo': iF})

    # the only way I can think to control location is make a list ahead of
    # time on allowed locations
    x, y = np.meshgrid(np.arange(-maxR, maxR, 0.5),
                       np.arange(-maxR, maxR, 0.5),
                       indexing='xy')
    rMask = np.sqrt(x**2 + y**2) <= maxR
    stimPositions = [[]] # a blank for Rest type
    stimCenters = [[]]
    for iStim in range(1, len(stimSpec)):
        nPhases = int(stimSpec[iStim]['dur']*frameRate)
        # start by rotating coordinate system depending on bar angle
        cos_a = np.cos(np.pi/180*stimSpec[iStim]['a'])
        sin_a = np.sin(np.pi/180*stimSpec[iStim]['a'])
        R = np.array([[cos_a, -sin_a],[sin_a, cos_a]])
        newXY = R.dot([x.ravel(), y.ravel()])
        stimPositions.append([])
        stimCenters.append([])
        for ph in range(nPhases):
            if stimSpec[iStim]['dir'] == 1:
                # vertical bar, left to right
                minX = -maxR - stimSpec[iStim]['w']/2 + 2*maxR*ph/nPhases
                maxX = minX + stimSpec[iStim]['w']
                mask = rMask.ravel()*(newXY[0,:] > minX)*(newXY[0,:] < maxX)
                coords = [x.ravel()[mask], y.ravel()[mask]]
            elif stimSpec[iStim]['dir'] == -1:
                # vertical bar, left to right
                minX = maxR - stimSpec[iStim]['w']/2 - 2*maxR*ph/nPhases
                maxX = minX + stimSpec[iStim]['w']
                mask = rMask.ravel()*(newXY[0,:] > minX)*(newXY[0,:] < maxX)
                coords = [x.ravel()[mask], y.ravel()[mask]]
            # now ... increase frequency proportional to 1/r
            r = np.sqrt(coords[0]**2 + coords[1]**2)
            fixedCoords = []
            for iR in range(len(r)):
                if r[iR] > 0.:
                    for iX in range(min(int(maxR/r[iR]), 6)):
                        fixedCoords.append((coords[0][iR], coords[1][iR]))
            stimPositions[-1].append(fixedCoords)
            stimCenters[-1].append([np.mean(coords[0]), np.mean(coords[1])])
    # we come out of that with a nStim x nPhases list of possible positions
    # for images
    # visual objects
    stimDir = 'pRFinputs'
    categories = ['noise',
                  'object',
                  'place',
                  'food',
                  'animal',
                  'animal_face',
                  'body',
                  'face']
    # details about display
    stimSampleRate = .05 # density of stimuli
    # name my stimuli ahead of time, but draw them realtime later
    msg = visual.TextStim(win, 'Loading stimuli', pos=(0,0))
    msg.draw()
    win.flip()

    stimList = []
    for iC, category in enumerate(categories):
        stimList.append([])
        imageList = glob(os.path.join(stimDir, 'hmIT_'+category, '*.png'))
        for img in imageList:
            stimList[iC].append(visual.ImageStim(win,
                                                img,
                                                units='deg',
                                                size=(2,2),
                                                pos=(0,0)))
else:
    # name my stimuli ahead of time, but draw them realtime later
    msg = visual.TextStim(win, 'Loading stimuli', pos=(0,0))
    msg.draw()
    win.flip()
    frameList = glob(os.path.join(premadeDir, 'frame*.png'))
    # if we need it, here's the logic for loading all the frames ahead of time
#    frameList = []
#    for iF, frame in enumerate(readyFrames):
#        if iF%100 == 0:
#            print('Frame %d of %d' %(iF, len(readyFrames)))
#        frameList.append(visual.ImageStim(win,
#                                          frame,
#                                          units='pix',
#                                          size=(1024, 768),
#                                          pos=(0,0)))
    # and specify the correct design information
    tempFrequencies = ['2Hz', '12Hz']
    objectCategories = ['human faces',
                        'animal faces',
                        'human bodies',
                        'animal bodies',
                        'food',
                        'objects',
                        'places',
                        'noise']
    barDirections = ['E to W',
                     'NE to SW',
                     'N to S',
                     'NW to SE',
                     'W to E',
                     'SW to NE',
                     'S to N',
                     'SE to NW']
    barDuration = 16.
    sweepOnsetFrames = range(48, 3888, 240)
    stimDictList = [{'directions': [7,4,0,2,1,6,7,3,3,2,6,1,5,7,4,0],
                     'categories': [1,4,3,5,0,6,3,2,0,7,2,4,6,5,1,7],
                     'frequencies': [1,1,0,0,0,0,1,0,1,0,1,0,1,1,0,1]},
                    {'directions': [0,6,7,4,3,2,1,5,0,4,3,7,5,1,6,2],
                     'categories': [0,7,5,4,7,3,4,0,3,5,2,2,6,1,1,6],
                     'frequencies': [0,0,0,1,1,0,0,1,1,1,1,0,1,0,1,0]},
                    {'directions': [1,7,6,2,0,5,4,3,0,3,2,6,1,4,5,7],
                     'categories': [4,4,7,6,3,2,0,5,7,3,5,1,0,2,1,6],
                     'frequencies': [0,1,1,0,0,0,1,0,0,1,1,1,0,1,0,1]},
                    {'directions': [4,0,3,7,1,2,5,6,5,4,1,3,0,6,2,7],
                     'categories': [4,5,0,6,2,6,4,7,3,1,0,3,2,7,5,1],
                     'frequencies': [0,0,0,0,0,1,1,1,0,1,1,1,1,0,1,0]}]
    visualCategories = []
    for iF in range(len(sweepOnsetFrames)):
        label = '%s, %s, %s' %(objectCategories[stimDictList[dirNo]['categories'][iF]],
                               tempFrequencies[stimDictList[dirNo]['frequencies'][iF]],
                               barDirections[stimDictList[dirNo]['directions'][iF]])
        visualCategories.append(label)

print('len(frameList): %d' %len(frameList))
print('Scan duration:  %2.2f seconds' %(len(frameList)/frameRate))

# sound stimuli -- no design, just cycle through
# wav files generated by http://www.audiocheck.net/audiofrequencysignalgenerator_sinetone.php
soundDuration = 0.5
soundISI = 1.
soundFiles = ['pRFinputs/auditoryCues/audiocheck.net_sin_250Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_315Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_400Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_500Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_630Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_800Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_1000Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_1250Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_1600Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_2000Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_2500Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_3150Hz_-3dBFS_.5s.wav',
              'pRFinputs/auditoryCues/audiocheck.net_sin_4000Hz_-3dBFS_.5s.wav']
soundCycles = 8 # 8 up, 8 down ...
soundFrequencies = [250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000]
soundVolumes = [ 0.88,  0.88,  0.88,  0.77,  0.55,  0.22,  0.11,  0.11,  0.22, 0.33,  0.33,  0.22,  0.22]
soundDelay = 10. # seconds from the start or end of scan
soundList = []
for soundFile in soundFiles:
    soundList.append(sound.Sound(soundFile, secs=soundDuration, sampleRate=44100))  # sample rate ignored because already set

# motor stimuli
cues = ['right_fingers', 'tongue', 'left_fingers', 'left_toes', 'right_toes']
motor = [visual.TextStim(win, '+', pos=(0, 0))]
for cue in cues:
    cueFile = os.path.join('pRFinputs', 'motorCues', '%s.png'  %cue)
    motor.append(visual.ImageStim(win,
                                  cueFile,
                                  pos=(0,0),
                                  size=minR))


# set up timing for motor task
motorDuration = int(len(frameList)/frameRate/len(motorOrder))
print('motorDuration: %d' %motorDuration)

motTaskFrames = motorDuration*len(motorOrder)*frameRate
extraFrames = len(frameList) - motTaskFrames
motFrameList = [0 for f in range(int(extraFrames/2))]
motRate = 1. # Hz tapping, 50% duty cycle stim
for iM in motorOrder:
    for iF in range(motorDuration*frameRate):
        if (iF%frameRate < 0.5*motRate*frameRate) and (iF < (motorDuration-1)*frameRate):
            motFrameList.append(iM)
        else:
            motFrameList.append(0)
for iF in range(len(motFrameList), len(frameList)+1):
    motFrameList.append(0)
print('len(motFrameList): %d' %len(motFrameList))

# here's the logic for wedge stim if we add them back in

#    minPhi = math.floor(iF/stimHz)*((2*np.pi/24)%(2*np.pi))
#    maxPhi = minPhi + np.pi/4
#    # ... including masking wedge
#    wedgeMin = (180/(np.pi)*maxPhi)%360
#    wedgeMax = (180/(np.pi)*minPhi)%360
#    if wedgeMax == 0:
#        wedgeMax = 360

# I'll draw them in roughly the right place, but then mask
# create clean edges, so here are the masks we'll draw

fixationClearSpace = visual.GratingStim(win,
                                        tex='sin',
                                        mask='raisedCos',
                                        pos=[0,0],
                                        units = 'deg',
                                        size=2.*minR,
                                        sf = 2,
                                        contrast=0.0)
rectMask = visual.GratingStim(win,
                              tex='sin',
                              mask=np.ones((int(2*maxR), int(2.2*maxR))),
                              pos=[0,0],
                              units = 'deg',
                              size=(2*maxR, 2.2*maxR),
                              sf = 2,
                              contrast=0.0)
#A non-square circle mask
hw = (win.size[0]/2, win.size[1]/2)
# convert to degrees
degWide = np.arctan(win.scrWidthCM/2./win.scrDistCM)*180/np.pi
ppd = hw[0]/degWide
x, y = np.meshgrid(np.arange(-hw[0], hw[0]),
                             np.arange(-hw[1], hw[1]),
                             indexing='xy')
rMask = 2.*(np.sqrt(x**2 + y**2)/ppd >= maxR) - 1.
circleMask = visual.GratingStim(win,
                                tex='sin',
                                mask=rMask,
                                pos=[0,0],
                                units='pix',
                                size=win.size,
                                sf = 2,
                                contrast=0.0)

msg=visual.TextStim(win, pos=[0,0], text='Scan will begin soon.')

###########################################################################################
#set up eyetracker stuff
#ANG 20171211
if subjInfo['eyetracking'] is 'Avotec':
    #
    #  -------- Constants (see file vpx.h for full listing)  --------
    #
    VPX_STATUS_ViewPointIsRunning = 1
    EYE_A = 0
    EYE_B = 1
    VPX_DAT_FRESH = 2

    #
    #  -------- Load the Mac ViewPoint dynamic library and initialize it  --------
    #

    vpxDll = "/usr/local/lib/libvpx_interapp.dylib"	# <<<< CHANGE AS NEEDED
    if ( not os.access(vpxDll,os.F_OK) ):
        print("WARNING: Invalid vpxDll path; you need to edit the .py file")
    cdll.LoadLibrary( vpxDll )
    vpx = CDLL( vpxDll )
    initializeResult = vpx.VPX_so_init()
    if ( initializeResult == 0 ):
        print("Successfully initialized dylib.")
    else:
        print("There was a problem initializing the Mac ViewPoint dynamic library")

    #
    #  -------- Make Ethernet connection to the ViewPoint EyeTracker  --------
    #

    connectResult = vpx.VPX_ConnectToViewPoint( '134.84.19.212'.encode('ascii'), 5000 )	 # <<<< CHANGE AS NEEDED
    if ( connectResult == 0 ):
        print("Successfully  connected to ViewPoint.")
    else:
        print("There was a problem making an Ethernet connection to ViewPoint")

    vpx.VPX_SendCommand('say "Hello from Mac Python" '.encode('ascii'))





    #
    #  -------- Create needed structures for variables  --------
    #
    class RealPoint(Structure):
        _fields_ = [("x",c_float),("y",c_float)]

    VPX_funcRealPoint2 = CFUNCTYPE( c_int, c_int, POINTER(RealPoint) )

    #
    vpxGetGazePoint2 = VPX_funcRealPoint2( vpx.VPX_GetGazePointCorrected2 )
    #####ANG ADDED this line to create the "helper function" to be able to "call" the getCalibrationStimulusPoint function
    ###I don't understand what this line is doing .... but this worked
    vpxGetCalibrationStimulusPoint = VPX_funcRealPoint2( vpx.VPX_GetCalibrationStimulusPoint )

    	# Need to declare a RealPoint variable
    gpA = RealPoint(1.1,1.1)
    ####ANG added a second variable for calibration .. not sure we need this, but I added it when I couldn't get the getCalStimPoint
    #to work and I was trying random stuff
    calA=RealPoint(1.1,1.1)
    #
    #  -------- Loop  --------
    #			?? For some reason, methods appear to return 0 the first time they are called.
    #
    print( "ViewPoint running: ", vpx.VPX_GetStatus(VPX_STATUS_ViewPointIsRunning) )



    #####ANG added calibration to their demo

    ###everything below here added by ANG

    # run calibration ....  by hand ... copied from matlab demo

    calDot=visual.Circle(win,radius=0.025,units='norm',
            fillColor=(-1,-1,-1),fillColorSpace='rgb')

    mymon = monitors.Monitor('LocalLinear')
    screenSize = mymon.getSizePix()
    screenDist=mymon.getDistance()
    screenWidth=mymon.getWidth()
    #set up the screen geometry so the gaze data are in useful coordinates
    mymsg='geoViewDistance %d'%screenDist
    vpx.VPX_SendCommand(mymsg.encode('ascii'))
    mymsg='geoHorizontalMeasure %d'%screenWidth*10
    vpx.VPX_SendCommand(mymsg.encode('ascii'))
    screenHeight=screenSize[1]/screenSize[0]*screenWidth*10
    mymsg='geoVerticalMeasure %d'%screenHeight
    vpx.VPX_SendCommand(mymsg.encode('ascii'))

    #adjust the calibration area for magnet
    #0-1.0 for LTRB
    mymsg='calibration_RealRect 0.3 0.3 0.7 0.7'
    vpx.VPX_SendCommand(mymsg.encode('ascii'))


    #open a data file with a unique name
    mydataFile='%s_pRF_run%s_%s_%s_eyetracking.txt' %(subjInfo['ID'],
                                                                subjInfo['runNo'],
                                                                dateStr,
                                                                timeStamp)
    mycmd='dataFile_NewName "'+mydataFile+'"'
    vpx.VPX_SendCommand(mycmd.encode('ascii'))
    #recording starts automatically

    runCal = True
    while runCal is True:
        msg.text="Operator, press c to start eyetracker calibration or m to move on"
        msg.draw()
        win.flip()

        thisKey=None
        while thisKey==None:
            thisKey = event.waitKeys()
        thisKey=thisKey[0]
        if thisKey in quitKeys:
            core.quit() #abort
        else:
            event.clearEvents()
        if thisKey =='m':
            runCal = False
        elif thisKey == 'c':
            npoints=12
            mycmd='calibration_points %d'%npoints

            vpx.VPX_SendCommand(mycmd.encode('ascii'))
            vpx.VPX_SendCommand('calibration_snapMode ON'.encode('ascii'))
            vpx.VPX_SendCommand('calibration_autoIncrement ON'.encode('ascii'))
            # You can adjust the calibration area within which the calibration stimulus
            # points are presented.  See ViewPoint pdf manual chapter 16.9.26.
            # vpx_SendCommandString('calibrationRealRect 0.2 0.2 0.8 0.8');

            calDataKeep=np.zeros((npoints,4))

            calPoints=np.arange(npoints)
            #np.random.shuffle(calPoints)
            for iPoint,thisPoint in enumerate(calPoints):
                print('step %d, getting cal point %d'%(iPoint,thisPoint))
                #get the location of the next stimulus point
                #copied from the matlab wrapper function  function [xstimpoint, ystimpoint]=vpx_GetCalibrationStimulusPoint(ixPt)

                vpxGetCalibrationStimulusPoint(thisPoint+1,calA)#normalized units (0 to 1)
                print('calibration point returned from Arrington')
                print(calA.x,calA.y)
                calDataKeep[iPoint,0]=calA.x
                calDataKeep[iPoint,1]=calA.y
                #convert to psychopy's normalized units (-1 to +1, y is inverted compared to arrington)
                x=2*calA.x-1
                y=-1*(2*calA.y-1)
                print('drawing dot at psychopy coordinates')
                print(x,y)
                calDataKeep[iPoint,2]=x
                calDataKeep[iPoint,3]=y

                calDot.pos=(x,y)
                calDot.draw()
                win.flip()
                core.wait(20*(1/60.0+0.05))
                win.flip()
                print('sending calibration snap command')
                mymsg='calibration_snap %d'%(thisPoint+1)
                vpx.VPX_SendCommand(mymsg.encode('ascii'))
                calDot.draw()
                win.flip()
                core.wait(19*(1/60.0+0.05))
                win.flip()
                core.wait(0.2)
elif subjInfo['eyetracking'] is 'Eyelink':
    #commenting out communication startup--must be done before visual.Window is opened
#    #set up eyetracker communications
#    iohub_tracker_class_path = 'eyetracker.hw.sr_research.eyelink.EyeTracker'
#    eyetracker_config = dict()
#    eyetracker_config['name'] = 'tracker'
#    eyetracker_config['model_name'] = 'EYELINK 1000 REMOTE'
#    eyetracker_config['runtime_settings'] = dict(sampling_rate=500,track_eyes='BOTH')
#    subjInfo['io'] = launchHubServer(**{iohub_tracker_class_path: eyetracker_config})
    subjInfo['tracker'] = subjInfo['io'].devices.tracker
    subjInfo['tracker'].runSetupProcedure()
    #filenames
    subjInfo['outFileNameEye']='%s_%04d%02d%02d_%02d%02d_pRF_fMRI_run%02d.edf'%(subjInfo['ID'],today.year,today.month,today.day,today.hour,today.minute,subjInfo['runNo'])
    subjInfo['outFileDirEye']=os.path.join('eyetracking',subjInfo['ID'])
    subjInfo['outFileEye']=os.path.join(subjInfo['outFileDirEye'],subjInfo['outFileNameEye'])


# get trigger from scanner #
msg=visual.TextStim(win, pos=[0,0], text='Scan will begin soon.')
msg.draw()
win.flip()
gotTrigger = None
while not gotTrigger:
    thisKey = event.waitKeys()
    gotTrigger = thisKey[0] in trigger
    if thisKey[0] in quitKeys:
        core.quit()
    else:
        event.clearEvents()
if subjInfo['eyetracking'] is 'Eyelink':
    subjInfo['tracker'].clearEvents()
    subjInfo['tracker'].setRecordingState(True)
lastType = 0
lastMotor = 0
motorTimer = 0.             # cao addition 8.28.2020 to get rid of bug
motorStart = clock.getTime()# that was resulting in .txt files that missed
                            # back-to-back motor blocks
startTime = clock.getTime()
for iF in range(len(frameList)):
    if subjInfo['eyetracking'] is 'Avotec':
        mymsg='dataFile_InsertString frame_%d_Onset'%iF
        vpx.VPX_SendCommand(mymsg)
    elif subjInfo['eyetracking'] is 'Eyelink':
        msg='frame_%d_Onset'%iF
        subjInfo['tracker'].sendMessage(msg)

    if not preMade:
        # plop all the visual stimuli up there
        iC = frameList[iF]['cat']
        iPh = frameList[iF]['phNo']
        iType = frameList[iF]['stim']
        if iType != lastType:
            print('Starting stimType %d at %2.2f' %(iType, clock.getTime()-startTime))
        lastType = iType
        if frameList[iF]['flip']:
            if iType:
                pos = []
                r = []
                imgNo = []
                # lay down a background of colorful noise by painting at
                # every 40th loc
                nb = np.random.randint(len(stimList[0]))
                stimList[0][nb].pos = (0, 0)
                stimList[0][nb].size = (2.2*maxR, 2.2*maxR)
                stimList[0][nb].draw()
                # populate a list of stim to draw
                nStim = int(stimSampleRate*len(stimPositions[iType][iPh]))
                for iS in range(nStim):
                    imgNo.append(np.random.randint(len(stimList[iC])))
                    randLoc = np.random.randint(len(stimPositions[iType][iPh]))
                    pos.append((stimPositions[iType][iPh][randLoc][0],
                                stimPositions[iType][iPh][randLoc][1]))
                    r.append(np.sqrt(pos[-1][0]**2 + pos[-1][1]**2))
                # sort them so more foveal ones are on top and draw them
                order = sorted(range(len(r)), key=r.__getitem__)
                for iS in order[-1::-1]:
                    stimList[iC][imgNo[iS]].pos = pos[iS]
                    stimList[iC][imgNo[iS]].size = (max(r[iS]/2., 2.),
                                                    max(r[iS]/2., 2.))
                    stimList[iC][imgNo[iS]].draw()
                # clean up edges
                circleMask.draw()
                dX = (maxR + 0.5*stimSpec[iType]['w'])*np.cos(-stimSpec[iType]['a']*np.pi/180)
                dY = (maxR + 0.5*stimSpec[iType]['w'])*np.sin(-stimSpec[iType]['a']*np.pi/180)
                rectMask.pos = (stimCenters[iType][iPh][0] - dX,
                                stimCenters[iType][iPh][1] - dY)
                rectMask.ori = stimSpec[iType]['a']
                rectMask.draw()
                rectMask.pos = (stimCenters[iType][iPh][0] + dX,
                                stimCenters[iType][iPh][1] + dY)
                rectMask.ori = stimSpec[iType]['a']
                rectMask.draw()
        # protect some fixation space
        fixationClearSpace.draw()
    else:
        # put up premade frame
        stim = visual.ImageStim(win,
                                os.path.join(premadeDir, 'frame%.4d.png' %iF),
                                units='pix',
                                size=(1024, 768),
                                pos=(0,0))
        stim.draw()
    if saveFrames:
        if frameList[iF]['flip']:
            win.getMovieFrame(buffer='back')
        else:
            win.getMovieFrame(buffer='front')
        win.saveMovieFrames(os.path.join(premadeDir, 'frame%.4d.png' %iF))
    else:
        #now put the motor cue there
        thisMotor = motFrameList[iF]
        motorTimer = clock.getTime() - motorStart
        # cao 8.28.2020 changing logic for motor block start
        newMotor = (thisMotor != lastMotor) or (motorTimer > 13.)
        if thisMotor and newMotor: #thisMotor and (thisMotor != lastMotor):
            print('Writing motor cue %s to %s' %(cues[thisMotor-1], outFile))
            with open(outFile, 'a') as fid:
                fid.write('%s\t%2.2f\t%2.2f\n' %(cues[thisMotor-1],
                                                clock.getTime()-startTime,
                                                motorDuration))
            lastMotor = motFrameList[iF]
            motorStart = clock.getTime() # cao 8.28.2020 addition
        motor[motFrameList[iF]].draw()
    while (clock.getTime()-startTime) < (iF/frameRate):
        pass
    if preMade:
        win.flip()
    else:
        if frameList[iF]['flip']:
            win.flip()
    if iF in sweepOnsetFrames:
        idx = [iO for iO, onsetTime in enumerate(sweepOnsetFrames) if onsetTime == iF][0]
        with open(outFile, 'a') as fid:
            fid.write('%s\t%2.2f\t%2.2f\n' %(visualCategories[idx],
                                             clock.getTime()-startTime,
                                             barDuration))
        print('%s beginning at %2.2f' %(visualCategories[idx], clock.getTime()-startTime))
    if len(event.getKeys(['escape'])):
        if subjInfo['eyetracking'] is 'Eyelink':
            #close the communication
            subjInfo['tracker'].setConnectionState(False)
            #shut down the iohub engine
            subjInfo['io'].quit()
            # check if eyetracking subdir exists
            if not os.path.isdir(subjInfo['outFileDirEye']): 
                os.makedirs(subjInfo['outFileDirEye']) 
            #rename the EDF file
            shutil.copy2('et_data.EDF',subjInfo['outFileEye'])
        core.quit()
    if iF%(soundISI*frameRate) == 0: # new tone every soundISI
        if (iF > frameRate*soundDelay) and (iF < frameRate*(soundDelay+len(soundFrequencies)*soundISI*soundCycles)):
            # keep it quiet for 10s, then play 8 cycles up if it's run 1 and down if 2
            # If you change this logic, change the info that's written to the .txt file!
            if int(subjInfo['runNo'])%2 == 0:
                iSound = int(iF/(soundISI*frameRate))%len(soundList)
            else:
                iSound = int((len(frameList)-frameRate*soundDelay-iF)/(soundISI*frameRate))%len(soundList)
            soundList[iSound].setVolume(soundVolumes[iSound])
            print('Sound %d' %iSound)
            with open(outFile, 'a') as fid:
                fid.write('%d\t%2.2f\t%2.2f\n' %(soundFrequencies[iSound],
                                                clock.getTime()-startTime,
                                                soundDuration))
            soundList[iSound].play()
        elif (iF < len(frameList)-frameRate*soundDelay) and \
              (iF > len(frameList)-frameRate*(soundDelay+len(soundFrequencies)*soundISI*soundCycles)):
            if int(subjInfo['runNo'])%2 == 0:
                iSound = int((len(frameList)-frameRate*soundDelay-iF)/(soundISI*frameRate))%len(soundList)
            else:
                iSound = int(iF/(soundISI*frameRate))%len(soundList)
            soundList[iSound].setVolume(soundVolumes[iSound])
            print('Sound %d' %iSound)
            with open(outFile, 'a') as fid:
                fid.write('%d\t%2.2f\t%2.2f\n' %(soundFrequencies[iSound],
                                                clock.getTime()-startTime,
                                                soundDuration))
            soundList[iSound].play()
    # and check for an escape key ...
    thisKey = event.getKeys()
    if thisKey:
        if thisKey[0] in quitKeys:
            if subjInfo['eyetracking'] is 'Avotec':
                #close the data file
                vpx.VPX_SendCommand('dataFile_Close'.encode('ascii'))

                #close link to eyetracker
                connectResult = vpx.VPX_DisconnectFromViewPoint()
                print('finished successfully!')
            elif subjInfo['eyetracking'] is 'Eyelink':
                #close the communication
                subjInfo['tracker'].setConnectionState(False)
                #shut down the iohub engine
                subjInfo['io'].quit()
                # check if eyetracking subdir exists
                if not os.path.isdir(subjInfo['outFileDirEye']): 
                    os.makedirs(subjInfo['outFileDirEye']) 
                #rename the EDF file
                shutil.copy2('et_data.EDF',subjInfo['outFileEye'])
            core.quit()
        elif thisKey[0] in responseKeys:
            print('Button press %s at %2.2f' %(thisKey[0], clock.getTime()-startTime))
            with open(outFile, 'a') as fid:
                fid.write('%s\t%2.2f\t \n' %(thisKey[0],
                                                clock.getTime()-startTime))


print('Actual scan time:  %2.2f' %(clock.getTime()-startTime))
if subjInfo['eyetracking'] is 'Avotec':
    #close the data file
    vpx.VPX_SendCommand('dataFile_Close'.encode('ascii'))

    #close link to eyetracker
    connectResult = vpx.VPX_DisconnectFromViewPoint()
    print('finished successfully!')
elif subjInfo['eyetracking'] is 'Eyelink':
    #close the communication
    subjInfo['tracker'].setConnectionState(False)
    #shut down the iohub engine
    subjInfo['io'].quit()
    # check if eyetracking subdir exists
    if not os.path.isdir(subjInfo['outFileDirEye']): 
        os.makedirs(subjInfo['outFileDirEye']) 
    #rename the EDF file
    shutil.copy2('et_data.EDF',subjInfo['outFileEye'])
win.close()
core.quit()
