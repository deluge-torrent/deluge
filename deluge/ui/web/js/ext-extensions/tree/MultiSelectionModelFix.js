/*!
 * Ext.ux.tree.MultiSelectionModelFix.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
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
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */

/**
 * This enhances the MSM to allow for shift selecting in tree grids etc.
 * @author Damien Churchill <damoxc@gmail.com>
 */
Ext.override(Ext.tree.MultiSelectionModel, {
	
	onNodeClick: function (node, e) {
		if (e.ctrlKey && this.isSelected(node)) {
			this.unselect(node);
		} else if (e.shiftKey && !this.isSelected(node)) {
			var parentNode = node.parentNode;
			// We can only shift select files in the same node
			if (this.lastSelNode.parentNode.id != parentNode.id) return;

			// Get the node indexes
			var fi = parentNode.indexOf(node),
				li = parentNode.indexOf(this.lastSelNode);

			// Select the last clicked node and wipe old selections
			this.select(this.lastSelNode, e, false, true);

			// Swap the values if required
			if (fi > li) {
				fi = fi + li, li = fi - li, fi = fi - li;
			}

			// Select all the nodes
			parentNode.eachChild(function(n) {
				var i = parentNode.indexOf(n);
				if (fi < i && i < li) {
					this.select(n, e, true, true);
				}
			}, this);

			// Select the clicked node
			this.select(node, e, true);
		} else {
			this.select(node, e, e.ctrlKey);
		}
	},

	select: function(node, e, keepExisting, suppressEvent) {
		if(keepExisting !== true){
			this.clearSelections(true);
		}         
		if(this.isSelected(node)){
			this.lastSelNode = node;
			return node;
		}         
		this.selNodes.push(node);
		this.selMap[node.id] = node;
		this.lastSelNode = node;
		node.ui.onSelectedChange(true);
		if (suppressEvent !== true) {
			this.fireEvent('selectionchange', this, this.selNodes);
		}
        return node;
	}

})
