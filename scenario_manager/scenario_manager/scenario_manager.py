#!/usr/bin/env python3

import os.path
import PyQt5.uic
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtWidgets, QtSql
from common import UI_SOURCE_LOCATION, SCHEMA_SCRIPT
from forms.resource import ResourceForm
from forms.costume import CostumeForm

# Load in the form for the main window
MAIN_WINDOW_SOURCE = os.path.join(UI_SOURCE_LOCATION, "form_scenario_manager_main.ui")
UiScenarioManagerMainWindow = PyQt5.uic.loadUiType(MAIN_WINDOW_SOURCE)[0]

DATABASE_FILE_EXTENSION = ".db"

class ScenarioManagerMainWindow(UiScenarioManagerMainWindow, QtWidgets.QMainWindow):
    """This class represents the main window of the application"""

    def __init__(self, parent = None):
        super().__init__(parent, Qt.Window)
        self.setupUi(self)

        self._database = None
        self._resource_root = "./"

        # Define all of the dependent widgets which will be used in the tab widget in this list for
        # convenient iteration.
        self._tab_widgets = [
            (ResourceForm(self.central_tab_widget), "Resources"),
            (CostumeForm(self.central_tab_widget), "Costumes"),
        ]

        # Add all of the widgets into the tab widget.
        for widget, tab_title in self._tab_widgets:
            self.central_tab_widget.addTab(widget, tab_title)

        # Disable the tab widget whilst no database is open.
        self.central_tab_widget.setEnabled(False)

    def _open_database_chooser(self):
        """Open a dialogue to select a database to use or create. Return the value as a string or
        return None if the user cancelled.
        """

        # Define the dialogue parameters
        dialogue = QtWidgets.QFileDialog(self)
        dialogue.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialogue.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialogue.setOptions(QtWidgets.QFileDialog.DontConfirmOverwrite)
        dialogue.setNameFilter("Databases (*{})".format(DATABASE_FILE_EXTENSION))
        dialogue.setNameFilters([
            "Databases (*{})".format(DATABASE_FILE_EXTENSION),
            "All Files (*.*)",
        ])

        # Get a result from the dialogue. If the user cancelled, propagate the "None".
        if not dialogue.exec_():
            return None
        # The dialogue returns a list. Extract the first element to return a single item.
        return dialogue.selectedFiles()[0]

    @staticmethod
    def _correct_filename(filename, *, exists = os.path.exists):
        # Make sure the correct file extension is in the filename if we are the create the
        # database.
        has_correct_file_extension = os.path.splitext(filename)[1] != DATABASE_FILE_EXTENSION
        file_exists = exists(filename)
        if has_correct_file_extension and not file_exists:
            return filename + DATABASE_FILE_EXTENSION
        else:
            return filename

    @staticmethod
    def _open_database_with_name(database_name):
        """Open a SQL database with the given filename."""

        # Open the new database.
        database = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        database.setDatabaseName(database_name)
        database.open()

        # Check that the database opened correctly. Display an error dialogue if it didn't and
        # abort.
        if database.isOpenError() or not database.isOpen():
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setText("Error opening the database.")
            msg_box.setInformativeText(
                "There was an error opening the database. The driver gave the following error "\
                "message: \"{}\"".format(database.lastError().text().strip())
            )
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msg_box.setIcon(QtWidgets.Critical)
            msg_box.exec_()
            return None
        else:
            return database

    @QtCore.pyqtSlot()
    def open_database(self):
        """Open or change the working database"""

        # Get a filename from the user. The function may return None to indicate the operation was
        # canceled.
        database_name = self._open_database_chooser()
        if database_name is None:
            return

        # Transform the filename to the correct form.
        database_name = self._correct_filename(database_name)

        # Open the new database. It may be none indicating something went wrong; an error message
        # will have been displayed by this point, so we should just stop here.
        new_database = self._open_database_with_name(database_name)
        if new_database is None:
            return

        # Swap out the old database if it exists and replace it with the new one.
        if self._database is not None:
            self._database.close()
        self._database = new_database

        # Create the tables using an external SQL script. The script must be submitted statement
        # by statement due to API limitations where only a statement may be executed.
        with open(SCHEMA_SCRIPT, "rt") as schema_file:
            for statement in schema_file.read().split(";"):
                self._database.exec_(statement)

        # Update the depended widgets with the new database.
        for widget, _ in self._tab_widgets:
            widget.set_database(self._database)

        # The database is now open so we can enable.
        self.central_tab_widget.setEnabled(True)

    @QtCore.pyqtSlot()
    def set_resource_root(self):
        """Set the new resource root"""

        # Define the dialogue parameters
        dialogue = QtWidgets.QFileDialog(self)
        dialogue.setFileMode(QtWidgets.QFileDialog.Directory)

        # Get a result from the dialogue. If the user cancel, stop changing the root resource
        # directory.
        if not dialogue.exec_():
            return
        self._resource_root = dialogue.selectedFiles()[0]

        # Update the depended widgets with the new resource root.
        for widget, _ in self._tab_widgets:
            widget.set_resource_root(self._resource_root)
