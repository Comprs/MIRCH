#!/usr/bin/env python3

import os.path
import PyQt5.uic
from PyQt5 import QtCore, QtWidgets, QtSql
from common import UI_SOURCE_LOCATION, DatabaseResourceForm

CHARACTER_FORM_RESOURCE = os.path.join(UI_SOURCE_LOCATION, "form_character.ui")
UiCharacterForm = PyQt5.uic.loadUiType(CHARACTER_FORM_RESOURCE)[0]

class CharacterForm(UiCharacterForm, DatabaseResourceForm):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self._character_model = None
        self._character_widget_mapper = QtWidgets.QDataWidgetMapper()

        # Define the connection here rather than in the .ui file like everything else because it
        # mysteriously doesn't work when defined like than.
        self.character_list.clicked.connect(self.update_selected_character)

    def reset_model(self):
        if self.database:
            self._character_model = CharacterModel(self, self.database, self.resource_root)

            self.character_list.setModel(self._character_model)
            self.character_list.setModelColumn(self._character_model.fieldIndex("name"))

            combo_model = self._character_model.relationModel(
                self._character_model.fieldIndex("filename")
            )
            self.resource_combo.setModel(combo_model)
            self.resource_combo.setModelColumn(combo_model.fieldIndex("filename"))

            self._character_widget_mapper.setModel(self._character_model)
            self._character_widget_mapper.setItemDelegate(QtSql.QSqlRelationalDelegate(self))

            fields = ["name", "description", "selection_weight", "filename"]
            widgets = [
                self.name_edit,
                self.description_edit,
                self.selection_weight_spin,
                self.resource_combo,
            ]
            field_ids = map(self._character_model.fieldIndex, fields)

            for widget, field_id in zip(widgets, field_ids):
                self._character_widget_mapper.addMapping(widget, field_id)
        else:
            self.character_list.setModel(None)

    def save_model(self):
        if self._character_model is not None:
            if not self._character_model.submit():
                QtWidgets.QMessageBox.critical(
                    self,
                    "Could not write the character data",
                    "Could not write the character data. The data is likely invalid.",
                    QtWidgets.QMessageBox.Ok,
                )
                return False
        return True

    @QtCore.pyqtSlot()
    def add_character(self):
        if self._character_model:
            # Make sure we have written out to the database.
            if not self.save_model():
                return

            new_index = self._character_model.rowCount()

            if self._character_model.insertRows(new_index, 1):
                new_item_index = self._character_model.index(new_index, 1)
                self._character_widget_mapper.setCurrentModelIndex(new_item_index)
                self.selection_weight_spin.setValue(100)
                self.resource_combo.setCurrentIndex(-1)
                self.character_list.edit(new_item_index)
            else:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Could not add a new character",
                    "Could not add a new character.",
                    QtWidgets.QMessageBox.Ok,
                )

    @QtCore.pyqtSlot()
    def remove_characters(self):
        if self._character_model:
            for index in self.character_list.selectedIndexes():
                self.model.removeRow(index.row(), index.parent())
            self.model.select()

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def update_selected_character(self, index):
        self._character_widget_mapper.setCurrentModelIndex(index)

class CharacterModel(QtSql.QSqlRelationalTableModel):
    def __init__(self, parent, database, resource_root = None):
        super().__init__(parent, database)
        self.setTable("characters")
        self.setRelation(4, QtSql.QSqlRelation("resources", "id", "filename"))
        self.setJoinMode(QtSql.QSqlRelationalTableModel.LeftJoin)
        self.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        self.select()
        self.resource_root = resource_root
