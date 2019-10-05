#!/usr/bin/env python3

from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from dali.driver import hasseb

# Create hasseb USB DALI driver instance to handle messages
DALI_device = hasseb.AsyncHassebDALIUSBDriver()

# DALI devices found from the bus
DALI_gear = None

class DALIThread(QRunnable):
    '''
    DALI messages are handled  here in a separate thread
    '''

    def __init__(self, fn, *args):
        super(DALIThread, self).__init__()
        self.fn = fn
        self.args = args

    @pyqtSlot()
    def run(self):
        while 1:
            data = DALI_device.receive()
            if data is not None:
                self.fn(0, data)
            data = DALI_device.send_message
            if data is not None:
                self.fn(1, data)
                DALI_device.send_message = None
            data = DALI_device.ballast_id
            if data is not None:
                self.fn(2, data)
                DALI_device.ballast_id = None

class mainWindow(QMainWindow):
    def __init__(self):
        super(mainWindow, self).__init__()
        self.title = 'DALI Controller'
        self.left = 50
        self.top = 50
        self.width = 500
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

        self.threadpool = QThreadPool()
        self.DALIThread = DALIThread(self.tabs_widget.writeDALILog)
        self.threadpool.start(self.DALIThread)

class tabsWidget(QWidget):

    ShortAddress, ID, DeviceType = range(3)

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

        # Tab 1
        # Layouts
        self.tab1.layout = QHBoxLayout(self.tab1)
        self.tab1.layout_treeview = QHBoxLayout()
        self.tab1.layout_controls = QHBoxLayout()

        # Widgets and actions
        self.tab1.treeview = QTreeView()
        self.model = QtGui.QStandardItemModel(0, 3)
        self.model.setHeaderData(self.ID, Qt.Horizontal, "ID")
        self.model.setHeaderData(self.ShortAddress, Qt.Horizontal, "Short address")
        self.model.setHeaderData(self.DeviceType, Qt.Horizontal, "Device type")
        self.tab1.treeview.setModel(self.model)
        self.tab1.initializeButton = QPushButton('Initialize')
        self.tab1.initializeButton.clicked.connect(self.initializeButtonClick)

        # Add widgets to layouts
        self.tab1.layout_treeview.addWidget(self.tab1.treeview)
        self.tab1.layout_controls.addWidget(self.tab1.initializeButton)
        self.tab1.layout_treeview.setAlignment(Qt.AlignTop)
        self.tab1.layout_controls.setAlignment(Qt.AlignTop)
        self.tab1.layout.addLayout(self.tab1.layout_controls)
        self.tab1.layout.addLayout(self.tab1.layout_treeview)
        self.tab1.layout.setAlignment(Qt.AlignTop)
        self.tab1.setLayout(self.tab1.layout)

        # Tab 2
        # Widgets
        self.tab2.layout = QHBoxLayout(self.tab2)
        self.tab2.log_textarea = QPlainTextEdit(self)
        
        # Add widgets to layout
        self.tab2.layout.addWidget(self.tab2.log_textarea)
        self.tab2.setLayout(self.tab2.layout)

        # Add tabs to the widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def writeDALILog(self, direction, data):
        if direction == 0:
            text = '|| DALI -> PC |'
            for i in data:
                text += '| ' + "0x{:02x}".format(i) + ' '
            text += '|| ' + f"{DALI_device.extract(data)}" + ' ||'
        elif direction  == 1:
            text = '|| PC -> DALI |'
            for i in data:
                text += '| ' + "0x{:02x}".format(i) + ' '
            text += '|| ' + f"{data}" + ' ||'
        elif direction == 2:
            self.model.insertRow(0)
            self.model.setData(self.model.index(0, self.ID), DALI_device.ballast_id)
            self.model.setData(self.model.index(0, self.ShortAddress), f"{DALI_device.ballast_short_address}")
            self.model.setData(self.model.index(0, self.DeviceType), f"{DALI_device.ballast_type}")
            text = f"{DALI_device.ballast_id} | {DALI_device.ballast_short_address} | {DALI_device.ballast_type}"

        #self.tab2.log_textarea. appendPlainText(f"{text}")
        #self.tab2.log_textarea.moveCursor(QtGui.QTextCursor.End)
        print(text)

    # Click actions
    @pyqtSlot()
    def initializeButtonClick(self):
        DALI_device.find_ballasts()
