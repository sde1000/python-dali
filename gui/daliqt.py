#!/usr/bin/env python3

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import usb.core

from dali.driver import hasseb

# Find hasseb USB DALI Master from all USB devices
DALI_device = None
dev = usb.core.find(find_all=True)
for cfg in dev:   
    if cfg.idVendor == 0x04cc and cfg.idProduct == 0x0802:
        DALI_device = hasseb.AsyncHassebDALIUSBDriver()

class mainWindow(QMainWindow):
    def __init__(self):
        super(mainWindow, self).__init__()
        self.title = 'DALI Controller'
        self.left = 50
        self.top = 50
        self.width = 700
        self.height = 500
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        if DALI_device != None:
            self.statusBar().showMessage('hasseb USB DALI Master device found.')
        else:
            self.label = QLabel(self)
            self.label.setText('<span style="color:red">No USB DALI master device found. Please connect the device and restart the program.</span>')
            self.statusBar().addPermanentWidget(self.label)

        self.tabs_widget = tabsWidget(self)
        self.setCentralWidget(self.tabs_widget)

        self.show()

class tabsWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QHBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()

        # Add tabs
        self.tabs.addTab(self.tab1,"Devices")
        self.tabs.addTab(self.tab2,"Log")

        # Create first tab
        # Layouts
        self.tab1.layout = QHBoxLayout(self.tab1)
        self.tab1.layout_listbox = QHBoxLayout()
        self.tab1.layout_controls = QHBoxLayout()

        # Widgets and actions
        self.tab1.listwidget = QListWidget()
        self.tab1.initializeButton = QPushButton('Initialize')
        self.tab1.initializeButton.clicked.connect(self.initializeButtonClick)

        # Add widgets to layouts
        self.tab1.layout_listbox.addWidget(self.tab1.listwidget)
        self.tab1.layout_controls.addWidget(self.tab1.initializeButton)
        self.tab1.layout_listbox.setAlignment(Qt.AlignTop)
        self.tab1.layout_controls.setAlignment(Qt.AlignTop)
        self.tab1.layout.addLayout(self.tab1.layout_controls)
        self.tab1.layout.addLayout(self.tab1.layout_listbox)
        self.tab1.layout.setAlignment(Qt.AlignTop)
        self.tab1.setLayout(self.tab1.layout)

        # Add tabs to the widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    # Click actions
    @pyqtSlot()
    def initializeButtonClick(self):
        colours = ['Red', 'Green', 'Blue', 'Yellow']
        self.tab1.listwidget.clear()
        i = 0
        for x in colours:
            self.tab1.listwidget.insertItem(i, x)
            i = i+1
