"""
#run this script in Maya Script Editor after putting the .py file in the maya scripts folder

from importlib import reload
from autosmear import demo_stretching_ui
reload(demo_stretching_ui)
demo_stretching_ui.run()
"""

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
from importlib import reload
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import ast

from autosmear import demo_stretching_utils
reload(demo_stretching_utils)

#! WIP
from autosmear import ghostingIntervalsmear
reload(ghostingIntervalsmear)

class MainWidget(QMainWindow):
    """
    main widget that contains TabWidget of the 3 main features
    """
    def __init__(self, *args, **kwargs):
        super(MainWidget, self).__init__(*args, **kwargs)

        self.resize(320, 620)
        self.setWindowTitle("Autosmear Tool")

        self.stretching_feature = StretchingWidget()
        self.infoinput = InfoInput()
        self.attribute_combobox = AttributeComboBox()
        self.hierawid = ChildControllerListWidget()

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        self.feature_tab_widget = QTabWidget()
        self.main_menubar = self.menuBar()

        self.main_toolbar = QToolBar()
        self.main_toolbar.setMovable(False)

        self.reload_action = QAction("Reload Tool", self)
        self.open_history = QAction("Open Smear History", self)
        self.help_action = QAction("Go to Autosmear Documentation", self)

        self.edit_menu = self.main_menubar.addMenu("Edit")
        self.edit_menu.addAction(self.reload_action)
        self.edit_menu.addAction(self.open_history)

        self.help_menu = self.main_menubar.addMenu("Help")
        self.help_menu.addAction(self.help_action)

        self.feature_tab_widget.addTab(self.stretching_feature,"Stretching")
        self.feature_tab_widget.addTab(GhostingWidget(),"Ghosting")
        self.feature_tab_widget.addTab(BlendingWidget(),"Blending")

        # ----------- CREATE MAIN BUTTON ------------ #
        self.button_layout = QVBoxLayout()

        self.create_button = QPushButton("Create Smear")
        self.create_button.setMinimumHeight(30)
        self.delete_button = QPushButton("Delete Smear")
        self.delete_button.setMinimumHeight(30)
        self.dummy_button = QPushButton("Dummy Button")
        self.dummy_button.setMinimumHeight(30)

        self.button_layout.addWidget(self.create_button)
        self.button_layout.addWidget(self.delete_button)

        # self.create_button.clicked.connect(
        #     self.hierawid.return_item_string)
        self.create_button.clicked.connect(self.create_command)
        #? self.delete_button.clicked.connect(self.stretching_feature.delete_command)
        self.delete_button.clicked.connect(self.clear_command)
        # # self.dummy_button.clicked.connect(self.hierawid.return_item_list)
        # self.dummy_button.clicked.connect(self.self.stretching_feature.delete_command)

        # ----------- ADD WIDGETS TO MAIN LAYOUT ------------ #

        self.addToolBar(self.main_toolbar)
        self.main_layout.addWidget(self.feature_tab_widget)
        self.main_layout.addWidget(self.infoinput)
        self.main_layout.addLayout(self.button_layout)

        self.setLayout(self.main_layout)
    
    def create_command(self):
        """
        Create Smear command bounded to the button
        (can be defined as main connection with Utils)

        can be switched with other main features' create command
        """
        #! Creation of Clear Smear
        if not cmds.objExists("smear_history_grp"):
            cmds.group(em=True, name="smear_history_grp")
        
        if self.feature_tab_widget.currentIndex() == 0:
            demo_stretching_utils.get_values(
            start_frame = self.infoinput.start_frame_spinbox.value(),
            end_frame = self.infoinput.end_frame_spinbox.value(),
            raw_squash_attribute = self.attribute_combobox.currentText(),
            master_squash_attribute = self.stretching_feature.selected_jnt_ctrl_layout.data_lineedit.text(),
            multiplier = self.infoinput.multiplier_doublespinbox.value(),
            start_ctrl = self.stretching_feature.start_jnt_controller_widget.data_lineedit.text(),
            end_ctrl = self.stretching_feature.end_jnt_controller_widget.data_lineedit.text(),
            command_option = self.stretching_feature.radiobutton_selection(),
            ctrl_hierarchy = self.stretching_feature.hierawid.return_item_list()
            )
        elif self.feature_tab_widget.currentIndex() == 1:
            ghostingIntervalsmear.get_values(
            start_frame = self.infoinput.start_frame_spinbox.value(),
            end_frame = self.infoinput.end_frame_spinbox.value(),
            smear_interval = self.infoinput.interval_spinbox.value()
            )
        else:
            print("NO TASK")
    
    def clear_command(self):
        attr_name = cmds.listAttr("smear_history_grp", ud=True)[0]
        smear_history = "smear_history_grp.{attr}".format(attr=attr_name)
        history_dict = cmds.getAttr(smear_history)
        split_history_dict = history_dict.split("||")
        converted_keyframe_list = ast.literal_eval(split_history_dict[1])
        current_time = int(split_history_dict[0])

        for member in converted_keyframe_list:
            cmds.cutKey( member, time=(current_time,current_time), option="keys", clear=True )
        
        cmds.setAttr(smear_history, lock=False)
        cmds.deleteAttr("smear_history_grp", at=attr_name)
        cmds.delete(
            "{last_ctrl}_autoSmearTool_LOC_grp".format(last_ctrl=converted_keyframe_list[-1]))


class StretchingWidget(QWidget):
    """
    Stretching feature sub-tab widget
    """

    signal = Signal()

    def __init__(self, *args, **kwargs):
        super(StretchingWidget, self).__init__(*args, **kwargs)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        # self.main_layout.setContentsMargins(0, 0, 0, 0)
        # self.main_layout.setSpacing(5)

        self.hierawid = ChildControllerListWidget()
        self.attribute_combobox = AttributeComboBox()
        self.infoinput = InfoInput()
        self.delete_current_command = None

        self.main_toolbox = QToolBox()
        # self.main_toolbox.setStyleSheet("background-color: #4d4d4d")

        # ----------- CREATE SPACER ------------ #
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer = QSpacerItem(20, 40, QSizePolicy.Expanding)
        self.fixed_spacer = QSpacerItem(20, 220, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.basedon_label = QLabel("Based on:")

        # ----------- ATTRIBUTE BASED SUB-WIDGET ------------ #
        self.selected_jnt_ctrl_layout = GetInputLayout(label="Selected controller:")

        self.selected_jnt_widget = QWidget()
        self.selected_jnt_vertical_layout = QVBoxLayout()
        self.selected_jnt_widget.setLayout(self.selected_jnt_vertical_layout)

        self.selected_jnt_ctrl_layout.data_button.clicked.connect(self.get_ctrl_command)

        self.selected_jnt_vertical_layout.addLayout(self.selected_jnt_ctrl_layout)
        self.selected_jnt_vertical_layout.addWidget(self.attribute_combobox)
        self.selected_jnt_vertical_layout.addItem(self.spacer)

        # ----------- HIERARCHICAL BASED SUB-WIDGET ------------ #
        self.hierarchy_widget = QWidget()
        self.hierarchy_vertical_layout = QVBoxLayout()
        self.get_hierarchy_button_layout = QHBoxLayout()
        self.hierarchy_widget.setLayout(self.hierarchy_vertical_layout)

        # add start/end jnt widget class
        self.start_jnt_controller_widget = GetInputLayout(label="Start controller:")
        self.end_jnt_controller_widget = GetInputLayout(label="End controller:")
        self.start_jnt_controller_widget.data_button.clicked.connect(self.set_start_text_command)
        self.end_jnt_controller_widget.data_button.clicked.connect(self.set_end_text_command)

        self.get_hierarchy_button = QPushButton("get hierarchy")
        self.get_hierarchy_button.setStyleSheet("background-color: #4d4d4d")
        self.get_hierarchy_button.clicked.connect(self.hierarwid_get_data)

        self.get_hierarchy_add_button = QPushButton("add")
        self.get_hierarchy_add_button.setStyleSheet("background-color: #4d4d4d")
        self.get_hierarchy_add_button.clicked.connect(self.hierawid.add_new_item)

        self.get_hierarchy_remove_button = QPushButton("remove")
        self.get_hierarchy_remove_button.setStyleSheet("background-color: #4d4d4d")
        self.get_hierarchy_remove_button.clicked.connect(self.hierawid.delete_current_index)

        self.get_hierarchy_button_layout.addWidget(self.get_hierarchy_button)
        self.get_hierarchy_button_layout.addWidget(self.get_hierarchy_add_button)
        self.get_hierarchy_button_layout.addWidget(self.get_hierarchy_remove_button)

        self.hierarchy_vertical_layout.addLayout(self.start_jnt_controller_widget)
        self.hierarchy_vertical_layout.addLayout(self.end_jnt_controller_widget)
        self.hierarchy_vertical_layout.addLayout(self.get_hierarchy_button_layout)
        self.hierarchy_vertical_layout.addWidget(self.hierawid)

        # --- test widget 02 --- #
        self.lolo = QWidget()

        # self.selected_jnt_widget.setStyleSheet("background-color: #4d4d4d")
        # self.hierarchy_widget.setStyleSheet("background-color: #4d4d4d")

        self.main_toolbox.addItem(self.selected_jnt_widget, "attribute")
        self.main_toolbox.addItem(self.hierarchy_widget, "controllers")
        # self.main_toolbox.setCurrentIndex(1)

        # ----------- ADD WIGETS TO MAIN LAYOUT ------------ #
        self.main_layout.addWidget(self.basedon_label)
        self.main_layout.addWidget(self.main_toolbox)
        # self.main_layout.addItem(self.fixed_spacer)
        #! self.main_layout.addWidget(self.keyframe_confining_widget)
        # self.main_layout.addLayout(self.button_layout)
        # self.main_layout.addWidget(self.dummy_button)
    
    def radiobutton_selection(self):
        """
        function for returning selected radio button selection

        Returns
            int: ordinal number of selected radio button
        """
        selection_number = 1
        if self.main_toolbox.currentIndex() == 1:
            selection_number = 2
        return(int(selection_number))
    
    def hierarwid_get_data(self):
        """
        get list data from hirarchy widget
        """
        start_text = self.start_jnt_controller_widget.data_lineedit.text()
        end_text = self.end_jnt_controller_widget.data_lineedit.text()
        self.hierawid.get_hierarchy(start_text, end_text)
    
    def set_start_text_command(self):
        """
        set start controller text
        """
        obj_name = object_query_command("single")
        if obj_name is None:
            cmds.warning("Nothing is selected")
            return
        self.start_jnt_controller_widget.data_lineedit.setText(obj_name)
    
    def set_end_text_command(self):
        """
        set end controller text
        """
        obj_name = object_query_command("single")
        if obj_name is None:
            cmds.warning("Nothing is selected")
            return
        self.end_jnt_controller_widget.data_lineedit.setText(obj_name)
    
    def get_ctrl_command(self):
        """
        add item to item list widget
        """
        obj_name = object_query_command("single")
        if obj_name is None:
            cmds.warning("Nothing is selected")
            return
        self.selected_jnt_ctrl_layout.data_lineedit.setText(obj_name)
        attrs_list = attributes_query_command(obj_name)
        if attrs_list is None:
            cmds.warning("No available attribute")
            return
        for item in attrs_list:
            self.attribute_combobox.addItem(item)
    
    def delete_command(self):
        if self.delete_current_command is None:
            self.delete_current_command = DeleteSmearWindow()
        
        show_delete_miniwindow()


class InfoInput(QWidget):
    """
    input mutiplier and start/end frame
    """
    def __init__(self, *args, **kwargs):
        super(InfoInput, self).__init__(*args, **kwargs)

        self.horizontal_spacer = QSpacerItem(20, 40, QSizePolicy.Expanding)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.setMaximumHeight(170)

        # ----------- MULTIPLIER & START/END FRAME WIDGET ------------ #
        self.keyframe_confining_layout = QVBoxLayout()
        self.keyframe_confining_layout.setContentsMargins(0, 0, 0, 0)
        self.keyframe_confining_layout.setSpacing(1)

        self.multiplier_layout = QHBoxLayout()
        self.setLayout(self.keyframe_confining_layout)

        self.multiplier_label = QLabel("Multiplier:")
        self.multiplier_doublespinbox = QDoubleSpinBox()
        self.multiplier_doublespinbox.setValue(1.0)
        self.multiplier_doublespinbox.setSingleStep(0.1)
        self.multiplier_doublespinbox.setMaximum(100.0)

        self.multiplier_layout.addWidget(self.multiplier_label)
        self.multiplier_layout.addWidget(self.multiplier_doublespinbox)
        self.multiplier_layout.addItem(self.horizontal_spacer)

        self.start_frame_layout = QHBoxLayout()
        self.start_frame_label = QLabel("Start Frame:")
        self.start_frame_spinbox = QSpinBox()
        self.start_frame_spinbox.setMaximum(100000)

        self.start_frame_layout.addWidget(self.start_frame_label)
        self.start_frame_layout.addWidget(self.start_frame_spinbox)
        self.start_frame_layout.addItem(self.horizontal_spacer)

        self.end_frame_layout = QHBoxLayout()
        self.end_frame_label = QLabel("End Frame: ")
        self.end_frame_spinbox = QSpinBox()
        self.end_frame_spinbox.setMaximum(100000)

        self.end_frame_layout.addWidget(self.end_frame_label)
        self.end_frame_layout.addWidget(self.end_frame_spinbox)
        self.end_frame_layout.addItem(self.horizontal_spacer)

        self.interval_layout = QHBoxLayout()
        self.interval_checkbox = QCheckBox("Create interval:")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setEnabled(False)
        self.interval_spinbox.setMaximum(100000)

        self.interval_checkbox.setChecked(False)
        self.interval_checkbox.stateChanged.connect(self.interval_connection)

        self.interval_layout.addWidget(self.interval_checkbox)
        self.interval_layout.addWidget(self.interval_spinbox)
        self.interval_layout.addItem(self.horizontal_spacer)

        self.custom_smear_layout = QHBoxLayout()
        self.custom_smear_checkbox = QCheckBox("Create custom smear frame:")
        self.custom_smear_spinbox = QSpinBox()
        self.custom_smear_spinbox.setEnabled(False)
        self.custom_smear_spinbox.setMaximum(100000)

        self.custom_smear_checkbox.setChecked(False)
        self.custom_smear_checkbox.stateChanged.connect(self.custom_smear_connection)

        self.custom_smear_layout.addWidget(self.custom_smear_checkbox)
        self.custom_smear_layout.addWidget(self.custom_smear_spinbox)
        self.custom_smear_layout.addItem(self.horizontal_spacer)

        self.keyframe_confining_layout.addLayout(self.multiplier_layout)
        self.keyframe_confining_layout.addLayout(self.start_frame_layout)
        self.keyframe_confining_layout.addLayout(self.end_frame_layout)
        self.keyframe_confining_layout.addWidget(self.line)
        self.keyframe_confining_layout.addLayout(self.interval_layout)
        self.keyframe_confining_layout.addLayout(self.custom_smear_layout)
    
    def interval_connection(self):
        if self.interval_checkbox.isChecked() is True:
            self.interval_spinbox.setEnabled(True)
            self.custom_smear_checkbox.setChecked(False)
        else:
            self.interval_spinbox.setEnabled(False)
    
    def custom_smear_connection(self):
        if self.custom_smear_checkbox.isChecked() is True:
            self.custom_smear_spinbox.setEnabled(True)
            self.interval_checkbox.setChecked(False)
        else:
            self.custom_smear_spinbox.setEnabled(False)


class GetInputLayout(QHBoxLayout):
    """
    create horizontal input data widget

    Args:
        label (str): human readable label text
        button_label (str): human readable button label text

    Attributes:
        label (str): stored label text
        button_label (str): stored button label text
    """
    def __init__(self, label="label", button_label="get"):
        super(GetInputLayout, self).__init__()

        self.label = label
        self.button_label = button_label

        self.data_label = QLabel(self.label)
        self.data_lineedit = QLineEdit()
        self.data_button = QPushButton(self.button_label)
        self.data_button.setStyleSheet("background-color: #4d4d4d")

        self.addWidget(self.data_label)
        self.addWidget(self.data_lineedit)
        self.addWidget(self.data_button)


#! create this class in case other functionalities have to be add to manage attributes in the future
class AttributeComboBox(QComboBox):
    """
    interactive ListWidget for showing main controller's children
    """
    def __init__(self, parent=None):
        super(AttributeComboBox, self).__init__(parent)
        self.setStyleSheet("background-color: #323232")
        # self.attributes = attributes
    
    # def add_item(self)
    #     for member in self.attributes:
    #         self.addItem(member)


class GhostFaceListWidget(QListWidget):
    """
    interactive ListWidget for showing main controller's children
    """
    def __init__(self, *args, **kwargs):
        super(GhostFaceListWidget, self).__init__(*args, **kwargs)
        self.item_list = []
    
    def get_faces_obj_name(self, obj_name="None"):
        item = ChildControllerListWidgetItem(obj_name)
        self.indexFromItem(item)
        self.addItem(item)


class ChildControllerListWidget(QListWidget):
    """
    interactive ListWidget for showing main controller's children
    """
    def __init__(self, *args, **kwargs):
        super(ChildControllerListWidget, self).__init__(*args, **kwargs)
        self.item_list = []
        # self.item_object_list = []

    def get_hierarchy(self, start, end):
        """
        get hierarchy to add list item

        Args:
            start (str): start joint controller
            end (str): end joint controller
        """
        if self.count() > 0:
            self.clear_item()
        test_stringlist = demo_stretching_utils.get_ctrl_hierarchy(start, end)
        for nametest in test_stringlist:
                item = ChildControllerListWidgetItem(nametest)
                self.indexFromItem(item)

                self.addItem(item)
                # self.item_object_list.append(item)
                self.item_list.append(item.item_name())
    
    def clear_item(self):
        self.clear()
        self.item_list.clear()
    
    def add_new_item(self):
        objs_name = object_query_command()
        for member in objs_name:
            item = ChildControllerListWidgetItem(member)
            self.indexFromItem(item)

            self.addItem(item)
            self.item_list.append(member)

    
    def delete_current_index(self):
        current_item = self.selectedItems()
        self.item_list.remove(current_item[0].item_name())
        # print(self.item_list)
        self.takeItem(self.currentRow())
    
    def return_item_list(self):
        print(self.item_list)
        return(self.item_list)
    
    #! WIP (in case needed to list all item in the widget at the time)
    def return_item_string(self):
        """
        query actual string name of ChildControllerListWidgetItem(s)

        Returns:
            list: name of items
        """
        return(self.item_list)


class ChildControllerListWidgetItem(QListWidgetItem):
    """
    create single item of ChildControllerListWidget

    Args:
        child_node (str): name of child node

    Attributes:
        child_node (str): stored name of child node
    """
    def __init__(self, child_node):
        super(ChildControllerListWidgetItem, self).__init__()
        self.child_node = child_node
        self.setText(self.child_node)
    
    def item_name(self):
        """
        function for returnnig child node

        Returns:
            str: name of child node
        """
        return(self.child_node)


class GhostingWidget(QWidget):
    """
    Ghosting feature widget
    """
    def __init__(self, *args, **kwargs):
        super(GhostingWidget, self).__init__(*args, **kwargs)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.ghost_list = GhostFaceListWidget()

        self.spacer = QSpacerItem(20, 150, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer = QSpacerItem(20, 40, QSizePolicy.Expanding)

        self.bake_layout = QHBoxLayout()
        self.bake_label = QLabel("Initiate Bake Object")
        self.duplicate_obj_button = QPushButton("Bake selection")
        self.duplicate_obj_button.clicked.connect(self.bake_obj_command)

        self.faces_label = QLabel("Faces of:")

        self.bake_layout.addWidget(self.bake_label)
        self.bake_layout.addWidget(self.duplicate_obj_button)
        self.bake_layout.addItem(self.horizontal_spacer)

        self.main_layout.addLayout(self.bake_layout)
        self.main_layout.addWidget(self.faces_label)
        self.main_layout.addWidget(self.ghost_list)
        self.main_layout.addItem(self.spacer)
    
    def bake_obj_command(self):
        obj = object_query_command()
        ghostingIntervalsmear.get_ghost_object_face_ID(selected_faces=obj)
        self.ghost_list.get_faces_obj_name((obj[0]).split(".")[0])


#! WIP
class BlendingWidget(QWidget):
    """
    Blending feature widget
    """
    def __init__(self, *args, **kwargs):
        super(BlendingWidget, self).__init__(*args, **kwargs)


class DeleteSmearWindow(QDialog):
    """
    Delete Button's separated option window
    """
    def __init__(self, *args, **kwargs):
        super(DeleteSmearWindow, self).__init__(*args, **kwargs)
        self.setFixedSize(QSize(320, 100))
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.setWindowTitle("Warning: Multiple smears")

        self.main_label = QLabel(
            "More than one Autosmear frame have been created. \n Do you want to delete the current frame?")
        self.buttons_layout = QHBoxLayout()
        self.open_history = QPushButton("Open History")
        self.delete_current = QPushButton("Delete Current Smear")
        self.close = QPushButton("Close")

        self.buttons_layout.addWidget(self.open_history)
        self.buttons_layout.addWidget(self.delete_current)
        self.buttons_layout.addWidget(self.close)
        
        self.main_layout.addWidget(self.main_label)
        self.main_layout.addLayout(self.buttons_layout)


def object_query_command(quantity=""):
    """
    function that returns selected
    this function can returns various type of variable depends on input argument

    Args:
        quantity (str): default for type of return; single means one object's name will be returned

    Returns:
        None: if nothing is selected
        str: if input argument is defined as single (return the first member of list)
        list: return all of selections
    """
    object_name_list = cmds.ls(selection=True)
    if len(object_name_list) == 0:
        return
    if quantity == "single":
        return(object_name_list[0])
    else:
        return(object_name_list)

def attributes_query_command(name=""):
    """
    this function only find attributes that is user-defined and keyable for easier filtering
    before user can find the squash/stretch attribute by themselves

    Args:
        name (str): name of controller

    Returns:
        list: list of attributes
    """
    user_defined_attribute = cmds.listAttr(name, ud=True, o=True)
    if user_defined_attribute is None:
        return
    tmp_list = user_defined_attribute[:]
    for member in user_defined_attribute:
        if (
            cmds.getAttr(name + "." + member, channelBox=True, keyable=True) == False
            and cmds.getAttr(name + "." + member, channelBox=True, keyable=False) == False
        ):
            tmp_list.remove(member)
            # print ("remove: " + member)

    user_defined_attribute = tmp_list
    print(user_defined_attribute)
    return user_defined_attribute

def show_delete_miniwindow():
	maya_ptr = omui.MQtUtil.mainWindow()
	ptr = wrapInstance(int(maya_ptr), QWidget)

	global ui_miniwindow
	try:
		ui_miniwindow.close()
	except:
		pass

	ui_miniwindow = DeleteSmearWindow(parent=ptr)
	ui_miniwindow.show()


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
