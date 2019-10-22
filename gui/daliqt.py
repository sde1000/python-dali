#!/usr/bin/env python3

from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from dali.driver import hasseb
from dali import bus
from dali import address
import DALICommands

# Create hasseb USB DALI driver instance to handle messages
DALI_device = hasseb.AsyncHassebDALIUSBDriver()
# Create DALI bus
DALI_bus = bus.Bus('hasseb DALI bus',   DALI_device)
# Instance to send individual DALI commands
DALI_command_sender = DALICommands.DALICommandSender(DALI_device)

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
        self.width, self.height = screen_resolution.width()/2, screen_resolution.height()/2
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
        self.tab1.layout_controls = QVBoxLayout()
        self.tab1.layout_treeWidget = QVBoxLayout()
        self.tab1.layout_sendCommands = QVBoxLayout()
        self.tab1.layout_addressByte = QHBoxLayout()
        self.tab1.layout_dataByte = QHBoxLayout()
        self.tab1.layout_sendButton = QHBoxLayout()
        self.tab1.layout_sendCommandsMiddle = QHBoxLayout()
        self.tab1.layout_response = QHBoxLayout()
        self.tab1.layout_sendCommandsBottom = QHBoxLayout()
        self.tab1.layout_sendCommandsBottomLeft = QHBoxLayout()
        self.tab1.layout_sendCommandsBottomRight = QHBoxLayout()

        # Widgets and actions
        # Buttons
        self.tab1.initializeButton = QPushButton('Initialize')
        self.tab1.initializeButton.clicked.connect(self.initializeButtonClick)
        self.tab1.scanButton = QPushButton('Scan bus')
        self.tab1.scanButton.clicked.connect(self.scanButtonClick)
        # TreeWidget
        self.tab1.treeWidget = QTreeWidget(self)
        self.tab1.treeWidget.setColumnCount(4)
        self.tab1.treeWidget.setHeaderLabels(["Short address", "Random address", "Group", "Device type"])
        for i in range(4):
            self.tab1.treeWidget.resizeColumnToContents(i)
        self.tab1.treeWidget.currentItemChanged.connect(self.updateCommand)
        self.tab1.treeWidget.itemClicked.connect(self.updateCommand)
        # Send commands group box
        self.tab1.sendCommandGroupBox = QGroupBox('Send commands')
        self.tab1.commandsComboBox = QComboBox()
        self.tab1.commandsComboBox.addItems(DALICommands.commands)
        self.tab1.commandsComboBox.activated[str].connect(self.updateCommand)
        # Address group box
        self.tab1.addressGroupBox = QGroupBox('Address')
        self.tab1.addressAll = QRadioButton('All')
        self.tab1.addressAll.setChecked(True)
        self.tab1.addressAll.toggled.connect(self.onAddressRadioClicked)
        self.tab1.addressGroup = QRadioButton('Group')
        self.tab1.addressGroup.toggled.connect(self.onAddressRadioClicked)
        self.tab1.addressShort = QRadioButton('Address')
        self.tab1.addressShort.toggled.connect(self.onAddressRadioClicked)
        self.tab1.addressByte = QSpinBox()
        self.tab1.addressByte.setRange(0, 255)
        self.tab1.addressByte.setEnabled(False)
        self.tab1.addressByte.clear()
        # Data group box
        self.tab1.dataGroupBox = QGroupBox('Data')
        self.tab1.dataByte = QSpinBox()
        self.tab1.dataByte.setRange(0, 255)
        self.tab1.dataByte2 = QSpinBox()
        self.tab1.dataByte2.setRange(0, 255)
        self.tab1.dataByte2.setVisible(False)
        # Send button
        self.tab1.sendButton = QPushButton('Send')
        self.tab1.sendButton.clicked.connect(self.sendButtonClick)
        # Response group box
        self.tab1.responseGroupBox = QGroupBox('Response')
        self.tab1.responseByte = QLineEdit()
        self.tab1.responseCommand = QLineEdit()

        # Add widgets to layouts
        # Buttons
        self.tab1.layout_controls.addWidget(self.tab1.initializeButton)
        self.tab1.layout_controls.addWidget(self.tab1.scanButton)
        # Treeview
        self.tab1.layout_treeWidget.addWidget(self.tab1.treeWidget)
        self.tab1.layout_treeWidget.addWidget(self.tab1.sendCommandGroupBox)
        # Send commands group box
        self.tab1.layout_sendCommands.addWidget(self.tab1.commandsComboBox)
        # Address group box
        self.tab1.layout_sendCommandsMiddle.addWidget(self.tab1.addressGroupBox)
        self.tab1.layout_addressByte.addWidget(self.tab1.addressAll)
        self.tab1.layout_addressByte.addWidget(self.tab1.addressGroup)
        self.tab1.layout_addressByte.addWidget(self.tab1.addressShort)
        self.tab1.layout_addressByte.addWidget(self.tab1.addressByte)
        self.tab1.addressGroupBox.setLayout(self.tab1.layout_addressByte)
        # Data group box
        self.tab1.layout_sendCommandsMiddle.addWidget(self.tab1.dataGroupBox)
        self.tab1.layout_dataByte.addWidget(self.tab1.dataByte)
        self.tab1.layout_dataByte.addWidget(self.tab1.dataByte2)
        self.tab1.dataGroupBox.setLayout(self.tab1.layout_dataByte)
        # Send button
        self.tab1.layout_sendButton.addWidget(self.tab1.sendButton)
        self.tab1.layout_sendCommandsMiddle.addLayout(self.tab1.layout_sendButton)
        # Response
        self.tab1.layout_sendCommandsBottomLeft.addWidget(self.tab1.responseGroupBox)
        self.tab1.layout_response.addWidget(self.tab1.responseByte)
        self.tab1.layout_response.addWidget(self.tab1.responseCommand)
        self.tab1.responseGroupBox.setLayout(self.tab1.layout_response)
        self.tab1.layout_treeWidget.setAlignment(Qt.AlignTop)
        self.tab1.layout_controls.setAlignment(Qt.AlignTop)
        self.tab1.layout_sendCommands.addLayout(self.tab1.layout_sendCommandsMiddle)
        self.tab1.layout_sendCommandsBottom.addLayout(self.tab1.layout_sendCommandsBottomLeft)
        self.tab1.layout_sendCommandsBottom.addLayout(self.tab1.layout_sendCommandsBottomRight)
        self.tab1.layout_sendCommandsBottomLeft.setAlignment(Qt.AlignLeft)
        self.tab1.layout_sendCommands.addLayout(self.tab1.layout_sendCommandsBottom)
        self.tab1.sendCommandGroupBox.setLayout(self.tab1.layout_sendCommands)
        self.tab1.layout.addLayout(self.tab1.layout_controls)
        self.tab1.layout.addLayout(self.tab1.layout_treeWidget)
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

    def onAddressRadioClicked(self):
        if self.tab1.addressAll.isChecked():
            self.tab1.addressByte.setEnabled(False)
            self.tab1.addressByte.clear()
        elif self.tab1.addressGroup.isChecked():
            self.tab1.addressByte.setRange(0, 15)
            self.tab1.addressByte.setEnabled(True)
        elif self.tab1.addressShort.isChecked():
            self.tab1.addressByte.setRange(0, 255)
            self.tab1.addressByte.setEnabled(True)

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
        '''Read selected short or group address from the treeWidget if selected, else do nothing
        '''
        selectedItem = self.tab1.treeWidget.selectedItems()
        if selectedItem and self.tab1.commandsComboBox.currentText():
            if self.tab1.addressAll.isChecked():
                self.tab1.addressByte.setEnabled(False)
                self.tab1.addressByte.clear()
            elif self.tab1.addressGroup.isChecked():
                self.tab1.addressByte.setRange(0, 31)
                self.tab1.addressByte.setEnabled(True)
                self.tab1.addressByte.setValue(int(selectedItem[0].text(2)))
            elif self.tab1.addressShort.isChecked():
                self.tab1.addressByte.setRange(0, 255)
                self.tab1.addressByte.setEnabled(True)
                self.tab1.addressByte.setValue(int(selectedItem[0].text(0)))
            # Data group box
            title, range = DALI_command_sender.getDataLabelRange(self.tab1.commandsComboBox.currentText())
            self.tab1.dataGroupBox.setTitle(title)
            self.tab1.dataByte.setRange(0, range)
            if range == 0:
                self.tab1.dataByte.setEnabled(False)
            else:
                self.tab1.dataByte.setEnabled(True)
            # If more than 1 data bytes
            # Set scene
            if self.tab1.commandsComboBox.currentText() == DALICommands.commands[29]:
                self.tab1.dataByte2.setVisible(True)
            else:
                self.tab1.dataByte2.setVisible(False)


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
        if self.tab1.addressAll.isChecked():
            DALI_command_sender.send(self.tab1.commandsComboBox.currentText(),
                                               address.Broadcast(),
                                               self.tab1.dataByte.value(),
                                               self.tab1.dataByte2.value())
        elif self.tab1.addressGroup.isChecked():
            DALI_command_sender.send(self.tab1.commandsComboBox.currentText(),
                                               address.Group(self.tab1.addressByte.value()),
                                               self.tab1.dataByte.value(),
                                               self.tab1.dataByte2.value())
        elif self.tab1.addressShort.isChecked():
            DALI_command_sender.send(self.tab1.commandsComboBox.currentText(),
                                               address.Short(self.tab1.addressByte.value()),
                                               self.tab1.dataByte.value(),
                                               self.tab1.dataByte2.value())