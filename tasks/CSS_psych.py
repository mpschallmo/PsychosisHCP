#!/usr/bin/env python2
# author: agrant, edits by mps

from psychopy.iohub.client import launchHubServer
from psychopy import visual, core, data, event, monitors, gui,misc, sound
import numpy
import os
import datetime
from timeit import default_timer as t_timer
import shutil

from psychopy.hardware import crs
debug=0

class ExpInfoX(object):
    def __init__(self, subject, runNumber, longInstructions, eyetrack):
        self.subject=subject
        self._runNumber=runNumber
        self.longInstructions=longInstructions
        self._eyetracking=eyetrack
        if self._eyetracking=='yes':
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
        self._mon='BitsSharp'
        self._subMonitor=monitors.Monitor(self._mon)
        self._screenSize=self._subMonitor.getSizePix()
        self.win=visual.Window(self._screenSize,monitor=self._mon,units='deg',useFBO=True,
                        screen=0,color=[0,0,0],colorSpace='rgb',fullscr=True,allowGUI=False)
        self._bits = crs.BitsSharp(win=self.win, mode='mono++')
        self._bits.gammaCorrectFile='greyLums.txt'
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
        self._continueKeys=['c','home']
        self._triggerKeys=['t']
        nowTime=datetime.datetime.now()
        #self._outFileName='css_subj_%s_run_%02d_%04d%02d%02d_%02d%02d.pickle'%(self.subject,self._runNumber,nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute)
        #self._outFile=os.path.join('subjectResponseFiles',self._outFileName)
        #self._timingAndConditions()
        self._doRepeat=0 # change this to 1 when repeating practice
        self._correctAnswer=0
        self._iT=-1 #GLOBAL trial counter
        self._keepTargetContrasts=[]
        self._keepSurroundContrasts=[]
        self._keepDeltas=[]
        self._keepTaskSides=[]
        self._keepOris=[]
        self._keepResponses={}
        self._haveResponse=0
        self._block=0
        self._blockOrder=[]
        self._numTrialsPerCond=8
        self._stimDuration=0.7
        self._totalScanTime=0
        self.beep=sound.Sound(850,secs=0.25,sampleRate=44100, bits=8)
        self.beep.setVolume(0.3)




    @property
    def correctAnswer(self):
        return self._correctAnswer
    @correctAnswer.setter
    def correctAnswer(self, value):
        self._correctAnswer = value

    @property
    def haveResponse(self):
        return self._haveResponse
    @haveResponse.setter
    def haveResponse(self, value):
        self._haveResponse=value

    @property
    def block(self):
        return self._block
    @block.setter
    def block(self, value):
        self._block=value


    @property
    def blockOrder(self):
        return self._blockOrder
    @blockOrder.setter
    def blockOrder(self,value):
        self._blockOrder=value

    @property
    def baselineBlank(self):
        return self._baselineBlank
    @baselineBlank.setter
    def baselineBlank(self, value):
        self._baselineBlank=value

    @property
    def responseBlank(self):
        return self._responseBlank
    @responseBlank.setter
    def responseBlank(self, value):
        self._responseBlank=value

    @property
    def numTrialsPerCond(self):
        return self._numTrialsPerCond
    @numTrialsPerCond.setter
    def numTrialsPerCond(self, value):
        self._numTrialsPerCond=value

    @property
    def stimDuration(self):
        return self._stimDuration
    @stimDuration.setter
    def stimDuration(self, value):
        self._stimDuration=value

    @property
    def totalScanTime(self):
        return self._totalScanTime


    def _timingAndConditions(self):
        pass


    def waitForKey(self,trigger=False):#non specific (trigger vs button press...)
        if trigger is True:
            gotTrigger=None
            while not gotTrigger:
                thisKey=event.waitKeys()
                gotTrigger = thisKey[0] in self._triggerKeys
                if thisKey[0] in self._quitKeys:
                    self.cleanup()
                else:
                    event.clearEvents()
        else:
            thisKey=None
            while thisKey==None:
                thisKey = event.waitKeys()
            if thisKey in self._quitKeys:
                self.cleanup()
            else:
                event.clearEvents()

    def waitForContKey(self,trigger=False):#non specific (trigger vs button press...)
        if trigger is True:
            gotTrigger=None
            while not gotTrigger:
                thisKey=event.waitKeys()
                gotTrigger = thisKey[0] in self._triggerKeys
                if thisKey[0] in self._quitKeys:
                    self.cleanup()
        else:
            contKey=None
            while not contKey:
                thisKey = event.waitKeys()
                contKey = thisKey[0] in self._continueKeys
                if thisKey[0] in self._quitKeys:
                    self.cleanup()
                if thisKey[0] in self._repeatKeys:
                    self._doRepeat = 1
                else:
                    self._doRepeat = 0

    def writeDataFile(self):
        pass

    def getResponses(self,condition):
        for key in event.getKeys():
            if key in self._quitKeys:
                self.writeDataFile()
                self.cleanup()
            #elif key in self._pauseKeys: #DISABLE THIs FOR FMRI?
                #wait....
                #goPause(expInfo) #FIX THIS
            elif (key in self._responseKeys) & (condition<98) & (self._haveResponse==0):
                if key==self._correctAnswer:
                    print('you typed %s, correct was %s'%(key,self._correctAnswer))
                    thisResp=1
                else:
                    print('you typed %s, correct was %s'%(key,self._correctAnswer))
                    thisResp=0
                #either way, keep the response
                self._keepResponses[self._iT]=[self._block, condition, self._iT, key,self._correctAnswer,thisResp]
                self._updateStair(condition,thisResp)
                self._haveResponse=1

    def getResponsesCont(self,side):
        for key in event.getKeys():
            if key in self._quitKeys:
                self.writeDataFile()
                self.cleanup()
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
            #elif key in self._pauseKeys: #DISABLE THIs FOR FMRI?
                #wait....
                #goPause(expInfo) #FIX THIS
            elif (key in self._responseKeys) & (self._haveResponse==0):
                self._correctAnswer=self._responseKeys[side]
                if key==self._correctAnswer:
                    respMsg='you typed %s, correct was %s'%(key,self._correctAnswer)
                    print(respMsg)
                    thisResp=1
                else:
                    respMsg='you typed %s, correct was %s'%(key,self._correctAnswer)
                    print(respMsg)
                    thisResp=0
                self._haveResponse=1
                self._keepCorr.append(thisResp)

    def _updateStair(self,condition, response):
        pass


    def setCondition(self, iTrial, condition, stimObject):
        self._iT+=1 #global trial counter
        if debug==9:
            print(self._conditions)
        print('global trial %d, condition %d [t: %2.1f%%, s: %2.1f%%]'%(self._iT+1, condition,100*self._conditions[condition]['targetContrast'],100*self._conditions[condition]['surroundContrast']))
        stimObject.targetContrast=self._conditions[condition]['targetContrast']
        stimObject.surroundContrast=self._conditions[condition]['surroundContrast']
        self._nextDelta(condition,stimObject)
        stimObject.initialPhase=numpy.random.rand()
        stimObject.setOrientation()#must set this first, because task side needs it to set the right mask ori
        stimObject.taskSide=numpy.random.randint(2)
        if debug>3:
            stimObject.taskSide=0
        if stimObject.deltaContrast<0:
            #negative dC, so the correct answer is the "other" side
            self._correctAnswer = self._responseKeys[1-stimObject.taskSide]
            print('------- deltaContrast %f, taskSide %d, correctAnswer %s'%(stimObject.deltaContrast,stimObject.taskSide,self._correctAnswer))
        else:
            self._correctAnswer=self._responseKeys[stimObject.taskSide]
            print('+++++++ deltaContrast %f, taskSide %d, correctAnswer %s'%(stimObject.deltaContrast,stimObject.taskSide,self._correctAnswer))
        #print(stimObject.targetContrast,stimObject.surroundContrast,stimObject.deltaContrast)
        self._keepTargetContrasts.append(self._conditions[condition]['targetContrast'])
        self._keepSurroundContrasts.append(self._conditions[condition]['surroundContrast'])
        self._keepDeltas.append(stimObject.deltaContrast)
        self._keepTaskSides.append(stimObject.taskSide)
        self._keepOris.append(stimObject.ori)

    def _nextDelta(self, condition, stimObject):
        pass

    def doInstructions(self, stimObject):
        oris=numpy.arange(0,180,45)
        #First thing is to always keep your eyes focused on the square in the middle (show the fixation square).
        msg='Please keep your eyes focused on the square in the middle at all times'
        stimObject.drawCustom(text=msg, fixation=True)
        self.waitForContKey()
        #Then show the segments, and explain that you're going to see stripes inside these different regions.
        msg='When the task starts, you will see stripes in these regions'
        #stimObject.drawCustom(text=msg, fixation=True, )
        #self.waitForKey()
        #Task is to compare how the stripes look in the left and right regions (marked "L" and "R").
        #Explain that this task looks at how you see contrast - contrast is how strong or faint the
        #black and white stripes look in these example pictures
        #msg='Here are some stripes'
        ori=numpy.random.choice(oris)
        stimObject.drawCustom(text=msg, fixation=True, pedestal=[0.25,0.0],ori=ori)
        self.waitForContKey()
        #(show some gratings in the L & R target
        #regions - "In this example, the one on the left is stronger than the one on the right").
        msg='Your task is to look for contrast, which is how strong or faint the black and white lines are. '\
        'In this example, the one on the left is stronger than the one on the right'
        ori=numpy.random.choice(oris)
        stimObject.drawCustom(text=msg, fixation=True, pedestal=[0.25,0.25],side=0,ori=ori)
        self.waitForContKey()

        #If the stripes on the left are stronger, press left arrow, if the stripes on the right are stronger,
        #press right arrow. Remember to keep your eyes at the center at all times, do not look right at the stripes.
        msg='If the stripes on the left are stronger, press the left arrow. If the stripes '\
        'on the right are stronger, press the right arrow. Remember to keep your eyes at the center at all times, do not look directly at the stripes.'
        stimObject.drawCustom(text=msg, fixation=True, pedestal=[0.25,0.25],side=0,ori=ori)
        self.waitForContKey()

        #Then show a very slow example trial - start with a blank screen, fixation mark and black annulus
        #outlines appear, then a target appears (25% pedestal, no surround) with a fairly large
        #increment on the right side (15%). Target stays on for 2.5 s. Then subject can respond.
        stimObject.drawCustom(text='',fixation=False)
        core.wait(0.1)
        stimObject.drawCustom(fixation=True)
        #core.wait(0.1)
        core.wait(1)
        pedestal=[0.25, 0.15]
        surround=None
        side=1
        ori=numpy.random.choice(oris)
        stimObject.drawCustom(fixation=True,  pedestal=pedestal, surround=surround,side=1,ori=ori)
        core.wait(2)
        msg='Which side had stronger contrast?'
        stimObject.drawCustom(text=msg, fixation=True, pedestal=None, surround=None)
        self.waitForKey()
        #need feedback

        #Then show a faster example (use the real task timing, 12% contrast pedestal).
        msg='Now we will try a faster example. The stripes will be on the screen for only a short time'
        stimObject.drawCustom(text=msg)
        self.waitForContKey()

        stimObject.drawCustom(text='',fixation=True)
        core.wait(0.75)

        phaseTimer=core.CountdownTimer()
        trialTimer=core.CountdownTimer()
        postTrialBlankTimer=core.CountdownTimer()
        self._correctAnswer=1
        self._haveResponse=0
        self._keepCorr=[]
        timeEpsilon=0.00015
        pedestal=[0.12, 0.15]
        ori=numpy.random.choice(oris)

        stimObject.drawCustom(text='',fixation=True,  pedestal=pedestal, surround=surround,side=1,ori=ori)
        numDraws=numpy.int(self._stimDuration/stimObject.phaseDuration)#that's an awkward split
        self.beep.play()
        for iDraw in range(numDraws):
            phaseTimer.reset()
            phaseTimer.add(stimObject.phaseDuration)
            stimObject.switchPhase()
            stimObject.drawCustom(text='',fixation=True,  pedestal=pedestal, surround=surround, side=1 ,ori=ori)
            while phaseTimer.getTime()>timeEpsilon:
                self.getResponsesInstr(1)
        while self._haveResponse==0:
            stimObject.drawCustom(fixation=True)
            self.getResponsesInstr(1)
        if self._keepCorr[0]==1:
            feedback='Correct!'
        else:
            feedback = "The correct answer was 'right side'."
        stimObject.drawCustom(text=feedback)
        self.waitForKey()

        postTrialBlankTimer=core.Clock()

        self._doRepeat = 1
        while self._doRepeat:
            msg='Now we will try 10 even faster examples. The stripes will be on the screen for only a short time.'
            stimObject.drawCustom(text=msg)
            self.waitForKey()

            stimObject.drawCustom(text='',fixation=True)
            core.wait(0.75)

            #Then show 10 more fast example trials (2.5% contrast pedestal, still no surround)
            pedestal=[0.025,0.15]
            surround=None
            self._keepCorr=[]
            for iTrial in range(10):
                self._haveResponse=0
                ori=numpy.random.choice(oris)
                side=numpy.random.randint(2)
                trialTimer.reset()
                trialTimer.add(self._stimDuration)
                #try a different timing control since drawing is VERY slow and unpredictable
                numDraws=numpy.int(self._stimDuration/stimObject.phaseDuration)#that's an awkward split
                self.beep.play()
                for iDraw in range(numDraws):
                    phaseTimer.reset()
                    phaseTimer.add(stimObject.phaseDuration)
                    stimObject.switchPhase()
                    stimObject.drawCustom(text='',fixation=True,  pedestal=pedestal, surround=surround,side=side,ori=ori)
                    while phaseTimer.getTime()>timeEpsilon:
                        self.getResponsesInstr(side)
                trialTimer.reset()
                trialTimer.add(self._responseBlank)
                stimObject.drawBlank()
                postTrialBlankTimer.reset()
                while postTrialBlankTimer.getTime()<self._responseBlank: 
                    self.getResponsesInstr(side)
                stimObject.drawBlank()
                while self._haveResponse==0:
                    self.getResponsesInstr(side)
            feedback='You got %d of 10 correct. Repeat or continue?'%(numpy.sum(self._keepCorr))
            print(self._keepCorr)
            stimObject.drawCustom(text=feedback)
            self.waitForContKey()

        #Then show an image of a target (12% pedestal) with a surround (50%). "Sometimes there will be
        #stripes in the background. You can ignore these. Your task is always the same, report
        #whether the stripes are stronger in the left or right outlined region."
        pedestal=[0.25, 0.15]
        surround=0.5
        ori=numpy.random.choice(oris)
        side=1
        msg='Sometimes there will be stripes in the background. You can ignore '\
        'these. Your task is always the same, report whether the stripes are stronger '\
        'in the left or right outlined region.'
        stimObject.drawCustom(text=msg, fixation=True,  pedestal=pedestal, surround=surround,side=1,ori=ori)
        self.waitForContKey()

        self._doRepeat=1
        while self._doRepeat:
            msg='Now we will try 10 fast examples with the background stripes you should ignore.'
            stimObject.drawCustom(text=msg)
            self.waitForContKey()

            stimObject.drawCustom(text='',fixation=True)
            core.wait(0.75)

            #Then 10 fast examples with a surround (target = 6% pedestal contrast)
            pedestal=[0.06, 0.15]
            surround=0.5
            self._keepCorr=[]
            for iTrial in range(10):
                self._haveResponse=0
                ori=numpy.random.choice(oris)
                side=numpy.random.randint(2)
                trialTimer.reset()
                trialTimer.add(self._stimDuration)
                self._haveResponse=0
                #try a different timing control since drawing is VERY slow and unpredictable
                numDraws=numpy.int(self._stimDuration/stimObject.phaseDuration)#that's an awkward split
                self.beep.play()
                for iDraw in range(numDraws):
                    phaseTimer.reset()
                    phaseTimer.add(stimObject.phaseDuration)
                    stimObject.switchPhase()
                    stimObject.drawCustom(text='',fixation=True,  pedestal=pedestal, surround=surround,side=side,ori=ori)
                    while phaseTimer.getTime()>timeEpsilon:
                        self.getResponsesInstr(side)
                trialTimer.reset()
                trialTimer.add(self._responseBlank)
                stimObject.drawBlank()
                postTrialBlankTimer.reset()
                while postTrialBlankTimer.getTime()<self._responseBlank:
                    self.getResponsesInstr(side)
                stimObject.drawBlank() 
                while self._haveResponse==0:
                    self.getResponsesInstr(side)
            feedback='You got %d of 10 correct.  Repeat or continue?'%(numpy.sum(self._keepCorr))
            print(self._keepCorr)
            stimObject.drawCustom(text=feedback)
            self.waitForContKey()

        #need option to repeat trials?


    def cleanup(self):
        self._bits.mode='bits++'
        self.win.close()
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
        core.quit()

class ExpInfoPsych(ExpInfoX):
    def __init__(self, subject, runNumber, longInstructions, eyetracking):
        ExpInfoX.__init__(self, subject, runNumber, longInstructions, eyetracking)
        nowTime=datetime.datetime.now()
        self._outFileName='%s_%04d%02d%02d_%02d%02d_CSS_psych_run%02d.pickle'%(self.subject,nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute,self._runNumber)
        self._outFile=os.path.join('subjectResponseFiles',self._outFileName)
        if self._eyetracking=='yes':
            self._outFileNameEye='%s_%04d%02d%02d_%02d%02d_CSS_psych_run%02d.edf'%(self.subject,nowTime.year,nowTime.month,nowTime.day,nowTime.hour,nowTime.minute,self._runNumber) 
            self._outFileDirEye=os.path.join('eyetracking',self.subject) 
            self._outFileEye=os.path.join(self._outFileDirEye,self._outFileNameEye) 
        self._timingAndConditions()
        self._responseKeys=['left','right']

    @property
    def block(self):
        return self._block
    @block.setter
    def block(self, value):
        self._block=value
        self._shuffleBlock()
        self._blockTrialNum=-1


    def _timingAndConditions(self):
        self._stimDuration=0.8
        #tricks to leave the main code alone...
        self._responseBlank=0.4
        self._baselineBlank=0
        self._numStairTrialsPerCond=30
        self._numCatchPerCond=20
        self._numStairsPerCond=3
        self._numTrialsPerCond=self._numStairTrialsPerCond*self._numStairsPerCond + self._numCatchPerCond

        #awkwardly, contrasts are in fractions, since psychopy wants 0-1
        #deltacontrasts, later are in percent for the staircase to maintain sanity
        self._contrasts = [ [0.0,0.0],
        					 [0.0065, 0.0],
        					 [0.0125, 0.0],
        					 [0.025,0.0],
        					 [0.05,0.0],
        					 [0.10,0.0],
        					 [0.20,0.0],
        					 [0.10,1.0]]
        numCond=len(self._contrasts)
        self._conditions={}
        iTrialType=0
        for iCond in range(numCond):
            targC=self._contrasts[iCond][0]
            surrC=self._contrasts[iCond][1]
            thisName='target %02.3f, surround %02.2f'%(targC,surrC)
            self._conditions[iTrialType]={'name':thisName,
                'targetContrast':targC,
                'surroundContrast':surrC}
            iTrialType+=1
        #create a trial list so I can keep track of catch trials
        #I will call them 0, 1, 2, 3, with 3 as the catch trials
        #this trial list is for a single block. It will persist, but be reshuffled for each block
        #I  30trials/stair X 3 stairs + 20 catch ==>
#        trialList=numpy.concatenate((numpy.repeat([0,1,2],self._numStairTrialsPerCond),numpy.repeat([3],self._numCatchPerCond)))
        #however, I need to shuffle them separately
        stairTrialList=numpy.repeat(numpy.arange(self._numStairsPerCond),self._numStairTrialsPerCond)
        #in a block ALL TRIALS are the same condition. This list tells me WHICH STAIRCASE and the deltaContrast sign
        #add a column with the inc/dec sign
        #stairDeltaList=numpy.repeat([1,-1],self._numStairsPerCond*self._numStairTrialsPerCond/2) #half pos, half neg deltas
        stairDeltaList=numpy.repeat([1,1],self._numStairsPerCond*self._numStairTrialsPerCond/2) #half pos, half neg deltas

        catchTrialList=numpy.repeat([3],self._numCatchPerCond)
        catchDeltaList=numpy.repeat([1],self._numCatchPerCond) #only positive deltas for catch trials

        stairTrialList=numpy.transpose(numpy.vstack((stairTrialList, stairDeltaList)))
        numpy.random.shuffle(stairTrialList)
        catchTrialList=numpy.transpose(numpy.vstack((catchTrialList,catchDeltaList)))#that escalated quickly
        numpy.random.shuffle(catchTrialList)
        trialList=numpy.concatenate((stairTrialList,catchTrialList))
        numpy.random.shuffle(trialList)#reshuffle each block
        self._trialList=trialList
        #### Block structure ####
        #random sequence of the 12 conditions
        blockOrder=numpy.arange(iTrialType,dtype=numpy.int)
        numpy.random.shuffle(blockOrder)
        self._blockOrder=blockOrder


        #### task staircases ####
        # equal number of contrast inc/dec distributed randomly across target blocks
        # no target tasks have their own inc (no dec!) level
        #both inc/dec and no-targ-inc should vary from run to run to keep at 80%

        self._contrastDeltas=[1.0/255.0/3.0 , 40] 
        # self._catchDelta=0.25
        self._catchDelta=0.4 
        #remaining parameters for the psi staircases
        self._alphaRange=[0,40] #endpoints of the "location parameter" 
        self._alphaPrecision=1 #step size 
        self._intensityRange=self._contrastDeltas #endpoints of the range of stimulus "intensities"
        self._intensityPrecision=40 #STEP SIZE, not number f steps, unless it's log, then it's number ofstep
        self._betaRange=[0.1,5]#range of slopes
        self._betaPrecision=0.1 #step size
        self._stepType='log' #  n.b. only applies to intensityRange and NOT alpha or beta
        self._delta=0.08  # delta/2 maps to MATLAB's guessRate (gamma)
        #need to nest for 3 reps...
        #http://stackoverflow.com/questions/18072759/python-nested-list-comprehension

        self._psiStairs=[[data.PsiHandler(nTrials=self._numStairTrialsPerCond,
                                    intensRange=self._intensityRange,
                                    alphaRange=self._alphaRange,
                                    betaRange=self._betaRange,
                                    intensPrecision=self._intensityPrecision,
                                    alphaPrecision=self._alphaPrecision,
                                    betaPrecision=self._betaPrecision,
                                    delta=self._delta,
                                    stepType=self._stepType,
                                    #TwoAFC=True,
                                    expectedMin=0.5) for i in range(len(self._conditions))] for j in range(self._numStairsPerCond)]
        ##access them later via this syntax:
        ##psiStairs[condition].attr
        #below, we will add a new response to the staircase:
        # psiStair[condition].addResponse(thisResult)
        #get the new intensity level
        # newlevel = psiStair[condition].next()
        self._psychResponses=numpy.zeros((len(self._trialList)*len(self._blockOrder),3))#needs to be len(trialList)*numBlocks
        self._catchResponses=numpy.zeros((len(self._trialList)*len(self._blockOrder),2))
        #argh! keep all the things in one place
        # block#, trial#, condition, TC, SC, correctAns, response, "condition" (stair#, catch)
        self._masterInfo=numpy.zeros((len(self._trialList)*len(self._blockOrder),8))
        self._psychResponsesByCondition=[[],[],[],[],[],[],[],[],[],[],[],[]]

    def _shuffleBlock(self):
        numpy.random.shuffle(self._trialList)


    def _updateStair(self,condition, response):
        #response is yes/no (right/wrong) NOT the actual key pressed!
        #NEED TO KNOW which of the 3 stairs, or catch
        #get this from my trial list
        stairRep=self._trialList[self._blockTrialNum,0]
        if stairRep<3:
            self._psiStairs[stairRep][condition].addResponse(response,self._pushDelta)#also push the delta used in case we overrode it
            print('staircase # %d'%(stairRep+1))
        else:
            self._catchResponses[self._iT,0]=condition
            self._catchResponses[self._iT,1]=response
            print('catch trial')
        self._psychResponses[self._iT,0]=condition
        self._psychResponses[self._iT,1]=stairRep
        self._psychResponses[self._iT,2]=response
        self._masterInfo[self._iT,0]=self._block
        self._masterInfo[self._iT,1]=self._iT
        self._masterInfo[self._iT,2]=condition
        self._masterInfo[self._iT,3]=self._conditions[condition]['targetContrast']
        self._masterInfo[self._iT,4]=self._conditions[condition]['surroundContrast']
        if self._correctAnswer=='left':
            self._masterInfo[self._iT,5]=0
        else:
            self._masterInfo[self._iT,5]=1
        self._masterInfo[self._iT,6]=response
        self._masterInfo[self._iT,7]=stairRep
        self._psychResponsesByCondition[condition].append(response)

    def _nextDelta(self, condition, stimObject):
        #NEED TO KNOW which of the 3 stairs, or catch
        self._blockTrialNum+=1#initialized to -1 when block changes. that's a strange choice
        stairRep=self._trialList[self._blockTrialNum,0]
        if stairRep<3:
            rawDelta=self._psiStairs[stairRep][condition].next()/100.0 #convert to 0-1 for psychopy
            if debug>0:
                print('stair.next: %2.1f%%'%(100*rawDelta))
            if stimObject.targetContrast+rawDelta>1.0:
                thisDelta=(1.0-stimObject.targetContrast)*self._trialList[self._blockTrialNum,1]#cap at 100%
                self._pushDelta=(1.0-stimObject.targetContrast)*100
                print('***** contrast exceeded 100%%; capping at max contrast****')
            else:
                thisDelta=rawDelta*self._trialList[self._blockTrialNum,1]
                self._pushDelta=rawDelta*100
            stimObject.deltaContrast=thisDelta
        else:
            stimObject.deltaContrast=self._catchDelta*self._trialList[self._blockTrialNum,1]

    def writeDataFile(self):
        #need to flatten the nested staircases
        #also, calculate the mean values for fMRI to pickup
        locs=numpy.zeros((self._numStairsPerCond))
        meanLocs=numpy.zeros((len(self._conditions)))
        for iC in range(len(self._conditions)-1):
            for stair in range(self._numStairsPerCond):
                locs[stair]=self._psiStairs[stair][iC].estimateLambda()[0]
            meanLocs[iC]=numpy.mean(locs)
        printNames=[]
        for iC, thisC in enumerate(self._conditions.keys()):
            printNames.append('condition %d, %s'%(thisC,self._conditions[thisC]['name']))
        data={'intensityRange':self._intensityRange,
            'alphaRange':self._alphaRange,
            'betaRange':self._betaRange,
            'delta':self._delta,
            'subject':self.subject,
            'run':self._runNumber,
            'intensityPrecision':self._intensityPrecision,
            'stepType':self._stepType,
            #need to flatten the nested staircases
            'slopes1':[thisStair.estimateLambda()[1] for thisStair in self._psiStairs[0]],
            'locations1':[thisStair.estimateLambda()[0] for thisStair in self._psiStairs[0]],
            'intensities1':[thisStair.intensities for thisStair in self._psiStairs[0]],
            'responses1':[thisStair.data for thisStair in self._psiStairs[0]],
            'slopes2':[thisStair.estimateLambda()[1] for thisStair in self._psiStairs[1]],
            'locations2':[thisStair.estimateLambda()[0] for thisStair in self._psiStairs[1]],
            'intensities2':[thisStair.intensities for thisStair in self._psiStairs[1]],
            'responses2':[thisStair.data for thisStair in self._psiStairs[1]],
            'slopes3':[thisStair.estimateLambda()[1] for thisStair in self._psiStairs[2]],
            'locations3':[thisStair.estimateLambda()[0] for thisStair in self._psiStairs[2]],
            'intensities3':[thisStair.intensities for thisStair in self._psiStairs[2]],
            'responses3':[thisStair.data for thisStair in self._psiStairs[2]],
            'meanLocs':meanLocs,
            'blockOrder':self._blockOrder,
            'conditionNames':'; '.join(printNames),
            'actualTargetContrasts':self._keepTargetContrasts,
            'actualSurroundContrasts':self._keepSurroundContrasts,
            'actualDeltaContrasts':self._keepDeltas,
            'actualTaskSides':self._keepTaskSides,
            'actualOrientation':self._keepOris,
            'actualResponses':self._keepResponses,
            'masterInfo':self._masterInfo,
            'catchResponses':self._catchResponses,
            'psychResponses':self._psychResponses,
            'psychResponsesByCondition':self._psychResponsesByCondition
            }
        misc.toFile(self._outFile,data)


class stimCSS(object):
    def __init__(self,win):
        self._win=win
        self._cpd=1.1
        self._revFreq=4
        self._phaseDuration=1.0/(2.0*self._revFreq)
        self._targetRadius = 1.0
        self._surroundRadii=[self._targetRadius+0.25, 2*self._targetRadius]
        self._fiducialGap = 0.05
        self._locLeft=[-3,0]
        self._locRight=[3,0]
        self._ori=0
        self._targetOri=90
        self._orientations=numpy.arange(0,180,45)
        self._targetContrast=0.0
        self._surroundContrast=0.0
        self._initialPhase=0
        self._phase=0
        self._taskSide=0
        self._deltaContrast=10
        self._grating=visual.GratingStim(self._win,
                                      mask='raisedCos',
                                      tex='sin',
                                      pos=self._locLeft,
                                      phase=0,
                                      size=2*self._targetRadius,
                                      sf=self._cpd,
                                      contrast=0.8,
                                      units='deg')

        self._circle=visual.Circle(self._win,
            radius=self._targetRadius+self._fiducialGap,
            lineColor=[-0.5,-0.5,-0.5],
            lineColorSpace='rgb',
            fillColor=[0,0,0],
            fillColorSpace='rgb',
            units='deg')
        self._fixationMark=visual.Rect(self._win,
            width=0.2,
            height=0.2,
            fillColor=[1,1,1],
            fillColorSpace='rgb',
            units='deg')
        self._fixationMask = visual.Rect(self._win,
            width=1.9,
            height=40.0,
            fillColor=[0,0,0],
            fillColorSpace='rgb',
            lineColor=[0,0,0],
            lineColorSpace='rgb',
            units='deg')
        self._blank=visual.Rect(self._win,
            width=50,
            height=40,
            fillColor=[0,0,0],
            fillColorSpace='rgb',
            units='deg')
        self._textMsg=visual.TextStim(self._win,text='Preparing the task',
            units='norm',pos=(0,0),height=0.065,alignVert='top',wrapWidth=1.9)
        self._textMsg.draw()
        self._win.flip()

    @property
    def targetContrast(self):
        return self._targetContrast
    @targetContrast.setter
    def targetContrast(self, value):
        self._targetContrast = value

    @property
    def surroundContrast(self):
        return self._surroundContrast
    @surroundContrast.setter
    def surroundContrast(self, value):
        self._surroundContrast = value

    @property
    def ori(self):
        return self._ori
    @ori.setter
    def ori(self, value):
        self._ori = value

    @property
    def targetOri(self):
        return self._targetOri
    @targetOri.setter
    def targetOri(self, value):
        self._targetOri = value

    @property
    def phase(self):
        return self._phase
    @phase.setter
    def phase(self, value):
        self._phase = value
        #self._grating.phase=self._phase

    @property
    def initialPhase(self):
        return self._initialPhase
    @initialPhase.setter
    def initialPhase(self, value):
        self._initialPhase = value

    @property
    def phaseDuration(self):
        return self._phaseDuration


    @property
    def taskSide(self):
        return self._taskSide
    @taskSide.setter
    def taskSide(self, value):
        self._taskSide = value


    @property
    def deltaContrast(self):
        return self._deltaContrast
    @deltaContrast.setter
    def deltaContrast(self, value):
        self._deltaContrast = value



    #methods


    def setOrientation(self):
        self._ori=self._orientations[numpy.random.randint(len(self._orientations))]
        self._targetOri=self._ori


    def updatePhase(self,elapsedTime):
        #phase is modulo 1, so 0 and 1 are the same thing. I want phase to alternate
        #between 0 and 0.5
        #
        modElapsedTime=elapsedTime%1
        modModTime=modElapsedTime%(2.0/self._revFreq)
        screenFlipEpsilon=3.0/60
        if modModTime<(1.0/self._revFreq - screenFlipEpsilon):
            self._phase=self._initialPhase+0
        else:
            self._phase=self._initialPhase+0.5

    def switchPhase(self):
        if self._phase - self._initialPhase==0:
            self._phase=self._initialPhase+0.5
        else:
            self._phase=self._initialPhase


    def draw(self):
        #startTime=t_timer()
        self._grating.phase=self._phase
        #left surround
        self._grating.size = self._surroundRadii[1]*2
        self._grating.maskParams={'fringWidth':0.25/self._surroundRadii[1]}
        self._grating.pos=self._locLeft
        self._grating.ori=self._ori
        self._grating.contrast=self._surroundContrast
        self._grating.draw()
        #right surround
        self._grating.pos=self._locRight
        self._grating.draw()

        #mask out the annulus between surround and target
        #left
        self._grating.size = self._surroundRadii[0]*2
        self._grating.maskParams={'fringWidth':0.25/self._surroundRadii[0]}
        self._grating.pos=self._locLeft
        self._grating.contrast=0
        self._grating.draw()
        #right
        self._grating.pos=self._locRight
        self._grating.draw()
        #fixation maSk
        self._fixationMask.draw()

        #fiducial circles around targets
        self._circle.pos=self._locLeft
        self._circle.draw()
        self._circle.pos=self._locRight
        self._circle.draw()

        #target left
        self._grating.size = self._targetRadius*2
        self._grating.maskParams={'fringWidth':0.25/self._targetRadius}
        self._grating.pos=self._locLeft
        self._grating.ori=self._ori
        if self._taskSide==0:
            self._grating.contrast=self._targetContrast+self._deltaContrast
        else:
            self._grating.contrast=self._targetContrast
        self._grating.draw()
        #right surround
        if self._taskSide==1:
             self._grating.contrast=self._targetContrast+self._deltaContrast
        else:
            self._grating.contrast=self._targetContrast
        self._grating.pos=self._locRight
        self._grating.draw()

        #fixation mark
        self._fixationMark.draw()


        self._win.flip()

        #endTime=t_timer()
        #print(endTime-startTime)

    def drawBlank(self):
        self._blank.draw()
        #fixation mark
        self._fixationMark.draw()
        #fiducial circle
        self._circle.pos=self._locLeft
        self._circle.draw()
        self._circle.pos=self._locRight
        self._circle.draw()
        self._win.flip()

    def drawRest(self):
        self._blank.draw()
        #fixation mark
        self._fixationMark.draw()
        self._win.flip()

    def drawText(self,msg):
        self._blank.draw()
        self._textMsg.pos=(0,0)
        self._textMsg.text=msg
        self._textMsg.draw()
        self._win.flip()

    def drawBreak(self,block,totalBlocks):
        self._blank.draw()
        self._textMsg.pos=(0,0)
        self._textMsg.text='You have finished %d of the %d blocks! Press any key to continue.'%(block+1, totalBlocks)
        self._textMsg.draw()
        self._win.flip()


    def drawFixEyetracker(self):
        self._blank.draw()
        self._textMsg.pos=(0,0)
        self._textMsg.text='Researcher, please adjust eyetracker as needed, then press the continue key.'
        self._textMsg.draw()
        self._win.flip()



    def drawCustom(self, text=None, fixation=True, pedestal=None, surround=None, side=0,ori=ori):
        self._blank.draw()

        #random ori
        self._ori=ori
        self._targetOri=self._ori
        self._grating.phase=self._phase

        if surround is not None:
            #left surround
            self._grating.size = self._surroundRadii[1]*2
            self._grating.maskParams={'fringWidth':0.25/self._surroundRadii[1]}
            self._grating.pos=self._locLeft
            self._grating.ori=self._ori
            self._grating.contrast=surround
            self._grating.draw()
            #right surround
            self._grating.pos=self._locRight
            self._grating.draw()

            #mask out the annulus between surround and target
            #left
            self._grating.size = self._surroundRadii[0]*2
            self._grating.maskParams={'fringWidth':0.25/self._surroundRadii[0]}
            self._grating.pos=self._locLeft
            self._grating.contrast=0
            self._grating.draw()
            #right
            self._grating.pos=self._locRight
            self._grating.draw()

            #fixation maSk
            self._fixationMask.draw()
        if pedestal is not None:
            #fiducial circles around targets
            self._circle.pos=self._locLeft
            self._circle.draw()
            self._circle.pos=self._locRight
            self._circle.draw()

            #target left
            self._grating.size = self._targetRadius*2
            self._grating.maskParams={'fringWidth':0.25/self._targetRadius}
            self._grating.pos=self._locLeft
            self._grating.ori=self._ori
            if side==0:
                self._grating.contrast=pedestal[0]+pedestal[1]
            else:
                self._grating.contrast=pedestal[0]
            self._grating.draw()
            #right surround
            if side==1:
                self._grating.contrast=pedestal[0]+pedestal[1]
            else:
                self._grating.contrast=pedestal[0]
            self._grating.pos=self._locRight
            self._grating.draw()
        if fixation is True:
            self._fixationMark.draw()
        self._textMsg.pos=(0,0.6)
        self._textMsg.text=text
        self._textMsg.draw()
        self._win.flip()


def main():

    #### Subject Information ####
    subInfo={'subject':'1','runNumber':1,'longInstructions':1,'eyetracking':['yes','no']}
    #update session info
    infoDlg=gui.DlgFromDict(dictionary=subInfo,title='Scan Parameters',
                            order=['subject','runNumber',
                            'longInstructions','eyetracking'],
                            tip={'subject':'subject number',
                                 'runNumber':'run number',
                                 'longInstructions':'Long instructions with practice trials? (1 for yes, 0 for no)',
                                 'eyetracking':'eyetracking'})
    print(subInfo)
    if infoDlg.OK:
        #create my expInfo object
        expInfo=ExpInfoPsych(subInfo['subject'],
                         subInfo['runNumber'],
                         subInfo['longInstructions'],
                         subInfo['eyetracking'])

    else:
        print 'user cancelled'
        core.quit()

    # run eyetracker calibration
    if subInfo['eyetracking']=='yes':
        expInfo.tracker.runSetupProcedure()

    stimObject=stimCSS(expInfo.win)
    if subInfo['longInstructions']==1:
        if subInfo['eyetracking']=='yes':
            #start recording
            expInfo.io.clearEvents()
            expInfo.tracker.setRecordingState(True)
            #send a message to the tracker
            msg='start instructions/practice'
            expInfo.tracker.sendMessage(msg)
        expInfo.doInstructions(stimObject) #shuld this be a method of expInfo?...almost certainly
        if subInfo['eyetracking']=='yes':
            #send a message to the tracker
            msg='end instructions/practice'
            expInfo.tracker.sendMessage(msg)
            #stop recording
            expInfo.io.clearEvents()
            expInfo.tracker.setRecordingState(False)

    #### initialize timers ####
    trialTimer=core.CountdownTimer()
    blockTimer=core.CountdownTimer()
    phaseTimer=core.CountdownTimer()
    timeEpsilon=0.00015
    globalClock=core.Clock()

    #test stim
    if debug==2:
        for iO, thisOri in enumerate(numpy.arange(0,180,45)):
            for iSeg in range(6):
                print(thisOri, iSeg)
                stimObject.targetContrast=0.5
                stimObject.surroundContrast=0.5
                stimObject.deltaContrast=0.4
                stimObject.ori=thisOri
                stimObject.targetOri=thisOri#must set this first, because task side needs it to set the right mask ori
                stimObject.taskSeg=iSeg
                stimObject.draw()
                expInfo.waitForKey()


    #### wait for subject to be ready ####
    buttonPrefix='arrow '
    msg="The experiment is about to begin. Decide which side (left or right)"\
    " has _higher_ contrast and press the left or right %sbutton. "\
    "If you aren't sure, it's OK to guess! Press any button when you are ready to start."%(buttonPrefix)
    stimObject.drawCustom(text=msg,fixation=True,  pedestal=[0.25,0.12],side=0,ori=0)
    expInfo.waitForKey()


    #### start experiment ####
    trialTimer.reset()
    blockTimer.reset()
    globalClock.reset()
    if subInfo['eyetracking']=='yes':
        #send a message to the tracker
        msg='starting experiment'
        expInfo.tracker.sendMessage(msg)
    for iBlock, condition in enumerate(expInfo.blockOrder): #don't I need a "getter" for blockOrder?
        if subInfo['eyetracking']=='yes':
            #start recording
            expInfo.io.clearEvents()
            expInfo.tracker.setRecordingState(True)
        expInfo.block=iBlock
        trialTimer.reset()
        trialTimer.add(2.5)
        while trialTimer.getTime()>0:
            stimObject.drawRest()
            expInfo.getResponses(99)
        if condition==99: #fMRI rest
            if subInfo['eyetracking']=='yes':
                #send a message to the tracker
                msg='block %d, condition %d, start'%(iBlock,condition)
                expInfo.tracker.sendMessage(msg)
            blockTimer.reset()
            blockTimer.add(expInfo.baselineBlank)
            stimObject.drawRest()
            while blockTimer.getTime()>0:
                #evidently no task during rest, but still check for quitkeys
                expInfo.getResponses(99)
        else:
            #startTime=t_timer()
            if subInfo['eyetracking']=='yes':
                #send a message to the tracker
                msg='block %d, condition %d, start'%(iBlock,condition)
                expInfo.tracker.sendMessage(msg)
            for iTrial in range(expInfo.numTrialsPerCond):
                if subInfo['eyetracking']=='yes':
                    #send a message to the tracker
                    msg='block %d, condition %d, trial %d, start trial, stimulus on'%(iBlock,condition,iTrial)
                    expInfo.tracker.sendMessage(msg)
                expInfo.setCondition(iTrial, condition, stimObject)#sets contrasts, task side, orientation, correct answer
                trialTimer.reset()
                trialTimer.add(expInfo.stimDuration)
                expInfo.haveResponse=0
                #try a different timing control since drawing is VERY slow and unpredictable
                numDraws=numpy.int(expInfo.stimDuration/stimObject.phaseDuration)#that's an awkward split
                expInfo.beep.play()
                for iDraw in range(numDraws):
                    phaseTimer.reset()
                    phaseTimer.add(stimObject.phaseDuration)
                    stimObject.switchPhase()
                    stimObject.draw()
                    while phaseTimer.getTime()>timeEpsilon:
                        expInfo.getResponses(condition)#getResponses already knows the right answer
                trialTimer.reset()
                trialTimer.add(expInfo.responseBlank)
                stimObject.drawBlank()
                if subInfo['eyetracking']=='yes':
                    #send a message to the tracker
                    msg='block %d, condition %d, trial %d, stimulus off, drawing blank'%(iBlock,condition,iTrial)
                    expInfo.tracker.sendMessage(msg)
                while trialTimer.getTime()>0: #mandatory blank for fMRI and psych
                    expInfo.getResponses(condition)
                #psych could still wait
                stimObject.drawBlank()
                while expInfo.haveResponse==0:
                    expInfo.getResponses(condition)
                if subInfo['eyetracking']=='yes':
                    #send a message to the tracker
                    msg='block %d, condition %d, trial %d, end trial'%(iBlock,condition,iTrial)
                    expInfo.tracker.sendMessage(msg)
            #endTime=t_timer()
            #print('block duration %f'%(endTime-startTime))
        #if psychophysics, offer a break after each block
        if subInfo['eyetracking']=='yes':
            #stop recording
            expInfo.tracker.setRecordingState(False)
        if iBlock<len(expInfo.blockOrder)-1:
            stimObject.drawBreak(iBlock,len(expInfo.blockOrder))
            expInfo.waitForKey()
            if subInfo['eyetracking']=='yes':
                #allow operator to adjust eye image
                stimObject.drawFixEyetracker()
                expInfo.waitForContKey()
        print('end of block %d, global clock %f'%(iBlock,globalClock.getTime()))
        #expInfo.writeDataFile()

    if subInfo['eyetracking']=='yes':
        #stop recording eyetracker
        expInfo.tracker.setRecordingState(False)

    expInfo.writeDataFile()
    expInfo.cleanup()

if __name__ == "__main__":

    main()
