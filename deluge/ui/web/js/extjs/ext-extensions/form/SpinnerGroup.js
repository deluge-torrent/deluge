/**
 * Ext.ux.form.SpinnerGroup.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Ext.ux.form');

/**
 *
 */
Ext.ux.form.SpinnerGroup = Ext.extend(Ext.form.CheckboxGroup, {
    // private
    defaultType: 'spinnerfield',
    anchor: '98%',

    // private
    groupCls: 'x-form-spinner-group',

    colCfg: {},

    // private
    onRender: function (ct, position) {
        if (!this.el) {
            var panelCfg = {
                cls: this.groupCls,
                layout: 'column',
                border: false,
                renderTo: ct,
            };
            var colCfg = Ext.apply(
                {
                    defaultType: this.defaultType,
                    layout: 'form',
                    border: false,
                    labelWidth: 60,
                    defaults: {
                        hideLabel: true,
                        anchor: '60%',
                    },
                },
                this.colCfg
            );

            if (this.items[0].items) {
                // The container has standard ColumnLayout configs, so pass them in directly

                Ext.apply(panelCfg, {
                    layoutConfig: { columns: this.items.length },
                    defaults: this.defaults,
                    items: this.items,
                });
                for (var i = 0, len = this.items.length; i < len; i++) {
                    Ext.applyIf(this.items[i], colCfg);
                }
            } else {
                // The container has field item configs, so we have to generate the column
                // panels first then move the items into the columns as needed.

                var numCols,
                    cols = [];

                if (typeof this.columns == 'string') {
                    // 'auto' so create a col per item
                    this.columns = this.items.length;
                }
                if (!Ext.isArray(this.columns)) {
                    var cs = [];
                    for (var i = 0; i < this.columns; i++) {
                        cs.push((100 / this.columns) * 0.01); // distribute by even %
                    }
                    this.columns = cs;
                }

                numCols = this.columns.length;

                // Generate the column configs with the correct width setting
                for (var i = 0; i < numCols; i++) {
                    var cc = Ext.apply({ items: [] }, colCfg);
                    cc[
                        this.columns[i] <= 1 ? 'columnWidth' : 'width'
                    ] = this.columns[i];
                    if (this.defaults) {
                        cc.defaults = Ext.apply(
                            cc.defaults || {},
                            this.defaults
                        );
                    }
                    cols.push(cc);
                }

                // Distribute the original items into the columns
                if (this.vertical) {
                    var rows = Math.ceil(this.items.length / numCols),
                        ri = 0;
                    for (var i = 0, len = this.items.length; i < len; i++) {
                        if (i > 0 && i % rows == 0) {
                            ri++;
                        }
                        if (this.items[i].fieldLabel) {
                            this.items[i].hideLabel = false;
                        }
                        cols[ri].items.push(this.items[i]);
                    }
                } else {
                    for (var i = 0, len = this.items.length; i < len; i++) {
                        var ci = i % numCols;
                        if (this.items[i].fieldLabel) {
                            this.items[i].hideLabel = false;
                        }
                        cols[ci].items.push(this.items[i]);
                    }
                }

                Ext.apply(panelCfg, {
                    layoutConfig: { columns: numCols },
                    items: cols,
                });
            }

            this.panel = new Ext.Panel(panelCfg);
            this.el = this.panel.getEl();

            if (this.forId && this.itemCls) {
                var l = this.el.up(this.itemCls).child('label', true);
                if (l) {
                    l.setAttribute('htmlFor', this.forId);
                }
            }

            var fields = this.panel.findBy(function (c) {
                return c.isFormField;
            }, this);

            this.items = new Ext.util.MixedCollection();
            this.items.addAll(fields);

            this.items.each(function (field) {
                field.on('spin', this.onFieldChange, this);
                field.on('change', this.onFieldChange, this);
            }, this);

            if (this.lazyValueSet) {
                this.setValue(this.value);
                delete this.value;
                delete this.lazyValueSet;
            }

            if (this.lazyRawValueSet) {
                this.setRawValue(this.rawValue);
                delete this.rawValue;
                delete this.lazyRawValueSet;
            }
        }

        Ext.ux.form.SpinnerGroup.superclass.onRender.call(this, ct, position);
    },

    onFieldChange: function (spinner) {
        this.fireEvent('change', this, this.getValue());
    },

    initValue: Ext.emptyFn,

    getValue: function () {
        var value = [this.items.getCount()];
        this.items.each(function (item, i) {
            value[i] = Number(item.getValue());
        });
        return value;
    },

    getRawValue: function () {
        var value = [this.items.getCount()];
        this.items.each(function (item, i) {
            value[i] = Number(item.getRawValue());
        });
        return value;
    },

    setValue: function (value) {
        if (!this.rendered) {
            this.value = value;
            this.lazyValueSet = true;
        } else {
            this.items.each(function (item, i) {
                item.setValue(value[i]);
            });
        }
    },

    setRawValue: function (value) {
        if (!this.rendered) {
            this.rawValue = value;
            this.lazyRawValueSet = true;
        } else {
            this.items.each(function (item, i) {
                item.setRawValue(value[i]);
            });
        }
    },
});
Ext.reg('spinnergroup', Ext.ux.form.SpinnerGroup);
