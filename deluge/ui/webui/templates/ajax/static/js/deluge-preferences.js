/*
Script: deluge-preferences.js
    Contains the classes that provides the preferences window with
    functionality

 *
 * Copyright (C) Damien Churchill 2008 <damoxc@gmail.com>
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
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

 *
*/

Deluge.Widgets.PreferencesCategory = new Class({
    Extends: Widgets.TabPage
});

Deluge.Widgets.PluginPreferencesCategory = new Class({
    Extends: Deluge.Widgets.PreferencesCategory
});

Deluge.Widgets.GenericPreferences = new Class({
    Extends: Deluge.Widgets.PreferencesCategory,

    initialize: function(name, options) {
        this.parent(name, options)
        this.core = true;
        this.addEvent('loaded', function(e) {
            this.form = this.element.getElement('form');
            this.form.getElements('input[rel=spinner]').each(function(el) {
                new Widgets.Spinner(el);
            });
            this.form.getElements('input[rel=spinner1]').each(function(el) {
                new Widgets.Spinner(el, {
                    precision: 1
                });
            });
            this.form.getElements('input[rel=spinner2]').each(function(el) {
                new Widgets.Spinner(el, {
                    precision: 2
                });
            });
        }.bindWithEvent(this));
    },

    update: function(config) {
        this.fireEvent('beforeUpdate');
        this.original = config;
        this.changed = new Hash();
        this.inputs = this.form.getElements('input, select');
        this.inputs.each(function(input) {
            if (!input.name) return;
            if (!$defined(config[input.name])) return;

            widget = $$W(input);
            if (widget) {
                widget.setValue(config[input.name]);
            } else if (input.tagName.toLowerCase() == 'select') {
                var value = config[input.name].toString();
                input.getElements('option').each(function(option) {
                    if (option.value == value) {
                        option.selected = true;
                    }
                });
            } else if (input.type == 'text') {
                input.value = config[input.name];
            } else if (input.type == 'checkbox') {
                input.checked = config[input.name];
            } else if (input.type == 'radio') {
                var value = config[input.name].toString()
                if (input.value == value) {
                    input.checked = true;
                }
            }

            input.addEvent('change', function(el) {
                if (input.type == 'checkbox') {
                    if (this.original[input.name] == input.checked) {
                        if (this.changed[input.name])
                            delete this.changed[input.name];
                    } else {
                        this.changed[input.name] = input.checked
                    }
                } else {
                    if (this.original[input.name] == input.value) {
                        if (this.changed[input.name])
                            delete this.changed[input.name];
                    } else {
                        this.changed[input.name] = input.value;
                    }
                }
            }.bindWithEvent(this))
        }, this);
        this.fireEvent('update');
    },

    getConfig: function() {
        changed = {}
        this.changed.each(function(value, key) {
            var type = $type(this.original[key]);
            if (type == 'number') {
                changed[key] = Number(value);
            } else if (type == 'string') {
                changed[key] = String(value);
            } else if (type == 'boolean') {
                changed[key] = Boolean(value);
            }
        }, this);
        return changed;
    }
});

Deluge.Widgets.WebUIPreferences = new Class({
    Extends: Deluge.Widgets.GenericPreferences,

    options: {
        url: '/template/render/html/preferences_webui.html'
    },

    initialize: function() {
        this.parent('Web UI');
        this.core = false;
        this.addEvent('beforeUpdate', this.beforeUpdate.bindWithEvent(this));
        this.addEvent('update', this.updated.bindWithEvent(this));
    },

    beforeUpdate: function(event) {
        var templates = Deluge.Client.get_webui_templates({async: false});
        this.form.template.empty();
        templates.each(function(template) {
            var option = new Element('option');
            option.set('text', template);
            this.form.template.grab(option);
        }, this);
    },

    updated: function(event) {
        if (this.form.template.value != 'ajax')
            this.form.theme.disabled = true;
        else
            this.form.theme.disabled = false;

        var theme = this.form.theme.getElement('option[value="' + Cookie.read('theme') + '"]')
        theme.selected = true

        this.form.template.addEvent('change', function(e) {
            if (this.form.template.value != 'ajax') {
                this.form.theme.disabled = true;
                this.form.theme.addClass('disabled')
                this.form.getElementById('lbl_theme').addClass('disabled')
            } else {
                this.form.theme.disabled = false;
                this.form.getElementById('lbl_theme').removeClass('disabled')
                this.form.theme.removeClass('disabled')
            }
        }.bindWithEvent(this));
    },

    apply: function() {
        Deluge.UI.setTheme(this.form.theme.value);
        Deluge.Client.set_webui_config(this.changed, {
            onSuccess: function(e) {
                if (this.changed['template']) location.reload(true);
            }.bindWithEvent(this)
        });
    }
});

Deluge.Widgets.PreferencesWindow = new Class({
    Extends: Widgets.Window,
    options: {
        width: 500,
        height: 430,
        title: 'Preferences',
        url: '/template/render/html/window_preferences.html'
    },

    initialize: function() {
        this.parent();
        this.categories = [];
        this.currentPage = -1;
        this.addEvent('loaded', this.loaded.bindWithEvent(this));
        this.addEvent('beforeShow', this.beforeShown.bindWithEvent(this));
    },

    loaded: function(event) {
        this.catlist = this.content.getElement('.categories ul');
        this.pages = this.content.getElement('.pref_pages');
        this.title = this.pages.getElement('h3');

        this.reset = this.content.getElement('.buttons .reset');
        this.apply = this.content.getElement('.buttons .apply');
        this.apply.addEvent('click', this.applied.bindWithEvent(this));

        this.webui = new Deluge.Widgets.WebUIPreferences();

        this.download = new Deluge.Widgets.GenericPreferences('Download', {
            url: '/template/render/html/preferences_download.html'
        });
        this.network = new Deluge.Widgets.GenericPreferences('Network', {
            url: '/template/render/html/preferences_network.html'
        });
        this.bandwidth = new Deluge.Widgets.GenericPreferences('Bandwidth', {
            url: '/template/render/html/preferences_bandwidth.html'
        });
        this.daemon = new Deluge.Widgets.GenericPreferences('Daemon', {
            url: '/template/render/html/preferences_daemon.html'
        });
        this.queue = new Deluge.Widgets.GenericPreferences('Queue', {
            url: '/template/render/html/preferences_queue.html'
        });

        this.addCategory(this.webui);
        this.addCategory(this.download);
        this.addCategory(this.network);
        this.addCategory(this.bandwidth);
        this.addCategory(this.daemon);
        this.addCategory(this.queue);
    },

    addCategory: function(category) {
        this.categories.include(category);
        var categoryIndex = this.categories.indexOf(category);

        var tab = new Element('li');
        tab.set('text', category.name);
        tab.addEvent('click', function(e) {
            this.select(categoryIndex);
        }.bindWithEvent(this));
        category.tab = tab;

        this.catlist.grab(tab);
        this.pages.grab(category.addClass('deluge-prefs-page'));


        if (this.currentPage < 0) {
            this.currentPage = categoryIndex;
            this.select(categoryIndex);
        };
    },

    select: function(id) {
        this.categories[this.currentPage].removeClass('deluge-prefs-page-active');
        this.categories[this.currentPage].tab.removeClass('deluge-prefs-active');
        this.categories[id].addClass('deluge-prefs-page-active');
        this.categories[id].tab.addClass('deluge-prefs-active');
        this.title.set('text', this.categories[id].name);
        this.currentPage = id;
        this.fireEvent('pageChanged');
    },

    applied: function(event) {
        var config = {};
        this.categories.each(function(category) {
            config = $merge(config, category.getConfig());
        });

        if ($defined(config['end_listen_port']) || $defined(config['start_listen_port'])) {
            var startport = $pick(config['start_listen_port'], this.config['listen_ports'][0]);
            var endport = $pick(config['end_listen_port'], this.config['listen_ports'][1]);
            delete config['end_listen_port'];
            delete config['start_listen_port'];
            config['listen_ports'] = [startport, endport];
        }

        if ($defined(config['end_outgoing_port']) || $defined(config['start_outgoing_port'])) {
            var startport = $pick(config['start_outgoing_port'], this.config['outgoing_ports'][0]);
            var endport = $pick(config['end_outgoing_port'], this.config['outgoing_ports'][1]);
            delete config['end_outgoing_port'];
            delete config['start_outgoing_port'];
            config['outgoing_ports'] = [startport, endport];
        }

        Deluge.Client.set_config(config, {
            onSuccess: function(e) {
                this.hide();
            }.bindWithEvent(this)
        });
        this.webui.apply();
    },

    beforeShown: function(event) {
        // we want this to be blocking
        this.config = Deluge.Client.get_config({async: false});

        // Unfortunately we have to modify the listen ports preferences
        // in order to not have to modify the generic preferences class.
        this.config['start_listen_port'] = this.config['listen_ports'][0];
        this.config['end_listen_port'] = this.config['listen_ports'][1];

        this.config['start_outgoing_port'] = this.config['outgoing_ports'][0];
        this.config['end_outgoing_port'] = this.config['outgoing_ports'][1];

        // Iterate through the pages and set the fields
        this.categories.each(function(category) {
            if (category.update && category.core) category.update(this.config);
        }, this);

        // Update the config for the webui pages.
        var webconfig = Deluge.Client.get_webui_config({async: false});
        this.webui.update(webconfig);
    }
});
