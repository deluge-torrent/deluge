/*
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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

#
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
