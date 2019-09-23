#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
from PyQt5.QtGui import QIcon

from daliqt import mainWindow

if __name__ == '__main__':
    app = QApplication([])
    GUI = mainWindow()
    app.setWindowIcon(QtGui.QIcon('hasseb_icon.ico'))
    app.exec_()
