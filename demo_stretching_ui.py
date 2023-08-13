"""
#run this script in Maya Script Editor after putting the .py file in the maya scripts folder

import importlib
import demo_stretch_ui
importlib.reload(demo_stretch_ui)
demo_stretch_ui.run()
"""

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.cmds as cmds

class DemoStrechWidget(QDialog):
    def __init__(self, *args, **kwargs):
        super(DemoStrechWidget, self).__init__(*args, **kwargs)

        self.resize(330, 420)
        self.setWindowTitle("Demo Streaching Smear Tool")

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # ----------- CREATE SPACER ------------ #
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontal_spacer = QSpacerItem(20, 40, QSizePolicy.Expanding)

        # ----------- JOINT SELECTION WIDGET ------------ #
        self.selected_jnt_widget = QWidget()
        self.selected_jnt_layout = QHBoxLayout()
        self.selected_jnt_widget.setLayout(self.selected_jnt_layout)

        self.selected_jnt_label = QLabel("Selected main joint controller:")
        self.selected_jnt_lineEdit = QLineEdit()
        ##self.selected_jnt_lineEdit.setPlaceholderText("input joint selected_jnt...")
        self.selected_jnt_button = QPushButton("get")

        self.selected_jnt_layout.addWidget(self.selected_jnt_label)
        ##self.selected_jnt_layout.addWidget(self.selected_jnt_lineEdit)
        self.selected_jnt_layout.addWidget(self.selected_jnt_button)

        # ----------- START FRAME WIDGET ------------ #
        self.start_frame_widget = QWidget()
        self.start_frame_layout = QHBoxLayout()
        self.start_frame_widget.setLayout(self.start_frame_layout)

        self.start_frame_label = QLabel("Start Frame:")
        self.start_frame_lineEdit = QSpinBox()
        ##self.selected_jnt_lineEdit.setPlaceholderText("input joint selected_jnt...")

        self.start_frame_layout.addWidget(self.start_frame_label)
        self.start_frame_layout.addWidget(self.start_frame_lineEdit)
        self.start_frame_layout.addItem(self.horizontal_spacer)

        # ----------- END FRAME WIDGET ------------ #
        self.end_frame_widget = QWidget()
        self.end_frame_layout = QHBoxLayout()
        self.end_frame_widget.setLayout(self.end_frame_layout)

        self.end_frame_label = QLabel("End Frame:")
        self.end_frame_lineEdit = QSpinBox()
        ##self.selected_jnt_lineEdit.setPlaceholderText("input joint selected_jnt...")

        self.end_frame_layout.addWidget(self.end_frame_label)
        self.end_frame_layout.addWidget(self.end_frame_lineEdit)
        self.end_frame_layout.addItem(self.horizontal_spacer)

        # ----------- RADIOBUTTONS WIDGET ------------ #
        self.acceleration_radiobutton_widget = QWidget()
        self.acceleration_radiobutton_layout = QVBoxLayout()
        self.acceleration_radiobutton_widget.setLayout(self.acceleration_radiobutton_layout)

        self.child_controller_radiobutton = QRadioButton("Based on child-controller: (in progress..)")
        self.child_controller_radiobutton.setChecked(True)
        self.attribute_radiobutton = QRadioButton("Based on attribute:")
        self.attribute_lineedit = QLineEdit()
        self.attribute_lineedit.setEnabled(False)
        self.attribute_radiobutton.toggled.connect(self.attribute_lineedit.setEnabled)

        self.acceleration_radiobutton_layout.addWidget(self.child_controller_radiobutton)
        self.acceleration_radiobutton_layout.addWidget(self.attribute_radiobutton)
        self.acceleration_radiobutton_layout.addWidget(self.attribute_lineedit)

        # ----------- CREATE MAIN BUTTON ------------ #
        self.create_button = QPushButton("Create Smear")
        self.create_button.setMinimumHeight(30)
        ##self.create_button.clicked.connect(self.doCreate)

        self.main_layout.addWidget(self.selected_jnt_widget)
        self.main_layout.addWidget(self.selected_jnt_lineEdit)
        self.main_layout.addWidget(self.start_frame_widget)
        self.main_layout.addWidget(self.end_frame_widget)
        self.main_layout.addWidget(self.acceleration_radiobutton_widget)
        self.main_layout.addItem(self.spacer)
        self.main_layout.addWidget(self.create_button)

def run():
	maya_ptr = omui.MQtUtil.mainWindow()
	ptr = wrapInstance(int(maya_ptr), QWidget)

	global ui
	try:
		ui.close()
	except:
		pass

	ui = DemoStrechWidget(parent=ptr)
	ui.show()
