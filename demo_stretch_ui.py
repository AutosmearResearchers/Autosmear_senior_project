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

        self.resize(310, 420)
        self.setWindowTitle("Demo Streaching Smear Tool")

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # ----------- JOINT SELECTION WIDGET ------------ #
        self.selected_jnt_widget = QWidget()
        self.selected_jnt_layout = QHBoxLayout()
        self.selected_jnt_widget.setLayout(self.selected_jnt_layout)

        self.selected_jnt_label = QLabel("Selected joint:")
        self.selected_jnt_lineEdit = QLineEdit()
        ##self.selected_jnt_lineEdit.setPlaceholderText("input joint selected_jnt...")
        self.selected_jnt_button = QPushButton("get")

        self.selected_jnt_layout.addWidget(self.selected_jnt_label)
        self.selected_jnt_layout.addWidget(self.selected_jnt_lineEdit)
        self.selected_jnt_layout.addWidget(self.selected_jnt_button)

        # ----------- RADIOBUTTONS WIDGET ------------ #
        self.acceleration_radiobutton_widget = QWidget()
        self.acceleration_radiobutton_layout = QVBoxLayout()
        self.acceleration_radiobutton_widget.setLayout(self.acceleration_radiobutton_layout)

        self.auto_acceleration_radiobutton = QRadioButton("Auto-detected acceleration")
        self.auto_acceleration_radiobutton.setChecked(True)
        self.define_acceleration_radiobutton = QRadioButton("Self-defined acceleration")
        self.define_acceleration_lineedit = QLineEdit()
        self.define_acceleration_lineedit.setEnabled(False)
        self.define_acceleration_radiobutton.toggled.connect(self.define_acceleration_lineedit.setEnabled)

        self.acceleration_radiobutton_layout.addWidget(self.auto_acceleration_radiobutton)
        self.acceleration_radiobutton_layout.addWidget(self.define_acceleration_radiobutton)
        self.acceleration_radiobutton_layout.addWidget(self.define_acceleration_lineedit)

        # ----------- INTERVAL PERCENTAGE WIDGET ------------ #
        self.interval_percent_widget = QWidget()
        self.interval_percent_layout = QHBoxLayout()
        self.interval_percent_widget.setLayout(self.interval_percent_layout)

        self.interval_percent_label = QLabel("Interval percentage:")
        self.interval_percent_lineEdit = QLineEdit()

        self.interval_percent_layout.addWidget(self.interval_percent_label)
        self.interval_percent_layout.addWidget(self.interval_percent_lineEdit)

        # ----------- CREATE MAIN BUTTON ------------ #
        self.create_button = QPushButton("Create Smear")
        self.create_button.setMinimumHeight(30)
        ##self.create_button.clicked.connect(self.doCreate)

        # ----------- CREATE SPACER ------------ #
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.main_layout.addWidget(self.selected_jnt_widget)
        self.main_layout.addWidget(self.interval_percent_widget)
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
