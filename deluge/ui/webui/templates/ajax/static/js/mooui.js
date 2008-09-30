
(function(){function pad(val,len){val=String(val);len=len||2;while(val.length<len)val="0"+val;return val;};var token=/d{1,4}|m{1,4}|yy(?:yy)?|([HhMsTt])\1?|[LloSZ]|"[^"]*"|'[^']*'/g,timezone=/\b(?:[PMCEA][SDP]T|(?:Pacific|Mountain|Central|Eastern|Atlantic) (?:Standard|Daylight|Prevailing) Time|(?:GMT|UTC)(?:[-+]\d{4})?)\b/g,timezoneClip=/[^-+\dA-Z]/g
Date.implement({i18n:{dayNames:["Sun","Mon","Tue","Wed","Thu","Fri","Sat","Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],monthNames:["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","January","February","March","April","May","June","July","August","September","October","November","December"]},masks:{'default':"ddd mmm dd yyyy HH:MM:ss",shortDate:"m/d/yy",mediumDate:"mmm d, yyyy",longDate:"mmmm d, yyyy",fullDate:"dddd, mmmm d, yyyy",shortTime:"h:MM TT",mediumTime:"h:MM:ss TT",longTime:"h:MM:ss TT Z",isoDate:"yyyy-mm-dd",isoTime:"HH:MM:ss",isoDateTime:"yyyy-mm-dd'T'HH:MM:ss",isoUtcDateTime:"UTC:yyyy-mm-dd'T'HH:MM:ss'Z'"},format:function(mask,utc){mask=String(this.masks[mask]||mask||this.masks["default"]);if(mask.slice(0,4)=="UTC:"){mask=mask.slice(4);utc=true;}
var _=utc?"getUTC":"get",d=this[_+"Date"](),D=this[_+"Day"](),m=this[_+"Month"](),y=this[_+"FullYear"](),H=this[_+"Hours"](),M=this[_+"Minutes"](),s=this[_+"Seconds"](),L=this[_+"Milliseconds"](),o=utc?0:this.getTimezoneOffset(),flags={d:d,dd:pad(d),ddd:this.i18n.dayNames[D],dddd:this.i18n.dayNames[D+7],m:m+1,mm:pad(m+1),mmm:this.i18n.monthNames[m],mmmm:this.i18n.monthNames[m+12],yy:String(y).slice(2),yyyy:y,h:H%12||12,hh:pad(H%12||12),H:H,HH:pad(H),M:M,MM:pad(M),s:s,ss:pad(s),l:pad(L,3),L:pad(L>99?Math.round(L/10):L),t:H<12?"a":"p",tt:H<12?"am":"pm",T:H<12?"A":"P",TT:H<12?"AM":"PM",Z:utc?"UTC":(String(this).match(timezone)||[""]).pop().replace(timezoneClip,""),o:(o>0?"-":"+")+pad(Math.floor(Math.abs(o)/60)*100+Math.abs(o)%60,4),S:["th","st","nd","rd"][d%10>3?0:(d%100-d%10!=10)*d%10]};return mask.replace(token,function($0){return $0 in flags?flags[$0]:$0.slice(1,$0.length-1);});}});})()
Array.implement({sum:function(key){var total=0
this.each(function(item){var value=item
if(!$defined(value))return;if($defined(key)){value=item[key]}
if($type(value)=='number'){total+=value}},this)
return total}})
Element.implement({getInnerSize:function(){this.getPadding();if((/^(?:body|html)$/i).test(this.tagName))return this.getWindow().getSize();return{x:this.clientWidth-this.padding.x,y:this.clientHeight-this.padding.y};},getInnerHeight:function(){return this.getInnerSize().y;},getInnerWidth:function(){return this.getInnerSize().x;},getSizeModifiers:function(update){if(!this.modifiers){var border=this.getBorder(update);var margin=this.getMargin(update);var padding=this.getPadding(update);this.modifiers={left:border.left+margin.left+padding.left,right:border.right+margin.right+padding.right,top:border.top+margin.top+padding.top,bottom:border.bottom+margin.bottom+padding.bottom,x:border.x+margin.x+padding.x,y:border.y+margin.y+padding.y}}},getMargin:function(update){if(!this.margin||update){var parts=this.getStyle('margin').split(' ')
this.margin={left:parts[1].toInt(),right:parts[3].toInt(),top:parts[0].toInt(),bottom:parts[2].toInt(),x:parts[0].toInt()+parts[2].toInt(),y:parts[1].toInt()+parts[3].toInt()};}
return this.margin},getPadding:function(update){if(!this.padding||update){var parts=this.getStyle('padding').split(' ')
this.padding={left:parts[1].toInt(),right:parts[3].toInt(),top:parts[0].toInt(),bottom:parts[2].toInt(),x:parts[0].toInt()+parts[2].toInt(),y:parts[1].toInt()+parts[3].toInt()};}
return this.padding},getBorder:function(update){if(!this.border||update){var parts=this.getStyle('border-width').split(' ')
this.border={left:parts[1].toInt(),right:parts[3].toInt(),top:parts[0].toInt(),bottom:parts[2].toInt(),x:parts[0].toInt()+parts[2].toInt(),y:parts[1].toInt()+parts[3].toInt()};}
return this.border}})
Number.implement({toBytes:function(){var bytes=this
if(bytes<1024){return bytes.toFixed(1)+'B';}
else{bytes=bytes/1024;}
if(bytes<1024){return bytes.toFixed(1)+'KiB';}
else{bytes=bytes/1024;}
if(bytes<1024){return bytes.toFixed(1)+'MiB';}
else{bytes=bytes/1024;}
return bytes.toFixed(1)+'GiB'},toSpeed:function(){var bits=this
if(bits<1024){return bits.toFixed(1)+'b/s';}
else{bits=bits/1024;}
if(bits<1024){return bits.toFixed(1)+'KiB/s';}
else{bits=bits/1024;}
return bits.toFixed(2)+'MiB/s'},toTime:function(){var time=this
if(time==0){return'∞'}
if(time<60){return time+'s';}
else{time=time/60;}
if(time<60){var minutes=Math.floor(time)
var seconds=Math.round(60*(time-minutes))
if(seconds>0){return minutes+'m '+seconds+'s';}else{return minutes+'m';}}
else{time=time/60;}
if(time<24){var hours=Math.floor(time)
var minutes=Math.round(60*(time-hours))
if(minutes>0){return hours+'h '+minutes+'m';}else{return hours+'h';}}
else{time=time/24;}
var days=Math.floor(time)
var hours=Math.round(24*(time-days))
if(hours>0){return days+'d '+hours+'h';}else{return days+'d';}}})
String.implement({strip:function(){var stripped=this.replace(/^\s*/,'')
stripped.replace(/\s*$/,'')
return stripped}})
Sorters={Simple:new Class({initialize:function(column,order){this.column=column
this.order=order},sorter:function(){return function(a,b){var av,bv
av=a.cells[this.column].value
bv=b.cells[this.column].value
return this.sort(av,bv)}.bind(this)},sort:function(a,b){if(a>b)
return 1*this.order
if(a<b)
return-1*this.order
return 0}})}
Sorters.Number=new Class({Extends:Sorters.Simple,sort:function(a,b){return(a-b)*this.order;}})
Sorters.Progress=new Class({Extends:Sorters.Simple,sort:function(a,b){return(a.percent-b.percent)*this.order;}})
Widgets={version:0.1,authors:['Damien Churchill'],license:'GPLv3'};elementMethods=['addClass','hasClass','removeClass','toggleClass','getInnerSize','getTop','getLeft','getWidth','getHeight','getScrollTop','getScrollLeft','getScrollHeight','getScrollWidth','getSize','getScrollSize','getScroll','getScrolls','getOffsetParent','getOffsets','getPosition','getCoordinates','getInnerWidth','getInnerHeight','getStyle','getParent','getSizeModifiers','setStyle'];Widgets.Base=new Class({Implements:[Events,Options],options:{expand:false},initialize:function(element,options){this.setOptions(options);this.element=$(element);this.element.store('moouiWidget',this);this.isMoouiWidget=true;this.width=this.element.getStyle('width');this.height=this.element.getStyle('height');this.width=(this.width)?this.width.toInt():-1;this.height=(this.height)?this.height.toInt():-1;elementMethods.each(function(method){if(this.element[method]){this[method]=this.element[method].bind(this.element);};},this);},refresh:function(){this.element.removeProperty('style');this.width=this.element.getStyle('width');this.height=this.element.getStyle('height');this.width=(this.width)?this.width.toInt():-1;this.height=(this.height)?this.height.toInt():-1;this.getSizeModifiers(true);if(this.refreshChildren)this.refreshChildren();},expand:function(){var parent=this.getParent();var parentSize=this.getParent().getInnerSize();this.element.getSizeModifiers();parentSize.y-=this.element.modifiers.y;parentSize.x-=this.element.modifiers.x;this.sets({'width':parentSize.x,'height':parentSize.y});},set:function(property,value,noFire){if(property=='height'||property=='width'){var eventArgs={};eventArgs[property]=value;eventArgs[('old-'+property).camelCase()]=this[property];this[property]=value;if(value>0)this.element.setStyle(property,value);if(!noFire)this.fireEvent('resize',eventArgs);}else{this[property]=value;this.element.setStyle(property,value);}},sets:function(properties){properties=new Hash(properties);var fireResize=false;var eventArgs={};properties.each(function(value,key){if(key=='height'||key=='width'){eventArgs[('old-'+key).camelCase()]=this[key];eventArgs[key]=value;fireResize=true;}
this.set(key,value,true);},this);if(fireResize)this.fireEvent('resize',eventArgs);},toElement:function(){return this.element;}});$W=function(wrap){if(!wrap.isMoouiWidget){if(wrap.retrieve){wrap=wrap.retrieve('moouiWidget');return(wrap)?wrap:new Widgets.Base(wrap);}else{return new Widgets.Base(wrap);};}else{return wrap;};};$$W=function(test){if(!test.isMoouiWidget){if(test.retrieve){test=test.retrieve('moouiWidget');return(test)?test:null;}else{return null;};}else{return wrap;};};Widgets.PopupMenu=new Class({Extends:Widgets.WidgetBase,Implements:Events,initialize:function(){this.items=[]
this.noClose=false
this.build()},add:function(item){if($type(item)=='array'){for(var i=0;i<item.length;i++){item[i].parent=this}
this.items.extend(item)}else if($type(item)=='object'){item.parent=this
this.items.include(item)}
this.build()},_build:function(items){var menu=new Element('ul')
menu.addClass('moouiMenu')
items.each(function(item){if(item.type=='text'){var el=new Element('li')
el.addClass('moouiMenuText')
new Element('span').set('text',item.text).inject(el)
if($defined(item.icon)){el.setStyle('background-image','url('+item.icon+')')
el.addClass('moouiMenuIcon')}
el.inject(menu)
el.addEvent('click',function(e){this.fireEvent('action',item)
this.hide()}.bind(this))}else if(item.type=='toggle'){var el=new Element('li');el.addClass('moouiMenuToggle');var toggle=new Element('span').inject(el);item.checkbox=new Element('input',{type:'checkbox'}).inject(toggle);new Element('span').set('text',item.text).inject(toggle)
if(item.value)item.checkbox.checked=item.value;if($defined(item.icon)){el.setStyle('background-image','url('+item.icon+')');el.addClass('moouiMenuIcon');}
el.inject(menu);var clicked=function(e){if(item.value==true)item.value=false
else item.value=true
this.fireEvent('action',item);this.hide();}.bindWithEvent(this)
item.set=function(value){item.value=value;item.checkbox.checked=value;}
el.addEvent('click',clicked)}else if(item.type=='seperator'){new Element('li').addClass('moouiMenuSep').inject(menu)}else if(item.type=='submenu'){var el=new Element('li')
el.addClass('mooui-menu-sub')
new Element('span').set('text',item.text).inject(el)
if($defined(item.icon)){el.setStyle('background-image','url('+item.icon+')')
el.addClass('moouiMenuIcon')}
var sub=this._build(item.items).inject(el)
el.addEvent('mouseenter',function(e){this.fixSize(sub)}.bind(this))
el.inject(menu)}},this)
menu.addEvent('mouseenter',function(e){this.fixLeft(menu)}.bind(this))
return menu},build:function(){var self=this
if($defined(this.element)){this.element.destroy();}
this.element=this._build(this.items)},hide:function(force){if(!this.no_close){this.element.dispose()
this.fireEvent('closed')}else if(force){this.element.dispose()
this.fireEvent('closed')}},show:function(e){this.showPos(e.client.x+10,e.client.y-10)},fixSize:function(el){var widest=0
el.getElements('li').each(function(item){var text=item.getElement('span')
var width=text.getSize().x
if(width>widest){widest=width}})
el.setStyle('width',widest+32)},fixLeft:function(el){var widest=0
el.getElements('li').each(function(item){var width=item.getSize().x
if(width>widest){widest=width}});el.setStyle('width',widest+2)
el.getElements('li ul').each(function(item){item.setStyle('left',widest-20)});},showPos:function(x,y){this.element.setStyles({'left':x,'top':y-2});this.element.inject(document.body)
this.element.addEvent('mouseleave',function(e){this.hide()}.bind(this));}})
Widgets.ProgressBar=new Class({Extends:Widgets.Base,initialize:function(){this.parent(new Element('div'));this.bound={onResize:this.onResize.bindWithEvent(this)};this.element.addClass('moouiProgressBar');this.bar=new Element('div').inject(this.element);this.textSpan=new Element('span').inject(this.bar);this.sets({width:200,height:20});this.addEvent('resize',this.bound.onResize);},onResize:function(){this.textSpan.setStyles({'width':this.width,'height':this.height});this.update(this.text,this.percent);},update:function(text,percent){if(this.text!=text){this.text=text;this.textSpan.set('text',text);};if(this.percent!=percent){this.percent=percent;this.bar.setStyles({'width':Math.floor(this.width/100.0*percent),'height':this.height});};}});Widgets.Spinner=new Class({Extends:Widgets.Base,options:{precision:0,step:1,limit:{high:null,low:null}},initialize:function(input,options){this.parent(new Element('div'),options);this.bound={onMouseDown:this.onMouseDown.bindWithEvent(this),onMouseUp:this.onMouseUp.bindWithEvent(this),onMouseWheel:this.onMouseWheel.bindWithEvent(this),onKeyDown:this.onKeyDown.bindWithEvent(this),onKeyUp:this.onKeyUp.bindWithEvent(this),onChange:this.onChange.bindWithEvent(this)};value=0;this.keyDown=false;if(input){this.element.replaces(input);value=new Number(input.value);};this.input=(input)?input:new Element('input');this.input.store('moouiWidget',this);this.element.grab(this.input);this.element.addClass('moouiSpinner');this.element.addEvent('mousewheel',this.bound.onMouseWheel);this.input.addEvent('keydown',this.bound.onKeyDown);this.input.addEvent('change',this.bound.onChange);this.buttons=new Element('div').addClass('moouiSpinnerButtons');this.up=new Element('div').addClass('moouiSpinnerUp');this.down=new Element('div').addClass('moouiSpinnerDown');this.up.addEvent('mousedown',this.bound.onMouseDown);this.down.addEvent('mousedown',this.bound.onMouseDown);this.buttons.grab(this.up);this.buttons.grab(this.down);this.element.grab(this.buttons);this.setValue(value);},getPrecision:function(){return Math.pow(10,this.options.precision+1)/10;},setValue:function(value){if(this.options.limit){if(this.options.limit.low&&value<=this.options.limit.low){value=this.options.limit.low;this.down.setStyle('opacity','0.5');}else if(this.options.limit.high&&value>=this.options.limit.high){value=this.options.limit.high;this.up.setStyle('opacity','0.5');}else{this.up.setStyle('opacity','1');this.down.setStyle('opacity','1');};};this.value=new Number(value);this.input.set('value',this.value.toFixed(this.options.precision));this.settingValue=true;this.input.fireEvent('change');},changeValue:function(change){value=this.value+(change/this.getPrecision());this.setValue(value);},acceleratingChange:function(change){if(this.stop)return;this.changeValue(change);if(this.interval>100)this.interval-=100
else if(this.interval>10)this.interval-=10
this.acceleratingChange.delay(this.interval,this,change);},onMouseDown:function(e){this.value=new Number(this.input.value);document.addEvent('mouseup',this.bound.onMouseUp);if(e.target.hasClass('moouiSpinnerUp'))change=this.options.step;else change=this.options.step*-1;this.interval=600;this.stop=false;this.acceleratingChange(change);},onMouseUp:function(e){this.stop=true;document.removeEvent('mouseup',this.bound.onMouseUp);},onKeyDown:function(e){if(e.key=='up'||e.key=='down'){if(this.keyDown)return;this.value=new Number(this.input.value);change=(e.key=='up')?this.options.step:this.options.step*-1;this.input.addEvent('keyup',this.bound.onKeyUp);this.interval=600;this.stop=false;this.keyDown=true;this.acceleratingChange(change);}else if($A(['left','right','backspace']).contains(e.key)){return;}else{e.key=(e.code==190)?'.':e.key;pattern=/[0-9]/;if(!this.input.value.match(/\./)&&this.options.precision>0){pattern=/[0-9\.]/;};if(!e.key.match(pattern)){e.stop();return;};};},onKeyUp:function(e){this.stop=true;this.keyDown=false;this.input.removeEvent('keyup',this.bound.onKeyUp);},onMouseWheel:function(e){this.changeValue(this.options.step*e.wheel);},onChange:function(e){if(this.settingValue){this.settingValue=false;return;};this.setValue(new Number(this.input.value));}});Widgets.SplitPane=new Class({Extends:Widgets.Base,options:{direction:'horizontal',name:null,splitSize:6,pane1:{},pane2:{}},initialize:function(element,pane1,pane2,options){this.parent(element,options);this.bound={onResize:this.onResize.bindWithEvent(this),onMouseDown:this.onMouseDown.bindWithEvent(this),onMouseMove:this.onMouseMove.bindWithEvent(this),onMouseUp:this.onMouseUp.bindWithEvent(this)};this.horizontal=(this.options.direction=='horizontal')?true:false;this.pane1=$W(pane1);this.pane2=$W(pane2);if(this.options.expand)this.expand();this.initPane(this.pane1,this.options.pane1);this.initPane(this.pane2,this.options.pane2);this.initSplitter();this.calculatePositions();this.setPosition(this.pane1);this.setPosition(this.splitter);this.setPosition(this.pane2);this.splitter.addEvent('mousedown',this.bound.onMouseDown);this.addEvent('resize',this.onResize.bindWithEvent(this));},initSplitter:function(){this.splitter=new Element('div').addClass('moouiSplitter');this.splitter.inject(this.pane1,'after');this.splitter.paneinfo={};if(this.horizontal){this.splitter.addClass('moouiSplitterVertical');}else{this.splitter.addClass('moouiSplitterHorizontal');};this.splitter.grab(new Element('div'));this.splitter.grab(new Element('div'));this.splitter.grab(new Element('div'));},onMouseDown:function(e){window.addEvent('mouseup',this.bound.onMouseUp);window.addEvent('mousemove',this.bound.onMouseMove);this.mouseStart={x:e.client.x,y:e.client.y};this.paneInfo={one:{startWidth:this.pane1.paneinfo.width,startHeight:this.pane1.paneinfo.height},two:{startWidth:this.pane2.paneinfo.width,startHeight:this.pane2.paneinfo.height}};},onMouseMove:function(e){if(this.horizontal){diff=e.client.x-this.mouseStart.x;p1width=this.paneInfo.one.startWidth+diff;p2width=this.paneInfo.two.startWidth-diff;if((this.pane1.paneinfo.min-this.pane1.element.modifiers.y)>p1width){this.pane1.paneinfo.width=this.pane1.paneinfo.min;this.pane2.paneinfo.width=this.paneInfo.two.startWidth+(this.paneInfo.one.startWidth-this.pane1.paneinfo.min);}else if((this.pane2.paneinfo.min-this.pane2.element.modifiers.y)>p2width){this.pane2.paneinfo.width=this.pane2.paneinfo.min;this.pane1.paneinfo.width=this.paneInfo.one.startWidth+(this.paneInfo.two.startWidth-this.pane2.paneinfo.min);}else{this.pane1.paneinfo.width=p1width;this.pane2.paneinfo.width=p2width;};}else{diff=e.client.y-this.mouseStart.y;p1height=this.paneInfo.one.startHeight+diff;p2height=this.paneInfo.two.startHeight-diff;if(this.pane1.paneinfo.min>p1height){this.pane1.paneinfo.height=this.pane1.paneinfo.min;this.pane2.paneinfo.height=this.paneInfo.two.startHeight+(this.paneInfo.one.startHeight-this.pane1.paneinfo.min);}else if(this.pane2.paneinfo.min>p2height){this.pane2.paneinfo.height=this.pane2.paneinfo.min;this.pane1.paneinfo.height=this.paneInfo.one.startHeight+(this.paneInfo.two.startHeight-this.pane2.paneinfo.min);}else{this.pane1.paneinfo.height=p1height;this.pane2.paneinfo.height=p2height;};};this.setPosition(this.pane1);this.setPosition(this.pane2);},onMouseUp:function(e){window.removeEvent('mouseup',this.bound.onMouseUp);window.removeEvent('mousemove',this.bound.onMouseMove);},initPane:function(pane,options){pane.addClass('moouiPane');pane.paneinfo={}
if(options){pane.paneinfo.min=(options.min)?options.min:0;pane.paneinfo.expand=(options.expand)?options.expand:false;};},calculatePositions:function(resized){if(resized){if(this.horizontal){this.calculateResize(resized,'width','height','x','y');}else{this.calculateResize(resized,'height','width','y','x');}}else{if(this.horizontal){this.calculateInitial('width','height','x','y');}else{this.calculateInitial('height','width','y','x');}}},calculateInitial:function(dm,ds,pm,ps){var size=this.getInnerSize();this.pane1.getSizeModifiers();this.pane2.getSizeModifiers();this.splitter.getSizeModifiers();if(this.pane1.paneinfo.expand){this.pane2.paneinfo[dm]=this.pane2.paneinfo.min;this.pane1.paneinfo[dm]=size[pm]-this.pane2.paneinfo.min-this.options.splitSize;this.pane1.paneinfo[dm]-=this.pane1.element.modifiers[pm]+this.pane2.element.modifiers[pm];}else{this.pane1.paneinfo[dm]=this.pane1.paneinfo.min;this.pane2.paneinfo[dm]=size[pm]-this.pane1.paneinfo.min-this.options.splitSize;this.pane2.paneinfo[dm]-=this.pane2.element.modifiers[pm]+this.pane1.element.modifiers[pm];}
this.pane1.paneinfo[ds]=this.pane2.paneinfo[ds]=size[ps];this.pane1.paneinfo[ds]-=this.pane1.element.modifiers[ps];this.pane2.paneinfo[ds]-=this.pane2.element.modifiers[ps];this.splitter.paneinfo[ds]=size[ps];this.splitter.paneinfo[dm]=this.options.splitSize;},calculateResize:function(resized,dm,ds,pm,ps){size=this.getInnerSize();this.pane1.getSizeModifiers();this.pane2.getSizeModifiers();this.splitter.getSizeModifiers();if(resized[dm]&&resized[dm]!=resized[('old-'+dm).camelCase()]){if(this.pane1.paneinfo.expand){this.pane1.paneinfo[dm]=size[pm]-this.pane2.paneinfo[dm]-this.options.splitSize;this.pane1.paneinfo[dm]-=this.pane1.element.modifiers[pm]+this.pane2.element.modifiers[pm];}else{this.pane2.paneinfo[dm]=size[pm]-this.pane1.paneinfo[dm]-this.options.splitSize;this.pane2.paneinfo[dm]-=this.pane2.element.modifiers[pm]+this.pane1.element.modifiers[pm];}};if(resized[ds]&&resized[ds]!=resized[('old-'+ds).camelCase()]){this.pane1.paneinfo[ds]=this.pane2.paneinfo[ds]=size[ps];this.splitter.paneinfo[ds]=size[ps];this.splitter.paneinfo[ds]-=this.splitter.modifiers[ps];this.pane1.paneinfo[ds]-=this.pane1.element.modifiers[ps];this.pane2.paneinfo[ds]-=this.pane2.element.modifiers[ps];};},setPosition:function(object){if(object.hasClass('moouiSplitter')){sets=object.setStyles.bind(object);}else{sets=object.sets.bind(object);};sets({width:object.paneinfo.width,height:object.paneinfo.height});},onResize:function(event){this.calculatePositions(event)
this.setPosition(this.pane1);this.setPosition(this.splitter);this.setPosition(this.pane2);}})
Widgets.Tabs=new Class({Extends:Widgets.Base,initialize:function(element){this.parent(element);this.bound={onResize:this.onResize.bindWithEvent(this)};this.pages=[];this.currentPage=-1;this.tabsList=new Element('ul').inject(this.element);this.element.addClass('moouiTabs');this.pagesDiv=new Element('div').inject(this.element);this.pagesDiv.addClass('moouiTabPages');if(this.options.expand)this.expand();},addPage:function(page){this.pages.include(page)
var tab=new Element('li')
tab.set('text',page.name)
tab.addEvent('click',function(e){this.select(pageIndex)}.bindWithEvent(this))
page.tab=tab
this.tabsList.grab(tab)
this.pagesDiv.grab(page.element.addClass('moouiTabPage'))
var pageIndex=this.pages.indexOf(page)
if(this.currentPage<0){this.currentPage=pageIndex
this.select(pageIndex)}},select:function(id){this.pages[this.currentPage].removeClass('moouiTabPageActive')
this.pages[this.currentPage].tab.removeClass('moouiTabActive')
this.pages[id].addClass('moouiTabPageActive')
this.pages[id].tab.addClass('moouiTabActive')
this.currentPage=id
this.fireEvent('pageChanged')},onResize:function(){this._pages.each(function(page){page.resize(this.width,this.height-45)},this)}});Widgets.TabPage=new Class({Extends:Widgets.Base,options:{element:null,url:null},initialize:function(name,options){this.name=name
var element=null
if(options&&options.element)element=options.element
else element=new Element('div')
this.parent(element,options)
if(this.options.url){new Request.HTML({url:this.options.url,update:element,onSuccess:function(e){this.fireEvent('loaded')}.bindWithEvent(this)}).get()}}});Widgets.VBox=new Class({Extends:Widgets.Base,initialize:function(element,options){this.parent(element,options);this.boxes=[];if(this.options.expand)this.expand();},addBox:function(box,options){box=$W(box);box.boxInfo=(options)?options:{fixed:false};this.boxes.include(box);this.element.grab(box);},calculatePositions:function(){if(this.options.expand)this.expand();var size=this.getInnerSize();var height=size.y,resizable=0;this.boxes.each(function(box){box.getSizeModifiers();if(!box.boxInfo.fixed)resizable++;else height-=box.height+box.element.modifiers.y;},this);var boxHeight=height/resizable,remainder=height%resizable
this.boxes.each(function(box){var boxInfo={};if(!box.boxInfo.fixed){var setHeight=boxHeight-box.element.modifiers.y;if(remainder>0){setHeight-=1;remainder--};boxInfo.height=setHeight;}else{boxInfo.height=box.height;}
boxInfo.width=size.x-box.element.modifiers.x;box.sets({height:boxInfo.height,width:boxInfo.width});},this);},refreshChildren:function(){this.boxes.each(function(box){box.refresh();box.setStyle('position','relative');});}})
Widgets.Window=new Class({Extends:Widgets.Base,initialize:function(options){var element=new Element('div');this.parent(element,options);this.addClass('moouiWindow');this.sets({width:this.options.width,height:this.options.height});this.element.setStyle('opacity',0);this.title=new Element('h3').addClass('moouiWindowTitle');this.element.grab(this.title);this.title.set('text',this.options.title);this.drag=new Drag(this.element,{handle:this.title});this.close=new Element('div').addClass('moouiWindowClose');this.close.inject(this.element);this.close.addEvent('click',function(e){this.hide();}.bindWithEvent(this));this.content=new Element('div').addClass('moouiWindowContent');this.content.inject(this.element);if(this.options.url){new Request.HTML({url:this.options.url,update:this.content,onSuccess:function(e){this.fireEvent('loaded');}.bindWithEvent(this)}).get();}},show:function(){this.fireEvent('beforeShow');var size=document.body.getInnerSize();var left=(size.x-this.options.width)/2,top=(size.y-this.options.height)/2;this.sets({left:left,top:top});document.body.grab(this.element);this.element.setStyle('opacity',1);this.fireEvent('show');},hide:function(){var tween=this.element.get('tween');tween.addEvent('complete',function(e){this.element.dispose();}.bind(this));this.element.fade(0);}})
Widgets.DataGridCell=new Class({Implements:[Events,Options],options:{name:'',type:'text',width:0},initialize:function(options){this.setOptions(options)
this.element=new Element('td')},set:function(value){this.value=value
var text=value,set_text=true
switch(this.options.type){case'bytes':text=value.toBytes()
break;case'time':text=value.toTime()
break;case'date':this.value=new Date(value)
text=this.value.format('ddd mmm dd yyyy')
break;case'speed':text=value.toSpeed()
break;case'icon':text=value.text
this.element.setStyles({'background-repeat':'no-repeat','background-position':'2px','background-image':'url('+value.icon+')','padding-left':20})
break;case'image':if(!this.image){this.image=new Element('img')
this.image.inject(this.element)}
this.image.src=value
set_text=false
break;case'progress':if(!this.progress){this.progress=new Widgets.ProgressBar()
this.progress.sets({'width':this.options.width,'height':14})
this.progress.element.inject(this.element)}
this.progress.update(value.text,value.percent)
set_text=false
break;}
if(set_text){this.element.set('text',text)}
this.fireEvent('changed',{cell:this})}})
Widgets.DataGridColumn=new Class({Implements:[Events,Options],options:{name:'',type:'string',text:'',width:50},initialize:function(options){this.setOptions(options)
this.order=1},setText:function(text){this.options.text=text
this.fireEvent('textChanged',text)},get_sorter:function(index){switch(this.options.type){case'number':return new Sorters.Number(index,this.order)
case'progress':return new Sorters.Progress(index,this.order)
default:return new Sorters.Simple(index,this.order)}}})
Widgets.DataGridRow=new Class({Implements:[Events],initialize:function(id,columns){this.id=id
this.columns=columns
this.element=new Element('tr')
this.element.store('rowid',this.id)
this.cells=[]
this.selected=false
this.columns.each(function(col){var cell=new Widgets.DataGridCell({name:col.options.name,type:col.options.type,width:col.options.width})
cell.element.inject(this.element)
cell.addEvent('changed',this.oncellchanged.bind(this))
this.cells.include(cell)},this)
this.element.addEvent('contextmenu',this.oncontextmenu.bind(this))
this.element.addEvent('click',this.onclick.bind(this))},update:function(row){row=new Hash(row)
row.getKeys().each(function(item){if(item!='data'||item!='id'){this[item]=row[item]}},this)
this.cells.each(function(cell){cell.set(row.data[cell.options.name])},this)
return this},oncellchanged:function(e){e.row=this
this.fireEvent('changed',e)},oncontextmenu:function(e){e.row=this
this.fireEvent('menu',e)},onclick:function(e){e.row=this
this.fireEvent('click',e)}})
Widgets.DataGrid=new Class({Implements:[Options,Events],Extends:Widgets.Base,options:{columns:[],element:null},initialize:function(element,options){if(!element)element=this.createElement
this.parent(element,options)
this.bound={onResize:this.onResize.bindWithEvent(this),onRowMenu:this.onRowMenu.bindWithEvent(this),onRowClick:this.onRowClick.bindWithEvent(this)}
this.columns=[]
this.options.columns.each(function(column_info){var column=new Widgets.DataGridColumn(column_info)
column.addEvent('textChanged',function(e){var index=this.columns.indexOf(column)
this.header.getElements('th')[index].set('text',e)}.bindWithEvent(this))
this.columns.include(column)},this)
this.rows=[]
this.displayRows=[]
this.selectedIndex=-1
this.filterer=false
this.sorted_by=0
this.columns[0].order=-1
if($chk(this.element)){this.scanElement()}else{this.createElement}
this.element.setStyle('MozUserSelect','none');this.resizeColumns();this.addEvent('resize',this.bound.onResize);},createElement:function(){this.element=new Element('div')
this.table=new Element('table').inject(this.element)
this.header=new Element('thead').inject(this.table).grab(new Element('tr'))
this.body=new Element('tbody').inject(this.table)
this.options.columns.each(function(column){new Element('th',{'class':column.name,'text':column.text})},this);},scanElement:function(){this.element.addClass('moouiDataGrid')
this.table=this.element.getElement('table')
if(!this.table)this.table=new Element('table').inject(this.element)
this.header=this.table.getElement('thead')
if(!this.header)this.header=new Element('thead').inject(this.table)
this.body=this.table.getElement('tbody')
if(!this.body)this.body=new Element('tbody').inject(this.table)
this.header.empty();var headerRow=new Element('tr');this.header.grab(headerRow)
this.columns.each(function(column,index){new Element('th').addEvent('click',function(e){this.sort(column,index)
this.render()}.bindWithEvent(this)).set('text',column.options.text).inject(headerRow)},this)},addRow:function(row_info,noRender){var row=new Widgets.DataGridRow(row_info.id,this.columns)
row.store=row_info.store
this.rows.include(row)
row.update(row_info)
row.addEvent('menu',this.bound.onRowMenu);row.addEvent('click',this.bound.onRowClick);if(!noRender)this.render();},onRowMenu:function(e){if(!this.selectedRow){this.selectRow(e.row);};this.fireEvent('rowMenu',e);},onRowClick:function(e){e.row.index=this.displayRows.indexOf(this.getById(e.row.id));if(e.shift){this.deselectRows();this.selectRows(e.row.index);}else if(e.control){if(e.row.selected){this.deselectRow(e.row)}
else{this.selectRow(e.row)};}else{this.deselectRows();this.selectRow(e.row);}
this.fireEvent('rowClick',e);},deselectRow:function(row){if(!$chk(row)){return}
row.selected=false
row.element.removeClass('selected')
if(row==this.selectedRow){this.selectedRow=null
this.fireEvent('selectedChanged')}},deselectRows:function(){this.selected=-1
this.rows.each(function(row){row.selected=false
row.element.removeClass('selected')})},filter:function(){this.filterer=(this.filterer)?this.filterer:$lambda(true);this.displayRows.empty();this.rows.each(function(row){if(this.filterer(row)){this.displayRows.include(row)}}.bind(this));},getById:function(id){var row=null
this.rows.each(function(r){if(r.id==id){row=r}})
return row},getSelected:function(){selected=[]
this.rows.each(function(row){if(row.selected){selected.include(row)}})
return selected},has:function(id){if(this.getById(id)){return true;}else{return false;}},remove:function(id){this.getById(id)},render:function(){this.filter();this.resort();var rows=[],rowIds=[]
this.rows.each(function(row){if(this.displayRows.contains(row)){rows.include(row.element)
rowIds.include(row.id)}},this)
this.body.adopt(rows)
this.body.getChildren().each(function(row){var id=row.retrieve('rowid')
if(!id){row.destroy()}else if(!rowIds.contains(id)){row.dispose()}},this)
var selected=this.body.getElements('tr.selected')
if(selected){this.selected=$A(this.body.rows).indexOf(selected)}},resizeColumns:function(){var totalWidth=this.options.columns.sum('width')
this.table.setStyle('width',totalWidth)
var cols=this.header.getElements('th')
cols.each(function(col,index){if(this.options.columns[index]){col.setStyle('width',this.options.columns[index].width)}},this)},onResize:function(){var width=this.width
var columnWidth=this.options.columns.sum('width')
if(columnWidth>width)this.table.setStyle('width',columnWidth)
else this.table.setStyle('width',width)
var cols=this.header.getElements('th')
cols.each(function(col,index){var colWidth=this.columns[index].options.width;if(index==cols.length-1&&width>colWidth)
col.setStyle('width',width)
else{col.setStyle('width',colWidth)
width-=colWidth}},this)},selectRows:function(index){var selectedIndex=this.displayRows.indexOf(this.selectedRow)
if(selectedIndex>index){for(var i=index;i<=selectedIndex;i++){this.displayRows[i].selected=true
this.displayRows[i].element.addClass('selected')}}else if(selectedIndex<index){for(var i=selectedIndex;i<=index;i++){this.displayRows[i].selected=true
this.displayRows[i].element.addClass('selected')}}},selectRow:function(row){row.selected=true
row.element.addClass('selected')
this.selectedRow=row
this.fireEvent('selectedChanged');},sort:function(column,index){var sorter=column.get_sorter(index)
this.rows.sort(sorter.sorter())
column.order*=-1
this.sorted_by=index},resort:function(){var column=this.columns[this.sorted_by]
column.order*=-1
this.sort(column,this.sorted_by)},updateRow:function(row,noRender){this.getById(row.id).update(row)
if(!noRender)this.render()}})