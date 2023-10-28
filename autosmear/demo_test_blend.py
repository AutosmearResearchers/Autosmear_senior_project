import maya.cmds as cmds
import maya.mel as mel
from pprint import pprint
import numpy as np

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
            
            cmds.matchTransform(locator_buffer_group,current_cluster)
            cmds.xform(locator_buffer_group,rotation = world_space_rotation,worldSpace = True)
            cmds.parentConstraint(current_locator,current_cluster,maintainOffset = True)
            cmds.scaleConstraint(current_locator,current_cluster,maintainOffset = True)

            each_ghost_cluster.append(current_cluster[1])
            each_ghost_cluster.append(locator_buffer_group)
            locator_group_list.append(locator_buffer_group)
            serial_number+=1

        group_name = '{ghost}_cluster_grp'.format(ghost = each_ghost)
        cmds.group(each_ghost_cluster,name = group_name)
        serial_number = 1

    return locator_group_list

def snap_controllers_on_cluster(locator_group_list = []):
    for each_locator_group in locator_group_list:
        each_ghost = each_locator_group.split('locator_grp_')[1]
        each_ghost = each_ghost[:each_ghost.rfind('_')]

        curve = create_curve(curve_type = 'circle',
                     name = '{each_ghost}_curve{sr_no}'.format(each_ghost=each_ghost,
                                                               sr_no = each_locator_group[each_locator_group.rfind('_'):]),
                     radius = 15,
                     normal = [1,0,0])
        
        curve_grp = cmds.group(curve, n = '{each_ghost}_curve_grp{sr_no}'.format(each_ghost=each_ghost,
                                                                     sr_no = each_locator_group[each_locator_group.rfind('_'):]))

        constraint = cmds.parentConstraint(each_locator_group,curve_grp,maintainOffset = False)
        cmds.delete(constraint[0])

        locator = each_locator_group.split('_grp')[0] + each_locator_group.split('_grp')[1]
        cmds.parentConstraint(curve,locator,maintainOffset = True)
        cmds.scaleConstraint(curve,locator,maintainOffset = True)
