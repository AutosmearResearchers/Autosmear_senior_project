import maya.cmds as cmds
import os
import json

def create_history_attr(main_handler="", smear_type="", frame_info=0, type_info="", ctrl_info=""):
    attr_naming = "ghosting_history"
    history_dict = ""
    if smear_type != "ghosting":
        full_path_list = cmds.listRelatives(main_handler, fullPath=True)
        main_handler = full_path_list[0].split('|')[1]
        order_num = check_smear_order(ctrl=main_handler)
        attr_naming = "{stype}_s{order}".format(stype=smear_type, order=order_num)

    if type_info != "":
        history_dict = "{frame}||{type}||{ctrl}".format(frame=frame_info, type=type_info, ctrl=ctrl_info)
    else:
        history_dict = "{frame}||{main_grp}".format(frame=frame_info, main_grp=ctrl_info)

    cmds.addAttr(main_handler, ln=attr_naming, dt="string")
    cmds.setAttr("{grp_path}.{attr_name}".format(grp_path=main_handler,attr_name = attr_naming), history_dict, type="string", lock = False)

def check_smear_order(ctrl=""):
    order_n = 1
    smear_count_list = []
    last_history = cmds.listAttr(ctrl, ud=True)

    if last_history is not None:
        if len(last_history) > 0:
            for each_smear in last_history:
                if each_smear.split("_s")[0] in ["stretching", "blending"]:
                    smear_count_list.append(each_smear)

            if len(smear_count_list) > 0:
                order_n = int((smear_count_list[-1]).split("_s")[1]) + 1
    
    return order_n

def check_unique(main_handler, frame_info, ctrl_info, type_info):

    # check if the creation is unique
    used_frame = frame_info[0] + 1
    nailed_attr_list = None
    checker = False
    if main_handler not in ctrl_info:
        ctrl_info.insert(0, main_handler)
    full_path_list = cmds.listRelatives(main_handler, fullPath=True)
    main_handler = full_path_list[0].split('|')[1]
    whole_stretching_history = cmds.listAttr(main_handler, ud=True)
    if whole_stretching_history:
        for each in whole_stretching_history:
            if "_s" in each:
                nailed_attr_list = (cmds.getAttr("{node}.{attr}".format(node=main_handler, attr=each))).split("||")
                if  type_info == "C":
                    if nailed_attr_list[0] == str(used_frame-1) and nailed_attr_list[2] == "{}".format(ctrl_info):
                        checker = each
                else:
                    if nailed_attr_list[0] == str(used_frame) and nailed_attr_list[2] == "{}".format(ctrl_info):
                        checker = each
    return checker

class HistoryChunkControl(object):
    """
    Combine a chain of commands into one undo.
    Can be used in combination with the "with" statement.
    
    with UndoChunkContext():
        # code
    """
    def __enter__(self):
        cmds.undoInfo(openChunk=True)
        
    def __exit__(self, *exc_info):
        cmds.undoInfo(closeChunk=True)

def write_smear_version(stretching_components=[]):
    """
    stretching_components = [start_ctrl, smear_frame, ctrl_hierarchy, smear_subtype]
    """
    path = get_current_maya_file_path(False)
    path = path[:path.rfind('.')]

    # should be something like; "NC11_woman_test_ghosting_base_ghosting1_version.json"
    full_path = '{path}_stretching_version.json'.format(path=path)

    # if os.path.exists(full_path):
    #     #! if file already exist
    #     old_file = open(full_path, 'r')
    #     SG_dict = json.load(old_file)
    #     old_file.close()
    # else:
    #     #! if file does not exist
    #     SG_dict = {}
    
    # ? overwrite the existing dict with the new dict
    file = open(full_path, 'w')


# def write_smear_version():
#     raw_dag = cmds.ls(ghostingGrp,dag = True,long=True)


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
