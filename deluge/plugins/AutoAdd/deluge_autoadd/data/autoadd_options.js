/**
 * Script: autoadd.js
 *      The client-side javascript code for the AutoAdd plugin.
 *
 * Copyright (C) 2009 GazpachoKing <chase.sterling@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Ext.ns('Deluge.ux.AutoAdd');

/**
 * @class Deluge.ux.AutoAdd.AutoAddWindowBase
 * @extends Ext.Window
 */
Deluge.ux.AutoAdd.AutoAddWindowBase = Ext.extend(Ext.Window, {
    width: 350,
    autoHeight: true,
    closeAction: 'hide',

    spin_ids: ['max_download_speed', 'max_upload_speed', 'stop_ratio'],
    spin_int_ids: ['max_upload_slots', 'max_connections'],
    chk_ids: [
        'stop_at_ratio',
        'remove_at_ratio',
        'move_completed',
        'add_paused',
        'auto_managed',
        'queue_to_top',
    ],
    toggle_ids: [
        'append_extension_toggle',
        'download_location_toggle',
        'label_toggle',
        'copy_torrent_toggle',
        'delete_copy_torrent_toggle',
        'seed_mode',
    ],

    accounts: new Ext.data.ArrayStore({
        storeId: 'accountStore',
        id: 0,
        fields: [
            {
                name: 'displayText',
                type: 'string',
            },
        ],
    }),
    labels: new Ext.data.ArrayStore({
        storeId: 'labelStore',
        id: 0,
        fields: [
            {
                name: 'displayText',
                type: 'string',
            },
        ],
    }),

    initComponent: function () {
        Deluge.ux.AutoAdd.AutoAddWindowBase.superclass.initComponent.call(this);
        this.addButton(_('Cancel'), this.onCancelClick, this);

        this.MainTab = new Deluge.ux.AutoAdd.AutoAddMainPanel();
        this.OptionsTab = new Deluge.ux.AutoAdd.AutoAddOptionsPanel();

        this.form = this.add({
            xtype: 'form',
            baseCls: 'x-plain',
            bodyStyle: 'padding: 5px',
            items: [
                {
                    xtype: 'tabpanel',
                    activeTab: 0,
                    items: [this.MainTab, this.OptionsTab],
                },
            ],
        });
    },

    onCancelClick: function () {
        this.hide();
    },

    getOptions: function () {
        var options = {};

        options['enabled'] = Ext.getCmp('enabled').getValue();
        options['path'] = Ext.getCmp('path').getValue();
        options['download_location'] = Ext.getCmp(
            'download_location'
        ).getValue();
        options['move_completed_path'] = Ext.getCmp(
            'move_completed_path'
        ).getValue();
        options['copy_torrent'] = Ext.getCmp('copy_torrent').getValue();

        options['label'] = Ext.getCmp('label').getValue();
        options['append_extension'] = Ext.getCmp('append_extension').getValue();
        options['owner'] = Ext.getCmp('owner').getValue();

        this.toggle_ids.forEach(function (toggle_id) {
            options[toggle_id] = Ext.getCmp(toggle_id).getValue();
        });
        this.spin_ids.forEach(function (spin_id) {
            options[spin_id] = Ext.getCmp(spin_id).getValue();
            options[spin_id + '_toggle'] = Ext.getCmp(
                spin_id + '_toggle'
            ).getValue();
        });
        this.spin_int_ids.forEach(function (spin_int_id) {
            options[spin_int_id] = Ext.getCmp(spin_int_id).getValue();
            options[spin_int_id + '_toggle'] = Ext.getCmp(
                spin_int_id + '_toggle'
            ).getValue();
        });
        this.chk_ids.forEach(function (chk_id) {
            options[chk_id] = Ext.getCmp(chk_id).getValue();
            options[chk_id + '_toggle'] = Ext.getCmp(
                chk_id + '_toggle'
            ).getValue();
        });

        if (
            options['copy_torrent_toggle'] &&
            options['path'] === options['copy_torrent']
        ) {
            throw _(
                '"Watch Folder" directory and "Copy of .torrent' +
                    ' files to" directory cannot be the same!'
            );
        }

        return options;
    },

    loadOptions: function (options) {
        /*
         * Populate all available options data to the UI
         */
        var value;

        if (options === undefined) {
            options = {};
        }
        Ext.getCmp('enabled').setValue(
            options['enabled'] !== undefined ? options['enabled'] : true
        );
        Ext.getCmp('isnt_append_extension').setValue(true);
        Ext.getCmp('append_extension_toggle').setValue(
            options['append_extension_toggle'] !== undefined
                ? options['append_extension_toggle']
                : false
        );
        Ext.getCmp('append_extension').setValue(
            options['append_extension'] !== undefined
                ? options['append_extension']
                : '.added'
        );
        Ext.getCmp('download_location_toggle').setValue(
            options['download_location_toggle'] !== undefined
                ? options['download_location_toggle']
                : false
        );
        Ext.getCmp('copy_torrent_toggle').setValue(
            options['copy_torrent_toggle'] !== undefined
                ? options['copy_torrent_toggle']
                : false
        );
        Ext.getCmp('delete_copy_torrent_toggle').setValue(
            options['delete_copy_torrent_toggle'] !== undefined
                ? options['delete_copy_torrent_toggle']
                : false
        );

        value =
            options['seed_mode'] !== undefined ? options['seed_mode'] : false;
        Ext.getCmp('seed_mode').setValue(value);

        this.accounts.removeAll(true);
        this.labels.removeAll(true);
        Ext.getCmp('owner').store = this.accounts;
        Ext.getCmp('label').store = this.labels;
        Ext.getCmp('label').setValue(
            options['label'] !== undefined ? options['label'] : ''
        );
        Ext.getCmp('label_toggle').setValue(
            options['label_toggle'] !== undefined
                ? options['label_toggle']
                : false
        );

        this.spin_ids.forEach(function (spin_id) {
            Ext.getCmp(spin_id).setValue(
                options[spin_id] !== undefined ? options[spin_id] : 0
            );
            Ext.getCmp(spin_id + '_toggle').setValue(
                options[spin_id + '_toggle'] !== undefined
                    ? options[spin_id + '_toggle']
                    : false
            );
        });
        this.chk_ids.forEach(function (chk_id) {
            Ext.getCmp(chk_id).setValue(
                options[chk_id] !== undefined ? options[chk_id] : true
            );
            Ext.getCmp(chk_id + '_toggle').setValue(
                options[chk_id + '_toggle'] !== undefined
                    ? options[chk_id + '_toggle']
                    : false
            );
        });
        value =
            options['add_paused'] !== undefined ? options['add_paused'] : true;
        if (!value) {
            Ext.getCmp('not_add_paused').setValue(true);
        }
        value =
            options['queue_to_top'] !== undefined
                ? options['queue_to_top']
                : true;
        if (!value) {
            Ext.getCmp('not_queue_to_top').setValue(true);
        }
        value =
            options['auto_managed'] !== undefined
                ? options['auto_managed']
                : true;
        if (!value) {
            Ext.getCmp('not_auto_managed').setValue(true);
        }
        [
            'move_completed_path',
            'path',
            'download_location',
            'copy_torrent',
        ].forEach(function (field) {
            value = options[field] !== undefined ? options[field] : '';
            Ext.getCmp(field).setValue(value);
        });

        if (Object.keys(options).length === 0) {
            deluge.client.core.get_config({
                success: function (config) {
                    var value;
                    Ext.getCmp('download_location').setValue(
                        options['download_location'] !== undefined
                            ? options['download_location']
                            : config['download_location']
                    );
                    value =
                        options['move_completed_toggle'] !== undefined
                            ? options['move_completed_toggle']
                            : config['move_completed'];
                    if (value) {
                        Ext.getCmp('move_completed_toggle').setValue(
                            options['move_completed_toggle'] !== undefined
                                ? options['move_completed_toggle']
                                : false
                        );
                        Ext.getCmp('move_completed_path').setValue(
                            options['move_completed_path'] !== undefined
                                ? options['move_completed_path']
                                : config['move_completed_path']
                        );
                    }
                    value =
                        options['copy_torrent_toggle'] !== undefined
                            ? options['copy_torrent_toggle']
                            : config['copy_torrent_file'];
                    if (value) {
                        Ext.getCmp('copy_torrent_toggle').setValue(true);
                        Ext.getCmp('copy_torrent').setValue(
                            options['copy_torrent'] !== undefined
                                ? options['copy_torrent']
                                : config['torrentfiles_location']
                        );
                    }
                    value =
                        options['delete_copy_torrent_toggle'] !== undefined
                            ? options['copy_torrent_toggle']
                            : config['del_copy_torrent_file'];
                    if (value) {
                        Ext.getCmp('delete_copy_torrent_toggle').setValue(true);
                    }
                },
            });
        }

        deluge.client.core.get_enabled_plugins({
            success: function (plugins) {
                if (plugins !== undefined && plugins.indexOf('Label') > -1) {
                    this.MainTab.LabelFset.setVisible(true);
                    deluge.client.label.get_labels({
                        success: function (labels) {
                            for (
                                var index = 0;
                                index < labels.length;
                                index++
                            ) {
                                labels[index] = [labels[index]];
                            }
                            this.labels.loadData(labels, false);
                        },
                        failure: function (failure) {
                            console.error(failure);
                        },
                        scope: this,
                    });
                } else {
                    this.MainTab.LabelFset.setVisible(false);
                }
            },
            scope: this,
        });

        var me = this;

        function on_accounts(accounts, owner) {
            for (var index = 0; index < accounts.length; index++) {
                accounts[index] = [accounts[index]['username']];
            }
            me.accounts.loadData(accounts, false);
            Ext.getCmp('owner').setValue(owner).enable();
        }

        function on_accounts_failure(failure) {
            deluge.client.autoadd.get_auth_user({
                success: function (user) {
                    me.accounts.loadData([[user]], false);
                    Ext.getCmp('owner').setValue(user).disable(true);
                },
                scope: this,
            });
        }

        deluge.client.autoadd.is_admin_level({
            success: function (is_admin) {
                if (is_admin) {
                    deluge.client.core.get_known_accounts({
                        success: function (accounts) {
                            deluge.client.autoadd.get_auth_user({
                                success: function (user) {
                                    on_accounts(
                                        accounts,
                                        options['owner'] !== undefined
                                            ? options['owner']
                                            : user
                                    );
                                },
                                scope: this,
                            });
                        },
                        failure: on_accounts_failure,
                        scope: this,
                    });
                } else {
                    on_accounts_failure(null);
                }
            },
            scope: this,
        });
    },
});

/**
 * @class Deluge.ux.AutoAdd.EditAutoAddCommandWindow
 * @extends Deluge.ux.AutoAdd.AutoAddWindowBase
 */
Deluge.ux.AutoAdd.EditAutoAddCommandWindow = Ext.extend(
    Deluge.ux.AutoAdd.AutoAddWindowBase,
    {
        title: _('Edit Watch Folder'),

        initComponent: function () {
            Deluge.ux.AutoAdd.EditAutoAddCommandWindow.superclass.initComponent.call(
                this
            );
            this.addButton(_('Save'), this.onSaveClick, this);
            this.addEvents({
                watchdiredit: true,
            });
        },

        show: function (watchdir_id, options) {
            Deluge.ux.AutoAdd.EditAutoAddCommandWindow.superclass.show.call(
                this
            );
            this.watchdir_id = watchdir_id;
            this.loadOptions(options);
        },

        onSaveClick: function () {
            try {
                var options = this.getOptions();
                deluge.client.autoadd.set_options(this.watchdir_id, options, {
                    success: function () {
                        this.fireEvent('watchdiredit', this, options);
                    },
                    scope: this,
                });
            } catch (err) {
                Ext.Msg.show({
                    title: _('Incompatible Option'),
                    msg: err,
                    buttons: Ext.Msg.OK,
                    scope: this,
                });
            }

            this.hide();
        },
    }
);

/**
 * @class Deluge.ux.AutoAdd.AddAutoAddCommandWindow
 * @extends Deluge.ux.AutoAdd.AutoAddWindowBase
 */
Deluge.ux.AutoAdd.AddAutoAddCommandWindow = Ext.extend(
    Deluge.ux.AutoAdd.AutoAddWindowBase,
    {
        title: _('Add Watch Folder'),

        initComponent: function () {
            Deluge.ux.AutoAdd.AddAutoAddCommandWindow.superclass.initComponent.call(
                this
            );
            this.addButton(_('Add'), this.onAddClick, this);
            this.addEvents({
                watchdiradd: true,
            });
        },

        show: function () {
            Deluge.ux.AutoAdd.AddAutoAddCommandWindow.superclass.show.call(
                this
            );
            this.loadOptions();
        },

        onAddClick: function () {
            var options = this.getOptions();
            deluge.client.autoadd.add(options, {
                success: function () {
                    this.fireEvent('watchdiradd', this, options);
                    this.hide();
                },
                failure: function (err) {
                    const regex = /: (.*\n)\n?\]/m;
                    var error;
                    if ((error = regex.exec(err.error.message)) !== null) {
                        error = error[1];
                    } else {
                        error = err.error.message;
                    }
                    Ext.Msg.show({
                        title: _('Incompatible Option'),
                        msg: error,
                        buttons: Ext.Msg.OK,
                        scope: this,
                    });
                },
                scope: this,
            });
        },
    }
);
