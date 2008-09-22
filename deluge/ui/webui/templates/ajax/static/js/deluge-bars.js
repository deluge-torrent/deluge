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
    
    regex: /([\w]+)\s\((\d)\)/,
    
    initialize: function() {
        this.parent($('labels'))
        this.bound = {
            resized: this.resized.bindWithEvent(this),
            clickedState: this.clickedState.bindWithEvent(this)
        }
        
        this.list = new Element('ul')
        this.element.grab(this.list)
        this.addStates()
        this.state = 'All'
        this.islabels = false;
        this.addEvent('resize', this.resized)
    },
    
    addStates: function() {
        this.list.grab(new Element('li').set('text', 'All').addClass('all').addClass('activestate'))
        this.list.grab(new Element('li').set('text', 'Downloading').addClass('downloading'))
        this.list.grab(new Element('li').set('text', 'Seeding').addClass('seeding'))
        this.list.grab(new Element('li').set('text', 'Queued').addClass('queued'))
        this.list.grab(new Element('li').set('text', 'Paused').addClass('paused'))
        this.list.grab(new Element('li').set('text', 'Error').addClass('error'))
        this.list.grab(new Element('li').set('text', 'Checking').addClass('checking'))
        this.list.grab(new Element('hr'))
    },
    
    addLabel: function(name) {
        
    },
    
    clickedState: function(e) {
        if (this.islabels) {
            var old = this.list.getElement('.' + this.state.toLowerCase())
            old.removeClass('activestate')
            this.state = e.target.get('text').match(/^(\w+)/)[1]
            e.target.addClass('activestate')
            this.fireEvent('stateChanged', this.state)
        } else {
            
        }
    },
    
    update: function(filters) {
        if (filters.state.length == 1)
            this.updateNoLabels(filters);
        else
            this.updateLabels(filters)
    },
    
    updateNoLabels: function(filters) {
        this.islabels = false;
    },
    
    updateLabels: function(filters) {
        this.islabels = true;
        $each(filters.state, function(state) {
            var el = this.list.getElement('.' + state[0].toLowerCase())
            if (!el) return
            
            el.set('text', state[0] + ' (' + state[1] + ')')
            el.removeEvent('click', this.bound.clickedState)
            el.addEvent('click', this.bound.clickedState)
        }, this)
    },
    
    resized: function(event) {
        var height = this.element.getInnerSize().y;
        this.list.getSizeModifiers();
        height -= this.list.modifiers.y;
        this.list.setStyle('height', height)
    }
});
