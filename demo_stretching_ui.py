"""
#run this script in Maya Script Editor after putting the .py file in the maya scripts folder

from importlib import reload
import demo_stretching_ui
reload(demo_stretching_ui)
demo_stretching_ui.run()
"""

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.cmds as cmds

class MainWidget(QDialog):
    """
    main widget that contains TabWidget of the 3 main features
    """
    def __init__(self, *args, **kwargs):
        super(MainWidget, self).__init__(*args, **kwargs)

        self.resize(330, 420)
        self.setWindowTitle("Demo Autosmear Tool")

        self.main_layout = QVBoxLayout()
        self.feature_tab_widget = QTabWidget()

        self.feature_tab_widget.addTab(StretchingWidget(),"Stretching")
        self.feature_tab_widget.addTab(GhostingWidget(),"Ghosting")
        self.feature_tab_widget.addTab(BlendingWidget(),"Blending")

        self.main_layout.addWidget(self.feature_tab_widget)

        self.setLayout(self.main_layout)


class StretchingWidget(QDialog):
    """
    Stretching feature widget
    """
    def __init__(self, *args, **kwargs):
        super(StretchingWidget, self).__init__(*args, **kwargs)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        # self.main_layout.setContentsMargins(0, 0, 0, 0)
        # self.main_layout.setSpacing(5)

        self.hierawid = ChildControllerListWidget()
        self.attribute_combobox = AttributeComboBox()


        # ----------- CREATE SPACER ------------ #
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer = QSpacerItem(20, 40, QSizePolicy.Expanding)

        # ----------- START/END FRAME WIDGET ------------ #
        self.keyframe_confining_widget = QWidget()
        self.keyframe_confining_layout = QVBoxLayout()
        self.keyframe_confining_widget.setLayout(self.keyframe_confining_layout)

        self.keyframe_confining_layout.setContentsMargins(0, 0, 0, 0)
        self.keyframe_confining_layout.setSpacing(1)

        self.start_frame_layout = QHBoxLayout()
        self.start_frame_label = QLabel("Start Frame:")
        self.start_frame_lineEdit = QSpinBox()
        self.start_frame_lineEdit.setMaximum(100000)

        self.start_frame_layout.addWidget(self.start_frame_label)
        self.start_frame_layout.addWidget(self.start_frame_lineEdit)
        self.start_frame_layout.addItem(self.horizontal_spacer)

        self.end_frame_layout = QHBoxLayout()
        self.end_frame_label = QLabel("End Frame: ")
        self.end_frame_lineEdit = QSpinBox()
        self.end_frame_lineEdit.setMaximum(100000)

        self.end_frame_layout.addWidget(self.end_frame_label)
        self.end_frame_layout.addWidget(self.end_frame_lineEdit)
        self.end_frame_layout.addItem(self.horizontal_spacer)

        self.keyframe_confining_layout.addLayout(self.start_frame_layout)
        self.keyframe_confining_layout.addLayout(self.end_frame_layout)

        # ----------- ATTRIBUTE BASED SUB-WIDGET ------------ #
        self.selected_jnt_widget = QWidget()
        self.selected_jnt_vertical_layout = QVBoxLayout()
        self.selected_jnt_horizontal_layout = QHBoxLayout()
        self.selected_jnt_widget.setLayout(self.selected_jnt_vertical_layout)

        self.selected_jnt_label = QLabel("Selected controller:")
        self.selected_jnt_lineEdit = QLineEdit()
        ##self.selected_jnt_lineEdit.setPlaceholderText("input joint selected_jnt...")
        self.selected_jnt_button = QPushButton("get")
        self.selected_jnt_button.clicked.connect(self.get_command)

        self.selected_jnt_horizontal_layout.addWidget(self.selected_jnt_label)
        self.selected_jnt_horizontal_layout.addWidget(self.selected_jnt_lineEdit)
        self.selected_jnt_horizontal_layout.addWidget(self.selected_jnt_button)

        self.selected_jnt_vertical_layout.addLayout(self.selected_jnt_horizontal_layout)
        self.selected_jnt_vertical_layout.addWidget(self.attribute_combobox)

        # ----------- HIERARCHICAL BASED SUB-WIDGET ------------ #
        self.hierarchy_widget = QWidget()
        self.hierarchy_vertical_layout = QVBoxLayout()
        self.get_hierarchy_button_layout = QHBoxLayout()
        self.hierarchy_widget.setLayout(self.hierarchy_vertical_layout)

        # add start/end jnt widget class
        self.start_jnt_controller_widget = GetSingleDataWidget(label="Start controller:")
        self.end_jnt_controller_widget = GetSingleDataWidget(label="End controller:")
        self.start_jnt_controller_widget.data_button.clicked.connect(self.set_start_text_command)
        self.end_jnt_controller_widget.data_button.clicked.connect(self.set_end_text_command)

        self.get_hierarchy_button = QPushButton("get hierarchy")
        self.get_hierarchy_add_button = QPushButton("add..(WIP)")
        self.get_hierarchy_add_button.setEnabled(False)
        self.get_hierarchy_clear_button = QPushButton("clear..(WIP)")
        self.get_hierarchy_clear_button.setEnabled(False)

        self.get_hierarchy_button_layout.addWidget(self.get_hierarchy_button)
        self.get_hierarchy_button_layout.addWidget(self.get_hierarchy_add_button)
        self.get_hierarchy_button_layout.addWidget(self.get_hierarchy_clear_button)


        self.hierarchy_vertical_layout.addLayout(self.start_jnt_controller_widget)
        self.hierarchy_vertical_layout.addLayout(self.end_jnt_controller_widget)
        self.hierarchy_vertical_layout.addLayout(self.get_hierarchy_button_layout)
        self.hierarchy_vertical_layout.addWidget(self.hierawid)

        self.get_hierarchy_button.clicked.connect(self.hierarwid_get_data)

        self.hierarchy_widget.setEnabled(False)

        # ----------- RADIOBUTTONS WIDGET ------------ #
        self.acceleration_radiobutton_widget = QWidget()
        self.acceleration_radiobutton_layout = QVBoxLayout()
        self.acceleration_radiobutton_widget.setLayout(self.acceleration_radiobutton_layout)

        self.child_controller_radiobutton = QRadioButton("Based on hierarchical controller:")
        self.attribute_radiobutton = QRadioButton("Based on squash/stretch attribute:")
        self.attribute_radiobutton.setChecked(True)
        
        self.attribute_radiobutton.toggled.connect(self.selected_jnt_widget.setEnabled)
        self.attribute_radiobutton.toggled.connect(self.attribute_combobox.setEnabled)

        self.child_controller_radiobutton.toggled.connect(self.hierarchy_widget.setEnabled)

        self.acceleration_radiobutton_layout.addWidget(self.attribute_radiobutton)
        self.acceleration_radiobutton_layout.addWidget(self.selected_jnt_widget)
        self.acceleration_radiobutton_layout.addWidget(self.child_controller_radiobutton)
        self.acceleration_radiobutton_layout.addWidget(self.hierarchy_widget)

        # ----------- CREATE MAIN BUTTON ------------ #
        self.create_button = QPushButton("Create Smear")
        self.create_button.setMinimumHeight(30)
        self.create_button.clicked.connect(self.hierawid.print_item_string)
        self.delete_button = QPushButton("Delete Smear")
        self.delete_button.setMinimumHeight(30)
        ##self.delete_button.clicked.connect()

        # ----------- SET UP MAIN WIDGET ------------ #
        self.main_layout.addWidget(self.acceleration_radiobutton_widget)
        self.main_layout.addWidget(self.keyframe_confining_widget)
        self.main_layout.addItem(self.spacer)
        self.main_layout.addWidget(self.create_button)
        self.main_layout.addWidget(self.delete_button)
    
    def hierarwid_get_data(self):
        start_text = self.start_jnt_controller_widget.data_lineedit.text()
        end_text = self.end_jnt_controller_widget.data_lineedit.text()
        self.hierawid.get_hierarchy(start_text, end_text)
    
    def set_start_text_command(self):
        obj_name = object_query_command("single")
        if obj_name is None:
            cmds.warning("Nothing is selected")
            return
        self.start_jnt_controller_widget.data_lineedit.setText(obj_name)
    
    def set_end_text_command(self):
        obj_name = object_query_command("single")
        if obj_name is None:
            cmds.warning("Nothing is selected")
            return
        self.end_jnt_controller_widget.data_lineedit.setText(obj_name)

    
    def get_command(self):
        obj_name = object_query_command("single")
        if obj_name is None:
            cmds.warning("Nothing is selected")
            return
        self.selected_jnt_lineEdit.setText(obj_name)
        attrs_list = attributes_query_command(obj_name)
        if attrs_list is None:
            cmds.warning("No available attribute")
            return
        for i in attrs_list:
            self.attribute_combobox.addItem(i)


class GetSingleDataWidget(QHBoxLayout):
    """
    create horizontal data widget
    """
    def __init__(self, label="label", button_label="get"):
        super(GetSingleDataWidget, self).__init__()

        self.label = label
        self.button_label = button_label

        self.data_label = QLabel(self.label)
        self.data_lineedit = QLineEdit()
        self.data_button = QPushButton(self.button_label)

        self.addWidget(self.data_label)
        self.addWidget(self.data_lineedit)
        self.addWidget(self.data_button)


class AttributeComboBox(QComboBox):
    """
    interactive ComboBox
    """
    def __init__(self, parent=None):
        super(AttributeComboBox, self).__init__(parent)
        # self.attributes = attributes
    
    # def add_item(self)
    #     for member in self.attributes:
    #         self.addItem(member)

class ChildControllerListWidget(QListWidget):
    """
    interactive ListWidget for showing main controller"s children
    """
    def __init__(self, *args, **kwargs):
        super(ChildControllerListWidget, self).__init__(*args, **kwargs)
        self.item_list = []

    def get_hierarchy(self, start, end):
        """
        get hierarchy to add list item
        """
        test_stringlist = getCtrlHierarchy(start, end)
        for nametest in test_stringlist:
                item = ChildControllerListWidgetItem(nametest)

                self.addItem(item)
                self.item_list.append(item.item_name())
    
    def print_item_string(self):
        """
        Query actual string name of ChildControllerListWidgetItem(s)

        Returns:
            (list) items" name
        """
        print(self.item_list)


class ChildControllerListWidgetItem(QListWidgetItem):
    """
    create item of ChildControllerListWidget
    """
    def __init__(self, child_node):
        super(ChildControllerListWidgetItem, self).__init__()
        self.child_node = child_node
        self.setText(self.child_node)
    
    def item_name(self):
        return(self.child_node)


class GhostingWidget(QDialog):
    """
    Ghosting feature widget
    """
    def __init__(self, *args, **kwargs):
        super(GhostingWidget, self).__init__(*args, **kwargs)


class BlendingWidget(QDialog):
    """
    Blending feature widget
    """
    def __init__(self, *args, **kwargs):
        super(BlendingWidget, self).__init__(*args, **kwargs)

# def hierarchyCall():
#     """
#     call of hierarchy

#     Returns
#     -------
#     list
#         list of children controller nodes of the main controller
#     """
#     hierarchy_list = cmds.

def getCtrlHierarchy(startCtrl = "",endCtrl = ""):
    """
    Note: Utils that actually have to import as module

    Returns:
        list: controller hierarchy
    """
    rawCtrlHierarchyLst = cmds.listRelatives(startCtrl,ad=True)
    ctrlHierarchy = []
        
    #todo filtering the rawLst
    for i in range(len(rawCtrlHierarchyLst)):
        lstElement = rawCtrlHierarchyLst[i]
            
        #! Check if lstElement is a nurb curve and is visible
        if cmds.nodeType(lstElement) == "nurbsCurve" and cmds.getAttr(lstElement+".visibility") == True:
            #! getting controller name from its shape
            ctrlName = cmds.listRelatives(lstElement,parent=True)[0]
                
            ctrlHierarchy.append(ctrlName)
            
        #! break once the the loop tranverse to the endCtrl
        if lstElement is endCtrl:
            break
                
    return ctrlHierarchy    

def object_query_command(quantity="single"):
    """
    Returns:
        None or list or string
    """
    object_name_list = cmds.ls(sl=True)
    if len(object_name_list) == 0:
        return
    if quantity == "single":
        return(object_name_list[0])
    else:
        return(object_name_list)

def attributes_query_command(name=""):
    """
    Returns:
        list
    """
    user_defined_attribute = cmds.listAttr(name, ud=True, o=True)
    if user_defined_attribute is None:
        return
    tmp_list = user_defined_attribute[:]
    for i in user_defined_attribute:
        if (
            cmds.getAttr(name + "." + i, cb=True, k=True) == False
            and cmds.getAttr(name + "." + i, cb=True, k=False) == False
        ):
            tmp_list.remove(i)
            print ("remove: " + i)

    user_defined_attribute = tmp_list
    print(user_defined_attribute)
    return user_defined_attribute


def run():
	maya_ptr = omui.MQtUtil.mainWindow()
	ptr = wrapInstance(int(maya_ptr), QWidget)

	global ui
	try:
		ui.close()
	except:
		pass

	ui = MainWidget(parent=ptr)
	ui.show()
