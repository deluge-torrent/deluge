/**
 * Deluge.add.OptionsPanel.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge.add');

Deluge.add.OptionsPanel = Ext.extend(Ext.TabPanel, {
    torrents: {},

    // layout options
    region: 'south',
    border: false,
    activeTab: 0,
    height: 265,

    initComponent: function () {
        Deluge.add.OptionsPanel.superclass.initComponent.call(this);
        this.files = this.add(new Deluge.add.FilesTab());
        this.form = this.add(new Deluge.add.OptionsTab());

        this.files.on('fileschecked', this.onFilesChecked, this);
    },

    addTorrent: function (torrent) {
        this.torrents[torrent['info_hash']] = torrent;
        var fileIndexes = {};
        this.walkFileTree(
            torrent['files_tree'],
            function (filename, type, entry, parent) {
                if (type != 'file') return;
                fileIndexes[entry.index] = entry.download;
            },
            this
        );

        var priorities = [];
        Ext.each(Ext.keys(fileIndexes), function (index) {
            priorities[index] = fileIndexes[index];
        });

        var oldId = this.form.optionsManager.changeId(
            torrent['info_hash'],
            true
        );
        this.form.optionsManager.setDefault('file_priorities', priorities);
        this.form.optionsManager.changeId(oldId, true);
    },

    clear: function () {
        this.files.clearFiles();
        this.form.optionsManager.resetAll();
    },

    getFilename: function (torrentId) {
        return this.torrents[torrentId]['filename'];
    },

    getOptions: function (torrentId) {
        var oldId = this.form.optionsManager.changeId(torrentId, true);
        var options = this.form.optionsManager.get();
        this.form.optionsManager.changeId(oldId, true);
        Ext.each(options['file_priorities'], function (priority, index) {
            options['file_priorities'][index] = priority ? 1 : 0;
        });
        return options;
    },

    setTorrent: function (torrentId) {
        if (!torrentId) return;

        this.torrentId = torrentId;
        this.form.optionsManager.changeId(torrentId);

        this.files.clearFiles();
        var root = this.files.getRootNode();
        var priorities = this.form.optionsManager.get('file_priorities');

        this.form.setDisabled(false);

        if (this.torrents[torrentId]['files_tree']) {
            this.walkFileTree(
                this.torrents[torrentId]['files_tree'],
                function (filename, type, entry, parentNode) {
                    var node = new Ext.tree.TreeNode({
                        download: entry.index ? priorities[entry.index] : true,
                        filename: filename,
                        fileindex: entry.index,
                        leaf: type != 'dir',
                        size: entry.length,
                    });
                    parentNode.appendChild(node);
                    if (type == 'dir') return node;
                },
                this,
                root
            );
            root.firstChild.expand();
            this.files.setDisabled(false);
            this.files.show();
        } else {
            // Files tab is empty so show options tab
            this.form.show();
            this.files.setDisabled(true);
        }
    },

    walkFileTree: function (files, callback, scope, parentNode) {
        for (var filename in files.contents) {
            var entry = files.contents[filename];
            var type = entry.type;

            if (scope) {
                var ret = callback.apply(scope, [
                    filename,
                    type,
                    entry,
                    parentNode,
                ]);
            } else {
                var ret = callback(filename, type, entry, parentNode);
            }

            if (type == 'dir') this.walkFileTree(entry, callback, scope, ret);
        }
    },

    onFilesChecked: function (nodes, newValue, oldValue) {
        Ext.each(
            nodes,
            function (node) {
                if (node.attributes.fileindex < 0) return;
                var priorities = this.form.optionsManager.get(
                    'file_priorities'
                );
                priorities[node.attributes.fileindex] = newValue;
                this.form.optionsManager.update('file_priorities', priorities);
            },
            this
        );
    },
});
