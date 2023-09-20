import maya.cmds as cmds
import maya.mel as mel
from pprint import pprint
import numpy as np

def duplicate_geo_for_selecting_faces(raw_selection_group = []):
    '''
    duplicate_geo_for_selecting_faces()
    this function accept the charcter group from the users and it duplicated the geometry in that
    character group, putting it in the newly created duplicate character geo group.

    Importance: Since, in some case, the character mesh are locked by the rigger, hence, we need to
    duplicate the entire mesh first. 

    Args:
        raw_selection_group([]): chracter group that are selected by the user.
    '''

    #todo filtering only 'mesh' type from raw_selection_group and put it to meshes_group. 
    meshes_group = cmds.ls(raw_selection_group,dag=True,type='mesh')
    
    #todo duplicate the meshes from the meshes_group and put it in a list duplicate_meshes_lst
    duplicate_meshes = cmds.duplicate(meshes_group)
    duplicate_meshes_lst = [] #! list storing all duplicate meshes name for grouping

    #? Now, meshes are duplicated but are are located inside the character_group
    #todo unparent the duplicate meshes and put it in the new group
    for ungroup_obj in duplicate_meshes:
        try:
            #! ungroup the current mesh element in the duplicate_meshes list  
            cmds.parent(ungroup_obj,world=True)
            duplicate_meshes_lst.append(ungroup_obj)

        except:
            continue
    
    #! group all duplicate mesh stored in the duplicate_meshes_lst 
    duplicate_group_name = '{meshes_group}_duplicate_geo'.format(meshes_group=meshes_group[0])

    try:
        cmds.group(duplicate_meshes_lst,name = duplicate_group_name)
    except:
        cmds.group(duplicate_meshes,name = duplicate_group_name)

    #todo unlock all the duplicate geo in the duplicate geo list
    duplicate_geo_lst = cmds.ls(duplicate_group_name,dag =True)

    for ungroup_obj in duplicate_geo_lst:
        try:
            cmds.setAttr(ungroup_obj+'.tx',lock=False)
            cmds.setAttr(ungroup_obj+'.ty',lock=False)
            cmds.setAttr(ungroup_obj+'.tz',lock=False)

            cmds.setAttr(ungroup_obj+'.rx',lock=False)
            cmds.setAttr(ungroup_obj+'.ry',lock=False)
            cmds.setAttr(ungroup_obj+'.rz',lock=False)

            cmds.setAttr(ungroup_obj+'.sx',lock=False)
            cmds.setAttr(ungroup_obj+'.sy',lock=False)
            cmds.setAttr(ungroup_obj+'.sz',lock=False)
        except:
            continue

def get_ghost_object(selected_faces = []):
    '''
    get_ghost_object()
    this function accepts selected faces from the user and then it creates a ghosting object from
    that selected faces.

    Args:
        selected_faces([]): list of faces ID selected by the user. (selection = True, flatten = True)
    '''

    #todo getting the total number of faces of the geometry.
    n_face = cmds.polyEvaluate(selected_faces[0],face = True)
    
    #! checking the geometry faceID that are NOT selected.
    all_face_lst = []
    for i in range(n_face):
        
        current_face_ID= selected_faces[0].split('[')[0] + '[{i}]'.format(i=i)

        #! if currentID did not exist in selected_faces imply, that the face aint selected by user
        if current_face_ID not in selected_faces:
             delete_face_lst = selected_faces[0].split('.')[0] + '_ghost.f[{i}]'.format(i=i)
             all_face_lst.append(delete_face_lst)

    #todo create a ghosting object
    cmds.duplicate(selected_faces[0].split('.')[0],name = selected_faces[0].split('.')[0] + '_ghost')
    
    #todo delete non selected face of ghost geo
    cmds.delete(current_face_ID.split('.')[0])
    cmds.polyDelFacet(all_face_lst)
    mel.eval('DeleteHistory;')

def auto_delete_non_ghost_geo(ghost_group = []):
    '''
    auto_delete_non_ghost_geo()
    this function allows the user to delete the non-ghost objects in the group.

    Args:
        ghost_group([]): list of the ghost_geo_grp
    '''
    #todo get all the geo in the group
    selected_group_component = cmds.ls(selection = True,dag = True,type = 'mesh')
    
    #todo get all the non ghost geo
    for ghost_geoShape in selected_group_component:
        #! delete all the geo without the '_ghost' postfix
        if '_ghost' not in ghost_geoShape:
            try:
                #! ensure that the shape nodes was not deleted
                cmds.delete(ghost_geoShape.replace('Shape',''))
            except:
                continue
    
    cmds.CenterPivot(ghost_group)