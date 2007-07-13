class plugin_NetworkHealth:
    def __init__(self, path, deluge_core, deluge_interface):
        self.parent = deluge_interface # Using this, you can access the Deluge client
        self.core = deluge_core
        self.location = path

        self.counter = 30
        self.maxCount = self.counter
    
    def update(self):
        session_info = self.core.get_state()
        if not session_info['has_incoming_connections'] and \
                 session_info['num_peers'] > 1:
            message = "[No incoming connections]"
            self.counter = self.counter - 1
            if self.counter < 0:
                # self.parent.addMessage("No incoming connections: you may be behind a firewall or router. Perhaps you need to forward the relevant ports.", "W")
                self.counter  = self.maxCount*2
                self.maxCount = self.counter
        else:
            message = "[Health: OK]"
            self.counter = self.maxCount

        self.parent.statusbar_temp_msg = self.parent.statusbar_temp_msg + '   ' + message
