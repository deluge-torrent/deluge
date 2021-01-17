/**
 * Deluge.ConnectionManager.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Deluge.ConnectionManager = Ext.extend(Ext.Window, {
    layout: 'fit',
    width: 300,
    height: 220,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'right',
    closeAction: 'hide',
    closable: true,
    plain: true,
    constrainHeader: true,
    title: _('Connection Manager'),
    iconCls: 'x-deluge-connect-window-icon',

    initComponent: function () {
        Deluge.ConnectionManager.superclass.initComponent.call(this);
        this.on('hide', this.onHide, this);
        this.on('show', this.onShow, this);

        deluge.events.on('login', this.onLogin, this);
        deluge.events.on('logout', this.onLogout, this);

        this.addButton(_('Close'), this.onClose, this);
        this.addButton(_('Connect'), this.onConnect, this);

        this.list = new Ext.list.ListView({
            store: new Ext.data.ArrayStore({
                fields: [
                    { name: 'status', mapping: 4 },
                    { name: 'host', mapping: 1 },
                    { name: 'port', mapping: 2 },
                    { name: 'user', mapping: 3 },
                    { name: 'version', mapping: 5 },
                ],
                id: 0,
            }),
            columns: [
                {
                    header: _('Status'),
                    width: 0.24,
                    sortable: true,
                    tpl: new Ext.XTemplate(
                        '<tpl if="status == \'Online\'">',
                        _('Online'),
                        '</tpl>',
                        '<tpl if="status == \'Offline\'">',
                        _('Offline'),
                        '</tpl>',
                        '<tpl if="status == \'Connected\'">',
                        _('Connected'),
                        '</tpl>'
                    ),
                    dataIndex: 'status',
                },
                {
                    id: 'host',
                    header: _('Host'),
                    width: 0.51,
                    sortable: true,
                    tpl: '{user}@{host}:{port}',
                    dataIndex: 'host',
                },
                {
                    header: _('Version'),
                    width: 0.25,
                    sortable: true,
                    tpl: '<tpl if="version">{version}</tpl>',
                    dataIndex: 'version',
                },
            ],
            singleSelect: true,
            listeners: {
                selectionchange: { fn: this.onSelectionChanged, scope: this },
            },
        });

        this.panel = this.add({
            autoScroll: true,
            items: [this.list],
            bbar: new Ext.Toolbar({
                buttons: [
                    {
                        id: 'cm-add',
                        cls: 'x-btn-text-icon',
                        text: _('Add'),
                        iconCls: 'icon-add',
                        handler: this.onAddClick,
                        scope: this,
                    },
                    {
                        id: 'cm-edit',
                        cls: 'x-btn-text-icon',
                        text: _('Edit'),
                        iconCls: 'icon-edit',
                        handler: this.onEditClick,
                        scope: this,
                    },
                    {
                        id: 'cm-remove',
                        cls: 'x-btn-text-icon',
                        text: _('Remove'),
                        iconCls: 'icon-remove',
                        handler: this.onRemoveClick,
                        disabled: true,
                        scope: this,
                    },
                    '->',
                    {
                        id: 'cm-stop',
                        cls: 'x-btn-text-icon',
                        text: _('Stop Daemon'),
                        iconCls: 'icon-error',
                        handler: this.onStopClick,
                        disabled: true,
                        scope: this,
                    },
                ],
            }),
        });
        this.update = this.update.createDelegate(this);
    },

    /**
     * Check to see if the the web interface is currently connected
     * to a Deluge Daemon and show the Connection Manager if not.
     */
    checkConnected: function () {
        deluge.client.web.connected({
            success: function (connected) {
                if (connected) {
                    deluge.events.fire('connect');
                } else {
                    this.show();
                }
            },
            scope: this,
        });
    },

    disconnect: function (show) {
        deluge.events.fire('disconnect');
        if (show) {
            if (this.isVisible()) return;
            this.show();
        }
    },

    loadHosts: function () {
        deluge.client.web.get_hosts({
            success: this.onGetHosts,
            scope: this,
        });
    },

    update: function () {
        this.list.getStore().each(function (r) {
            deluge.client.web.get_host_status(r.id, {
                success: this.onGetHostStatus,
                scope: this,
            });
        }, this);
    },

    /**
     * Updates the buttons in the Connection Manager UI according to the
     * passed in records host state.
     * @param {Ext.data.Record} record The hosts record to update the UI for
     */
    updateButtons: function (record) {
        var button = this.buttons[1],
            status = record.get('status');

        // Update the Connect/Disconnect button
        button.enable();
        if (status.toLowerCase() == 'connected') {
            button.setText(_('Disconnect'));
        } else {
            button.setText(_('Connect'));
            if (status.toLowerCase() != 'online') button.disable();
        }

        // Update the Stop/Start Daemon button
        if (
            status.toLowerCase() == 'connected' ||
            status.toLowerCase() == 'online'
        ) {
            this.stopHostButton.enable();
            this.stopHostButton.setText(_('Stop Daemon'));
        } else {
            if (
                record.get('host') == '127.0.0.1' ||
                record.get('host') == 'localhost'
            ) {
                this.stopHostButton.enable();
                this.stopHostButton.setText(_('Start Daemon'));
            } else {
                this.stopHostButton.disable();
            }
        }
    },

    // private
    onAddClick: function (button, e) {
        if (!this.addWindow) {
            this.addWindow = new Deluge.AddConnectionWindow();
            this.addWindow.on('hostadded', this.onHostChange, this);
        }
        this.addWindow.show();
    },

    // private
    onEditClick: function (button, e) {
        var connection = this.list.getSelectedRecords()[0];
        if (!connection) return;

        if (!this.editWindow) {
            this.editWindow = new Deluge.EditConnectionWindow();
            this.editWindow.on('hostedited', this.onHostChange, this);
        }
        this.editWindow.show(connection);
    },

    // private
    onHostChange: function () {
        this.loadHosts();
    },

    // private
    onClose: function (e) {
        this.hide();
    },

    // private
    onConnect: function (e) {
        var selected = this.list.getSelectedRecords()[0];
        if (!selected) return;

        var me = this;
        var disconnect = function () {
            deluge.client.web.disconnect({
                success: function (result) {
                    this.update(this);
                    deluge.events.fire('disconnect');
                },
                scope: me,
            });
        };

        if (selected.get('status').toLowerCase() == 'connected') {
            disconnect();
        } else {
            if (
                this.list
                    .getStore()
                    .find('status', 'Connected', 0, false, false) > -1
            ) {
                disconnect();
            }

            var id = selected.id;
            deluge.client.web.connect(id, {
                success: function (methods) {
                    deluge.client.reloadMethods();
                    deluge.client.on(
                        'connected',
                        function (e) {
                            deluge.events.fire('connect');
                        },
                        this,
                        { single: true }
                    );
                },
            });
            this.hide();
        }
    },

    // private
    onGetHosts: function (hosts) {
        this.list.getStore().loadData(hosts);
        Ext.each(
            hosts,
            function (host) {
                deluge.client.web.get_host_status(host[0], {
                    success: this.onGetHostStatus,
                    scope: this,
                });
            },
            this
        );
    },

    // private
    onGetHostStatus: function (host) {
        var record = this.list.getStore().getById(host[0]);
        record.set('status', host[1]);
        record.set('version', host[2]);
        record.commit();
        var selected = this.list.getSelectedRecords()[0];
        if (!selected) return;
        if (selected == record) this.updateButtons(record);
    },

    // private
    onHide: function () {
        if (this.running) window.clearInterval(this.running);
    },

    // private
    onLogin: function () {
        if (deluge.config.first_login) {
            Ext.MessageBox.confirm(
                _('Change Default Password'),
                _(
                    'We recommend changing the default password.<br><br>Would you like to change it now?'
                ),
                function (res) {
                    this.checkConnected();
                    if (res == 'yes') {
                        deluge.preferences.show();
                        deluge.preferences.selectPage('Interface');
                    }
                    deluge.client.web.set_config({ first_login: false });
                },
                this
            );
        } else {
            this.checkConnected();
        }
    },

    // private
    onLogout: function () {
        this.disconnect();
        if (!this.hidden && this.rendered) {
            this.hide();
        }
    },

    // private
    onRemoveClick: function (button) {
        var connection = this.list.getSelectedRecords()[0];
        if (!connection) return;

        deluge.client.web.remove_host(connection.id, {
            success: function (result) {
                if (!result) {
                    Ext.MessageBox.show({
                        title: _('Error'),
                        msg: result[1],
                        buttons: Ext.MessageBox.OK,
                        modal: false,
                        icon: Ext.MessageBox.ERROR,
                        iconCls: 'x-deluge-icon-error',
                    });
                } else {
                    this.list.getStore().remove(connection);
                }
            },
            scope: this,
        });
    },

    // private
    onSelectionChanged: function (list, selections) {
        if (selections[0]) {
            this.editHostButton.enable();
            this.removeHostButton.enable();
            this.stopHostButton.enable();
            this.stopHostButton.setText(_('Stop Daemon'));
            this.updateButtons(this.list.getRecord(selections[0]));
        } else {
            this.editHostButton.disable();
            this.removeHostButton.disable();
            this.stopHostButton.disable();
        }
    },

    // FIXME: Find out why this is being fired twice
    // private
    onShow: function () {
        if (!this.addHostButton) {
            var bbar = this.panel.getBottomToolbar();
            this.addHostButton = bbar.items.get('cm-add');
            this.editHostButton = bbar.items.get('cm-edit');
            this.removeHostButton = bbar.items.get('cm-remove');
            this.stopHostButton = bbar.items.get('cm-stop');
        }
        this.loadHosts();
        if (this.running) return;
        this.running = window.setInterval(this.update, 2000, this);
    },

    // private
    onStopClick: function (button, e) {
        var connection = this.list.getSelectedRecords()[0];
        if (!connection) return;

        if (connection.get('status') == 'Offline') {
            // This means we need to start the daemon
            deluge.client.web.start_daemon(connection.get('port'));
        } else {
            // This means we need to stop the daemon
            deluge.client.web.stop_daemon(connection.id, {
                success: function (result) {
                    if (!result[0]) {
                        Ext.MessageBox.show({
                            title: _('Error'),
                            msg: result[1],
                            buttons: Ext.MessageBox.OK,
                            modal: false,
                            icon: Ext.MessageBox.ERROR,
                            iconCls: 'x-deluge-icon-error',
                        });
                    }
                },
            });
        }
    },
});
