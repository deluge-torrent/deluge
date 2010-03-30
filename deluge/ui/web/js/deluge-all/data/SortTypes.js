/*!
 * Deluge.data.SortTypes.js
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
	asIPAddress: function(value) {
		var d = value.match(/(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\:(\d+)/);
		return ((((((+d[1])*256)+(+d[2]))*256)+(+d[3]))*256)+(+d[4]);
	},

	asQueuePosition: function(value) {
		return (value > -1) ? value : Number.MAX_VALUE;
	}
}
