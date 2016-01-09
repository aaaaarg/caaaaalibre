#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL 3'
__copyright__ = '2016, Alex Kosloff <pisatel1976@gmail.com>'
__docformat__ = 'restructuredtext en'

from functools import partial

try:
    from PyQt4.Qt import QMenu, Qt, QToolButton, QUrl
except:
    from PyQt5.Qt import QMenu, Qt, QToolButton, QUrl

from calibre.gui2 import error_dialog, question_dialog, info_dialog, open_url
from calibre.gui2.actions import InterfaceAction
from calibre.utils.config import config_dir
from calibre.gui2.dialogs.restore_library import DBRestore

from calibre.gui2.tag_browser.view import TagsView
# The class that all interface action plugins must inherit from
from calibre.gui2.actions import InterfaceAction
from calibre.gui2.actions.choose_library import ChooseLibraryAction

#from calibre_plugins.casanova_plugin.main import DemoDialog

from calibre_plugins.arg_plugin.config import prefs
from calibre_plugins.arg_plugin.utils import (set_plugin_icon_resources, get_icon,
                                                         create_menu_action_unique, get_library_path, create_library_path)
from calibre_plugins.arg_plugin.dialogs import SearchDialog
from calibre_plugins.arg_plugin.api import ArgAPI



PLUGIN_ICONS = ['images/bauta.ico', 'images/link.png', 'images/books.png']


class ArgUI(InterfaceAction):

    name = "A*RG"
    action_spec = (_('Casanova'), None, None, None)
    action_type = 'current'
    popup_type = QToolButton.InstantPopup
    
    def genesis(self):
        # This method is called once per plugin, do initial setup here
        self.old_actions_unique_map = {}

        icon_resources = self.load_resources(PLUGIN_ICONS)
        set_plugin_icon_resources(self.name, icon_resources)

        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)
        self.qaction.setIcon(get_icon(PLUGIN_ICONS[0]))

        self.qaction.setMenu(self.menu)
        #self.menu.aboutToShow.connect(self.about_to_show_menu)
        

    def initialization_complete(self):
        ''' An InterfaceAction method '''
        # @todo : create Casanova managers here
        self.api = ArgAPI(self.gui)
        #self.mm = CasanovaMetadataManager(self.gui)
        #self.dm = CasanovaDownloadManager(self.gui, self.mm)
        #self.am = CasanovaAddManager(self.gui)
        #self.rebuild_menus()
        self.create_add_library_actions()
        #print(self.api.update_library())
        #print(self.api.commit(1))
        #self.restore_db()

    def add_book():
        pass
    def download_format():
        pass
    def casanova_issue_submenu():
        pass
    def search():
        pass
    def refresh_metadata():
        pass
    def upload_metadata():
        pass
    def update_issues():
        pass
    def update_author():
        pass
    def show_configuration():
        pass

    """
    Adds a couple actions to Calibre's choose library menu so that users can quickly 
    import an entire collection or author as a new library.
    """
    def create_add_library_actions(self):
        choose_library_action = self.gui.iactions['Choose Library']
        self.choose_library_action = choose_library_action
        choose_library_action.choose_menu.addSeparator()
        ac = self.create_action(spec=(_('Create new library from an A*RG collection'), 'images/books.png', None, None), attr='action_arg_collection')
        ac.triggered.connect(self.search_collections, type=Qt.QueuedConnection)
        choose_library_action.choose_menu.addAction(ac)
        ac = self.create_action(spec=(_('Create new library from an A*RG author'), 'images/books.png', None, None), attr='action_arg_author')
        ac.triggered.connect(self.search_authors, type=Qt.QueuedConnection)
        choose_library_action.choose_menu.addAction(ac)

    def search_collections(self):
        search_dialog = SearchDialog(self.gui, self.api.search_collections, title="Search collections:")
        search_dialog.exec_()
        if search_dialog.result() != search_dialog.Accepted:
            return
        if search_dialog.selected_result is None:
            return error_dialog(self.gui, 'No results',
                                'No results!', show=True)
        id, text = search_dialog.selected_result
        text = text.rsplit(' (',1)[0]
        np = create_library_path(self.gui, text)
        self.choose_library_action.choose_library_callback(np)
        # save some data to the new database
        self.api.download_collection(id)
        db = self.gui.current_db.new_api
        db.set_pref('arg_library_type', 'collection')
        db.set_pref('arg_id', id)
        db.set_pref('arg_title', text)
        return info_dialog(self.gui, 'Created library', 'Created a new library at ' + np, show=True)

    def search_authors(self):
        search_dialog = SearchDialog(self.gui, self.api.search_authors, title="Search authors:")
        search_dialog.exec_()
        if search_dialog.result() != search_dialog.Accepted:
            return
        if search_dialog.selected_result is None:
            return error_dialog(self.gui, 'No results',
                                'No results!', show=True)
        id, text = search_dialog.selected_result
        np = create_library_path(self.gui, text)
        self.choose_library_action.choose_library_callback(np)
        # save some data to the new database
        self.api.download_author(id)
        db = self.gui.current_db.new_api
        db.set_pref('arg_library_type', 'author')
        db.set_pref('arg_id', id)
        db.set_pref('arg_title', text)
        return info_dialog(self.gui, 'Created library', 'Created a new library at ' + np, show=True)

    def rebuild_menus(self):
        ''' Builds the UI menus '''
        print('Rebuilding menus')
        m = self.menu
        m.clear()
        self.actions_unique_map = {}

        if False and prefs['username']=='guest' and prefs['password']=='guest':
            foo = True
        else:
            self.add_new_menu_item = create_menu_action_unique(self, m, _('&Add to Casanova') + '...', None, shortcut=False, triggered=self.add_book)
            self.casanova_book_submenu = m.addMenu(get_icon('images/link.png'), 'Linked text')
            self.create_menu_item_ex(self.casanova_book_submenu, 'Refresh metadata',
                    'images/update.png', 'Gets any updates to the metadata for this text from the server',
                    triggered=self.refresh_metadata)
            self.create_menu_item_ex(self.casanova_book_submenu, 'Upload metadata',
                    'images/commit.png', 'Send your metadata changes for this text to the server',
                    triggered=self.upload_metadata)
            self.casanova_book_submenu.addSeparator()
            self.create_menu_item_ex(self.casanova_book_submenu, 'Download',
                    'images/download.png', 'Download a file format from the Casanova server',
                    triggered=self.download_format)
            m.addSeparator()
            self.casanova_issue_submenu = m.addMenu(get_icon('images/link.png'), 'Get metadata')
            self.create_menu_item_ex(self.casanova_issue_submenu, 'Update issues',
                    'images/refresh.png', 'Get updates to issues from the Casanova server',
                    triggered=self.update_issues)
            self.author_menu_item = self.create_menu_item_ex(self.casanova_issue_submenu, 'Get all by author',
                    'images/download.png', 'Get metadata for all texts by this author',
                    triggered=self.update_author)
            self.create_menu_item_ex(self.casanova_issue_submenu, 'Search',
                    'images/download.png', 'Search Casanova titles and authors',
                    triggered=self.search)

        m.addSeparator()
        create_menu_action_unique(self, m, _('&Settings') + '...', None, shortcut=False, triggered=self.show_configuration)
        # Before we finalize, make sure we delete any actions for menus that are no longer displayed
        for menu_id, unique_name in self.old_actions_unique_map.iteritems():
            if menu_id not in self.actions_unique_map:
                self.gui.keyboard.unregister_shortcut(unique_name)
        self.old_actions_unique_map = self.actions_unique_map
        self.gui.keyboard.finalize()

        from calibre.gui2 import gprefs
        
        if self.name not in gprefs['action-layout-context-menu']:
            gprefs['action-layout-context-menu'] += (self.name, )
        if self.name not in gprefs['action-layout-toolbar']:
            gprefs['action-layout-toolbar'] += (self.name, )
        
        #gprefs['action-layout-context-menu'] += ('AAAARG', )
        #gprefs['action-layout-toolbar'] += ('AAAARG', )
        #print(gprefs['action-layout-toolbar'])
        # force add our menu into the gui toolbar
        #print(self.gui.tags_view.context_menu)
        #print(gprefs['action-layout-context-menu'])
        for x in (self.gui.preferences_action, self.qaction):
            x.triggered.connect(self.show_configuration)


    def create_menu_item_ex(self, parent_menu, menu_text, image=None, tooltip=None,
                           shortcut=None, triggered=None, is_checked=None, shortcut_name=None,
                           unique_name=None):
        ac = create_menu_action_unique(self, parent_menu, menu_text, image, tooltip,
                                       shortcut, triggered, is_checked, shortcut_name, unique_name)
        self.actions_unique_map[ac.calibre_shortcut_unique_name] = ac.calibre_shortcut_unique_name
        return ac
