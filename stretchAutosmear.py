import maya.cmds as cmds
from pprint import pprint
import numpy as np

#start from 35 and ends with 55 expected smearFrame from 45
def getValues(*args):
    startFrame = 35
    endFrame = 55
    rawSquashAttributes = ''
    multiplier = 0.5
    startCtrl = 'charizard_rig_v003:flame_01_ctrl'
    endCtrl = 'charizard_rig_v003:flame_04_ctrl'  
    
    #check if user input start to end ctrl or squash and stretch attribute
    if rawSquashAttributes is '':
        #using function to get the hierarchy of the ctrl
        ctrlHierarchy = getCtrlHierarchy(startCtrl,endCtrl)
        #using function to calculate the velocity of the obj from startFrame to endFrame
        smearFrame = calculateVelocityFromCtrl(startFrame,endFrame,ctrlHierarchy)
        #using function to keyframe the stretch smear effect
        stretchCtrl(smearFrame,ctrlHierarchy,multiplier)
        
    elif startCtrl == '' and endCtrl == '':
        pass

def getCtrlHierarchy(startCtrl = '',endCtrl = ''):
    rawCtrlHierarchyLst = cmds.listRelatives(startCtrl,ad=True)
    ctrlHierarchy = []
        
    #filtering the rawLst
    for i in range(len(rawCtrlHierarchyLst)):
        lstElement = rawCtrlHierarchyLst[i]
            
        #Check if lstElement is a nurb curve and is visible
        if cmds.nodeType(lstElement) == 'nurbsCurve' and cmds.getAttr(lstElement+'.visibility') == True:
            #getting controller name from its shape
            ctrlName = cmds.listRelatives(lstElement,parent=True)[0]
                
            ctrlHierarchy.append(ctrlName)
            
        #break once the the loop tranverse to the endCtrl
        if lstElement is endCtrl:
            break
                
    return ctrlHierarchy    
        
def calculateVelocityFromCtrl(startFrame=1,endFrame=1,ctrlHierarchy=[]):
    #? testing the velocity of three different axis
    #Calculate velocity via the mainCtrl
    mainCtrl = ctrlHierarchy[0]
    posLst = []
    max_a = 0 #peak acceleration
    s = []    #list of position difference
    n = 0     #dynamic array index
    smearFrame = startFrame
    
    for i in range(startFrame,endFrame):
        #finding position vector of the mainCtrl for each frame
        cmds.currentTime(i)
        posVector = np.array(cmds.xform(mainCtrl,q=True,t=True,ws=True))
        posLst.append(posVector)
        
        #Since, s = posLst[n] - posLst[n-1] ==> at n = 0; s = posLst[0] - 0 
        if i is startFrame:
                        s.append(posLst[n])
                        n+=1
                        continue
                        
        #Calculate the displacement cover by an object at one frame
        s.append(posLst[n]-posLst[n-1])
        n+=1
        
    #?Since, the position difference is calculate per 1 frame i.e. t = 1; velocity = change in position/frame(=1) ==> velocity = displacement
    #now, to find the frame with maximum change in velocity(acceleration) i.e. a smear frame
    for n in range(len(posLst)):
        a = np.sqrt(posLst[n][0]**2+posLst[n][1]**2+posLst[n][2]**2)
        if a>max_a:
            max_a = a
            smearFrame = n + startFrame
    
    return smearFrame

def stretchCtrl(smearFrame = 1,ctrlHierarchy = [],multiplier = 1):    
    numberOfCtrl = len(ctrlHierarchy)

    for i in range(1,numberOfCtrl):
        #create ctrl on the smearFrame
        cmds.currentTime(smearFrame)
        ctrlTranslation = cmds.xform(ctrlHierarchy[i],q=True,t=True,ws=True)
        cmds.xform(ctrlHierarchy[i],t=ctrlTranslation,ws=True)

        #snap the ctrl of the next frame to the created loc
        cmds.currentTime(smearFrame+1)
        cmds.xform(ctrlHierarchy[i],t=ctrlTranslation,ws=True)


getValues()