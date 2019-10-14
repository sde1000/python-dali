#!/usr/bin/env python3

from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from dali.driver import hasseb
from dali import bus
import DALICommands

# Create hasseb USB DALI driver instance to handle messages
DALI_device = hasseb.HassebDALIUSBDriver()
# Create DALI bus
DALI_bus = bus.Bus('hasseb DALI bus',   DALI_device)
# Instance to send individual DALI commands
DALI_command_sender = DALICommands.DALICommandSender()

# Circular buffer for received DALI messages
DALI_BUFFER_LENGTH = 8
dali_rec_buffer = [0 for i in range(DALI_BUFFER_LENGTH)]
dali_message_received = [float('inf') for i in range(DALI_BUFFER_LENGTH)]
dali_message_type = [None for i in range(DALI_BUFFER_LENGTH)]
dali_rec_buffer_write_idx = 0
MESSAGE_TYPE_DALI_PC = 0
MESSAGE_TYPE_PC_DALI = 1
MESSAGE_TYPE_BALLAST_FOUND = 2

class DALIThread(QRunnable):
    '''
    DALI messages are handled  here in a separate thread
    '''

    def __init__(self, signal):
        super(DALIThread, self).__init__()
        self.signal = signal
        self.message_number = 0

    @pyqtSlot()
    def run(self):
        global dali_rec_buffer
        global dali_message_type
        global dali_message_received
        global dali_rec_buffer_write_idx
        while 1:
            data = DALI_device.receive()
            if data is not None:
                dali_rec_buffer[dali_rec_buffer_write_idx] = data
                dali_message_type[dali_rec_buffer_write_idx] = MESSAGE_TYPE_DALI_PC
                self.message_number += 1
                dali_message_received[dali_rec_buffer_write_idx] = self.message_number
                if dali_rec_buffer_write_idx < DALI_BUFFER_LENGTH-1:
                    dali_rec_buffer_write_idx += 1
                else:
                    dali_rec_buffer_write_idx = 0
                self.signal.emit()
            data = DALI_device.send_message
            if data is not None:
                dali_rec_buffer[dali_rec_buffer_write_idx] = data
                dali_message_type[dali_rec_buffer_write_idx] = MESSAGE_TYPE_PC_DALI
                self.message_number += 1
                dali_message_received[dali_rec_buffer_write_idx] = self.message_number
                if dali_rec_buffer_write_idx < DALI_BUFFER_LENGTH-1:
                    dali_rec_buffer_write_idx += 1
                else:
                    dali_rec_buffer_write_idx = 0
                self.signal.emit()
                DALI_device.send_message = None
            #data = DALI_device.ballast_id
            #if data is not None:
                #self.fn(2, data)
                #self.signal.emit()
                #DALI_device.ballast_id = None

class mainWindow(QMainWindow):
    # Signal updating DALI message log received in different thread
    updateLog = pyqtSignal()

    def __init__(self, app):
        super(mainWindow, self).__init__()
        self.title = 'DALI Controller'
        screen_resolution = app.desktop().screenGeometry()
        self.width, self.height = screen_resolution.width()/3, screen_resolution.height()/2
        self.left = screen_resolution.width()/2-self.width/2
        self.top = screen_resolution.height()/2-self.height/2
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.tabs_widget = tabsWidget(self)
        self.setCentralWidget(self.tabs_widget)

        if DALI_device.device_found != None:
            self.statusBar().showMessage(f"hasseb USB DALI Master device with firmware version {DALI_device.readFirmwareVersion()} found.")
            self.updateLog.connect(self.tabs_widget.writeDALILog)
            self.threadpool = QThreadPool()
            self.DALIThread = DALIThread(self.updateLog)
            self.threadpool.start(self.DALIThread)
        else:
            self.label = QLabel(self)
            self.label.setText('<span style="color:red">No USB DALI master device found. Please check the connection and restart program.</span>')
            self.statusBar().addPermanentWidget(self.label)

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
        self.tabs.addTab(self.tab1, "Devices")
        self.tabs.addTab(self.tab2, "Log")

        # Tab 1
        # Layouts
        self.tab1.layout = QHBoxLayout(self.tab1)
        self.tab1.layout_treeview = QVBoxLayout()
        self.tab1.layout_controls = QVBoxLayout()
        self.tab1.layout_sendCommands = QVBoxLayout()
        self.tab1.layout_sendCommandsMiddle = QHBoxLayout()
        self.tab1.layout_sendCommandsMiddleLeft = QHBoxLayout()
        self.tab1.layout_sendCommandsMiddleRight = QHBoxLayout()
        self.tab1.layout_sendCommandsBottom = QHBoxLayout()
        self.tab1.layout_sendCommandsBottomLeft = QHBoxLayout()
        self.tab1.layout_sendCommandsBottomRight = QHBoxLayout()

        # Widgets and actions
        # Tree view
        self.tab1.treeWidget = QTreeWidget(self)
        self.tab1.treeWidget.setColumnCount(4)
        self.tab1.treeWidget.setHeaderLabels(["Short address", "Random address", "Group", "Device type"])
        for i in range(4):
            self.tab1.treeWidget.resizeColumnToContents(i)
        print('hello')
        self.tab1.treeWidget.currentItemChanged.connect(self.updateCommand)
        self.tab1.treeWidget.itemClicked.connect(self.updateCommand)

        # Send commands group box
        self.tab1.sendCommandGroupBox = QGroupBox('Send commands')
        self.tab1.commandsComboBox = QComboBox()
        self.tab1.commandsComboBox.addItems(DALICommands.commands)
        self.tab1.commandsComboBox.activated[str].connect(self.updateCommand)
        self.tab1.commandsByte1Label = QLabel('Byte 1:')
        self.tab1.commandsByte1Label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tab1.commandsByte1 = QSpinBox()
        self.tab1.commandsByte1.setRange(0, 255)
        self.tab1.commandsByte1.setFixedWidth(80)
        self.tab1.commandsByte2Label = QLabel('Byte 2:')
        self.tab1.commandsByte2Label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tab1.commandsByte2 = QSpinBox()
        self.tab1.commandsByte2.setRange(0, 255)
        self.tab1.commandsByte2.setFixedWidth(80)
        self.tab1.commandsResponseLabel = QLabel("Response:")
        self.tab1.commandsResponseLabel.setFixedWidth(120)
        self.tab1.commandsResponse = QLineEdit()
        self.tab1.commandsResponse.setFixedWidth(100)
        self.tab1.sendButton = QPushButton('Send')
        self.tab1.sendButton.clicked.connect(self.sendButtonClick)
        # Buttons
        self.tab1.initializeButton = QPushButton('Initialize')
        self.tab1.initializeButton.clicked.connect(self.initializeButtonClick)
        self.tab1.scanButton = QPushButton('Scan bus')
        self.tab1.scanButton.clicked.connect(self.scanButtonClick)

        # Add widgets to layouts
        self.tab1.layout_treeview.addWidget(self.tab1.treeWidget)
        self.tab1.layout_treeview.addWidget(self.tab1.sendCommandGroupBox)
        self.tab1.layout_sendCommands.addWidget(self.tab1.commandsComboBox)
        self.tab1.layout_sendCommandsMiddleLeft.addWidget(self.tab1.commandsByte1Label)
        self.tab1.layout_sendCommandsMiddleLeft.addWidget(self.tab1.commandsByte1)
        self.tab1.layout_sendCommandsMiddleLeft.addWidget(self.tab1.commandsByte2Label)
        self.tab1.layout_sendCommandsMiddleLeft.addWidget(self.tab1.commandsByte2)
        self.tab1.layout_sendCommandsMiddleRight.addWidget(self.tab1.sendButton)
        self.tab1.layout_sendCommandsBottomLeft.addWidget(self.tab1.commandsResponseLabel)
        self.tab1.layout_sendCommandsBottomLeft.addWidget(self.tab1.commandsResponse)
        self.tab1.layout_controls.addWidget(self.tab1.initializeButton)
        self.tab1.layout_controls.addWidget(self.tab1.scanButton)
        self.tab1.layout_treeview.setAlignment(Qt.AlignTop)
        self.tab1.layout_controls.setAlignment(Qt.AlignTop)
        self.tab1.layout_sendCommandsMiddle.addLayout(self.tab1.layout_sendCommandsMiddleLeft)
        self.tab1.layout_sendCommandsMiddle.addLayout(self.tab1.layout_sendCommandsMiddleRight)
        self.tab1.layout_sendCommands.addLayout(self.tab1.layout_sendCommandsMiddle)
        self.tab1.layout_sendCommandsBottom.addLayout(self.tab1.layout_sendCommandsBottomLeft)
        self.tab1.layout_sendCommandsBottom.addLayout(self.tab1.layout_sendCommandsBottomRight)
        self.tab1.layout_sendCommandsBottomLeft.setAlignment(Qt.AlignLeft)
        self.tab1.layout_sendCommands.addLayout(self.tab1.layout_sendCommandsBottom)
        self.tab1.sendCommandGroupBox.setLayout(self.tab1.layout_sendCommands)
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

        for i in range(10):
            l1 = QTreeWidgetItem([ f"{i}",  f"{i}",  "0", "asdf" ])
            self.tab1.treeWidget.addTopLevelItem(l1)

    def openMenu(self, position):
        indexes = self.tab1.treeView.selectedIndexes()
        print(indexes)
        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1
        menu = QMenu()
        if level == 0:
            menu.addAction(self.tr("Change short address"))
            menu.addAction(self.tr("Add to group"))
        elif level == 1:
            menu.addAction(self.tr("Edit object/container"))
        elif level == 2:
            menu.addAction(self.tr("Edit object"))
        menu.exec_(self.tab1.treeView.viewport().mapToGlobal(position))

    def sendCommandDialog(self):
        sendDlg = QDialog(self)
        sendDlg.setWindowTitle("Send command")
        layout_sendCommandDialog = QHBoxLayout()
        comboBox = QComboBox()

        layout_sendCommandDialog.addWidget(comboBox)
        sendDlg.setLayout(layout_sendCommandDialog)
        sendDlg.exec_()

    @pyqtSlot()
    def writeDALILog(self):
        global dali_rec_buffer
        global dali_message_type
        global dali_message_received
        while dali_message_received.count(float('inf')) != DALI_BUFFER_LENGTH:
            index = dali_message_received.index(min(dali_message_received))
            if dali_message_type[index] == MESSAGE_TYPE_DALI_PC:
                text = '|| DALI -> PC |'
                for i in range(2,4):
                    text += '| ' + "0x{:02x}".format(dali_rec_buffer[index][i]) + ' '
                text += '|| '
            elif dali_message_type[index] == MESSAGE_TYPE_PC_DALI:
                text = '|| PC -> DALI |'
                for data in dali_rec_buffer[index]:
                    text += '| ' + "0x{:02x}".format(data) + ' '
                    text += '|| '
            #elif dali_message_type[index] == MESSAGE_TYPE_BALLAST_FOUND:
            dali_message_received[index] = float('inf')
        # elif direction == 2:
        #     text = f"{DALI_device.ballast_id} | {DALI_device.ballast_short_address} | {DALI_device.ballast_type}"

            self.tab2.log_textarea.appendPlainText(f"{text}")
            self.tab2.log_textarea.moveCursor(QtGui.QTextCursor.End)
            #print(text)

    # Click actions
    @pyqtSlot()
    def updateCommand(self):
        '''Read selected short address from the treeWidget if selected, else do nothing
        '''
        selectedItem = self.tab1.treeWidget.selectedItems()
        if selectedItem and self.tab1.commandsComboBox.currentText():
            byte1, byte2, byte1label, byte2label = DALI_command_sender.commandHandler(self.tab1.commandsComboBox.currentText(),
                int(selectedItem[0].text(0)),
                self.tab1.commandsByte1.value(),
                self.tab1.commandsByte2.value(),
                0)
            self.tab1.commandsByte1.setValue(byte1)
            self.tab1.commandsByte1Label.setText(byte1label)
            self.tab1.commandsByte2.setValue(byte2)
            self.tab1.commandsByte2Label.setText(byte2label)

    @pyqtSlot()
    def initializeButtonClick(self):
        self.tab1.treeWidget.clear()
        DALI_bus.initialize_bus()
        for i in range(len(DALI_bus._devices)):
            l1 = QTreeWidgetItem([ f"{DALI_bus._devices[i].address}",  f"{DALI_bus._devices[i].randomAddress}",  "0", f"{DALI_bus._devices[i].deviceType}" ])
            self.tab1.treeWidget.addTopLevelItem(l1)
        for i in range(4):
            self.tab1.treeWidget.resizeColumnToContents(i)


    @pyqtSlot()
    def scanButtonClick(self):
        self.tab1.treeWidget.clear()
        DALI_bus.assign_short_addresses()
        for i in range(len(DALI_bus._devices)):
            l1 = QTreeWidgetItem([ f"{DALI_bus._devices[i].address}",  f"{DALI_bus._devices[i].randomAddress}",  "0", f"{DALI_bus._devices[i].deviceType}" ])
            self.tab1.treeWidget.addTopLevelItem(l1)
        for i in range(4):
            self.tab1.treeWidget.resizeColumnToContents(i)

    @pyqtSlot()
    def sendButtonClick(self):
        self.sendCommandDialog()