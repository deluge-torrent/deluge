/**
 * Deluge.MultiOptionsManager.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

/**
 * @description A class that can be used to manage options throughout the ui.
 * @namespace Deluge
 * @class Deluge.MultiOptionsManager
 * @extends Deluge.OptionsManager
 */
Deluge.MultiOptionsManager = Ext.extend(Deluge.OptionsManager, {
    constructor: function (config) {
        this.currentId = null;
        this.stored = {};
        Deluge.MultiOptionsManager.superclass.constructor.call(this, config);
    },

    /**
     * Changes bound fields to use the specified id.
     * @param {String} id
     */
    changeId: function (id, dontUpdateBinds) {
        var oldId = this.currentId;
        this.currentId = id;
        if (!dontUpdateBinds) {
            for (var option in this.options) {
                if (!this.binds[option]) continue;
                Ext.each(
                    this.binds[option],
                    function (bind) {
                        bind.setValue(this.get(option));
                    },
                    this
                );
            }
        }
        return oldId;
    },

    /**
     * Changes all the changed values to be the default values
     * @param {String} id
     */
    commit: function () {
        this.stored[this.currentId] = Ext.apply(
            this.stored[this.currentId],
            this.changed[this.currentId]
        );
        this.reset();
    },

    /**
     * Get the value for an option
     * @param {String/Array} option A single option or an array of options to return.
     * @returns {Object} the options value.
     */
    get: function () {
        if (arguments.length == 1) {
            var option = arguments[0];
            return this.isDirty(option)
                ? this.changed[this.currentId][option]
                : this.getDefault(option);
        } else if (arguments.length == 0) {
            var options = {};
            for (var option in this.options) {
                options[option] = this.isDirty(option)
                    ? this.changed[this.currentId][option]
                    : this.getDefault(option);
            }
            return options;
        } else {
            var options = {};
            Ext.each(
                arguments,
                function (option) {
                    options[option] = this.isDirty(option)
                        ? this.changed[this.currentId][option]
                        : this.getDefault(option);
                },
                this
            );
            return options;
        }
    },

    /**
     * Get the default value for an option.
     * @param {String} option A single option.
     * @returns {Object} the value of the option
     */
    getDefault: function (option) {
        return this.has(option)
            ? this.stored[this.currentId][option]
            : this.options[option];
    },

    /**
     * Returns the dirty (changed) values.
     * @returns {Object} the changed options
     */
    getDirty: function () {
        return this.changed[this.currentId] ? this.changed[this.currentId] : {};
    },

    /**
     * Check to see if the option has been changed.
     * @param {String} option
     * @returns {Boolean} true if the option has been changed, else false.
     */
    isDirty: function (option) {
        return (
            this.changed[this.currentId] &&
            !Ext.isEmpty(this.changed[this.currentId][option])
        );
    },

    /**
     * Check to see if an id has had an option set to something other than the
     * default value.
     * @param {String} option
     * @returns {Boolean} true if the id has an option, else false.
     */
    has: function (option) {
        return (
            this.stored[this.currentId] &&
            !Ext.isEmpty(this.stored[this.currentId][option])
        );
    },

    /**
     * Reset the options back to the default values for the specified id.
     */
    reset: function () {
        if (this.changed[this.currentId]) delete this.changed[this.currentId];
        if (this.stored[this.currentId]) delete this.stored[this.currentId];
    },

    /**
     * Reset the options back to their defaults for all ids.
     */
    resetAll: function () {
        this.changed = {};
        this.stored = {};
        this.changeId(null);
    },

    /**
     * Sets the value of specified option for the passed in id.
     * @param {String} id
     * @param {String} option
     * @param {Object} value The value for the option
     */
    setDefault: function (option, value) {
        if (option === undefined) {
            return;
        } else if (value === undefined) {
            for (var key in option) {
                this.setDefault(key, option[key]);
            }
        } else {
            var oldValue = this.getDefault(option);
            value = this.convertValueType(oldValue, value);

            // If the value is the same as the old value there is
            // no point in setting it again.
            if (oldValue == value) return;

            // Store the new default
            if (!this.stored[this.currentId]) this.stored[this.currentId] = {};
            this.stored[this.currentId][option] = value;

            if (!this.isDirty(option)) {
                this.fireEvent('changed', option, value, oldValue);
            }
        }
    },

    /**
     * Update the value for the specified option and id.
     * @param {String} id
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
            if (!this.changed[this.currentId])
                this.changed[this.currentId] = {};

            var defaultValue = this.getDefault(option);
            value = this.convertValueType(defaultValue, value);

            var oldValue = this.get(option);
            if (oldValue == value) return;

            if (defaultValue == value) {
                if (this.isDirty(option))
                    delete this.changed[this.currentId][option];
                this.fireEvent('changed', option, value, oldValue);
                return;
            } else {
                this.changed[this.currentId][option] = value;
                this.fireEvent('changed', option, value, oldValue);
            }
        }
    },
});
