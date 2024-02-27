import maya.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel
import numpy as np
import ast
import maya.OpenMayaUI as omui
import logging
import math
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from autosmear_utils import history_control

def get_values(
    start_frame=1,
    end_frame=1,
    raw_squash_attribute="",
    master_squash_attribute="",
    multiplier=1.0,
    start_ctrl="",
    end_ctrl="",
    command_option=1,
    ctrl_hierarchy=[],
    interval = 1,
    custom_frame = 1,
    smear_option = 1,
    camera_space=False
    ):
    """
    main function for proceeding stretching feature

    Args:
        start_frame (int): start keyframe
        end_frame (int): end keyframe
        raw_squash_attribute (str): node squash/stretch attribute
        master_squash_attribute (str): parent node of squash/stretch attribute (controller)
        multiplier (float): value used to increase the strength of the smear
        start_ctrl (str): start joint controller
        end_ctrl (str): end joint controller
        command_option (int): the chosen option number for different operations (Based on ...)
        smear_option (int): the chosen option for the type of smear that must be generated
    """
    
    #todo check if user choose based on attribute or controller
    print(smear_option)
    smear_subtype = ""
    if command_option == 1:
        #! using function to get the hierarchy of the ctrl
        # ctrl_hierarchy = get_ctrl_hierarchy(start_ctrl,end_ctrl)
        #! using function to calculate the velocity of the obj from start_frame to end_frame
        if smear_option == 1:
            smear_frame = calculate_velocity(start_frame,end_frame,[start_ctrl])  #auto smear
            smear_subtype = "A"
        elif smear_option == 2:
            smear_frame = calculate_interval_smear(start_frame,end_frame,interval)  #interval smear
            smear_subtype = "B"
        else:
            smear_frame = calculate_custom_smear(custom_frame)     #custom smear
            smear_subtype = "C"

        if camera_space == True:
            smear_frame = calculate_velocity_from_camera_space(start_frame, end_frame, [start_frame])
        
        #! using function to keyframe the stretch smear effect (by ctrl)
        if history_control.check_unique(start_ctrl, smear_frame, ctrl_hierarchy, smear_subtype):
            stretch_ctrl(start_frame,end_frame,start_ctrl,smear_frame,ctrl_hierarchy,multiplier,smear_subtype)
        else:
            logger.warning("Existing smear: skip creating")
            return

    else:
        tmp_attr_list = []
        tmp_attr_list.append(master_squash_attribute)
        #! using function to query [[range],default] of the selected attribute
        attribute_value_list = find_attribute_range(raw_squash_attribute,master_squash_attribute)
        #! using function to calculate the velocity of the obj from start_frame to end_frame
        if smear_option == 1:
            smear_subtype = "A"
            smear_frame = calculate_velocity(start_frame,end_frame,ctrl_hierarchy=tmp_attr_list)  #auto smear
        elif smear_option == 2:
            smear_subtype = "B"
            smear_frame = calculate_interval_smear(start_frame,end_frame,interval)  #interval smear
        else:
            smear_subtype = "C"
            smear_frame = calculate_custom_smear(custom_frame)     #custom smear
        
        if camera_space == True:
            smear_frame = calculate_velocity_from_camera_space(start_frame, end_frame, ctrl_hierarchy=tmp_attr_list)
        #! using function to keyframe the stretch smear effect (by attr)
        stretch_attribute(
            smear_frame,
            end_frame,
            master_squash_attribute,
            raw_squash_attribute,
            attribute_value_list,
            multiplier,
            smear_subtype)

def find_attribute_range(raw_squash_attribute = "",master_squash_attribute = ""):
    """
    finding range of squash/stretch attribute

    Args:
        raw_squash_attribute (str): node squash/stretch attribute
        master_squash_attribute (str): parent node of squash/stretch attribute (controller)
    """
    attribute_max = cmds.attributeQuery(raw_squash_attribute,node = master_squash_attribute,maximum = True)
    attribute_default = cmds.attributeQuery(raw_squash_attribute,node = master_squash_attribute,listDefault = True)
    return([attribute_max[0], attribute_default[0]])

def stretch_attribute(smear_frames=[],end_frame = 1,master_squash_attribute="",raw_squash_attribute="",attribute_value_list=[],multiplier=1.0,smear_subtype=""):
    """
    keyframing function
    this function is developed to support calculations in both cases;
    Based on attribute and Based on hierarchical node (controller)

    Args:
        smear_frames (list): list of calculated frames that smear will be created on
        end_frame (int): end frame of smear
        master_squash_attribute (str): node squash/stretch attribute
        raw_squash_attribute (str): parent node of squash/stretch attribute (controller)
        attribute_value_list (list): range of squash/stretch attribute
        multiplier (float): value used to increase the strength of the smear
    """
    max_stretch_value = attribute_value_list[0]
    original_stretch_value = attribute_value_list[1]
    attribute = "{master}.{raw}".format(master = master_squash_attribute,raw = raw_squash_attribute)

    if multiplier<=1:
        max_stretch_value*= multiplier
    else:
        multiplier = 1
    
    print(smear_frames)
    for smear_frame in smear_frames:
        #! keyframe the frame before smear_frame
        cmds.currentTime(smear_frame - 1)
        cmds.setAttr(attribute,original_stretch_value)
        cmds.setKeyframe(attribute,breakdown = False, preserveCurveShape = False, hierarchy = "None",controlPoints= False, shape = False)

        #! keyframe the smear_frame aka. Stretch the rig
        cmds.currentTime(smear_frame)
        cmds.setAttr(attribute,max_stretch_value)
        cmds.setKeyframe(attribute,breakdown = False, preserveCurveShape = False, hierarchy = "None",controlPoints= False, shape = False)

        #! keyframe the end_frame
        cmds.currentTime(end_frame)
        cmds.setAttr(attribute,original_stretch_value)
        cmds.setKeyframe(attribute,breakdown = False, preserveCurveShape = False, hierarchy = "None",controlPoints= False, shape = False)

        order_num = 1
        full_path = cmds.listRelatives(master_squash_attribute, ap=True)[0]
        # full_path = full_path_list[0].split('|')[1]
        last_history = cmds.listAttr(full_path, ud=True)

        if last_history is not None:
            if len(last_history) > 0:
                for each_smear in last_history:
                    if each_smear.split("_s")[0] == "stretching":
                        smear_count_list.append(each_smear)

                if len(smear_count_list) > 0:
                    order_num = int((smear_count_list[-1]).split("_s")[1]) + 1

        history_dict = "{frame}||{type}||{ctrl}".format(frame=smear_frame, type=smear_subtype, ctrl=master_squash_attribute)
        attr_naming = "stretching_s{order}".format(order=order_num)

        cmds.addAttr(full_path, ln=attr_naming, dt="string")
        cmds.setAttr("{grp_path}.{attr_name}".format(grp_path=full_path,attr_name = attr_naming), history_dict, type="string", lock = True)

def get_ctrl_hierarchy(start_ctrl = "",end_ctrl = ""):
    """
    get all descendents (include parent) of referred hierarchical controller

    Args:
        start_ctrl (str): start joint controller
        end_ctrl (str): end joint controller
    """
    raw_ctrl_hierarchy_list = cmds.listRelatives(start_ctrl,allDescendents=True)
    ctrl_hierarchy = []
        
    #todo filtering the rawLst
    for number in range(len(raw_ctrl_hierarchy_list)):
        lstElement = raw_ctrl_hierarchy_list[number]
            
        #! Check if lstElement is a nurb curve and is visible
        if cmds.nodeType(lstElement) == "nurbsCurve" and cmds.getAttr(lstElement+".visibility") == True:
            #! getting controller name from its shape
            ctrlName = cmds.listRelatives(lstElement,parent=True)[0]
                
            ctrl_hierarchy.append(ctrlName)
            
        #! break once the the loop tranverse to the end_ctrl
        if lstElement is end_ctrl:
            break
                
    return(ctrl_hierarchy)    
        
def calculate_velocity(start_frame=1,end_frame=1,ctrl_hierarchy=[]):
    """
    calculating velocity

    Args:
        start_frame (int): start keyframe
        end_frame (int): end keyframe
        ctrl_hierarchy (list): list of hierarchical controller
    """
    #? testing the velocity of three different axis
    #todo Calculate velocity via the main_ctrl
    main_ctrl = ctrl_hierarchy[0]
    pos_list = []
    velocity = [] #?List of all the velocity
    max_a = 0 #? peak acceleration
    s = []    #? list of position difference
    n = 0     #? dynamic array index
    smear_frame = start_frame
    
    for frame_number in range(start_frame,end_frame):
        #todo finding position vector of the main_ctrl for each frame
        cmds.currentTime(frame_number)
        pos_vector = np.array(cmds.xform(main_ctrl,query=True,translation=True,worldSpace=True))
        pos_list.append(pos_vector)
        
        #todo Since, s = pos_list[n] - pos_list[n-1] ==> at n = 0; s = pos_list[0] - 0 
        if frame_number is start_frame:
                        s.append(pos_list[n])
                        n+=1
                        continue
                        
        #todo Calculate the displacement cover by an object at one frame
        s.append(pos_list[n]-pos_list[n-1])
        n+=1
        
    #?Since, the position difference is calculate per 1 frame i.e. t = 1; velocity = change in position/frame(=1) ==> velocity = displacement
    #todo now, to find the frame with maximum change in velocity(acceleration) i.e. a smear frame
    for number in range(len(pos_list)):
        velocity.append(np.sqrt(pos_list[number][0]**2+pos_list[number][1]**2+pos_list[number][2]**2))
        
    for vi in range(len(velocity)): #a1-a0 find the difference    
        if vi == 0:
            continue
        a = velocity[vi] - velocity[vi-1]
        if a>max_a:
            max_a = a
            smear_frame = vi + start_frame
    
    return [smear_frame]

def worldSpaceToScreenSpace(camera, worldPoint):

    # get current resolution
    res_width = cmds.getAttr('defaultResolution.width')
    res_height = cmds.getAttr('defaultResolution.height')

    # get the dagPath to the camera shape node to get the world inverse matrix
    sel_lst = om.MSelectionList()
    print(camera)
    sel_lst.add(camera)
    dagPath = om.MDagPath()
    sel_lst.getDagPath(0, dagPath)
    dagPath.extendToShape()
    camInvMtx = dagPath.inclusiveMatrix().inverse()

    # use a camera function set to get projection matrix, convert the MFloatMatrix
    # into a MMatrix for multiplication compatibility
    fnCam = om.MFnCamera(dagPath)
    mFloatMtx = fnCam.projectionMatrix()
    projMtx = om.MMatrix(mFloatMtx.matrix)

    # multiply all together and do the normalisation
    mPoint = om.MPoint(worldPoint[0], worldPoint[1],
                       worldPoint[2]) * camInvMtx * projMtx
    x = (mPoint[0] / mPoint[3] / 2 + .5) * res_width
    y = (mPoint[1] / mPoint[3] / 2 + .5) * res_height

    return [x, y]

def find_current_camera():
    """
    find_current_camera()
    finding the active camera. Returns string.
    """
    view = omui.M3dView.active3dView()
    cam = om.MDagPath()
    view.getCamera(cam)
    cam_path = cam.fullPathName()

    cam_name = cam_path[1:cam_path.rfind('|')]

    return cam_name

def calculate_velocity_from_camera_space(start_frame=1,end_frame=1,ctrl_hierarchy=[]):
    """
    calculate_velocity_from_camera_space()

    Args:
        start_frame (int): start keyframe
        end_frame (int): end keyframe
        ctrl_hierarchy (list): list of hierarchical controller
    """
    start_ctrl = ctrl_hierarchy[0]
    pos_list = []
    velocity = []  # ?List of all the velocity
    max_a = 0  # ? peak acceleration
    s = []  # ? list of position difference
    n = 0  # ? dynamic array index
    smear_frame = start_frame
    camera = find_current_camera()
    print(camera)

    for frame_number in range(start_frame,end_frame):
        #todo finding position vector of the start_ctrl for each frame
        cmds.currentTime(frame_number)
        worldPosition = cmds.xform(
            start_ctrl, query=True, translation=True, worldSpace=True)
        pos_vector = worldSpaceToScreenSpace(camera=camera,worldPoint=worldPosition)  # //NOTE: Change the camera!
        pos_list.append(pos_vector)

        # todo Since, s = pos_list[n] - pos_list[n-1] ==> at n = 0; s = pos_list[0] - 0
        if frame_number is start_frame:
            s.append(pos_list[n])
            n += 1
            continue

    for vi in range(len(velocity)):  # a1-a0 find the difference
        if vi == 0:
            continue
        a = velocity[vi] - velocity[vi-1]
        if a > max_a:
            max_a = a
            smear_frame = vi + start_frame

    return [smear_frame]

def calculate_interval_smear(start_frame=1,end_frame=1,interval=1):
    """
    calculating an interval smear

    Args:
        start_frame (int): start keyframe
        end_frame (int): end keyframe
        interval (int): interval of the smear
    """
    smear_frames = []
    for each_frame in range(start_frame,end_frame+1,interval):
        smear_frames.append(each_frame)

    return smear_frames

def calculate_custom_smear(custom_frame=1):
    """
    returns the custom_smear_frames

    Args:
        custom_frame (int): custom smear frame
    """  
    return [custom_frame]

def prolonged_end_ctrl(smear_frame=1, prolonged_frame=1, ctrl_hierarchy=[]):
    """
    this function accepts existing smear frames, then creates a prolonged stretch. 

    Args:
        smear_frame (int): existing smear frame.
        prolonged_frame (int): last frame of the stretching effect.
        ctrl_hierarchy (lst): list of hierarical ctrls.
    """

    '''
    CODE SNIPPED:
    import importlib
import sys
toolPath = 'C:/Users/User/OneDrive/Documents/maya/2022/scripts/autosmear/autosmear_scripts'
systemPath = sys.path

if toolPath not in systemPath:
    systemPath.append(toolPath)

from autosmear_utils import stretching_utils as su
importlib.reload(su)

su.prolonged_end_ctrl(
smear_frame = 50,
prolonged_frame = 53, 
ctrl_hierarchy = [
'charizard_rig_v003:flame_01_ctrl',
'charizard_rig_v003:flame_02_ctrl',
'charizard_rig_v003:flame_03_ctrl',
'charizard_rig_v003:flame_04_ctrl'])
    '''

    # todo find the main ctrl (start ctrl)
    first_ctrl = cmds.listRelatives(ctrl_hierarchy[0], children=True)
    last_ctrl = cmds.listRelatives(ctrl_hierarchy[-1], children=True)

    #! determine end ctrl and eliminate
    if len(first_ctrl) > 1:  # imply that first_ctrl is the main ctrl
        end_ctrl = ctrl_hierarchy[-1]

    elif len(last_ctrl) > 1:  # imply that last_ctrl is the main ctrl
        end_ctrl = ctrl_hierarchy[0]

    frame_range = prolonged_frame - smear_frame

    # todo set keyframe to perform a prolonged stretch
    for each_frame in range(frame_range+1):
        cmds.currentTime(smear_frame + each_frame)
        
        if smear_frame + each_frame == smear_frame:
            loc_pos = cmds.xform(end_ctrl, query=True,translation=True, worldSpace=True)
            loc = cmds.spaceLocator(
                name="{ctrlHie}_autoSmearTool_LOC".format(ctrlHie=end_ctrl))
            cmds.xform(loc, translation=loc_pos, worldSpace=True)
        
        cmds.matchTransform(end_ctrl,loc,position = True)
        cmds.setKeyframe(end_ctrl, breakdown=False,
                        preserveCurveShape=False, hierarchy="None", controlPoints=False, shape=False)
    cmds.delete(loc)

def stretch_ctrl(start_frame=1,end_frame=1,start_ctrl="",smear_frames = [],ctrl_hierarchy = [],multiplier = 1.0,smear_subtype = ""):
    number_of_ctrl = len(ctrl_hierarchy)-1
    
    if ctrl_hierarchy[0] != start_ctrl:
        ctrl_hierarchy = ctrl_hierarchy[::-1]
    if start_ctrl in ctrl_hierarchy:
        ctrl_hierarchy.remove(start_ctrl)
    
    locator_list = []
    used_ctrl=[start_ctrl]
    for smear_frame in smear_frames:
        for number in range(number_of_ctrl):

            #todo keyframe start/end frame first!
            cmds.currentTime(start_frame)
            cmds.setKeyframe(ctrl_hierarchy[number],breakdown = False, preserveCurveShape = False, hierarchy = "None",controlPoints= False, shape = False)
            cmds.currentTime(end_frame)
            cmds.setKeyframe(ctrl_hierarchy[number],breakdown = False, preserveCurveShape = False, hierarchy = "None",controlPoints= False, shape = False)

            #todo create ctrl on the smear_frame
            cmds.currentTime(smear_frame)
            ctrl_translation = cmds.xform(ctrl_hierarchy[number],query=True,translation=True,worldSpace=True)
        
            #todo create locator on the location
            if cmds.objExists("{ctrlHie}_{frame}_autoSmearTool_LOC".format(frame=smear_frame,ctrlHie = ctrl_hierarchy[number])) is False:    
                loc = cmds.spaceLocator(name = "{ctrlHie}_{frame}_autoSmearTool_LOC".format(frame=smear_frame,ctrlHie = ctrl_hierarchy[number]))
                locator_list.append(loc[0])
                #!get and set the locator value
                cmds.xform(loc,translation=ctrl_translation,worldSpace=True)
                loc_translate = cmds.xform(loc,query=True,translation=True,worldSpace=True)
                #!snap the ctrl to locator
                cmds.xform(ctrl_hierarchy[number],translation=loc_translate,worldSpace=True)

                #todo snap the ctrl of the next frame to the created loc
                used_frame = smear_frame+1
                cmds.currentTime(used_frame)
                cmds.xform(ctrl_hierarchy[number],translation=loc_translate,worldSpace=True)
                used_ctrl.append(ctrl_hierarchy[number])
    
        #todo group all the locators created after the iteration is complete
        loc_group = cmds.group(locator_list,name = "{ctrlHie}_{frame}_autoSmearTool_LOC_grp".format(frame=smear_frame,ctrlHie = ctrl_hierarchy[number]))
        cmds.delete(loc_group)
        locator_list = []

    #! create history dict and record history of smear
    history_control.create_history_attr(
        start_ctrl, "stretching", used_frame, smear_subtype, str(used_ctrl)
    )
