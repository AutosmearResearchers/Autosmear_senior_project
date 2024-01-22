import maya.cmds as cmds
import maya.mel as mel
from pprint import pprint
import numpy as np
import os
import json
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
from importlib import reload

from utils import history_control
reload(history_control)

'''
NOTE: for testing the NCrig paste this in the script editor

from importlib import reload
from autosmear import demo_ghosting_utils
reload(demo_ghosting_utils)
#1
sel = cmds.ls(sl=1)
demo_ghosting_utils.get_ghost_object_face_ID(sel)

#2
demo_ghosting_utils.get_values(
    start_frame=1,
    end_frame=60,
    main_ctrl=['wristFK_R_CTL'],
    interval = 10,
    custom_frame = 15,
    smear_option = 3)
'''

def get_current_maya_file_path(full_path = False):
    '''
    get_current_maya_file_path()
    '''
    maya_file_path = cmds.file(query=True,expandName=True)

    if full_path:
        scene_directory = maya_file_path[:maya_file_path.rfind('/')+1]
        return scene_directory
    else:
        return maya_file_path

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
    main_ctrl = ctrl_hierarchy[-1]
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
        # print(cmds.xform(main_ctrl,query=True,translation=True,worldSpace=True))
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
    print(f'SMEAR FRAME AT:{smear_frame}')
    return [smear_frame]

def worldSpaceToScreenSpace(camera, worldPoint):

    # get current resolution
    res_width = cmds.getAttr('defaultResolution.width')
    res_height = cmds.getAttr('defaultResolution.height')

    # get the dagPath to the camera shape node to get the world inverse matrix
    sel_lst = om.MSelectionList()
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

def calculate_velocity_from_camera_space(start_frame=1, end_frame=1, ctrl_hierarchy=[]):
    """
    calculate_velocity_from_camera_space()
    This function calculates the smear frame of the object based on its velocity wrt camera spaces

    Args:
        start_frame (int): start keyframe
        end_frame (int): end keyframe
        ctrl_hierarchy (list): list of hierarchical controller
    """
    end_ctrl = ctrl_hierarchy[-1]
    pos_list = []
    velocity = []  # ?List of all the velocity
    max_a = 0  # ? peak acceleration
    s = []  # ? list of position difference
    n = 0  # ? dynamic array index
    smear_frame = start_frame
    camera = find_current_camera()

    for frame_number in range(start_frame, end_frame):
        # todo finding position vector of the end_ctrl for each frame
        cmds.currentTime(frame_number)
        worldPosition = cmds.xform(
            end_ctrl, query=True, translation=True, worldSpace=True)
        pos_vector = worldSpaceToScreenSpace(
            camera=camera, worldPoint=worldPosition)  #//NOTE: Change the camera!
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

def get_smear_interval(start_frame = 1,end_frame = 1,smear_interval=1):
    '''
    get_smear_interval()
    this function accepts the start and end frame and returns the list of intervals the smears must 
    be generated. 
    
    Args:
        start_frame (int): start keyframe
        end_frame (int): end keyframe
        smear_interval (int): interval that the smear should be generated
    '''
    smear_frame = [] #!list containing all interval that smear must takes place

    for current_frame in range(start_frame,end_frame+1,smear_interval):
        smear_frame.append(current_frame)
    
    return smear_frame

def get_custom_smear_frame(custom_frame=1):
    '''
    get_custom_smear_frame ()
    this function accepts the start and end frame and returns the list of intervals the smears must 
    be generated. 
    
    Args:
        start_frame (int): start keyframe
        end_frame (int): end keyframe
        smear_interval (int): interval that the smear should be generated
    '''
    smear_frame = [custom_frame]
    
    return smear_frame

def get_ghost_object_face_ID(selected_faces = []):
    '''
    get_ghost_object_face_ID()
    this function accepts selected faces or geometry from the user and store its ID in the text file

    Args:
        selected_faces([]): list of faces ID selected by the user.
    '''
    #todo getting all the selected faces
    face_ID = cmds.ls(selected_faces,flatten=True)
    
    path = get_current_maya_file_path(False)
    path = path[:path.rfind('.')]
    
    full_path = '{path}_Autosmear_Ghosting_face_ID.json'.format(path=path)

    if os.path.exists(full_path):   
        #! if file already exist
        old_file = open(full_path, 'r')
        face_ID_dict = json.load(old_file)  # a dictionary storing geo_name: geo_face_ID pair
        old_geo_key_lst = list(face_ID_dict.keys()) #geo keys that should not be return to the UI
        
        old_file.close()
    else:
        #! if file does not exist
        face_ID_dict = {}
        old_geo_key_lst = []
    
    # ? overwrite the existing dict with the new dict
    file = open(full_path,'w')    
    for each_face in face_ID: 

        if cmds.nodeType(each_face)=='mesh':
            geo_name = each_face[:each_face.rfind('.f')]
            
            #! creating a geo_name key first before gradually appending the value into it

            if geo_name not in face_ID_dict:    #!if geo_name is not a key in face_ID_dict
                face_ID_dict[geo_name] = []     #imply that its a new key introduce to the dict

            elif each_face in face_ID_dict[geo_name]: #!if geo_name already exist as key in dict AND repeated element 
                continue                              #ignore repeated element 

            face_ID_dict[geo_name].append(each_face)
            
    json_object = json.dumps(face_ID_dict,indent=2)
    #todo overwrite the dictionary into the text file
    file.write(json_object)
    file.close()

    geo_key_lst = list(face_ID_dict.keys())
    geo_return_lst = subtract_lst(geo_key_lst,old_geo_key_lst)

    #print('OLD:')
    #pprint(old_geo_key_lst)
    #print('NEW:')
    #pprint(geo_key_lst)
    #print('RETURN:')
    #print(geo_return_lst)

    return geo_return_lst

def subtract_lst(new_lst = [],old_lst = []):
    '''
    subtract_lst()
    accept two lists from the users and returns the 
    
    lst3 = [value for value in lst1 if value in lst2]
    '''
    intersection_lst = [value for value in new_lst if value not in old_lst]

    return intersection_lst

def clear_face_ID_data():
    '''
    clear_face_ID_data()
    this function clear all the selected face IDs

    Args:
        None
    '''
    path = get_current_maya_file_path(False)
    path = path[:path.rfind('.')]
    full_path = '{path}_Autosmear_Ghosting_face_ID.json'.format(path=path)
    if os.path.exists(full_path):
        os.remove(full_path)
    else:
        print("wth???")
        return

def delete_geo_name_key(geo_name = ''):
    '''
    get_ghost_object_face_ID()
    this function accepts key geo_name and pop the corresponding key:value pair from the ghosting_face_ID
    dictionary.

    Args:
        geo_name (str): key that user wish to delete.
    '''
    path = get_current_maya_file_path(False)
    path = path[:path.rfind('.')]
    full_path = '{path}_Autosmear_Ghosting_face_ID.json'.format(path=path)

    if os.path.exists(full_path):
        file = open(full_path, 'r')
        face_ID_dict = json.load(file)
        file.close()

        try:
            face_ID_dict.pop(geo_name)
            new_file = open(full_path,'w')
            json_object = json.dumps(face_ID_dict, indent=2)

            new_file.write(json_object)
            new_file.close()

        except:
            cmds.warning('Dictionary key does not exist.')

def get_values(
    start_frame=1,
    end_frame=1,
    main_ctrl=[],
    interval = 1,
    custom_frame=1,
    smear_option=1,
    visibility_keyframe=2,
    camera_space=False
    ):
    '''
    main function for proceeding ghosting smear feature

    Args:
        start_frame (int): start keyframe
        end_frame (int): end keyframe
        main_ctrl (list): the list of controller that moves so, to calculate its velocity.
        visibility_keyframe (int): number of frame the ghost should be visible
    '''
    #todo read the text file containing the face_ID ghosting data
    path = get_current_maya_file_path(False)
    path = path[:path.rfind('.')]

    read_file = open('{path}_Autosmear_Ghosting_face_ID.json'.format(path=path),'r')
    ghosting_lst = json.load(read_file)
    read_file.close()

    #! calculate the smear_frame as a list
    #todo identify current smear frame(s)
    q_smear_frames = ""
    smear_subtype = ""
    if smear_option == 1:    
        smear_frames = calculate_velocity(start_frame,end_frame,main_ctrl)  #auto smear
        q_smear_frames = "{current}".format(current=smear_frames[0])
        smear_subtype = "A"
    elif smear_option == 2:
        smear_frames = get_smear_interval(start_frame,end_frame,interval)   #interval smear
        # q_smear_frames = "{start_current}-{end_current}".format(start_current=smear_frames[0],end_current=smear_frames[-1])
        q_smear_frames = "{current}".format(current=smear_frames)
        smear_subtype = "B"
    else:
        smear_frames = get_custom_smear_frame(custom_frame)
        q_smear_frames = "{current}".format(current=custom_frame)
        smear_subtype = "C"

    if camera_space == True:
        smear_frames = calculate_velocity_from_camera_space(start_frame, end_frame, main_ctrl)  # auto smear with camera space
        q_smear_frames = "{current}".format(current=smear_frames[0])

    sub_grp_lst = [] #?list containing all the sub_grp(s)
    current_grp_name = cmds.group(
        empty = True, name='Autosmear_ghostingGrp_001')
    
    for current_frame in smear_frames:
        ghosting_geo_list = []  # ? a list stored all the ghosting geometry generated
        
        # todo transversing through each object face_ID
        for each_ghost_geo in ghosting_lst:

            original_geo_name = each_ghost_geo
            face_ID_list = ghosting_lst[each_ghost_geo]

            # todo create ghosting for every smear frames calculated.
            #!duplicate the geometry
            duplicate_geo_name = duplicate_geometry(original_geo_name)
            ghosting_geo_list.append(duplicate_geo_name)

            #!remove all the unselected face for that geometry
            if face_ID_list is not []:
                remove_non_selected_faces(duplicate_geo_name, face_ID_list)
        
        #todo create sub_grp
        subGrp_prefix = 'Autosmear'+current_grp_name[current_grp_name.rfind('_'):]
        ctrl_matrix = (cmds.xform(main_ctrl[0], q=True, m=True, ws=True))
        sub_grp = bake_transform_to_parent_matrix(
            ctrl_matrix, ghosting_geo_list, subGrp_prefix)
        sub_grp_lst.append(sub_grp)
        
        #todo key the sub_grp
        initial_frame = (int(cmds.playbackOptions(q=True, min=1)))
        cmds.currentTime(initial_frame)
        cmds.setKeyframe(sub_grp,
                         attribute='visibility', time=initial_frame, value=0)
        
        cmds.currentTime(current_frame)
        cmds.setKeyframe(sub_grp,
                         attribute='visibility', time=current_frame, value=1)
        
        cmds.currentTime(current_frame+visibility_keyframe)
        cmds.setKeyframe(sub_grp,
                         attribute='visibility', time=current_frame+visibility_keyframe, value=0)

    cmds.parent(sub_grp_lst,current_grp_name)

    #! store the shaders for the ghosting object
    store_material_SG(current_grp_name)
    
    #! create history dict and record history of smear
    history_control.create_history_attr(
        current_grp_name, "ghosting", q_smear_frames, smear_subtype, current_grp_name
    )
    # order_num = 1
    # smear_count_list = []

    # history_dict = "{frame}||{type}||{ghost_grp}".format(frame=q_smear_frames, type=smear_subtype, ghost_grp=current_grp_name)
    # attr_naming = "ghosting_s{order}".format(order=order_num)

    # #! EDIT: keep history attr in the ghosting_grp itself
    # cmds.addAttr(current_grp_name, ln="smear_history", dt="string")
    # cmds.setAttr("{grp}.{attr_name}".format(grp=current_grp_name, attr_name = "smear_history"), history_dict, type="string", lock = True)

def bake_transform_to_parent_matrix(ctrl_matrix=[], ghosting_geos=[], grp_name=""):
    #! create tmp_grp for Ghosting geos & find its world translation
    cmds.group(ghosting_geos, n="tmp_grp")
    tmp_grp_translation = cmds.xform("tmp_grp", query=True, scalePivot=True)

    #! clear old translation matrix and add the tmp instead
    del ctrl_matrix[-4:]
    for member in tmp_grp_translation:
        ctrl_matrix.append(member)
    ctrl_matrix.append(1.0)

    #! create sub group at (0,0,0) & set offsetParentMatrix
    new_grp_name = "{prefix}_{postfix}".format(
        prefix=grp_name, postfix='Ghosting_SubGrp_001')
    grp_command = cmds.group(em=True, n=new_grp_name)
    cmds.setAttr("{subgrp}.offsetParentMatrix".format(
        subgrp=grp_command), ctrl_matrix, type="matrix")

    #! move Ghosting geos into Ghosting_SubGrp & delete tmp_grp
    cmds.parent(ghosting_geos, grp_command)
    cmds.delete("tmp_grp")

    grp_children = cmds.listRelatives(grp_command, allDescendents=True)
    for each_child in grp_children:
        try:
            cmds.rename(each_child,
                        '{new_grp_name}_{each_child}'.format(new_grp_name=grp_command, each_child=each_child))
        except:
            continue

    return grp_command

def duplicate_geometry(ghosting_object=''):
    '''
    duplicate_geometry()
    this function accepts the original geometry name then, duplicates it with the new name. It returns
    the new name.

    Args:
        ghosting_object(str): Geometry to be duplicated. 
    '''
    
    #todo duplicate the entire geometry
    new_name = '{ghost_name}__Autosmear_ghost_obj'.format(ghost_name=ghosting_object)
    duplicate_geo = cmds.duplicate(ghosting_object,name = new_name)
    cmds.parent(duplicate_geo,world=True)
    
    #! unlock the duplicate geometry
    cmds.setAttr('{dup}.tx'.format(dup = duplicate_geo[0]),lock = False)
    cmds.setAttr('{dup}.ty'.format(dup = duplicate_geo[0]),lock = False)
    cmds.setAttr('{dup}.tz'.format(dup = duplicate_geo[0]),lock = False)

    cmds.setAttr('{dup}.rx'.format(dup = duplicate_geo[0]),lock = False)
    cmds.setAttr('{dup}.ry'.format(dup = duplicate_geo[0]),lock = False)    
    cmds.setAttr('{dup}.rz'.format(dup = duplicate_geo[0]),lock = False)

    cmds.setAttr('{dup}.sx'.format(dup = duplicate_geo[0]),lock = False)
    cmds.setAttr('{dup}.sy'.format(dup = duplicate_geo[0]),lock = False)
    cmds.setAttr('{dup}.sz'.format(dup = duplicate_geo[0]),lock = False)

    cmds.setAttr('{dup}.v'.format(dup = duplicate_geo[0]),lock = False)

    duplicate_geo_name = cmds.ls(duplicate_geo)[0]

    return duplicate_geo_name

def remove_non_selected_faces(ghosting_name = '',face_ID_list = []):
    '''
    remove_non_selected_faces()
    '''
    all_selected_faces = []
    all_delete_faces = []

    for each_face in face_ID_list:
        face_ID_name = '{ghosting_name}.f{each_face}'.format(ghosting_name = ghosting_name,
                                                             each_face = each_face.split('.f')[1])
        all_selected_faces.append(face_ID_name)

    all_faces = cmds.polyListComponentConversion(ghosting_name,toFace = True)
    all_faces = cmds.ls(all_faces,flatten = True)

    for current_face in all_faces:
        if current_face not in all_selected_faces:
            all_delete_faces.append(current_face)
    
    cmds.polyDelFacet(all_delete_faces)

def store_material_SG(ghostingGrp=''):
    '''
    store_material_SG()
    this function create a JSON file that store the dictionary of mat_SG:[ghosting_geo(s)] pair.
    Does not return any value.

    ARGS:
    ghosting_geo(str): name of the ghosting group.
    '''
    raw_dag = cmds.ls(ghostingGrp,dag = True,long=True)
    path = get_current_maya_file_path(False)
    path = path[:path.rfind('.')]

    full_path = '{path}_Autosmear_Ghosting_SG.json'.format(path=path)

    if os.path.exists(full_path):
        #! if file already exist
        old_file = open(full_path, 'r')
        SG_dict = json.load(old_file)
        old_file.close()
    else:
        #! if file does not exist
        SG_dict = {}
    
    # ? overwrite the existing dict with the new dict
    file = open(full_path, 'w')
    
    #todo obtain the key value pair for creating the dictionary  
    for long_name in raw_dag:       
        # ! obtain the long name from tranversing the raw_dag list a.k.a. value  
        if '__Autosmear_ghost_obj' in long_name and 'Shape' not in long_name:
            
            # ! obtain the SG
            shaders = cmds.ls(cmds.listHistory(long_name,future = True),type='shadingEngine')
            
            for current_shader in shaders:
                #! if current shader does not exist as a key in an SG_dict, create one
                if current_shader not in SG_dict:
                    SG_dict[current_shader] = []
                
                SG_dict[current_shader].append(long_name)
            #print(f'LONG NAME: {long_name}')
            #print(f'SHADER: {shaders}')
    
    json_object = json.dumps(SG_dict, indent=2)
    
    # todo overwrite the dictionary into the text file
    file.write(json_object)
    file.close()

def reassign_materials():
    '''
    reassign_material()
    this function reassign the shader to the selected object or, ghosting group based on the stored 
    JSON file. Returns no value.

    Args:
        None
    '''
    path = get_current_maya_file_path(False)
    path = path[:path.rfind('.')]
    full_path = '{path}_Autosmear_Ghosting_SG.json'.format(path=path)
    
    #! if file already exist
    if os.path.exists(full_path):
        SG_file = open(full_path, 'r')
        SG_dict = json.load(SG_file)
        
        for current_shader in SG_dict:
            for each_ghosting_geo in SG_dict[current_shader]:
                cmds.select(each_ghosting_geo)
                try:
                    cmds.sets(edit=True, forceElement= current_shader)
                except:
                    continue

    SG_file.close()

def clear_SG_data():
    '''
    clear_SG_data()
    this function clear all the shading group ID

    Args:
        None
    '''
    path = get_current_maya_file_path(False)
    path = path[:path.rfind('.')]
    full_path = '{path}_Autosmear_Ghosting_SG.json'.format(path=path)
    if os.path.exists(full_path):
        os.remove(full_path)
    else:
        print("wth???")
        return
