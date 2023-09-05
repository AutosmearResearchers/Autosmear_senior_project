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
from importlib import reload
import maya.OpenMayaUI as omui
import maya.cmds as cmds

import demo_stretching_utils
reload(demo_stretching_utils)

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
    Stretching feature sub-tab widget
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

        # ----------- ATTRIBUTE BASED SUB-WIDGET ------------ #
        self.selected_jnt_ctrl_layout = GetInputLayout(label="Selected controller:")

        self.selected_jnt_widget = QWidget()
        self.selected_jnt_vertical_layout = QVBoxLayout()
        self.selected_jnt_widget.setLayout(self.selected_jnt_vertical_layout)

        self.selected_jnt_ctrl_layout.data_button.clicked.connect(self.get_ctrl_command)

        self.selected_jnt_vertical_layout.addLayout(self.selected_jnt_ctrl_layout)
        self.selected_jnt_vertical_layout.addWidget(self.attribute_combobox)

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

        # ----------- MULTIPLIER & START/END FRAME WIDGET ------------ #
        self.keyframe_confining_widget = QWidget()
        self.keyframe_confining_layout = QVBoxLayout()
        self.multiplier_layout = QHBoxLayout()
        self.keyframe_confining_widget.setLayout(self.keyframe_confining_layout)

        self.multiplier_label = QLabel("Multiplier:")
        self.multiplier_doublespinbox = QDoubleSpinBox()
        self.multiplier_doublespinbox.setValue(1.0)
        self.multiplier_doublespinbox.setSingleStep(0.1)
        self.multiplier_doublespinbox.setMaximum(100.0)

        self.multiplier_layout.addWidget(self.multiplier_label)
        self.multiplier_layout.addWidget(self.multiplier_doublespinbox)
        self.multiplier_layout.addItem(self.horizontal_spacer)

        self.keyframe_confining_layout.setContentsMargins(0, 0, 0, 0)
        self.keyframe_confining_layout.setSpacing(1)

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

        self.keyframe_confining_layout.addLayout(self.multiplier_layout)
        self.keyframe_confining_layout.addLayout(self.start_frame_layout)
        self.keyframe_confining_layout.addLayout(self.end_frame_layout)

        # ----------- CREATE MAIN BUTTON ------------ #
        self.create_button = QPushButton("Create Smear")
        self.create_button.setMinimumHeight(30)
        # self.create_button.clicked.connect(
        #     self.hierawid.return_item_string)
        self.create_button.clicked.connect(self.create_command)
        self.delete_button = QPushButton("Delete Smear")
        self.delete_button.setMinimumHeight(30)
        self.delete_button.clicked.connect(self.radiobutton_selection)

        # ----------- SET UP MAIN WIDGET ------------ #
        self.main_layout.addWidget(self.acceleration_radiobutton_widget)
        self.main_layout.addWidget(self.keyframe_confining_widget)
        self.main_layout.addItem(self.spacer)
        self.main_layout.addWidget(self.create_button)
        self.main_layout.addWidget(self.delete_button)
    
    def radiobutton_selection(self):
        """
        function for returning selected radio button selection

        Returns
            int: ordinal number of selected radio button
        """
        selection_number = 1
        if self.child_controller_radiobutton.isChecked() is True:
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
    
    def create_command(self):
        """
        Create Smear command bounded to the button
        (can be defined as main connection with Utils)
        """
        demo_stretching_utils.get_values(
            start_frame = self.start_frame_spinbox.value(),
            end_frame = self.end_frame_spinbox.value(),
            raw_squash_attribute = self.attribute_combobox.currentText(),
            master_squash_attribute = self.selected_jnt_ctrl_layout.data_lineedit.text(),
            multiplier = self.multiplier_doublespinbox.value(),
            start_ctrl = self.start_jnt_controller_widget.data_lineedit.text(),
            end_ctrl = self.end_jnt_controller_widget.data_lineedit.text(),
            command_option = self.radiobutton_selection()
            )


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

        Args:
            start (str): start joint controller
            end (str): end joint controller
        """
        test_stringlist = demo_stretching_utils.get_ctrl_hierarchy(start, end)
        for nametest in test_stringlist:
                item = ChildControllerListWidgetItem(nametest)

                self.addItem(item)
                self.item_list.append(item.item_name())
    
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


#! WIP
class GhostingWidget(QDialog):
    """
    Ghosting feature widget
    """
    def __init__(self, *args, **kwargs):
        super(GhostingWidget, self).__init__(*args, **kwargs)


#! WIP
class BlendingWidget(QDialog):
    """
    Blending feature widget
    """
    def __init__(self, *args, **kwargs):
        super(BlendingWidget, self).__init__(*args, **kwargs)


def object_query_command(quantity="single"):
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
