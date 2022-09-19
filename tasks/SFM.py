#!/usr/bin/env python2
# author: agrant, edits by mps

from psychopy.iohub.client import launchHubServer
import numpy
from psychopy import visual,core, monitors, event, misc,gui
import os
import datetime
import shutil

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

def writeData():
    data={'responses':responses}
    misc.toFile(outFile,data)

    f = open(txtFile,'w')
    f.write('%s\t%s\t%s'%('block','time','key'))
    f.write('\n')
    SFMlist = data['responses']
    for item in SFMlist:
        for iV,val in enumerate(item):
            if iV < len(item)-1:
                f.write('%s\t'%(str(val)))
            else:
                f.write('%s'%(str(val)))
        f.write('\n')
    f.close() 
    if subInfo['eyetracking']=='yes':
        #close the communication
        tracker.setConnectionState(False)
        #shut down the iohub engine
        io.quit()
        # check if eyetracking subdir exists
        if not os.path.isdir(outFileDirEye):
            os.makedirs(outFileDirEye) 
        #rename the EDF file
        shutil.copy2('et_data.EDF',outFileEye)


def getResponses(block, time):
    for key in event.getKeys():
        if key in quitKeys:
            writeData()
            core.quit()
        elif (key in responseKeys):
            responses.append([block, time, key])
            print(block, time, key)



def waitForKey():#non specific (trigger vs button press...)
    thisKey=None
    while thisKey==None:
        thisKey = event.waitKeys()
        if thisKey[0] in quitKeys:
            core.quit() #abort
        else:
            event.clearEvents()

def waitForContKey():#non specific (trigger vs button press...)
    contKey = None
    while not contKey:
        thisKey = event.waitKeys()
        contKey = thisKey[0] in continueKeys
        if thisKey[0] in quitKeys:
            core.quit() #abort
        else:
            event.clearEvents()
        if thisKey[0] in repeatKeys:
            do_repeat = 1
        else:
            do_repeat = 0
    return do_repeat

subInfo={'subject':'1','runType':['A','B'],'runNumber':1,'lastRunNum':0,'eyetracking':['yes','no']}

#update session info
infoDlg=gui.DlgFromDict(dictionary=subInfo,title='Scan Parameters',
                        order=['subject','runType','lastRunNum','runNumber','eyetracking'],
                        fixed=['lastRunNum'],
                        tip={'subject':'subject number',
                             'runType':'run type A or B',
                             'runNumber':'run number',
                             'lastRunNum':'previous run number',
                             'eyetracking':'yes or no',
                             })
if infoDlg.OK:
    #create my expInfo object
    misc.toFile('sfm_lastrun.pickle',subInfo)
else:
    print 'user cancelled'
    core.quit()

quitKeys=['q','escape']
responseKeys=['left','right']
repeatKeys=['home']
continueKeys=['c','home']

nowTime=datetime.datetime.now() 
outFileName='%s_%04d%02d%02d_%02d%02d_SFM_type%s_run%.2d.pickle'%(subInfo['subject'],nowTime.year,nowTime.month,nowTime.day,
	nowTime.hour,nowTime.minute,subInfo['runType'],subInfo['runNumber']) 
outFile=os.path.join('subjectResponseFiles',outFileName)
txtFileName='%s_%04d%02d%02d_%02d%02d_SFM_type%s_run%.2d.txt'%(subInfo['subject'],nowTime.year,nowTime.month,nowTime.day,
	nowTime.hour,nowTime.minute,subInfo['runType'],subInfo['runNumber']) 
txtFile=os.path.join('subjectResponseFiles',txtFileName)

if subInfo['eyetracking']=='yes':
    #set up eyetracker communications
    iohub_tracker_class_path = 'eyetracker.hw.sr_research.eyelink.EyeTracker'
    eyetracker_config = dict()
    eyetracker_config['name'] = 'tracker'
    eyetracker_config['model_name'] = 'EYELINK 1000 REMOTE'
    #does this work? custom file name, which is still limited to 8.3, DOS-style
    #eyetracker_config['default_native_data_file_name']='%02d%02d%02.edf'%(nowTime.day,nowTime.hour,nowTime.minute)
    eyetracker_config['runtime_settings'] = dict(sampling_rate=500,track_eyes='BOTH')
    io = launchHubServer(**{iohub_tracker_class_path: eyetracker_config})
    tracker = io.devices.tracker
    outFileNameEye='SFM_subj_%s_run_%02d_%s_%04d%02d%02d_%02d%02d.edf'%(subInfo['subject'],
        subInfo['runNumber'],subInfo['runType'],nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute)
    #outFileEye=os.path.join('eyetracking',outFileNameEye)
    outFileDirEye=os.path.join('eyetracking', '%s'%(subInfo['subject']) )
    outFileEye=os.path.join(outFileDirEye,outFileNameEye) 


mon='LocalLinear' 
subMonitor=monitors.Monitor(mon)
screenSize=subMonitor.getSizePix()
win=visual.Window(screenSize,monitor=mon,units='deg',
                screen=0,color=[0,0,0],colorSpace='rgb',fullscr=True,allowGUI=False) 

if subInfo['runType'] == 'A': 
    numBlocks=1
    numPracBlocks=1
elif subInfo['runType'] == 'B':
    numBlocks=5
    numPracBlocks=0

textMsg=visual.TextStim(win,text='Preparing the task',
            units='norm',pos=(0,0),height=0.065,alignVert='top',wrapWidth=1.0)
textMsg.draw()
win.flip()
responses=[]

movies=[]
for iM in range(numBlocks):
    thismovie='SFM_movies/SFM_%s_%d.mp4'%(subInfo['runType'],iM)
    movies.append(visual.MovieStim3(win, thismovie, size=(1920,1200), flipVert=False,
        flipHoriz=False, loop=False))

if numPracBlocks == 1: 
    pracMovies=[]
    for iM in range(5): # can only do this many practices...
        thismovie='SFM_movies/SFM_prac_0.mp4'
        pracMovies.append(visual.MovieStim3(win, thismovie, size=(1920,1200), flipVert=False,
            flipHoriz=False, loop=False))


# run eyetracker calibration
if subInfo['eyetracking']=='yes':
    tracker.runSetupProcedure()


#instructions
textMsg.text="In this task, you will see a rotating cylinder covered with " \
            "black and white squares. If it looks like the front is rotating to " \
            "the left, press the left arrow. If it's rotating to the right, press " \
            "the right arrow. Please keep your eyes on the red dot at the center " \
            "of the screen at all times."
textMsg.draw()
win.flip()
waitForContKey()

clock=core.Clock()
clock.reset()
blockDuration=2*60
pracBlockDuration=30 

if numPracBlocks == 1:
    iB=-1
    do_repeat = 1
    while do_repeat:
        iB += 1
        textMsg.text='Ready to start practice block %d'%(iB+1)
        textMsg.draw()
        win.flip()
        waitForContKey()
        if subInfo['eyetracking']=='yes':
            #start recording
            io.clearEvents()
            tracker.setRecordingState(True)
            #send a message to the tracker
            msg='starting practice'
            tracker.sendMessage(msg)
        clock.reset()
        while pracMovies[iB].status != visual.FINISHED:
            pracMovies[iB].draw()
            win.flip()
            getResponses(-1-iB,clock.getTime())
        print(clock.getTime())
        if subInfo['eyetracking']=='yes':
            #send a message to the tracker
            msg='ending practice'
            tracker.sendMessage(msg)
            tracker.setRecordingState(False)
        textMsg.text='Repeat or continue?'
        textMsg.draw()
        win.flip()
        do_repeat = waitForContKey()

for iB in range(numBlocks):
    if iB == 0:
        textMsg.text='Ready to start block %d'%(iB+1)
    else:
        textMsg.text='Press any key to start block %d'%(iB+1)
    textMsg.draw()
    win.flip()
    if iB == 0:
        waitForContKey()
    else:
    	core.wait(1.5)
        waitForKey()
    if subInfo['eyetracking']=='yes':
        #start recording
        io.clearEvents()
        tracker.setRecordingState(True)
    clock.reset()
    if subInfo['eyetracking']=='yes':
        #send a message to the tracker
        msg='start block %d'%iB
        tracker.sendMessage(msg)
    while movies[iB].status != visual.FINISHED:
        movies[iB].draw()
        win.flip()
        getResponses(iB,clock.getTime())
    print(clock.getTime())
    if subInfo['eyetracking']=='yes':
        #send a message to the tracker
        msg='end block %d'%iB
        tracker.sendMessage(msg)
        tracker.setRecordingState(False)

textMsg.text='Thank you!'
textMsg.draw()
win.flip()

writeData()
os.remove('sfm_lastrun.pickle')
core.quit()
