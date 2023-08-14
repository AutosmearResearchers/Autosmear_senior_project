import maya.cmds as cmds
from pprint import pprint
def autoStretchSmear(selCtrl = '',startFrame = 1,endFrame = 1,attr = ''):
    '''
    Tool: Autosmear
    feature: automate stretch smear
    
    autoStretchSmear(selCtrl = string,startFrame = int,endFrame = int,attr = string)
    
    args
    -------------------------------
    selCtrl(string):
        the controllers that is used to detect object acceleration.
    
    startFrame(int):
        the frame where the acceleration detection must initiate.
    
    endFrame(int):
        the frame where the detection must terminate. 
        
    attr(string):
        name of the attribute responsible for squash and stretch of the given rig. 
    
    ------------------------------
    
    This function accepts args from the user than it calculates the position moved for every frame from startFrame to endFrame, 
    then, it detects the frame in which have instanteneuos position change. Once found, it stretch model on that frame and release
    this stretch at the endFrame.            
    '''
    
    ctrl = selCtrl[0]
    pi = []
    n = 0
    vi = 0
    smearFrame = 0
    
    #finding the velocity based on position difference(v = p - p0) for every frame from startFrame to endFrame, then, find the frame with maximum velocity, store it as smearFrame.
    for i in range(startFrame,endFrame):
        cmds.currentTime(i)
        
        #getting translate z of the ctrl in the current frame.
        p = cmds.xform(ctrl,q=True,t=True)
        p = p[2] 
        pi.append(p)
        
        #subtract current position with that from previous frame to get a velocity, as v = p0-p/t where, in this case t=1 as we calculate from each frame and hence, neglected. 
        if n>=1:
            v = pi[n]-pi[n-1]
            
            #comparing current velocity with prevoius one, which one is greater is stored as smearFrame.
            if vi<v:
                vi = v
                smearFrame = i
        n=n+1
    
    #spliting the attr accepted from the user as attrHi[ctrl_name,attr_name]            
    attrHi = attr.split('.')
    
    #key frame the one frame right before stretch smear
    cmds.currentTime(smearFrame-1)
    cmds.setKeyframe(attrHi[0],bd = False, pcs = False, hi = 'None',cp= False, shape = False)
    currentAttr = cmds.getAttr(attr)
    cmds.setAttr(attr,currentAttr)
    cmds.autoKeyframe()
    
    #keyframe the startSmear (stretch smear frame).
    cmds.currentTime(smearFrame)
    #finding the maximum value of the squash and stretch attr. 
    attr_max = cmds.attributeQuery(attrHi[-1],node = attrHi[0],max = True)[0]
    cmds.setKeyframe(attrHi[0],bd = False, pcs = False, hi = 'None',cp= False, shape = False)
    cmds.setAttr(attr,attr_max)
    cmds.autoKeyframe()
    
    #keyframe the endFrame
    cmds.currentTime(endFrame)
    cmds.setKeyframe(attrHi[0],bd = False, pcs = False, hi = 'None',cp= False, shape = False)
    cmds.setAttr(attr,currentAttr)
    cmds.autoKeyframe()

master_ctrl = cmds.ls(sl = True)
autoStretchSmear(master_ctrl,1,20,'squash_ctrl.squash_attr')