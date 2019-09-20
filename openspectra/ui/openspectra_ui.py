#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.
from math import floor

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QApplication, QWidget

from openspectra.ui.bandlist import BandList
from openspectra.ui.imagedisplay import ImageDisplayWindow
from openspectra.ui.windowmanager import WindowManager
from openspectra.utils import Logger, LogHelper


class OpenSpectraUI(QMainWindow):

    __LOG:Logger = LogHelper.logger("OpenSpectraUI")

    def __init__(self):
        super().__init__()

        # listen for focus change events so we can control which menu items are available
        qApp = QtWidgets.qApp
        qApp.focusChanged.connect(self.__handle_focus_changed)

        self.__init_ui()

        # TODO QMainWindow can store the state of its layout with saveState(); it can later be retrieved
        # with restoreState(). It is the position and size (relative to the size of the main window) of the
        # toolbars and dock widgets that are stored.

    def __init_ui(self):
        self.setGeometry(25, 50, 600, 0)
        self.setWindowTitle('OpenSpectra')
        # self.setWindowIcon(QIcon('web.png'))

        # TODO on Mac this is redundant and doesn't seem to do anything, other paltforms probably need it
        # exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        # exitAct.setShortcut('Ctrl+Q')
        # exitAct.setStatusTip('Exit application')
        # exitAct.triggered.connect(qApp.quit)

        self.__open_action = QAction('&Open', self)
        self.__open_action.setShortcut('Ctrl+O')
        self.__open_action.setStatusTip('Open file')
        self.__open_action.triggered.connect(self.__open)

        self.__save_action = QAction("&Save", self)
        self.__save_action.setShortcut("Ctrl+S")
        self.__save_action.setStatusTip("Save sub-cube")
        self.__save_action.triggered.connect(self.__save)
        # TODO probably init to disabled until file opened?

        self.__close_action = QAction("&Close", self)
        self.__close_action.setShortcut("Ctrl+C")
        self.__close_action.setStatusTip("Close file")
        self.__close_action.triggered.connect(self.__close)
        # TODO probably init to disabled until file opened?

        self.__spectrum_plot_action = QAction('&Spectrum', self)
        self.__spectrum_plot_action.setShortcut('Ctrl+P')
        self.__spectrum_plot_action.setStatusTip('Open spectrum plot for current window')
        self.__spectrum_plot_action.triggered.connect(self.__plot)
        self.__spectrum_plot_action.setDisabled(True)

        self.__histogram_plot_action = QAction('&Histogram', self)
        self.__histogram_plot_action.setShortcut('Ctrl+G')
        self.__histogram_plot_action.setStatusTip('Open histogram for current window')
        self.__histogram_plot_action.triggered.connect(self.__plot)
        self.__histogram_plot_action.setDisabled(True)

        self.__link_action = QAction('&Link', self)
        self.__link_action.setShortcut('Ctrl+L')
        self.__link_action.setStatusTip('Link displays')
        self.__link_action.triggered.connect(self.__link_displays)
        self.__link_action.setDisabled(True)

        # TODO??
        # self.toolbar = self.addToolBar('Open')
        # self.toolbar.addAction(openAct)

        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(self.__open_action)
        file_menu.addAction(self.__save_action)
        file_menu.addAction(self.__close_action)
        # fileMenu.addAction(exitAct)

        plot_menu = menu_bar.addMenu("&Plot")
        plot_menu.addAction(self.__spectrum_plot_action)
        plot_menu.addAction(self.__histogram_plot_action)

        plot_menu = menu_bar.addMenu("&Windows")
        plot_menu.addAction(self.__link_action)

        self.__band_list = BandList(self)
        self.setCentralWidget(self.__band_list)

        self.__window_manager = WindowManager(self, self.__band_list)
        available_geometry = self.__window_manager.available_geometry()

        self.statusBar().showMessage('Ready')
        self.setGeometry(2, 25, 270, floor(available_geometry.bottom() * 0.90))
        self.show()

    def __open(self):
        self.__window_manager.open_file()

    def __save(self):
        self.__window_manager.open_save_subcube(self.__band_list.selected_file())

    def __close(self):
        self.__window_manager.close_file(self.__band_list.selected_file())

    def __link_displays(self):
        current_window:QWidget = QApplication.activeWindow()
        if current_window is not None and isinstance(current_window, ImageDisplayWindow):
            OpenSpectraUI.__LOG.debug("Found current window with title: {}", current_window.windowTitle())
            self.__window_manager.link_windows(current_window)
        else:
            # this shouldn't happen if __handle_focus_changed is working correctly
            OpenSpectraUI.__LOG.error(
                "Internal error, __link_displays called without focus on an image window.  Focus was on: {}",
                current_window)
            dialog = QMessageBox()
            dialog.setIcon(QMessageBox.Critical)
            dialog.setText("You must select an image window to start linking.")
            dialog.addButton(QMessageBox.Ok)
            dialog.exec()

    @pyqtSlot("QWidget*", "QWidget*")
    def __handle_focus_changed(self, old:QWidget, new:QWidget):
        current_window = QApplication.activeWindow()
        OpenSpectraUI.__LOG.debug("__handle_focus_changed called old: {}, new: {}, active window: {}",
            old, new, current_window)

        # TODO control which menus are available based on which window is active
        if current_window is not None and isinstance(current_window, ImageDisplayWindow):
            self.__link_action.setDisabled(False)
            self.__spectrum_plot_action.setDisabled(False)
            self.__histogram_plot_action.setDisabled(False)
        else:
            self.__link_action.setDisabled(True)
            self.__spectrum_plot_action.setDisabled(True)
            self.__histogram_plot_action.setDisabled(True)

    def __plot(self):
        # TODO open plots
        pass



