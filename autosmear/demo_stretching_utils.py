import maya.cmds as cmds
import maya.mel as mel
import numpy as np
import ast

def get_values(
    start_frame=1,
    end_frame=1,
    raw_squash_attribute="",
    master_squash_attribute="",
    multiplier=1.0,
    start_ctrl="",
    end_ctrl="",
    command_option=1,
    ctrl_hierarchy=[]):
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
    """
    
    #todo check if user choose based on attribute or controller
    if command_option == 2:
        #! using function to get the hierarchy of the ctrl
        # ctrl_hierarchy = get_ctrl_hierarchy(start_ctrl,end_ctrl)
        #! using function to calculate the velocity of the obj from start_frame to end_frame
        smear_frame = calculate_velocity(start_frame,end_frame,ctrl_hierarchy)
        #! using function to keyframe the stretch smear effect (by ctrl)
        stretch_ctrl(start_frame,end_frame,smear_frame,ctrl_hierarchy,multiplier)

    else:
        tmp_attr_list = []
        tmp_attr_list.append(master_squash_attribute)
        #! using function to query [[range],default] of the selected attribute
        attribute_value_list = find_attribute_range(raw_squash_attribute,master_squash_attribute)
        #! using function to calculate the velocity of the obj from start_frame to end_frame
        smear_frame = calculate_velocity(start_frame=start_frame,end_frame=end_frame,ctrl_hierarchy_list=tmp_attr_list)
        #! using function to keyframe the stretch smear effect (by attr)
        stretch_attribute(smear_frame,end_frame,master_squash_attribute,raw_squash_attribute,attribute_value_list,multiplier)

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

def stretch_attribute(smear_frame=1,end_frame = 1,master_squash_attribute="",raw_squash_attribute="",attribute_value_list=[],multiplier=1.0):
    """
    keyframing function
    this function is developed to support calculations in both cases;
    Based on attribute and Based on hierarchical node (controller)

    Args:
        smear_frame (int): calculated frame that smear will be created on
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
    
    return(smear_frame)

def stretch_ctrl(start_frame=1,end_frame=1,smear_frame = 1,ctrl_hierarchy = [],multiplier = 1.0):    
    """
    calculating velocity

    Args:
        smear_frame (int): calculated frame that smear will be created on
        ctrl_hierarchy (list): list of hierarchical controller
        multiplier (float): value used to increase the strength of the smear
    """
    number_of_ctrl = len(ctrl_hierarchy)
    locator_list = []
    used_ctrl=[]

    for number in range(1,number_of_ctrl):
        #todo keyframe start/end frame first!
        cmds.currentTime(start_frame)
        cmds.setKeyframe(ctrl_hierarchy[number],breakdown = False, preserveCurveShape = False, hierarchy = "None",controlPoints= False, shape = False)
        cmds.currentTime(end_frame)
        cmds.setKeyframe(ctrl_hierarchy[number],breakdown = False, preserveCurveShape = False, hierarchy = "None",controlPoints= False, shape = False)

        #todo create ctrl on the smear_frame
        cmds.currentTime(smear_frame)
        ctrl_transaltion = cmds.xform(ctrl_hierarchy[number],query=True,translation=True,worldSpace=True)
        
        #todo create locator on the location
        if cmds.objExists("{ctrlHie}_autoSmearTool_LOC".format(ctrlHie = ctrl_hierarchy[number])) is False:    
            loc = cmds.spaceLocator(name = "{ctrlHie}_autoSmearTool_LOC".format(ctrlHie = ctrl_hierarchy[number]))
            locator_list.append(loc[0])
            #!get and set the locator value
            cmds.xform(loc,translation=ctrl_transaltion,worldSpace=True)
            loc_translate = cmds.xform(loc,query=True,translation=True,worldSpace=True)
            #!snap the ctrl to locator
            cmds.xform(ctrl_hierarchy[number],translation=loc_translate,worldSpace=True)

            #todo snap the ctrl of the next frame to the created loc
            used_frame = smear_frame+1
            cmds.currentTime(used_frame)
            cmds.xform(ctrl_hierarchy[number],translation=loc_translate,worldSpace=True)
            used_ctrl.append(ctrl_hierarchy[number])
    
    #todo group all the locators created after the iteration is complete
    loc_group = cmds.group(locator_list,name = "{ctrlHie}_autoSmearTool_LOC_grp".format(ctrlHie = ctrl_hierarchy[number]))

    #! create history dict and record history of smear
    order_num = 1
    last_history = cmds.listAttr("smear_history_grp", ud=True)
    if last_history is not None:
        if len(last_history) > 0:
            order_num = int((last_history[-1]).split("_s")[1]) + 1

    history_dict = "{frame}||{ctrl}".format(frame=used_frame, ctrl=used_ctrl)
    attr_naming = "stretching_s{order}".format(order=order_num)

    cmds.addAttr("smear_history_grp", ln=attr_naming, dt="string")
    cmds.setAttr("smear_history_grp.{attr_name}".format(attr_name = attr_naming), history_dict, type="string", lock = True)

#! keyframe the Charlizard

