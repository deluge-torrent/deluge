/**
 * Copyright (c) 2008, Steven Chim
 * All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 
 *     * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 *     * The names of its contributors may not be used to endorse or promote products derived from this software without specific prior written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/**
  * Ext.ux.form.Spinner Class
	*
	* @author  Steven Chim
	* @version Spinner.js 2008-08-27 v0.35
  *
  * @class Ext.ux.form.Spinner
  * @extends Ext.form.TriggerField
  */

Ext.namespace("Ext.ux.form");

Ext.ux.form.Spinner = function(config){
	Ext.ux.form.Spinner.superclass.constructor.call(this, config);
	this.addEvents({
		'spin' : true,
		'spinup' : true,
		'spindown' : true
	});
	this.initStrategy();
}

Ext.extend(Ext.ux.form.Spinner, Ext.form.TriggerField, {
	triggerClass : 'x-form-spinner-trigger',
	splitterClass : 'x-form-spinner-splitter',

	alternateKey : Ext.EventObject.shiftKey,
	strategy : undefined,

	//private
	onRender : function(ct, position){
		Ext.ux.form.Spinner.superclass.onRender.call(this, ct, position);

		this.splitter = this.wrap.createChild({tag:'div', cls:this.splitterClass, style:'width:13px; height:2px;'});
		this.splitter.show().setRight( (Ext.isIE) ? 1 : 2 );
		this.splitter.show().setTop(10);

		this.proxy = this.trigger.createProxy('', this.splitter, true);
		this.proxy.addClass("x-form-spinner-proxy");
		this.proxy.setStyle('left','0px');  
		this.proxy.setSize(14, 1);
		this.proxy.hide();
		this.dd = new Ext.dd.DDProxy(this.splitter.dom.id, "SpinnerDrag", {dragElId: this.proxy.id});

		this.initSpinner();
	},

	//private
	initTrigger : function(){
		this.trigger.addClassOnOver('x-form-trigger-over');
		this.trigger.addClassOnClick('x-form-trigger-click');
	},

	//private
	initSpinner : function(){
		this.keyNav = new Ext.KeyNav(this.el, {
			"up" : function(e){
				e.preventDefault();
				this.onSpinUp();
			},

			"down" : function(e){
				e.preventDefault();
				this.onSpinDown();
			},

			"pageUp" : function(e){
				e.preventDefault();
				this.onSpinUpAlternate();
			},

			"pageDown" : function(e){
				e.preventDefault();
				this.onSpinDownAlternate();
			},

			scope : this
		});

		this.repeater = new Ext.util.ClickRepeater(this.trigger);
		this.repeater.on("click", this.onTriggerClick, this, {preventDefault:true});
		this.trigger.on("mouseover", this.onMouseOver, this, {preventDefault:true});
		this.trigger.on("mouseout",  this.onMouseOut,  this, {preventDefault:true});
		this.trigger.on("mousemove", this.onMouseMove, this, {preventDefault:true});
		this.trigger.on("mousedown", this.onMouseDown, this, {preventDefault:true});
		this.trigger.on("mouseup",   this.onMouseUp,   this, {preventDefault:true});
		this.wrap.on("mousewheel",   this.handleMouseWheel, this);

		this.dd.setXConstraint(0, 0, 10)
		this.dd.setYConstraint(1500, 1500, 10);
		this.dd.endDrag = this.endDrag.createDelegate(this);
		this.dd.startDrag = this.startDrag.createDelegate(this);
		this.dd.onDrag = this.onDrag.createDelegate(this);
	},
	
	initStrategy: function() {
		/*
		jsakalos suggestion
		http://extjs.com/forum/showthread.php?p=121850#post121850 */
		if('object' == typeof this.strategy && this.strategy.xtype) {
		    switch(this.strategy.xtype) {
			case 'number':
			    this.strategy = new Ext.ux.form.Spinner.NumberStrategy(this.strategy);
				break;
	
			case 'date':
			    this.strategy = new Ext.ux.form.Spinner.DateStrategy(this.strategy);
				break;
	
			case 'time':
			    this.strategy = new Ext.ux.form.Spinner.TimeStrategy(this.strategy);
				break;
	
			default:
			    delete(this.strategy);
				break;
		    }
		    delete(this.strategy.xtype);
		}

		if(this.strategy == undefined){
			this.strategy = new Ext.ux.form.Spinner.NumberStrategy();
		}
	},

	//private
	onMouseOver : function(){
		if(this.disabled){
			return;
		}
		var middle = this.getMiddle();
		this.__tmphcls = (Ext.EventObject.getPageY() < middle) ? 'x-form-spinner-overup' : 'x-form-spinner-overdown';
		this.trigger.addClass(this.__tmphcls);
	},

	//private
	onMouseOut : function(){
		this.trigger.removeClass(this.__tmphcls);
	},

	//private
	onMouseMove : function(){
		if(this.disabled){
			return;
		}
		var middle = this.getMiddle();
		if( ((Ext.EventObject.getPageY() > middle) && this.__tmphcls == "x-form-spinner-overup") ||
			((Ext.EventObject.getPageY() < middle) && this.__tmphcls == "x-form-spinner-overdown")){
		}
	},

	//private
	onMouseDown : function(){
		if(this.disabled){
			return;
		}
		var middle = this.getMiddle();
		this.__tmpccls = (Ext.EventObject.getPageY() < middle) ? 'x-form-spinner-clickup' : 'x-form-spinner-clickdown';
		this.trigger.addClass(this.__tmpccls);
	},

	//private
	onMouseUp : function(){
		this.trigger.removeClass(this.__tmpccls);
	},

	//private
	onTriggerClick : function(){
		if(this.disabled || this.getEl().dom.readOnly){
			return;
		}
		var middle = this.getMiddle();
		var ud = (Ext.EventObject.getPageY() < middle) ? 'Up' : 'Down';
		this['onSpin'+ud]();
	},

	//private
	getMiddle : function(){
		var t = this.trigger.getTop();
		var h = this.trigger.getHeight();
		var middle = t + (h/2);
		return middle;
	},
	
	//private
	//checks if control is allowed to spin
	isSpinnable : function(){
		if(this.disabled || this.getEl().dom.readOnly){
			Ext.EventObject.preventDefault();	//prevent scrolling when disabled/readonly
			return false;
		}
		return true;
	},

	handleMouseWheel : function(e){
		//disable scrolling when not focused
		if(this.wrap.hasClass('x-trigger-wrap-focus') == false){
			return;
		}

		var delta = e.getWheelDelta();
		if(delta > 0){
			this.onSpinUp();
			e.stopEvent();
		} else if(delta < 0){
			this.onSpinDown();
			e.stopEvent();
		}
	},

	//private
	startDrag : function(){
		this.proxy.show();
		this._previousY = Ext.fly(this.dd.getDragEl()).getTop();
	},

	//private
	endDrag : function(){
		this.proxy.hide();
	},

	//private
	onDrag : function(){
		if(this.disabled){
			return;
		}
		var y = Ext.fly(this.dd.getDragEl()).getTop();
		var ud = '';

		if(this._previousY > y){ud = 'Up';}         //up
		if(this._previousY < y){ud = 'Down';}       //down

		if(ud != ''){
			this['onSpin'+ud]();
		}

		this._previousY = y;
	},

	//private
	onSpinUp : function(){
		if(this.isSpinnable() == false) {
			return;
		}
		if(Ext.EventObject.shiftKey == true){
			this.onSpinUpAlternate();
			return;
		}else{
			this.strategy.onSpinUp(this);
		}
		this.fireEvent("spin", this);
		this.fireEvent("spinup", this);
		this.fireEvent("change", this);
	},

	//private
	onSpinDown : function(){
		if(this.isSpinnable() == false) {
			return;
		}
		if(Ext.EventObject.shiftKey == true){
			this.onSpinDownAlternate();
			return;
		}else{
			this.strategy.onSpinDown(this);
		}
		this.fireEvent("spin", this);
		this.fireEvent("spindown", this);
		this.fireEvent("change", this);
	},

	//private
	onSpinUpAlternate : function(){
		if(this.isSpinnable() == false) {
			return;
		}
		this.strategy.onSpinUpAlternate(this);
		this.fireEvent("spin", this);
		this.fireEvent("spinup", this);
		this.fireEvent("change", this);
	},

	//private
	onSpinDownAlternate : function(){
		if(this.isSpinnable() == false) {
			return;
		}
		this.strategy.onSpinDownAlternate(this);
		this.fireEvent("spin", this);
		this.fireEvent("spindown", this);
		this.fireEvent("change", this);
	},
	
	setValue: function(value) {
		value = this.strategy.fixBoundries(value);
		this.setRawValue(value);
	}

});

Ext.reg('uxspinner', Ext.ux.form.Spinner);

/**
 * Copyright (c) 2008, Steven Chim
 * All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 
 *     * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 *     * The names of its contributors may not be used to endorse or promote products derived from this software without specific prior written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/***
 * Abstract Strategy
 */
Ext.ux.form.Spinner.Strategy = function(config){
	Ext.apply(this, config);
};

Ext.extend(Ext.ux.form.Spinner.Strategy, Ext.util.Observable, {
	defaultValue : 0,
	minValue : undefined,
	maxValue : undefined,
	incrementValue : 1,
	alternateIncrementValue : 5,
	validationTask : new Ext.util.DelayedTask(),
	
	onSpinUp : function(field){
		this.spin(field, false, false);
	},

	onSpinDown : function(field){
		this.spin(field, true, false);
	},

	onSpinUpAlternate : function(field){
		this.spin(field, false, true);
	},

	onSpinDownAlternate : function(field){
		this.spin(field, true, true);
	},

	spin : function(field, down, alternate){
		this.validationTask.delay(500, function(){field.validate()});
		//extend
	},

	fixBoundries : function(value){
		return value;
		//overwrite
	}
	
});

/***
 * Concrete Strategy: Numbers
 */
Ext.ux.form.Spinner.NumberStrategy = function(config){
	Ext.ux.form.Spinner.NumberStrategy.superclass.constructor.call(this, config);
};

Ext.extend(Ext.ux.form.Spinner.NumberStrategy, Ext.ux.form.Spinner.Strategy, {

    allowDecimals : true,
    decimalPrecision : 2,
    
	spin : function(field, down, alternate){
		Ext.ux.form.Spinner.NumberStrategy.superclass.spin.call(this, field, down, alternate);

		var v = parseFloat(field.getValue());
		var incr = (alternate == true) ? this.alternateIncrementValue : this.incrementValue;

		(down == true) ? v -= incr : v += incr ;
		v = (isNaN(v)) ? this.defaultValue : v;
		v = this.fixBoundries(v);
		field.setRawValue(v);
	},

	fixBoundries : function(value){
		var v = value;

		if(this.minValue != undefined && v < this.minValue){
			v = this.minValue;
		}
		if(this.maxValue != undefined && v > this.maxValue){
			v = this.maxValue;
		}

		return this.fixPrecision(v);
	},
	
    // private
    fixPrecision : function(value){
        var nan = isNaN(value);
        if(!this.allowDecimals || this.decimalPrecision == -1 || nan || !value){
            return nan ? '' : value;
        }
        return value.toFixed(this.decimalPrecision);
    }
});


/***
 * Concrete Strategy: Date
 */
Ext.ux.form.Spinner.DateStrategy = function(config){
	Ext.ux.form.Spinner.DateStrategy.superclass.constructor.call(this, config);
};

Ext.extend(Ext.ux.form.Spinner.DateStrategy, Ext.ux.form.Spinner.Strategy, {
	defaultValue : new Date(),
	format : "Y-m-d",
	incrementValue : 1,
	incrementConstant : Date.DAY,
	alternateIncrementValue : 1,
	alternateIncrementConstant : Date.MONTH,

	spin : function(field, down, alternate){
		Ext.ux.form.Spinner.DateStrategy.superclass.spin.call(this);

		var v = field.getRawValue();
		
		v = Date.parseDate(v, this.format);
		var dir = (down == true) ? -1 : 1 ;
		var incr = (alternate == true) ? this.alternateIncrementValue : this.incrementValue;
		var dtconst = (alternate == true) ? this.alternateIncrementConstant : this.incrementConstant;

		if(typeof this.defaultValue == 'string'){
			this.defaultValue = Date.parseDate(this.defaultValue, this.format);
		}

		v = (v) ? v.add(dtconst, dir*incr) : this.defaultValue;

		v = this.fixBoundries(v);
		field.setRawValue(Ext.util.Format.date(v,this.format));
	},
	
	//private
	fixBoundries : function(date){
		var dt = date;
		var min = (typeof this.minValue == 'string') ? Date.parseDate(this.minValue, this.format) : this.minValue ;
		var max = (typeof this.maxValue == 'string') ? Date.parseDate(this.maxValue, this.format) : this.maxValue ;

		if(this.minValue != undefined && dt < min){
			dt = min;
		}
		if(this.maxValue != undefined && dt > max){
			dt = max;
		}

		return dt;
	}

});

/***
 * Concrete Strategy: Time
 */
Ext.ux.form.Spinner.TimeStrategy = function(config){
	Ext.ux.form.Spinner.TimeStrategy.superclass.constructor.call(this, config);
};

Ext.extend(Ext.ux.form.Spinner.TimeStrategy, Ext.ux.form.Spinner.DateStrategy, {
	format : "H:i",
	incrementValue : 1,
	incrementConstant : Date.MINUTE,
	alternateIncrementValue : 1,
	alternateIncrementConstant : Date.HOUR
});

Ext.tree.ColumnTree = Ext.extend(Ext.tree.TreePanel, {
    lines:false,
    borderWidth: Ext.isBorderBox ? 0 : 2, // the combined left/right border for each cell
    cls:'x-column-tree',
    
    onRender : function(){
        Ext.tree.ColumnTree.superclass.onRender.apply(this, arguments);
        this.headers = this.body.createChild(
            {cls:'x-tree-headers'},this.innerCt.dom);

        var cols = this.columns, c;
        var totalWidth = 0;

        for(var i = 0, len = cols.length; i < len; i++){
             c = cols[i];
             totalWidth += c.width;
             this.headers.createChild({
                 cls:'x-tree-hd ' + (c.cls?c.cls+'-hd':''),
                 cn: {
                     cls:'x-tree-hd-text',
                     html: c.header
                 },
                 style:'width:'+(c.width-this.borderWidth)+'px;'
             });
        }
        this.headers.createChild({cls:'x-clear'});
        // prevent floats from wrapping when clipped
        this.headers.setWidth(totalWidth);
        this.innerCt.setWidth(totalWidth);
    }
});

Ext.tree.ColumnTreeNode = Ext.extend(Ext.tree.TreeNode, {
	
	setColumnValue: function(index, value) {
		var t = this.getOwnerTree();
		var oldValue = this[t.columns[index].dataIndex];
		this[t.columns[index].dataIndex] = value;
		this.attributes[[t.columns[index].dataIndex]] = value;
		if (this.rendered) {
			this.ui.onColumnValueChange(this, index, value, oldValue);
		}
		this.fireEvent('columnvaluechange', this, index, value, oldValue);
	}
});

Ext.tree.ColumnNodeUI = Ext.extend(Ext.tree.TreeNodeUI, {
    focus: Ext.emptyFn, // prevent odd scrolling behavior
	
	onColumnValueChange: function(n, colIndex, value, oldValue) {
		if (this.rendered) {
			var c = n.getOwnerTree().columns[colIndex];
			this.columnNodes[colIndex].innerHTML = (c.renderer ? c.renderer(value, n, null) : value);
		}
	},

    renderElements : function(n, a, targetNode, bulkRender){
        this.indentMarkup = n.parentNode ? n.parentNode.ui.getChildIndent() : '';

        var t = n.getOwnerTree();
        var cols = t.columns;
        var bw = t.borderWidth;
        var c = cols[0];
        
        var cb = typeof a.checked == 'boolean';
		var href = a.href ? a.href : Ext.isGecko ? "" : "#";

        var buf = [
             '<li class="x-tree-node"><div ext:tree-node-id="',n.id,'" class="x-tree-node-el x-tree-node-leaf x-unselectable ', a.cls,'" unselectable="on">',
                '<div class="x-tree-col" style="width:',c.width-bw,'px;">',
                    '<span class="x-tree-node-indent">',this.indentMarkup,"</span>",
                    '<img src="', this.emptyIcon, '" class="x-tree-ec-icon x-tree-elbow">',
                    '<img src="', a.icon || this.emptyIcon, '" class="x-tree-node-icon',(a.icon ? " x-tree-node-inline-icon" : ""),(a.iconCls ? " "+a.iconCls : ""),'" unselectable="on" />',
                    cb ? ('<input class="x-tree-node-cb" type="checkbox" ' + (a.checked ? 'checked="checked" />' : '/>')) : '',
                    '<a hidefocus="on" class="x-tree-node-anchor" href="',href,'" tabIndex="1" ',
                    a.hrefTarget ? ' target="'+a.hrefTarget+'"' : "", '>',
                    '<span unselectable="on">', n.text || (c.renderer ? c.renderer(a[c.dataIndex], n, a) : a[c.dataIndex]),"</span></a>",
                "</div>"];
         for(var i = 1, len = cols.length; i < len; i++){
             c = cols[i];

             buf.push('<div class="x-tree-col ',(c.cls?c.cls:''),'" style="width:',c.width-bw,'px;">',
                        '<div class="x-tree-col-text">',(c.renderer ? c.renderer(a[c.dataIndex], n, a) : a[c.dataIndex]),"</div>",
                      "</div>");
         }
         buf.push(
            '<div class="x-clear"></div></div>',
            '<ul class="x-tree-node-ct" style="display:none;"></ul>',
            "</li>");

        if(bulkRender !== true && n.nextSibling && n.nextSibling.ui.getEl()){
            this.wrap = Ext.DomHelper.insertHtml("beforeBegin",
                                n.nextSibling.ui.getEl(), buf.join(""));
        }else{
            this.wrap = Ext.DomHelper.insertHtml("beforeEnd", targetNode, buf.join(""));
        }

        this.elNode = this.wrap.childNodes[0];
        this.ctNode = this.wrap.childNodes[1];
        var cs = this.elNode.firstChild.childNodes;
        this.indentNode = cs[0];
        this.ecNode = cs[1];
        this.iconNode = cs[2];
		var index = 3;
        if(cb){
            this.checkbox = cs[3];
			// fix for IE6
			this.checkbox.defaultChecked = this.checkbox.checked;			
            index++;
        }
        this.anchor = cs[index];
		this.columnNodes = [cs[index].firstChild];
		for(var i = 1, len = cols.length; i < len; i++){
			this.columnNodes[i] = this.elNode.childNodes[i].firstChild;
		}
    }
});

Ext.form.FileUploadField = Ext.extend(Ext.form.TextField,  {
    /**
     * @cfg {String} buttonText The button text to display on the upload button (defaults to
     * 'Browse...').  Note that if you supply a value for {@link #buttonCfg}, the buttonCfg.text
     * value will be used instead if available.
     */
    buttonText: 'Browse...',
    /**
     * @cfg {Boolean} buttonOnly True to display the file upload field as a button with no visible
     * text field (defaults to false).  If true, all inherited TextField members will still be available.
     */
    buttonOnly: false,
    /**
     * @cfg {Number} buttonOffset The number of pixels of space reserved between the button and the text field
     * (defaults to 3).  Note that this only applies if {@link #buttonOnly} = false.
     */
    buttonOffset: 3,
    /**
     * @cfg {Object} buttonCfg A standard {@link Ext.Button} config object.
     */

    // private
    readOnly: true,
    
    /**
     * @hide 
     * @method autoSize
     */
    autoSize: Ext.emptyFn,
    
    // private
    initComponent: function(){
        Ext.form.FileUploadField.superclass.initComponent.call(this);
        
        this.addEvents(
            /**
             * @event fileselected
             * Fires when the underlying file input field's value has changed from the user
             * selecting a new file from the system file selection dialog.
             * @param {Ext.form.FileUploadField} this
             * @param {String} value The file value returned by the underlying file input field
             */
            'fileselected'
        );
    },
    
    // private
    onRender : function(ct, position){
        Ext.form.FileUploadField.superclass.onRender.call(this, ct, position);
        
        this.wrap = this.el.wrap({cls:'x-form-field-wrap x-form-file-wrap'});
        this.el.addClass('x-form-file-text');
        this.el.dom.removeAttribute('name');
        
        this.fileInput = this.wrap.createChild({
            id: this.getFileInputId(),
            name: this.name||this.getId(),
            cls: 'x-form-file',
            tag: 'input', 
            type: 'file',
            size: 1
        });
        
        var btnCfg = Ext.applyIf(this.buttonCfg || {}, {
            text: this.buttonText
        });
        this.button = new Ext.Button(Ext.apply(btnCfg, {
            renderTo: this.wrap
        }));
        
        if(this.buttonOnly){
            this.el.hide();
            this.wrap.setWidth(this.button.getEl().getWidth());
        }
        
        this.fileInput.on('change', function(){
            var v = this.fileInput.dom.value;
            this.setValue(v);
            this.fireEvent('fileselected', this, v);
        }, this);
    },
    
    // private
    getFileInputId: function(){
        return this.id+'-file';
    },
    
    // private
    onResize : function(w, h){
        Ext.form.FileUploadField.superclass.onResize.call(this, w, h);
        
        this.wrap.setWidth(w);
        
        if(!this.buttonOnly){
            var w = this.wrap.getWidth() - this.button.getEl().getWidth() - this.buttonOffset;
            this.el.setWidth(w);
        }
    },
    
    // private
    preFocus : Ext.emptyFn,
    
    // private
    getResizeEl : function(){
        return this.wrap;
    },

    // private
    getPositionEl : function(){
        return this.wrap;
    },

    // private
    alignErrorIcon : function(){
        this.errorIcon.alignTo(this.wrap, 'tl-tr', [2, 0]);
    }
    
});
Ext.reg('fileuploadfield', Ext.form.FileUploadField);

/**
  * Ext.ux.FullProgressBar Class
  *
  * @author Damien Churchill <damoxc@gmail.com>
  * @version 1.2
  *
  * @class Ext.deluge.ProgressBar
  * @extends Ext.ProgressBar
  * @constructor
  * @param {Object} config Configuration options
  */
Ext.ux.FullProgressBar = Ext.extend(Ext.ProgressBar, {
	initComponent: function() {
		Ext.ux.FullProgressBar.superclass.initComponent.call(this);
	},
	
	updateProgress: function(value, text, animate) {
		this.value = value || 0;
		if (text) {
			this.updateText(text);
		}
		
		if (this.rendered) {
			var w = Math.floor(value*this.el.dom.firstChild.offsetWidth / 100.0);
	        this.progressBar.setWidth(w, animate === true || (animate !== false && this.animate));
	        if (this.textTopEl) {
	            //textTopEl should be the same width as the bar so overflow will clip as the bar moves
	            this.textTopEl.removeClass('x-hidden').setWidth(w);
	        }
		}
		this.fireEvent('update', this, value, text);
		return this;
	}
});
Ext.reg('fullprogressbar', Ext.ux.FullProgressBar);


// Allow radiogroups to be treated as a single form element.
Ext.override(Ext.form.RadioGroup, {

	afterRender: function() {
		var that = this;
		this.items.each(function(i) {
			that.relayEvents(i, ['check']);
		});
		Ext.form.RadioGroup.superclass.afterRender.call(this)
	},

	getName: function() {
		return this.items.first().getName();
	},

	getValue: function() {
		var v;

		this.items.each(function(item) {
			v = item.getRawValue();
			return !item.getValue();
		});

		return v;
	},

	setValue: function(v) {
		if (!this.items.each) return;
		this.items.each(function(item) {
			var checked = (item.el.getValue() == String(v));
			item.setValue(checked);
		});
	}
});