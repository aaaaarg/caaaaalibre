#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL 3'
__copyright__ = '2014, Alex Kosloff <pisatel1976@gmail.com>'
__docformat__ = 'restructuredtext en'

import re, urllib, collections, copy
from functools import partial

try:
    from PyQt4.Qt import (Qt, QVBoxLayout, QLabel, QLineEdit, QApplication,
        QGroupBox, QHBoxLayout, QToolButton, QTableWidgetItem,
        QIcon, QTableWidget, QPushButton, QCheckBox, QSizePolicy,
        QAbstractItemView, QVariant, QDialogButtonBox, QAction,
        QGridLayout, pyqtSignal, QUrl, QListWidget, QListWidgetItem,
        QTextEdit, QDialog, QTimer)
except:
    from PyQt5.Qt import (Qt, QVBoxLayout, QLabel, QLineEdit, QApplication,
        QGroupBox, QHBoxLayout, QToolButton, QTableWidgetItem,
        QIcon, QTableWidget, QPushButton, QCheckBox, QSizePolicy,
        QAbstractItemView, QVariant, QDialogButtonBox, QAction,
        QGridLayout, pyqtSignal, QUrl, QListWidget, QListWidgetItem,
        QTextEdit, QDialog, QTimer, QFileDialog)


from calibre.gui2.dialogs.choose_library_ui import Ui_Dialog

from calibre.ebooks.metadata import MetaInformation
from calibre.gui2 import error_dialog, question_dialog, gprefs, open_url
from calibre.gui2.library.delegates import RatingDelegate
from calibre.utils.date import qt_to_dt, UNDEFINED_DATE

from calibre_plugins.arg_plugin.utils import (get_icon, SizePersistedDialog, ImageLabel,
                                         ReadOnlyTableWidgetItem, ImageTitleLayout, ReadOnlyLineEdit,
                                         DateDelegate, RatingTableWidgetItem, DateTableWidgetItem)
from calibre.constants import (filesystem_encoding, iswindows,
        get_portable_base)

class SearchDialog(SizePersistedDialog):

    def __init__(self, parent=None, func=None, title="Search"):
        SizePersistedDialog.__init__(self, parent, 'arg plugin:search dialog')
        self.setWindowTitle(title)
        self.gui = parent
        self.func = func
        
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.search_label = QLabel(title)
        layout.addWidget(self.search_label)
        self.search_str = QLineEdit(self)
        self.search_str.setText('')
        layout.addWidget(self.search_str)
        self.search_label.setBuddy(self.search_str)

        self.find_button = QPushButton("&Find")
        self.search_button_box = QDialogButtonBox(Qt.Horizontal)
        self.search_button_box.addButton(self.find_button, QDialogButtonBox.ActionRole)
        self.search_button_box.clicked.connect(self._find_clicked)
        layout.addWidget(self.search_button_box)        

        self.values_list = QListWidget(self)
        # for multiple selection
        #self.values_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.values_list)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._accept_clicked)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Cause our dialog size to be restored from prefs or created on first usage
        self.resize_dialog()

    def _display_choices(self, choices):
        self.values_list.clear()
        for id, name in choices.items():
            item = QListWidgetItem(get_icon('images/books.png'), name, self.values_list)
            item.setData(1, (id,))
            self.values_list.addItem(item)

    def _find_clicked(self):
        query = unicode(self.search_str.text())
        self._display_choices(self.func(query))

    def _accept_clicked(self):
        #self._save_preferences()
        self.selected_result = None
        if self.values_list.currentItem():
            i = self.values_list.currentItem()
            self.selected_result = (i.data(1)[0], i.text())
        self.accept() 

