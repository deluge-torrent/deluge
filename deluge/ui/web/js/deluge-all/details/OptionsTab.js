/**
 * Deluge.details.OptionsTab.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Deluge.details.OptionsTab = Ext.extend(Ext.form.FormPanel, {
    constructor: function (config) {
        config = Ext.apply(
            {
                autoScroll: true,
                bodyStyle: 'padding: 5px;',
                border: false,
                cls: 'x-deluge-options',
                defaults: {
                    autoHeight: true,
                    labelWidth: 1,
                    defaultType: 'checkbox',
                },
                deferredRender: false,
                layout: 'column',
                title: _('Options'),
            },
            config
        );
        Deluge.details.OptionsTab.superclass.constructor.call(this, config);
    },

    initComponent: function () {
        Deluge.details.OptionsTab.superclass.initComponent.call(this);

        (this.fieldsets = {}), (this.fields = {});
        this.optionsManager = new Deluge.MultiOptionsManager({
            options: {
                max_download_speed: -1,
                max_upload_speed: -1,
                max_connections: -1,
                max_upload_slots: -1,
                auto_managed: false,
                stop_at_ratio: false,
                stop_ratio: 2.0,
                remove_at_ratio: false,
                move_completed: false,
                move_completed_path: '',
                private: false,
                prioritize_first_last: false,
                super_seeding: false,
            },
        });

        /*
         * Bandwidth Options
         */
        this.fieldsets.bandwidth = this.add({
            xtype: 'fieldset',
            defaultType: 'spinnerfield',
            bodyStyle: 'padding: 5px',

            layout: 'table',
            layoutConfig: { columns: 3 },
            labelWidth: 150,

            style: 'margin-left: 10px; margin-right: 5px; padding: 5px',
            title: _('Bandwidth'),
            width: 250,
        });

        /*
         * Max Download Speed
         */
        this.fieldsets.bandwidth.add({
            xtype: 'label',
            text: _('Max Download Speed:'),
            forId: 'max_download_speed',
            cls: 'x-deluge-options-label',
        });
        this.fields.max_download_speed = this.fieldsets.bandwidth.add({
            id: 'max_download_speed',
            name: 'max_download_speed',
            width: 70,
            strategy: {
                xtype: 'number',
                decimalPrecision: 1,
                minValue: -1,
                maxValue: 99999,
            },
        });
        this.fieldsets.bandwidth.add({
            xtype: 'label',
            text: _('KiB/s'),
            style: 'margin-left: 10px',
        });

        /*
         * Max Upload Speed
         */
        this.fieldsets.bandwidth.add({
            xtype: 'label',
            text: _('Max Upload Speed:'),
            forId: 'max_upload_speed',
            cls: 'x-deluge-options-label',
        });
        this.fields.max_upload_speed = this.fieldsets.bandwidth.add({
            id: 'max_upload_speed',
            name: 'max_upload_speed',
            width: 70,
            value: -1,
            strategy: {
                xtype: 'number',
                decimalPrecision: 1,
                minValue: -1,
                maxValue: 99999,
            },
        });
        this.fieldsets.bandwidth.add({
            xtype: 'label',
            text: _('KiB/s'),
            style: 'margin-left: 10px',
        });

        /*
         * Max Connections
         */
        this.fieldsets.bandwidth.add({
            xtype: 'label',
            text: _('Max Connections:'),
            forId: 'max_connections',
            cls: 'x-deluge-options-label',
        });
        this.fields.max_connections = this.fieldsets.bandwidth.add({
            id: 'max_connections',
            name: 'max_connections',
            width: 70,
            value: -1,
            strategy: {
                xtype: 'number',
                decimalPrecision: 0,
                minValue: -1,
                maxValue: 99999,
            },
            colspan: 2,
        });

        /*
         * Max Upload Slots
         */
        this.fieldsets.bandwidth.add({
            xtype: 'label',
            text: _('Max Upload Slots:'),
            forId: 'max_upload_slots',
            cls: 'x-deluge-options-label',
        });
        this.fields.max_upload_slots = this.fieldsets.bandwidth.add({
            id: 'max_upload_slots',
            name: 'max_upload_slots',
            width: 70,
            value: -1,
            strategy: {
                xtype: 'number',
                decimalPrecision: 0,
                minValue: -1,
                maxValue: 99999,
            },
            colspan: 2,
        });

        /*
         * Queue Options
         */
        this.fieldsets.queue = this.add({
            xtype: 'fieldset',
            title: _('Queue'),
            style: 'margin-left: 5px; margin-right: 5px; padding: 5px',
            width: 210,

            layout: 'table',
            layoutConfig: { columns: 2 },
            labelWidth: 0,

            defaults: {
                fieldLabel: '',
                labelSeparator: '',
            },
        });

        this.fields.auto_managed = this.fieldsets.queue.add({
            xtype: 'checkbox',
            fieldLabel: '',
            labelSeparator: '',
            name: 'is_auto_managed',
            boxLabel: _('Auto Managed'),
            width: 200,
            colspan: 2,
        });

        this.fields.stop_at_ratio = this.fieldsets.queue.add({
            fieldLabel: '',
            labelSeparator: '',
            id: 'stop_at_ratio',
            width: 120,
            boxLabel: _('Stop seed at ratio:'),
            handler: this.onStopRatioChecked,
            scope: this,
        });

        this.fields.stop_ratio = this.fieldsets.queue.add({
            xtype: 'spinnerfield',
            id: 'stop_ratio',
            name: 'stop_ratio',
            disabled: true,
            width: 50,
            value: 2.0,
            strategy: {
                xtype: 'number',
                minValue: -1,
                maxValue: 99999,
                incrementValue: 0.1,
                alternateIncrementValue: 1,
                decimalPrecision: 1,
            },
        });

        this.fields.remove_at_ratio = this.fieldsets.queue.add({
            fieldLabel: '',
            labelSeparator: '',
            id: 'remove_at_ratio',
            ctCls: 'x-deluge-indent-checkbox',
            bodyStyle: 'padding-left: 10px',
            boxLabel: _('Remove at ratio'),
            disabled: true,
            colspan: 2,
        });

        this.fields.move_completed = this.fieldsets.queue.add({
            fieldLabel: '',
            labelSeparator: '',
            id: 'move_completed',
            boxLabel: _('Move Completed:'),
            colspan: 2,
            handler: this.onMoveCompletedChecked,
            scope: this,
        });

        this.fields.move_completed_path = this.fieldsets.queue.add({
            xtype: 'textfield',
            fieldLabel: '',
            id: 'move_completed_path',
            colspan: 3,
            bodyStyle: 'margin-left: 20px',
            width: 180,
            disabled: true,
        });

        /*
         * General Options
         */
        this.rightColumn = this.add({
            border: false,
            autoHeight: true,
            style: 'margin-left: 5px',
            width: 210,
        });

        this.fieldsets.general = this.rightColumn.add({
            xtype: 'fieldset',
            autoHeight: true,
            defaultType: 'checkbox',
            title: _('General'),
            layout: 'form',
        });

        this.fields['private'] = this.fieldsets.general.add({
            fieldLabel: '',
            labelSeparator: '',
            boxLabel: _('Private'),
            id: 'private',
            disabled: true,
        });

        this.fields.prioritize_first_last = this.fieldsets.general.add({
            fieldLabel: '',
            labelSeparator: '',
            boxLabel: _('Prioritize First/Last'),
            id: 'prioritize_first_last',
        });

        this.fields.super_seeding = this.fieldsets.general.add({
            fieldLabel: '',
            labelSeparator: '',
            boxLabel: _('Super Seeding'),
            id: 'super_seeding',
        });

        // Bind the fields so the options manager can manage them.
        for (var id in this.fields) {
            this.optionsManager.bind(id, this.fields[id]);
        }

        /*
         * Buttons
         */
        this.buttonPanel = this.rightColumn.add({
            layout: 'hbox',
            xtype: 'panel',
            border: false,
        });

        /*
         * Edit Trackers button
         */
        this.buttonPanel.add({
            id: 'edit_trackers',
            xtype: 'button',
            text: _('Edit Trackers'),
            cls: 'x-btn-text-icon',
            iconCls: 'x-deluge-edit-trackers',
            border: false,
            width: 100,
            handler: this.onEditTrackers,
            scope: this,
        });

        /*
         * Apply button
         */
        this.buttonPanel.add({
            id: 'apply',
            xtype: 'button',
            text: _('Apply'),
            style: 'margin-left: 10px;',
            border: false,
            width: 100,
            handler: this.onApply,
            scope: this,
        });
    },

    onRender: function (ct, position) {
        Deluge.details.OptionsTab.superclass.onRender.call(this, ct, position);

        // This is another hack I think, so keep an eye out here when upgrading.
        this.layout = new Ext.layout.ColumnLayout();
        this.layout.setContainer(this);
        this.doLayout();
    },

    clear: function () {
        if (this.torrentId == null) return;
        this.torrentId = null;
        this.optionsManager.changeId(null);
    },

    reset: function () {
        if (this.torrentId) this.optionsManager.reset();
    },

    update: function (torrentId) {
        if (this.torrentId && !torrentId) this.clear(); // we want to clear the pane if we get a null torrent torrentIds

        if (!torrentId) return; // We do not care about null torrentIds.

        if (this.torrentId != torrentId) {
            this.torrentId = torrentId;
            this.optionsManager.changeId(torrentId);
        }
        deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Options, {
            success: this.onRequestComplete,
            scope: this,
        });
    },

    onApply: function () {
        var changed = this.optionsManager.getDirty();
        deluge.client.core.set_torrent_options([this.torrentId], changed, {
            success: function () {
                this.optionsManager.commit();
            },
            scope: this,
        });
    },

    onEditTrackers: function () {
        deluge.editTrackers.show();
    },

    onMoveCompletedChecked: function (checkbox, checked) {
        this.fields.move_completed_path.setDisabled(!checked);

        if (!checked) return;
        this.fields.move_completed_path.focus();
    },

    onStopRatioChecked: function (checkbox, checked) {
        this.fields.remove_at_ratio.setDisabled(!checked);
        this.fields.stop_ratio.setDisabled(!checked);
    },

    onRequestComplete: function (torrent, options) {
        this.fields['private'].setValue(torrent['private']);
        this.fields['private'].setDisabled(true);
        delete torrent['private'];
        torrent['auto_managed'] = torrent['is_auto_managed'];
        torrent['prioritize_first_last_pieces'] =
            torrent['prioritize_first_last'];
        this.optionsManager.setDefault(torrent);
        var stop_at_ratio = this.optionsManager.get('stop_at_ratio');
        this.fields.remove_at_ratio.setDisabled(!stop_at_ratio);
        this.fields.stop_ratio.setDisabled(!stop_at_ratio);
        this.fields.move_completed_path.setDisabled(
            !this.optionsManager.get('move_completed')
        );
    },
});
