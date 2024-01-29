"""
# Autosmear Tool - Python Script

# Latest Version: 1.0.0
# Release Dates
#   - 1.0.0: Jan 29, 2024
# DESCRIPTION: Tool for quick scale adjustment
# REQUIRE: Python2-Python3
# AUTHOR: BulinThira - GitHub



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

#! define maya ui pointer
maya_ptr = omui.MQtUtil.mainWindow()
ptr = wrapInstance(int(maya_ptr), QWidget)

from utils import stretching_utils
reload(stretching_utils)

from utils import ghosting_utils
reload(ghosting_utils)

from utils import blending_utils
reload(blending_utils)

class MainWidget(QMainWindow):
    """
    main widget that contains TabWidget of the 3 main features
    """
    def __init__(self, *args, **kwargs):
        super(MainWidget, self).__init__(*args, **kwargs)

        self.resize(320, 730)
        self.setWindowTitle("Autosmear Tool v.1.0.0")

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

        self.create_button = QPushButton("Create Controller Stretching")
        self.create_button.setMinimumHeight(30)
        self.delete_button = QPushButton("Delete Stretching")
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

        self.camera_space_checkbox = QCheckBox("Calculate by Camera Space")
        self.version_control_checkbox = QCheckBox("Create Version Control")

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

        self.frame_widget_3 = QWidget()

        self.frame_two = QFrame(self.frame_widget_3)
        self.frame_two.setFrameShape(QFrame.StyledPanel)
        self.frame_two.setFrameShadow(QFrame.Plain)
        self.frame_two.setLineWidth(2)

        self.label_step_4 = QLabel("4) Choose smear frame calculation:")

        self.frame_two_layout = QVBoxLayout(self.frame_two)
        self.frame_two_layout.addWidget(self.label_step_4)
        self.frame_two_layout.addWidget(self.camera_space_checkbox)
        self.frame_two.setLayout(self.frame_two_layout)

        self.frame_widget_4 = QWidget()

        self.frame_three = QFrame(self.frame_widget_4)
        self.frame_three.setFrameShape(QFrame.StyledPanel)
        self.frame_three.setFrameShadow(QFrame.Plain)
        self.frame_three.setLineWidth(2)

        self.label_step_5 = QLabel("5) Smear's version control")

        self.frame_three_layout = QVBoxLayout(self.frame_three)
        self.frame_three_layout.addWidget(self.label_step_5)
        self.frame_three_layout.addWidget(self.version_control_checkbox)
        self.frame_three.setLayout(self.frame_three_layout)

        # ----------- ADD WIDGETS TO MAIN LAYOUT ------------ #

        self.addToolBar(self.main_toolbar)
        self.main_layout.addWidget(self.feature_tab_widget)
        self.main_layout.addWidget(self.frame_zer)
        self.main_layout.addWidget(self.frame_one)
        self.main_layout.addWidget(self.frame_two)
        #self.main_layout.addWidget(self.frame_three)
        self.main_layout.addLayout(self.button_layout)

        self.setLayout(self.main_layout)
    
    def create_command(self):
        """
        Create Smear command bounded to the button
        (can be defined as main connection with Utils)

        can be switched with other main features' create command
        """
        #! Creation of Clear Smear
        if self.feature_tab_widget.currentIndex() == 0:
            stretching_utils.get_values(
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
            smear_option = self.radiobutton_selection(),
            camera_space = self.camera_space_checkbox.isChecked()
            )
        elif self.feature_tab_widget.currentIndex() == 1:
            type_selection = self.radiobutton_selection()
            auto_main_ctrl = self.ghosting_feature.main_ctrl_layout.data_lineedit.text()
            if auto_main_ctrl == "":
                logger.error("No controller has been selected for Auto-smear creation.")
                return
            ghosting_utils.get_values(
            start_frame = self.infoinput.start_frame_spinbox.value(),
            end_frame = self.infoinput.end_frame_spinbox.value(),
            main_ctrl = [auto_main_ctrl],
            interval = self.interval_spinbox.value(),
            custom_frame = self.custom_smear_spinbox.value(),
            smear_option = type_selection,
            visibility_keyframe = self.ghosting_feature.vis_duration_spinbox.value(),
            camera_space = self.camera_space_checkbox.isChecked()
            )
        # elif self.feature_tab_widget.currentIndex() == 2:
        #     ghosting_geo_name_list = []
        #     ghosting_geo_name_list = (self.blending_feature.ghosting_geo_list.return_item_list())
        #     lattice_dict = blending_utils.create_lattice_from_selected_ghost(ghosting_group=ghosting_geo_name_list,lattice_division = [4,3,3])
        #     cluster_grp_lst = blending_utils.create_clusters_on_lattice(lattice_edge_loop_dict = lattice_dict)
        #     blending_utils.snap_controllers_on_cluster(
        #    locator_group_list = cluster_grp_lst,
        #    ghosting_grp = self.blending_feature.ghosting_geo_list.return_item_list()
        #    )
        elif self.feature_tab_widget.currentIndex() == 2:
            ghosting_geo_name_list = []
            ghosting_geo_name_list = (self.blending_feature.ghosting_geo_list.return_item_list())
            blending_utils.get_stretching_value(ghosting_geo_name_list)
        else:
            print("NO TASK")
        # if table_window.isVisible() is True:
        #     #! update at the time
    
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
                self.create_button.setText("Create Controller Stretching")
            else:
                self.create_button.setText("Create Controller Stretching")
            self.delete_button.setText("Delete Stretching")
            self.current_tab_color(0)
            self.set_widget_frame_enable(True)
        elif self.feature_tab_widget.currentIndex() == 1:
            self.create_button.setText("Create Ghosting")
            self.delete_button.setText("Delete Ghosting")
            self.current_tab_color(1)
            self.set_widget_frame_enable(True)
        else:
            self.create_button.setText("Create Blending")
            self.delete_button.setText("Delete Blending")
            self.current_tab_color(2)
            self.set_widget_frame_enable(False)
    
    def set_widget_frame_enable(self, mode=True):
        self.frame_zer.setEnabled(mode)
        self.frame_one.setEnabled(mode)
        self.frame_two.setEnabled(mode)

    
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
            self.create_button.setText("Create Controller Stretching")
        else:
            self.create_button.setText("Create Attribute Stretching")
        # self.delete_button.setText("Delete Stretching")
    
    def default_connection(self):
        if self.autosmear_radiobutton.isChecked() is True:
            self.interval_spinbox.setEnabled(False)
            self.custom_smear_spinbox.setEnabled(False)
            self.set_enabled_infoinput(True)
    
    def interval_connection(self):
        if self.interval_radiobutton.isChecked() is True:
            self.interval_spinbox.setEnabled(True)
            self.interval_vis_duration_spinbox.setEnabled(True)
            self.interval_vis_duration_end_label.setEnabled(True)
            self.set_enabled_infoinput(True)
        else:
            self.interval_spinbox.setEnabled(False)
            self.interval_vis_duration_spinbox.setEnabled(False)
            self.interval_vis_duration_end_label.setEnabled(False)
    
    def custom_smear_connection(self):
        if self.custom_smear_radiobutton.isChecked() is True:
            self.custom_smear_spinbox.setEnabled(True)
            self.custom_smear_button.setEnabled(True)
            self.set_enabled_infoinput(False)
            
        else:
            self.custom_smear_spinbox.setEnabled(False)
            self.custom_smear_button.setEnabled(False)
    
    def set_enabled_infoinput(self, task=True):
        self.infoinput.start_frame_label.setEnabled(task)
        self.infoinput.start_frame_spinbox.setEnabled(task)
        self.infoinput.start_frame_select_button.setEnabled(task)
        self.infoinput.end_frame_label.setEnabled(task)
        self.infoinput.end_frame_spinbox.setEnabled(task)
        self.infoinput.end_frame_select_button.setEnabled(task)
    
    def open_history_command(self):
        # history_list = []
        # for member in cmds.listAttr("smear_history_grp", ud=True):
        #     history_list.append(member)
        # if self.history_smear is None:
        #     self.history_smear = HistoryTableWindow()
        show_history_window()
    
    def delete_command(self):
        if self.delete_button.text() == "Delete Stretching":
            stretching_main_node = find_stretching_history()
            if len(stretching_main_node) > 0:
                if len(stretching_main_node) == 1:
                        if len(stretching_main_node[list(stretching_main_node.keys())[0]]) == 1:
                            clear_command(current_history_attr=(list(stretching_main_node.values())[0])[0], type_smear="stretching")
                        else:
                            show_delete_miniwindow(smear_type="stretching")
                else:
                    show_delete_miniwindow(smear_type="stretching")
            else :
                logger.error("No Autosmear has been created.")
        elif self.delete_button.text() == "Delete Ghosting":
            autosmear_ghosting_grp = []
            referred_group = cmds.ls(assemblies=True)
            if referred_group is not None:
                if len(referred_group) > 1:
                    show_delete_miniwindow(smear_type="ghosting")
                elif len(referred_group) == 1:
                    for member in referred_group:
                        if member.startswith("Autosmear_ghostingGrp") is True:
                            autosmear_ghosting_grp.append(nodes)
                    clear_command(current_history_attr="", type_smear="ghosting", ghosting_group=autosmear_ghosting_grp[-1])
    
    def closeEvent(self, event):
        ghosting_utils.clear_face_ID_data()
        event.accept()


class StretchingWidget(QWidget):
    """
    Stretching feature sub-tab widget
    """

    signal = Signal()

    def __init__(self, *args, **kwargs):
        super(StretchingWidget, self).__init__(*args, **kwargs)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.hierawid = ChildControllerListWidget()
        self.attribute_combobox = AttributeComboBox()
        self.infoinput = InfoInput()
        self.delete_current_command = None

        self.main_toolbox = QToolBox()

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
        self.get_hierarchy_add_button.clicked.connect(self.bake_item_command)

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

        self.main_toolbox.addItem(self.hierarchy_widget, "controllers")
        self.main_toolbox.addItem(self.selected_jnt_widget, "attribute")
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
    
    def bake_item_command(self):
        obj = object_query_command()
        list_item = self.hierawid.return_item_list()
        for member in obj:
            if member not in list_item:
                self.hierawid.add_new_item(member)
            else:
                logger.warning(
                    "Objects with the same name won't be included in the baking process: {item}".format(item=member)
                    )


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
        self.end_frame_spinbox.setValue(int(cmds.playbackOptions(q=True, max = 1)))
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
        self.item_list.append(item.item_name())
    
    def return_item_list(self):
        return(self.item_list)


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
        test_stringlist = stretching_utils.get_ctrl_hierarchy(start, end)
        for nametest in test_stringlist:
                item = ChildControllerListWidgetItem(nametest)
                self.indexFromItem(item)

                self.addItem(item)
                # self.item_object_list.append(item)
                self.item_list.append(item.item_name())
    
    def clear_item(self):
        self.clear()
        self.item_list.clear()
    
    def add_new_item(self, obj_name="None"):
            item = ChildControllerListWidgetItem(obj_name)
            self.indexFromItem(item)

            self.addItem(item)
            self.item_list.append(obj_name)
    
    def delete_current_index(self):
        current_item = self.selectedItems()
        self.item_list.remove(current_item[0].item_name())
        self.takeItem(self.currentRow())
    
    def return_item_list(self):
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
        self.main_ctrl_layout= GetInputLayout(label="Referred controller:")
        self.main_ctrl_layout.data_button.clicked.connect(self.set_main_ctrl_text_command)

        self.spacer = QSpacerItem(20, 150, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer = QSpacerItem(20, 40, QSizePolicy.Expanding)

        self.tutorial_label = QLabel("1) Select faces to create Ghosting and configure duration:")

        self.bake_layout = QHBoxLayout()
        self.bake_label = QLabel("Initiate Bake Object")
        self.duplicate_obj_button = QPushButton("add")
        self.delete_obj_button = QPushButton("remove")
        self.duplicate_obj_button.clicked.connect(self.bake_obj_command)
        self.delete_obj_button.clicked.connect(self.delete_obj_command)

        self.faces_label = QLabel("Faces of:")

        self.bake_layout.addWidget(self.bake_label)
        self.bake_layout.addWidget(self.duplicate_obj_button)
        self.bake_layout.addWidget(self.delete_obj_button)
        # self.bake_layout.addItem(self.horizontal_spacer)

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
        self.main_layout.addWidget(self.faces_label)
        self.main_layout.addWidget(self.ghost_list)
        self.main_layout.addLayout(self.main_ctrl_layout)
        self.main_layout.addLayout(self.vis_duration_layout)
        self.main_layout.addItem(self.spacer)
    
    def bake_obj_command(self):
        obj = object_query_command()
        ret_obj = ghosting_utils.get_ghost_object_face_ID(selected_faces=obj)
        if ret_obj != []:
            for objs in ret_obj:
                self.ghost_list.get_obj_name(objs)
        else:
            logger.warning("All faces of selected object(s) is already baked")
    
    def delete_obj_command(self):
        current_item = self.ghost_list.selectedItems()
        current_item_name = current_item[0].item_name()
        self.ghost_list.item_list.remove(current_item_name)
        self.ghost_list.takeItem(self.ghost_list.currentRow())
        ghosting_utils.delete_geo_name_key(
            geo_name=current_item_name
            )
    
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
        self.duplicate_obj_button = QPushButton("add")
        self.delete_obj_button = QPushButton("remove")
        self.duplicate_obj_button.clicked.connect(self.bake_obj_command)
        self.delete_obj_button.clicked.connect(self.remove_obj_command)
        self.set_ctrl_button = QPushButton("Set controller")
        self.set_ctrl_button.clicked.connect(self.set_ctrl_command)

        self.bake_ghost_layout.addWidget(self.bake_ghost_label)
        self.bake_ghost_layout.addWidget(self.duplicate_obj_button)
        self.bake_ghost_layout.addWidget(self.delete_obj_button)
        # self.bake_ghost_layout.addItem(self.horizontal_spacer)

        self.ghosting_geo_label = QLabel("Related Ghosting geo:")
        self.ghosting_geo_list = CustomListWidget()

        self.blending_main_layout.addWidget(self.tutorial_label)
        self.blending_main_layout.addLayout(self.bake_ghost_layout)
        self.blending_main_layout.addWidget(self.ghosting_geo_label)
        self.blending_main_layout.addWidget(self.ghosting_geo_list)
        self.blending_main_layout.addWidget(self.set_ctrl_button)
        self.blending_main_layout.addItem(self.spacer)
    
    def bake_obj_command(self):
        obj = object_query_command()
        list_item = self.ghosting_geo_list.return_item_list()
        for member in obj:
            if member not in list_item:
                self.ghosting_geo_list.get_obj_name(member)
            else:
                logger.warning(
                    "Objects with the same name won't be included in the baking process: {item}".format(item=member)
                    )
    
    def set_ctrl_command(self):
        ghosting_geo_name_list = []
        ghosting_geo_name_list = (self.ghosting_geo_list.return_item_list())
        if len(ghosting_geo_name_list) < 1:
            logger.error("There is no object to set controller.")
            return
        lattice_dict = blending_utils.create_lattice_from_selected_ghost(ghosting_group=ghosting_geo_name_list,lattice_division=[4,2,2])
        cluster_grp_lst = blending_utils.create_clusters_on_lattice(lattice_edge_loop_dict = lattice_dict)
        blending_utils.snap_controllers_on_cluster(locator_group_list = cluster_grp_lst ,ghosting_grp = ghosting_geo_name_list)
    
    def remove_obj_command(self):
        current_item = self.ghosting_geo_list.selectedItems()
        current_item_name = current_item[0].item_name()
        self.ghosting_geo_list.item_list.remove(current_item_name)
        self.ghosting_geo_list.takeItem(self.ghosting_geo_list.currentRow())


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
        if ui.delete_button.text() == "Delete Stretching":
            stretching_main_node = find_stretching_history()
            print(((list(stretching_main_node.values()))[0])[-1])
            clear_command(current_history_attr=((list(stretching_main_node.values()))[0])[-1], type_smear="stretching", latest=True)
        elif ui.delete_button.text() == "Delete Ghosting":
            autosmear_ghosting_grp = []
            referred_group = cmds.ls(assemblies=True)
            for member in referred_group:
                if member.startswith("Autosmear_ghostingGrp") is True:
                    autosmear_ghosting_grp.append(member)
            clear_command(current_history_attr="", type_smear="ghosting", ghosting_grp=autosmear_ghosting_grp[-1])
        self.close()
    
    def open_history_window(self):
        clicked_button = self.sender()
        if clicked_button == self.open_history:
            show_history_window()
        self.close()


class HistoryTableWindow(QMainWindow):
    """
    AutoSmear history tab widget
    """
    def __init__(self, *args, **kwargs):
        super(HistoryTableWindow, self).__init__(*args, **kwargs)
        self.setMinimumSize(QSize(550,380))

        self.setWindowTitle("Autosmear history")

        self.edit_ghosting = EditGhostingWidget()

        self.history_item_dict = {"feature":[], "type":[], "frame":[], "main_handler":[]}

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        header = ["feature", "type", "frame", "main handler"]
        self.main_table = QTableWidget(0, len(header))
        self.main_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for index, item in enumerate(header):
            self.main_table.setHorizontalHeaderItem(index, QTableWidgetItem(item))
        self.main_table.setColumnWidth(3, 200)

        self.main_table.selectionModel().selectionChanged.connect(self.on_selectionChanged)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setMinimumHeight(30)
        self.delete_button.clicked.connect(self.delete_smear_command)

        self.main_layout.addWidget(self.main_table)
        self.main_layout.addWidget(self.delete_button)

        #----- ADD HISTORY FROM ATTR -----#
        #! 1) add stretching history
        stretching_main_node = find_stretching_history()
        for key in (stretching_main_node):
            for value in stretching_main_node[key]:
                type = ((value).split("_"))[0]
                current_data = str(cmds.getAttr("{node}.{attr}".format(node=key,attr=value)))
                split_current_data = current_data.split("||")

                if type == "stretching":
                    type = value
                    if str(split_current_data[2]).startswith("["):
                        current_name = str((ast.literal_eval(split_current_data[2]))[0])
                    else:
                        current_name = str(split_current_data[2])
                elif type == "ghosting":
                    current_name = str(split_current_data[2])

                current_subtype = str(split_current_data[1])
                current_time = str(split_current_data[0])
                self.add_history(smear_type=type, smear_subtype=current_subtype, frame=current_time, main_handler=current_name)

        #! 2) add ghosting history + blending history
        autosmear_ghosting_grp = []
        top_node = cmds.ls(assemblies=True)
        for nodes in top_node:
            if nodes.startswith("Autosmear_ghostingGrp") is True:
                autosmear_ghosting_grp.append(nodes)
        for members in autosmear_ghosting_grp:
            list_attr = cmds.listAttr(members, ud=True)
            len_list = len(list_attr)
            # ghosting history
            current_data = str(cmds.getAttr("{name}.ghosting_history".format(name=members)))
            split_current_data = current_data.split("||")
            current_subtype = str(split_current_data[1])
            current_name = str(split_current_data[2])
            current_time = str(split_current_data[0])
            self.add_history(smear_type="ghosting", smear_subtype=current_subtype, frame=current_time, main_handler=current_name)
            # blending history check
            if len_list > 1:
                for ind in range(1,len_list):
                    current_data = str(cmds.getAttr("{name}.blending_s{num}".format(name=members, num=ind)))
                    split_current_data = current_data.split("||")
                    current_name = str(split_current_data[1])
                    current_time = str(split_current_data[0])
                    self.add_history(smear_type="blending", smear_subtype="-", frame=current_time, main_handler=current_name)


    def on_selectionChanged(self, selected):
        #todo Check if it's interval, then create commmand to drop down menu for user to choose the frame (should be +1 to see)
        for ix in selected.indexes():
            print("{r},{cl}".format(r=ix.row(),cl=ix.column()))
            if self.main_table.item(ix.row(), 1).item_name() == "B":
                ctrl_member_list = (self.main_table.item(ix.row(), 3).item_name())
                cmds.select(ctrl_member_list, replace=True)
                if ix.column() == 2:
                    interval_frames_list = ast.literal_eval(self.main_table.item(ix.row(), 2).item_name())
                    self.ghosting_bystep_menu = GhostingByStepMenu(
                        item_list = interval_frames_list
                    )
                    self.ghosting_bystep_menu.popup(QCursor.pos())
                    self.ghosting_bystep_menu.triggered.connect(
                        lambda: self.set_interval(
                            row_num=ix.row(),
                            current_frame=self.ghosting_bystep_menu.set_action(),
                            frame_list = interval_frames_list
                            )
                    )
            else:
                cmds.currentTime(int(self.main_table.item(ix.row(), 2).item_name()))
                ctrl_member_list = (self.main_table.item(ix.row(), 3).item_name())
                cmds.select(clear=True)
                cmds.select(ctrl_member_list, replace=True)
    
    def set_interval(self, row_num=0, current_frame=0, frame_list=[]):
        number = "0"
        default_name = self.main_table.item(row_num, 2).text()
        split_default_name = default_name.split(" --> ")[0]
        self.main_table.item(row_num, 2).setText(
            "{default} --> {current}".format(default=split_default_name, current=str(current_frame)))
        for ind, item in enumerate(frame_list):
            if str(current_frame) == str(item):
                number = str(ind-1)
                break
        self.main_table.clearSelection()
        number_padding = number.zfill(3)
        main_group = self.main_table.item(row_num, 3).item_name()
        #todo check after utils re-engineer
        # cmds.select("|{main_grp}|Ghosting_SubGrp_{padding}".format(main_grp=main_group,padding=number_padding.zfill(3)),
        #     replace = True,
        #     hierarchy = True
        # )
        cmds.currentTime(current_frame)
    
    def add_history(self, smear_type="", smear_subtype="", frame="", main_handler=""):
        """
        add AutoSmear data to table widget
        """
        rowPosition = self.main_table.rowCount()
        self.main_table.insertRow(rowPosition)

        type_item = HistoryTableItem(smear_type)
        subtype_item = HistoryTableItem(smear_subtype)
        frame_item = HistoryTableItem(frame)
        main_handler_item = HistoryTableItem(main_handler)

        self.main_table.setItem(rowPosition , 0, type_item)
        self.main_table.setItem(rowPosition , 1, subtype_item)
        self.main_table.setItem(rowPosition , 2, frame_item)
        self.main_table.setItem(rowPosition , 3, main_handler_item)

        self.history_item_dict["feature"].append(type_item.item_name())
        self.history_item_dict["type"].append(subtype_item.item_name())
        self.history_item_dict["frame"].append(frame_item.item_name())
        self.history_item_dict["main_handler"].append(main_handler_item.item_name())

        #! set display for By-step Ghosting
        # if smear_type == "ghosting" and smear_subtype == "B"
    
    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        edit_action = QAction('Edit', self)
        edit_action.triggered.connect(lambda: self.open_edit_ghosting(self.main_table.item((self.main_table.currentRow()), 3).text()))
        self.menu.addAction(edit_action)
        if len(self.main_table.selectedItems()) == 1 and self.main_table.item(self.main_table.currentItem().row(), 0).text() == "ghosting":
            self.menu.popup(QCursor.pos())
    
    def open_edit_ghosting(self, main_grp=""):
        self.edit_ghosting.bake_main_grp(main_grp)
        self.edit_ghosting.show()

    # def edit_slot(self, event):
    #     print "renaming slot called"
    #     row = self.tableWidget.rowAt(event.pos().y())
    #     col = self.tableWidget.columnAt(event.pos().x())
    #     cell = self.tableWidget.item(row, col)
    #     cellText = cell.text()
    #     widget = self.tableWidget.cellWidget(row, col)
    
    def delete_smear_command(self):
        #! Clear smear in history window
        if self.main_table.rowCount() > 0:
            current_row = self.main_table.currentRow()
            smear_type = self.main_table.item(current_row, 0).display_item_name()
            smear_attr = self.main_table.item(current_row, 0).item_name()
            ghost_type_grp = self.main_table.item(current_row, 3).item_name()
            self.main_table.removeRow(current_row)
            clear_command(
                current_history_attr=smear_attr,
                type_smear=smear_type,
                ghosting_grp=ghost_type_grp)
        else:
            logger.error("There is no smear history to delete.")

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
        self.display_item = item
        
        # check feature
        if (self.item).startswith("stretching"):
            self.display_item = "stretching"

        # check sub-type
        if self.item == "A":
            self.display_item = "Autosmear"
        elif self.item == "B":
            self.display_item = "By-step"
        elif self.item == "C":
            self.display_item = "Custom"

        if (self.item).startswith("["):
            item_list = ast.literal_eval(item)
            self.display_item = "{start_int}-{end_int} --> ".format(
                start_int=item_list[0],end_int=item_list[-1])
        self.setText(self.display_item)
    
    def item_name(self):
        """
        function for returnnig child node

        Returns:
            str: name of child node
        """
        return(self.item)
    
    def display_item_name(self):
        """
        function for returnnig child node's display name

        Returns:
            str: display name of child node
        """
        return(self.display_item)


class GhostingByStepMenu(QMenu):
    def __init__(self, item_list):
        super(GhostingByStepMenu, self).__init__()
        self.item_list = item_list
        self.return_action_name = "default"
        for index, each in enumerate(self.item_list):
            self.addAction(str(each), self.set_action)

    def set_action(self):
        action = self.sender()
        return(action.text())


class EditGhostingWidget(QDialog):
    def __init__(self, parent=ptr):
        super(EditGhostingWidget, self).__init__(parent)
        self.setFixedSize(QSize(280,100))
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.setWindowTitle("Edit Ghosting")

        self.horizontal_layout = QHBoxLayout()
        self.button_layout = QHBoxLayout()
        self.label = QLabel("Ghosting visibility duration:")
        self.end_label = QLabel("frame")
        self.spinbox = QDoubleSpinBox()
        self.horizontal_layout_above = QHBoxLayout()
        self.maingroup_label = QLabel("Children of:")
        self.maingroup_lineedit = QLineEdit()
        self.maingroup_lineedit.setEnabled(False)
        self.maingroup_button = QPushButton("Select")
        #todo set value of the spinbox as current duration
        self.spinbox.setValue(1.0)
        self.spinbox.setMaximum(100000.0)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(lambda: self.edit_vis_duration_command(new_frame=self.spinbox.value()))
        self.cancel_button = QPushButton("Cancel")

        self.horizontal_layout_above.addWidget(self.maingroup_label)
        self.horizontal_layout_above.addWidget(self.maingroup_lineedit)

        self.horizontal_layout.addWidget(self.label)
        self.horizontal_layout.addWidget(self.spinbox)
        self.horizontal_layout.addWidget(self.end_label)

        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)

        self.main_layout.addLayout(self.horizontal_layout_above)
        self.main_layout.addLayout(self.horizontal_layout)
        self.main_layout.addLayout(self.button_layout)
    
    def edit_vis_duration_command(self, new_frame=0.0):
        main_grp = self.maingroup_lineedit.text()
        main_children = cmds.listRelatives(main_grp, children=True)
        for node in main_children:
            keylist = cmds.keyframe(node, q=True)
            cmds.currentTime(keylist[-1])
            cmds.cutKey(node,
                        attribute='visibility', time=(keylist[-1], keylist[-1]), clear=True)
            new_keyframe = keylist[-2]+new_frame
            cmds.currentTime(new_keyframe)
            cmds.setKeyframe(node,
                        attribute='visibility', time=new_keyframe, value=0)
    
    def bake_main_grp(self, main_grp=""):
        self.maingroup_lineedit.setText(main_grp)


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

def show_delete_miniwindow(smear_type=""):
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

def clear_command(current_history_attr="", type_smear="", ghosting_grp="", latest=False):
    if type_smear == "stretching":
        stretching_main_node = find_stretching_history()
        for key in (stretching_main_node):
            for value in stretching_main_node[key]:
                # print("key --> ", key, "value --> ", value)
                # print("current_history_attr --> ", current_history_attr)
                if value == current_history_attr:
                    if latest:
                        if key != list(stretching_main_node.keys())[-1]:
                            continue
                    smear_history = "{node}.{attr}".format(node=key,attr=value)
                    history_string_list = (cmds.getAttr(smear_history)).split("||")
                    converted_ctrl_string_list = ast.literal_eval(history_string_list[-1])
                    current_time = int(history_string_list[0])

                    for member in converted_ctrl_string_list:
                        cmds.cutKey( member, time=(current_time,current_time), option="keys", clear=True )

                    cmds.setAttr(smear_history, lock=False)
                    cmds.deleteAttr(key, at=value)
                    cmds.delete(
                        "{last_ctrl}_{timeframe}_autoSmearTool_LOC_grp".format(
                            last_ctrl=converted_ctrl_string_list[-1], timeframe=str(current_time-1)))
    elif type_smear == "ghosting":
        cmds.delete(ghosting_grp)
    elif type_smear == "blending":
        cmds.delete(ghosting_grp)


def find_stretching_history():
    """
    Return:
        (dict): 
    """
    top_node_grp = cmds.ls(assemblies=True)
    use_node = []
    grp_with_history = {}
    for node in top_node_grp:
        ud_attr = cmds.listAttr(node, ud=True)
        if ud_attr is None:
            continue
        else:
            ud_attr_list = []
            for attr in ud_attr:
                if attr.startswith("stretching"):
                    ud_attr_list.append(attr)
            grp_with_history[node] = ud_attr_list
    return(grp_with_history)

def go_to_web():
    webbrowser.open('https://youtu.be/Yllz-8T4-h4')

def run():
    # ghosting_utils.test_print()
	maya_ptr = omui.MQtUtil.mainWindow()
	ptr = wrapInstance(int(maya_ptr), QWidget)

	global ui
	try:
		ui.close()
	except:
		pass

	ui = MainWidget(parent=ptr)
	ui.show()
