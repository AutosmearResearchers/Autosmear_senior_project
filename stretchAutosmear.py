import maya.cmds as cmds
import maya.mel as mel
from pprint import pprint
import numpy as np


#//start from 35 and ends with 55 expected smearFrame from 45
def getValues(*args):
    startFrame = 1
    endFrame = 24
    rawSquashAttributes = 'squash_attr'
    masterSquashAttributes = 'squash_ctrl'
    multiplier = 1
    startCtrl = ''
    endCtrl = ''  

    #startFrame = 35
    #endFrame = 55
    #rawSquashAttributes = ''
    #masterSquashAttributes = ''
    #multiplier = 0.5
    #startCtrl = "charizard_rig_v003:flame_01_ctrl"
    #endCtrl = "charizard_rig_v003:flame_04_ctrl"
    
    #todo check if user input start to end ctrl or squash and stretch attribute
    if rawSquashAttributes is '':
        #! using function to get the hierarchy of the ctrl
        ctrlHierarchy = getCtrlHierarchy(startCtrl,endCtrl)
        #! using function to calculate the velocity of the obj from startFrame to endFrame
        smearFrame = calculateVelocityFromCtrl(startFrame,endFrame,ctrlHierarchy)
        #! using function to keyframe the stretch smear effect (by ctrl)
        stretchCtrl(smearFrame,ctrlHierarchy,multiplier)

    elif startCtrl == '' and endCtrl == '':
        #! using function to query [[range],default] of the selected attribute
        attributeValuesLst = findAttrRange(rawSquashAttributes,masterSquashAttributes)
        #! using function to calculate the velocity of the obj from startFrame to endFrame
        smearFrame = calculateVelocityFromCtrl(startFrame=startFrame,endFrame=endFrame,ctrlHierarchy=[masterSquashAttributes]) #todo BULIN put your masterSquashAttributes inside [] so, it can be recycle
        #! using function to keyframe the stretch smear effect (by attr)
        stretchAttr(smearFrame,endFrame,masterSquashAttributes,rawSquashAttributes,attributeValuesLst,multiplier)

def findAttrRange(rawSquashAttributes = '',masterSquashAttributes = ''):
     attributeMax = cmds.attributeQuery(rawSquashAttributes,node = masterSquashAttributes,max = True)
     attributeDefault = cmds.attributeQuery(rawSquashAttributes,node = masterSquashAttributes, ld = True)   
     return [attributeMax[0], attributeDefault[0]]

def stretchAttr(smearFrame=1,endFrame = 1,masterSquashAttributes='',rawSquashAttributes='',attributeValuesLst=[],multiplier=1):
    maxStretchValue = attributeValuesLst[0]
    originalStretchValue = attributeValuesLst[1]
    attribute = '{master}.{raw}'.format(master = masterSquashAttributes,raw = rawSquashAttributes)

    if multiplier<=1:
        maxStretchValue*= multiplier
    else:
         multiplier = 1
    
    #! keyframe the frame before smearFrame
    cmds.currentTime(smearFrame - 1)
    cmds.setAttr(attribute,originalStretchValue)
    cmds.setKeyframe(attribute,bd = False, pcs = False, hi = 'None',cp= False, shape = False)

    #! keyframe the smearFrame aka. Stretch the rig
    cmds.currentTime(smearFrame)
    cmds.setAttr(attribute,maxStretchValue)
    cmds.setKeyframe(attribute,bd = False, pcs = False, hi = 'None',cp= False, shape = False)

    #! keyframe the endFrame
    cmds.currentTime(endFrame)
    cmds.setAttr(attribute,originalStretchValue)
    cmds.setKeyframe(attribute,bd = False, pcs = False, hi = 'None',cp= False, shape = False)

def getCtrlHierarchy(startCtrl = '',endCtrl = ''):
    rawCtrlHierarchyLst = cmds.listRelatives(startCtrl,ad=True)
    ctrlHierarchy = []
        
    #todo filtering the rawLst
    for i in range(len(rawCtrlHierarchyLst)):
        lstElement = rawCtrlHierarchyLst[i]
            
        #! Check if lstElement is a nurb curve and is visible
        if cmds.nodeType(lstElement) == 'nurbsCurve' and cmds.getAttr(lstElement+'.visibility') == True:
            #! getting controller name from its shape
            ctrlName = cmds.listRelatives(lstElement,parent=True)[0]
                
            ctrlHierarchy.append(ctrlName)
            
        #! break once the the loop tranverse to the endCtrl
        if lstElement is endCtrl:
            break
                
    return ctrlHierarchy    
        
def calculateVelocityFromCtrl(startFrame=1,endFrame=1,ctrlHierarchy=[]):
    #? testing the velocity of three different axis
    #todo Calculate velocity via the mainCtrl
    mainCtrl = ctrlHierarchy[0]
    posLst = []
    v = [] #?List of all the velocity
    max_a = 0 #? peak acceleration
    s = []    #? list of position difference
    n = 0     #? dynamic array index
    smearFrame = startFrame
    
    for i in range(startFrame,endFrame):
        #todo finding position vector of the mainCtrl for each frame
        cmds.currentTime(i)
        posVector = np.array(cmds.xform(mainCtrl,q=True,t=True,ws=True))
        posLst.append(posVector)
        
        #todo Since, s = posLst[n] - posLst[n-1] ==> at n = 0; s = posLst[0] - 0 
        if i is startFrame:
                        s.append(posLst[n])
                        n+=1
                        continue
                        
        #todo Calculate the displacement cover by an object at one frame
        s.append(posLst[n]-posLst[n-1])
        n+=1
        
    #?Since, the position difference is calculate per 1 frame i.e. t = 1; velocity = change in position/frame(=1) ==> velocity = displacement
    #todo now, to find the frame with maximum change in velocity(acceleration) i.e. a smear frame
    for n in range(len(posLst)):
        v.append(np.sqrt(posLst[n][0]**2+posLst[n][1]**2+posLst[n][2]**2))
        
    for vi in range(len(v)): #a1-a0 find the difference    
        if vi == 0:
             continue
        a = v[vi] - v[vi-1]
        #//print(f'frame {vi}')
        #//print(f'acceleration: {a}')
        if a>max_a:
            max_a = a
            smearFrame = vi + startFrame
    
    #//print(f'Smear at: {smearFrame}')  
    return smearFrame

def stretchCtrl(smearFrame = 1,ctrlHierarchy = [],multiplier = 1):    
    numberOfCtrl = len(ctrlHierarchy)
    locatorLst = []

    for i in range(1,numberOfCtrl):
        #todo create ctrl on the smearFrame
        cmds.currentTime(smearFrame)
        ctrlTranslation = cmds.xform(ctrlHierarchy[i],q=True,t=True,ws=True)
        
        #todo create locator on the location
        if cmds.objExists('{ctrlHie}_autoSmearTool_LOC'.format(ctrlHie = ctrlHierarchy[i])) is False:    
            loc = cmds.spaceLocator(n = '{ctrlHie}_autoSmearTool_LOC'.format(ctrlHie = ctrlHierarchy[i]))
            locatorLst.append(loc[0])
            #!get and set the locator value
            cmds.xform(loc,t=ctrlTranslation,ws=True)
            locTranslate = cmds.xform(loc,q=True,t=True,ws=True)
            #!snap the ctrl to locator
            cmds.xform(ctrlHierarchy[i],t=locTranslate,ws=True)

            #todo snap the ctrl of the next frame to the created loc
            cmds.currentTime(smearFrame+1)
            cmds.xform(ctrlHierarchy[i],t=locTranslate,ws=True)
    
    #todo group all the locators created after the iteration is complete
    locGrp = cmds.group(locatorLst,n = '{ctrlHie}_autoSmearTool_LOC_grp'.format(ctrlHie = ctrlHierarchy[i]))


getValues()
#! keyframe the Charlizard