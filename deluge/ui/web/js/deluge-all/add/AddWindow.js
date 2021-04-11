/**
 * Deluge.add.AddWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Ext.namespace('Deluge.add');

// This override allows file upload buttons to contain icons
Ext.override(Ext.ux.form.FileUploadField, {
    onRender: function (ct, position) {
        Ext.ux.form.FileUploadField.superclass.onRender.call(
            this,
            ct,
            position
        );

        this.wrap = this.el.wrap({ cls: 'x-form-field-wrap x-form-file-wrap' });
        this.el.addClass('x-form-file-text');
        this.el.dom.removeAttribute('name');
        this.createFileInput();

        var btnCfg = Ext.applyIf(this.buttonCfg || {}, {
            text: this.buttonText,
        });
        this.button = new Ext.Button(
            Ext.apply(btnCfg, {
                renderTo: this.wrap,
                cls:
                    'x-form-file-btn' +
                    (btnCfg.iconCls ? ' x-btn-text-icon' : ''),
            })
        );

        if (this.buttonOnly) {
            this.el.hide();
            this.wrap.setWidth(this.button.getEl().getWidth());
        }

        this.bindListeners();
        this.resizeEl = this.positionEl = this.wrap;
    },
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

    initComponent: function () {
        Deluge.add.AddWindow.superclass.initComponent.call(this);

        this.addButton(_('Cancel'), this.onCancelClick, this);
        this.addButton(_('Add'), this.onAddClick, this);

        function torrentRenderer(value, p, r) {
            if (r.data['info_hash']) {
                return String.format(
                    '<div class="x-deluge-add-torrent-name">{0}</div>',
                    value
                );
            } else {
                return String.format(
                    '<div class="x-deluge-add-torrent-name-loading">{0}</div>',
                    value
                );
            }
        }

        this.list = new Ext.list.ListView({
            store: new Ext.data.SimpleStore({
                fields: [
                    { name: 'info_hash', mapping: 1 },
                    { name: 'text', mapping: 2 },
                ],
                id: 0,
            }),
            columns: [
                {
                    id: 'torrent',
                    width: 150,
                    sortable: true,
                    renderer: torrentRenderer,
                    dataIndex: 'text',
                },
            ],
            stripeRows: true,
            singleSelect: true,
            listeners: {
                selectionchange: {
                    fn: this.onSelect,
                    scope: this,
                },
            },
            hideHeaders: true,
            autoExpandColumn: 'torrent',
            height: '100%',
            autoScroll: true,
        });

        this.add({
            region: 'center',
            items: [this.list],
            border: false,
            bbar: new Ext.Toolbar({
                items: [
                    {
                        id: 'fileUploadForm',
                        xtype: 'form',
                        layout: 'fit',
                        baseCls: 'x-plain',
                        fileUpload: true,
                        items: [
                            {
                                buttonOnly: true,
                                xtype: 'fileuploadfield',
                                id: 'torrentFile',
                                name: 'file',
                                multiple: true,
                                buttonCfg: {
                                    iconCls: 'x-deluge-add-file',
                                    text: _('File'),
                                },
                                listeners: {
                                    scope: this,
                                    fileselected: this.onFileSelected,
                                },
                            },
                        ],
                    },
                    {
                        text: _('Url'),
                        iconCls: 'icon-add-url',
                        handler: this.onUrl,
                        scope: this,
                    },
                    {
                        text: _('Infohash'),
                        iconCls: 'icon-magnet-add',
                        hidden: true,
                        disabled: true,
                    },
                    '->',
                    {
                        text: _('Remove'),
                        iconCls: 'icon-remove',
                        handler: this.onRemove,
                        scope: this,
                    },
                ],
            }),
        });

        this.fileUploadForm = Ext.getCmp('fileUploadForm').getForm();
        this.optionsPanel = this.add(new Deluge.add.OptionsPanel());
        this.on('hide', this.onHide, this);
        this.on('show', this.onShow, this);
    },

    clear: function () {
        this.list.getStore().removeAll();
        this.optionsPanel.clear();
        // Reset upload form so handler fires when a canceled file is reselected
        this.fileUploadForm.reset();
    },

    onAddClick: function () {
        var torrents = [];
        if (!this.list) return;
        this.list.getStore().each(function (r) {
            var id = r.get('info_hash');
            torrents.push({
                path: this.optionsPanel.getFilename(id),
                options: this.optionsPanel.getOptions(id),
            });
        }, this);

        deluge.client.web.add_torrents(torrents, {
            success: function (result) {},
        });
        this.clear();
        this.hide();
    },

    onCancelClick: function () {
        this.clear();
        this.hide();
    },

    onFile: function () {
        if (!this.file) this.file = new Deluge.add.FileWindow();
        this.file.show();
    },

    onHide: function () {
        this.optionsPanel.setActiveTab(0);
        this.optionsPanel.files.setDisabled(true);
        this.optionsPanel.form.setDisabled(true);
    },

    onRemove: function () {
        if (!this.list.getSelectionCount()) return;
        var torrent = this.list.getSelectedRecords()[0];
        if (!torrent) return;
        this.list.getStore().remove(torrent);
        this.optionsPanel.clear();

        if (this.torrents && this.torrents[torrent.id])
            delete this.torrents[torrent.id];
    },

    onSelect: function (list, selections) {
        if (selections.length) {
            var record = this.list.getRecord(selections[0]);
            this.optionsPanel.setTorrent(record.get('info_hash'));
        } else {
            this.optionsPanel.files.setDisabled(true);
            this.optionsPanel.form.setDisabled(true);
        }
    },

    onShow: function () {
        if (!this.url) {
            this.url = new Deluge.add.UrlWindow();
            this.url.on('beforeadd', this.onTorrentBeforeAdd, this);
            this.url.on('add', this.onTorrentAdd, this);
            this.url.on('addfailed', this.onTorrentAddFailed, this);
        }

        this.optionsPanel.form.getDefaults();
    },

    onFileSelected: function () {
        if (this.fileUploadForm.isValid()) {
            var torrentIds = [];
            var files = this.fileUploadForm.findField('torrentFile').value;
            var randomId = this.createTorrentId();
            Array.prototype.forEach.call(
                files,
                function (file, i) {
                    // Append index for batch of unique torrentIds.
                    var torrentId = randomId + i.toString();
                    torrentIds.push(torrentId);
                    this.onTorrentBeforeAdd(torrentId, file.name);
                }.bind(this)
            );
            this.fileUploadForm.submit({
                url: deluge.config.base + 'upload',
                waitMsg: _('Uploading your torrent...'),
                success: this.onUploadSuccess,
                failure: this.onUploadFailure,
                scope: this,
                torrentIds: torrentIds,
            });
        }
    },

    onUploadSuccess: function (fp, upload) {
        if (!upload.result.success) {
            this.clear();
            return;
        }

        upload.result.files.forEach(
            function (filename, i) {
                deluge.client.web.get_torrent_info(filename, {
                    success: this.onGotInfo,
                    scope: this,
                    filename: filename,
                    torrentId: upload.options.torrentIds[i],
                });
            }.bind(this)
        );
        this.fileUploadForm.reset();
    },

    onUploadFailure: function (form, action) {
        this.hide();
        Ext.MessageBox.show({
            title: _('Error'),
            msg: _('Failed to upload torrent'),
            buttons: Ext.MessageBox.OK,
            modal: false,
            icon: Ext.MessageBox.ERROR,
            iconCls: 'x-deluge-icon-error',
        });
        this.fireEvent('addfailed', this.torrentId);
    },

    onGotInfo: function (info, obj, response, request) {
        info.filename = request.options.filename;
        torrentId = request.options.torrentId;
        this.onTorrentAdd(torrentId, info);
    },

    onTorrentBeforeAdd: function (torrentId, text) {
        var store = this.list.getStore();
        store.loadData([[torrentId, null, text]], true);
    },

    onTorrentAdd: function (torrentId, info) {
        var r = this.list.getStore().getById(torrentId);
        if (!info) {
            Ext.MessageBox.show({
                title: _('Error'),
                msg: _('Not a valid torrent'),
                buttons: Ext.MessageBox.OK,
                modal: false,
                icon: Ext.MessageBox.ERROR,
                iconCls: 'x-deluge-icon-error',
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

    onTorrentAddFailed: function (torrentId) {
        var store = this.list.getStore();
        var torrentRecord = store.getById(torrentId);
        if (torrentRecord) {
            store.remove(torrentRecord);
        }
    },

    onUrl: function (button, event) {
        this.url.show();
    },
});
