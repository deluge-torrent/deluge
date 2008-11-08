/*
see : gtkui/sidebar_menu.py:
    def apply_sensitivity(self, event=None):
        for chk_id , sensitive_list in self.sensitive_groups:
            chk = self.glade.get_widget(chk_id)
            sens = chk.get_active() and chk.get_property("sensitive")
            for widget_id in sensitive_list:
                self.glade.get_widget(widget_id).set_sensitive(sens)
*/

var sensitive_groups = [
    ["apply_max", ["max_download_speed", "max_upload_speed", "max_upload_slots", "max_connections"]],
    ["apply_queue", ["is_auto_managed", "stop_at_ratio"]],
    ["stop_at_ratio", ["remove_at_ratio", "stop_ratio"]], /*#nested*/
    ["apply_move_completed", ["move_completed"]],
    ["move_completed", ["move_completed_path"]], /*#nested*/
    ["auto_add", ["auto_add_trackers"]]
];


