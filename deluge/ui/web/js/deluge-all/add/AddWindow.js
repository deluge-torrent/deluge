/*!
 * Deluge.add.AddWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
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

Ext.namespace('Deluge.add');

// This override allows file upload buttons to contain icons
Ext.override(Ext.ux.form.FileUploadField, {
    onRender : function(ct, position){
        Ext.ux.form.FileUploadField.superclass.onRender.call(this, ct, position);

        this.wrap = this.el.wrap({cls:'x-form-field-wrap x-form-file-wrap'});
        this.el.addClass('x-form-file-text');
        this.el.dom.removeAttribute('name');
        this.createFileInput();

        var btnCfg = Ext.applyIf(this.buttonCfg || {}, {
            text: this.buttonText
        });
        this.button = new Ext.Button(Ext.apply(btnCfg, {
            renderTo: this.wrap,
            cls: 'x-form-file-btn' + (btnCfg.iconCls ? ' x-btn-text-icon' : '')
        }));

        if(this.buttonOnly){
            this.el.hide();
            this.wrap.setWidth(this.button.getEl().getWidth());
        }

        this.bindListeners();
        this.resizeEl = this.positionEl = this.wrap;
    }
});

Deluge.add.AddWindow = Ext.extend(Deluge.add.Window, {
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
        Deluge.add.AddWindow.superclass.initComponent.call(this);

        this.addButton(_('Cancel'), this.onCancelClick, this);
        this.addButton(_('Add'), this.onAddClick, this);

        function torrentRenderer(value, p, r) {
            if (r.data['info_hash']) {
                return String.format('<div class="x-deluge-add-torrent-name">{0}</div>', value);
            } else {
                return String.format('<div class="x-deluge-add-torrent-name-loading">{0}</div>', value);
            }
        }

        this.list = new Ext.list.ListView({
            store: new Ext.data.SimpleStore({
                fields: [
                    {name: 'info_hash', mapping: 1},
                    {name: 'text', mapping: 2}
                ],
                id: 0
            }),
            columns: [{
                id: 'torrent',
                width: 150,
                sortable: true,
                renderer: torrentRenderer,
                dataIndex: 'text'
            }],
            stripeRows: true,
            singleSelect: true,
            listeners: {
                'selectionchange': {
                    fn: this.onSelect,
                    scope: this
                }
            },
            hideHeaders: true,
            autoExpandColumn: 'torrent',
            height: '100%',
            autoScroll: true
        });

        this.add({
            region: 'center',
            items: [this.list],
            margins: '5 5 5 5',
            bbar: new Ext.Toolbar({
                items: [{
                    id: 'fileUploadForm',
                    xtype: 'form',
                    layout: 'fit',
                    baseCls: 'x-plain',
                    fileUpload: true,
                    items: [{
                        buttonOnly: true,
                        xtype: 'fileuploadfield',
                        id: 'torrentFile',
                        name: 'file',
                        buttonCfg: {
                            iconCls: 'x-deluge-add-file',
                            text: _('File')
                        },
                        listeners: {
                            scope: this,
                            'fileselected': this.onFileSelected
                        }
                    }]
                }, {
                    text: _('Url'),
                    iconCls: 'icon-add-url',
                    handler: this.onUrl,
                    scope: this
                }, {
                    text: _('Infohash'),
                    iconCls: 'icon-add-magnet',
                    hidden: true,
                    disabled: true
                }, '->', {
                    text: _('Remove'),
                    iconCls: 'icon-remove',
                    handler: this.onRemove,
                    scope: this
                }]
            })
        });

        this.fileUploadForm = Ext.getCmp('fileUploadForm').getForm();
        this.optionsPanel = this.add(new Deluge.add.OptionsPanel());
        this.on('hide', this.onHide, this);
        this.on('show', this.onShow, this);
    },

    clear: function() {
        this.list.getStore().removeAll();
        this.optionsPanel.clear();
        // Reset upload form so handler fires when a canceled file is reselected
        this.fileUploadForm.reset();
    },

    onAddClick: function() {
        var torrents = [];
        if (!this.list) return;
        this.list.getStore().each(function(r) {
            var id = r.get('info_hash');
            torrents.push({
                path: this.optionsPanel.getFilename(id),
                options: this.optionsPanel.getOptions(id)
            });
        }, this);

        deluge.client.web.add_torrents(torrents, {
            success: function(result) {
            }
        });
        this.clear();
        this.hide();
    },

    onCancelClick: function() {
        this.clear();
        this.hide();
    },

    onFile: function() {
        if (!this.file) this.file = new Deluge.add.FileWindow();
        this.file.show();
    },

    onHide: function() {
        this.optionsPanel.setActiveTab(0);
        this.optionsPanel.files.setDisabled(true);
        this.optionsPanel.form.setDisabled(true);
    },

    onRemove: function() {
        if (!this.list.getSelectionCount()) return;
        var torrent = this.list.getSelectedRecords()[0];
        this.list.getStore().remove(torrent);
        this.optionsPanel.clear();

        if (this.torrents && this.torrents[torrent.id]) delete this.torrents[torrent.id];
    },

    onSelect: function(list, selections) {
        if (selections.length) {
            var record = this.list.getRecord(selections[0]);
            this.optionsPanel.setTorrent(record.get('info_hash'));
        } else {
            this.optionsPanel.files.setDisabled(true);
            this.optionsPanel.form.setDisabled(true);
        }
    },

    onShow: function() {
        if (!this.url) {
            this.url = new Deluge.add.UrlWindow();
            this.url.on('beforeadd', this.onTorrentBeforeAdd, this);
            this.url.on('add', this.onTorrentAdd, this);
        }

        this.optionsPanel.form.getDefaults();
    },

    onFileSelected: function() {
        if (this.fileUploadForm.isValid()) {
            this.torrentId = this.createTorrentId();
            this.fileUploadForm.submit({
                url: deluge.config.base + 'upload',
                waitMsg: _('Uploading your torrent...'),
                success: this.onUploadSuccess,
                scope: this
            });
            var name = this.fileUploadForm.findField('torrentFile').value;
            name = name.split('\\').slice(-1)[0];
            this.onTorrentBeforeAdd(this.torrentId, name);
        }
    },

    onUploadSuccess: function(fp, upload) {
        if (upload.result.success) {
            var filename = upload.result.files[0];
            this.fileUploadForm.findField('torrentFile').setValue('');
            deluge.client.web.get_torrent_info(filename, {
                success: this.onGotInfo,
                scope: this,
                filename: filename
            });
        }
    },

    onGotInfo: function(info, obj, response, request) {
        info.filename = request.options.filename;
        this.onTorrentAdd(this.torrentId, info);
    },

    onTorrentBeforeAdd: function(torrentId, text) {
        var store = this.list.getStore();
        store.loadData([[torrentId, null, text]], true);
    },

    onTorrentAdd: function(torrentId, info) {
        var r = this.list.getStore().getById(torrentId);
        if (!info) {
            Ext.MessageBox.show({
                title: _('Error'),
                msg: _('Not a valid torrent'),
                buttons: Ext.MessageBox.OK,
                modal: false,
                icon: Ext.MessageBox.ERROR,
                iconCls: 'x-deluge-icon-error'
            });
            this.list.getStore().remove(r);
        } else {
            r.set('info_hash', info['info_hash']);
            r.set('text', info['name']);
            this.list.getStore().commitChanges();
            this.optionsPanel.addTorrent(info);
            this.list.select(r);
        }
    },

    onUrl: function(button, event) {
        this.url.show();
    }
});
