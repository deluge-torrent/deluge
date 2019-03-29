# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Bro <bro.development@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component
from deluge.ui.client import client

from .path_combo_chooser import PathChooserComboBox

log = logging.getLogger(__name__)


def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


@singleton
class PathChoosersHandler(component.Component):
    def __init__(self, paths_config_key=None):
        # self.chooser_name = "PathChooser_%d" % (len(PathChooser.path_choosers) +1)
        component.Component.__init__(self, 'PathChoosersHandler')
        self.path_choosers = []
        self.paths_list_keys = []
        self.config_properties = {}
        self.started = False
        self.config_keys_to_funcs_mapping = {
            'path_chooser_show_chooser_button_on_localhost': 'filechooser_button_visible',
            'path_chooser_show_path_entry': 'path_entry_visible',
            'path_chooser_auto_complete_enabled': 'auto_complete_enabled',
            'path_chooser_show_folder_name': 'show_folder_name_on_button',
            'path_chooser_accelerator_string': 'accelerator_string',
            'path_chooser_show_hidden_files': 'show_hidden_files',
            'path_chooser_max_popup_rows': 'max_popup_rows',
        }

    def start(self):
        self.started = True
        self.update_config_from_core()

    def stop(self):
        self.started = False

    def update_config_from_core(self):
        def _on_config_values(config):
            self.config_properties.update(config)
            for chooser in self.path_choosers:
                chooser.set_config(config)

        keys = list(self.config_keys_to_funcs_mapping)
        keys += self.paths_list_keys
        client.core.get_config_values(keys).addCallback(_on_config_values)

    def register_chooser(self, chooser):
        chooser.config_key_funcs = {}
        for key in self.config_keys_to_funcs_mapping:
            chooser.config_key_funcs[key] = [None, None]
            chooser.config_key_funcs[key][0] = getattr(
                chooser, 'get_%s' % self.config_keys_to_funcs_mapping[key]
            )
            chooser.config_key_funcs[key][1] = getattr(
                chooser, 'set_%s' % self.config_keys_to_funcs_mapping[key]
            )

        self.path_choosers.append(chooser)
        if chooser.paths_config_key not in self.paths_list_keys:
            self.paths_list_keys.append(chooser.paths_config_key)
            if self.started:
                self.update_config_from_core()
        else:
            chooser.set_config(self.config_properties)

    def set_value_for_path_choosers(self, value, key):
        for chooser in self.path_choosers:
            chooser.config_key_funcs[key][1](value)

        # Save to core
        if key != 'path_chooser_max_popup_rows':
            client.core.set_config({key: value})
        else:
            # Since the max rows value can be changed fast with a spinbutton, we
            # delay saving to core until the values hasn't been changed in 1 second.
            self.max_rows_value_set = value

            def update(value_):
                # The value hasn't been changed in one second, so save to core
                if self.max_rows_value_set == value_:
                    client.core.set_config({'path_chooser_max_popup_rows': value})

            from twisted.internet import reactor

            reactor.callLater(1, update, value)

    def on_list_values_changed(self, values, key, caller):
        # Save to core
        config = {key: values}
        client.core.set_config(config)
        # Set the values on all path choosers with that key
        for chooser in self.path_choosers:
            # Found chooser with values from 'key'
            if chooser.paths_config_key == key:
                chooser.set_values(values)

    def get_config_keys(self):
        keys = list(self.config_keys_to_funcs_mapping)
        keys += self.paths_list_keys
        return keys


class PathChooser(PathChooserComboBox):
    def __init__(self, paths_config_key=None, parent=None):
        self.paths_config_key = paths_config_key
        super(PathChooser, self).__init__(parent=parent)
        self.chooser_handler = PathChoosersHandler()
        self.chooser_handler.register_chooser(self)
        self.set_auto_completer_func(self.on_completion)
        self.connect('list-values-changed', self.on_list_values_changed_event)
        self.connect(
            'auto-complete-enabled-toggled', self.on_auto_complete_enabled_toggled
        )
        self.connect('show-filechooser-toggled', self.on_show_filechooser_toggled)
        self.connect(
            'show-folder-name-on-button', self.on_show_folder_on_button_toggled
        )
        self.connect('show-path-entry-toggled', self.on_show_path_entry_toggled)
        self.connect('accelerator-set', self.on_accelerator_set)
        self.connect('max-rows-changed', self.on_max_rows_changed)
        self.connect('show-hidden-files-toggled', self.on_show_hidden_files_toggled)

    def on_auto_complete_enabled_toggled(self, widget, value):
        self.chooser_handler.set_value_for_path_choosers(
            value, 'path_chooser_auto_complete_enabled'
        )

    def on_show_filechooser_toggled(self, widget, value):
        self.chooser_handler.set_value_for_path_choosers(
            value, 'path_chooser_show_chooser_button_on_localhost'
        )

    def on_show_folder_on_button_toggled(self, widget, value):
        self.chooser_handler.set_value_for_path_choosers(
            value, 'path_chooser_show_folder_name'
        )

    def on_show_path_entry_toggled(self, widget, value):
        self.chooser_handler.set_value_for_path_choosers(
            value, 'path_chooser_show_path_entry'
        )

    def on_accelerator_set(self, widget, value):
        self.chooser_handler.set_value_for_path_choosers(
            value, 'path_chooser_accelerator_string'
        )

    def on_show_hidden_files_toggled(self, widget, value):
        self.chooser_handler.set_value_for_path_choosers(
            value, 'path_chooser_show_hidden_files'
        )

    def on_max_rows_changed(self, widget, value):
        self.chooser_handler.set_value_for_path_choosers(
            value, 'path_chooser_max_popup_rows'
        )

    def on_list_values_changed_event(self, widget, values):
        self.chooser_handler.on_list_values_changed(values, self.paths_config_key, self)

    def set_config(self, config):
        self.config = config
        for key in self.config_key_funcs:
            if key in config:
                try:
                    self.config_key_funcs[key][1](config[key])
                except TypeError as ex:
                    log.warning('TypeError: %s', ex)

        # Set the saved paths
        if self.paths_config_key and self.paths_config_key in config:
            self.set_values(config[self.paths_config_key])

    def on_completion(self, args):
        def on_paths_cb(args):
            self.complete(args)

        d = client.core.get_completion_paths(args)
        d.addCallback(on_paths_cb)
