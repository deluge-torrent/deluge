Deluge.Login = {
    Form: new Ext.form.FormPanel({
        defaultType: 'textfield',
        id: 'loginForm',
        baseCls: 'x-plain',
        labelWidth: 55,
        items: [{
            fieldLabel: 'Password',
            id: 'password',
            name: 'password',
            inputType: 'password',
            anchor: '100%'
        }]
    }),
    
    onLogin: function() {
        var passwordField = Deluge.Login.Form.items.get('password');
        Deluge.Client.web.login(passwordField.getValue(), {
            onSuccess: function(result) {
                if (result == true) {
                    Deluge.Login.Window.hide();
                }
            }
        });
    }
}

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
    title: 'Login',
    items: Deluge.Login.Form,
    buttons: [{
        text: 'Login',
        handler: Deluge.Login.onLogin
    }]
});