/**
 * Deluge.Statusbar.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge');

Deluge.Statusbar = Ext.extend(Ext.ux.StatusBar, {
    constructor: function (config) {
        config = Ext.apply(
            {
                id: 'deluge-statusbar',
                defaultIconCls: 'x-deluge-statusbar x-not-connected',
                defaultText: _('Not Connected'),
            },
            config
        );
        Deluge.Statusbar.superclass.constructor.call(this, config);
    },

    initComponent: function () {
        Deluge.Statusbar.superclass.initComponent.call(this);

        deluge.events.on('connect', this.onConnect, this);
        deluge.events.on('disconnect', this.onDisconnect, this);
    },

    createButtons: function () {
        this.buttons = this.add(
            {
                id: 'statusbar-connections',
                text: ' ',
                cls: 'x-btn-text-icon',
                iconCls: 'x-deluge-connections',
                tooltip: _('Connections'),
                menu: new Deluge.StatusbarMenu({
                    items: [
                        {
                            text: '50',
                            value: '50',
                            group: 'max_connections_global',
                            checked: false,
                        },
                        {
                            text: '100',
                            value: '100',
                            group: 'max_connections_global',
                            checked: false,
                        },
                        {
                            text: '200',
                            value: '200',
                            group: 'max_connections_global',
                            checked: false,
                        },
                        {
                            text: '300',
                            value: '300',
                            group: 'max_connections_global',
                            checked: false,
                        },
                        {
                            text: '500',
                            value: '500',
                            group: 'max_connections_global',
                            checked: false,
                        },
                        {
                            text: _('Unlimited'),
                            value: '-1',
                            group: 'max_connections_global',
                            checked: false,
                        },
                        '-',
                        {
                            text: _('Other'),
                            value: 'other',
                            group: 'max_connections_global',
                            checked: false,
                        },
                    ],
                    otherWin: {
                        title: _('Set Maximum Connections'),
                    },
                }),
            },
            '-',
            {
                id: 'statusbar-downspeed',
                text: ' ',
                cls: 'x-btn-text-icon',
                iconCls: 'x-deluge-downloading',
                tooltip: _('Download Speed'),
                menu: new Deluge.StatusbarMenu({
                    items: [
                        {
                            value: '5',
                            text: _('5 KiB/s'),
                            group: 'max_download_speed',
                            checked: false,
                        },
                        {
                            value: '10',
                            text: _('10 KiB/s'),
                            group: 'max_download_speed',
                            checked: false,
                        },
                        {
                            value: '30',
                            text: _('30 KiB/s'),
                            group: 'max_download_speed',
                            checked: false,
                        },
                        {
                            value: '80',
                            text: _('80 KiB/s'),
                            group: 'max_download_speed',
                            checked: false,
                        },
                        {
                            value: '300',
                            text: _('300 KiB/s'),
                            group: 'max_download_speed',
                            checked: false,
                        },
                        {
                            value: '-1',
                            text: _('Unlimited'),
                            group: 'max_download_speed',
                            checked: false,
                        },
                        '-',
                        {
                            value: 'other',
                            text: _('Other'),
                            group: 'max_download_speed',
                            checked: false,
                        },
                    ],
                    otherWin: {
                        title: _('Set Maximum Download Speed'),
                        unit: _('KiB/s'),
                    },
                }),
            },
            '-',
            {
                id: 'statusbar-upspeed',
                text: ' ',
                cls: 'x-btn-text-icon',
                iconCls: 'x-deluge-seeding',
                tooltip: _('Upload Speed'),
                menu: new Deluge.StatusbarMenu({
                    items: [
                        {
                            value: '5',
                            text: _('5 KiB/s'),
                            group: 'max_upload_speed',
                            checked: false,
                        },
                        {
                            value: '10',
                            text: _('10 KiB/s'),
                            group: 'max_upload_speed',
                            checked: false,
                        },
                        {
                            value: '30',
                            text: _('30 KiB/s'),
                            group: 'max_upload_speed',
                            checked: false,
                        },
                        {
                            value: '80',
                            text: _('80 KiB/s'),
                            group: 'max_upload_speed',
                            checked: false,
                        },
                        {
                            value: '300',
                            text: _('300 KiB/s'),
                            group: 'max_upload_speed',
                            checked: false,
                        },
                        {
                            value: '-1',
                            text: _('Unlimited'),
                            group: 'max_upload_speed',
                            checked: false,
                        },
                        '-',
                        {
                            value: 'other',
                            text: _('Other'),
                            group: 'max_upload_speed',
                            checked: false,
                        },
                    ],
                    otherWin: {
                        title: _('Set Maximum Upload Speed'),
                        unit: _('KiB/s'),
                    },
                }),
            },
            '-',
            {
                id: 'statusbar-traffic',
                text: ' ',
                cls: 'x-btn-text-icon',
                iconCls: 'x-deluge-traffic',
                tooltip: _('Protocol Traffic Download/Upload'),
                handler: function () {
                    deluge.preferences.show();
                    deluge.preferences.selectPage('Network');
                },
            },
            '-',
            {
                id: 'statusbar-externalip',
                text: ' ',
                cls: 'x-btn-text',
                tooltip: _('External IP Address'),
            },
            '-',
            {
                id: 'statusbar-dht',
                text: ' ',
                cls: 'x-btn-text-icon',
                iconCls: 'x-deluge-dht',
                tooltip: _('DHT Nodes'),
            },
            '-',
            {
                id: 'statusbar-freespace',
                text: ' ',
                cls: 'x-btn-text-icon',
                iconCls: 'x-deluge-freespace',
                tooltip: _('Freespace in download folder'),
                handler: function () {
                    deluge.preferences.show();
                    deluge.preferences.selectPage('Downloads');
                },
            }
        );
        this.created = true;
    },

    onConnect: function () {
        this.setStatus({
            iconCls: 'x-connected',
            text: '',
        });
        if (!this.created) {
            this.createButtons();
        } else {
            Ext.each(this.buttons, function (item) {
                item.show();
                item.enable();
            });
        }
        this.doLayout();
    },

    onDisconnect: function () {
        this.clearStatus({ useDefaults: true });
        Ext.each(this.buttons, function (item) {
            item.hide();
            item.disable();
        });
        this.doLayout();
    },

    update: function (stats) {
        if (!stats) return;

        function addSpeed(val) {
            return val + ' KiB/s';
        }

        var updateStat = function (name, config) {
            var item = this.items.get('statusbar-' + name);
            if (config.limit.value > 0) {
                var value = config.value.formatter
                    ? config.value.formatter(config.value.value, true)
                    : config.value.value;
                var limit = config.limit.formatter
                    ? config.limit.formatter(config.limit.value, true)
                    : config.limit.value;
                var str = String.format(config.format, value, limit);
            } else {
                var str = config.value.formatter
                    ? config.value.formatter(config.value.value, true)
                    : config.value.value;
            }
            item.setText(str);

            if (!item.menu) return;
            item.menu.setValue(config.limit.value);
        }.createDelegate(this);

        updateStat('connections', {
            value: { value: stats.num_connections },
            limit: { value: stats.max_num_connections },
            format: '{0} ({1})',
        });

        updateStat('downspeed', {
            value: {
                value: stats.download_rate,
                formatter: Deluge.Formatters.speed,
            },
            limit: {
                value: stats.max_download,
                formatter: addSpeed,
            },
            format: '{0} ({1})',
        });

        updateStat('upspeed', {
            value: {
                value: stats.upload_rate,
                formatter: Deluge.Formatters.speed,
            },
            limit: {
                value: stats.max_upload,
                formatter: addSpeed,
            },
            format: '{0} ({1})',
        });

        updateStat('traffic', {
            value: {
                value: stats.download_protocol_rate,
                formatter: Deluge.Formatters.speed,
            },
            limit: {
                value: stats.upload_protocol_rate,
                formatter: Deluge.Formatters.speed,
            },
            format: '{0}/{1}',
        });

        this.items.get('statusbar-dht').setText(stats.dht_nodes);
        this.items
            .get('statusbar-freespace')
            .setText(
                stats.free_space >= 0 ? fsize(stats.free_space) : _('Error')
            );
        this.items
            .get('statusbar-externalip')
            .setText(
                String.format(
                    _('<b>IP</b> {0}'),
                    stats.external_ip ? stats.external_ip : _('n/a')
                )
            );
    },
});
