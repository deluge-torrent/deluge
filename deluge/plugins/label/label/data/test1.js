/*
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# License : GPL v3.
*/


popup_icon = "/static/images/tango/emblem-symbolic-link.png" /*the best i could find in 15 minutes, i still hate it.*/

Plugins = {}
Plugins.Label = {
	initialize : function() {
		this.bound = {
			addPopup: this.addPopup.bind(this),
			labelAction: this.labelAction.bindWithEvent(this),
		};

		$$('.filter_label').each(this.bound.addPopup);

		var menu = new Widgets.PopupMenu();
		menu.add(this.menu);
		menu.addEvent('action', this.bound.labelAction);

	},

	/*add menu to html-ui*/
	addPopup: function (el) {

		var label_id = el.id.substring(13); /*crop of "filter_label_"*/
		el.addEvent('contextmenu', function(el) {
			alert('popup menu here : [label="' + label_id + '"] (using this.menu definitions)');
			return false;
		});
	},

	/*callback handler*/
	labelAction:  function(action, label_id) {
		// We use $empty here to ensure that there is some form of a
		// function to call
		func = ($defined(this[action])) ? this[action] : $empty;
		func(label_id);
	},

	/*menu callbacks:*/
	add: function(label_id) {
		alert("Add Label:" + label_id);
	},
	edit: function() {
		alert("Edit Label:" + label_id);
	},
	remove: function() {
		alert("Remove Label:" + label_id);
	},

	/*popup menu definition*/
	menu:[
		{
		    type:'text',
		    action:'add',
		    text: _('Add Label'),
		    icon:'/static/images/tango/pause.png'
		},
		{
		    type: 'text',
		    action: 'edit',
		    text: _('Label Options'),
		    icon: '/static/images/tango/start.png'
		},
		{
		    type: 'text',
		    action: 'remove',
		    text: _('Remove Label'),
		    icon: '/static/images/tango/start.png'
		}
	]
};

window.addEvent('domready', function(e) {
	Plugins.Label.initialize();
});

