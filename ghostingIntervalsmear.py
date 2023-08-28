import maya.cmds as cmds
from pprint import pprint
import numpy as np

#todo get the faceId to be duplicated
def getGhostObject(*args):
    sel = cmds.ls(sl=True,fl=True)
    #//pprint(sel)

    #! getting the total number of faces of the geometry.
    nFace = cmds.polyEvaluate(sel[0],face = True)
    #//print(nFace)
    
    #todo checking the geometry faceID that are NOT selected.
    allFaceLst = []
    for i in range(nFace):
        
        currentFaceID = sel[0].split('[')[0] + '[{i}]'.format(i=i)
        
        #! if currentID did not exist in sel imply, that the face aint selected by user
        if currentFaceID not in sel:
             delFaceLst = sel[0].split('.')[0] + '_ghost.f[{i}]'.format(i=i)
             allFaceLst.append(delFaceLst)

    #todo create a ghosting object
    cmds.duplicate(sel[0].split('.')[0],name = sel[0].split('.')[0] + '_ghost')
    
    #!delete non selected face of ghost geo
    cmds.polyDelFacet(allFaceLst)


getGhostObject()
