/*
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# License : GPL v3.
*/


popup_icon = "/static/images/tango/emblem-symbolic-link.png" /*the best i could find in 15 minutes, i still hate it.*/

Plugins = {}

function _(str)  {
	return str /*#todo : translations; see Deluge.Strings.get*/
}

Plugins.Label = {
	/*onload:*/
	initialize: function() {
		$$('.filter_label').each(Plugins.Label.addPopup);

		var menu = new Widgets.PopupMenu()
		menu.add(this.menu);
		menu.addEvent('action', function(e) {
		    Plugins.Label.labelAction(e.action, e.value)
		}.bind(this));

	},
	/*add menu to html-ui*/
	addPopup: function (el) {
		var label_id = el.id.substring(13) /*crop of "filter_label_"*/
		el.innerHTML = "<img src='" + popup_icon + "' onclick=alert('popup:" + label_id + "')>" + el.innerHTML;
	},

	/*callback handler*/
	labelAction:  function(action, label_id) {
		func = Plugins.Label[action];
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

window.addEvent('domready', Plugins.Label.initialize);
