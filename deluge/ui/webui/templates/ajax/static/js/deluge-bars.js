/*
 * Script: deluge-bars.js
 *  Contains the various bars (Sidebar, Toolbar, Statusbar) used within deluge
 *
 * Copyright:
 *   Damien Churchill (c) 2008
 */

Deluge.Widgets.Toolbar = new Class({
    Implements: Events,
    Extends: Widgets.Base,
    
    initialize: function() {
        this.parent($('toolbar'))
        this.buttons = this.element.getFirst()
        this.info = this.element.getLast()
        this.buttons.getElements('li').each(function(el) {
            el.addEvent('click', function(e) {
                e.action = el.id
                this.fireEvent('buttonClick', e)
            }.bind(this))
        }, this)
    }
});

Deluge.Widgets.StatusBar = new Class({
    Extends: Widgets.Base,
    
    initialize: function() {
        this.parent($('status'));
        this.element.getElements('li').each(function(el) {
            this[el.id] = el;
        }, this);
    },
    
    update: function(stats) {
        this.connections.set('text', stats.num_connections);
        this.downspeed.set('text', stats.download_rate.toSpeed());
        this.upspeed.set('text', stats.upload_rate.toSpeed());
        this.dht.set('text', stats.dht_nodes);
    }
});


Deluge.Widgets.Labels = new Class({
    
    Extends: Widgets.Base,
    
    initialize: function() {
        this.parent($('labels'));
        this.bound = {
            labelClicked: this.labelClicked.bindWithEvent(this)
        };
        this.filters = {};
    },
    
    labelClicked: function(e) {
        this.currentFilter.removeClass('activestate');
        this.filterType = e.filter;
        this.filterName = e.name;
        this.currentFilter = e.target;
        e.target.addClass('activestate');
    },
    
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
    
    clicked: function(e) {
        e.filter = e.target.retrieve('filterName');
        e.name = this.name
        this.fireEvent('labelClicked', e);
    }
});
