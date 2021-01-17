/**
 * Deluge.add.OptionsPanel.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge.add');

/**
 * @class Deluge.add.OptionsTab
 * @extends Ext.form.FormPanel
 */
Deluge.add.OptionsTab = Ext.extend(Ext.form.FormPanel, {
    title: _('Options'),
    height: 170,
    border: false,
    bodyStyle: 'padding: 5px',
    disabled: true,
    labelWidth: 1,

    initComponent: function () {
        Deluge.add.OptionsTab.superclass.initComponent.call(this);

        this.optionsManager = new Deluge.MultiOptionsManager();

        var fieldset = this.add({
            xtype: 'fieldset',
            title: _('Download Folder'),
            border: false,
            autoHeight: true,
            defaultType: 'textfield',
            labelWidth: 1,
            fieldLabel: '',
            style: 'padding: 5px 0; margin-bottom: 0;',
        });
        this.optionsManager.bind(
            'download_location',
            fieldset.add({
                fieldLabel: '',
                name: 'download_location',
                anchor: '95%',
                labelSeparator: '',
            })
        );
        var fieldset = this.add({
            xtype: 'fieldset',
            title: _('Move Completed Folder'),
            border: false,
            autoHeight: true,
            defaultType: 'togglefield',
            labelWidth: 1,
            fieldLabel: '',
            style: 'padding: 5px 0; margin-bottom: 0;',
        });
        var field = fieldset.add({
            fieldLabel: '',
            name: 'move_completed_path',
            anchor: '98%',
        });
        this.optionsManager.bind('move_completed', field.toggle);
        this.optionsManager.bind('move_completed_path', field.input);

        var panel = this.add({
            border: false,
            layout: 'column',
            defaultType: 'fieldset',
        });

        fieldset = panel.add({
            title: _('Bandwidth'),
            border: false,
            autoHeight: true,
            bodyStyle: 'padding: 2px 5px',
            labelWidth: 105,
            width: 200,
            defaultType: 'spinnerfield',
            style: 'padding-right: 10px;',
        });
        this.optionsManager.bind(
            'max_download_speed',
            fieldset.add({
                fieldLabel: _('Max Down Speed'),
                name: 'max_download_speed',
                width: 60,
            })
        );
        this.optionsManager.bind(
            'max_upload_speed',
            fieldset.add({
                fieldLabel: _('Max Up Speed'),
                name: 'max_upload_speed',
                width: 60,
            })
        );
        this.optionsManager.bind(
            'max_connections',
            fieldset.add({
                fieldLabel: _('Max Connections'),
                name: 'max_connections',
                width: 60,
            })
        );
        this.optionsManager.bind(
            'max_upload_slots',
            fieldset.add({
                fieldLabel: _('Max Upload Slots'),
                name: 'max_upload_slots',
                width: 60,
            })
        );

        fieldset = panel.add({
            // title: _('General'),
            border: false,
            autoHeight: true,
            defaultType: 'checkbox',
        });
        this.optionsManager.bind(
            'add_paused',
            fieldset.add({
                name: 'add_paused',
                boxLabel: _('Add In Paused State'),
                fieldLabel: '',
                labelSeparator: '',
            })
        );
        this.optionsManager.bind(
            'prioritize_first_last_pieces',
            fieldset.add({
                name: 'prioritize_first_last_pieces',
                boxLabel: _('Prioritize First/Last Pieces'),
                fieldLabel: '',
                labelSeparator: '',
            })
        );
        this.optionsManager.bind(
            'sequential_download',
            fieldset.add({
                name: 'sequential_download',
                boxLabel: _('Sequential Download'),
                fieldLabel: '',
                labelSeparator: '',
            })
        );
        this.optionsManager.bind(
            'seed_mode',
            fieldset.add({
                name: 'seed_mode',
                boxLabel: _('Skip File Hash Check'),
                fieldLabel: '',
                labelSeparator: '',
            })
        );
        this.optionsManager.bind(
            'super_seeding',
            fieldset.add({
                name: 'super_seeding',
                boxLabel: _('Super Seed'),
                fieldLabel: '',
                labelSeparator: '',
            })
        );
        this.optionsManager.bind(
            'pre_allocate_storage',
            fieldset.add({
                name: 'pre_allocate_storage',
                boxLabel: _('Preallocate Disk Space'),
                fieldLabel: '',
                labelSeparator: '',
            })
        );
    },

    getDefaults: function () {
        var keys = [
            'add_paused',
            'pre_allocate_storage',
            'download_location',
            'max_connections_per_torrent',
            'max_download_speed_per_torrent',
            'move_completed',
            'move_completed_path',
            'max_upload_slots_per_torrent',
            'max_upload_speed_per_torrent',
            'prioritize_first_last_pieces',
            'sequential_download',
        ];

        deluge.client.core.get_config_values(keys, {
            success: function (config) {
                var options = {
                    file_priorities: [],
                    add_paused: config.add_paused,
                    sequential_download: config.sequential_download,
                    pre_allocate_storage: config.pre_allocate_storage,
                    download_location: config.download_location,
                    move_completed: config.move_completed,
                    move_completed_path: config.move_completed_path,
                    max_connections: config.max_connections_per_torrent,
                    max_download_speed: config.max_download_speed_per_torrent,
                    max_upload_slots: config.max_upload_slots_per_torrent,
                    max_upload_speed: config.max_upload_speed_per_torrent,
                    prioritize_first_last_pieces:
                        config.prioritize_first_last_pieces,
                    seed_mode: false,
                    super_seeding: false,
                };
                this.optionsManager.options = options;
                this.optionsManager.resetAll();
            },
            scope: this,
        });
    },
});
