/**
 * Deluge.data.SortTypes.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge.data');

/**
 * Common sort functions that can be used for data Stores.
 *
 * @author Damien Churchill <damoxc@gmail.com>
 * @version 1.3
 *
 * @class Deluge.data.SortTypes
 * @singleton
 */
Deluge.data.SortTypes = {
    // prettier-ignore
    asIPAddress: function(value) {
        var d = value.match(
            /(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\:(\d+)/
        );
        return ((+d[1] * 256 + (+d[2])) * 256 + (+d[3])) * 256 + (+d[4]);
    },

    asQueuePosition: function (value) {
        return value > -1 ? value : Number.MAX_VALUE;
    },

    asName: function (value) {
        return String(value).toLowerCase();
    },
};
