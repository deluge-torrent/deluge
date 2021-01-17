/**
 * Deluge.preferences.DownloadsPage.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Downloads
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Downloads = Ext.extend(Ext.FormPanel, {
    constructor: function (config) {
        config = Ext.apply(
            {
                border: false,
                title: _('Downloads'),
                header: false,
                layout: 'form',
                autoHeight: true,
                width: 320,
            },
            config
        );
        Deluge.preferences.Downloads.superclass.constructor.call(this, config);
    },

    initComponent: function () {
        Deluge.preferences.Downloads.superclass.initComponent.call(this);

        var optMan = deluge.preferences.getOptionsManager();
        var fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Folders'),
            labelWidth: 150,
            defaultType: 'togglefield',
            autoHeight: true,
            labelAlign: 'top',
            width: 300,
            style: 'margin-bottom: 5px; padding-bottom: 5px;',
        });

        optMan.bind(
            'download_location',
            fieldset.add({
                xtype: 'textfield',
                name: 'download_location',
                fieldLabel: _('Download to:'),
                labelSeparator: '',
                width: 280,
            })
        );

        var field = fieldset.add({
            name: 'move_completed_path',
            fieldLabel: _('Move completed to:'),
            labelSeparator: '',
            width: 280,
        });
        optMan.bind('move_completed', field.toggle);
        optMan.bind('move_completed_path', field.input);

        field = fieldset.add({
            name: 'torrentfiles_location',
            fieldLabel: _('Copy of .torrent files to:'),
            labelSeparator: '',
            width: 280,
        });
        optMan.bind('copy_torrent_file', field.toggle);
        optMan.bind('torrentfiles_location', field.input);

        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('Options'),
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'checkbox',
            style: 'margin-bottom: 0; padding-bottom: 0;',
            width: 280,
        });
        optMan.bind(
            'prioritize_first_last_pieces',
            fieldset.add({
                name: 'prioritize_first_last_pieces',
                labelSeparator: '',
                height: 22,
                boxLabel: _('Prioritize first and last pieces of torrent'),
            })
        );
        optMan.bind(
            'sequential_download',
            fieldset.add({
                name: 'sequential_download',
                labelSeparator: '',
                height: 22,
                boxLabel: _('Sequential download'),
            })
        );
        optMan.bind(
            'add_paused',
            fieldset.add({
                name: 'add_paused',
                labelSeparator: '',
                height: 22,
                boxLabel: _('Add torrents in Paused state'),
            })
        );
        optMan.bind(
            'pre_allocate_storage',
            fieldset.add({
                name: 'pre_allocate_storage',
                labelSeparator: '',
                height: 22,
                boxLabel: _('Pre-allocate disk space'),
            })
        );
    },
});
