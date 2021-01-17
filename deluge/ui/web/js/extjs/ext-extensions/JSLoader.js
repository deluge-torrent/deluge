Ext.ux.JSLoader = function (options) {
    Ext.ux.JSLoader.scripts[++Ext.ux.JSLoader.index] = {
        url: options.url,
        success: true,
        jsLoadObj: null,
        options: options,
        onLoad: options.onLoad || Ext.emptyFn,
        onError: options.onError || Ext.ux.JSLoader.stdError,
        scope: options.scope || this,
    };

    Ext.Ajax.request({
        url: options.url,
        scriptIndex: Ext.ux.JSLoader.index,
        success: function (response, options) {
            var script = Ext.ux.JSLoader.scripts[options.scriptIndex];
            try {
                eval(response.responseText);
            } catch (e) {
                script.success = false;
                script.onError(script.options, e);
            }
            if (script.success) {
                script.onLoad.call(script.scope, script.options);
            }
        },
        failure: function (response, options) {
            var script = Ext.ux.JSLoader.scripts[options.scriptIndex];
            script.success = false;
            script.onError(script.options, response.status);
        },
    });
};
Ext.ux.JSLoader.index = 0;
Ext.ux.JSLoader.scripts = [];
Ext.ux.JSLoader.stdError = function (options, e) {
    window.alert(
        'Error loading script:\n\n' + options.url + '\n\nstatus: ' + e
    );
};
