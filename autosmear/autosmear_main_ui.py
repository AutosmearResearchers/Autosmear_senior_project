"""
#run this script in Maya Script Editor after putting the .py file in the maya scripts folder

from importlib import reload
from autosmear import autosmear_main_ui
reload(autosmear_main_ui)
autosmear_main_ui.run()
"""

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
from importlib import reload
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import ast
import sys
import webbrowser
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from autosmear import demo_stretching_utils
reload(demo_stretching_utils)

#! WIP
from autosmear import demo_ghosting_utils
reload(demo_ghosting_utils)

class MainWidget(QMainWindow):
    """
    main widget that contains TabWidget of the 3 main features
    """
    def __init__(self, *args, **kwargs):
        super(MainWidget, self).__init__(*args, **kwargs)

        self.resize(320, 700)
        self.setWindowTitle("Autosmear Tool")

        self.stretching_feature = StretchingWidget()
        self.ghosting_feature = GhostingWidget()
        self.blending_feature = BlendingWidget()
        self.infoinput = InfoInput()
        self.attribute_combobox = AttributeComboBox()
        self.hierawid = ChildControllerListWidget()
        #self.tablewid = HistoryTableWindow()

        self.history_smear = None

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        self.feature_tab_widget = QTabWidget()
        self.feature_tab_widget.setStyleSheet("""
            }
            QTabWidget::pane{
                border-width: 2px; 
                border-style: solid;
                border-color: #F93462;
            }
        """)
        self.feature_tab_widget.tabBar().setStyleSheet("""
            }
            QTabBar::tab:selected{
                color: #000000;
                background-color: #F93462;
            }
        """)
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
        self.feature_tab_widget.addTab(self.ghosting_feature,"Ghosting")
        self.feature_tab_widget.addTab(self.blending_feature,"Blending")

        self.feature_tab_widget.currentChanged.connect(self.current_tab)
        self.stretching_feature.main_toolbox.currentChanged.connect(self.stretching_current_tab)

        self.open_history.triggered.connect(self.open_history_command)
        self.reload_action.triggered.connect(run)
        self.help_action.triggered.connect(go_to_web)

        # ----------- CREATE MAIN BUTTON ------------ #
        self.button_layout = QVBoxLayout()

        self.create_button = QPushButton("Create Attribute Stretching")
        self.create_button.setMinimumHeight(30)
        self.delete_button = QPushButton("Delete Attribute Stretching")
        self.delete_button.setMinimumHeight(30)
        self.dummy_button = QPushButton("Dummy Button")
        self.dummy_button.setMinimumHeight(30)

        self.button_layout.addWidget(self.create_button)
        self.button_layout.addWidget(self.delete_button)
        # self.button_layout.addWidget(self.dummy_button)

        # self.create_button.clicked.connect(
        #     self.hierawid.return_item_string)
        self.infoinput.start_frame_select_button.clicked.connect(self.frame_selection_command)
        self.infoinput.end_frame_select_button.clicked.connect(self.frame_selection_command)
        self.create_button.clicked.connect(self.create_command)
        self.delete_button.clicked.connect(self.delete_command)
        #? self.delete_button.clicked.connect(self.clear_command)
        # self.dummy_button.clicked.connect(self.open_history_command)
        # self.dummy_button.clicked.connect(self.hierawid.return_item_list)
        # self.dummy_button.clicked.connect(self.stretching_feature.delete_command)

        # --------- ADD GRID LAYOUT --------- #

        self.radiobutton_grid_layout = QGridLayout()
        self.autosmear_radiobutton = QRadioButton("Auto-smear")
        self.autosmear_radiobutton.setChecked(True)

        self.interval_radiobutton = QRadioButton("Create by steps:")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setEnabled(False)
        self.interval_spinbox.setValue(1)
        self.interval_spinbox.setMaximum(100000)

        self.interval_radiobutton.setChecked(False)

        self.interval_vis_duration_label = QLabel("      Each visible for:")
        self.interval_vis_duration_end_label = QLabel("frame")
        self.interval_vis_duration_spinbox = QSpinBox()
        self.interval_vis_duration_spinbox.setEnabled(False)
        self.interval_vis_duration_spinbox.setValue(1)
        self.interval_vis_duration_spinbox.setMaximum(100000)

        self.custom_smear_radiobutton = QRadioButton("Custom smear frame:")
        self.custom_smear_spinbox = QSpinBox()
        self.custom_smear_spinbox.setEnabled(False)
        self.custom_smear_spinbox.setValue(1)
        self.custom_smear_spinbox.setMaximum(100000)
        self.interval_vis_duration_end_label.setEnabled(False)

        self.custom_smear_button = QPushButton("Select")
        self.custom_smear_button.setEnabled(False)

        self.custom_smear_button.clicked.connect(self.frame_selection_command)

        self.custom_smear_radiobutton.setChecked(False)

        self.autosmear_radiobutton.toggled.connect(self.default_connection)
        self.interval_radiobutton.toggled.connect(self.interval_connection)
        self.custom_smear_radiobutton.toggled.connect(self.custom_smear_connection)

        self.radiobutton_grid_layout.addWidget(self.autosmear_radiobutton, 0, 0)
        self.radiobutton_grid_layout.addWidget(self.interval_radiobutton, 1, 0)
        self.radiobutton_grid_layout.addWidget(self.interval_spinbox, 1, 1)
        self.radiobutton_grid_layout.addWidget(self.custom_smear_radiobutton, 2, 0)
        self.radiobutton_grid_layout.addWidget(self.custom_smear_spinbox, 2, 1)
        self.radiobutton_grid_layout.addWidget(self.custom_smear_button, 2, 2)

        # ----------- ADD FRAME ------------ #
        self.frame_widget = QWidget()

        self.frame_one = QFrame(self.frame_widget)
        self.frame_one.setFrameShape(QFrame.StyledPanel)
        self.frame_one.setFrameShadow(QFrame.Plain)
        self.frame_one.setLineWidth(2)

        self.label_step_three = QLabel("3) Choose type of smear:")

        self.frame_one_layout = QVBoxLayout(self.frame_one)
        self.frame_one_layout.addWidget(self.label_step_three)
        self.frame_one_layout.addLayout(self.radiobutton_grid_layout)
        self.frame_one.setLayout(self.frame_one_layout)

        self.frame_widget_2 = QWidget()

        self.frame_zer = QFrame(self.frame_widget_2)
        self.frame_zer.setFrameShape(QFrame.StyledPanel)
        self.frame_zer.setFrameShadow(QFrame.Plain)
        self.frame_zer.setLineWidth(2)

        self.label_step_two = QLabel("2) Input Multiplier and Start/End Frame:")

        self.frame_zer_layout = QVBoxLayout(self.frame_zer)
        self.frame_zer_layout.addWidget(self.label_step_two)
        self.frame_zer_layout.addLayout(self.infoinput)
        self.frame_zer.setLayout(self.frame_zer_layout)

        # ----------- ADD WIDGETS TO MAIN LAYOUT ------------ #

        self.addToolBar(self.main_toolbar)
        self.main_layout.addWidget(self.feature_tab_widget)
        self.main_layout.addWidget(self.frame_zer)
        self.main_layout.addWidget(self.frame_one)
        self.main_layout.addLayout(self.button_layout)

        self.setLayout(self.main_layout)
    
    def test_print(self):
        print("OK")
    
    def create_command(self):
        """
        Create Smear command bounded to the button
        (can be defined as main connection with Utils)

        can be switched with other main features' create command
        """
        #! Creation of Clear Smear
        if self.feature_tab_widget.currentIndex() == 0:
            demo_stretching_utils.get_values(
            start_frame = self.infoinput.start_frame_spinbox.value(),
            end_frame = self.infoinput.end_frame_spinbox.value(),
            raw_squash_attribute = self.stretching_feature.attribute_combobox.currentText(),
            master_squash_attribute = self.stretching_feature.selected_jnt_ctrl_layout.data_lineedit.text(),
            multiplier = self.infoinput.multiplier_doublespinbox.value(),
            start_ctrl = self.stretching_feature.start_jnt_controller_widget.data_lineedit.text(),
            end_ctrl = self.stretching_feature.end_jnt_controller_widget.data_lineedit.text(),
            command_option = self.stretching_feature.basedon_selection(),
            ctrl_hierarchy = self.stretching_feature.hierawid.return_item_list(),
            interval = self.interval_spinbox.value(),
            custom_frame = self.custom_smear_spinbox.value(),
            smear_option = self.radiobutton_selection()
            )
        elif self.feature_tab_widget.currentIndex() == 1:
            type_selection = self.radiobutton_selection()
            auto_main_ctrl = self.ghosting_feature.main_ctrl_layout.data_lineedit.text()
            if type_selection == 1 and auto_main_ctrl == "":
                logger.error("No controller has been selected for Auto-smear creation.")
                return
            demo_ghosting_utils.get_values(
            start_frame = self.infoinput.start_frame_spinbox.value(),
            end_frame = self.infoinput.end_frame_spinbox.value(),
            main_ctrl = [auto_main_ctrl],
            interval = self.interval_spinbox.value(),
            custom_frame = self.custom_smear_spinbox.value(),
            smear_option = type_selection,
            visibility_keyframe = self.ghosting_feature.vis_duration_spinbox.value()
            )
        else:
            print("NO TASK")
    
    # def clear_command(self):
    #     attr_name = cmds.listAttr("smear_history_grp", ud=True)[0]
    #     smear_history = "smear_history_grp.{attr}".format(attr=attr_name)
    #     history_dict = cmds.getAttr(smear_history)
    #     split_history_dict = history_dict.split("||")
    #     converted_keyframe_list = ast.literal_eval(split_history_dict[1])
    #     current_time = int(split_history_dict[0])

    #     for member in converted_keyframe_list:
    #         cmds.cutKey( member, time=(current_time,current_time), option="keys", clear=True )
        
    #     cmds.setAttr(smear_history, lock=False)
    #     cmds.deleteAttr("smear_history_grp", at=attr_name)
    #     cmds.delete(
    #         "{last_ctrl}_autoSmearTool_LOC_grp".format(last_ctrl=converted_keyframe_list[-1]))
    
    def radiobutton_selection(self):
        """
        function for returning selected radio button selection

        Returns
            int: ordinal number of selected radio button
        """
        selection_number = 3
        if self.autosmear_radiobutton.isChecked() is True:
            selection_number = 1
        elif self.interval_radiobutton.isChecked() is True:
            selection_number = 2
        return(int(selection_number))
    
    def frame_selection_command(self):
        clicked_button = self.sender()
        current_frame = int(cmds.currentTime(query=True))
        if clicked_button == self.infoinput.start_frame_select_button:
            self.infoinput.start_frame_spinbox.setValue(current_frame)
        elif clicked_button == self.infoinput.end_frame_select_button:
            self.infoinput.end_frame_spinbox.setValue(current_frame)
        elif clicked_button == self.custom_smear_button:
            self.custom_smear_spinbox.setValue(current_frame)
    
    def current_tab(self):
        if self.feature_tab_widget.currentIndex() == 0:
            if self.stretching_feature.main_toolbox.currentIndex() == 0:
                self.create_button.setText("Create Attribute Stretching")
                self.delete_button.setText("Delete Attribute Stretching")
            else:
                self.create_button.setText("Create Controller Stretching")
                self.delete_button.setText("Delete Controller Stretching")
            self.current_tab_color(0)
        elif self.feature_tab_widget.currentIndex() == 1:
            self.create_button.setText("Create Ghosting")
            self.delete_button.setText("Delete Ghosting")
            self.current_tab_color(1)
        else:
            self.create_button.setText("Create Blending")
            self.delete_button.setText("Delete Blending")
            self.current_tab_color(2)
    
    def current_tab_color(self, selected_tab=0):
        if selected_tab == 0:
            self.feature_tab_widget.setStyleSheet("""
                    QTabWidget::pane{
                        border-width: 2px; 
                        border-style: solid;
                        border-color: #F93462;
                    }
                """)
            self.feature_tab_widget.tabBar().setStyleSheet("""
                    QTabBar::tab:selected{
                        background-color: #F93462;
                    }
                """)
        elif selected_tab == 1:
            self.feature_tab_widget.setStyleSheet("""
                    QTabWidget::pane{
                        border-width: 2px; 
                        border-style: solid;
                        border-color: #1CEA8A;
                    }
                """)
            self.feature_tab_widget.tabBar().setStyleSheet("""
                    QTabBar::tab:selected{
                        background-color: #1CEA8A;
                    }
                """)
        elif selected_tab == 2:
            self.feature_tab_widget.setStyleSheet("""
                    QTabWidget::pane{
                        border-width: 2px; 
                        border-style: solid;
                        border-color: #1CA6EA;
                    }
                """)
            self.feature_tab_widget.tabBar().setStyleSheet("""
                    QTabBar::tab:selected{
                        background-color: #1CA6EA;
                    }
                """)

    def stretching_current_tab(self):
        if self.stretching_feature.main_toolbox.currentIndex() == 0:
            self.create_button.setText("Create Attribute Stretching")
            self.delete_button.setText("Delete Attribute Stretching")
        else:
            self.create_button.setText("Create Controller Stretching")
            self.delete_button.setText("Delete Controller Stretching")
    
    def default_connection(self):
        if self.autosmear_radiobutton.isChecked() is True:
            self.interval_spinbox.setEnabled(False)
            self.custom_smear_spinbox.setEnabled(False)
    
    def interval_connection(self):
        if self.interval_radiobutton.isChecked() is True:
            self.interval_spinbox.setEnabled(True)
            self.interval_vis_duration_spinbox.setEnabled(True)
            self.interval_vis_duration_end_label.setEnabled(True)
        else:
            self.interval_spinbox.setEnabled(False)
            self.interval_vis_duration_spinbox.setEnabled(False)
            self.interval_vis_duration_end_label.setEnabled(False)
    
    def custom_smear_connection(self):
        if self.custom_smear_radiobutton.isChecked() is True:
            self.custom_smear_spinbox.setEnabled(True)
            self.custom_smear_button.setEnabled(True)
        else:
            self.custom_smear_spinbox.setEnabled(False)
            self.custom_smear_button.setEnabled(False)
    
    def open_history_command(self):
        # history_list = []
        # for member in cmds.listAttr("smear_history_grp", ud=True):
        #     history_list.append(member)
        # if self.history_smear is None:
        #     self.history_smear = HistoryTableWindow()
        show_history_window()
    
    def delete_command(self):
        # if self.delete_current_command is None:
        #     self.delete_current_command = DeleteSmearWindow()
        histo_list = cmds.listAttr("persp", ud=True)
        if histo_list is not None:
            if len(histo_list) > 1:
                show_delete_miniwindow()
            elif len(histo_list) == 1:
                clear_command(current_history_index=0, type_smear="stretching")
        else:
            logger.error("No Autosmear has been created.")


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
        # self.setStyleSheet("background-color: #F93462")

        # ----------- CREATE SPACER ------------ #
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer = QSpacerItem(20, 40, QSizePolicy.Expanding)
        self.fixed_spacer = QSpacerItem(20, 220, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.basedon_label = QLabel("1) Choose where Stretching will be created on:")

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
        self.end_jnt_controller_widget = GetInputLayout(label="End controller: ")
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
    
    def basedon_selection(self):
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
            logger.warning("Nothing is selected")
            return
        self.start_jnt_controller_widget.data_lineedit.setText(obj_name)
        self.end_jnt_controller_widget.data_lineedit.setText("")
        self.hierawid.clear_item()
    
    def set_end_text_command(self):
        """
        set end controller text
        """
        obj_name = object_query_command("single")
        if obj_name is None:
            logger.warning("Nothing is selected")
            return
        self.end_jnt_controller_widget.data_lineedit.setText(obj_name)
    
    def get_ctrl_command(self):
        """
        add item to item list widget
        """
        obj_name = object_query_command("single")
        if obj_name is None:
            logger.warning("Nothing is selected")
            return
        self.selected_jnt_ctrl_layout.data_lineedit.setText(obj_name)
        attrs_list = attributes_query_command(obj_name)
        if attrs_list is None:
            logger.warning("No available attribute")
            return
        for item in attrs_list:
            self.attribute_combobox.addItem(item)


class InfoInput(QGridLayout):
    """
    input mutiplier and start/end frame
    """
    def __init__(self, *args, **kwargs):
        super(InfoInput, self).__init__(*args, **kwargs)

        self.horizontal_spacer = QSpacerItem(20, 40, QSizePolicy.Expanding)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        # ----------- MULTIPLIER & START/END FRAME WIDGET ------------ #
        # self.setContentsMargins(1,20,1,20)
        self.setSpacing(5)

        self.multiplier_label = QLabel("Multiplier:")
        self.multiplier_doublespinbox = QDoubleSpinBox()
        self.multiplier_doublespinbox.setValue(1.0)
        self.multiplier_doublespinbox.setSingleStep(0.1)
        self.multiplier_doublespinbox.setMaximum(100.0)
        self.start_frame_label = QLabel("Start Frame:")
        self.start_frame_spinbox = QSpinBox()
        self.start_frame_spinbox.setMaximum(100000)
        self.start_frame_select_button = QPushButton("Select")
        self.start_frame_select_button.setMinimumHeight(20)
        self.end_frame_label = QLabel("End Frame: ")
        self.end_frame_spinbox = QSpinBox()
        self.end_frame_spinbox.setMaximum(100000)
        self.end_frame_select_button = QPushButton("Select")
        self.end_frame_select_button.setMinimumHeight(20)

        self.addWidget(self.multiplier_label, 0, 0)
        self.addWidget(self.multiplier_doublespinbox, 0, 1)
        self.addWidget(self.start_frame_label, 1, 0)
        self.addWidget(self.start_frame_spinbox, 1, 1)
        self.addWidget(self.start_frame_select_button, 1, 2)
        self.addWidget(self.end_frame_label, 2, 0)
        self.addWidget(self.end_frame_spinbox, 2, 1)
        self.addWidget(self.end_frame_select_button, 2, 2)


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


class CustomListWidget(QListWidget):
    """
    interactive ListWidget for showing main controller's children
    """
    def __init__(self, *args, **kwargs):
        super(CustomListWidget, self).__init__(*args, **kwargs)
        self.item_list = []
    
    def get_obj_name(self, obj_name="None"):
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
        # print(self.item_list)
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

        self.ghost_list = CustomListWidget()
        self.main_ctrl_layout= GetInputLayout(label="Start controller:")
        self.main_ctrl_layout.data_button.clicked.connect(self.set_main_ctrl_text_command)

        self.spacer = QSpacerItem(20, 150, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer = QSpacerItem(20, 40, QSizePolicy.Expanding)

        self.tutorial_label = QLabel("1) Select faces to create Ghosting and configure duration:")

        self.bake_layout = QHBoxLayout()
        self.bake_label = QLabel("Initiate Bake Object")
        self.duplicate_obj_button = QPushButton("Bake selection")
        self.duplicate_obj_button.clicked.connect(self.bake_obj_command)

        self.faces_label = QLabel("Faces of:")

        self.bake_layout.addWidget(self.bake_label)
        self.bake_layout.addWidget(self.duplicate_obj_button)
        self.bake_layout.addItem(self.horizontal_spacer)

        self.vis_duration_layout = QHBoxLayout()
        self.vis_duration_label = QLabel("Ghosting visibility duration:")
        self.vis_duration_end_label = QLabel("frame")
        self.vis_duration_spinbox = QSpinBox()
        self.vis_duration_spinbox.setValue(1)
        self.vis_duration_spinbox.setMaximum(100000)

        self.vis_duration_layout.addWidget(self.vis_duration_label)
        self.vis_duration_layout.addWidget(self.vis_duration_spinbox)
        self.vis_duration_layout.addWidget(self.vis_duration_end_label)
        self.vis_duration_layout.addItem(self.horizontal_spacer)

        self.main_layout.addWidget(self.tutorial_label)
        self.main_layout.addLayout(self.bake_layout)
        self.main_layout.addLayout(self.main_ctrl_layout)
        self.main_layout.addWidget(self.faces_label)
        self.main_layout.addWidget(self.ghost_list)
        self.main_layout.addLayout(self.vis_duration_layout)
        self.main_layout.addItem(self.spacer)
    
    def bake_obj_command(self):
        obj = object_query_command()
        demo_ghosting_utils.get_ghost_object_face_ID(selected_faces=obj)
        self.ghost_list.get_obj_name((obj[0]).split(".")[0])
    
    def set_main_ctrl_text_command(self):
        """
        set end controller text
        """
        obj_name = object_query_command("single")
        if obj_name is None:
            logger.warning("Nothing is selected")
            return
        self.main_ctrl_layout.data_lineedit.setText(obj_name)


#! WIP
class BlendingWidget(QWidget):
    """
    Blending feature widget
    """
    def __init__(self, *args, **kwargs):
        super(BlendingWidget, self).__init__(*args, **kwargs)
        self.blending_main_layout = QVBoxLayout()
        self.setLayout(self.blending_main_layout)
        self.spacer = QSpacerItem(20, 150, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer = QSpacerItem(20, 40, QSizePolicy.Expanding)
        
        self.tutorial_label = QLabel("1) Choose Ghostiong geo to create Blending smear:")

        self.bake_ghost_layout = QHBoxLayout()
        self.bake_ghost_label = QLabel("Bake Ghosting geo")
        self.bake_ghost_button = QPushButton("Bake selection")
        self.bake_ghost_button.clicked.connect(self.bake_obj_command)

        self.bake_ghost_layout.addWidget(self.bake_ghost_label)
        self.bake_ghost_layout.addWidget(self.bake_ghost_button)
        self.bake_ghost_layout.addItem(self.horizontal_spacer)

        self.ghosting_geo_label = QLabel("Related Ghosting geo:")
        self.ghosting_geo_list = CustomListWidget()

        self.blending_main_layout.addWidget(self.tutorial_label)
        self.blending_main_layout.addLayout(self.bake_ghost_layout)
        self.blending_main_layout.addWidget(self.ghosting_geo_label)
        self.blending_main_layout.addWidget(self.ghosting_geo_list)
        self.blending_main_layout.addItem(self.spacer)
    
    def bake_obj_command(self):
        obj = object_query_command()
        for member in obj:
            self.ghosting_geo_list.get_obj_name(member)


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
            "More than one Autosmear frame have been created. \n Do you want to delete the latest smear frame?")
        self.buttons_layout = QHBoxLayout()
        self.open_history = QPushButton("Open History")
        self.delete_current = QPushButton("Delete Latest Smear")
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.open_history_window)

        self.open_history.clicked.connect(self.open_history_window)
        self.delete_current.clicked.connect(self.delete_latest_smear)

        self.buttons_layout.addWidget(self.open_history)
        self.buttons_layout.addWidget(self.delete_current)
        self.buttons_layout.addWidget(self.close_button)
        
        self.main_layout.addWidget(self.main_label)
        self.main_layout.addLayout(self.buttons_layout)
    
    def delete_latest_smear(self):
        clear_command(current_history_index=-1, type_smear="stretching")
        self.close()
    
    def open_history_window(self):
        clicked_button = self.sender()
        if clicked_button == self.open_history:
            show_history_window()
        self.close()
    
    def close_command(self):
        self.close()


class HistoryTableWindow(QMainWindow):
    """
    AutoSmear history tab widget
    """
    def __init__(self, *args, **kwargs):
        super(HistoryTableWindow, self).__init__(*args, **kwargs)
        self.setFixedSize(QSize(440,300))

        self.setWindowTitle("Autosmear history")

        self.history_item_dict = {"type":[], "frame":[], "main_handler":[]}

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        header = ["type", "frame", "main handler"]
        self.main_table = QTableWidget(0, len(header))
        self.main_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for index, item in enumerate(header):
            self.main_table.setHorizontalHeaderItem(index, QTableWidgetItem(item))
        self.main_table.setColumnWidth(2, 200)

        self.main_table.selectionModel().selectionChanged.connect(self.on_selectionChanged)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setMinimumHeight(30)
        self.delete_button.clicked.connect(self.delete_smear_command)

        self.main_layout.addWidget(self.main_table)
        self.main_layout.addWidget(self.delete_button)

        #----- ADD HISTORY FROM ATTR -----#
        if cmds.objExists("persp") is True:
            history_node = cmds.listAttr("persp", ud=True) or []
            for member in (history_node):
                type = ((member).split("_"))[0]
                current_data = str(cmds.getAttr("persp.{attr}".format(attr=member)))
                split_current_data = current_data.split("||")

                if type == "stretching":
                    current_name = str((ast.literal_eval(split_current_data[1]))[0])
                elif type == "ghosting":
                    current_name = str(split_current_data[1])

                current_time = str(split_current_data[0])
                self.add_history(smear_type=type, frame=current_time, main_handler=current_name)
    
    def on_selectionChanged(self, selected):
        for ix in selected.indexes():
            print("{r},{cl}".format(r=ix.row(),cl=ix.column()))
            if ix.column() == 1 or ix.column() == 2:
                cmds.currentTime(int(self.main_table.item(ix.row(), 1).item_name()))
                ctrl_member_list = (self.main_table.item(ix.row(), 2).item_name())
                cmds.select(clear=True)
                cmds.select(ctrl_member_list, add=True)

    
    def add_history(self, smear_type="", frame="", main_handler=""):
        """
        add AutoSmear data to table widget
        """
        rowPosition = self.main_table.rowCount()
        self.main_table.insertRow(rowPosition)

        type_item = HistoryTableItem(smear_type)
        frame_item = HistoryTableItem(frame)
        main_handler_item = HistoryTableItem(main_handler)

        self.main_table.setItem(rowPosition , 0, type_item)
        self.main_table.setItem(rowPosition , 1, frame_item)
        self.main_table.setItem(rowPosition , 2, main_handler_item)

        self.history_item_dict["type"].append(type_item.item_name())
        self.history_item_dict["frame"].append(frame_item.item_name())
        self.history_item_dict["main_handler"].append(main_handler_item.item_name())
    
    def test_print_result(self):
        # print(self.history_item_dict)
        # print(self.main_table.currentItem().item_name())
        # print(self.main_table.selectedItems())
        print(self.main_table.currentRow())
    
    def delete_smear_command(self):
        #! Clear smear in history window
        current_row = self.main_table.currentRow()
        smear_type = self.main_table.item(current_row, 0).item_name()
        self.main_table.removeRow(current_row)
        clear_command(current_history_index=current_row, type_smear=smear_type)

    # def message_box(self):
    #     message = QMessageBox()
    #     message.setWindowTitle("Delete Confirmation")
    #     message.setText("Do you want to delete selected Autosmear?")
    #     message.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    #     message.exec_()


class HistoryTableItem(QTableWidgetItem):
    def __init__(self, item):
        super(HistoryTableItem, self).__init__()
        self.item = item
        self.setText(self.item)
    
    def item_name(self):
        """
        function for returnnig child node

        Returns:
            str: name of child node
        """
        return(self.item)


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

def show_history_window():
	maya_ptr = omui.MQtUtil.mainWindow()
	ptr = wrapInstance(int(maya_ptr), QWidget)

	global table_window
	try:
		table_window.close()
	except:
		pass

	table_window = HistoryTableWindow(parent=ptr)
	table_window.show()

def clear_command(current_history_index=0, type_smear=""):
    attr_name = cmds.listAttr("persp", ud=True)[current_history_index]
    smear_history = "persp.{attr}".format(attr=attr_name)
    history_string_list = (cmds.getAttr(smear_history)).split("||")

    if type_smear == "stretching":
        converted_ctrl_string_list = ast.literal_eval(history_string_list[1])
        current_time = int(history_string_list[0])

        for member in converted_ctrl_string_list:
            cmds.cutKey( member, time=(current_time,current_time), option="keys", clear=True )

        cmds.setAttr(smear_history, lock=False)
        cmds.deleteAttr("persp", at=attr_name)
        cmds.delete(
            "{last_ctrl}_{timeframe}_autoSmearTool_LOC_grp".format(
                last_ctrl=converted_ctrl_string_list[-1], timeframe=str(current_time-1)))
    elif type_smear == "ghosting":
        cmds.setAttr(smear_history, lock=False)
        cmds.deleteAttr("persp", at=attr_name)
        cmds.delete(history_string_list[1])

def go_to_web():
    webbrowser.open('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

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
