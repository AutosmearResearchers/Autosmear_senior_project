import maya.cmds as cmds
import maya.mel as mel
from pprint import pprint
import numpy as np
import os

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
    interval_smear_list = [] #!list containing all interval that smear must takes place

    for current_frame in range(start_frame,end_frame+1,smear_interval):
        interval_smear_list.append(current_frame)
    
    return interval_smear_list 

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
    smear_interval=1,
    ):
    '''
    main function for proceeding ghosting smear feature

    Args:
        start_frame (int): start keyframe
        end_frame (int): end keyframe
        smear_interval (int): interval that the smear should be generated
    '''
    #todo read the text file containing the face_ID ghosting data
    path = get_current_maya_file_path(True)

    read_file = open('{path}collection_face_ID.txt'.format(path=path),'r')
    read = read_file.readlines()[0]
    ghosting_lst = eval(read)
    read_file.close()

    #! calculate the smear_frame interval as a list
    smear_frames = get_smear_interval(start_frame,end_frame,smear_interval)

    ghosting_geo_list = []  #? a list stored all the ghosting geometry generated

    #todo transversing through each object face_ID 
    for each_ghost_geo in ghosting_lst:
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
            ghosting_geo_list.append(duplicate_geo_name)
            #!remove all the unselected face for that geometry
            if face_ID_list is not []:    
                remove_non_selected_faces(duplicate_geo_name,face_ID_list)
    
    grouping = cmds.group(ghosting_geo_list,name = 'ghosting_Grp')
    group_name = cmds.ls(grouping)[0]


############################################################################    
    #NOTE: Creation of Clear Smear for testing purpose ONLY
    if not cmds.objExists("smear_history_grp"):
        cmds.group(em=True, name="smear_history_grp")
############################################################################

    #! create history dict and record history of smear
    history_dict = "{frame}||{ghost_grp}".format(frame=start_frame, ghost_grp=group_name)
    attr_naming = "ghosting_{keyframe}_{group}".format(group= group_name,keyframe=start_frame)

    cmds.addAttr("smear_history_grp", ln=attr_naming, dt="string")
    cmds.setAttr("smear_history_grp.{attr_name}".format(attr_name = attr_naming), history_dict, type="string", lock = True)

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