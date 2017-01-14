#!/usr/bin/env python3

import os.path
import PyQt5.uic
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtWidgets, QtSql
from common import resource_icon, UI_SOURCE_LOCATION, DatabaseResourceForm

COSTUME_FORM_SOURCE = os.path.join(UI_SOURCE_LOCATION, "form_costume.ui")
UiCostumeForm = PyQt5.uic.loadUiType(COSTUME_FORM_SOURCE)[0]

class CostumeForm(UiCostumeForm, DatabaseResourceForm):
    """This class represents the form for manipulating the costumes."""

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self._model = None
        self._relational_delegate = QtSql.QSqlRelationalDelegate(self.costume_table)

    def reset_model(self):
        # Implementation of the parent's abstract method.
        if self.database:
            self._model = CostumeModel(self, self.database, self.resource_root)
            self.costume_table.setModel(self._model)
            self.costume_table.setItemDelegateForColumn(
                self._model.fieldIndex("filename"),
                self._relational_delegate,
            )
            self.costume_table.hideColumn(self._model.fieldIndex("id"))
        else:
            self._model = None
            self.costume_table.setModel(None)

    def save_model(self):
        if self._model is not None:
            if not self._model.submit():
                QtWidgets.QMessageBox.critical(
                    self,
                    "Could not write the costume data",
                    "Could not write the costume data. The data is likely invalid.",
                    QtWidgets.QMessageBox.Ok,
                )
                return False
        return True

    @QtCore.pyqtSlot()
    def add_costume(self):
        """Adds a costume to the end of the table."""

        if self._model:
            # Make sure we have written out to the database.
            if not self.save_model():
                return

            # Create a new item at the bottom of the list by getting the list length.
            new_index = self._model.rowCount()

            if self._model.insertRows(new_index, 1):
                # Immediately edit the new field if creation was a success.
                self.costume_table.edit(self._model.index(new_index, 1))
            else:
                # Raise an error dialogue otherwise.
                QtWidgets.QMessageBox.critical(
                    self,
                    "Could not add a new costume",
                    "Could not add a new costume.",
                    QtWidgets.QMessageBox.Ok,
                )

    @QtCore.pyqtSlot()
    def remove_costumes(self):
        """Removes costumes based on the indices selected in the view."""

        if self._model:
            for index in self.costume_table.selectedIndexes():
                self._model.removeRow(index.row(), index.parent())
            self._model.select()

class CostumeModel(QtSql.QSqlRelationalTableModel):
    """This class represents the database table costumes left joined with the table resources."""

    def __init__(self, parent, database, resource_root = None):
        super().__init__(parent, database)
        self.setTable("costumes")
        self.setRelation(2, QtSql.QSqlRelation("resources", "id", "filename"))
        self.setJoinMode(QtSql.QSqlRelationalTableModel.LeftJoin)
        self.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        self.select()
        self.resource_root = resource_root

    def data(self, index, role = Qt.DisplayRole):
        # This method is overridden in order to provide icons of the resources themselves. This is
        # done by providing a valid icon for the role "DecorationRole".

        if index.column() == self.fieldIndex("filename") and role == Qt.DecorationRole:
            return resource_icon(self, index, self.resource_root)
        else:
            # Don't touch the other columns/roles. Delegate this to the parent.
            return super().data(index, role)
