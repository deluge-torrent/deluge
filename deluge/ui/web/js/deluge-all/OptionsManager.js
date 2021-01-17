/**
 * Deluge.OptionsManager.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Deluge');

/**
 * @class Deluge.OptionsManager
 * @extends Ext.util.Observable
 * A class that can be used to manage options throughout the ui.
 * @constructor
 * Creates a new OptionsManager
 * @param {Object} config Configuration options
 */
Deluge.OptionsManager = Ext.extend(Ext.util.Observable, {
    constructor: function (config) {
        config = config || {};
        this.binds = {};
        this.changed = {};
        this.options = (config && config['options']) || {};
        this.focused = null;

        this.addEvents({
            /**
             * @event add
             * Fires when an option is added
             */
            add: true,

            /**
             * @event changed
             * Fires when an option is changed
             * @param {String} option The changed option
             * @param {Mixed} value The options new value
             * @param {Mixed} oldValue The options old value
             */
            changed: true,

            /**
             * @event reset
             * Fires when the options are reset
             */
            reset: true,
        });
        this.on('changed', this.onChange, this);

        Deluge.OptionsManager.superclass.constructor.call(this);
    },

    /**
     * Add a set of default options and values to the options manager
     * @param {Object} options The default options.
     */
    addOptions: function (options) {
        this.options = Ext.applyIf(this.options, options);
    },

    /**
     * Binds a form field to the specified option.
     * @param {String} option
     * @param {Ext.form.Field} field
     */
    bind: function (option, field) {
        this.binds[option] = this.binds[option] || [];
        this.binds[option].push(field);
        field._doption = option;

        field.on('focus', this.onFieldFocus, this);
        field.on('blur', this.onFieldBlur, this);
        field.on('change', this.onFieldChange, this);
        field.on('check', this.onFieldChange, this);
        field.on('spin', this.onFieldChange, this);
        return field;
    },

    /**
     * Changes all the changed values to be the default values
     */
    commit: function () {
        this.options = Ext.apply(this.options, this.changed);
        this.reset();
    },

    /**
     * Converts the value so it matches the originals type
     * @param {Mixed} oldValue The original value
     * @param {Mixed} value The new value to convert
     */
    convertValueType: function (oldValue, value) {
        if (Ext.type(oldValue) != Ext.type(value)) {
            switch (Ext.type(oldValue)) {
                case 'string':
                    value = String(value);
                    break;
                case 'number':
                    value = Number(value);
                    break;
                case 'boolean':
                    if (Ext.type(value) == 'string') {
                        value = value.toLowerCase();
                        value =
                            value == 'true' || value == '1' || value == 'on'
                                ? true
                                : false;
                    } else {
                        value = Boolean(value);
                    }
                    break;
            }
        }
        return value;
    },

    /**
     * Get the value for an option or options.
     * @param {String} [option] A single option or an array of options to return.
     * @returns {Object} the options value.
     */
    get: function () {
        if (arguments.length == 1) {
            var option = arguments[0];
            return this.isDirty(option)
                ? this.changed[option]
                : this.options[option];
        } else {
            var options = {};
            Ext.each(
                arguments,
                function (option) {
                    if (!this.has(option)) return;
                    options[option] = this.isDirty(option)
                        ? this.changed[option]
                        : this.options[option];
                },
                this
            );
            return options;
        }
    },

    /**
     * Get the default value for an option or options.
     * @param {String|Array} [option] A single option or an array of options to return.
     * @returns {Object} the value of the option
     */
    getDefault: function (option) {
        return this.options[option];
    },

    /**
     * Returns the dirty (changed) values.
     * @returns {Object} the changed options
     */
    getDirty: function () {
        return this.changed;
    },

    /**
     * @param {String} [option] The option to check
     * @returns {Boolean} true if the option has been changed from the default.
     */
    isDirty: function (option) {
        return !Ext.isEmpty(this.changed[option]);
    },

    /**
     * Check to see if an option exists in the options manager
     * @param {String} option
     * @returns {Boolean} true if the option exists, else false.
     */
    has: function (option) {
        return this.options[option];
    },

    /**
     * Reset the options back to the default values.
     */
    reset: function () {
        this.changed = {};
    },

    /**
     * Sets the value of specified option(s) for the passed in id.
     * @param {String} option
     * @param {Object} value The value for the option
     */
    set: function (option, value) {
        if (option === undefined) {
            return;
        } else if (typeof option == 'object') {
            var options = option;
            this.options = Ext.apply(this.options, options);
            for (var option in options) {
                this.onChange(option, options[option]);
            }
        } else {
            this.options[option] = value;
            this.onChange(option, value);
        }
    },

    /**
     * Update the value for the specified option and id.
     * @param {String/Object} option or options to update
     * @param {Object} [value];
     */
    update: function (option, value) {
        if (option === undefined) {
            return;
        } else if (value === undefined) {
            for (var key in option) {
                this.update(key, option[key]);
            }
        } else {
            var defaultValue = this.getDefault(option);
            value = this.convertValueType(defaultValue, value);

            var oldValue = this.get(option);
            if (oldValue == value) return;

            if (defaultValue == value) {
                if (this.isDirty(option)) delete this.changed[option];
                this.fireEvent('changed', option, value, oldValue);
                return;
            }

            this.changed[option] = value;
            this.fireEvent('changed', option, value, oldValue);
        }
    },

    /**
     * Lets the option manager know when a field is blurred so if a value
     * so value changing operations can continue on that field.
     */
    onFieldBlur: function (field, event) {
        if (this.focused == field) {
            this.focused = null;
        }
    },

    /**
     * Stops a form fields value from being blocked by the change functions
     * @param {Ext.form.Field} field
     * @private
     */
    onFieldChange: function (field, event) {
        if (field.field) field = field.field; // fix for spinners
        this.update(field._doption, field.getValue());
    },

    /**
     * Lets the option manager know when a field is focused so if a value changing
     * operation is performed it will not change the value of the field.
     */
    onFieldFocus: function (field, event) {
        this.focused = field;
    },

    onChange: function (option, newValue, oldValue) {
        // If we don't have a bind there's nothing to do.
        if (Ext.isEmpty(this.binds[option])) return;
        Ext.each(
            this.binds[option],
            function (bind) {
                // The field is currently focused so we do not want to change it.
                if (bind == this.focused) return;
                // Set the form field to the new value.
                bind.setValue(newValue);
            },
            this
        );
    },
});
