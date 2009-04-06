/*
Script: deluge-bars.js
    Contains the various bars (Sidebar, Toolbar, Statusbar) used within Deluge.

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


    Class: Deluge.Widgets.Toolbar
        Manages the top toolbar handling clicks and actions.

    Example:
        toolbar = new Deluge.Widgets.Toolbar();

    Returns:
        An instance of the class wrapped about the toolbar.
*/

Deluge.Widgets.Toolbar = new Class({
    Implements: Events,
    Extends: Widgets.Base,

    initialize: function() {
        this.parent($('toolbar'));
        this.buttons = this.element.getFirst();
        this.buttons.getElements('li').each(function(el) {
            el.addEvent('click', function(e) {
                e.action = el.id;
                this.fireEvent('buttonClick', e);
            }.bind(this));
        }, this);
    }
});


/*
    Class: Deluge.Widgets.StatusBar
        Class to manage the bottom status bar

    Example:
        status = new Deluge.Widgets.StatusBar();

    Returns:
        An instance of the class wrapped about the status div
*/
Deluge.Widgets.StatusBar = new Class({
    Extends: Widgets.Base,

    initialize: function() {
        this.parent($('status'));
        this.bound = {
            onContextMenu: this.onContextMenu.bindWithEvent(this)
        };

        this.element.getElements('li').each(function(el) {
            this[el.id] = el;
        }, this);
        this.incoming_connections.setStyle('display', 'none');

        this.connections.addEvent('contextmenu', this.bound.onContextMenu);
        var menu = new Widgets.PopupMenu();
        menu.add(Deluge.Menus.Connections);
        menu.addEvent('action', this.onMenuAction);
        this.connections.store('menu', menu);

        this.downspeed.addEvent('contextmenu', this.bound.onContextMenu);
        menu = new Widgets.PopupMenu();
        menu.add(Deluge.Menus.Download);
        menu.addEvent('action', this.onMenuAction);
        this.downspeed.store('menu', menu);

        this.upspeed.addEvent('contextmenu', this.bound.onContextMenu);
        menu = new Widgets.PopupMenu();
        menu.add(Deluge.Menus.Upload);
        menu.addEvent('action', this.onMenuAction);
        this.upspeed.store('menu', menu);
    },

    /*
        Property: update
            Takes thes stats part of the update_ui rpc call and
            performs the required changes on the statusbar.

        Arguments:
            stats - A dictionary of the returned stats

        Example:
            statusbar.update(data['stats']);
    */
    update: function(stats) {
        this.connections.set('text', stats.num_connections + ' (' + stats.max_num_connections + ')');
        this.downspeed.set('text', stats.download_rate.toSpeed() + ' (' + stats.max_download + ' KiB/s)');
        this.upspeed.set('text', stats.upload_rate.toSpeed() + ' (' + stats.max_upload + ' KiB/s)');
        this.dht.set('text', stats.dht_nodes);
        this.free_space.set('text', stats.free_space.toBytes());
        if (stats.has_incoming_connections) {
            this.incoming_connections.setStyle('display', 'none');
        } else {
            this.incoming_connections.setStyle('display', 'inline');
        }
    },

    /*
        Property: onContextMenu
            Event handler for when certain parts of the statusbar have been
            right clicked.

        Arguments:
            e - The event args

        Example:
            el.addEvent('contextmenu', this.onContextMenu.bindWithEvent(this));
    */
    onContextMenu: function(e) {
        e.stop();
        var menu = e.target.retrieve('menu');
        if (menu) menu.show(e);
    },

    /*
        Property: onMenuAction
            Event handler for when an item in one of the menus is clicked.
            Note that it does not need to be bound as it doesn't use `this`
            anywhere within the method.

        Arguments:
            e - The event args

        Example:
            menu.addEvent('action', this.onMenuAction);
    */
    onMenuAction: function(e) {
        if (e.action == 'max_connections') e.action = 'max_connections_global';
        config = {}
        config[e.action] = e.value;
        Deluge.Client.set_config(config);
        Deluge.UI.update();
    }
});


/*
    Class: Deluge.Wdigets.Labels
        Class to manage the filtering labels in the sidebar

    Example:
        labels = new Deluge.Widgets.Labels();

    Returns:
        An instance of the class wrapped about the labels div
*/
Deluge.Widgets.Labels = new Class({

    Extends: Widgets.Base,

    initialize: function() {
        this.parent($('labels'));
        this.bound = {
            labelClicked: this.labelClicked.bindWithEvent(this)
        };
        this.filters = {};
    },

    /*
        Property: update
            Takes thes filters part of the update_ui rpc call and
            performs the required changes on the filtering

        Arguments:
            filters - A dictionary of the available filters

        Example:
            labels.update({'state': [['All', '3'], ['Downloading', '2']]);
    */
    update: function(filters) {
        $each(filters, function(values, name) {
            if ($defined(this.filters[name])) {
                this.filters[name].update(values);
            } else {
                this.filters[name] = new Deluge.Widgets.LabelSection(name);
                this.filters[name].addEvent('labelClicked', this.bound.labelClicked);
                this.element.grab(this.filters[name]);
                this.filters[name].update(values);
                if (!this.filterType && !this.filterName) {
                    var el = this.filters[name].list.getElements('li')[0];
                    this.currentFilter = el;
                    this.filterType = name;
                    this.filterName = el.retrieve('filterName');
                    this.currentFilter.addClass('activestate');
                }
            }
        }, this);
    },

    /*
        Property: labelClicked

        Arguments:
            e - The event args

        Example:
            labelSection.addEvent('labelClicked', this.bound.labelClicked);
    */
    labelClicked: function(e) {
        this.currentFilter.removeClass('activestate');
        this.filterType = e.name;
        this.filterName = e.filter;
        this.currentFilter = e.target;
        e.target.addClass('activestate');
        this.fireEvent('filterChanged');
    }
});

/*
    Class: Deluge.Widgets.LabelSection
        Class to manage a section of filters within the labels block

    Arguments:
        string (the name of the section)

    Returns:
        A widget with the ability to manage the filters
*/
Deluge.Widgets.LabelSection = new Class({

    Extends: Widgets.Base,

    regex: /([\w]+)\s\((\d)\)/,

    initialize: function(name) {
        this.parent(new Element('div'));
        this.name = name;
        this.bound = {
            'clicked': this.clicked.bindWithEvent(this)
        }

        name = name.replace('_', ' ');
        parts = name.split(' ');
        name = '';
        parts.each(function(part) {
            firstLetter = part.substring(0, 1);
            firstLetter = firstLetter.toUpperCase();
            part = firstLetter + part.substring(1);
            name += part + ' ';
        });

        this.header = new Element('h3').set('text', name);
        this.list = new Element('ul');

        this.element.grab(this.header);
        this.element.grab(this.list);
    },

    /*
        Property: update
            Updates the filters list

        Arguments:
            values - a list of name/count values for the filters

        Example:
            labelSection.update([['All', '3'], ['Downloading', '2']]);
    */
    update: function(values) {
        names = new Array();
        $each(values, function(value) {
            var name = value[0], count = value[1], lname = name.toLowerCase();
            lname = lname.replace('.', '_');
            names.include(lname);
            var el = this.list.getElement('li.' + lname);
            if (!el) {
                el = new Element('li').addClass(lname);
                el.store('filterName', name)
                el.addEvent('click', this.bound.clicked);
                if (this.name == 'tracker_host') {
                    var icon = 'url(/tracker/icon/' + name + ')';
                    el.setStyle('background-image', icon);
                };
                this.list.grab(el);
            }
            el.set('text', name + ' (' + count +')');
        }, this);

        // Clean out any labels that are no longer returned
        this.list.getElements('li').each(function(el) {
            var hasName = false;
            names.each(function(name) {
                if (hasName) return;
                hasName = el.hasClass(name);
            });

            if (!hasName) {
                el.destroy();
            }
        });
    },

    /*
        Property: clicked
            Event handler for when a list item is clicked

        Arguments:
            e - The event args

        Example:
            listItem.addEvent('click', this.clicked.bindWithEvent(this));
    */
    clicked: function(e) {
        e.filter = e.target.retrieve('filterName');
        e.name = this.name
        this.fireEvent('labelClicked', e);
    }
});
