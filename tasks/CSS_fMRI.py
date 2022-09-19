#!/usr/bin/env python2
# author: caolman, edits by mps

from psychopy.iohub.client import launchHubServer

from psychopy import visual, core, data, event, monitors, gui, misc
from psychopy.contrib import mseq
import numpy
import os, glob # primarily useful for file handling
import datetime #for getting the date and time....
from ctypes import *
import shutil

def checkResponses(expInfo, subjectResponses, thisCond):
    for key in event.getKeys(expInfo['quitKeys']+expInfo['responseKeys']):
        if key in expInfo['quitKeys']:
            with open(expInfo['outFile'],'a') as f:
                f.write('quit key detected\n')
            if expInfo['eyetracking'] is 'Avotec':
                #close the data file
                vpx.VPX_SendCommand('dataFile_Close'.encode('ascii'))
                #close link to eyetracker
                connectResult = vpx.VPX_DisconnectFromViewPoint()
                print('finished successfully!')
            elif expInfo['eyetracking'] is 'Eyelink':
                expInfo['tracker'].setRecordingState(False)
                expInfo['tracker'].setConnectionState(False)
                expInfo['io'].quit()
                #check for output dir
                if not os.path.isdir(expInfo['outFileDirEye']):
                    os.makedirs(expInfo['outFileDirEye'])
                #copy file and rename
                shutil.copy2('et_data.EDF',expInfo['outFileEye'])
            core.quit()
        elif key in expInfo['responseKeys']:
            subjectResponses.append({'response':key,
                                     'time':scanTimer.getTime(),
                                     'condition': thisCond,
                                     'dC': expInfo['staircases'][thisCond]['currentDC']})

expInfo={}
###########################################################################################
#subject information dialog
expInfo={'subject':'P', 'runNo':1, 'eyetracking':['Eyelink','none','Avotec']}

#pop a GUI to update scan info
infoDlg = gui.DlgFromDict(dictionary=expInfo,
                          title='Scan Parameters',
                          order=['subject', 'runNo', 'eyetracking'],
                          tip={'subject':'subject number'})
if infoDlg.OK:
    print(expInfo)
else:
    print('user cancelled')
    core.quit()

# check that this run hasn't already been done for this subject today
# quit if it has
nowTime = datetime.datetime.now()
checkStr = '%s_%04d%02d%02d_*_CSS_fMRI_run%.2d' %(expInfo['subject'], 
                                              nowTime.year,
                                              nowTime.month,
                                              nowTime.day,
                                              expInfo['runNo'])
checkFiles = glob.glob(os.path.join('subjectResponseFiles',
                                    checkStr + '.txt'))
if len(checkFiles) > 0:
    print('There is already a file for this runNo for this participant today.')
    print('If this is really what you want to do, delete that file and try again.')
    core.quit()

#create an output file name for saving the data later
if os.path.isdir('subjectResponseFiles') == False:
    #create directory
    os.makedirs('subjectResponseFiles')

outFileName = '%s_%04d%02d%02d_%02d%02d_CSS_fMRI_run%.2d' %(expInfo['subject'], 
                                            			nowTime.year,
                                            			nowTime.month,
                                            			nowTime.day,
                                            			nowTime.hour,
                                            			nowTime.minute,
                                            			expInfo['runNo'])
outFile = os.path.join('subjectResponseFiles', outFileName + '.txt') 
expInfo['outFile'] = outFile

# write column headers to that output file
with open(outFile, 'w') as fid:
    fid.write('Condition\tOnsetTime\tDuration\tdC\tresponse\tcorrect\n')

###########################################################################################
#stimulus geometry
#targets (previously "centers")
expInfo['targetRadius'] = 1. #degrees
expInfo['fiducialGap'] = 0.05 # gap between edge of target grating and fiducial circle
expInfo['stimLocLeft']  = [-3, 0]
expInfo['stimLocRight' ] = [3, 0]
# surround
expInfo['surrInnerR'] = expInfo['targetRadius'] + 0.25
expInfo['surrOuterR'] = 2.*expInfo['targetRadius']
# contrasts
targetPedestals = [0., .1, .2, .4, .8]
surroundRelOrientations = [0.]
surroundContrasts = [0., 1.]

###########################################################################################
#timing
expInfo['trialDuration'] = 0.75 + 1.05 # sec
expInfo['responseTimeout'] = 0.6 # sec
expInfo['stimDuration'] = 0.75 # sec
expInfo['blockDuration'] = 9.0 # sec
expInfo['nCycles'] = 5
expInfo['tempFreq'] = 4. # Hz
expInfo['frameDuration'] = 0.5/expInfo['tempFreq']
expInfo['nFramesPerStim'] = int(expInfo['stimDuration']/expInfo['frameDuration'])

###########################################################################################
#conditions  ... first the rest, condition = 0
expInfo['conditionNames'] = ['localizer']
expInfo['pedestals'] = [0.8]
expInfo['surrRelOri'] = [0.]
expInfo['surrContrast'] = [0.]
# then the actual conditions (8 of them)
for t in targetPedestals:
    # this surround orientation capability is in there for historic reasons
    for sro in surroundRelOrientations:
        for sc in surroundContrasts:
            expInfo['pedestals'].append(t)
            expInfo['surrRelOri'].append(sro)
            expInfo['surrContrast'].append(sc)
            condStr = 'target %d surr %d relOri %d' %(int(100*t), int(100*sc), int(sro))
            expInfo['conditionNames'].append(condStr)

# we should have a total of 11 conditions:
#  localizer, which is 80%/0%, but even, so it'll get contrasted against 0%/80% by the logic below
#  5 contrasts (including 0) x 2 surrounds
expInfo['numCond'] = len(expInfo['conditionNames'])

expInfo['targetOri']=numpy.arange(0, 180, 15)
expInfo['numOri']=len(expInfo['targetOri'])

# we want to randomize across scans, but with localizer always
# at the beginning of the first scan
possibleOrders = [[[0, 3, 10], [5, 8, 7], [9, 6, 4]],
                  [[0, 4, 9], [8, 3, 6], [5, 10, 7]],
                  [[0, 5, 8], [10, 4, 9], [3, 7, 6]],
                  [[0, 6, 7], [3, 10, 8], [9, 4, 5]]]
# pick one of those orders based on the day
# this does mean that 2 participants run on the same day
# will get the same order, but that seems tolerable
orders = possibleOrders[nowTime.day%4]
order = orders[expInfo['runNo']-1]

# now create a list that specifies every block for the scan
expInfo['blockDesign'] = []
for c in order:
    expInfo['blockDesign'].append(c)
    for b in range(expInfo['nCycles']):
        if c%2:
            # odd-numbered conditions are no-surround
            expInfo['blockDesign'].append(1)
        else:
            # even-numbered conditions are with surround
            # this creates differential localizer, too
            expInfo['blockDesign'].append(2)
        expInfo['blockDesign'].append(c)

expInfo['trialOrder'] = []
nTrialsPerBlock = int(expInfo['blockDuration']/expInfo['trialDuration'])
for iB in expInfo['blockDesign']:
    expInfo['trialOrder'] += nTrialsPerBlock*[iB]
expInfo['trialStartTimes'] = expInfo['trialDuration']*numpy.arange(0, len(expInfo['trialOrder']))

scanDuration = len(expInfo['trialOrder'])*expInfo['trialDuration']

###########################################################################################
# staircases
expInfo['rightColor'] = [0., 1., 0.]
expInfo['wrongColor'] = [0., 0., 0.]
expInfo['staircases'] = []
for iC in range(expInfo['numCond']):
    maxDC = max(expInfo['pedestals'][iC]/4., .03)
    dCrange = numpy.logspace(-2, numpy.log10(maxDC), 10)
    print(dCrange)
    dCidx = int(len(dCrange)/2.)
    currentDC = dCrange[dCidx]
    expInfo['staircases'].append({'currentDC': currentDC,
                                  'dCrange': dCrange,
                                  'dCidx': dCidx,
                                  'nCorrect': 0})

###########################################################################################
# responses
expInfo['triggerKeys'] = ['t','5']
expInfo['responseKeys'] = ['r','g','b','y','1','2','3','4']
expInfo['quitKeys'] = ['q','escape']


###########################################################################################
#initiate communication with Eyelink, if using. This must be done before visual.Window is opened
if expInfo['eyetracking'] is 'Eyelink':
    #set up eyetracker communications
    iohub_tracker_class_path = 'eyetracker.hw.sr_research.eyelink.EyeTracker'
    eyetracker_config = dict()
    eyetracker_config['name'] = 'tracker'
    eyetracker_config['model_name'] = 'EYELINK 1000 REMOTE'
    eyetracker_config['runtime_settings'] = dict(sampling_rate=500,track_eyes='BOTH')
    expInfo['io'] = launchHubServer(**{iohub_tracker_class_path: eyetracker_config})


###########################################################################################
# open the subject window
# monitor
expInfo['mon'] = 'LocalCalibrated'
# There's a "feature" in Apple that is weird about full screen controls, so we
# can't use full screen on Macs ... ever.
#unless it's the primary screen, and then you have to use fullscreen to get rid of the toolbar
expInfo['subMonitor'] = monitors.Monitor(expInfo['mon'])
expInfo['screenSize'] = expInfo['subMonitor'].getSizePix()
expInfo['win'] = visual.Window(expInfo['screenSize'],
                               monitor=expInfo['mon'],
                               units='deg',
                               screen=0,
                               color=[0,0,0],
                               colorSpace='rgb',
                               fullscr=True,
                               allowGUI=False)

###########################################################################################
# create stimuli
# create a gabor patch. I can use this for both targets and both surrounds,
# by just adjusting outer radius, contrast (and mask overlay) as needed
# it's seeded w/ details for a target, but it's used for everything
expInfo['grating']=visual.GratingStim(expInfo['win'],
                                      tex='sin',
                                      mask='raisedCos',
                                      pos=expInfo['stimLocLeft'],
                                      size=2*expInfo['targetRadius'],
                                      sf=1.1,
                                      contrast=0.8,
                                      units='deg')

# dark gray circle to surround the targets (fiducial mark)
# want 15% contrast .....
expInfo['fiducialCircle']=visual.Circle(expInfo['win'],
    radius=expInfo['targetRadius']+expInfo['fiducialGap'],
    lineColor=[-0.5,-0.5,-0.5],
    lineColorSpace='rgb',
    fillColor=[0,0,0],
    fillColorSpace='rgb',
    units='deg')

# fixation mark
expInfo['fixationMark']=visual.Rect(expInfo['win'],
                                    width=0.2,
                                    height=0.2,
                                    fillColor=[1,1,1],
                                    fillColorSpace='rgb',
                                    units='deg')

# mask around fixation mark, which we need to keep the surrounds from running into each other
expInfo['fixationMask'] = visual.Rect(expInfo['win'],
                                      width = 1.9,
                                      height = 40.0,
                                      fillColor=[0,0,0],
                                      fillColorSpace='rgb',
                                      lineColor=[0,0,0],
                                      lineColorSpace='rgb',
                                      units='deg')

# a text message
longText="Scan duration: %d sec (%d min) "\
        "\n\nPress right button if right target is higher contrast."\
        "\n     Press left button if left target is higher contrast."\
        "\n\nKeep your eyes on the square in the middle."\
        "\n     It will turn green when you are getting the answer right."\
        "\n\nPress any button when ready to start." %(int(scanDuration), numpy.round(scanDuration/60.))
expInfo['textMsg']=visual.TextStim(expInfo['win'],
    text=longText,
    units='norm',
    pos=(0,0.2),
    height=0.075,
    alignVert='top',
    wrapWidth=1.9)

#a giant blank screen
expInfo['blank']=visual.Rect(expInfo['win'],
                             width=50,
                             height=40,
                             fillColor=[0,0,0],
                             fillColorSpace='rgb',
                             units='deg')


###########################################################################################
#set up eyetracker stuff
#ANG 20171211
if expInfo['eyetracking'] is 'Avotec':
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

    calDot=visual.Circle(expInfo['win'],radius=0.025,units='norm',
            fillColor=(-1,-1,-1),fillColorSpace='rgb')

    mymon = monitors.Monitor('LocalCalibrated')
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
    mydataFile='%s_CSSfMRI_run%d_%04d%02d%02d_%02d%02d_eyetracking.txt' %(expInfo['subject'],
                                                  expInfo['runNo'],
                                                  nowTime.year,
                                                  nowTime.month,
                                                  nowTime.day,nowTime.hour, nowTime.minute)
    mycmd='dataFile_NewName "'+mydataFile+'"'
    vpx.VPX_SendCommand(mycmd.encode('ascii'))
    #recording starts automatically
    runCal=True
    while runCal is True:
        expInfo['textMsg'].text="Operator, press c to start eyetracker calibration or m to move on"
        expInfo['textMsg'].draw()
        expInfo['win'].flip()
        thisKey=None
        while thisKey==None:
            thisKey = event.waitKeys()
        thisKey=thisKey[0]
        if thisKey in expInfo['quitKeys']:
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

            calDataKeep=numpy.zeros((npoints,4))

            calPoints=numpy.arange(npoints)
            #numpy.random.shuffle(calPoints)
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
                expInfo['win'].flip()
                core.wait(20*(1/60.0+0.05))
                expInfo['win'].flip()
                print('sending calibration snap command')
                mymsg='calibration_snap %d'%(thisPoint+1)
                vpx.VPX_SendCommand(mymsg.encode('ascii'))
                calDot.draw()
                expInfo['win'].flip()
                core.wait(19*(1/60.0+0.05))
                expInfo['win'].flip()
                core.wait(0.2)
elif expInfo['eyetracking'] is 'Eyelink':
    #iohub must be launched before visual.window is opened
#    #set up eyetracker communications
#    iohub_tracker_class_path = 'eyetracker.hw.sr_research.eyelink.EyeTracker'
#    eyetracker_config = dict()
#    eyetracker_config['name'] = 'tracker'
#    eyetracker_config['model_name'] = 'EYELINK 1000 REMOTE'
#    eyetracker_config['runtime_settings'] = dict(sampling_rate=500,track_eyes='BOTH')
#    expInfo['io'] = launchHubServer(**{iohub_tracker_class_path: eyetracker_config})
    expInfo['tracker'] = expInfo['io'].devices.tracker
    #set up output file names
    expInfo['outFileNameEye']='%s_%04d%02d%02d_%02d%02d_CSS_fMRI_run%02d.edf'%(expInfo['subject'],
        nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute,expInfo['runNo'])
    expInfo['outFileDirEye']=os.path.join('eyetracking',expInfo['subject'])
    #check for output dir
    if not os.path.isdir(expInfo['outFileDirEye']):
        os.makedirs(expInfo['outFileDirEye'])
    expInfo['outFileEye']=os.path.join(expInfo['outFileDirEye'],expInfo['outFileNameEye'])

    #run cal
    expInfo['tracker'].runSetupProcedure()

###########################################################################################
#prepare to start the experiment
longText="Scan duration: %d sec (%d min) "\
        "\n\nPress right button if right target is higher contrast."\
        "\n     Press left button if left target is higher contrast."\
        "\n\nKeep your eyes on the square in the middle."\
        "\n     It will turn green when you are getting the answer right."\
        "\n\nPress any button when ready to start." %(int(scanDuration), numpy.round(scanDuration/60.))

expInfo['textMsg'].text=longText
expInfo['textMsg'].draw()
expInfo['win'].flip()

thisKey=None
while thisKey==None:
    thisKey = event.waitKeys()
if thisKey in expInfo['quitKeys']:
    core.quit() #abort
else:
    event.clearEvents()

if expInfo['eyetracking'] is 'Eyelink':
    expInfo['tracker'].clearEvents()
    expInfo['tracker'].setRecordingState(True)

###########################################################################################
#start trial loop
scanTimer = core.Clock()
trialTimer = core.Clock()

# wait for trigger
expInfo['textMsg'].setText('Noise coming.')
expInfo['textMsg'].draw()
expInfo['win'].flip()
gotTrigger = None
while not gotTrigger:
    thisKey = event.waitKeys()
    gotTrigger = thisKey[0] in expInfo['triggerKeys']
    if thisKey[0] in expInfo['quitKeys']:
        core.quit()
    else:
        event.clearEvents()

subjectResponses = []
scanTimer.reset()
gotResponse = numpy.zeros((len(expInfo['trialOrder']), 1))
for iT in range(len(expInfo['trialOrder'])):
    #get condition
    thisCond=expInfo['trialOrder'][iT] # trialOrder has integers 0 through 5

    #get target orientation
    thisOri = expInfo['targetOri'][numpy.random.randint(expInfo['numOri'])]

    #set target contrast and surround orientation and contrast
    tgtC = expInfo['pedestals'][thisCond]
    surrC = expInfo['surrContrast'][thisCond]
    surrOri = thisOri + expInfo['surrRelOri'][thisCond]

    # decide on task ...
    thisDC = expInfo['staircases'][thisCond]['currentDC']
    if numpy.random.random(1) > 0.5:
        whichSide = 0 # left
        leftC = tgtC + thisDC
        rightC = tgtC
        correctResponse = 'b'
    else:
        whichSide = 1
        leftC = tgtC
        rightC = tgtC + thisDC
        correctResponse = 'r'
    if expInfo['eyetracking'] is 'Avotec':
        mymsg='dataFile_InsertString Trial_%d_condition_%d_ori_%d_stimOnset'%(iT,thisCond,thisOri)
        vpx.VPX_SendCommand(mymsg)
    elif expInfo['eyetracking'] is 'Eyelink':
        msg='Trial_%d_condition_%d_ori_%d_stimOnset'%(iT,thisCond,thisOri)
        expInfo['tracker'].sendMessage(msg)
    # Draw stimulus, looping through frames for contrast reversal
    nReversals = int(2.*expInfo['stimDuration']*expInfo['tempFreq'])
    frameDur = 2./expInfo['tempFreq']*expInfo['stimDuration']
    nResponsesBefore = len(subjectResponses)
    for iF in range(nReversals):
        if iF%2:
            cMul = 1.
        else:
            cMul = -1.
        # for all conditions, draw the same sequence of stimuli:
        #left surround
        expInfo['grating'].size = expInfo['surrOuterR']*2
        expInfo['grating'].maskParams = {'fringeWidth':.25/expInfo['surrOuterR']}
        expInfo['grating'].pos = expInfo['stimLocLeft']
        expInfo['grating'].ori = surrOri
        expInfo['grating'].contrast = surrC*cMul
        expInfo['grating'].draw()

        #right surround
        expInfo['grating'].pos = expInfo['stimLocRight']
        expInfo['grating'].draw()

        #mask out the inner portion of the left surround (i.e., create an annulus)
        expInfo['grating'].size = expInfo['surrInnerR']*2
        expInfo['grating'].maskParams = {'fringeWidth':.25/expInfo['surrInnerR']}
        expInfo['grating'].pos = expInfo['stimLocLeft']
        expInfo['grating'].contrast = 0
        expInfo['grating'].draw()

        #mask out the inner portion of the right surround (i.e., create an annulus)
        expInfo['grating'].pos = expInfo['stimLocRight']
        expInfo['grating'].draw()

        #mask the fixation mark ...
        expInfo['fixationMask'].draw()

        #fiducial circles around targets
        expInfo['fiducialCircle'].pos = expInfo['stimLocLeft']
        expInfo['fiducialCircle'].draw()
        expInfo['fiducialCircle'].pos = expInfo['stimLocRight']
        expInfo['fiducialCircle'].draw()

        #target left
        expInfo['grating'].size=expInfo['targetRadius']*2
        expInfo['grating'].maskParams = {'fringeWidth':.25/expInfo['targetRadius']}
        expInfo['grating'].pos = expInfo['stimLocLeft']
        expInfo['grating'].ori = thisOri
        expInfo['grating'].contrast = leftC*cMul
        expInfo['grating'].draw()

        # target right
        expInfo['grating'].pos = expInfo['stimLocRight']
        expInfo['grating'].contrast = rightC*cMul
        expInfo['grating'].draw()

        #fixation
        expInfo['fixationMark'].draw()

        # wait for right time to start trial
        thisFrameTime = expInfo['trialStartTimes'][iT] + (iF+1)*expInfo['frameDuration']
        while scanTimer.getTime() < thisFrameTime:
            checkResponses(expInfo, subjectResponses, thisCond)
        expInfo['win'].flip()

    if expInfo['eyetracking'] is 'Avotec':
        mymsg='dataFile_InsertString Trial_%d_condition_%d_ori_%d_stimOff'%(iT,thisCond,thisOri)
        vpx.VPX_SendCommand(mymsg)
    elif expInfo['eyetracking'] is 'Eyelink':
        msg='Trial_%d_condition_%d_ori%d_stimOff'%(iT,thisCond,thisOri)
        expInfo['tracker'].sendMessage(msg)
    #draw blank screen and keep looking for responses
    expInfo['blank'].draw()
    expInfo['fixationMark'].draw()

    #fiducial circles around targets
    expInfo['fiducialCircle'].pos = expInfo['stimLocLeft']
    expInfo['fiducialCircle'].draw()
    expInfo['fiducialCircle'].pos = expInfo['stimLocRight']
    expInfo['fiducialCircle'].draw()
    expInfo['win'].flip()
    print 'Trial: %d %s, end time: %f' %(iT,
                                         expInfo['conditionNames'][thisCond],
                                         scanTimer.getTime())

    #reset clock to 0 at the beginning of each trial
    trialTimer.reset()
    #show stim for stimDuration time, then show blank screen, all while
    #looking for subject response ... there's another chance to respond after targets go away
    while trialTimer.getTime() < expInfo['stimDuration']:
        #look for responses
        checkResponses(expInfo, subjectResponses, thisCond)

    #look for responses
    while trialTimer.getTime() < expInfo['responseTimeout']:
        checkResponses(expInfo, subjectResponses)
    gotResponse[iT] = len(subjectResponses) > nResponsesBefore

    # decide if subject was right and adjust staircase accordingly
    if gotResponse[iT]:
        correct = subjectResponses[-1]['response'] == correctResponse
    else:
        correct = False
        subjectResponses.append({'response': ' ',
                                 'time': -999.,
                                 'condition': thisCond,
                                 'dC': thisDC})
        print('No response')
    if correct:
        expInfo['staircases'][thisCond]['nCorrect'] += 1
        if expInfo['staircases'][thisCond]['nCorrect'] > 3:
            # reset counter
            expInfo['staircases'][thisCond]['nCorrect'] = 0
            # decrease dC
            dCidx = expInfo['staircases'][thisCond]['dCidx'] - 1
            expInfo['staircases'][thisCond]['dCidx'] = max(0, dCidx)
            expInfo['staircases'][thisCond]['currentDC'] = expInfo['staircases'][thisCond]['dCrange'][expInfo['staircases'][thisCond]['dCidx']]
        print('Response: %s (correct); new DC = %2.4f; dCidx %d' %(subjectResponses[-1]['response'], expInfo['staircases'][thisCond]['currentDC'], expInfo['staircases'][thisCond]['dCidx']))
        # feedback
        expInfo['fixationMark'].fillColor = expInfo['rightColor']
    else:
        # reset counter
        expInfo['staircases'][thisCond]['nCorrect'] = 0
        # increase dC
        dCidx = expInfo['staircases'][thisCond]['dCidx'] + 1
        expInfo['staircases'][thisCond]['dCidx'] = min(len(expInfo['staircases'][thisCond]['dCrange']) - 1, dCidx)
        expInfo['staircases'][thisCond]['currentDC'] = expInfo['staircases'][thisCond]['dCrange'][expInfo['staircases'][thisCond]['dCidx']]
        # feedback
        expInfo['fixationMark'].fillColor = expInfo['wrongColor']
        if gotResponse[iT]:
            print('Response: %s (incorrect); new DC = %2.4f; dCidx %d' %(subjectResponses[-1]['response'], expInfo['staircases'][thisCond]['currentDC'], expInfo['staircases'][thisCond]['dCidx']))
    # refresh screen w/ fiducial lines and fixation mark
    expInfo['fixationMark'].draw()

    #fiducial circles around targets
    expInfo['fiducialCircle'].pos = expInfo['stimLocLeft']
    expInfo['fiducialCircle'].draw()
    expInfo['fiducialCircle'].pos = expInfo['stimLocRight']
    expInfo['fiducialCircle'].draw()
    expInfo['win'].flip()

    #append to output file
    with open(outFile, 'a') as fid:
        fid.write('%s\t%2.2f\t%2.2f\t%2.2f\t%s\t%d\n' %(thisCond,
                                                        thisFrameTime,
                                                        expInfo['stimDuration'],
                                                        thisDC,
                                                        subjectResponses[-1]['response'],
                                                        correct))
    if expInfo['eyetracking'] is 'Avotec':
        mymsg='dataFile_InsertString Trial_%d_condition_%d_ori_%d_trialEnd'%(iT,thisCond,thisOri)
        vpx.VPX_SendCommand(mymsg)
    elif expInfo['eyetracking'] is 'Eyelink':
        msg='Trial_%d_condition_%d_ori_%d_trialEnd'%(iT,thisCond,thisOri)
        expInfo['tracker'].sendMessage(msg)

print('total time: %f'%scanTimer.getTime())
########################################################################################
if expInfo['eyetracking'] is 'Avotec':
    #close the data file
    vpx.VPX_SendCommand('dataFile_Close'.encode('ascii'))

    #close link to eyetracker
    connectResult = vpx.VPX_DisconnectFromViewPoint()
    print('finished successfully!')
elif expInfo['eyetracking'] is 'Eyelink':
    expInfo['tracker'].setRecordingState(False)
    expInfo['tracker'].setConnectionState(False)
    expInfo['io'].quit()
    #copy file and rename
    shutil.copy2('et_data.EDF',expInfo['outFileEye'])
#save data
expInfo['blank'].draw()
pctResponse = int(100*sum(gotResponse)/len(gotResponse))
expInfo['textMsg'].setText('Thank you!\n\nResponses recorded on %d pct. of trials' %pctResponse)
expInfo['textMsg'].draw()
expInfo['win'].flip()

core.wait(2)
#close screen
expInfo['win'].close()
