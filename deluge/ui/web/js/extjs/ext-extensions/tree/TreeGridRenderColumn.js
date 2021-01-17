Ext.tree.RenderColumn = Ext.extend(Ext.tree.Column, {
    constructor: function (c) {
        c.tpl = c.tpl || new Ext.XTemplate('{' + c.dataIndex + ':this.format}');
        c.tpl.format = c.renderer;
        c.tpl.col = this;
        Ext.tree.RenderColumn.superclass.constructor.call(this, c);
    },
});
Ext.reg('tgrendercolumn', Ext.tree.RenderColumn);
