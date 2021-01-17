/**
 * Ext.ux.tree.MultiSelectionModelFix.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
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
                (fi = fi + li), (li = fi - li), (fi = fi - li);
            }

            // Select all the nodes
            parentNode.eachChild(function (n) {
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

    select: function (node, e, keepExisting, suppressEvent) {
        if (keepExisting !== true) {
            this.clearSelections(true);
        }
        if (this.isSelected(node)) {
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
    },
});
