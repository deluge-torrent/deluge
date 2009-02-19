Deluge.Login = {
    onLogin: function() {
        var passwordField = Deluge.Login.Form.items.get('password');
        Deluge.Client.web.login(passwordField.getValue(), {
            onSuccess: function(result) {
                if (result == true) {
                    Deluge.Login.Window.hide();
                    Deluge.Connections.Window.show();
                    passwordField.setRawValue('');
                    Deluge.Events.fire('login')
                } else {
                    Ext.MessageBox.show({
                        title: _('Login Failed'),
                        msg: _('You entered an incorrect password'),
                        buttons: Ext.MessageBox.OK,
                        modal: false,
                        icon: Ext.MessageBox.WARNING
                    });
                }
            }
        });
    },
    
    onLogout: function() {
        Deluge.Login.Window.show();
    },
    
    onKey: function(field, e) {
        if (e.getKey() == 13) Deluge.Login.onLogin();
    },
    
    onRender: function() {  
        Deluge.Events.on('logout', this.onLogout);
    }
}

Deluge.Login.Form = new Ext.form.FormPanel({
    defaultType: 'textfield',
    id: 'loginForm',
    baseCls: 'x-plain',
    labelWidth: 55,
    items: [{
        fieldLabel: _('Password'),
        id: 'password',
        name: 'password',
        inputType: 'password',
        anchor: '100%',
        listeners: {
            'specialkey': {
                fn: Deluge.Login.onKey,
                scope: Deluge.Login
            }
        }
    }]
});

Deluge.Login.Window = new Ext.Window({
    layout: 'fit',
    width: 300,
    height: 150,
    bodyStyle: 'padding: 10px 5px;',
    buttonAlign: 'center',
    closeAction: 'hide',
    closable: false,
    modal: true,
    plain: true,
    title: _('Login'),
    items: Deluge.Login.Form,
    buttons: [{
        text: _('Login'),
        handler: Deluge.Login.onLogin
    }],
    listeners: {'render': {fn: Deluge.Login.onRender, scope: Deluge.Login}}
});