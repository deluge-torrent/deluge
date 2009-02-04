/*
 * Mootools Ext Adapter
 * Author: christoph.pojer@gmail.com - http://og5.net/christoph
 * Last Update: 6 April 2008
 * Version: 0.9a
 *
 * Requires:
 * Core, Browser, Array, Function, Number, String, Hash, Event, Class,
 * Class.Extras, Element, Element.Event, Element.Style, Element.Dimensions,
 * DomReady, Fx, Fx.CSS, Fx.Morph, Fx.Transitions, Request, Fx.Scroll
 *
 */

(function(){

Ext.lib.Dom = {
	getViewWidth : function(full) {
		return document['get'+(full ? 'Scroll' : '')+'Width']();
	},

    getViewHeight : function(full) {
		return document['get'+(full ? 'Scroll' : '')+'Height']();
    },

    getDocumentHeight: function() {
    	return document.getScrollHeight();
    },

    getDocumentWidth: function() {
    	return document.getScrollWidth();
    },

    getViewportHeight: function() {
        return document.getHeight();
    },

    getViewportWidth: function() {
        return document.getWidth();
    },

    isAncestor : function(p, c){
    	return $(p).hasChild(c);
    },

    getRegion : function(el){
        return Ext.lib.Region.getRegion(el);
    },

    getY : function(el){
        return $(el).getTop();
    },

    getX : function(el){
        return $(el).getLeft();
    },

    getXY : function(el){
    	return Hash.getValues($(el).getPosition());
    },

    setXY : function(el, xy){
    	var pts = Ext.get(el).translatePoints(xy);
    	Hash.each(pts, function(v, i){
    		if(!v) return;
    		$(el).setStyle(i, v+'px');
    	});
    },

    setX : function(el, x){
        this.setXY(el, [x, false]);
    },

    setY : function(el, y){
        this.setXY(el, [false, y]);
    }
};
function getElement(el){
	if($type(el)=='object') return new Document(el);
	
	return $(el);
}
Ext.lib.Event = {
    getPageX : function(e){
    	return new Event(e.browserEvent || e).page.x;
    },

    getPageY : function(e){
    	return new Event(e.browserEvent || e).page.y;
    },

    getXY : function(e){
    	var p = new Event(e.browserEvent || e).page;
    	return p ? [p.x, p.y] : [0, 0];
    },

    getTarget : function(e){
    	return new Event(e.browserEvent || e).target;
    },

    resolveTextNode: function(node) {
    	return node && 3 == node.nodeType ? node.parentNode : node;
    },

    getRelatedTarget: function(e) {
    	return new Event(e.browserEvent || e).relatedTarget;
    },

    on: function(el, e, fn){
    	el = getElement(el);
    	if(el) el.addListener(e, fn);
    },

    un: function(el, e, fn){
    	el = getElement(el);
    	if(el) el.removeListener(e, fn);
    },

    purgeElement: function(el){
       el = getElement(el);
    	if(el) el.removeEvents();
    },
    
    preventDefault: function(e){
        new Event(e.browserEvent || e).preventDefault();
    },

    stopPropagation: function(e){
        new Event(e.browserEvent || e).stopPropagation();
    },

    stopEvent: function(e){
        new Event(e.browserEvent || e).stop();
    },

    onAvailable: function(id, fn, scope){
    	if(Browser.loaded) fn.call(scope || window, $(id));
    	else document.addEvent('domready', fn);
    }
};

Ext.lib.Ajax = function(){
    var createSuccess = function(cb){
         return cb.success ? function(text, xml){
         	cb.success.call(cb.scope||window, {
                responseText: text,
                responseXML : xml,
                argument: cb.argument
            });
         } : Ext.emptyFn;
    };
    var createFailure = function(cb){
         return cb.failure ? function(text, xml){
            cb.failure.call(cb.scope||window, {
                responseText: text,
                responseXML : xml,
                argument: cb.argument
            });
         } : Ext.emptyFn;
    };
    return {
        request: function(method, uri, cb, data, options){
            var o = {
            	url: uri,
            	method: method.toLowerCase(),
                data: data || '',
                /*timeout: cb.timeout,*/
                onSuccess: createSuccess(cb),
                onFailure: createFailure(cb)
            };
            if(options){
            	if(options.headers)
                    o.headers = options.headers;
                
                if(options.xmlData){
                    o.method = 'post';
                    o.headers = {'Content-type': 'text/xml'};
                    o.data = options.xmlData;
                }
                if(options.jsonData){
                    o.method = 'post';
                    o.headers = {'Content-type': 'text/javascript'};
                    o.data = typeof options.jsonData == 'object' ? Ext.encode(options.jsonData) : options.jsonData;
                }
            }
            new Request(o).send();
        },

        formRequest: function(form, uri, cb, data, isUpload, sslUri){
        	new Request({
            	url: uri,
                method: (Ext.getDom(form).method || 'post').toLowerCase(),
                data: $(form).toQueryString()+(data?'&'+data:''),
                /*timeout: cb.timeout,*/
                onSuccess: createSuccess(cb),
                onFailure: createFailure(cb)
            }).send();
        },

        isCallInProgress: function(trans){
        	//still need a way to access the request object.
            return false;
        },

        abort: function(trans){
        	//like above
            return false;
        },
        
        serializeForm: function(form){
            return $(form.dom || form).toQueryString();
        }
    };
}();


Ext.lib.Anim = function(){
    
	var createAnim = function(cb, scope){
        return {
            stop : function(skipToLast){
                this.effect.pause();
            },

            isAnimated : function(){
                return !!this.effect.timer;
            },

            proxyCallback : function(){
                Ext.callback(cb, scope);
            }
        };
    };
    var transition = function(t){
    	if(!Fx.Transitions[t]) t = 'linear';
    	return Fx.Transitions[t];
    };
    var obj = {
        scroll : function(el, args, duration, easing, cb, scope){
            var anim = createAnim(cb, scope);
            anim.effect = new Fx.Scroll(el, {
			    duration: duration * 1000,
			    transisions: transition(easing),
			    onComplete: anim.proxyCallback
	   		}).start(args);
            return anim;
        },

        run : function(el, args, duration, easing, cb, scope, type){
            if(easing=='easeNone') easing = 'linear';
            var anim = createAnim(cb, scope);
            var style = {};
            for(i in args){
            	if(i=='points'){
            		var by, p, e = Ext.fly(el, '_animrun');
                    e.position();
                    if(by = args[i].by){
                        var xy = e.getXY();
                        p = e.translatePoints([xy[0]+by[0], xy[1]+by[1]]);
                    }else{
                        p = e.translatePoints(args[i].to);
                    }
                    style.left = p.left;
                    style.top = p.top;
            	}else{
            		style[i] = args[i].from ? [args[i].from, args[i].to] : [args[i].to];
            	}
            }
            anim.effect = new Fx.Morph(el, {
                duration: duration * 1000,
                transition: transition(easing),
                onComplete: anim.proxyCallback
            }).start(style);
            return anim;
        }
    };
    
    return Hash.extend(obj, {
    	motion: obj.run,
    	color: obj.run
	});
}();

Ext.lib.Region = function(t, r, b, l) {
    this.top = t;
    this[1] = t;
    this.right = r;
    this.bottom = b;
    this.left = l;
    this[0] = l;
};

Ext.lib.Region.prototype = {
    contains : function(region) {
        return ( region.left   >= this.left   &&
                 region.right  <= this.right  &&
                 region.top    >= this.top    &&
                 region.bottom <= this.bottom    );

    },

    getArea : function() {
        return ( (this.bottom - this.top) * (this.right - this.left) );
    },

    intersect : function(region) {
        var t = Math.max( this.top,    region.top    );
        var r = Math.min( this.right,  region.right  );
        var b = Math.min( this.bottom, region.bottom );
        var l = Math.max( this.left,   region.left   );

        if (b >= t && r >= l) {
            return new Ext.lib.Region(t, r, b, l);
        } else {
            return null;
        }
    },
    union : function(region) {
        var t = Math.min( this.top,    region.top    );
        var r = Math.max( this.right,  region.right  );
        var b = Math.max( this.bottom, region.bottom );
        var l = Math.min( this.left,   region.left   );

        return new Ext.lib.Region(t, r, b, l);
    },

    constrainTo : function(r) {
            this.top = this.top.constrain(r.top, r.bottom);
            this.bottom = this.bottom.constrain(r.top, r.bottom);
            this.left = this.left.constrain(r.left, r.right);
            this.right = this.right.constrain(r.left, r.right);
            return this;
    },

    adjust : function(t, l, b, r){
        this.top += t;
        this.left += l;
        this.right += r;
        this.bottom += b;
        return this;
    }
};

Ext.lib.Region.getRegion = function(el) {
    var p = Ext.lib.Dom.getXY(el);
	
    var t = p[1];
    var r = p[0] + el.offsetWidth;
    var b = p[1] + el.offsetHeight;
    var l = p[0];

    return new Ext.lib.Region(t, r, b, l);
};

Ext.lib.Point = function(x, y) {
   if (Ext.isArray(x)) {
      y = x[1];
      x = x[0];
   }
    this.x = this.right = this.left = this[0] = x;
    this.y = this.top = this.bottom = this[1] = y;
};

Ext.lib.Point.prototype = new Ext.lib.Region();
})();