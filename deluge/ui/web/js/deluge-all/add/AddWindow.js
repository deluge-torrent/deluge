/*!
 * Deluge.add.AddWindow.js
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

Ext.define('Deluge.add.AddWindow', {
    extend: 'Deluge.add.Window',

    title: _('Add Torrents'),
    layout: 'border',
    width: 470,
    height: 450,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'right',
    closeAction: 'hide',
    closable: true,
    plain: true,
    iconCls: 'x-deluge-add-window-icon',

    initComponent: function() {
        this.callParent(arguments);
        this.afterMethod('onHide', this.afterHidden, this);
        this.afterMethod('onShow', this.afterShown, this);

        this.addDocked({
            xtype: 'toolbar',
            dock: 'bottom',
            defaultType: 'button',
            items: [
                '->',
                {text: _('Cancel'), handler: this.onCancelClick, scope: this},
                {text: _('Add'), handler: this.onAddClick, scope: this}
            ]
        });

        function torrentRenderer(value, p, r) {
            if (r.data['info_hash']) {
                return Ext.String.format('<div class="x-deluge-add-torrent-name">{0}</div>', value);
            } else {
                return Ext.String.format('<div class="x-deluge-add-torrent-name-loading">{0}</div>', value);
            }
        }

        this.grid = this.add({
            xtype: 'grid',
            autoScroll: true,
            store: Ext.create('Ext.data.Store', {
                model: 'Deluge.data.AddTorrent'
            }),
            columns: [{
                id: 'torrent',
                width: 150,
                sortable: true,
                renderer: torrentRenderer,
                dataIndex: 'text',
                flex: 1
            }],
            hideHeaders: true,
            margins: '5 5 5 5',
            region: 'center',
            singleSelect: true,
            listeners: {
                'selectionchange': {
                    fn: this.onSelect,
                    scope: this
                },
                'render': {
                    fn: function(list) {
                        var el = list.getEl(),
                            dh = Ext.core.DomHelper,
                            dropEl = {
                                tag: 'div',
                                cls: 'x-deluge-dropzone',
                                style: 'display: none',
                                html: 'Drop torrent file here'
                            };
                        this.dropEl = Ext.get(dh.insertFirst(el, dropEl));
                    },
                    scope: this
                }
            },
            bbar: {
                items: [{
                    iconCls: 'x-deluge-add-file',
                    text: _('File'),
                    handler: this.onFile,
                    scope: this
                }, {
                    text: _('Url'),
                    iconCls: 'icon-add-url',
                    handler: this.onUrl,
                    scope: this
                }, {
                    text: _('Infohash'),
                    iconCls: 'icon-add-magnet',
                    disabled: true
                }, '->', {
                    text: _('Remove'),
                    iconCls: 'icon-remove',
                    handler: this.onRemove,
                    scope: this
                }]
            }
        });

        this.optionsPanel = this.add(Ext.create('Deluge.add.OptionsPanel'));
    },

    clear: function() {
        this.grid.getStore().removeAll();
        this.optionsPanel.clear();
    },

    processDnDFileUpload: function(file) {
        console.log(file.size);
    },

    onAddClick: function() {
        var torrents = [];
        if (!this.grid) return;
        this.grid.getStore().each(function(r) {
            var id = r.get('info_hash');
            torrents.push({
                path: this.optionsPanel.getFilename(id),
                options: this.optionsPanel.getOptions(id)
            });
        }, this);

        deluge.client.web.add_torrents(torrents, {
            success: function(result) {
            }
        })
        this.clear();
        this.hide();
    },

    onCancelClick: function() {
        this.clear();
        this.hide();
    },

    onFile: function() {
        if (!this.file) this.file = Ext.create('Deluge.add.FileWindow');
        this.file.show();
    },

    onRemove: function() {
        if (!this.list.getSelectionCount()) return;
        var torrent = this.grid.getSelectedRecords()[0];
        this.grid.getStore().remove(torrent);
        this.optionsPanel.clear();

        if (this.torrents && this.torrents[torrent.id]) delete this.torrents[torrent.id];
    },

    onSelect: function(grid, selections) {
        if (selections.length) {
            var record = selections[0];
            this.optionsPanel.setTorrent(record.get('info_hash'));
            this.optionsPanel.files.setDisabled(false);
            this.optionsPanel.form.setDisabled(false);
        } else {
            this.optionsPanel.files.setDisabled(true);
            this.optionsPanel.form.setDisabled(true);
        }
    },

    afterHidden: function() {
        this.optionsPanel.setActiveTab(0);
        this.optionsPanel.files.setDisabled(true);
        this.optionsPanel.form.setDisabled(true);
    },

    afterShown: function() {
        if (!this.url) {
            this.url = Ext.create('Deluge.add.UrlWindow');
            this.url.on('beforeadd', this.onTorrentBeforeAdd, this);
            this.url.on('add', this.onTorrentAdd, this);
        }

        if (!this.file) {
            this.file = Ext.create('Deluge.add.FileWindow');
            this.file.on('beforeadd', this.onTorrentBeforeAdd, this);
            this.file.on('add', this.onTorrentAdd, this);
        }

        this.optionsPanel.form.getDefaults();

        var body = Ext.getBody(),
            dropEl = this.dropEl;

        body.on({
            dragenter: function(evt) {
                dropEl.setStyle('display', 'block');
                return true;
            },
            dragleave: function(evt) {
                var viewSize = body.getViewSize(),
                    pageX = evt.getPageX(),
                    pageY = evt.getPageY();
                if (pageX < 10 || pageY < 10 || viewSize.width - pageX < 10  || viewSize.height - pageY < 10) {
                    dropEl.setStyle('display', 'none');
                }
                return true;
            },
            dragover: function(evt) {
                evt.stopEvent();
                return true;
            },
            drop: function(evt) {
                evt.stopEvent();
                return true;
            }
        });

        this.dropEl.on({
            dragenter: function(evt) {
                evt.browserEvent.dataTransfer.dropEffect = 'move';
                return true;
            },
            dragover: function(evt) {
                evt.browserEvent.dataTransfer.dropEffect = 'move';
                evt.stopEvent();
                return true;
            },
            drop: {
                fn: function(evt) {
                    evt.stopEvent();
                    var files = evt.browserEvent.dataTransfer.files;

                    if (files === undefined) {
                        return true;
                    }
                    var len = files.length;
                    while (--len >= 0) {
                        this.processDnDFileUpload(files[len]);
                    }
                    this.dropEl.setStyle('display', 'none');
                },
                scope: this
            }
        });
    },

    onTorrentBeforeAdd: function(torrentId, text) {
        var rec = Ext.create('Deluge.data.AddTorrent', {
            'id':        torrentId,
            'info_hash': null,
            'text':      text

        }, torrentId);
        this.grid.getStore().add(rec);
    },

    onTorrentAdd: function(torrentId, info) {
        var r = this.grid.getStore().getById(String(torrentId));
        if (!info) {
            Ext.MessageBox.show({
                title: _('Error'),
                msg: _('Not a valid torrent'),
                buttons: Ext.MessageBox.OK,
                modal: false,
                icon: Ext.MessageBox.ERROR,
                iconCls: 'x-deluge-icon-error'
            });
            this.grid.getStore().remove(r);
        } else {
            r.set('info_hash', info['info_hash']);
            r.set('text', info['name']);
            r.commit();;
            this.optionsPanel.addTorrent(info);
        }
    },

    onUrl: function(button, event) {
        this.url.show();
    }
});
