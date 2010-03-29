Ext.override(Ext.form.TriggerField, {
	onResize: function(w, h) {
		Ext.form.TriggerField.superclass.onResize.call(this, w, h);
		var tw = this.getTriggerWidth();
		if (Ext.isNumber(w)) {
			this.el.setWidth(w - tw);
		}
		this.wrap.setWidth(w);
	}
});
