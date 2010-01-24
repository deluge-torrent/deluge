Ext.tree.CustomColumn = Ext.extend(Ext.tree.Column, {
	
	constructor: function(c) {
		c.tpl = c.tpl || new Ext.XTemplate('{' + c.dataIndex + ':this.format}');
		c.tpl.format = c.renderer;
		Ext.tree.CustomColumn.superclass.constructor.call(this, c);
	}
});
Ext.reg('tgcustomcolumn', Ext.tree.CustomColumn);
