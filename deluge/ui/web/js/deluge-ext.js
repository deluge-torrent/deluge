/*
Script: deluge-ext.js
    Container for all classes that extend Exts native classes.

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
*/

Deluge.FilesTreeLoader = Ext.extend(Ext.tree.TreeLoader, {
	initComponent: function() {
		Deluge.FilesTreeLoader.superclass.initComponent.call(this);
	},
});

Deluge.ProgressBar = Ext.extend(Ext.ProgressBar, {
	initComponent: function() {
		Deluge.ProgressBar.superclass.initComponent.call(this);
	},
	
	updateProgress: function(value, text, animate) {
		this.value = value || 0;
		if (text) {
			this.updateText(text);
		}
		
		if (this.rendered) {
			var w = Math.floor(value*this.el.dom.firstChild.offsetWidth / 100.0);
	        this.progressBar.setWidth(w, animate === true || (animate !== false && this.animate));
	        if (this.textTopEl) {
	            //textTopEl should be the same width as the bar so overflow will clip as the bar moves
	            this.textTopEl.removeClass('x-hidden').setWidth(w);
	        }
		}
		this.fireEvent('update', this, value, text);
		return this;
	}
});
Ext.reg('deluge-progress', Deluge.ProgressBar);