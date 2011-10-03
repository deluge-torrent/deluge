/*!
 * Deluge.ConnectionManager.js
 *
 * Copyright (c) Damien Churchill 2009-2011 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */

Ext.define('Deluge.ConnectionManager', {
    extend: 'Ext.Window',

    layout: 'fit',
    width: 300,
    height: 220,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'right',
    closeAction: 'hide',
    closable: true,
    plain: true,
    title: _('Connection Manager'),
    iconCls: 'x-deluge-connect-window-icon',

    initComponent: function() {
        this.callParent(arguments);
        this.afterMethod('onHide', this.afterHide, this);
        this.afterMethod('onShow', this.afterShow, this);

        deluge.events.on('login', this.onLogin, this);
        deluge.events.on('logout', this.onLogout, this);

        this.addDocked({
            xtype: 'toolbar',
            dock: 'bottom',
            defaultType: 'button',
            items: [
                '->',
                {text: _('Close'), handler: this.onClose, scope: this},
                {text: _('Connect'), handler: this.onConnect, scope: this}
            ]
        });

        this.grid = this.add({
            xtype: 'grid',
            autoScroll: true,
            store: new Ext.data.Store({
                model: 'Deluge.data.Host',
                proxy: {
                    type: 'memory',
                    reader: {
                        type: 'json',
                        root: 'hosts',
                        idProperty: 'id'
                    }
                }
            }),
            columns: [{
                header: _('Status'),
                width: 70,
                sortable: true,
                dataIndex: 'status'
            }, {
                xtype: 'templatecolumn',
                flex: 1,
                header: _('Host'),
                sortable: true,
                tpl: '{host}:{port}'
            }, {
                xtype: 'templatecolumn',
                header: _('Version'),
                width: 70,
                sortable: true,
                tpl: '<tpl if="version">{version}</tpl>'
            }],
            singleSelect: true,
            listeners: {
                'selectionchange': {fn: this.onSelectionChanged, scope: this}
            },
            bbar: [
                {xtype: 'button', text: _('Add'), iconCls: 'icon-add', handler: this.onAddClick, scope: this},
                {xtype: 'button', text: _('Remove'), iconCls: 'icon-remove', handler: this.onRemoveClick, scope: this},
                '->',
                {xtype: 'button', text: _('Stop Daemon'), iconCls: 'icon-error', handler: this.onStopClick, scope: this, disabled: true}
            ]
        });

        this.update = this.update.bind(this);
    },

    /**
     * Check to see if the the web interface is currently connected
     * to a Deluge Daemon and show the Connection Manager if not.
     */
    checkConnected: function() {
        deluge.client.web.connected({
            success: function(connected) {
                if (connected) {
                    deluge.events.fire('connect');
                } else {
                    this.show();
                }
            },
            scope: this
        });
    },

    disconnect: function(show) {
        deluge.events.fire('disconnect');
        if (show) {
            if (this.isVisible()) return;
            this.show();
        }
    },

    loadHosts: function() {
        deluge.client.web.get_hosts({
            success: this.onGetHosts,
            scope: this
        });
    },

    update: function() {
        this.grid.getStore().each(function(r) {
            deluge.client.web.get_host_status(r.getId(), {
                success: this.onGetHostStatus,
                scope: this
            });
        }, this);
    },

    /**
     * Updates the buttons in the Connection Manager UI according to the
     * passed in records host state.
     * @param {Ext.data.Record} record The hosts record to update the UI for
     */
    updateButtons: function(record) {
        var btns = this.query('toolbar[dock=bottom] button'),
            btn = btns[4],
            s = record.get('status');

        // Update the Connect/Disconnect button
        if (s == _('Connected')) {
            btn.enable();
            btn.setText(_('Disconnect'));
        } else if (s == _('Offline')) {
            btn.disable();
        } else {
            btn.enable();
            btn.setText(_('Connect'));
        }

        // Update the Stop/Start Daemon button
        if (s == _('Offline')) {
            if (record.get('host') == '127.0.0.1' || record.get('host') == 'localhost') {
                this.stopHostButton.enable();
                this.stopHostButton.setText(_('Start Daemon'));
            } else {
                this.stopHostButton.disable();
            }
        } else {
            this.stopHostButton.enable();
            this.stopHostButton.setText(_('Stop Daemon'));
        }
    },

    // private
    onAddClick: function(button, e) {
        if (!this.addWindow) {
            this.addWindow = new Deluge.AddConnectionWindow();
            this.addWindow.on('hostadded', this.onHostAdded, this);
        }
        this.addWindow.show();
    },

    // private
    onHostAdded: function() {
        this.loadHosts();
    },

    // private
    onClose: function(e) {
        this.hide();
    },

    // private
    onConnect: function(e) {
        var sm = this.grid.getSelectionModel(),
            selected = sm.getLastSelected();

        if (!selected) return;

        if (selected.get('status') == _('Connected')) {
            deluge.client.web.disconnect({
                success: function(result) {
                    this.update(this);
                    deluge.events.fire('disconnect');
                },
                scope: this
            });
        } else {
            deluge.client.web.connect(selected.getId(), {
                success: function(methods) {
                    deluge.client.reloadMethods();
                    deluge.client.on('connected', function(e) {
                        deluge.events.fire('connect');
                    }, this, {single: true});
                }
            });
            this.hide();
        }
    },

    // private
    onGetHosts: function(hosts) {
        // FIXME: Why on earth do I need to do it like this?!
        var store = this.grid.getStore(),
            results = store.proxy.reader.readRecords(hosts);
        store.loadRecords(results.records);

        Ext.each(hosts, function(host) {
            deluge.client.web.get_host_status(host['id'], {
                success: this.onGetHostStatus,
                scope: this
            });
        }, this);
    },

    // private
    onGetHostStatus: function(host) {
        var record = this.grid.getStore().getById(host['id']);
        record.set('status', host['status'])
        record.set('version', host['version'])
        record.commit();

        if (this.grid.getSelectionModel().isSelected(record)) {
            this.updateButtons(record);
        }
    },

    // private
    afterHide: function() {
        if (this.running) window.clearInterval(this.running);
    },

    // private
    onLogin: function() {
        if (deluge.config.first_login) {
            Ext.MessageBox.confirm('Change password',
                'As this is your first login, we recommend that you ' +
                'change your password. Would you like to ' +
                'do this now?', function(res) {
                    this.checkConnected();
                    if (res == 'yes') {
                        deluge.preferences.show();
                        deluge.preferences.selectPage('Interface');
                    }
                    deluge.client.web.set_config({first_login: false});
                }, this);
        } else {
            this.checkConnected();
        }
    },

    // private
    onLogout: function() {
        this.disconnect();
        if (!this.hidden && this.rendered) {
            this.hide();
        }
    },

    // private
    onRemoveClick: function(button) {
        var sm = this.grid.getSelectionModel(),
            selected = sm.getLastSelected();

        if (!selected) return;

        deluge.client.web.remove_host(selected.getId(), {
            success: function(result) {
                if (!result) {
                    Ext.MessageBox.show({
                        title: _('Error'),
                        msg: result[1],
                        buttons: Ext.MessageBox.OK,
                        modal: false,
                        icon: Ext.MessageBox.ERROR,
                        iconCls: 'x-deluge-icon-error'
                    });
                } else {
                    this.grid.getStore().remove(selected);
                }
            },
            scope: this
        });
    },

    // private
    onSelectionChanged: function(grid, selections) {
        if (selections[0]) {
            this.removeHostButton.enable();
            this.stopHostButton.enable();
            this.stopHostButton.setText(_('Stop Daemon'));
            this.updateButtons(selections[0]);
        } else {
            this.removeHostButton.disable();
            this.stopHostButton.disable();
        }
    },

    // FIXME: Find out why this is being fired twice
    // private
    afterShow: function() {
        if (!this.addHostButton) {
            var buttons = this.grid.query('button');
            this.addHostButton = buttons[0];
            this.removeHostButton = buttons[1];
            this.stopHostButton = buttons[2];
        }
        this.loadHosts();
        if (this.running) return;
        this.running = window.setInterval(this.update, 2000, this);
    },

    // private
    onStopClick: function(button, e) {
        var sm = this.grid.getSelectionModel(),
            selected = sm.getLastSelected();
        if (!selected) return;

        if (selected.get('status') == 'Offline') {
            // This means we need to start the daemon
            deluge.client.web.start_daemon(selected.get('port'));
        } else {
            // This means we need to stop the daemon
            deluge.client.web.stop_daemon(selected.getId(), {
                success: function(result) {
                    if (!result[0]) {
                        Ext.MessageBox.show({
                            title: _('Error'),
                            msg: result[1],
                            buttons: Ext.MessageBox.OK,
                            modal: false,
                            icon: Ext.MessageBox.ERROR,
                            iconCls: 'x-deluge-icon-error'
                        });
                    }
                }
            });
        }
    }
});
