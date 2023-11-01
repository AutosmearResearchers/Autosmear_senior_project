import maya.cmds as cmds
import maya.mel as mel
from pprint import pprint
import numpy as np
import os

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
    path = get_current_maya_file_path(True)
    
    if '.f[' in face_ID[0]:    
        geo_name = face_ID[0][:face_ID[0].rfind('.')]
        
        all_faces = cmds.polyListComponentConversion(geo_name,toFace=True)
        all_faces_ID = cmds.ls(all_faces,flatten = True)
        
        for remove_selected_face in face_ID:
            all_faces_ID.remove(remove_selected_face)
                
    else:
        all_faces_ID = face_ID

    file = open('{path}collection_face_ID.txt'.format(path = path),'a+')
    file.write('{all_faces_ID},'.format(all_faces_ID=all_faces_ID))
    file.close()

def clear_face_ID_data():
    '''
    clear_face_ID_data()
    this function clear all the selected face IDs

    Args:
        None
    '''
    path = get_current_maya_file_path(True)

    clear_file = open('{path}collection_face_ID.txt'.format(path=path),'w')
    clear_file.close()


def get_values(
    start_frame=1,
    end_frame=1,
    main_ctrl=[],
    interval = 1,
    custom_frame = 1,
    smear_option = 1,
    visibility_keyframe = 2):
    '''
    main function for proceeding ghosting smear feature

    Args:
        start_frame (int): start keyframe
        end_frame (int): end keyframe
        main_ctrl (list): the list of controller that moves so, to calculate its velocity.
        visibility_keyframe (int): number of frame the ghost should be visible
    '''
    #todo read the text file containing the face_ID ghosting data
    path = get_current_maya_file_path(True)

    read_file = open('{path}collection_face_ID.txt'.format(path=path),'r')
    read = read_file.readlines()[0]
    ghosting_lst = eval(read)
    read_file.close()

    #! calculate the smear_frame  as a list
    if smear_option == 1:    
        smear_frames = calculate_velocity(start_frame,end_frame,main_ctrl)  #auto smear
    elif smear_option == 2:
        smear_frames = get_smear_interval(start_frame,end_frame,interval)   #interval smear
    else:
        smear_frames = get_custom_smear_frame(custom_frame)

    ghosting_geo_list = []  #? a list stored all the ghosting geometry generated
    
    #todo transversing through each object face_ID 
    for each_ghost_geo in ghosting_lst:
        each_ghost_geo_List = []    #? a list used for grouping each generated ghosting object
        first_element = each_ghost_geo[0] #eg. jecket_Geo.f[3280]

        #todo check wether the current elemeny contains the face ID or the entire geometry
        #!contains a face ID i.e. '.f[]'
        if '.f[' in first_element:  
            original_geo_name = first_element[:first_element.rfind('.')]
            face_ID_list = []
            
            for each_face in each_ghost_geo:
                face_ID_list.append(each_face[each_face.rfind('.'):])

        #!contains the entire geometry
        else:   
            original_geo_name = first_element
            face_ID_list = []

        #todo create ghosting for every smear frames calculated.
        for current_frame in smear_frames:
            #!set the keyframe to current frame 
            cmds.currentTime(current_frame)
            #!duplicate the geometry 
            duplicate_geo_name = duplicate_geometry(original_geo_name)
            each_ghost_geo_List.append(duplicate_geo_name)
            
            #!keyframe the visibility of the ghost to be 0 from zero to current frame
            cmds.currentTime(0)
            cmds.setKeyframe(duplicate_geo_name, attribute='visibility', time=0, value=0)
            cmds.currentTime(current_frame)

            #!keyframe the visibility of the ghost to be 1
            cmds.setKeyframe(duplicate_geo_name, attribute='visibility', time=current_frame, value=1)

            ghosting_geo_list.append(duplicate_geo_name)
            #!remove all the unselected face for that geometry
            if face_ID_list is not []:    
                remove_non_selected_faces(duplicate_geo_name,face_ID_list)
            
            #!after visible frame inputed by the user, keyframe the visibility of the ghost to 0 
            cmds.currentTime(current_frame+visibility_keyframe)
            cmds.setKeyframe(duplicate_geo_name, attribute='visibility', time=current_frame+visibility_keyframe, value=0)
    
    #!grouping individual ghost geometry
    grouping = cmds.group(ghosting_geo_list,name = 'AutoSmear_Ghosting_Grp_001')
    group_name = cmds.ls(grouping)[0]

    #!create each individual grouping
    all_ghosting_component = cmds.listRelatives(group_name)
    number_of_ghost_sub_grp = len(smear_frames)

    keyword = ''
    for each_ghost_geo in range(1,number_of_ghost_sub_grp+1):
        #! adding padding
        if len(str(each_ghost_geo)) == 1:
            keyword = '00' + str(each_ghost_geo)
        elif len(str(each_ghost_geo)) == 2:
            keyword = '0' + str(each_ghost_geo)
        else:
            keyword = str(each_ghost_geo)
        
        #! find the matching keyword and group
        individual_group = []
        for each_ghost_component in all_ghosting_component:
            if keyword in each_ghost_component:
                individual_group.append(each_ghost_component)
        
        current_frame = each_ghost_geo - 1
        cmds.currentTime(current_frame)
        sub_grp_name = cmds.group(individual_group,name = 'Ghosting_SubGrp_001')
        
        #!adjust pivot of the ghosting group !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        object_world_rotation = cmds.xform(main_ctrl[0],query = True,rotation = True,worldSpace = True)
        cmds.select(sub_grp_name)
        cmds.manipPivot(o=object_world_rotation)

    #!clear the text file after smear is complete
    clear_face_ID_data()

############################################################################    
    #NOTE: Creation of Clear Smear for testing purpose ONLY
    # if not cmds.objExists("smear_history_grp"):
    #     cmds.group(em=True, name="smear_history_grp")
############################################################################

    #! create history dict and record history of smear
    order_num = 1
    smear_count_list = []
    last_history = cmds.listAttr("persp", ud=True)

    if last_history is not None:
        if len(last_history) > 0:
            for each_smear in last_history:
                if each_smear.split("_s")[0] == "ghosting":
                    smear_count_list.append(each_smear)

            if len(smear_count_list) > 0:
                order_num = int((smear_count_list[-1]).split("_s")[1]) + 1

    history_dict = "{frame}||{ghost_grp}".format(frame=start_frame, ghost_grp=group_name)
    attr_naming = "ghosting_s{order}".format(order=order_num)

    cmds.addAttr("persp", ln=attr_naming, dt="string")
    cmds.setAttr("persp.{attr_name}".format(attr_name = attr_naming), history_dict, type="string", lock = True)

def duplicate_geometry(ghosting_object=''):
    '''
    duplicate_geometry()
    this function accepts the original geometry name then, duplicates it with the new name. It returns
    the new name.

    Args:
        ghosting_object(str): Geometry to be duplicated. 
    '''
    
    #todo duplicate the entire geometry
    new_name = '{ghost_name}__Autosmear_ghost_obj_001'.format(ghost_name=ghosting_object)
    duplicate_geo = cmds.duplicate(ghosting_object,name = new_name)
    cmds.parent(duplicate_geo,world=True)

    duplicate_geo_name = cmds.ls(duplicate_geo)[0]

    return duplicate_geo_name

def remove_non_selected_faces(ghosting_name = '',face_ID_list = []):
    '''
    remove_non_selected_faces()
    '''
    all_delete_face = []
    for each_face in face_ID_list:
        all_delete_face.append(ghosting_name+each_face)

    cmds.polyDelFacet(all_delete_face)

