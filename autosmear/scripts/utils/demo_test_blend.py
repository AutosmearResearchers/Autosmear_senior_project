import maya.cmds as cmds
import maya.mel as mel
from pprint import pprint
import numpy as np
import os
import json
import maya.OpenMaya as om
import math

'''
#PASTE THIS CODE IN THE MAYA SCRIPT EDITOR
from importlib import reload
from autosmear import demo_test_blend
reload(demo_test_blend)

sel = cmds.ls(sl=True)
lattice_dict = demo_test_blend.create_lattice_from_selected_ghost(ghosting_group=sel,lattice_division = [4,3,3])
cluster_grp_lst = demo_test_blend.create_clusters_on_lattice(lattice_edge_loop_dict = lattice_dict)
demo_test_blend.snap_controllers_on_cluster(locator_group_list = cluster_grp_lst)
'''

def create_curve(curve_type = 'circle',name = 'default_curve',radius = 1,normal = [0,1,0]):
    '''
    create_curve()
    This function create a curve based on the shapes input by the user

    Args:
        curve_type (str): type of curve shape to be generated
        name (str): name of the generated curve
        radius (int): radius of the generated curve
        normal ([int,int,int]): list of narmals axis of the generated curve
    '''
    if curve_type == 'circle':
        curve  = cmds.circle(name=name,radius=radius,normal=normal)

    elif curve_type == 'cube':
        curve = cmds.curve(d=1,p=[(0,0,0),(5,0,0),(5,0,5),(0,0,5),(0,0,0),
                                   (0,5,0),(5,5,0),(5,0,0),(5,5,0),
                                   (5,5,5),(5,0,5),(5,5,5),
                                   (0,5,5),(0,0,5),(0,5,5),(0,5,0)])
 
        cmds.CenterPivot()
        cmds.xform(curve,t=(-.5,-.5,-.5))
        cmds.select(curve)
        cmds.FreezeTransformations()
        curve = cmds.rename(name)
        cmds.delete(ch=1)

    return curve    

def create_lattice_from_selected_ghost(ghosting_group=[],lattice_division = [4,2,2]):
    '''
    create_lattice_from_selected_ghost()
    This function accepts the ghosting group and from it generate the lattice deformer to the 
    selected ghost objects. It returns list of vertices of each edge loop on the lattices.

    Args:
        ghosting_group (list): list of ghosting group
        lattice_division ([int,int,int]): three axis of lattice list divisions 
    '''
    lattice_edge_loop_dict = {} #the dictionary storing all the ghosting group : lattice edge loop pair

    #todo create lattice base 
    for each_ghost_ID,each_ghost in enumerate(ghosting_group):
        lattice_elements_list = cmds.lattice(each_ghost,divisions = lattice_division, 
                                             objectCentered = True,
                                             commonParent=True,
                                             outsideLattice = 1,
                                             name='autoSmear{each_ghost_ID}'.format(
                                                 each_ghost_ID=each_ghost_ID+1))
     
        cmds.hide(lattice_elements_list)
        
        #!getting the current ffdLattice name
        ffdLattice = lattice_elements_list[1]
        lattice_group_name = '{ffdLattice}Group'.format(ffdLattice=ffdLattice)
        cmds.select(lattice_group_name)
        cmds.CenterPivot()

        #todo creating cluster and controllers to control them 
        #!querrying each ffdLattice edge loop
        ffd_lattice_edge_loop_lst = []
        
        #!get the lattice edge loop ID in the list 
        for s_division_lattice_ID in range(lattice_division[0]):
            ffd_lattice_vtx_ID_list = []
            
            for t_dividion_lattice_ID in range(lattice_division[1]):
                ffd_edge_loop = '{ffd}.pt[{S}][{T}][0:{U}]'.format(
                    ffd=ffdLattice,
                    S=s_division_lattice_ID,
                    T=t_dividion_lattice_ID,
                    U=lattice_division[2])
                
                #! storing 1 edge loop of a lattice
                ffd_lattice_vtx_ID_list.append(ffd_edge_loop)
            #! storing all the edge loops in that lattice
            ffd_lattice_edge_loop_lst.append(ffd_lattice_vtx_ID_list)

            #todo store the list of edge loops in a dict as ghosting group : [lattice edge loops] pair
            lattice_edge_loop_dict[each_ghost] = ffd_lattice_edge_loop_lst

        cmds.parent(lattice_group_name,each_ghost)

    return lattice_edge_loop_dict

def create_clusters_on_lattice(lattice_edge_loop_dict = {}):
    '''
    create_cluster_on_latiice()
    This function creates the cluster on the lattice input by the users.

    Args:
        lattice_edge_loop_dict (dict): dictionary containing ghosting group : [lattice edge loops] pair
    '''
    #todo create cluster on each edge loops and resets its pivot to match the ghost ws rot
    serial_number = 1
    locator_group_list = []

    for each_ghost in lattice_edge_loop_dict:        
        #todo create cluster on the lattice edge loops
        all_edge_loops = lattice_edge_loop_dict[each_ghost]
        world_space_rotation = cmds.xform(each_ghost,query=True,rotation = True, worldSpace = True)

        #! create cluster on all the edge loops 
        each_ghost_cluster = []
        for current_edge_loop in all_edge_loops:
            cmds.select(current_edge_loop)
            
            suffix = '{each_ghost}_{serial_number}'.format(
                each_ghost = each_ghost,
                serial_number = serial_number
            )

            current_cluster = cmds.cluster(name='cluster_'+suffix)
            current_locator = cmds.spaceLocator(name='locator_'+suffix)
            locator_buffer_group = cmds.group(current_locator,name = 'locator_grp_' + suffix)

            cmds.hide(current_cluster)
            cmds.hide(current_locator)
            
            cmds.matchTransform(locator_buffer_group,current_cluster)
            cmds.xform(locator_buffer_group,rotation = world_space_rotation,worldSpace = True)
            cmds.parentConstraint(current_locator,current_cluster,maintainOffset = True)
            cmds.scaleConstraint(current_locator,current_cluster,maintainOffset = True)

            each_ghost_cluster.append(current_cluster[1])
            each_ghost_cluster.append(locator_buffer_group)
            locator_group_list.append(locator_buffer_group)
            serial_number+=1

        group_name = '{ghost}_cluster_grp'.format(ghost = each_ghost)
        
        #! parent the cluster_grp to subGrp
        cluster_grp = cmds.group(each_ghost_cluster,name = group_name)
        subgrp_name = cluster_grp.split('_cluster_grp')[0]
        cmds.parent(cluster_grp,subgrp_name)
        serial_number = 1

    return locator_group_list

def snap_controllers_on_cluster(locator_group_list=[],ghosting_grp = []):
    '''
    snap_controllers_on_cluster()
    this function accepts list arguments and creates a corresponding ctrl to control the lattice. 
    Also, create a master ctrl.

    ARGS:
    locator_group_list(lst) : list containing the name of the locator placing on the cluster location.
    ghosting_grp(lst) : list contain all the cluster name.
    '''
    curve_lst = []
    ctrl_len = len(locator_group_list)//len(ghosting_grp)
    #todo create a ctrl for the blending object
    for each_locator_group in locator_group_list:
        each_ghost = each_locator_group.split('locator_grp_')[1]
        each_ghost = each_ghost[:each_ghost.rfind('_')]

        #! create a curve ctrl.
        curve = create_curve(curve_type = 'cube',
                     name = '{each_ghost}_curve{sr_no}'.format(each_ghost=each_ghost,
                                                               sr_no = each_locator_group[each_locator_group.rfind('_'):]),
                     radius = 15,
                     normal = [1,0,0])
        
        curve_grp = cmds.group(curve,name = '{each_ghost}_curve_grp{sr_no}'.format(each_ghost=each_ghost,sr_no = each_locator_group[each_locator_group.rfind('_'):]))
        curve_lst.append(curve)
        
        #! snap a created curve ctrl to locator.
        constraint = cmds.parentConstraint(
            each_locator_group, curve_grp, maintainOffset=False)
        cmds.delete(constraint[0])

        if len(curve_lst) == 2:
            crv_i = curve_lst[0].split('_curve')[0]
            crv_ii = curve_lst[1].split('_curve')[0]
            serial_number = curve_lst[1].split('_curve')[1]

            previous_curve_grp_name = '{crv_ii}_curve_grp{serial_number}'.format(
                crv_ii=crv_ii, serial_number=serial_number)

            if crv_i == crv_ii:
                cmds.parent(previous_curve_grp_name, curve_lst[0])

            curve_lst.remove(curve_lst[0])

        #! parent and scale constraint the ctrl.
        locator = each_locator_group.split(
            '_grp')[0] + each_locator_group.split('_grp')[1]
        cmds.pointConstraint(curve, locator, maintainOffset=True)
        cmds.orientConstraint(curve, locator, maintainOffset=True)
        cmds.scaleConstraint(curve, locator, maintainOffset=True)
    
    # todo create master ctrl
        if '_curve_{crv_len}'.format(crv_len=str(ctrl_len)) in curve_lst[0]:
            master_ctrl_grp = create_master_ctrl(curve_lst[0])

            #! parent the master ctrl to the ghosting grp.
            ghost_name = master_ctrl_grp.split('_master_CTRL_GRP')[0]
            cmds.parent(master_ctrl_grp, ghost_name)

            #! parent all the blending component under one single component_grp
            group_blending_components(ghost_name)

def create_master_ctrl(child_curve = ''):
    '''
    create_master_ctrl()
    this function accepts the name of the child curve and creates the master ctrl for it.
    ARGS:
    child_curve(str) : name of the child curve.
    '''
    ghost_name = child_curve.split('_curve')[0]
    main_ctrl = '{ghost_name}_curve_grp_1'.format(ghost_name=ghost_name)

    master_ctrl_name = '{gst}_master_CTRL'.format(gst = ghost_name)
    
    master_crv = create_curve(curve_type='circle', name=master_ctrl_name,
                 radius=30, normal=[0, 1, 0])
    
    master_ctrl_grp = cmds.group(master_crv[0],name = '{master_ctrl}_GRP'.format(master_ctrl = master_ctrl_name))
    
    constraint = cmds.parentConstraint(
        ghost_name, master_ctrl_grp, maintainOffset=False)
    cmds.delete(constraint[0])
    
    cmds.parent(main_ctrl, master_crv[0])

    return master_ctrl_grp

def group_blending_components(sub_grp = ''):
    '''
    group_blending_components()
    this function accepts the name of the sub group, look for all the components related to the blending
    feature then group it. return a resulted blending group.
    ARGS:
    sub_grp(str) : name of the ghosting sub group.
    '''
    hierarchy = cmds.listRelatives(sub_grp,children = True)
    blending_components = []

    for each_child in hierarchy:
        if 'autoSmear' and 'LatticeGroup' in each_child:
            blending_components.append(each_child)
        if '_cluster_grp' in each_child:
            blending_components.append(each_child)
        if '_master_CTRL_GRP' in each_child:
            blending_components.append(each_child)

    sr_no = sub_grp[sub_grp.rfind('_')+1:]
    main_grp = cmds.listRelatives(sub_grp, parent=True)[0]
    prefix = main_grp[main_grp.rfind('_')+1:]
    blending_grp_name = cmds.group(blending_components, 
                                   name = 'Autosmear_{pre}_blendingGrp_{sr_no}'.format(sr_no = sr_no,pre=prefix))
    
    return blending_grp_name

def get_stretching_value(
        sub_grp_lst = []
):
    #todo get the ctrl data for stretching calculation
    ctrl_ID = get_blending_ctrl_data(sub_grp_lst)

    #todo calculate the stretch
    stretch_blending_ctrl(ctrl_ID)

    #todo create history
    tmp_building_func_component(sub_grp_lst)


def get_blending_ctrl_data(sub_grp_lst = []):
    '''
    get_blending_ctrl_data()
    this function accept the list of ghosting sub groups from the user and returns the dictionary of
    'master ctrl grp' : [list of ctrls excluding master ctrl] pair.
    ARGS:
    sub_grp_lst(list) : list of the ghosting sub groups.
    '''
    #todo query all the blending data
    #! query the blending grp
    blend_grp_lst = []
    for sub_grp in sub_grp_lst:
        blend_grp_lst.append([each for each in cmds.listRelatives(sub_grp)
                        if '_blendingGrp_' in each][0])
    
    #! from the blending_grp_lst, query the ctrl grp
    blending_ctrl_ID = {}
    for blend_grp in blend_grp_lst:
        ctrl_grp = [each for each in cmds.listRelatives(blend_grp)
                             if '_master_CTRL_GRP' in each][0]

        if ctrl_grp not in blending_ctrl_ID:
            blending_ctrl_ID[ctrl_grp] = []

        for each_ctrl in cmds.listRelatives(ctrl_grp, allDescendents = True):
            if '_curve_' in each_ctrl and '_grp_' not in each_ctrl and 'shape' not in each_ctrl.lower():
                blending_ctrl_ID[ctrl_grp].append(each_ctrl)

    return blending_ctrl_ID

def stretch_blending_ctrl(ctrl_ID = {}):
    '''
    stretch_blending_ctrl()
    stretch the ctrl by referencing the position of the referred ctrl at the end frame of the 
    ghosting sub group
    '''

    #todo 'pull' the ctrl between start and main ctrl towards aim position with percentage reduction.
    #! query each set of ctrl(s) from the ctrl_ID dictionary.
    for current_master in ctrl_ID:
        ctrl_lst = ctrl_ID[current_master]

        #todo get various value for calculations
        number_of_ctrl = len(ctrl_lst) 
        step_angle = 90/number_of_ctrl
        index = number_of_ctrl - 1

        #! calculation for each ctrl
        for each_ctrl in ctrl_lst:
            
            if index == 3:  # ! if current_ctrl is an end_ctrl
                start_ctrl_translate = cmds.xform(
                    each_ctrl,query = True,translation  = True,worldSpace = True)
            
            elif index == 0:  # ! if current_ctrl is a main ctrl
                end_ctrl_translate = cmds.xform(
                    each_ctrl, query=True, translation=True, worldSpace=True)

            else: #for all the ctrls that needs calculation 
                '''
                if three coordinates A, B and, C forming a right angle triangle. Objective is to find the 
                coordinates of A provided that the angles, coordinate of B being the world space of start_ctrl
                and C being that of the initial position of the current_ctrl. Then, 
                '''
                #todo find the distance and vector BC
                #! current angle ABC
                current_angle = step_angle * index  

                #! position vector B and vector C of triangle ABC
                vector_B = np.array(cmds.xform(ctrl_lst[-1],query=True,translation = True,worldSpace = True))
                vector_C = np.array(cmds.xform(each_ctrl, query=True, translation=True, worldSpace=True))
                
                #! calculate vector BC
                vector_BC = np.array([vector_C[0]-vector_B[0],
                                      vector_C[1]-vector_B[1],
                                      vector_C[2]-vector_B[2]])
                
                #! finding a magnitude of BC, aka a distance
                distance = math.sqrt(math.pow(vector_C[0]-vector_B[0], 2) +
                                     math.pow(vector_C[1]-vector_B[1], 2) +
                                     math.pow(vector_C[2]-vector_B[2], 2))
                
                cap_BC = vector_BC/distance

                #print(f'VECTOR BC : {vector_BC}')
                #print(f'DISTANCE : {distance}')
                #print(f'CAP BC : {cap_BC}')

                #todo find the coordinate of A (vector_A)
                vector_A = np.array([vector_C[0] + (distance*math.cos(current_angle)),
                                     vector_C[1] + (distance*math.cos(current_angle)),
                                     vector_C[2] + (distance*math.cos(current_angle))])
                
                #print(f'VECTOR A : {vector_A}')
                #print('====================================================')

                cmds.xform(each_ctrl,translation = vector_A,worldSpace = True)

            #! updation
            index-=1

def tmp_building_func_component(main_ghosting_grp=[]):
    #! create history dict and record history of smear
    order_num = 1
    smear_count_list = []
    for member in main_ghosting_grp:
        used_frame = (cmds.keyframe(member, q=True))[1]
        full_path_list = cmds.listRelatives(member, fullPath=True)
        full_path = full_path_list[0].split('|')[1]
        last_history = cmds.listAttr(full_path, ud=True)

        if last_history is not None:
            if len(last_history) > 0:
                for each_smear in last_history:
                    if each_smear.split("_s")[0] == "Blending":
                        smear_count_list.append(each_smear)

                if len(smear_count_list) > 0:
                    order_num = int((smear_count_list[-1]).split("_s")[1]) + 1

        history_dict = "{frame}||{main_grp}".format(frame=used_frame, main_grp=full_path)
        attr_naming = "Blending_s{order}".format(order=order_num)

        cmds.addAttr(full_path, ln=attr_naming, dt="string")
        cmds.setAttr("{grp_path}.{attr_name}".format(grp_path=full_path,attr_name = attr_naming), history_dict, type="string", lock = True)
