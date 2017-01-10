/*
 * Ext.ux.layout.FormLayoutFix.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */
Ext.override(Ext.layout.FormLayout,{renderItem:function(e,a,d){if(e&&!e.rendered&&(e.isFormField||e.fieldLabel)&&e.inputType!="hidden"){var b=this.getTemplateArgs(e);if(typeof a=="number"){a=d.dom.childNodes[a]||null}if(a){e.formItem=this.fieldTpl.insertBefore(a,b,true)}else{e.formItem=this.fieldTpl.append(d,b,true)}e.actionMode="formItem";e.render("x-form-el-"+e.id);e.container=e.formItem;e.actionMode="container"}else{Ext.layout.FormLayout.superclass.renderItem.apply(this,arguments)}}});
/*
 * Ext.ux.tree.MultiSelectionModelFix.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */
Ext.override(Ext.tree.MultiSelectionModel,{onNodeClick:function(c,d){if(d.ctrlKey&&this.isSelected(c)){this.unselect(c)}else{if(d.shiftKey&&!this.isSelected(c)){var b=c.parentNode;if(this.lastSelNode.parentNode.id!=b.id){return}var f=b.indexOf(c),a=b.indexOf(this.lastSelNode);this.select(this.lastSelNode,d,false,true);if(f>a){f=f+a,a=f-a,f=f-a}b.eachChild(function(g){var e=b.indexOf(g);if(f<e&&e<a){this.select(g,d,true,true)}},this);this.select(c,d,true)}else{this.select(c,d,d.ctrlKey)}}},select:function(b,d,c,a){if(c!==true){this.clearSelections(true)}if(this.isSelected(b)){this.lastSelNode=b;return b}this.selNodes.push(b);this.selMap[b.id]=b;this.lastSelNode=b;b.ui.onSelectedChange(true);if(a!==true){this.fireEvent("selectionchange",this,this.selNodes)}return b}})
/*
 * Ext JS Library 3.4.0
 * Copyright(c) 2006-2011 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */
;Ext.ns("Ext.ux.tree");Ext.ux.tree.TreeGrid=Ext.extend(Ext.tree.TreePanel,{rootVisible:false,useArrows:true,lines:false,borderWidth:Ext.isBorderBox?0:2,cls:"x-treegrid",columnResize:true,enableSort:true,reserveScrollOffset:true,enableHdMenu:true,columnsText:"Columns",initComponent:function(){if(!this.root){this.root=new Ext.tree.AsyncTreeNode({text:"Root"})}var a=this.loader;if(!a){a=new Ext.ux.tree.TreeGridLoader({dataUrl:this.dataUrl,requestMethod:this.requestMethod,store:this.store})}else{if(Ext.isObject(a)&&!a.load){a=new Ext.ux.tree.TreeGridLoader(a)}}this.loader=a;Ext.ux.tree.TreeGrid.superclass.initComponent.call(this);this.initColumns();if(this.enableSort){this.treeGridSorter=new Ext.ux.tree.TreeGridSorter(this,this.enableSort)}if(this.columnResize){this.colResizer=new Ext.tree.ColumnResizer(this.columnResize);this.colResizer.init(this)}var b=this.columns;if(!this.internalTpl){this.internalTpl=new Ext.XTemplate('<div class="x-grid3-header">','<div class="x-treegrid-header-inner">','<div class="x-grid3-header-offset">','<table style="table-layout: fixed;" cellspacing="0" cellpadding="0" border="0"><colgroup><tpl for="columns"><col /></tpl></colgroup>','<thead><tr class="x-grid3-hd-row">','<tpl for="columns">','<td class="x-grid3-hd x-grid3-cell x-treegrid-hd" style="text-align: {align};" id="',this.id,'-xlhd-{#}">','<div class="x-grid3-hd-inner x-treegrid-hd-inner" unselectable="on">',this.enableHdMenu?'<a class="x-grid3-hd-btn" href="#"></a>':"",'{header}<img class="x-grid3-sort-icon" src="',Ext.BLANK_IMAGE_URL,'" />',"</div>","</td></tpl>","</tr></thead>","</table>","</div></div>","</div>",'<div class="x-treegrid-root-node">','<table class="x-treegrid-root-table" cellpadding="0" cellspacing="0" style="table-layout: fixed;"></table>',"</div>")}if(!this.colgroupTpl){this.colgroupTpl=new Ext.XTemplate('<colgroup><tpl for="columns"><col style="width: {width}px"/></tpl></colgroup>')}},initColumns:function(){var e=this.columns,a=e.length,d=[],b,f;for(b=0;b<a;b++){f=e[b];if(!f.isColumn){f.xtype=f.xtype?(/^tg/.test(f.xtype)?f.xtype:"tg"+f.xtype):"tgcolumn";f=Ext.create(f)}f.init(this);d.push(f);if(this.enableSort!==false&&f.sortable!==false){f.sortable=true;this.enableSort=true}}this.columns=d},onRender:function(){Ext.tree.TreePanel.superclass.onRender.apply(this,arguments);this.el.addClass("x-treegrid");this.outerCt=this.body.createChild({cls:"x-tree-root-ct x-treegrid-ct "+(this.useArrows?"x-tree-arrows":this.lines?"x-tree-lines":"x-tree-no-lines")});this.internalTpl.overwrite(this.outerCt,{columns:this.columns});this.mainHd=Ext.get(this.outerCt.dom.firstChild);this.innerHd=Ext.get(this.mainHd.dom.firstChild);this.innerBody=Ext.get(this.outerCt.dom.lastChild);this.innerCt=Ext.get(this.innerBody.dom.firstChild);this.colgroupTpl.insertFirst(this.innerCt,{columns:this.columns});if(this.hideHeaders){this.el.child(".x-grid3-header").setDisplayed("none")}else{if(this.enableHdMenu!==false){this.hmenu=new Ext.menu.Menu({id:this.id+"-hctx"});if(this.enableColumnHide!==false){this.colMenu=new Ext.menu.Menu({id:this.id+"-hcols-menu"});this.colMenu.on({scope:this,beforeshow:this.beforeColMenuShow,itemclick:this.handleHdMenuClick});this.hmenu.add({itemId:"columns",hideOnClick:false,text:this.columnsText,menu:this.colMenu,iconCls:"x-cols-icon"})}this.hmenu.on("itemclick",this.handleHdMenuClick,this)}}},setRootNode:function(a){a.attributes.uiProvider=Ext.ux.tree.TreeGridRootNodeUI;a=Ext.ux.tree.TreeGrid.superclass.setRootNode.call(this,a);if(this.innerCt){this.colgroupTpl.insertFirst(this.innerCt,{columns:this.columns})}return a},clearInnerCt:function(){if(Ext.isIE){var a=this.innerCt.dom;while(a.firstChild){a.removeChild(a.firstChild)}}else{Ext.ux.tree.TreeGrid.superclass.clearInnerCt.call(this)}},initEvents:function(){Ext.ux.tree.TreeGrid.superclass.initEvents.apply(this,arguments);this.mon(this.innerBody,"scroll",this.syncScroll,this);this.mon(this.innerHd,"click",this.handleHdDown,this);this.mon(this.mainHd,{scope:this,mouseover:this.handleHdOver,mouseout:this.handleHdOut})},onResize:function(b,c){Ext.ux.tree.TreeGrid.superclass.onResize.apply(this,arguments);var e=this.innerBody.dom;var f=this.innerHd.dom;if(!e){return}if(Ext.isNumber(c)){e.style.height=this.body.getHeight(true)-f.offsetHeight+"px"}if(Ext.isNumber(b)){var a=Ext.num(this.scrollOffset,Ext.getScrollBarWidth());if(this.reserveScrollOffset||((e.offsetWidth-e.clientWidth)>10)){this.setScrollOffset(a)}else{var d=this;setTimeout(function(){d.setScrollOffset(e.offsetWidth-e.clientWidth>10?a:0)},10)}}},updateColumnWidths:function(){var k=this.columns,m=k.length,a=this.outerCt.query("colgroup"),l=a.length,h,e,d,b;for(d=0;d<m;d++){h=k[d];for(b=0;b<l;b++){e=a[b];e.childNodes[d].style.width=(h.hidden?0:h.width)+"px"}}for(d=0,a=this.innerHd.query("td"),len=a.length;d<len;d++){h=Ext.fly(a[d]);if(k[d]&&k[d].hidden){h.addClass("x-treegrid-hd-hidden")}else{h.removeClass("x-treegrid-hd-hidden")}}var f=this.getTotalColumnWidth();Ext.fly(this.innerHd.dom.firstChild).setWidth(f+(this.scrollOffset||0));this.outerCt.select("table").setWidth(f);this.syncHeaderScroll()},getVisibleColumns:function(){var c=[],d=this.columns,a=d.length,b;for(b=0;b<a;b++){if(!d[b].hidden){c.push(d[b])}}return c},getTotalColumnWidth:function(){var d=0;for(var b=0,c=this.getVisibleColumns(),a=c.length;b<a;b++){d+=c[b].width}return d},setScrollOffset:function(a){this.scrollOffset=a;this.updateColumnWidths()},handleHdDown:function(j,f){var h=j.getTarget(".x-treegrid-hd");if(h&&Ext.fly(f).hasClass("x-grid3-hd-btn")){var b=this.hmenu.items,g=this.columns,a=this.findHeaderIndex(h),k=g[a],d=k.sortable;j.stopEvent();Ext.fly(h).addClass("x-grid3-hd-menu-open");this.hdCtxIndex=a;this.fireEvent("headerbuttonclick",b,k,h,a);this.hmenu.on("hide",function(){Ext.fly(h).removeClass("x-grid3-hd-menu-open")},this,{single:true});this.hmenu.show(f,"tl-bl?")}else{if(h){var a=this.findHeaderIndex(h);this.fireEvent("headerclick",this.columns[a],h,a)}}},handleHdOver:function(d,a){var c=d.getTarget(".x-treegrid-hd");if(c&&!this.headersDisabled){index=this.findHeaderIndex(c);this.activeHdRef=a;this.activeHdIndex=index;var b=Ext.get(c);this.activeHdRegion=b.getRegion();b.addClass("x-grid3-hd-over");this.activeHdBtn=b.child(".x-grid3-hd-btn");if(this.activeHdBtn){this.activeHdBtn.dom.style.height=(c.firstChild.offsetHeight-1)+"px"}}},handleHdOut:function(c,a){var b=c.getTarget(".x-treegrid-hd");if(b&&(!Ext.isIE||!c.within(b,true))){this.activeHdRef=null;Ext.fly(b).removeClass("x-grid3-hd-over");b.style.cursor=""}},findHeaderIndex:function(d){d=d.dom||d;var b=d.parentNode.childNodes;for(var a=0,e;e=b[a];a++){if(e==d){return a}}return -1},beforeColMenuShow:function(){var d=this.columns,b=d.length,a,e;this.colMenu.removeAll();for(a=1;a<b;a++){e=d[a];if(e.hideable!==false){this.colMenu.add(new Ext.menu.CheckItem({itemId:"col-"+a,text:e.header,checked:!e.hidden,hideOnClick:false,disabled:e.hideable===false}))}}},handleHdMenuClick:function(b){var a=this.hdCtxIndex,c=b.getItemId();if(this.fireEvent("headermenuclick",this.columns[a],c,a)!==false){a=c.substr(4);if(a>0&&this.columns[a]){this.setColumnVisible(a,!b.checked)}}return true},setColumnVisible:function(a,b){this.columns[a].hidden=!b;this.updateColumnWidths()},scrollToTop:function(){this.innerBody.dom.scrollTop=0;this.innerBody.dom.scrollLeft=0},syncScroll:function(){this.syncHeaderScroll();var a=this.innerBody.dom;this.fireEvent("bodyscroll",a.scrollLeft,a.scrollTop)},syncHeaderScroll:function(){var a=this.innerBody.dom;this.innerHd.dom.scrollLeft=a.scrollLeft;this.innerHd.dom.scrollLeft=a.scrollLeft},registerNode:function(a){Ext.ux.tree.TreeGrid.superclass.registerNode.call(this,a);if(!a.uiProvider&&!a.isRoot&&!a.ui.isTreeGridNodeUI){a.ui=new Ext.ux.tree.TreeGridNodeUI(a)}}});Ext.reg("treegrid",Ext.ux.tree.TreeGrid);
/*
 * Ext JS Library 3.4.0
 * Copyright(c) 2006-2011 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */
Ext.tree.ColumnResizer=Ext.extend(Ext.util.Observable,{minWidth:14,constructor:function(a){Ext.apply(this,a);Ext.tree.ColumnResizer.superclass.constructor.call(this)},init:function(a){this.tree=a;a.on("render",this.initEvents,this)},initEvents:function(a){a.mon(a.innerHd,"mousemove",this.handleHdMove,this);this.tracker=new Ext.dd.DragTracker({onBeforeStart:this.onBeforeStart.createDelegate(this),onStart:this.onStart.createDelegate(this),onDrag:this.onDrag.createDelegate(this),onEnd:this.onEnd.createDelegate(this),tolerance:3,autoStart:300});this.tracker.initEl(a.innerHd);a.on("beforedestroy",this.tracker.destroy,this.tracker)},handleHdMove:function(f,k){var g=5,j=f.getPageX(),d=f.getTarget(".x-treegrid-hd",3,true);if(d){var b=d.getRegion(),l=d.dom.style,c=d.dom.parentNode;if(j-b.left<=g&&d.dom!==c.firstChild){var a=d.dom.previousSibling;while(a&&Ext.fly(a).hasClass("x-treegrid-hd-hidden")){a=a.previousSibling}if(a){this.activeHd=Ext.get(a);l.cursor=Ext.isWebKit?"e-resize":"col-resize"}}else{if(b.right-j<=g){var h=d.dom;while(h&&Ext.fly(h).hasClass("x-treegrid-hd-hidden")){h=h.previousSibling}if(h){this.activeHd=Ext.get(h);l.cursor=Ext.isWebKit?"w-resize":"col-resize"}}else{delete this.activeHd;l.cursor=""}}}},onBeforeStart:function(a){this.dragHd=this.activeHd;return !!this.dragHd},onStart:function(b){this.dragHeadersDisabled=this.tree.headersDisabled;this.tree.headersDisabled=true;this.proxy=this.tree.body.createChild({cls:"x-treegrid-resizer"});this.proxy.setHeight(this.tree.body.getHeight());var a=this.tracker.getXY()[0];this.hdX=this.dragHd.getX();this.hdIndex=this.tree.findHeaderIndex(this.dragHd);this.proxy.setX(this.hdX);this.proxy.setWidth(a-this.hdX);this.maxWidth=this.tree.outerCt.getWidth()-this.tree.innerBody.translatePoints(this.hdX).left},onDrag:function(b){var a=this.tracker.getXY()[0];this.proxy.setWidth((a-this.hdX).constrain(this.minWidth,this.maxWidth))},onEnd:function(d){var b=this.proxy.getWidth(),a=this.tree,c=this.dragHeadersDisabled;this.proxy.remove();delete this.dragHd;a.columns[this.hdIndex].width=b;a.updateColumnWidths();setTimeout(function(){a.headersDisabled=c},100)}});
/*
 * Ext JS Library 3.4.0
 * Copyright(c) 2006-2011 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */
(function(){Ext.override(Ext.list.Column,{init:function(){var b=Ext.data.Types,a=this.sortType;if(this.type){if(Ext.isString(this.type)){this.type=Ext.data.Types[this.type.toUpperCase()]||b.AUTO}}else{this.type=b.AUTO}if(Ext.isString(a)){this.sortType=Ext.data.SortTypes[a]}else{if(Ext.isEmpty(a)){this.sortType=this.type.sortType}}}});Ext.tree.Column=Ext.extend(Ext.list.Column,{});Ext.tree.NumberColumn=Ext.extend(Ext.list.NumberColumn,{});Ext.tree.DateColumn=Ext.extend(Ext.list.DateColumn,{});Ext.tree.BooleanColumn=Ext.extend(Ext.list.BooleanColumn,{});Ext.reg("tgcolumn",Ext.tree.Column);Ext.reg("tgnumbercolumn",Ext.tree.NumberColumn);Ext.reg("tgdatecolumn",Ext.tree.DateColumn);Ext.reg("tgbooleancolumn",Ext.tree.BooleanColumn)})();
/*
 * Ext JS Library 3.4.0
 * Copyright(c) 2006-2011 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */
Ext.ux.tree.TreeGridLoader=Ext.extend(Ext.tree.TreeLoader,{createNode:function(a){if(!a.uiProvider){a.uiProvider=Ext.ux.tree.TreeGridNodeUI}return Ext.tree.TreeLoader.prototype.createNode.call(this,a)}});
/*
 * Ext JS Library 3.4.0
 * Copyright(c) 2006-2011 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */
Ext.ux.tree.TreeGridNodeUI=Ext.extend(Ext.tree.TreeNodeUI,{isTreeGridNodeUI:true,renderElements:function(d,l,h,m){var o=d.getOwnerTree(),k=o.columns,j=k[0],e,b,g;this.indentMarkup=d.parentNode?d.parentNode.ui.getChildIndent():"";b=['<tbody class="x-tree-node">','<tr ext:tree-node-id="',d.id,'" class="x-tree-node-el x-tree-node-leaf ',l.cls,'">','<td class="x-treegrid-col">','<span class="x-tree-node-indent">',this.indentMarkup,"</span>",'<img src="',this.emptyIcon,'" class="x-tree-ec-icon x-tree-elbow" />','<img src="',l.icon||this.emptyIcon,'" class="x-tree-node-icon',(l.icon?" x-tree-node-inline-icon":""),(l.iconCls?" "+l.iconCls:""),'" unselectable="on" />','<a hidefocus="on" class="x-tree-node-anchor" href="',l.href?l.href:"#",'" tabIndex="1" ',l.hrefTarget?' target="'+l.hrefTarget+'"':"",">",'<span unselectable="on">',(j.tpl?j.tpl.apply(l):l[j.dataIndex]||j.text),"</span></a>","</td>"];for(e=1,g=k.length;e<g;e++){j=k[e];b.push('<td class="x-treegrid-col ',(j.cls?j.cls:""),'">','<div unselectable="on" class="x-treegrid-text"',(j.align?' style="text-align: '+j.align+';"':""),">",(j.tpl?j.tpl.apply(l):l[j.dataIndex]),"</div>","</td>")}b.push('</tr><tr class="x-tree-node-ct"><td colspan="',k.length,'">','<table class="x-treegrid-node-ct-table" cellpadding="0" cellspacing="0" style="table-layout: fixed; display: none; width: ',o.innerCt.getWidth(),'px;"><colgroup>');for(e=0,g=k.length;e<g;e++){b.push('<col style="width: ',(k[e].hidden?0:k[e].width),'px;" />')}b.push("</colgroup></table></td></tr></tbody>");if(m!==true&&d.nextSibling&&d.nextSibling.ui.getEl()){this.wrap=Ext.DomHelper.insertHtml("beforeBegin",d.nextSibling.ui.getEl(),b.join(""))}else{this.wrap=Ext.DomHelper.insertHtml("beforeEnd",h,b.join(""))}this.elNode=this.wrap.childNodes[0];this.ctNode=this.wrap.childNodes[1].firstChild.firstChild;var f=this.elNode.firstChild.childNodes;this.indentNode=f[0];this.ecNode=f[1];this.iconNode=f[2];this.anchor=f[3];this.textNode=f[3].firstChild},animExpand:function(a){this.ctNode.style.display="";Ext.ux.tree.TreeGridNodeUI.superclass.animExpand.call(this,a)}});Ext.ux.tree.TreeGridRootNodeUI=Ext.extend(Ext.tree.TreeNodeUI,{isTreeGridNodeUI:true,render:function(){if(!this.rendered){this.wrap=this.ctNode=this.node.ownerTree.innerCt.dom;this.node.expanded=true}if(Ext.isWebKit){var a=this.ctNode;a.style.tableLayout=null;(function(){a.style.tableLayout="fixed"}).defer(1)}},destroy:function(){if(this.elNode){Ext.dd.Registry.unregister(this.elNode.id)}delete this.node},collapse:Ext.emptyFn,expand:Ext.emptyFn});
/*
 * Ext.ux.tree.TreeGridNodeUIFix.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */
Ext.override(Ext.ux.tree.TreeGridNodeUI,{updateColumns:function(){if(!this.rendered){return}var b=this.node.attributes,d=this.node.getOwnerTree(),e=d.columns,f=e[0];this.anchor.firstChild.innerHTML=(f.tpl?f.tpl.apply(b):b[f.dataIndex]||f.text);for(i=1,len=e.length;i<len;i++){f=e[i];this.elNode.childNodes[i].firstChild.innerHTML=(f.tpl?f.tpl.apply(b):b[f.dataIndex]||f.text)}}});Ext.tree.RenderColumn=Ext.extend(Ext.tree.Column,{constructor:function(a){a.tpl=a.tpl||new Ext.XTemplate("{"+a.dataIndex+":this.format}");a.tpl.format=a.renderer;a.tpl.col=this;Ext.tree.RenderColumn.superclass.constructor.call(this,a)}});Ext.reg("tgrendercolumn",Ext.tree.RenderColumn);
/*
 * Ext JS Library 3.4.0
 * Copyright(c) 2006-2011 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */
Ext.ns("Ext.ux.tree");Ext.ux.tree.TreeGridSorter=Ext.extend(Ext.tree.TreeSorter,{sortClasses:["sort-asc","sort-desc"],sortAscText:"Sort Ascending",sortDescText:"Sort Descending",constructor:function(a,b){if(!Ext.isObject(b)){b={property:a.columns[0].dataIndex||"text",folderSort:true}}Ext.ux.tree.TreeGridSorter.superclass.constructor.apply(this,arguments);this.tree=a;a.on("headerclick",this.onHeaderClick,this);a.ddAppendOnly=true;var c=this;this.defaultSortFn=function(l,k){var j=c.dir&&c.dir.toLowerCase()=="desc",d=c.property||"text",f=c.sortType,n=c.caseSensitive===true,e=c.leafAttr||"leaf",o=l.attributes,m=k.attributes;if(c.folderSort){if(o[e]&&!m[e]){return 1}if(!o[e]&&m[e]){return -1}}var h=o[d],g=m[d],p=f?f(h):(n?h:h.toUpperCase());v2=f?f(g):(n?g:g.toUpperCase());if(p<v2){return j?+1:-1}else{if(p>v2){return j?-1:+1}else{return 0}}};a.on("afterrender",this.onAfterTreeRender,this,{single:true});a.on("headermenuclick",this.onHeaderMenuClick,this)},onAfterTreeRender:function(){if(this.tree.hmenu){this.tree.hmenu.insert(0,{itemId:"asc",text:this.sortAscText,cls:"xg-hmenu-sort-asc"},{itemId:"desc",text:this.sortDescText,cls:"xg-hmenu-sort-desc"})}this.updateSortIcon(0,"asc")},onHeaderMenuClick:function(d,b,a){if(b==="asc"||b==="desc"){this.onHeaderClick(d,null,a);return false}},onHeaderClick:function(e,b,a){if(e&&!this.tree.headersDisabled){var d=this;d.property=e.dataIndex;d.dir=e.dir=(e.dir==="desc"?"asc":"desc");d.sortType=e.sortType;d.caseSensitive===Ext.isBoolean(e.caseSensitive)?e.caseSensitive:this.caseSensitive;d.sortFn=e.sortFn||this.defaultSortFn;this.tree.root.cascade(function(c){if(!c.isLeaf()){d.updateSort(d.tree,c)}});this.updateSortIcon(a,e.dir)}},updateSortIcon:function(b,a){var d=this.sortClasses,c=this.tree.innerHd.select("td").removeClass(d);c.item(b).addClass(d[a=="desc"?1:0])}});
/*
 * Ext JS Library 3.4.0
 * Copyright(c) 2006-2011 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */
Ext.ns("Ext.ux.grid");Ext.ux.grid.BufferView=Ext.extend(Ext.grid.GridView,{rowHeight:19,borderHeight:2,scrollDelay:100,cacheSize:20,cleanDelay:500,initTemplates:function(){Ext.ux.grid.BufferView.superclass.initTemplates.call(this);var a=this.templates;a.rowHolder=new Ext.Template('<div class="x-grid3-row {alt}" style="{tstyle}"></div>');a.rowHolder.disableFormats=true;a.rowHolder.compile();a.rowBody=new Ext.Template('<table class="x-grid3-row-table" border="0" cellspacing="0" cellpadding="0" style="{tstyle}">',"<tbody><tr>{cells}</tr>",(this.enableRowBody?'<tr class="x-grid3-row-body-tr" style="{bodyStyle}"><td colspan="{cols}" class="x-grid3-body-cell" tabIndex="0" hidefocus="on"><div class="x-grid3-row-body">{body}</div></td></tr>':""),"</tbody></table>");a.rowBody.disableFormats=true;a.rowBody.compile()},getStyleRowHeight:function(){return Ext.isBorderBox?(this.rowHeight+this.borderHeight):this.rowHeight},getCalculatedRowHeight:function(){return this.rowHeight+this.borderHeight},getVisibleRowCount:function(){var b=this.getCalculatedRowHeight(),a=this.scroller.dom.clientHeight;return(a<1)?0:Math.ceil(a/b)},getVisibleRows:function(){var a=this.getVisibleRowCount(),b=this.scroller.dom.scrollTop,c=(b===0?0:Math.floor(b/this.getCalculatedRowHeight())-1);return{first:Math.max(c,0),last:Math.min(c+a+2,this.ds.getCount()-1)}},doRender:function(g,k,u,a,s,A,l){var b=this.templates,f=b.cell,h=b.row,x=b.rowBody,n=s-1,t=this.getStyleRowHeight(),z=this.getVisibleRows(),d="width:"+this.getTotalWidth()+";height:"+t+"px;",D=[],w,E,v={},m={tstyle:d},q;for(var y=0,C=k.length;y<C;y++){q=k[y];w=[];var o=(y+a),e=o>=z.first&&o<=z.last;if(e){for(var B=0;B<s;B++){E=g[B];v.id=E.id;v.css=B===0?"x-grid3-cell-first ":(B==n?"x-grid3-cell-last ":"");v.attr=v.cellAttr="";v.value=E.renderer(q.data[E.name],v,q,o,B,u);v.style=E.style;if(v.value===undefined||v.value===""){v.value="&#160;"}if(q.dirty&&typeof q.modified[E.name]!=="undefined"){v.css+=" x-grid3-dirty-cell"}w[w.length]=f.apply(v)}}var F=[];if(A&&((o+1)%2===0)){F[0]="x-grid3-row-alt"}if(q.dirty){F[1]=" x-grid3-dirty-row"}m.cols=s;if(this.getRowClass){F[2]=this.getRowClass(q,o,m,u)}m.alt=F.join(" ");m.cells=w.join("");D[D.length]=!e?b.rowHolder.apply(m):(l?x.apply(m):h.apply(m))}return D.join("")},isRowRendered:function(a){var b=this.getRow(a);return b&&b.childNodes.length>0},syncScroll:function(){Ext.ux.grid.BufferView.superclass.syncScroll.apply(this,arguments);this.update()},update:function(){if(this.scrollDelay){if(!this.renderTask){this.renderTask=new Ext.util.DelayedTask(this.doUpdate,this)}this.renderTask.delay(this.scrollDelay)}else{this.doUpdate()}},onRemove:function(d,a,b,c){Ext.ux.grid.BufferView.superclass.onRemove.apply(this,arguments);if(c!==true){this.update()}},doUpdate:function(){if(this.getVisibleRowCount()>0){var f=this.grid,b=f.colModel,h=f.store,e=this.getColumnData(),a=this.getVisibleRows(),j;for(var d=a.first;d<=a.last;d++){if(!this.isRowRendered(d)&&(j=this.getRow(d))){var c=this.doRender(e,[h.getAt(d)],h,d,b.getColumnCount(),f.stripeRows,true);j.innerHTML=c}}this.clean()}},clean:function(){if(!this.cleanTask){this.cleanTask=new Ext.util.DelayedTask(this.doClean,this)}this.cleanTask.delay(this.cleanDelay)},doClean:function(){if(this.getVisibleRowCount()>0){var b=this.getVisibleRows();b.first-=this.cacheSize;b.last+=this.cacheSize;var c=0,d=this.getRows();if(b.first<=0){c=b.last+1}for(var a=this.ds.getCount();c<a;c++){if((c<b.first||c>b.last)&&d[c].innerHTML){d[c].innerHTML=""}}}},removeTask:function(b){var a=this[b];if(a&&a.cancel){a.cancel();this[b]=null}},destroy:function(){this.removeTask("cleanTask");this.removeTask("renderTask");Ext.ux.grid.BufferView.superclass.destroy.call(this)},layout:function(){Ext.ux.grid.BufferView.superclass.layout.call(this);this.update()}});
/*
 * Ext JS Library 3.4.0
 * Copyright(c) 2006-2011 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */
Ext.ns("Ext.ux.form");Ext.ux.form.FileUploadField=Ext.extend(Ext.form.TextField,{buttonText:"Browse...",buttonOnly:false,buttonOffset:3,readOnly:true,autoSize:Ext.emptyFn,initComponent:function(){Ext.ux.form.FileUploadField.superclass.initComponent.call(this);this.addEvents("fileselected")},onRender:function(c,a){Ext.ux.form.FileUploadField.superclass.onRender.call(this,c,a);this.wrap=this.el.wrap({cls:"x-form-field-wrap x-form-file-wrap"});this.el.addClass("x-form-file-text");this.el.dom.removeAttribute("name");this.createFileInput();var b=Ext.applyIf(this.buttonCfg||{},{text:this.buttonText});this.button=new Ext.Button(Ext.apply(b,{renderTo:this.wrap,cls:"x-form-file-btn"+(b.iconCls?" x-btn-icon":"")}));if(this.buttonOnly){this.el.hide();this.wrap.setWidth(this.button.getEl().getWidth())}this.bindListeners();this.resizeEl=this.positionEl=this.wrap},bindListeners:function(){this.fileInput.on({scope:this,mouseenter:function(){this.button.addClass(["x-btn-over","x-btn-focus"])},mouseleave:function(){this.button.removeClass(["x-btn-over","x-btn-focus","x-btn-click"])},mousedown:function(){this.button.addClass("x-btn-click")},mouseup:function(){this.button.removeClass(["x-btn-over","x-btn-focus","x-btn-click"])},change:function(){var a=this.fileInput.dom.value;this.setValue(a);this.fireEvent("fileselected",this,a)}})},createFileInput:function(){this.fileInput=this.wrap.createChild({id:this.getFileInputId(),name:this.name||this.getId(),cls:"x-form-file",tag:"input",type:"file",size:1})},reset:function(){if(this.rendered){this.fileInput.remove();this.createFileInput();this.bindListeners()}Ext.ux.form.FileUploadField.superclass.reset.call(this)},getFileInputId:function(){return this.id+"-file"},onResize:function(a,b){Ext.ux.form.FileUploadField.superclass.onResize.call(this,a,b);this.wrap.setWidth(a);if(!this.buttonOnly){var a=this.wrap.getWidth()-this.button.getEl().getWidth()-this.buttonOffset;this.el.setWidth(a)}},onDestroy:function(){Ext.ux.form.FileUploadField.superclass.onDestroy.call(this);Ext.destroy(this.fileInput,this.button,this.wrap)},onDisable:function(){Ext.ux.form.FileUploadField.superclass.onDisable.call(this);this.doDisable(true)},onEnable:function(){Ext.ux.form.FileUploadField.superclass.onEnable.call(this);this.doDisable(false)},doDisable:function(a){this.fileInput.dom.disabled=a;this.button.setDisabled(a)},preFocus:Ext.emptyFn,alignErrorIcon:function(){this.errorIcon.alignTo(this.wrap,"tl-tr",[2,0])}});Ext.reg("fileuploadfield",Ext.ux.form.FileUploadField);Ext.form.FileUploadField=Ext.ux.form.FileUploadField;
/*
 * Ext.ux.form.RadioGroup.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */
Ext.override(Ext.form.RadioGroup,{afterRender:function(){this.items.each(function(a){this.relayEvents(a,["check"])},this);if(this.lazyValue){this.setValue(this.value);delete this.value;delete this.lazyValue}Ext.form.RadioGroup.superclass.afterRender.call(this)},getName:function(){return this.items.first().getName()},getValue:function(){return this.items.first().getGroupValue()},setValue:function(a){if(!this.items.each){this.value=a;this.lazyValue=true;return}this.items.each(function(c){if(c.rendered){var b=(c.el.getValue()==String(a));c.el.dom.checked=b;c.el.dom.defaultChecked=b;c.wrap[b?"addClass":"removeClass"](c.checkedCls)}})}});
/*
 * Ext JS Library 3.4.0
 * Copyright(c) 2006-2011 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */
Ext.ns("Ext.ux.form");Ext.ux.form.SpinnerField=Ext.extend(Ext.form.NumberField,{actionMode:"wrap",deferHeight:true,autoSize:Ext.emptyFn,onBlur:Ext.emptyFn,adjustSize:Ext.BoxComponent.prototype.adjustSize,constructor:function(c){var b=Ext.copyTo({},c,"incrementValue,alternateIncrementValue,accelerate,defaultValue,triggerClass,splitterClass");var d=this.spinner=new Ext.ux.Spinner(b);var a=c.plugins?(Ext.isArray(c.plugins)?c.plugins.push(d):[c.plugins,d]):d;Ext.ux.form.SpinnerField.superclass.constructor.call(this,Ext.apply(c,{plugins:a}))},getResizeEl:function(){return this.wrap},getPositionEl:function(){return this.wrap},alignErrorIcon:function(){if(this.wrap){this.errorIcon.alignTo(this.wrap,"tl-tr",[2,0])}},validateBlur:function(){return true}});Ext.reg("spinnerfield",Ext.ux.form.SpinnerField);Ext.form.SpinnerField=Ext.ux.form.SpinnerField;
/*
 * Ext.ux.form.SpinnerField.js
 * 
 * Copyright (c) Damien Churchill 2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */
Ext.override(Ext.ux.form.SpinnerField,{onBlur:Ext.form.Field.prototype.onBlur});
/*
 * Ext.ux.form.SpinnerGroup.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */
Ext.ns("Ext.ux.form");Ext.ux.form.SpinnerGroup=Ext.extend(Ext.form.CheckboxGroup,{defaultType:"spinnerfield",anchor:"98%",groupCls:"x-form-spinner-group",colCfg:{},onRender:function(h,f){if(!this.el){var o={cls:this.groupCls,layout:"column",border:false,renderTo:h};var a=Ext.apply({defaultType:this.defaultType,layout:"form",border:false,labelWidth:60,defaults:{hideLabel:true,anchor:"60%"}},this.colCfg);if(this.items[0].items){Ext.apply(o,{layoutConfig:{columns:this.items.length},defaults:this.defaults,items:this.items});for(var e=0,k=this.items.length;e<k;e++){Ext.applyIf(this.items[e],a)}}else{var d,m=[];if(typeof this.columns=="string"){this.columns=this.items.length}if(!Ext.isArray(this.columns)){var j=[];for(var e=0;e<this.columns;e++){j.push((100/this.columns)*0.01)}this.columns=j}d=this.columns.length;for(var e=0;e<d;e++){var b=Ext.apply({items:[]},a);b[this.columns[e]<=1?"columnWidth":"width"]=this.columns[e];if(this.defaults){b.defaults=Ext.apply(b.defaults||{},this.defaults)}m.push(b)}if(this.vertical){var q=Math.ceil(this.items.length/d),n=0;for(var e=0,k=this.items.length;e<k;e++){if(e>0&&e%q==0){n++}if(this.items[e].fieldLabel){this.items[e].hideLabel=false}m[n].items.push(this.items[e])}}else{for(var e=0,k=this.items.length;e<k;e++){var p=e%d;if(this.items[e].fieldLabel){this.items[e].hideLabel=false}m[p].items.push(this.items[e])}}Ext.apply(o,{layoutConfig:{columns:d},items:m})}this.panel=new Ext.Panel(o);this.el=this.panel.getEl();if(this.forId&&this.itemCls){var c=this.el.up(this.itemCls).child("label",true);if(c){c.setAttribute("htmlFor",this.forId)}}var g=this.panel.findBy(function(l){return l.isFormField},this);this.items=new Ext.util.MixedCollection();this.items.addAll(g);this.items.each(function(l){l.on("spin",this.onFieldChange,this);l.on("change",this.onFieldChange,this)},this);if(this.lazyValueSet){this.setValue(this.value);delete this.value;delete this.lazyValueSet}if(this.lazyRawValueSet){this.setRawValue(this.rawValue);delete this.rawValue;delete this.lazyRawValueSet}}Ext.ux.form.SpinnerGroup.superclass.onRender.call(this,h,f)},onFieldChange:function(a){this.fireEvent("change",this,this.getValue())},initValue:Ext.emptyFn,getValue:function(){var a=[this.items.getCount()];this.items.each(function(c,b){a[b]=Number(c.getValue())});return a},getRawValue:function(){var a=[this.items.getCount()];this.items.each(function(c,b){a[b]=Number(c.getRawValue())});return a},setValue:function(a){if(!this.rendered){this.value=a;this.lazyValueSet=true}else{this.items.each(function(c,b){c.setValue(a[b])})}},setRawValue:function(a){if(!this.rendered){this.rawValue=a;this.lazyRawValueSet=true}else{this.items.each(function(c,b){c.setRawValue(a[b])})}}});Ext.reg("spinnergroup",Ext.ux.form.SpinnerGroup);
/*
 * Ext.ux.form.ToggleField.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */
Ext.namespace("Ext.ux.form");Ext.ux.form.ToggleField=Ext.extend(Ext.form.Field,{cls:"x-toggle-field",initComponent:function(){Ext.ux.form.ToggleField.superclass.initComponent.call(this);this.toggle=new Ext.form.Checkbox();this.toggle.on("check",this.onToggleCheck,this);this.input=new Ext.form.TextField({disabled:true})},onRender:function(b,a){if(!this.el){this.panel=new Ext.Panel({cls:this.groupCls,layout:"table",layoutConfig:{columns:2},border:false,renderTo:b});this.panel.ownerCt=this;this.el=this.panel.getEl();this.panel.add(this.toggle);this.panel.add(this.input);this.panel.doLayout();this.toggle.getEl().parent().setStyle("padding-right","10px")}Ext.ux.form.ToggleField.superclass.onRender.call(this,b,a)},onResize:function(a,b){this.panel.setSize(a,b);this.panel.doLayout();var c=a-this.toggle.getSize().width-25;this.input.setSize(c,b)},onToggleCheck:function(a,b){this.input.setDisabled(!b)}});Ext.reg("togglefield",Ext.ux.form.ToggleField);Ext.ux.JSLoader=function(options){Ext.ux.JSLoader.scripts[++Ext.ux.JSLoader.index]={url:options.url,success:true,jsLoadObj:null,options:options,onLoad:options.onLoad||Ext.emptyFn,onError:options.onError||Ext.ux.JSLoader.stdError,scope:options.scope||this};Ext.Ajax.request({url:options.url,scriptIndex:Ext.ux.JSLoader.index,success:function(response,options){var script=Ext.ux.JSLoader.scripts[options.scriptIndex];try{eval(response.responseText)}catch(e){script.success=false;script.onError(script.options,e)}if(script.success){script.onLoad.call(script.scope,script.options)}},failure:function(response,options){var script=Ext.ux.JSLoader.scripts[options.scriptIndex];script.success=false;script.onError(script.options,response.status)}})};Ext.ux.JSLoader.index=0;Ext.ux.JSLoader.scripts=[];Ext.ux.JSLoader.stdError=function(a,b){window.alert("Error loading script:\n\n"+a.url+"\n\nstatus: "+b)}
/*
 * Ext JS Library 3.4.0
 * Copyright(c) 2006-2011 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */
;Ext.ux.Spinner=Ext.extend(Ext.util.Observable,{incrementValue:1,alternateIncrementValue:5,triggerClass:"x-form-spinner-trigger",splitterClass:"x-form-spinner-splitter",alternateKey:Ext.EventObject.shiftKey,defaultValue:0,accelerate:false,constructor:function(a){Ext.ux.Spinner.superclass.constructor.call(this,a);Ext.apply(this,a);this.mimicing=false},init:function(a){this.field=a;a.afterMethod("onRender",this.doRender,this);a.afterMethod("onEnable",this.doEnable,this);a.afterMethod("onDisable",this.doDisable,this);a.afterMethod("afterRender",this.doAfterRender,this);a.afterMethod("onResize",this.doResize,this);a.afterMethod("onFocus",this.doFocus,this);a.beforeMethod("onDestroy",this.doDestroy,this)},doRender:function(b,a){var c=this.el=this.field.getEl();var d=this.field;if(!d.wrap){d.wrap=this.wrap=c.wrap({cls:"x-form-field-wrap"})}else{this.wrap=d.wrap.addClass("x-form-field-wrap")}this.trigger=this.wrap.createChild({tag:"img",src:Ext.BLANK_IMAGE_URL,cls:"x-form-trigger "+this.triggerClass});if(!d.width){this.wrap.setWidth(c.getWidth()+this.trigger.getWidth())}this.splitter=this.wrap.createChild({tag:"div",cls:this.splitterClass,style:"width:13px; height:2px;"});this.splitter.setRight((Ext.isIE)?1:2).setTop(10).show();this.proxy=this.trigger.createProxy("",this.splitter,true);this.proxy.addClass("x-form-spinner-proxy");this.proxy.setStyle("left","0px");this.proxy.setSize(14,1);this.proxy.hide();this.dd=new Ext.dd.DDProxy(this.splitter.dom.id,"SpinnerDrag",{dragElId:this.proxy.id});this.initTrigger();this.initSpinner()},doAfterRender:function(){var a;if(Ext.isIE&&this.el.getY()!=(a=this.trigger.getY())){this.el.position();this.el.setY(a)}},doEnable:function(){if(this.wrap){this.disabled=false;this.wrap.removeClass(this.field.disabledClass)}},doDisable:function(){if(this.wrap){this.disabled=true;this.wrap.addClass(this.field.disabledClass);this.el.removeClass(this.field.disabledClass)}},doResize:function(a,b){if(typeof a=="number"){this.el.setWidth(a-this.trigger.getWidth())}this.wrap.setWidth(this.el.getWidth()+this.trigger.getWidth())},doFocus:function(){if(!this.mimicing){this.wrap.addClass("x-trigger-wrap-focus");this.mimicing=true;Ext.get(Ext.isIE?document.body:document).on("mousedown",this.mimicBlur,this,{delay:10});this.el.on("keydown",this.checkTab,this)}},checkTab:function(a){if(a.getKey()==a.TAB){this.triggerBlur()}},mimicBlur:function(a){if(!this.wrap.contains(a.target)&&this.field.validateBlur(a)){this.triggerBlur()}},triggerBlur:function(){this.mimicing=false;Ext.get(Ext.isIE?document.body:document).un("mousedown",this.mimicBlur,this);this.el.un("keydown",this.checkTab,this);this.field.beforeBlur();this.wrap.removeClass("x-trigger-wrap-focus");this.field.onBlur.call(this.field)},initTrigger:function(){this.trigger.addClassOnOver("x-form-trigger-over");this.trigger.addClassOnClick("x-form-trigger-click")},initSpinner:function(){this.field.addEvents({spin:true,spinup:true,spindown:true});this.keyNav=new Ext.KeyNav(this.el,{up:function(a){a.preventDefault();this.onSpinUp()},down:function(a){a.preventDefault();this.onSpinDown()},pageUp:function(a){a.preventDefault();this.onSpinUpAlternate()},pageDown:function(a){a.preventDefault();this.onSpinDownAlternate()},scope:this});this.repeater=new Ext.util.ClickRepeater(this.trigger,{accelerate:this.accelerate});this.field.mon(this.repeater,"click",this.onTriggerClick,this,{preventDefault:true});this.field.mon(this.trigger,{mouseover:this.onMouseOver,mouseout:this.onMouseOut,mousemove:this.onMouseMove,mousedown:this.onMouseDown,mouseup:this.onMouseUp,scope:this,preventDefault:true});this.field.mon(this.wrap,"mousewheel",this.handleMouseWheel,this);this.dd.setXConstraint(0,0,10);this.dd.setYConstraint(1500,1500,10);this.dd.endDrag=this.endDrag.createDelegate(this);this.dd.startDrag=this.startDrag.createDelegate(this);this.dd.onDrag=this.onDrag.createDelegate(this)},onMouseOver:function(){if(this.disabled){return}var a=this.getMiddle();this.tmpHoverClass=(Ext.EventObject.getPageY()<a)?"x-form-spinner-overup":"x-form-spinner-overdown";this.trigger.addClass(this.tmpHoverClass)},onMouseOut:function(){this.trigger.removeClass(this.tmpHoverClass)},onMouseMove:function(){if(this.disabled){return}var a=this.getMiddle();if(((Ext.EventObject.getPageY()>a)&&this.tmpHoverClass=="x-form-spinner-overup")||((Ext.EventObject.getPageY()<a)&&this.tmpHoverClass=="x-form-spinner-overdown")){}},onMouseDown:function(){if(this.disabled){return}var a=this.getMiddle();this.tmpClickClass=(Ext.EventObject.getPageY()<a)?"x-form-spinner-clickup":"x-form-spinner-clickdown";this.trigger.addClass(this.tmpClickClass)},onMouseUp:function(){this.trigger.removeClass(this.tmpClickClass)},onTriggerClick:function(){if(this.disabled||this.el.dom.readOnly){return}var b=this.getMiddle();var a=(Ext.EventObject.getPageY()<b)?"Up":"Down";this["onSpin"+a]()},getMiddle:function(){var b=this.trigger.getTop();var c=this.trigger.getHeight();var a=b+(c/2);return a},isSpinnable:function(){if(this.disabled||this.el.dom.readOnly){Ext.EventObject.preventDefault();return false}return true},handleMouseWheel:function(a){if(this.wrap.hasClass("x-trigger-wrap-focus")==false){return}var b=a.getWheelDelta();if(b>0){this.onSpinUp();a.stopEvent()}else{if(b<0){this.onSpinDown();a.stopEvent()}}},startDrag:function(){this.proxy.show();this._previousY=Ext.fly(this.dd.getDragEl()).getTop()},endDrag:function(){this.proxy.hide()},onDrag:function(){if(this.disabled){return}var b=Ext.fly(this.dd.getDragEl()).getTop();var a="";if(this._previousY>b){a="Up"}if(this._previousY<b){a="Down"}if(a!=""){this["onSpin"+a]()}this._previousY=b},onSpinUp:function(){if(this.isSpinnable()==false){return}if(Ext.EventObject.shiftKey==true){this.onSpinUpAlternate();return}else{this.spin(false,false)}this.field.fireEvent("spin",this);this.field.fireEvent("spinup",this)},onSpinDown:function(){if(this.isSpinnable()==false){return}if(Ext.EventObject.shiftKey==true){this.onSpinDownAlternate();return}else{this.spin(true,false)}this.field.fireEvent("spin",this);this.field.fireEvent("spindown",this)},onSpinUpAlternate:function(){if(this.isSpinnable()==false){return}this.spin(false,true);this.field.fireEvent("spin",this);this.field.fireEvent("spinup",this)},onSpinDownAlternate:function(){if(this.isSpinnable()==false){return}this.spin(true,true);this.field.fireEvent("spin",this);this.field.fireEvent("spindown",this)},spin:function(d,b){var a=parseFloat(this.field.getValue());var c=(b==true)?this.alternateIncrementValue:this.incrementValue;(d==true)?a-=c:a+=c;a=(isNaN(a))?this.defaultValue:a;a=this.fixBoundries(a);this.field.setRawValue(a)},fixBoundries:function(b){var a=b;if(this.field.minValue!=undefined&&a<this.field.minValue){a=this.field.minValue}if(this.field.maxValue!=undefined&&a>this.field.maxValue){a=this.field.maxValue}return this.fixPrecision(a)},fixPrecision:function(b){var a=isNaN(b);if(!this.field.allowDecimals||this.field.decimalPrecision==-1||a||!b){return a?"":b}return parseFloat(parseFloat(b).toFixed(this.field.decimalPrecision))},doDestroy:function(){if(this.trigger){this.trigger.remove()}if(this.wrap){this.wrap.remove();delete this.field.wrap}if(this.splitter){this.splitter.remove()}if(this.dd){this.dd.unreg();this.dd=null}if(this.proxy){this.proxy.remove()}if(this.repeater){this.repeater.purgeListeners()}if(this.mimicing){Ext.get(Ext.isIE?document.body:document).un("mousedown",this.mimicBlur,this)}}});Ext.form.Spinner=Ext.ux.Spinner;
/*
 * Ext JS Library 3.4.0
 * Copyright(c) 2006-2011 Sencha Inc.
 * licensing@sencha.com
 * http://www.sencha.com/license
 */
Ext.ux.StatusBar=Ext.extend(Ext.Toolbar,{cls:"x-statusbar",busyIconCls:"x-status-busy",busyText:"Loading...",autoClear:5000,emptyText:"&nbsp;",activeThreadId:0,initComponent:function(){if(this.statusAlign=="right"){this.cls+=" x-status-right"}Ext.ux.StatusBar.superclass.initComponent.call(this)},afterRender:function(){Ext.ux.StatusBar.superclass.afterRender.call(this);var a=this.statusAlign=="right";this.currIconCls=this.iconCls||this.defaultIconCls;this.statusEl=new Ext.Toolbar.TextItem({cls:"x-status-text "+(this.currIconCls||""),text:this.text||this.defaultText||""});if(a){this.add("->");this.add(this.statusEl)}else{this.insert(0,this.statusEl);this.insert(1,"->")}this.doLayout()},setStatus:function(d){d=d||{};if(typeof d=="string"){d={text:d}}if(d.text!==undefined){this.setText(d.text)}if(d.iconCls!==undefined){this.setIcon(d.iconCls)}if(d.clear){var e=d.clear,b=this.autoClear,a={useDefaults:true,anim:true};if(typeof e=="object"){e=Ext.applyIf(e,a);if(e.wait){b=e.wait}}else{if(typeof e=="number"){b=e;e=a}else{if(typeof e=="boolean"){e=a}}}e.threadId=this.activeThreadId;this.clearStatus.defer(b,this,[e])}return this},clearStatus:function(c){c=c||{};if(c.threadId&&c.threadId!==this.activeThreadId){return this}var b=c.useDefaults?this.defaultText:this.emptyText,a=c.useDefaults?(this.defaultIconCls?this.defaultIconCls:""):"";if(c.anim){this.statusEl.el.fadeOut({remove:false,useDisplay:true,scope:this,callback:function(){this.setStatus({text:b,iconCls:a});this.statusEl.el.show()}})}else{this.statusEl.hide();this.setStatus({text:b,iconCls:a});this.statusEl.show()}return this},setText:function(a){this.activeThreadId++;this.text=a||"";if(this.rendered){this.statusEl.setText(this.text)}return this},getText:function(){return this.text},setIcon:function(a){this.activeThreadId++;a=a||"";if(this.rendered){if(this.currIconCls){this.statusEl.removeClass(this.currIconCls);this.currIconCls=null}if(a.length>0){this.statusEl.addClass(a);this.currIconCls=a}}else{this.currIconCls=a}return this},showBusy:function(a){if(typeof a=="string"){a={text:a}}a=Ext.applyIf(a||{},{text:this.busyText,iconCls:this.busyIconCls});return this.setStatus(a)}});Ext.reg("statusbar",Ext.ux.StatusBar);