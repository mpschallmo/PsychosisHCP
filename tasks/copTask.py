#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue May  2 13:20:03 2017

@author: agrant, edits by mps
"""

#framework for contour object detection stimulus
from psychopy.iohub.client import launchHubServer
from psychopy import visual, core, data, event, monitors, gui, misc
import numpy
import os
import datetime
import pickle, glob, sys
from timeit import default_timer as t_timer
debug=0
from ctypes import *
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

class ExpInfoX(object):
    def __init__(self, subject, runNumber, longInstructions, eyetrack):
        self._subject=subject
        self._runNumber=runNumber
        self._longInstructions = longInstructions
        self._numContour=15
        self._mon='LocalLinear'
        self._subMonitor=monitors.Monitor(self._mon)
        self._screenSize=self._subMonitor.getSizePix()
        self.win=visual.Window(self._screenSize, monitor=self._mon, units='deg',
                               screen=0, color=[0,0,0], colorSpace='rgb', fullscr=True,allowGUI=False) # n.b. screen needs to be mirrored
        self._textMsg=visual.TextStim(self.win,
                                      text='Preparing the task',
                                      units='norm',
                                      pos=(0,0),
                                      height=0.065,
                                      alignVert='top',
                                      wrapWidth=1.9)
        self._textMsg.draw()
        self.win.flip()
        self._quitKeys=['q','escape']
        self._responseKeys=['b','r']
        self._pauseKeys=['space']
        self._repeatKeys=['home']
        self._triggerKeys=['t']
        self._continueKeys=['c','home']
        nowTime=datetime.datetime.now()
        #self._outFileName='COP_sub_%s_run_%02d_%04d%02d%02d_%02d%02d.pickle'%(self._subject,self._runNumber,nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute)
        #self._outFile=os.path.join('subjectResponseFiles',self._outFileName)
        #self._timingAndConditions()
        self._doRepeat=0 # chage to 1 if we're repeating instructions
        self._correctAnswer=0
        self._keepLocations=[]
        self._keepResponses={}
        self._keepResponseKeys=[]
        self._haveResponse=0
        self._trials=[]
        self._iT=-1
        self._stairJitter=0 #starting jitter for staircased jitter in fMRI
        self._jitterBlankTime=3 #jittered time between trials
        self._baselineBlank=12
        self._totalScanLengtb=0
        self._keepSides=[]
        self._stimOnsetTimes=[]
        self._keepCorr=[]
        self._locResponses=[]
        self._blockLoc=[]

    @property
    def correctAnswer(self):
        return self._correctAnswer
    @correctAnswer.setter
    def correctAnswer(self, value):
        self._correctAnswer=value

    @property
    def stimDuration(self):
        return self._stimDuration
    @stimDuration.setter
    def stimDuration(self, value):
        self._stimDuration=value

    @property
    def baselineBlank(self):
        return self._baselineBlank
    @baselineBlank.setter
    def baselineBlank(self, value):
        self._baselineBlank = value

    @property
    def trials(self):
        return self._trials
    @trials.setter
    def trials(self, value):
        self._trials=value

    @property
    def blockOrder(self):
        return self._blockOrder
    @blockOrder.setter
    def blockOrder(self,value):
        self._blockOrder=value

    @property
    def jitterBlankTime(self):
        return self._jitterBlankTime
    @jitterBlankTime.setter
    def jitterBlankTime(self, value):
        self._jitterBlankTime=value

    @property
    def haveResponse(self):
        return self._haveResponse
    @haveResponse.setter
    def haveResponse(self, value):
        self._haveResponse=value

    @property
    def totalScanLength(self):
        return self._totalScanLength

    def _timingAndConditions(self):
        pass


    def waitForKey(self,trigger=False):#non specific (trigger vs button press...)
        if trigger is True:
            gotTrigger=None
            while not gotTrigger:
                thisKey=event.waitKeys()
                gotTrigger = thisKey[0] in self._triggerKeys
                if thisKey[0] in self._quitKeys:
                    self.writeDataFile() 
                    core.quit()
                else:
                    event.clearEvents()
        else:
            thisKey=None
            while thisKey==None:
                thisKey = event.waitKeys()
            if thisKey[0] in self._quitKeys:
                self.writeDataFile() 
                core.quit() #abort
            else:
                event.clearEvents()
            if thisKey[0] in ['c','m']:
                return(thisKey[0])

    def waitForContKey(self,trigger=False):#non specific (trigger vs button press...)
        if trigger is True:
            gotTrigger=None
            while not gotTrigger:
                thisKey=event.waitKeys()
                gotTrigger = thisKey[0] in self._triggerKeys
                if thisKey[0] in self._quitKeys:
                    self.writeDataFile() 
                    core.quit()
        else:
            contKey=None
            while not contKey:
                thisKey = event.waitKeys()
                contKey = thisKey[0] in self._continueKeys
                if thisKey[0] in self._quitKeys:
                    self.writeDataFile() 
                    core.quit() #abort
                if thisKey[0] in self._repeatKeys:
                    self._doRepeat = 1
                else:
                    self._doRepeat = 0

    def writeDataFile(self):
        pass

    def cleanup(self):
        pass

    def getResponses(self,condition):
            if (len(self._keepResponseKeys)-1) < self._iT:
                self._keepResponseKeys.append('none')
            for key in event.getKeys():
                if key in self._quitKeys:
                    self.writeDataFile()
                    self.cleanup()
                    core.quit()
                #elif key in self._pauseKeys: #DISABLE THIs FOR FMRI?
                    #wait....
                    #goPause(expInfo) #FIX THIS
                elif (key in self._responseKeys) & (condition<99) & (self._haveResponse==0):
                    if key==self._correctAnswer:
                        print('you typed %s, correct was %s'%(key,self._correctAnswer))
                        thisResp=1
                    else:
                        print('you typed %s, correct was %s'%(key,self._correctAnswer))
                        thisResp=0
                    #either way, keep the response
                    self._keepResponses[self._iT]=[condition, self._iT, key, self._correctAnswer,thisResp]
                    self._keepResponseKeys[self._iT] = key 
                    self._updateStair(condition, thisResp)
                    self._haveResponse=1

    def getResponsesCont(self,side):
        for key in event.getKeys():
            if key in self._quitKeys:
                self.writeDataFile()
                self.cleanup()
                core.quit()
            #elif key in self._pauseKeys: #DISABLE THIs FOR FMRI?
                #wait....
                #goPause(expInfo) #FIX THIS
            elif (key in self._continueKeys) & (self._haveResponse==0):
                self._haveResponse=1

    def getResponsesInstr(self,side):
        for key in event.getKeys():
            if key in self._quitKeys:
                self.writeDataFile()
                self.cleanup()
                core.quit()
            #elif key in self._pauseKeys: #DISABLE THIs FOR FMRI?
                #wait....
                #goPause(expInfo) #FIX THIS
            elif (key in self._responseKeys) & (self._haveResponse==0):
                self._correctAnswer=self._responseKeys[side]
                if key==self._correctAnswer:
                    print('you typed %s, correct was %s'%(key,self._correctAnswer))
                    thisResp=1
                else:
                    print('you typed %s, correct was %s'%(key,self._correctAnswer))
                    thisResp=0
                self._haveResponse=1
                self._keepCorr.append(thisResp)

    def _updateStair(self, condition, response):
        pass

    def setBlock(self,block):
        self._block=block
        self._trials=self._trialListMaster[block]
        self._trialTimeJitters=self._timeJitterListMaster[block]


    def setCondition(self, iTrial, trialType, stimObject):
        self._iT+=1 #global trial counter
        #iTrial is the within-block trial counter (i.e., 0 to 5)
        print('global trial %d, condition %d'%(self._iT+1, trialType))
        #trialType is the condition (0-3fMRI or 0-4psyc)
        #setLocation needs the array of orienation jitters and the absolute trial number and condition--withbackground?
        self._setOriJitter(trialType)
        stimObject.setLocation(self._oriJitters, self._iT, self._backgrounds[trialType])#this randomly sets left/right pointing Egg
        self._jitterBlankTime=self._trialTimeJitters[iTrial]
        #collect the egg direction
        self._correctAnswer=self._responseKeys[stimObject.narrowEnd]
        if debug==8:
            print(self._correctAnswer)
        self._keepSides.append(stimObject.narrowEnd)

    def addOnsetTime(self, condition, onsetTime):
        self._stimOnsetTimes.append([self._iT,condition, onsetTime])

    def doInstructions(self, stimObject):
        pass
        #This "practice block" should be run at the beginning of this psychophysics experiment.
        #First thing is to always keep your eyes focused on the square in the middle (show the fixation square).
        msg='Please keep your eyes focused on the square in the middle at all times.'
        stimObject.drawCustom(text=msg, fixation=True, jitter=None)
        self.waitForContKey()

        #Then show an egg shaped contour made of Gabors (0 jitter, no background),
        #and explain that you’re going to see egg shapes made up of little striped
        #line segments. Task is to "connect the dots" to decide whether the pointy
        #end of the egg is on the left or right.
        msg="In each trial, you will see an 'egg' shape made of little striped line"\
        " segments. The task is to 'connect the dots' and decide if the pointy end "\
        "of the egg is to the left or right."
        stimObject.drawCustom(text=msg,fixation=True,jitter=[0], side=0,background=False)
        self.waitForContKey()

        msg="In the scanner, the striped segments will sometimes flash, like this." 
        phaseTimer=core.CountdownTimer()
        timeEpsilon=0.0025
        iT=numpy.random.randint(100)
        self._haveResponse=0
        while self._haveResponse==0:
            self.getResponsesCont(1)
            phaseTimer.reset()
            phaseTimer.add(stimObject.phaseDuration)
            stimObject.switchPhase()
            stimObject.drawCustom(text=msg,fixation=True,jitter=[0], side=0,background=False,iT=iT)
            while phaseTimer.getTime()>timeEpsilon:
                self.getResponsesCont(1)


        #If the egg points to the left, press left arrow, if right, press right arrow.
        #Remember to keep your eyes at the center at all times, do not look right at the egg (look "out of the corner of your eye").
        msg="If the egg points to the left, press the left arrow. If it points to the "\
        "right, press the right arrow. In this example, it points to the left."\
        " Remember to keep your eyes in the center at all times and do not look directly "\
        "at the egg (look at it 'out of the corner of your eye')."
        iT=numpy.random.randint(100)
        self._haveResponse=0
        while self._haveResponse==0:
            self.getResponsesCont(1)
            phaseTimer.reset()
            phaseTimer.add(stimObject.phaseDuration)
            stimObject.drawCustom(text=msg,fixation=True,jitter=[0], side=0,background=False,iT=iT)
            while phaseTimer.getTime()>timeEpsilon:
                self.getResponsesCont(1)

        #Then show a very slow example trial - start with a blank screen, fixation mark,
        #then a target appears (0 jitter, no background). Target stays on for 2.5 s. Then subject can respond.
        stimObject.drawCustom(text=None, fixation=True)
        core.wait(0.5)
        iT=numpy.random.randint(100)
        numDraws=numpy.int(numpy.ceil(2.5/stimObject.phaseDuration))
        for iDraw in range(numDraws):
            self.getResponsesInstr(1)#allow quits
            phaseTimer.reset()
            phaseTimer.add(stimObject.phaseDuration)
            stimObject.drawCustom(text=None, fixation=True, jitter=[0], side=1, background=False,iT=iT)
            while phaseTimer.getTime()>timeEpsilon:
                self.getResponsesInstr(1) #allow quits
        self._keepCorr=[]
        self._haveResponse=0
        msg="Was the egg pointing to the left or right?"
        stimObject.drawCustom(text=msg)
        while self._haveResponse==0:
            self.getResponsesInstr(1)
        if self._keepCorr[0]==1:
            feedback='Correct! Press any key to continue.'
        else:
            feedback = "The correct answer was 'right side'. Press any key to continue."
        stimObject.drawCustom(text=feedback)
        self.waitForKey()

        #Then include a screen explaining that the lines that make up the egg may
        #not line up perfectly all the time, but the task is always the same.
        msg="The small striped lines that make up the egg may not line up"\
        " perfectly all the time, but the task is the same (is the egg pointing "\
        "to the left or right)."
        iT=numpy.random.randint(100)
        randomOrient=numpy.repeat([1,-1],numpy.ceil(self._numContour/2.0))
        numpy.random.shuffle(randomOrient)
        randomOrient=numpy.delete(randomOrient,self._numContour)
        oriJitters=numpy.repeat(25, self._numContour)
        jitterArray = oriJitters*randomOrient
        self._haveResponse=0
        while self._haveResponse==0:
            self.getResponsesCont(1)
            phaseTimer.reset()
            phaseTimer.add(stimObject.phaseDuration)
            stimObject.drawCustom(text=msg,fixation=True,jitter=jitterArray, side=0,background=False,iT=iT)
            while phaseTimer.getTime()>timeEpsilon:
                self.getResponsesCont(1)


        #Then show a faster example (use the real task timing, 4.5 deg. Jitter, no background).
        msg='Now we will try a faster example. The egg will be on the screen for only a short time.'
        stimObject.drawCustom(text=msg)
        self.waitForContKey()
        self._keepCorr=[]
        self._haveResponse=0
        iT=numpy.random.randint(100)
        randomOrient=numpy.repeat([1,-1],numpy.ceil(self._numContour/2.0))
        numpy.random.shuffle(randomOrient)
        randomOrient=numpy.delete(randomOrient,self._numContour)
        oriJitters=numpy.repeat(4.5, self._numContour)
        jitterArray = oriJitters*randomOrient
        trialTimer=core.CountdownTimer()
        numDraws=numpy.int(self._stimDuration/stimObject.phaseDuration)
        for iDraw in range(numDraws):
            self.getResponsesInstr(1)#allow quits
            phaseTimer.reset()
            phaseTimer.add(stimObject.phaseDuration)
            stimObject.drawCustom(text=None, fixation=True, jitter=jitterArray, side=0, background=False,iT=iT)
            while phaseTimer.getTime()>timeEpsilon:
                self.getResponsesInstr(1) #allow quits
        stimObject.drawCustom(fixation=True)
        while self._haveResponse==0:
            self.getResponsesInstr(0)
        if self._keepCorr[0]==1:
            feedback='Correct! Press any key to continue.'
        else:
            feedback = "The correct answer was 'left side'. Press any key to continue."
        stimObject.drawCustom(text=feedback)
        self.waitForKey()

        #Then show 10 more fast example trials (4.5 deg. jitter, still no background)
        self._doRepeat = 1
        while self._doRepeat:
            msg="Now we will try 10 examples."
            stimObject.drawCustom(text=msg)
            self.waitForContKey()
            postTrialBlankTimer=core.Clock()
            self._keepCorr=[]
            for iTrial in range(10):
                randomOrient=numpy.repeat([1,-1],numpy.ceil(self._numContour/2.0))
                numpy.random.shuffle(randomOrient)
                randomOrient=numpy.delete(randomOrient,self._numContour)
                oriJitters=numpy.repeat(4.5, self._numContour)
                jitterArray = oriJitters*randomOrient
                self._haveResponse=0
                side=numpy.random.randint(2)
                numDraws=numpy.int(self._stimDuration/stimObject.phaseDuration)
                for iDraw in range(numDraws):
                    phaseTimer.reset()
                    phaseTimer.add(stimObject.phaseDuration)
                    stimObject.drawCustom(text=None, fixation=True, jitter=jitterArray, background=False, side=side,iT=iTrial)
                    while phaseTimer.getTime()>timeEpsilon:
                        self.getResponsesInstr(side)
                stimObject.drawBlank()
                postTrialBlankTimer.reset()
                while postTrialBlankTimer.getTime()<0.5:
                    self.getResponsesInstr(side)
                while self._haveResponse==0:
                    self.getResponsesInstr(side)
                postTrialBlankTimer.reset()
                while postTrialBlankTimer.getTime()<0.5:
                    stimObject.drawBlank()
            feedback='You got %d of 10 correct. Repeat or continue?'%(numpy.sum(self._keepCorr))
            print(self._keepCorr)
            stimObject.drawCustom(text=feedback)
            self.waitForContKey()

        #Then show a static image of a target (0 jitter) with the background.
        #"Most of the time there will be lines in the background. You can ignore
        #these. Your task is always the same, report whether the egg points to the left or right."
        msg="Sometimes there will be striped lines in the background. You can ignore"\
        " these. Your task is always the same: report whether the egg points to the left "\
        "or right."
        iT=numpy.random.randint(100)
        randomOrient=numpy.repeat([1,-1],numpy.ceil(self._numContour/2.0))
        numpy.random.shuffle(randomOrient)
        randomOrient=numpy.delete(randomOrient,self._numContour)
        oriJitters=numpy.repeat(4.5, self._numContour)
        jitterArray = oriJitters*randomOrient
        self._haveResponse=0
        while self._haveResponse==0:
            self.getResponsesCont(1)
            phaseTimer.reset()
            phaseTimer.add(stimObject.phaseDuration)
            stimObject.drawCustom(text=msg,fixation=True,jitter=jitterArray, side=0,background=True,iT=iT)
            while phaseTimer.getTime()>timeEpsilon:
                self.getResponsesCont(1)

        #Then 10 fast examples with background (jitter = 4.5 degrees)
        self._doRepeat = 1
        while self._doRepeat:
            msg="Now we will try 10 examples with backgrounds."
            stimObject.drawCustom(text=msg)
            self.waitForContKey()
            postTrialBlankTimer=core.Clock()
            self._keepCorr=[]
            for iTrial in range(10):
                randomOrient=numpy.repeat([1,-1],numpy.ceil(self._numContour/2.0))
                numpy.random.shuffle(randomOrient)
                randomOrient=numpy.delete(randomOrient,self._numContour)
                oriJitters=numpy.repeat(4.5, self._numContour)
                jitterArray = oriJitters*randomOrient
                self._haveResponse=0
                side=numpy.random.randint(2)
                numDraws=numpy.int(self._stimDuration/stimObject.phaseDuration)
                for iDraw in range(numDraws):
                    phaseTimer.reset()
                    phaseTimer.add(stimObject.phaseDuration)
                    stimObject.drawCustom(text=None, fixation=True, jitter=jitterArray, background=True, side=side,iT=iTrial)
                    while phaseTimer.getTime()>timeEpsilon:
                        self.getResponsesInstr(side)
                stimObject.drawBlank()
                postTrialBlankTimer.reset()
                while postTrialBlankTimer.getTime()<0.5:
                    self.getResponsesInstr(side)
                while self._haveResponse==0:
                    self.getResponsesInstr(side)
                postTrialBlankTimer.reset()
                while postTrialBlankTimer.getTime()<0.5:
                    stimObject.drawBlank()
            feedback='You got %d of 10 correct. Repeat or continue?'%(numpy.sum(self._keepCorr))
            print(self._keepCorr)
            stimObject.drawCustom(text=feedback)
            self.waitForContKey()


    def doLoc(self,stimObject):
        msg=''
        self._keepCorr=[]
        self._haveResponse=0
        phaseTimer=core.CountdownTimer()
        iT=0
        locPeriod=24
        timeEpsilon=0.0001
        blockLoc=[99]
        lrseq=numpy.random.randint(0,2,6)
        for iRep in range(6):
            if lrseq[iRep]==0:
                blockLoc.extend([10,11])
            else:
                blockLoc.extend([11,10])
            blockLoc.append(99)#99=rest, 10=left, 11=right
        self._blockLoc=blockLoc
        numDraws=numpy.int(1/stimObject.phaseDuration)
        trialTimer=core.CountdownTimer()
        for iBlock in self._blockLoc:
            print('starting loc block %d'%iBlock)
            print(trialTimer.getTime())
            if iBlock==99:
                trialTimer.reset()
                trialTimer.add(locPeriod/2)
                stimObject.drawBlank()
                while trialTimer.getTime()>timeEpsilon:
                    self.getResponses(99)
            else:
                side=iBlock-10
                for iTrial in range(locPeriod/4):
                    for iDraw in range(numDraws):
                        phaseTimer.reset()
                        phaseTimer.add(stimObject.phaseDuration)
                        stimObject.switchPhase()
                        stimObject.drawCustom(text=msg,fixation=True,jitter=[0], side=side,background=False,iT=iT)
                        while phaseTimer.getTime()>timeEpsilon:
                            self.getResponsesInstr(side)
                    iT+=1
                    self._locResponses=self._keepCorr[:]


class ExpInfofMRI(ExpInfoX):
    def __init__(self, subject, runNumber, longInstructions, eyetrack):
        self._eyetracking=eyetrack
        self._subject=subject
        self._runNumber=runNumber
        nowTime=datetime.datetime.now()
        if self._eyetracking=='Eyelink':
            #set up eyetracker communications
            iohub_tracker_class_path = 'eyetracker.hw.sr_research.eyelink.EyeTracker'
            eyetracker_config = dict()
            eyetracker_config['name'] = 'tracker'
            eyetracker_config['model_name'] = 'EYELINK 1000 REMOTE'
            #does this work? custom file name, which is still limited to 8.3, DOS-style
            #eyetracker_config['default_native_data_file_name']='%02d%02d%02.edf'%(nowTime.day,nowTime.hour,nowTime.minute)
            eyetracker_config['runtime_settings'] = dict(sampling_rate=500,track_eyes='BOTH')
            self.io = launchHubServer(**{iohub_tracker_class_path: eyetracker_config})
            self.tracker = self.io.devices.tracker
            self._outFileNameEyetracking='%s_%04d%02d%02d_%02d%02d_COP_fMRI_run%02d_eyetracking.edf'%(self._subject,nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute,self._runNumber)
            self._outFileDirEye=os.path.join('eyetracking', '%s'%(subject) )
            self._outFileEye=os.path.join(self._outFileDirEye,self._outFileNameEyetracking)
        elif self._eyetracking=='Avotec':
            self._outFileNameEyetracking='%s_%04d%02d%02d_%02d%02d_COP_fMRI_run%02d_eyetracking.txt'%(self._subject,nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute,self._runNumber)

        ExpInfoX.__init__(self, subject, runNumber, longInstructions, eyetrack)

        self._outFileName='%s_%04d%02d%02d_%02d%02d_COP_fMRI_run%02d.pickle'%(self._subject,nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute,self._runNumber)
        self._outFile=os.path.join('subjectResponseFiles',self._outFileName)
        self._tsvFileName='%s_%04d%02d%02d_%02d%02d_COP_fMRI_run%02d.txt'%(self._subject,nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute,self._runNumber)
        self._tsvFile=os.path.join('subjectResponseFiles',self._tsvFileName)
        self._timingAndConditions()

    @property
    def eyetrackingFile(self):
        return self._outFileNameEyetracking

    def cleanup(self):
        self.win.close()
        if self._eyetracking=='Eyelink':
            #close the communication
            self.tracker.setConnectionState(False)
            #shut down the iohub engine
            self.io.quit()
            # check if eyetracking subdir exists
            if not os.path.isdir(self._outFileDirEye):
                os.makedirs(self._outFileDirEye)
            #rename the EDF file
            shutil.copy2('et_data.EDF',self._outFileEye)
        core.quit()

    def _timingAndConditions(self):
        self._stimDuration=1.0
        self._baselineBlank=12.0
        self._numScrambledPerBlock=2
        self._numStaircasedPerBlock=4
        self._numTrialsPerBlock=self._numScrambledPerBlock+self._numStaircasedPerBlock
        self._numblocksPerBackground=6
        self._jitteredBlank=numpy.asarray([2, 2, 3, 3, 4, 4]) #mean 3 s jitter. is there a clever way to do this?

        #create trial and block sequences
        #each block has 6 trials. 2 are 100% scramble, 4 are "staircased"
        #block A (0) has background, block B (1) has no background
        blockOrder=numpy.tile([0,1],self._numblocksPerBackground)
        blockOrder=numpy.insert(blockOrder,0,99)
        blockOrder=numpy.append(blockOrder,99)
        self._blockOrder=blockOrder
        self._conditions={'0':{'name':'background, scrambled','jitter':45},
                            '1':{'name':'background, staircased','jitter':36},#wrong--now staircased
                            '2':{'name':'noBackground, scrambled','jitter':45},
                            '3':{'name':'noBackground, staircased','jitter':36}}#wrong--now picked up from cond 1
        self._backgrounds=[True,True,False,False]#yikes
        trialList=[[],]
        trialTimeJitterList=[[],]
        #create a nested list of trials per block
        for iB in range(self._numblocksPerBackground):
            #block A, with background
            scrambleTrials=numpy.repeat([0],self._numScrambledPerBlock)
            stairTrials=numpy.repeat([1],self._numStaircasedPerBlock)
            theseTrials=numpy.concatenate((scrambleTrials,stairTrials))
            numpy.random.shuffle(theseTrials)
            trialList.append(theseTrials[:]) #slicing here to get a copy of the contents
            #also do the time jitters
            numpy.random.shuffle(self._jitteredBlank)
            trialTimeJitterList.append(self._jitteredBlank[:])
            #block A, NO background
            scrambleTrials=numpy.repeat([2],self._numScrambledPerBlock)
            stairTrials=numpy.repeat([3],self._numStaircasedPerBlock)
            theseTrials=numpy.concatenate((scrambleTrials,stairTrials))
            numpy.random.shuffle(theseTrials)
            trialList.append(theseTrials[:]) #slicing here to get a copy of the contents
            numpy.random.shuffle(self._jitteredBlank)
            trialTimeJitterList.append(self._jitteredBlank[:])
        #append dummy lists for the rest block at and
        trialList.append([])
        trialTimeJitterList.append([])
        self._trialListMaster=trialList
        self._timeJitterListMaster=trialTimeJitterList

        self._totalScanLength=self._baselineBlank+(self._stimDuration+3)*(self._numStaircasedPerBlock+self._numScrambledPerBlock)*2*self._numblocksPerBackground + self._baselineBlank

        #pre-allocate left/right ?

        #put the background-staircased trials on a 3-up, 1-down staircase
        #for now, ONE staircase for the whole run
        #the problem is that staircase logic assumes LARGER intensity is EASIER, but in
        #this case it's the opposite--smaller numbers make the contour easier to see.
        #I can't use negative numbers in the stairacase, so I'll have to "invert" their output.
        #when the stair returns the max [easiest] (45), I want jitter=0
        #when the stair returns the min [hardest] (0) I want jitter=45
        #"nUp and nDown are always considered as 1 until the first reversal is reached. The values entered as arguments are then used."
        #self._stair=data.StairHandler(startVal=90-self._stairJitter,stepSizes=numpy.linspace(45,90,16),#steps of 3
        self._stair=data.StairHandler(startVal=90-self._stairJitter,stepSizes=3,#steps of 3 
                            nTrials=self._numblocksPerBackground*self._numStaircasedPerBlock,
                            nUp=1, nDown=3, stepType='lin',
                            minVal=45, maxVal=90)

        #print(trialList)
        numTrialsPerRun=self._numTrialsPerBlock*self._numblocksPerBackground*2
        self._fMRIresponses=numpy.zeros((numTrialsPerRun,2))
        self._fMRIjitters=numpy.zeros((numTrialsPerRun,1+self._numContour))

    def _setOriJitter(self, condition):
        if (condition==0) | (condition==2):#100% scrambled
            #oriJitters=numpy.random.randint(-45, 45, self._numContour)
            randomOrient=numpy.repeat([1,-1],numpy.ceil(self._numContour/2.0)) 
            numpy.random.shuffle(randomOrient)
            randomOrient=numpy.delete(randomOrient,self._numContour)
            oriJitters=numpy.repeat(45, self._numContour)
            oriJitters = oriJitters*randomOrient
            print('scrambled, actual jitters:%s'% ', '.join(str(x) for x in oriJitters))
        elif condition==1: #staircased with background
            #rawStairJitter=self._stair.next()
            #see note at staircase setup
            #self._stairJitter= -1*rawStairJitter+45
            WeibullJitter=self._stair.next()
            self._stairJitter= 90 - WeibullJitter
            if self._stairJitter==0:
                oriJitters=numpy.zeros((self._numContour))
            else:
                #oriJitters=numpy.random.randint(-self._stairJitter, self._stairJitter, self._numContour)
                randomOrient=numpy.repeat([1,-1],numpy.ceil(self._numContour/2.0)) 
                numpy.random.shuffle(randomOrient)
                randomOrient=numpy.delete(randomOrient,self._numContour)
                oriJitters=numpy.repeat(self._stairJitter, self._numContour)
                oriJitters = oriJitters*randomOrient
            print('stair range: %d, actual jitters:%s'%(self._stairJitter, ', '.join(str(x) for x in oriJitters)))
        else: #no background--use last staircase val (which has already been flipped)
            if self._stairJitter==0:
                oriJitters=numpy.zeros((self._numContour))
            else:
                #oriJitters=numpy.random.randint(-self._stairJitter, self._stairJitter, self._numContour)
                randomOrient=numpy.repeat([1,-1],numpy.ceil(self._numContour/2.0)) 
                numpy.random.shuffle(randomOrient)
                randomOrient=numpy.delete(randomOrient,self._numContour)
                oriJitters=numpy.repeat(self._stairJitter, self._numContour)
                oriJitters = oriJitters*randomOrient
            print('stair range: %d, actual jitters:%s'%(self._stairJitter, ', '.join(str(x) for x in oriJitters)))
        self._oriJitters=oriJitters
        self._fMRIjitters[self._iT,0]=condition
        self._fMRIjitters[self._iT,1:]=oriJitters

    def _updateStair(self, condition, response):
        #store the response in a list
        self._fMRIresponses[self._iT,0]=condition#0,1,2,3 for the 4 trial types
        self._fMRIresponses[self._iT,1]=response #actually, right/wrong, not "the" response
        if condition==1:
            #staircased with background
            self._stair.addResponse(response)

    def writeDataFile(self):
        data={'subject':self._subject,
            'run':self._runNumber,
            'blockOrder':self._blockOrder,
            'responses':self._fMRIresponses, # actually, right/wrong, not "the" response
            'responseKeys':self._keepResponseKeys, 
            'jitters':self._fMRIjitters,
            'stair reversals':self._stair.reversalIntensities,
            'conditionNames':self._conditions,
            'trialList':self._trialListMaster,
            'stimOnsetTimes':self._stimOnsetTimes,
            'actualSides':self._keepSides,
            'localizerResponses':self._locResponses,
            'localizerBlockOrder':self._blockLoc
            }
        misc.toFile(self._outFile,data)
        self.writeTsv() 

    def writeTsv(self): 
        with open(self._tsvFile, 'a') as fid:
            fid.write('Condition\tOnsetTime\tDuration\tjitter\tresponse\tcorrect\n')
            for stim in self._stimOnsetTimes:
                fid.write('%s\t%2.2f\t%2.2f\t%2.2f\t%s\t%d\n' %(stim[1],
                                                                stim[2],
                                                                self._stimDuration,
                                                                numpy.absolute(self._fMRIjitters[stim[0]][1]), # not sure about the formatting of this, should be an index i, j?
                                                                self._keepResponseKeys[stim[0]],
                                                                self._fMRIresponses[stim[0]][1]))
            fid.close()

class ExpInfoPsych(ExpInfoX):
    def __init__(self, subject, runNumber, longInstructions, eyetrack):
        self._eyetracking=eyetrack
        nowTime=datetime.datetime.now()
        if self._eyetracking=='Eyelink':
            #set up eyetracker communications
            iohub_tracker_class_path = 'eyetracker.hw.sr_research.eyelink.EyeTracker'
            eyetracker_config = dict()
            eyetracker_config['name'] = 'tracker'
            eyetracker_config['model_name'] = 'EYELINK 1000 REMOTE'
            #does this work? custom file name, which is still limited to 8.3, DOS-style
            #eyetracker_config['default_native_data_file_name']='%02d%02d%02.edf'%(nowTime.day,nowTime.hour,nowTime.minute)
            eyetracker_config['runtime_settings'] = dict(sampling_rate=500,track_eyes='BOTH')
            self.io = launchHubServer(**{iohub_tracker_class_path: eyetracker_config})
            self.tracker = self.io.devices.tracker
            self._outFileNameEye='%s_%04d%02d%02d_%02d%02d_COP_psych_run%02d.edf'%(subject,nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute,runNumber)
            self._outFileDirEye=os.path.join('eyetracking', '%s'%(subject) ) 
            self._outFileEye=os.path.join(self._outFileDirEye,self._outFileNameEye) 
        ExpInfoX.__init__(self, subject, runNumber, longInstructions, self._eyetracking)
        self._outFileName='%s_%04d%02d%02d_%02d%02d_COP_psych_run%02d.pickle'%(self._subject,nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute,self._runNumber)
        self._outFile=os.path.join('subjectResponseFiles',self._outFileName)
        self._timingAndConditions()
        self._responseKeys=['left','right']

    def cleanup(self):
        self.win.close()
        if self._eyetracking=='Eyelink':
            #close the communication
            self.tracker.setConnectionState(False)
            #shut down the iohub engine
            self.io.quit()
            # check if eyetracking subdir exists
            if not os.path.isdir(self._outFileDirEye):
                os.makedirs(self._outFileDirEye)
            #rename the EDF file
            shutil.copy2('et_data.EDF',self._outFileEye)
        core.quit()

    def _timingAndConditions(self):
        self._stimDuration=1.0
        self._baselineBlank=1.5
        self._numStairs=3
        self._numTrialsPerStair=30
        self._numCatchBG=20
        self._numNObg = 20
        self._numTrialsPerBlock = self._numStairs*self._numTrialsPerStair + self._numCatchBG + self._numNObg
        self._blockOrder=[0,1]#just two blocks. instructions are elsewhere
        trialList=[]
        #just set all trial jitters to 500ms, which is the min required duration
        trialTimeJitterList=[]
        for iB in range(len(self._blockOrder)):
            stairTrials=numpy.repeat(numpy.arange(self._numStairs),self._numTrialsPerStair)
            catchTrials=numpy.repeat([3],self._numCatchBG)
            noBGtrials=numpy.repeat([4],self._numNObg)
            theseTrials=numpy.concatenate((stairTrials, catchTrials, noBGtrials))
            numpy.random.shuffle(theseTrials)
            trialList.append(theseTrials[:])
            trialTimeJitterList.append([0.5]*self._numTrialsPerBlock)
        self._trialListMaster=trialList
        self._conditions={'0':{'name':'background, staircase 1','jitter':'N/A'},
                            '1':{'name':'background, staircase 2','jitter':'N/A'},
                            '2':{'name':'background, staircase 3','jitter':'N/A'},
                            '3':{'name':'catch with Background','jitter':0},
                            '4':{'name':'noBackground, scrambled','jitter':45}
                            }
        self._backgrounds=[True,True,True,True,False]
        #remaining parameters for the psi staircases
        self._alphaRange=[45,90] #endpoints of the "location parameter"
        self._alphaPrecision=1
        self._intensityRange=[45,90]#endpoints of the range of stimulus "intensities"
        self._intensityPrecision=3 #STEP SIZE, not number f steps, unless it's log, then it's number ofstep
        self._betaRange=[0.25,25]#range of slopes
        self._betaPrecision=.5
        self._stepType='lin'
        self._delta=0.08  # maps to MATLAB's guessRate (gamma)
        self._psiStairs=[]
        for iB,block in enumerate(self._blockOrder):
            self._psiStairs.append([0]*self._numStairs)
        for i in range(len(self._blockOrder)):
            for j in range(self._numStairs):
                self._psiStairs[i][j]=data.PsiHandler(nTrials=self._numTrialsPerStair,#*241,#why was this here????
                                    intensRange=self._intensityRange,
                                    alphaRange=self._alphaRange,
                                    betaRange=self._betaRange,
                                    intensPrecision=self._intensityPrecision,
                                    alphaPrecision=self._alphaPrecision,
                                    betaPrecision=self._betaPrecision,
                                    delta=self._delta,
                                    stepType=self._stepType,
                                    #TwoAFC=False,
                                    expectedMin=0.5)
        self._timeJitterListMaster=trialTimeJitterList
        numPsych=self._numStairs*self._numTrialsPerStair*len(self._blockOrder)
        numCatch=self._numCatchBG*len(self._blockOrder)
        numNObg=self._numNObg*len(self._blockOrder)
        self._allResponses=numpy.zeros((numPsych+numCatch+numNObg,2))
        self._psychResponses=numpy.zeros((numPsych,3))#why 3?
        self._catchResponses=numpy.zeros((numCatch,2))
        self._noBGresponses=numpy.zeros((numNObg,2))
        self._conditionCounter=[0]*len(self._conditions)
        self._psychJitters=numpy.zeros((numPsych+numCatch+numNObg,1+self._numContour))



    def _setOriJitter(self, condition):
        if condition<3:
            #condition number is the stair repetition :)
            WeibullJitter=self._psiStairs[self._block][condition].next()
            jitter = 90 - WeibullJitter
            if jitter<0.1:
                oriJitters=numpy.zeros((self._numContour))
            else:
                randomOrient=numpy.repeat([1,-1],numpy.ceil(self._numContour/2.0))
                numpy.random.shuffle(randomOrient)
                randomOrient=numpy.delete(randomOrient,self._numContour)
                oriJitters=numpy.repeat(jitter, self._numContour)
                oriJitters = oriJitters*randomOrient
            print('stair range: %f, actual jitters:%s'%(jitter, ', '.join(str(x) for x in numpy.nditer(oriJitters))))
        elif condition==3:
            #catch trial with 0deg
            oriJitters=[0]*self._numContour
        else:
            #no BG with 45 deg
            randomOrient=numpy.repeat([1,-1],numpy.ceil(self._numContour/2.0))
            numpy.random.shuffle(randomOrient)
            randomOrient=numpy.delete(randomOrient,self._numContour)
            oriJitters=numpy.repeat(45, self._numContour)
            oriJitters = oriJitters*randomOrient
        self._oriJitters=oriJitters
        self._psychJitters[self._iT,0]=condition
        self._psychJitters[self._iT,1:]=oriJitters

    def _updateStair(self, condition, response):
        thisTrialNum=self._conditionCounter[condition]
        if condition<3:
            print('updating stair for block %d, condition %d'%(self._block,condition))
            self._psychResponses[thisTrialNum,0]=response
            self._psiStairs[self._block][condition].addResponse(response)
        elif condition==3:
            self._catchResponses[thisTrialNum,0]=response
        else:
            self._noBGresponses[thisTrialNum,0]=response
        self._allResponses[self._iT,0]=condition
        self._allResponses[self._iT,1]=response
        self._conditionCounter[condition]+=1



    def writeDataFile(self):
        slopes1=[]
        locations1=[]
        intensities1=[]
        responses1=[]
        slopes2=[]
        locations2=[]
        intensities2=[]
        responses2=[]
        slopes3=[]
        locations3=[]
        intensities3=[]
        responses3=[]
        for iB, block in enumerate(self._blockOrder):
            slopes1.append(self._psiStairs[block][0].estimateLambda()[1])
            locations1.append(self._psiStairs[block][0].estimateLambda()[0])
            intensities1.append(self._psiStairs[block][0].intensities)
            responses1.append(self._psiStairs[block][0].data)
            slopes2.append(self._psiStairs[block][1].estimateLambda()[1])
            locations2.append(self._psiStairs[block][1].estimateLambda()[0])
            intensities2.append(self._psiStairs[block][1].intensities)
            responses2.append(self._psiStairs[block][1].data)
            slopes3.append(self._psiStairs[block][2].estimateLambda()[1])
            locations3.append(self._psiStairs[block][2].estimateLambda()[0])
            intensities3.append(self._psiStairs[block][2].intensities)
            responses3.append(self._psiStairs[block][2].data)
        data={'intensityRange':self._intensityRange,
            'alphaRange':self._alphaRange,
            'betaRange':self._betaRange,
            'delta':self._delta,
            'subject':self._subject,
            'run':self._runNumber,
            'intensityPrecision':self._intensityPrecision,
            'stepType':self._stepType,
            #need to flatten the nested staircases
            #the list of staircases is
            'slopes1':slopes1,
            'locations1':locations1,
            'intensities1':intensities1,
            'responses1':responses1,
            'slopes2':slopes2,
            'locations2':locations2,
            'intensities2':intensities2,
            'responses2':responses2,
            'slopes3':slopes3,
            'locations3':locations3,
            'intensities3':intensities3,
            'responses3':responses3,
            'allResponses':self._allResponses,
            'psychResponses':self._psychResponses,
            'catchResponses':self._catchResponses,
            'noBGresponses':self._noBGresponses,
            'psychJitters':self._psychJitters,
            'trialList':self._trialListMaster,
            'actualSides':self._keepSides
            }
        misc.toFile(self._outFile,data)
        if self._eyetracking=='yes':
            #close the communication
            self.tracker.setConnectionState(False)
            #shut down the iohub engine
            self.io.quit()
            # check if eyetracking subdir exists
            if not os.path.isdir(self._outFileDirEye):
                os.makedirs(self._outFileDirEye)
            #rename the EDF file
            shutil.copy2('et_data.EDF',self._outFileEye)


class stimCOP(object):
    def __init__(self,win):
        self._win=win
        self._cpd=2.0/0.4
        self._radius=0.2
        self._narrowEnd=0
        self._fieldSize=[14,11.3]
        self._revFreq=2
        self._phaseDuration=1.0/(2.0*self._revFreq)
        self._initialPhase=0.25
        self._phase=0.25
        self._loadLocations()
        self._gratingArray=visual.ElementArrayStim(self._win,
                                                   fieldPos=(0.0,0.0),
                                                   fieldShape='square',
                                                   nElements=self._numDistractors+self._numContour,
                                                   xys=self._gratingLocs,#these might needs to be converted into "from 0,0)?
                                                   oris=self._gratingOris,
                                                   sizes=2*self._radius,#width  not radius
                                                   sfs=self._cpd,
                                                   elementTex='sin',
                                                   elementMask='gauss',
                                                   units='deg')
        self._fixationMark=visual.Rect(self._win,
                                       width=0.2,
                                       height=0.2,
                                       fillColor=[1,1,1],
                                       fillColorSpace='rgb',
                                       units='deg')
        self._blank=visual.Rect(self._win,
                                width=50,
                                height=40,
                                fillColor=[0,0,0],
                                fillColorSpace='rgb',
                                units='deg')
        self._dot=visual.Circle(self._win,radius=0.025,units='norm',
                fillColor=(-1,-1,-1),fillColorSpace='rgb')
        self._textMsg=visual.TextStim(self._win,
                                      text='Preparing the task',
                                      units='norm',
                                      pos=(0,0),
                                      height=0.065,
                                      alignVert='top',
                                      wrapWidth=1.9)
        self._textMsg.draw()
        self._win.flip()

    @property
    def narrowEnd(self):
        return self._narrowEnd
    @narrowEnd.setter
    def narrowEnd(self, value):
        self._narrowEnd = value

    @property
    def phaseDuration(self):
        return self._phaseDuration

    @property
    def numContour(self):
        return self._numContour
    @numContour.setter
    def numContour(self, value):
        self._numContour=value

    def _loadLocations(self):
        #locs=sio.loadmat('260Trials.mat')
        #self._allEggs=locs['keepEggs'][0]
        #self._allDistractors=locs['keepDistractors'][0]
        #numpy.random.shuffle(self._allEggs)
        #numpy.random.shuffle(self._allDistractors)
        numTrials=1000
        allEggs=misc.fromFile('%dTrials_V4.pickle'%numTrials)
        #SHUFFLE THEM for each run so I can re-use one list
        #but I need to co-shuffle the eggs/distractors.
        newOrder=numpy.arange(numTrials/2)
        numpy.random.shuffle(newOrder)
        self._leftEggs=allEggs['leftEggs'][newOrder,:]
        self._rightEggs=allEggs['rightEggs'][newOrder,:]
        self._leftDistractors=allEggs['leftDistractors'][newOrder,:]
        self._rightDistractors=allEggs['rightDistractors'][newOrder,:]
        self._numDistractors=len(self._leftDistractors[0,:])
        self._numContour=len(self._leftEggs[0,:])
        eggLocs=self._leftEggs[0,:,0:2]
        eggOris=self._leftEggs[0,:,2]
        distractorLocs=self._leftDistractors[0,:,0:2]
        distractorOris=self._leftDistractors[0,:,2]
        self._gratingLocs=numpy.concatenate((eggLocs,distractorLocs))
        self._gratingOris=numpy.concatenate((eggOris,distractorOris))


    def setLocation(self, jitterArray, iT, background):
        #need to know which side the egg points to
        #where to do the rand (here or it's own method)?
        #need to have two location arrays: one for right and one for left
        self._narrowEnd=numpy.random.randint(2)
        if self._narrowEnd==0:
            #left
            eggLocs=self._leftEggs[iT,:,0:2]
            eggOris=self._leftEggs[iT,:,2]
            distractorLocs=self._leftDistractors[iT,:,0:2]
            distractorOris=self._leftDistractors[iT,:,2]
        else:
            eggLocs=self._rightEggs[iT,:,0:2]
            eggOris=self._rightEggs[iT,:,2]
            distractorLocs=self._rightDistractors[iT,:,0:2]
            distractorOris=self._rightDistractors[iT,:,2]
        #add jitter to eggs
        #jitter is AN ARRAY with jitter for each egg
        #add plus or minus "jitter" degrees of jitter to each egg orientation
        #numEgg=len(eggOris)
        #jitterArray=jitter*numpy.random.choice(numpy.array(2*numEgg*[1]),numEgg,replace=False)
        eggOris=eggOris+jitterArray
        if background is True:
            self._gratingLocs=numpy.concatenate((eggLocs,distractorLocs))
            self._gratingOris=numpy.concatenate((eggOris,distractorOris))
        else:
            fakeLocs=100*numpy.ones((self._numDistractors,2))
            fakeOris=numpy.zeros((self._numDistractors))
            self._gratingLocs=numpy.concatenate((eggLocs,fakeLocs))
            self._gratingOris=numpy.concatenate((eggOris,fakeOris))

    def switchPhase(self):
        if self._phase - self._initialPhase==0:
            self._phase=self._initialPhase+0.5
        else:
            self._phase=self._initialPhase

    def draw(self):
        self._gratingArray.xys=self._gratingLocs
        self._gratingArray.oris=self._gratingOris
        self._gratingArray.phases=self._phase
        self._gratingArray.draw()
        self._fixationMark.draw()
        self._win.flip()

    def drawBlank(self):
        self._fixationMark.draw()
        self._win.flip()

    def drawText(self,msg):
        self._blank.draw()
        self._textMsg.pos=(0,0)
        self._textMsg.text=msg
        self._textMsg.draw()
        self._win.flip()

    def drawBreak(self):
        self._blank.draw()
        self._textMsg.pos=(0,0)
        self._textMsg.text='You have finished half of the trials! Press any key to continue.'
        self._textMsg.draw()
        self._win.flip()

    def drawCustom(self, text=None, fixation=True, jitter=None, side=0, background=False, iT=0):
        self._blank.draw()
        if jitter is not None:
            if side==0:
                #left
                eggLocs=self._leftEggs[iT,:,0:2]
                eggOris=self._leftEggs[iT,:,2]
                distractorLocs=self._leftDistractors[iT,:,0:2]
                distractorOris=self._leftDistractors[iT,:,2]
            else:
                eggLocs=self._rightEggs[iT,:,0:2]
                eggOris=self._rightEggs[iT,:,2]
                distractorLocs=self._rightDistractors[iT,:,0:2]
                distractorOris=self._rightDistractors[iT,:,2]
            if len(jitter)>1:
                jitterArray=jitter
            else:
                jitterArray=numpy.zeros((15))
            eggOris=eggOris+jitterArray
            if background is True:
                self._gratingLocs=numpy.concatenate((eggLocs,distractorLocs))
                self._gratingOris=numpy.concatenate((eggOris,distractorOris))
            else:
                fakeLocs=100*numpy.ones((self._numDistractors,2))
                fakeOris=numpy.zeros((self._numDistractors))
                self._gratingLocs=numpy.concatenate((eggLocs,fakeLocs))
                self._gratingOris=numpy.concatenate((eggOris,fakeOris))
            self._gratingArray.xys=self._gratingLocs
            self._gratingArray.oris=self._gratingOris
            self._gratingArray.phases=self._phase
            self._gratingArray.draw()


        if fixation is True:
            self._fixationMark.draw()

        if text is not None:
            self._textMsg.pos=(0,0.6)
            self._textMsg.text=text
            self._textMsg.draw()

        self._win.flip()

    def drawDot(self, x, y):
        self._blank.draw()
        self._dot.pos=(x,y)
        self._dot.draw()
        self._win.flip()



def main():

    ### subject info ###
    #check for a previous run...
    os.system('rm contourObject_lastrun.pickle')


    subInfo={'subject':'1','runType':['fMRI','psychophysics'],
            'longInstructions':['yes','no'],'functionalLocalizer':['yes','no'],
            'eyetracking':['Eyelink','none','Avotec']}

    #update session info
    infoDlg=gui.DlgFromDict(dictionary=subInfo,title='Scan Parameters',
                            order=['subject','runType',
                            'longInstructions','functionalLocalizer','eyetracking'],
                            tip={'subject':'subject number',
                                 'runType':'fMRI or psychophysics',
                                 'longInstructions':'Long instructions with practice trials? yes or no)',
                                 'functionalLocalizer':'yes or no',
                                 'eyetracking':'Eyelink, Avotec, or none',})
    if infoDlg.OK:
        #create my expInfo object
        if subInfo['runType']=='fMRI':
            #look for previous runs to determine run number
            nowTime=datetime.datetime.now()
            stubFile='%s_%04d%02d%02d_*_COP_fMRI_run*.pickle'%(subInfo['subject'],nowTime.year,nowTime.month,nowTime.day) 

            subFiles=sorted(glob.glob('subjectResponseFiles/%s'%stubFile))
            if len(subFiles)>0:
                #found a previous run--take the last run
                num=subFiles[-1].find('run') 
                subInfo['runNumber']=int(subFiles[-1][num+3:num+5])+1 
            else:
                subInfo['runNumber']=1
            expInfo=ExpInfofMRI(subInfo['subject'],
                     subInfo['runNumber'],
                     subInfo['longInstructions'],
                     subInfo['eyetracking'])

        else:
            #look for previous runs to determine run number
            nowTime=datetime.datetime.now()
            stubFile='%s_%04d%02d%02d_*_COP_psych_run*.pickle'%(subInfo['subject'],nowTime.year,nowTime.month,nowTime.day) 
            subFiles=sorted(glob.glob('subjectResponseFiles/%s'%stubFile))
            if len(subFiles)>0:
                #found a previous run--take the last run
                num=subFiles[-1].find('run') 
                subInfo['runNumber']=int(subFiles[-1][num+3:num+5])+1 
            else:
                subInfo['runNumber']=1
            expInfo=ExpInfoPsych(subInfo['subject'],
                     subInfo['runNumber'],
                     subInfo['longInstructions'],
                     subInfo['eyetracking'])

        misc.toFile('contourObject_lastrun.pickle',subInfo)
        os.system('rm contourObject_lastrun.pickle')
    else:
        print 'user cancelled'
        core.quit()

    stimObject=stimCOP(expInfo.win)

    # run eyetracker calibration
    if subInfo['eyetracking']=='Avotec':
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
        mydataFile=expInfo.eyetrackingFile
        mycmd='dataFile_NewName "'+mydataFile+'"'
        vpx.VPX_SendCommand(mycmd.encode('ascii'))
        #recording starts automatically

        runCal=True
        while runCal is True:
            stimObject.drawCustom(text='Operator, press c to start eyetracker calibration or m to move on',fixation=False)
            thisKey=expInfo.waitForKey()
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

                    stimObject.drawDot(x,y)
                    core.wait(20*(1/60.0+0.05))
                    stimObject.drawBlank()
                    print('sending calibration snap command')
                    mymsg='calibration_snap %d'%(thisPoint+1)
                    vpx.VPX_SendCommand(mymsg.encode('ascii'))
                    stimObject.drawDot(x,y)
                    core.wait(19*(1/60.0+0.05))
                    stimObject.drawBlank()
                    core.wait(0.2)
    elif subInfo['eyetracking'] is 'Eyelink':
        expInfo.tracker.runSetupProcedure()


    if subInfo['longInstructions'] is 'yes':
        if subInfo['eyetracking'] is 'Avotec':
            mymsg='dataFile_InsertString start instructions'
            vpx.VPX_SendCommand(mymsg)
        elif subInfo['eyetracking'] is 'Eyelink':
            #start recording
            expInfo.io.clearEvents()
            expInfo.tracker.setRecordingState(True)
            msg='start instruction/practice block'
            expInfo.tracker.sendMessage(msg)

        expInfo.doInstructions(stimObject)

        if subInfo['eyetracking'] is 'Avotec':
            mymsg='dataFile_InsertString end instructions'
            vpx.VPX_SendCommand(mymsg)
        elif subInfo['eyetracking'] is 'Eyelink':
            #start recording
            msg='end instruction/practice block'
            expInfo.tracker.sendMessage(msg)
            expInfo.io.clearEvents()
            expInfo.tracker.setRecordingState(False)

    print(expInfo.blockOrder)
    #initialize timers
    trialTimer=core.CountdownTimer()
    blockTimer=core.CountdownTimer()
    phaseTimer=core.CountdownTimer()
    globalClock=core.Clock()
    #timeEpsilon=0.017
    timeEpsilon=0.0025
    ### wait for subject to be ready ###
    if subInfo['runType']=='fMRI':
        buttonPrefix=''
    else:
        buttonPrefix='arrow '
    msg="The experiment is about to begin. Decide if the contour is pointing to "\
    "the left or the right and press the left or right %sbutton. "\
    "If you aren't sure, it's OK to guess! Press any button when you are ready to start."%buttonPrefix
    stimObject.drawCustom(text=msg, fixation=True, jitter=[0], background=False)
    expInfo.waitForKey()

    if subInfo['runType']=='fMRI':
        locLength=24*6.5
        print('total scan length with Loc: %d s'%(expInfo.totalScanLength+locLength))
        print('total scan length without Loc: %d s'%(expInfo.totalScanLength))
        stimObject.drawText('Ready to scan, waiting for scanner trigger')
        expInfo.waitForKey(trigger=True)
    globalClock.reset()
    if subInfo['eyetracking'] is 'Eyelink':
        #start recording
        expInfo.io.clearEvents()
        expInfo.tracker.setRecordingState(True)
    if subInfo['functionalLocalizer']=='yes':
        expInfo.doLoc(stimObject)
    for iBlock, condition in enumerate(expInfo.blockOrder):
        if (subInfo['eyetracking'] is 'Eyelink') & (subInfo['runType']=='psychophysics') & (iBlock > 0):
            #start recording
            expInfo.io.clearEvents()
            expInfo.tracker.setRecordingState(True)
        if subInfo['eyetracking'] is 'Avotec':
            mymsg='dataFile_InsertString block_%d_condition_%d_start'%(iBlock,condition)
            vpx.VPX_SendCommand(mymsg)
        elif subInfo['eyetracking'] is 'Eyelink':
            msg='start block_%d_condition_%d_start'%(iBlock,condition)
            expInfo.tracker.sendMessage(msg)

        if subInfo['runType']=='psychophysics':
            stimObject.drawBlank()
            blockTimer.reset()
            blockTimer.add(expInfo.baselineBlank)
            while blockTimer.getTime()>0:
                expInfo.getResponses(99)
        expInfo.setBlock(iBlock) #gets pre-shuffled trials and trial timing for this block
        blockTimer.reset()
        if condition==99: #fMRI starting/ending rest
            blockTimer.add(expInfo.baselineBlank)
            stimObject.drawBlank()
            while blockTimer.getTime()>timeEpsilon:
                expInfo.getResponses(99)#check for quit keys
        else:
            for iTrial, condition in enumerate(expInfo.trials): #ANG 20171211: didn't this just overwrite 'condition' from block enumerate?
                #startTime=t_timer()
                expInfo.setCondition(iTrial, condition, stimObject)#sets jitterOri, location, left/right, correct answer, jitteredBlankTIme
                expInfo.haveResponse=0
                #add contrast reverse
                expInfo.addOnsetTime(condition,globalClock.getTime())
                numDraws=numpy.int(expInfo.stimDuration/stimObject.phaseDuration)
                if subInfo['eyetracking'] is 'Avotec':
                    mymsg='dataFile_InsertString block_%d_condition_%d_trial_%d_stimOnset'%(iBlock,condition,iTrial)
                    vpx.VPX_SendCommand(mymsg)
                elif subInfo['eyetracking'] is 'Eyelink':
                    msg='block_%d_condition_%d_trial_%d_stimOnset'%(iBlock,condition,iTrial)
                    expInfo.tracker.sendMessage(msg)

                for iDraw in range(numDraws):
                    phaseTimer.reset()
                    phaseTimer.add(stimObject.phaseDuration)
                    stimObject.draw()
                    while phaseTimer.getTime()>timeEpsilon:
                        expInfo.getResponses(condition)
                if subInfo['eyetracking'] is 'Avotec':
                    mymsg='dataFile_InsertString block_%d_condition_%d_trial_%d_stimOff'%(iBlock,condition,iTrial)
                    vpx.VPX_SendCommand(mymsg)
                elif subInfo['eyetracking'] is 'Eyelink':
                    msg='block_%d_condition_%d_trial_%d_stimOff'%(iBlock,condition,iTrial)
                    expInfo.tracker.sendMessage(msg)
                stimObject.drawBlank()
                trialTimer.reset()
                trialTimer.add(expInfo.jitterBlankTime)
                while trialTimer.getTime()>timeEpsilon:
                    expInfo.getResponses(condition)
                if subInfo['runType']=='psychophysics':
                    while expInfo.haveResponse==0:
                        stimObject.drawBlank()
                        expInfo.getResponses(condition)
                    trialTimer.reset()
                    trialTimer.add(expInfo.jitterBlankTime)
                    while trialTimer.getTime()>timeEpsilon:
                            stimObject.drawBlank()
                            expInfo.getResponses(99)
                if subInfo['eyetracking'] is 'Avotec':
                    mymsg='dataFile_InsertString block_%d_condition_%d_trial_%d_trialEnd'%(iBlock,condition,iTrial)
                    vpx.VPX_SendCommand(mymsg)
                elif subInfo['eyetracking'] is 'Eyelink':
                    msg='block_%d_condition_%d_trial_%d_trialEnd'%(iBlock,condition,iTrial)
                    expInfo.tracker.sendMessage(msg)

                #endTime=t_timer()
                #print('*#*#*#*#*#*#*#*#*#*#*#*trial duration %f'%(endTime-startTime))
        #if psychophysics, offer a break after each block
        if (subInfo['runType']=='psychophysics') & (iBlock<len(expInfo.blockOrder)-1):
            if subInfo['eyetracking'] is 'Eyelink':
                msg='block_%d_condition_%d_blockEnd'%(iBlock,condition)
                expInfo.tracker.sendMessage(msg)
                #stop recording at end of block
                expInfo.tracker.setRecordingState(False)
            stimObject.drawBreak()
            expInfo.waitForKey()
        print('*^*^*^*^*^*^*^*^*^*^*^*end of block %d, global clock %f'%(iBlock,globalClock.getTime()))
        if subInfo['eyetracking'] is 'Avotec':
            mymsg='dataFile_InsertString block_%d_condition_%d_blockEnd'%(iBlock,condition)
            vpx.VPX_SendCommand(mymsg)
        elif subInfo['eyetracking'] is 'Eyelink':
            msg='block_%d_condition_%d_blockEnd'%(iBlock,condition)
            expInfo.tracker.sendMessage(msg)
    expInfo.writeDataFile()
    if subInfo['eyetracking'] is 'Avotec':
        #close the data file
        vpx.VPX_SendCommand('dataFile_Close'.encode('ascii'))

        #close link to eyetracker
        connectResult = vpx.VPX_DisconnectFromViewPoint()
        print('finished successfully!')
    elif subInfo['eyetracking'] is 'Eyelink':
        expInfo.tracker.setRecordingState(False)

    expInfo.cleanup()

if __name__ == "__main__":
    main()
