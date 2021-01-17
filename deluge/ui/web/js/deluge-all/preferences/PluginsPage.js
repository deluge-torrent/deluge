/**
 * Deluge.preferences.PluginsPage.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.Plugins
 * @extends Ext.Panel
 */
Deluge.preferences.Plugins = Ext.extend(Ext.Panel, {
    layout: 'border',
    title: _('Plugins'),
    header: false,
    border: false,
    cls: 'x-deluge-plugins',

    pluginTemplate: new Ext.Template(
        '<dl class="singleline">' +
            '<dt>' +
            _('Author:') +
            '</dt><dd>{author}</dd>' +
            '<dt>' +
            _('Version:') +
            '</dt><dd>{version}</dd>' +
            '<dt>' +
            _('Author Email:') +
            '</dt><dd>{email}</dd>' +
            '<dt>' +
            _('Homepage:') +
            '</dt><dd>{homepage}</dd>' +
            '<dt>' +
            _('Details:') +
            '</dt><dd style="white-space:normal">{details}</dd>' +
            '</dl>'
    ),

    initComponent: function () {
        Deluge.preferences.Plugins.superclass.initComponent.call(this);
        this.defaultValues = {
            version: '',
            email: '',
            homepage: '',
            details: '',
        };
        this.pluginTemplate.compile();

        var checkboxRenderer = function (v, p, record) {
            p.css += ' x-grid3-check-col-td';
            return (
                '<div class="x-grid3-check-col' + (v ? '-on' : '') + '"> </div>'
            );
        };

        this.list = this.add({
            xtype: 'listview',
            store: new Ext.data.ArrayStore({
                fields: [
                    { name: 'enabled', mapping: 0 },
                    { name: 'plugin', mapping: 1, sortType: 'asUCString' },
                ],
            }),
            columns: [
                {
                    id: 'enabled',
                    header: _('Enabled'),
                    width: 0.2,
                    sortable: true,
                    tpl: new Ext.XTemplate('{enabled:this.getCheckbox}', {
                        getCheckbox: function (v) {
                            return (
                                '<div class="x-grid3-check-col' +
                                (v ? '-on' : '') +
                                '" rel="chkbox"> </div>'
                            );
                        },
                    }),
                    dataIndex: 'enabled',
                },
                {
                    id: 'plugin',
                    header: _('Plugin'),
                    width: 0.8,
                    sortable: true,
                    dataIndex: 'plugin',
                },
            ],
            singleSelect: true,
            autoExpandColumn: 'plugin',
            listeners: {
                selectionchange: { fn: this.onPluginSelect, scope: this },
            },
        });

        this.panel = this.add({
            region: 'center',
            autoScroll: true,
            items: [this.list],
            bbar: new Ext.Toolbar({
                items: [
                    {
                        cls: 'x-btn-text-icon',
                        iconCls: 'x-deluge-install-plugin',
                        text: _('Install'),
                        handler: this.onInstallPluginWindow,
                        scope: this,
                    },
                    '->',
                    {
                        cls: 'x-btn-text-icon',
                        text: _('Find More'),
                        iconCls: 'x-deluge-find-more',
                        handler: this.onFindMorePlugins,
                        scope: this,
                    },
                ],
            }),
        });

        var pp = (this.pluginInfo = this.add({
            xtype: 'panel',
            border: false,
            height: 100,
            region: 'south',
            padding: '5',
            autoScroll: true,
            bodyCfg: {
                style: 'white-space: nowrap',
            },
        }));

        this.pluginInfo.on('render', this.onPluginInfoRender, this);
        this.list.on('click', this.onNodeClick, this);
        deluge.preferences.on('show', this.onPreferencesShow, this);
        deluge.events.on('PluginDisabledEvent', this.onPluginDisabled, this);
        deluge.events.on('PluginEnabledEvent', this.onPluginEnabled, this);
    },

    disablePlugin: function (plugin) {
        deluge.client.core.disable_plugin(plugin);
    },

    enablePlugin: function (plugin) {
        deluge.client.core.enable_plugin(plugin);
    },

    setInfo: function (plugin) {
        if (!this.pluginInfo.rendered) return;
        var values = plugin || this.defaultValues;
        this.pluginInfo.body.dom.innerHTML = this.pluginTemplate.apply(values);
    },

    updatePlugins: function () {
        var onGotAvailablePlugins = function (plugins) {
            this.availablePlugins = plugins.sort(function (a, b) {
                return a.toLowerCase().localeCompare(b.toLowerCase());
            });

            deluge.client.core.get_enabled_plugins({
                success: onGotEnabledPlugins,
                scope: this,
            });
        };

        var onGotEnabledPlugins = function (plugins) {
            this.enabledPlugins = plugins;
            this.onGotPlugins();
        };

        deluge.client.core.get_available_plugins({
            success: onGotAvailablePlugins,
            scope: this,
        });
    },

    updatePluginsGrid: function () {
        var plugins = [];
        Ext.each(
            this.availablePlugins,
            function (plugin) {
                if (this.enabledPlugins.indexOf(plugin) > -1) {
                    plugins.push([true, plugin]);
                } else {
                    plugins.push([false, plugin]);
                }
            },
            this
        );
        this.list.getStore().loadData(plugins);
    },

    onNodeClick: function (dv, index, node, e) {
        var el = new Ext.Element(e.target);
        if (el.getAttribute('rel') != 'chkbox') return;

        var r = dv.getStore().getAt(index);
        if (r.get('plugin') == 'WebUi') return;
        r.set('enabled', !r.get('enabled'));
        r.commit();
        if (r.get('enabled')) {
            this.enablePlugin(r.get('plugin'));
        } else {
            this.disablePlugin(r.get('plugin'));
        }
    },

    onFindMorePlugins: function () {
        window.open('http://dev.deluge-torrent.org/wiki/Plugins');
    },

    onGotPlugins: function () {
        this.setInfo();
        this.updatePluginsGrid();
    },

    onGotPluginInfo: function (info) {
        var values = {
            author: info['Author'],
            version: info['Version'],
            email: info['Author-email'],
            homepage: info['Home-page'],
            details: info['Description'],
        };
        this.setInfo(values);
        delete info;
    },

    onInstallPluginWindow: function () {
        if (!this.installWindow) {
            this.installWindow = new Deluge.preferences.InstallPluginWindow();
            this.installWindow.on('pluginadded', this.onPluginInstall, this);
        }
        this.installWindow.show();
    },

    onPluginEnabled: function (pluginName) {
        var index = this.list.getStore().find('plugin', pluginName);
        if (index == -1) return;
        var plugin = this.list.getStore().getAt(index);
        plugin.set('enabled', true);
        plugin.commit();
    },

    onPluginDisabled: function (pluginName) {
        var index = this.list.getStore().find('plugin', pluginName);
        if (index == -1) return;
        var plugin = this.list.getStore().getAt(index);
        plugin.set('enabled', false);
        plugin.commit();
    },

    onPluginInstall: function () {
        this.updatePlugins();
    },

    onPluginSelect: function (dv, selections) {
        if (selections.length == 0) return;
        var r = dv.getRecords(selections)[0];
        deluge.client.web.get_plugin_info(r.get('plugin'), {
            success: this.onGotPluginInfo,
            scope: this,
        });
    },

    onPreferencesShow: function () {
        this.updatePlugins();
    },

    onPluginInfoRender: function (ct, position) {
        this.setInfo();
    },
});
