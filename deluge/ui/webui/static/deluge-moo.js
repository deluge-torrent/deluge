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
*/



/*
= InputSensitivitySetter =
see : gtkui/sidebar_menu.py:
    def apply_sensitivity(self, event=None):
        for chk_id , sensitive_list in self.sensitive_groups:
            chk = self.glade.get_widget(chk_id)
            sens = chk.get_active() and chk.get_property("sensitive")
            for widget_id in sensitive_list:
                self.glade.get_widget(widget_id).set_sensitive(sens)


Sets disabled property of input fields according to value of checkboxes.
Example (see label plugin)

new InputSensitivitySetter({prefix:"id_",groups:[
    ["apply_max", ["max_download_speed", "max_upload_speed", "max_upload_slots", "max_connections"]],
    ["apply_queue", ["is_auto_managed", "stop_at_ratio"]],
    ["stop_at_ratio", ["remove_at_ratio", "stop_ratio"]], #nested
    ["apply_move_completed", ["move_completed"]],
    ["move_completed", ["move_completed_path"]], #nested
    ["auto_add", ["auto_add_trackers"]]
]});

*/
var InputSensitivitySetter = new Class({
    Implements: [Options, Events],
    options: {
        groups : [],
        prefix : "" /*django forms prefixes input elements with id_*/
    },
    initialize :function(options){
        this.setOptions(options);
        this.attachWidgets();
        this.appySensitivity();
    }
    ,attachWidgets: function() {
        this.options.groups.each(function(group, i) {
            el = $(this.options.prefix + group[0]);
            el.addEvent('click', this.appySensitivity.bind(this));
        }, this);
    }
    ,appySensitivity: function () {
	this.options.groups.each(function(group, i) {
            var el = $(this.options.prefix + group[0]);
            var widgets = group[1];
            var sensitive = (el.checked && !el.get('disabled'));
            widgets.each(function(widget, i) {
                $(this.options.prefix + widget).set('disabled', !sensitive);
            },this);
	},this);
    }
});
