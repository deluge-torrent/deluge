/**
 * Deluge.preferences.InstallPluginWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.InstallPluginWindow
 * @extends Ext.Window
 */
Deluge.preferences.InstallPluginWindow = Ext.extend(Ext.Window, {
    title: _('Install Plugin'),
    layout: 'fit',
    height: 115,
    width: 350,
    constrainHeader: true,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'center',
    closeAction: 'hide',
    iconCls: 'x-deluge-install-plugin',
    modal: true,
    plain: true,

    initComponent: function () {
        Deluge.preferences.InstallPluginWindow.superclass.initComponent.call(
            this
        );
        this.addButton(_('Install'), this.onInstall, this);

        this.form = this.add({
            xtype: 'form',
            baseCls: 'x-plain',
            labelWidth: 70,
            autoHeight: true,
            fileUpload: true,
            items: [
                {
                    xtype: 'fileuploadfield',
                    width: 240,
                    emptyText: _('Select an egg'),
                    fieldLabel: _('Plugin Egg'),
                    name: 'file',
                    buttonCfg: {
                        text: _('Browse...'),
                    },
                },
            ],
        });
    },

    onInstall: function (field, e) {
        this.form.getForm().submit({
            url: deluge.config.base + 'upload',
            waitMsg: _('Uploading your plugin...'),
            success: this.onUploadSuccess,
            scope: this,
        });
    },

    onUploadPlugin: function (info, obj, response, request) {
        this.fireEvent('pluginadded');
    },

    onUploadSuccess: function (fp, upload) {
        this.hide();
        if (upload.result.success) {
            var filename = this.form.getForm().getFieldValues().file;
            filename = filename.split('\\').slice(-1)[0];
            var path = upload.result.files[0];
            this.form.getForm().setValues({ file: '' });
            deluge.client.web.upload_plugin(filename, path, {
                success: this.onUploadPlugin,
                scope: this,
                filename: filename,
            });
        }
    },
});
