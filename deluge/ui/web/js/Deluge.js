/*
Script: Deluge.js
    Contains the keys for get_torrent(s)_status.

Copyright:
	(C) Damien Churchill 2009 <damoxc@gmail.com>
	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 3, or (at your option)
	any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, write to:
		The Free Software Foundation, Inc.,
		51 Franklin Street, Fifth Floor
		Boston, MA  02110-1301, USA.

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.
*/

Ext.namespace('Ext.deluge');

(function() {
	/* Add some helper functions to Ext */
	Ext.apply(Function.prototype, {
		bind: function(scope) {
			var self = this;
			return function() {
				return self.apply(scope, arguments);
			}
		}
	});
	
	Ext.apply(Ext, {
		keys: function(obj) {
			var keys = [];
			for (i in obj) if (obj.hasOwnProperty(i))
			{
				keys.push(i);
			}
			return keys;
		},
			
		splat: function(obj) {
			var type = Ext.type(obj);
			return (type) ? ((type != 'array') ? [obj] : obj) : [];
		}
	});
	Ext.getKeys = Ext.keys;
})();

(function() {
	var tpl = '<div class="x-progress-wrap x-progress-renderered">' +
		'<div class="x-progress-inner">' +
			'<div style="width: {2}px" class="x-progress-bar">' +
				'<div style="z-index: 99; width: {3}px" class="x-progress-text">' +
					'<div style="width: {1}px;">{0}</div>' +
				'</div>' +
			'</div>' +
			'<div class="x-progress-text x-progress-text-back">' +
				'<div style="width: {1}px;">{0}</div>' +
			'</div>' +
		'</div>' +
	'</div>';
	
	Deluge.progressBar =  function(progress, width, text, modifier) {
		modifier = Ext.value(modifier, 10);
		var progressWidth = ((width / 100.0) * progress).toFixed(0);
		var barWidth = progressWidth - 1;
		var textWidth = ((progressWidth - modifier) > 0 ? progressWidth - modifier : 0);
		return String.format(tpl, text, width, barWidth, textWidth);
	}
})();

// Hinting for gettext_gen.py
// _('Do Not Download')
// _('Normal Priority')
// _('High Priority')
// _('Highest Priority')
FILE_PRIORITY = {
    0: 'Do Not Download',
    1: 'Normal Priority',
    2: 'High Priority',
    5: 'Highest Priority',
    'Do Not Download': 0,
    'Normal Priority': 1,
    'High Priority': 2,
    'Highest Priority': 5
}

FILE_PRIORITY_CSS = {
	0: 'x-no-download',
	1: 'x-normal-download',
	2: 'x-high-download',
	5: 'x-highest-download'
}
