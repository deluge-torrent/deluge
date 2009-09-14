Deluge.Plugin = Ext.extend(Ext.util.Observable, {
    constructor: function(config) {
        this.name = config.name;
        this.addEvents({
            "enabled": true,
            "disabled": true
        });
        this.isDelugePlugin = true;
        Deluge.Plugin.superclass.constructor.call(config);
    }
});