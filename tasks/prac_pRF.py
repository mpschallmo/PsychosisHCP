#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Code made by Schallmo, MP based on code from Olman, CA
2017/10/10

Runs a practice version of the pRF code, which explains the motor task, then adds auditory and pRF stimuli.

Information below copied from pRF.py

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
    
"""

from __future__ import division
from psychopy import visual, event, core, gui
from psychopy.contrib import mseq
from psychopy import prefs
prefs.general['audioLib'] = ['pygame']
from psychopy import sound
from glob import glob
import os
import numpy as np
import datetime

from psychopy.hardware import crs

try:
    win=visual.Window([1920, 1200],monitor="BitsSharp",units='deg',screen=0,useFBO=True,fullscr=True)
    bits = crs.BitsSharp(win=win, mode='bits++')
    bits.gammaCorrectFile='greyLums.txt'
    bits.mode='bits++'
    core.wait(0.2)
    win.close()
except:
    print('No Bits# found, skipping...')
    win.close()

soundVolume = .2
# geta run number and a subject ID
# and use that to pick 1 of 4 possible scans ...
subjInfo = {'ID': 'P', 'runNo': 1} 
infoDlg=gui.DlgFromDict(dictionary=subjInfo,
                        title='Scan Parameters',
                        order=['ID', 'runNo'],
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
# outFile = os.path.join('subjectResponseFiles', '%s_pRF_prac%s_%s_%s.txt' %(subjInfo['ID'],
#                                                             subjInfo['runNo'],
#                                                             dateStr,
#                                                             timeStamp))
outFile = os.path.join('subjectResponseFiles', '%s_%s_%s_pRF_prac_run%.2d.txt' %(subjInfo['ID'],
                                                                          dateStr,
                                                                          timeStamp,
                                                                          int(subjInfo['runNo'])))

# Open outFile and write column headers to it
with open(outFile, 'w') as fid:
    fid.write('Condition\tOnset\tDuration\n')

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

# want to put the instructions & practice in here 
# cues = ['right_fingers', 'tongue', 'left_fingers', 'left_toes', 'right_toes']

msg=visual.TextStim(win, pos=[0,0], text='This is a tapping task. You will tap your fingers, toes, and tongue.')
msg.draw()
win.flip()
gotKey = None
while not gotKey:
    thisKey = event.waitKeys()
    gotKey = thisKey[0] in responseKeys
    if thisKey[0] in quitKeys:
        core.quit()
    else:
        event.clearEvents()

msg=visual.TextStim(win, pos=[0,0], text='Please keep your eyes at the middle of the screen the whole time.')
msg.draw()
win.flip()
gotKey = None
while not gotKey:
    thisKey = event.waitKeys()
    gotKey = thisKey[0] in responseKeys
    if thisKey[0] in quitKeys:
        core.quit()
    else:
        event.clearEvents()

msg=visual.TextStim(win, pos=[0,0], text='Here are the cues for tapping each body part.')
msg.draw()
win.flip()
gotKey = None
while not gotKey:
    thisKey = event.waitKeys()
    gotKey = thisKey[0] in responseKeys
    if thisKey[0] in quitKeys:
        core.quit()
    else:
        event.clearEvents()

# cues = ['right_fingers', 'tongue', 'left_fingers', 'left_toes', 'right_toes']
cueLabels = ['right hand','tongue','left hand','left foot','right foot']
cueOrder = [1, 3, 5, 4, 2] # right hand, left hand, right foot, left foot, tongue
startBlank = 1
for iCue in cueOrder:
	startTime = clock.getTime()
	motor[0].draw()
	win.flip()
	while (clock.getTime()-startTime) < startBlank:
		waiting = 1 # do nothing
	motor[iCue].draw()
	msg=visual.TextStim(win, pos=[0,1.5], text=cueLabels[iCue-1])
	msg.draw()
	win.flip()
	gotKey = None
	while not gotKey:
		thisKey = event.waitKeys()
		gotKey = thisKey[0] in responseKeys
		if thisKey[0] in quitKeys:
			core.quit()
		else:
			event.clearEvents()


# start with no sound or pRF pictures
commandList = ['press the red button','tap your tongue to the roof of your mouth','press the blue button','scrunch your left foot','scrunch your right foot']
# cues = ['right_fingers', 'tongue', 'left_fingers', 'left_toes', 'right_toes']
cueOrder = [3, 1, 2, 5, 4]
motRate = 1. # Hz tapping, 50% duty cycle stim
startBlank = 2
exDuration = 13

for iCue in cueOrder:
#for iCue in [1]: # only for testing
	msg=visual.TextStim(win, pos=[0,0],
		text='Next you will see a blinking ' + cueLabels[iCue-1] + '. Every time it blinks, ' + commandList[iCue-1] + '.')
	msg.draw()
	win.flip()
	gotKey = None
	while not gotKey:
	    thisKey = event.waitKeys()
	    gotKey = thisKey[0] in responseKeys
	    if thisKey[0] in quitKeys:
	        core.quit()
	    else:
	        event.clearEvents()

	exFrameList = [0 for f in range(startBlank*frameRate)]
	for iF in range(exDuration*frameRate):
	    if (iF%frameRate < 0.5*motRate*frameRate) and (iF < (exDuration-1)*frameRate):
	        exFrameList.append(iCue)
	    else:
	        exFrameList.append(0)

	startTime = clock.getTime()
	lastMotor = 0
	for iF in range(len(exFrameList)):
		#now put the motor cue there
		thisMotor = exFrameList[iF]
		if thisMotor and (thisMotor != lastMotor):
			print('Writing motor cue %s to %s' %(cues[thisMotor-1], outFile))
			with open(outFile, 'a') as fid:
				fid.write('%s\t%2.2f\t%2.2f\n' %(cues[thisMotor-1],
					clock.getTime()-startTime,motorDuration))
			lastMotor = exFrameList[iF]
		motor[exFrameList[iF]].draw()
		while (clock.getTime()-startTime) < (iF/frameRate):
			pass
		win.flip()
		# and check for an escape key ...
		thisKey = event.getKeys()
		if thisKey:
			if thisKey[0] in quitKeys:
				core.quit()
			elif thisKey[0] in responseKeys:
				print('Button press %s at %2.2f' %(thisKey[0], clock.getTime()-startTime))
				with open(outFile, 'a') as fid:
					fid.write('%s\t%2.2f\t \n' %(thisKey[0],
						clock.getTime()-startTime))




# add in the sounds (descending order to start)
msg=visual.TextStim(win, pos=[0,0],
	text='Now you will do the same task again. You will also hear sounds. Ignore the sounds and do the tapping task.')
msg.draw()
win.flip()
gotKey = None
while not gotKey:
    thisKey = event.waitKeys()
    gotKey = thisKey[0] in responseKeys
    if thisKey[0] in quitKeys:
        core.quit()
    else:
        event.clearEvents()

# cues = ['right_fingers', 'tongue', 'left_fingers', 'left_toes', 'right_toes']
cueOrder = [4, 2]
exFrameList = []
for iCue in cueOrder:
	exFrameList.extend([0 for f in range(startBlank*frameRate)])
	for iF in range(exDuration*frameRate):
	    if (iF%frameRate < 0.5*motRate*frameRate) and (iF < (exDuration-1)*frameRate):
	        exFrameList.append(iCue)
	    else:
	        exFrameList.append(0)

startTime = clock.getTime()
lastMotor = 0
for iF in range(len(exFrameList)):
	#now put the motor cue there
	thisMotor = exFrameList[iF]
	if thisMotor and (thisMotor != lastMotor):
		print('Writing motor cue %s to %s' %(cues[thisMotor-1], outFile))
		with open(outFile, 'a') as fid:
			fid.write('%s\t%2.2f\t%2.2f\n' %(cues[thisMotor-1],
				clock.getTime()-startTime,motorDuration))
		lastMotor = exFrameList[iF]
	motor[exFrameList[iF]].draw()
	while (clock.getTime()-startTime) < (iF/frameRate):
		pass
	win.flip()

	# add sounds
	if (iF%(soundISI*frameRate) == 0) & (iF > frameRate*startBlank): # new tone every soundISI
		iSound = int((len(exFrameList)-frameRate*startBlank-iF)/(soundISI*frameRate))%len(soundList)
		soundList[iSound].setVolume(soundVolumes[iSound])
		print('Sound %d' %iSound)
		with open(outFile, 'a') as fid:
			fid.write('%d\t%2.2f\t%2.2f\n' %(soundFrequencies[iSound],clock.getTime()-startTime,soundDuration))
		soundList[iSound].play()

	# and check for an escape key ...
	thisKey = event.getKeys()
	if thisKey:
		if thisKey[0] in quitKeys:
			core.quit()
		elif thisKey[0] in responseKeys:
			print('Button press %s at %2.2f' %(thisKey[0], clock.getTime()-startTime))
			with open(outFile, 'a') as fid:
				fid.write('%s\t%2.2f\t \n' %(thisKey[0],
					clock.getTime()-startTime))



# add in the pictures and sounds (ascending order now)
msg=visual.TextStim(win, pos=[0,0],
	text='Now you will do the same task one more time. You will hear sounds and see other pictures. Ignore them and do the tapping task.')
msg.draw()
win.flip()
gotKey = None
while not gotKey:
    thisKey = event.waitKeys()
    gotKey = thisKey[0] in responseKeys
    if thisKey[0] in quitKeys:
        core.quit()
    else:
        event.clearEvents()


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


# get trigger from scanner #
msg=visual.TextStim(win, pos=[0,0], text='Keep your eyes at the center the whole time. Press t to begin.')
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


lastType = 0
lastMotor = 0
startTime = clock.getTime()
for iF in range(int(len(frameList)/2)):
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
        if thisMotor and (thisMotor != lastMotor):
            print('Writing motor cue %s to %s' %(cues[thisMotor-1], outFile))
            with open(outFile, 'a') as fid:
                fid.write('%s\t%2.2f\t%2.2f\n' %(cues[thisMotor-1],
                                                clock.getTime()-startTime,
                                                motorDuration))
            lastMotor = motFrameList[iF]
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
            core.quit()
        elif thisKey[0] in responseKeys:
            print('Button press %s at %2.2f' %(thisKey[0], clock.getTime()-startTime))
            with open(outFile, 'a') as fid:
                fid.write('%s\t%2.2f\t \n' %(thisKey[0],
                                                clock.getTime()-startTime))
            
    
print('Actual scan time:  %2.2f' %(clock.getTime()-startTime))
win.close()
core.quit()

