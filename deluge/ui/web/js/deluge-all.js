/*
 * Deluge.data.SortTypes.js
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
Ext.namespace("Deluge.data");Deluge.data.SortTypes={asIPAddress:function(a){var b=a.match(/(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\:(\d+)/);return((((((+b[1])*256)+(+b[2]))*256)+(+b[3]))*256)+(+b[4])},asQueuePosition:function(a){return(a>-1)?a:Number.MAX_VALUE},asName:function(a){return String(a).toLowerCase()}}
/*
 * Deluge.data.PeerRecord.js
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
;Ext.namespace("Deluge.data");Deluge.data.Peer=Ext.data.Record.create([{name:"country",type:"string"},{name:"ip",type:"string",sortType:Deluge.data.SortTypes.asIPAddress},{name:"client",type:"string"},{name:"progress",type:"float"},{name:"down_speed",type:"int"},{name:"up_speed",type:"int"},{name:"seed",type:"int"}]);
/*
 * Deluge.data.TorrentRecord.js
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
Ext.namespace("Deluge.data");Deluge.data.Torrent=Ext.data.Record.create([{name:"queue",type:"int"},{name:"name",type:"string",sortType:Deluge.data.SortTypes.asName},{name:"total_wanted",type:"int"},{name:"state",type:"string"},{name:"progress",type:"int"},{name:"num_seeds",type:"int"},{name:"total_seeds",type:"int"},{name:"num_peers",type:"int"},{name:"total_peers",type:"int"},{name:"download_payload_rate",type:"int"},{name:"upload_payload_rate",type:"int"},{name:"eta",type:"int"},{name:"ratio",type:"float"},{name:"distributed_copies",type:"float"},{name:"time_added",type:"int"},{name:"tracker_host",type:"string"},{name:"save_path",type:"string"},{name:"total_done",type:"int"},{name:"total_uploaded",type:"int"},{name:"max_download_speed",type:"int"},{name:"max_upload_speed",type:"int"},{name:"seeds_peers_ratio",type:"float"}]);
/*
 * Deluge.details.DetailsPanel.js
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
Ext.namespace("Deluge.details");Deluge.details.DetailsPanel=Ext.extend(Ext.TabPanel,{id:"torrentDetails",activeTab:0,initComponent:function(){Deluge.details.DetailsPanel.superclass.initComponent.call(this);this.add(new Deluge.details.StatusTab());this.add(new Deluge.details.DetailsTab());this.add(new Deluge.details.FilesTab());this.add(new Deluge.details.PeersTab());this.add(new Deluge.details.OptionsTab())},clear:function(){this.items.each(function(a){if(a.clear){a.clear.defer(100,a);a.disable()}})},update:function(a){var b=deluge.torrents.getSelected();if(!b){this.clear();return}this.items.each(function(c){if(c.disabled){c.enable()}});a=a||this.getActiveTab();if(a.update){a.update(b.id)}},onRender:function(b,a){Deluge.details.DetailsPanel.superclass.onRender.call(this,b,a);deluge.events.on("disconnect",this.clear,this);deluge.torrents.on("rowclick",this.onTorrentsClick,this);this.on("tabchange",this.onTabChange,this);deluge.torrents.getSelectionModel().on("selectionchange",function(c){if(!c.hasSelection()){this.clear()}},this)},onTabChange:function(a,b){this.update(b)},onTorrentsClick:function(a,c,b){this.update()}});Deluge.details.DetailsTab=Ext.extend(Ext.Panel,{title:_("Details"),fields:{},autoScroll:true,queuedItems:{},oldData:{},initComponent:function(){Deluge.details.DetailsTab.superclass.initComponent.call(this);this.addItem("torrent_name",_("Name"));this.addItem("hash",_("Hash"));this.addItem("path",_("Path"));this.addItem("size",_("Total Size"));this.addItem("files",_("# of files"));this.addItem("comment",_("Comment"));this.addItem("status",_("Status"));this.addItem("tracker",_("Tracker"))},onRender:function(b,a){Deluge.details.DetailsTab.superclass.onRender.call(this,b,a);this.body.setStyle("padding","10px");this.dl=Ext.DomHelper.append(this.body,{tag:"dl"},true);for(var c in this.queuedItems){this.doAddItem(c,this.queuedItems[c])}},addItem:function(b,a){if(!this.rendered){this.queuedItems[b]=a}else{this.doAddItem(b,a)}},doAddItem:function(b,a){Ext.DomHelper.append(this.dl,{tag:"dt",cls:b,html:a+":"});this.fields[b]=Ext.DomHelper.append(this.dl,{tag:"dd",cls:b,html:""},true)},clear:function(){if(!this.fields){return}for(var a in this.fields){this.fields[a].dom.innerHTML=""}this.oldData={}},update:function(a){deluge.client.web.get_torrent_status(a,Deluge.Keys.Details,{success:this.onRequestComplete,scope:this,torrentId:a})},onRequestComplete:function(e,c,a,b){var d={torrent_name:e.name,hash:b.options.torrentId,path:e.save_path,size:fsize(e.total_size),files:e.num_files,status:e.message,tracker:e.tracker,comment:e.comment};for(var f in this.fields){if(!Ext.isDefined(d[f])){continue}if(d[f]==this.oldData[f]){continue}this.fields[f].dom.innerHTML=Ext.escapeHTML(d[f])}this.oldData=d}});
/*
 * Deluge.details.FilesTab.js
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
Deluge.details.FilesTab=Ext.extend(Ext.ux.tree.TreeGrid,{title:_("Files"),rootVisible:false,columns:[{header:_("Filename"),width:330,dataIndex:"filename"},{header:_("Size"),width:150,dataIndex:"size",tpl:new Ext.XTemplate("{size:this.fsize}",{fsize:function(a){return fsize(a)}})},{xtype:"tgrendercolumn",header:_("Progress"),width:150,dataIndex:"progress",renderer:function(a){var b=a*100;return Deluge.progressBar(b,this.col.width,b.toFixed(2)+"%",0)}},{header:_("Priority"),width:150,dataIndex:"priority",tpl:new Ext.XTemplate('<tpl if="!isNaN(priority)"><div class="{priority:this.getClass}">{priority:this.getName}</div></tpl>',{getClass:function(a){return FILE_PRIORITY_CSS[a]},getName:function(a){return _(FILE_PRIORITY[a])}})}],selModel:new Ext.tree.MultiSelectionModel(),initComponent:function(){Deluge.details.FilesTab.superclass.initComponent.call(this);this.setRootNode(new Ext.tree.TreeNode({text:"Files"}))},clear:function(){var a=this.getRootNode();if(!a.hasChildNodes()){return}a.cascade(function(c){var b=c.parentNode;if(!b){return}if(!b.ownerTree){return}b.removeChild(c)})},createFileTree:function(c){function b(g,d){for(var e in g.contents){var f=g.contents[e];if(f.type=="dir"){b(f,d.appendChild(new Ext.tree.TreeNode({text:e,filename:e,size:f.size,progress:f.progress,priority:f.priority})))}else{d.appendChild(new Ext.tree.TreeNode({text:e,filename:e,fileIndex:f.index,size:f.size,progress:f.progress,priority:f.priority,leaf:true,iconCls:"x-deluge-file",uiProvider:Ext.ux.tree.TreeGridNodeUI}))}}}var a=this.getRootNode();b(c,a);a.firstChild.expand()},update:function(a){if(this.torrentId!=a){this.clear();this.torrentId=a}deluge.client.web.get_torrent_files(a,{success:this.onRequestComplete,scope:this,torrentId:a})},updateFileTree:function(b){function a(g,c){for(var d in g.contents){var f=g.contents[d];var e=c.findChild("filename",d);e.attributes.size=f.size;e.attributes.progress=f.progress;e.attributes.priority=f.priority;e.ui.updateColumns();if(f.type=="dir"){a(f,e)}}}a(b,this.getRootNode())},onRender:function(b,a){Deluge.details.FilesTab.superclass.onRender.call(this,b,a);deluge.menus.filePriorities.on("itemclick",this.onItemClick,this);this.on("contextmenu",this.onContextMenu,this);this.sorter=new Ext.tree.TreeSorter(this,{folderSort:true})},onContextMenu:function(b,c){c.stopEvent();var a=this.getSelectionModel();if(a.getSelectedNodes().length<2){a.clearSelections();b.select()}deluge.menus.filePriorities.showAt(c.getPoint())},onItemClick:function(h,g){switch(h.id){case"expandAll":this.expandAll();break;default:var f={};function a(e){if(Ext.isEmpty(e.attributes.fileIndex)){return}f[e.attributes.fileIndex]=e.attributes.priority}this.getRootNode().cascade(a);var b=this.getSelectionModel().getSelectedNodes();Ext.each(b,function(i){if(!i.isLeaf()){function e(j){if(Ext.isEmpty(j.attributes.fileIndex)){return}f[j.attributes.fileIndex]=h.filePriority}i.cascade(e)}else{if(!Ext.isEmpty(i.attributes.fileIndex)){f[i.attributes.fileIndex]=h.filePriority;return}}});var d=new Array(Ext.keys(f).length);for(var c in f){d[c]=f[c]}deluge.client.core.set_torrent_file_priorities(this.torrentId,d,{success:function(){Ext.each(b,function(e){e.setColumnValue(3,h.filePriority)})},scope:this});break}},onRequestComplete:function(b,a){if(!this.getRootNode().hasChildNodes()){this.createFileTree(b)}else{this.updateFileTree(b)}}});
/*
 * Deluge.details.OptionsTab.js
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
Deluge.details.OptionsTab=Ext.extend(Ext.form.FormPanel,{constructor:function(a){a=Ext.apply({autoScroll:true,bodyStyle:"padding: 5px;",border:false,cls:"x-deluge-options",defaults:{autoHeight:true,labelWidth:1,defaultType:"checkbox"},deferredRender:false,layout:"column",title:_("Options")},a);Deluge.details.OptionsTab.superclass.constructor.call(this,a)},initComponent:function(){Deluge.details.OptionsTab.superclass.initComponent.call(this);this.fieldsets={},this.fields={};this.optionsManager=new Deluge.MultiOptionsManager({options:{max_download_speed:-1,max_upload_speed:-1,max_connections:-1,max_upload_slots:-1,auto_managed:false,stop_at_ratio:false,stop_ratio:2,remove_at_ratio:false,move_completed:false,move_completed_path:"","private":false,prioritize_first_last:false}});this.fieldsets.bandwidth=this.add({xtype:"fieldset",defaultType:"spinnerfield",bodyStyle:"padding: 5px",layout:"table",layoutConfig:{columns:3},labelWidth:150,style:"margin-left: 10px; margin-right: 5px; padding: 5px",title:_("Bandwidth"),width:250});this.fieldsets.bandwidth.add({xtype:"label",text:_("Max Download Speed"),forId:"max_download_speed",cls:"x-deluge-options-label"});this.fields.max_download_speed=this.fieldsets.bandwidth.add({id:"max_download_speed",name:"max_download_speed",width:70,strategy:{xtype:"number",decimalPrecision:1,minValue:-1,maxValue:99999}});this.fieldsets.bandwidth.add({xtype:"label",text:_("KiB/s"),style:"margin-left: 10px"});this.fieldsets.bandwidth.add({xtype:"label",text:_("Max Upload Speed"),forId:"max_upload_speed",cls:"x-deluge-options-label"});this.fields.max_upload_speed=this.fieldsets.bandwidth.add({id:"max_upload_speed",name:"max_upload_speed",width:70,value:-1,strategy:{xtype:"number",decimalPrecision:1,minValue:-1,maxValue:99999}});this.fieldsets.bandwidth.add({xtype:"label",text:_("KiB/s"),style:"margin-left: 10px"});this.fieldsets.bandwidth.add({xtype:"label",text:_("Max Connections"),forId:"max_connections",cls:"x-deluge-options-label"});this.fields.max_connections=this.fieldsets.bandwidth.add({id:"max_connections",name:"max_connections",width:70,value:-1,strategy:{xtype:"number",decimalPrecision:0,minValue:-1,maxValue:99999},colspan:2});this.fieldsets.bandwidth.add({xtype:"label",text:_("Max Upload Slots"),forId:"max_upload_slots",cls:"x-deluge-options-label"});this.fields.max_upload_slots=this.fieldsets.bandwidth.add({id:"max_upload_slots",name:"max_upload_slots",width:70,value:-1,strategy:{xtype:"number",decimalPrecision:0,minValue:-1,maxValue:99999},colspan:2});this.fieldsets.queue=this.add({xtype:"fieldset",title:_("Queue"),style:"margin-left: 5px; margin-right: 5px; padding: 5px",width:210,layout:"table",layoutConfig:{columns:2},labelWidth:0,defaults:{fieldLabel:"",labelSeparator:""}});this.fields.auto_managed=this.fieldsets.queue.add({xtype:"checkbox",fieldLabel:"",labelSeparator:"",name:"is_auto_managed",boxLabel:_("Auto Managed"),width:200,colspan:2});this.fields.stop_at_ratio=this.fieldsets.queue.add({fieldLabel:"",labelSeparator:"",id:"stop_at_ratio",width:120,boxLabel:_("Stop seed at ratio"),handler:this.onStopRatioChecked,scope:this});this.fields.stop_ratio=this.fieldsets.queue.add({xtype:"spinnerfield",id:"stop_ratio",name:"stop_ratio",disabled:true,width:50,value:2,strategy:{xtype:"number",minValue:-1,maxValue:99999,incrementValue:0.1,alternateIncrementValue:1,decimalPrecision:1}});this.fields.remove_at_ratio=this.fieldsets.queue.add({fieldLabel:"",labelSeparator:"",id:"remove_at_ratio",ctCls:"x-deluge-indent-checkbox",bodyStyle:"padding-left: 10px",boxLabel:_("Remove at ratio"),disabled:true,colspan:2});this.fields.move_completed=this.fieldsets.queue.add({fieldLabel:"",labelSeparator:"",id:"move_completed",boxLabel:_("Move Completed"),colspan:2,handler:this.onMoveCompletedChecked,scope:this});this.fields.move_completed_path=this.fieldsets.queue.add({xtype:"textfield",fieldLabel:"",id:"move_completed_path",colspan:3,bodyStyle:"margin-left: 20px",width:180,disabled:true});this.rightColumn=this.add({border:false,autoHeight:true,style:"margin-left: 5px",width:210});this.fieldsets.general=this.rightColumn.add({xtype:"fieldset",autoHeight:true,defaultType:"checkbox",title:_("General"),layout:"form"});this.fields["private"]=this.fieldsets.general.add({fieldLabel:"",labelSeparator:"",boxLabel:_("Private"),id:"private",disabled:true});this.fields.prioritize_first_last=this.fieldsets.general.add({fieldLabel:"",labelSeparator:"",boxLabel:_("Prioritize First/Last"),id:"prioritize_first_last"});for(var a in this.fields){this.optionsManager.bind(a,this.fields[a])}this.buttonPanel=this.rightColumn.add({layout:"hbox",xtype:"panel",border:false});this.buttonPanel.add({id:"edit_trackers",xtype:"button",text:_("Edit Trackers"),cls:"x-btn-text-icon",iconCls:"x-deluge-edit-trackers",border:false,width:100,handler:this.onEditTrackers,scope:this});this.buttonPanel.add({id:"apply",xtype:"button",text:_("Apply"),style:"margin-left: 10px;",border:false,width:100,handler:this.onApply,scope:this})},onRender:function(b,a){Deluge.details.OptionsTab.superclass.onRender.call(this,b,a);this.layout=new Ext.layout.ColumnLayout();this.layout.setContainer(this);this.doLayout()},clear:function(){if(this.torrentId==null){return}this.torrentId=null;this.optionsManager.changeId(null)},reset:function(){if(this.torrentId){this.optionsManager.reset()}},update:function(a){if(this.torrentId&&!a){this.clear()}if(!a){return}if(this.torrentId!=a){this.torrentId=a;this.optionsManager.changeId(a)}deluge.client.web.get_torrent_status(a,Deluge.Keys.Options,{success:this.onRequestComplete,scope:this})},onApply:function(){var b=this.optionsManager.getDirty();if(!Ext.isEmpty(b.prioritize_first_last)){var a=b.prioritize_first_last;deluge.client.core.set_torrent_prioritize_first_last(this.torrentId,a,{success:function(){this.optionsManager.set("prioritize_first_last",a)},scope:this})}deluge.client.core.set_torrent_options([this.torrentId],b,{success:function(){this.optionsManager.commit()},scope:this})},onEditTrackers:function(){deluge.editTrackers.show()},onMoveCompletedChecked:function(b,a){this.fields.move_completed_path.setDisabled(!a);if(!a){return}this.fields.move_completed_path.focus()},onStopRatioChecked:function(b,a){this.fields.remove_at_ratio.setDisabled(!a);this.fields.stop_ratio.setDisabled(!a)},onRequestComplete:function(c,b){this.fields["private"].setValue(c["private"]);this.fields["private"].setDisabled(true);delete c["private"];c.auto_managed=c.is_auto_managed;this.optionsManager.setDefault(c);var a=this.optionsManager.get("stop_at_ratio");this.fields.remove_at_ratio.setDisabled(!a);this.fields.stop_ratio.setDisabled(!a);this.fields.move_completed_path.setDisabled(!this.optionsManager.get("move_completed"))}});
/*
 * Deluge.details.PeersTab.js
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
(function(){function a(d){if(!d.replace(" ","").replace(" ","")){return""}return String.format('<img src="{0}flag/{1}" />',deluge.config.base,d)}function b(h,i,f){var e=(f.data.seed==1024)?"x-deluge-seed":"x-deluge-peer";var d=h.split(":");if(d.length>2){var g=d.pop();var j=d.join(":");h="["+j+"]:"+g}return String.format('<div class="{0}">{1}</div>',e,h)}function c(e){var d=(e*100).toFixed(0);return Deluge.progressBar(d,this.width-8,d+"%")}Deluge.details.PeersTab=Ext.extend(Ext.grid.GridPanel,{peers:{},constructor:function(d){d=Ext.apply({title:_("Peers"),cls:"x-deluge-peers",store:new Ext.data.Store({reader:new Ext.data.JsonReader({idProperty:"ip",root:"peers"},Deluge.data.Peer)}),columns:[{header:"&nbsp;",width:30,sortable:true,renderer:a,dataIndex:"country"},{header:"Address",width:125,sortable:true,renderer:b,dataIndex:"ip"},{header:"Client",width:125,sortable:true,renderer:fplain,dataIndex:"client"},{header:"Progress",width:150,sortable:true,renderer:c,dataIndex:"progress"},{header:"Down Speed",width:100,sortable:true,renderer:fspeed,dataIndex:"down_speed"},{header:"Up Speed",width:100,sortable:true,renderer:fspeed,dataIndex:"up_speed"}],stripeRows:true,deferredRender:false,autoScroll:true},d);Deluge.details.PeersTab.superclass.constructor.call(this,d)},clear:function(){this.getStore().removeAll();this.peers={}},update:function(d){deluge.client.web.get_torrent_status(d,Deluge.Keys.Peers,{success:this.onRequestComplete,scope:this})},onRequestComplete:function(h,g){if(!h){return}var f=this.getStore();var e=[];var i={};Ext.each(h.peers,function(m){if(this.peers[m.ip]){var j=f.getById(m.ip);j.beginEdit();for(var l in m){if(j.get(l)!=m[l]){j.set(l,m[l])}}j.endEdit()}else{this.peers[m.ip]=1;e.push(new Deluge.data.Peer(m,m.ip))}i[m.ip]=1},this);f.add(e);f.each(function(j){if(!i[j.id]){f.remove(j);delete this.peers[j.id]}},this);f.commitChanges();var d=f.getSortState();if(!d){return}f.sort(d.field,d.direction)}})})();
/*
 * Deluge.details.StatusTab.js
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
Ext.ns("Deluge.details");Deluge.details.StatusTab=Ext.extend(Ext.Panel,{title:_("Status"),autoScroll:true,onRender:function(b,a){Deluge.details.StatusTab.superclass.onRender.call(this,b,a);this.progressBar=this.add({xtype:"progress",cls:"x-deluge-status-progressbar"});this.status=this.add({cls:"x-deluge-status",id:"deluge-details-status",border:false,width:1000,listeners:{render:{fn:function(c){c.load({url:deluge.config.base+"render/tab_status.html",text:_("Loading")+"..."});c.getUpdater().on("update",this.onPanelUpdate,this)},scope:this}}})},clear:function(){this.progressBar.updateProgress(0," ");for(var a in this.fields){this.fields[a].innerHTML=""}},update:function(a){if(!this.fields){this.getFields()}deluge.client.web.get_torrent_status(a,Deluge.Keys.Status,{success:this.onRequestComplete,scope:this})},onPanelUpdate:function(b,a){this.fields={};Ext.each(Ext.query("dd",this.status.body.dom),function(c){this.fields[c.className]=c},this)},onRequestComplete:function(a){seeders=a.total_seeds>-1?a.num_seeds+" ("+a.total_seeds+")":a.num_seeds;peers=a.total_peers>-1?a.num_peers+" ("+a.total_peers+")":a.num_peers;var d={downloaded:fsize(a.total_done,true),uploaded:fsize(a.total_uploaded,true),share:(a.ratio==-1)?"&infin;":a.ratio.toFixed(3),announce:ftime(a.next_announce),tracker_status:a.tracker_status,downspeed:(a.download_payload_rate)?fspeed(a.download_payload_rate):"0.0 KiB/s",upspeed:(a.upload_payload_rate)?fspeed(a.upload_payload_rate):"0.0 KiB/s",eta:ftime(a.eta),pieces:a.num_pieces+" ("+fsize(a.piece_length)+")",seeders:seeders,peers:peers,avail:a.distributed_copies.toFixed(3),active_time:ftime(a.active_time),seeding_time:ftime(a.seeding_time),seed_rank:a.seed_rank,time_added:fdate(a.time_added)};d.auto_managed=_((a.is_auto_managed)?"True":"False");var c={Error:_("Error"),Warning:_("Warning"),"Announce OK":_("Announce OK"),"Announce Sent":_("Announce Sent")};for(var b in c){if(d.tracker_status.indexOf(b)!=-1){d.tracker_status=d.tracker_status.replace(b,c[b]);break}}d.downloaded+=" ("+((a.total_payload_download)?fsize(a.total_payload_download):"0.0 KiB")+")";d.uploaded+=" ("+((a.total_payload_upload)?fsize(a.total_payload_upload):"0.0 KiB")+")";for(var e in this.fields){this.fields[e].innerHTML=d[e]}var f=a.state+" "+a.progress.toFixed(2)+"%";this.progressBar.updateProgress(a.progress/100,f)}});
/*
 * Deluge.add.Window.js
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
Ext.ns("Deluge.add");Deluge.add.Window=Ext.extend(Ext.Window,{initComponent:function(){Deluge.add.Window.superclass.initComponent.call(this);this.addEvents("beforeadd","add","addfailed")},createTorrentId:function(){return new Date().getTime()}});
/*
 * Deluge.add.AddWindow.js
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
Ext.namespace("Deluge.add");Deluge.add.AddWindow=Ext.extend(Deluge.add.Window,{title:_("Add Torrents"),layout:"border",width:470,height:450,bodyStyle:"padding: 10px 5px;",buttonAlign:"right",closeAction:"hide",closable:true,plain:true,iconCls:"x-deluge-add-window-icon",initComponent:function(){Deluge.add.AddWindow.superclass.initComponent.call(this);this.addButton(_("Cancel"),this.onCancelClick,this);this.addButton(_("Add"),this.onAddClick,this);function a(c,d,b){if(b.data.info_hash){return String.format('<div class="x-deluge-add-torrent-name">{0}</div>',c)}else{return String.format('<div class="x-deluge-add-torrent-name-loading">{0}</div>',c)}}this.list=new Ext.list.ListView({store:new Ext.data.SimpleStore({fields:[{name:"info_hash",mapping:1},{name:"text",mapping:2}],id:0}),columns:[{id:"torrent",width:150,sortable:true,renderer:a,dataIndex:"text"}],stripeRows:true,singleSelect:true,listeners:{selectionchange:{fn:this.onSelect,scope:this}},hideHeaders:true,autoExpandColumn:"torrent",height:"100%",autoScroll:true});this.add({region:"center",items:[this.list],margins:"5 5 5 5",bbar:new Ext.Toolbar({items:[{iconCls:"x-deluge-add-file",text:_("File"),handler:this.onFile,scope:this},{text:_("Url"),iconCls:"icon-add-url",handler:this.onUrl,scope:this},{text:_("Infohash"),iconCls:"icon-add-magnet",hidden:true,disabled:true},"->",{text:_("Remove"),iconCls:"icon-remove",handler:this.onRemove,scope:this}]})});this.optionsPanel=this.add(new Deluge.add.OptionsPanel());this.on("hide",this.onHide,this);this.on("show",this.onShow,this)},clear:function(){this.list.getStore().removeAll();this.optionsPanel.clear()},onAddClick:function(){var a=[];if(!this.list){return}this.list.getStore().each(function(b){var c=b.get("info_hash");a.push({path:this.optionsPanel.getFilename(c),options:this.optionsPanel.getOptions(c)})},this);deluge.client.web.add_torrents(a,{success:function(b){}});this.clear();this.hide()},onCancelClick:function(){this.clear();this.hide()},onFile:function(){if(!this.file){this.file=new Deluge.add.FileWindow()}this.file.show()},onHide:function(){this.optionsPanel.setActiveTab(0);this.optionsPanel.files.setDisabled(true);this.optionsPanel.form.setDisabled(true)},onRemove:function(){if(!this.list.getSelectionCount()){return}var a=this.list.getSelectedRecords()[0];this.list.getStore().remove(a);this.optionsPanel.clear();if(this.torrents&&this.torrents[a.id]){delete this.torrents[a.id]}},onSelect:function(c,b){if(b.length){var a=this.list.getRecord(b[0]);this.optionsPanel.setTorrent(a.get("info_hash"))}else{this.optionsPanel.files.setDisabled(true);this.optionsPanel.form.setDisabled(true)}},onShow:function(){if(!this.url){this.url=new Deluge.add.UrlWindow();this.url.on("beforeadd",this.onTorrentBeforeAdd,this);this.url.on("add",this.onTorrentAdd,this);this.url.on("addfailed",this.onTorrentAddFailed,this)}if(!this.file){this.file=new Deluge.add.FileWindow();this.file.on("beforeadd",this.onTorrentBeforeAdd,this);this.file.on("add",this.onTorrentAdd,this);this.file.on("addfailed",this.onTorrentAddFailed,this)}this.optionsPanel.form.getDefaults()},onTorrentBeforeAdd:function(b,c){var a=this.list.getStore();a.loadData([[b,null,c]],true)},onTorrentAdd:function(a,c){var b=this.list.getStore().getById(a);if(!c){Ext.MessageBox.show({title:_("Error"),msg:_("Not a valid torrent"),buttons:Ext.MessageBox.OK,modal:false,icon:Ext.MessageBox.ERROR,iconCls:"x-deluge-icon-error"});this.list.getStore().remove(b)}else{b.set("info_hash",c.info_hash);b.set("text",c.name);this.list.getStore().commitChanges();this.optionsPanel.addTorrent(c);this.list.select(b)}},onTorrentAddFailed:function(c){var b=this.list.getStore();var a=b.getById(c);if(a){b.remove(a)}},onUrl:function(a,b){this.url.show()}});
/*
 * Deluge.add.File.js
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
Ext.ns("Deluge.add");Deluge.add.FileWindow=Ext.extend(Deluge.add.Window,{title:_("Add from File"),layout:"fit",width:350,height:115,modal:true,plain:true,buttonAlign:"center",closeAction:"hide",bodyStyle:"padding: 10px 5px;",iconCls:"x-deluge-add-file",initComponent:function(){Deluge.add.FileWindow.superclass.initComponent.call(this);this.addButton(_("Add"),this.onAddClick,this);this.form=this.add({xtype:"form",baseCls:"x-plain",labelWidth:35,autoHeight:true,fileUpload:true,items:[{xtype:"fileuploadfield",id:"torrentFile",width:280,height:24,emptyText:_("Select a torrent"),fieldLabel:_("File"),name:"file",buttonCfg:{text:_("Browse")+"..."}}]})},onAddClick:function(c,b){if(this.form.getForm().isValid()){this.torrentId=this.createTorrentId();this.form.getForm().submit({url:deluge.config.base+"upload",waitMsg:_("Uploading your torrent..."),failure:this.onUploadFailure,success:this.onUploadSuccess,scope:this});var a=this.form.getForm().findField("torrentFile").value;a=a.split("\\").slice(-1)[0];this.fireEvent("beforeadd",this.torrentId,a)}},onGotInfo:function(d,c,a,b){d.filename=b.options.filename;this.fireEvent("add",this.torrentId,d)},onUploadFailure:function(a,b){this.hide();Ext.MessageBox.show({title:_("Error"),msg:_("Failed to upload torrent"),buttons:Ext.MessageBox.OK,modal:false,icon:Ext.MessageBox.ERROR,iconCls:"x-deluge-icon-error"});this.fireEvent("addfailed",this.torrentId)},onUploadSuccess:function(c,b){this.hide();if(b.result.success){var a=b.result.files[0];this.form.getForm().findField("torrentFile").setValue("");deluge.client.web.get_torrent_info(a,{success:this.onGotInfo,scope:this,filename:a})}}});
/*
 * Deluge.add.FilesTab.js
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
Ext.ns("Deluge.add");Deluge.add.FilesTab=Ext.extend(Ext.ux.tree.TreeGrid,{layout:"fit",title:_("Files"),autoScroll:false,animate:false,border:false,disabled:true,rootVisible:false,columns:[{header:_("Filename"),width:295,dataIndex:"filename"},{header:_("Size"),width:60,dataIndex:"size",tpl:new Ext.XTemplate("{size:this.fsize}",{fsize:function(a){return fsize(a)}})},{header:_("Download"),width:65,dataIndex:"download",tpl:new Ext.XTemplate("{download:this.format}",{format:function(a){return'<div rel="chkbox" class="x-grid3-check-col'+(a?"-on":"")+'"> </div>'}})}],initComponent:function(){Deluge.add.FilesTab.superclass.initComponent.call(this);this.on("click",this.onNodeClick,this)},clearFiles:function(){var a=this.getRootNode();if(!a.hasChildNodes()){return}a.cascade(function(b){if(!b.parentNode||!b.getOwnerTree()){return}b.remove()})},setDownload:function(b,c,d){b.attributes.download=c;b.ui.updateColumns();if(b.isLeaf()){if(!d){return this.fireEvent("fileschecked",[b],c,!c)}}else{var a=[b];b.cascade(function(e){e.attributes.download=c;e.ui.updateColumns();a.push(e)},this);if(!d){return this.fireEvent("fileschecked",a,c,!c)}}},onNodeClick:function(b,c){var a=new Ext.Element(c.target);if(a.getAttribute("rel")=="chkbox"){this.setDownload(b,!b.attributes.download)}}});
/*
 * Deluge.add.Infohash.js
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
Ext.namespace("Ext.deluge.add");
/*
 * Deluge.add.OptionsPanel.js
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
Ext.ns("Deluge.add");Deluge.add.OptionsPanel=Ext.extend(Ext.TabPanel,{torrents:{},region:"south",margins:"5 5 5 5",activeTab:0,height:265,initComponent:function(){Deluge.add.OptionsPanel.superclass.initComponent.call(this);this.files=this.add(new Deluge.add.FilesTab());this.form=this.add(new Deluge.add.OptionsTab());this.files.on("fileschecked",this.onFilesChecked,this)},addTorrent:function(c){this.torrents[c.info_hash]=c;var b={};this.walkFileTree(c.files_tree,function(e,g,h,f){if(g!="file"){return}b[h.index]=h.download},this);var a=[];Ext.each(Ext.keys(b),function(e){a[e]=b[e]});var d=this.form.optionsManager.changeId(c.info_hash,true);this.form.optionsManager.setDefault("file_priorities",a);this.form.optionsManager.changeId(d,true)},clear:function(){this.files.clearFiles();this.form.optionsManager.resetAll()},getFilename:function(a){return this.torrents[a]["filename"]},getOptions:function(a){var c=this.form.optionsManager.changeId(a,true);var b=this.form.optionsManager.get();this.form.optionsManager.changeId(c,true);Ext.each(b.file_priorities,function(e,d){b.file_priorities[d]=(e)?1:0});return b},setTorrent:function(b){if(!b){return}this.torrentId=b;this.form.optionsManager.changeId(b);this.files.clearFiles();var a=this.files.getRootNode();var c=this.form.optionsManager.get("file_priorities");this.form.setDisabled(false);if(this.torrents[b]["files_tree"]){this.walkFileTree(this.torrents[b]["files_tree"],function(e,f,h,d){var g=new Ext.tree.TreeNode({download:(h.index)?c[h.index]:true,filename:e,fileindex:h.index,leaf:f!="dir",size:h.length});d.appendChild(g);if(f=="dir"){return g}},this,a);a.firstChild.expand();this.files.setDisabled(false);this.files.show()}else{this.form.show();this.files.setDisabled(true)}},walkFileTree:function(g,h,e,a){for(var b in g.contents){var f=g.contents[b];var d=f.type;if(e){var c=h.apply(e,[b,d,f,a])}else{var c=h(b,d,f,a)}if(d=="dir"){this.walkFileTree(f,h,e,c)}}},onFilesChecked:function(a,c,b){if(this.form.optionsManager.get("compact_allocation")){Ext.Msg.show({title:_("Unable to set file priority!"),msg:_("File prioritization is unavailable when using Compact allocation. Would you like to switch to Full allocation?"),buttons:Ext.Msg.YESNO,fn:function(d){if(d=="yes"){this.form.optionsManager.update("compact_allocation",false);Ext.each(a,function(f){if(f.attributes.fileindex<0){return}var e=this.form.optionsManager.get("file_priorities");e[f.attributes.fileindex]=c;this.form.optionsManager.update("file_priorities",e)},this)}else{this.files.setDownload(a[0],b,true)}},scope:this,icon:Ext.MessageBox.QUESTION})}else{Ext.each(a,function(e){if(e.attributes.fileindex<0){return}var d=this.form.optionsManager.get("file_priorities");d[e.attributes.fileindex]=c;this.form.optionsManager.update("file_priorities",d)},this)}}});
/*
 * Deluge.add.OptionsPanel.js
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
Ext.ns("Deluge.add");Deluge.add.OptionsTab=Ext.extend(Ext.form.FormPanel,{title:_("Options"),height:170,border:false,bodyStyle:"padding: 5px",disabled:true,labelWidth:1,initComponent:function(){Deluge.add.OptionsTab.superclass.initComponent.call(this);this.optionsManager=new Deluge.MultiOptionsManager();var a=this.add({xtype:"fieldset",title:_("Download Location"),border:false,autoHeight:true,defaultType:"textfield",labelWidth:1,fieldLabel:"",style:"padding-bottom: 5px; margin-bottom: 0px;"});this.optionsManager.bind("download_location",a.add({fieldLabel:"",name:"download_location",width:400,labelSeparator:""}));var a=this.add({xtype:"fieldset",title:_("Move Completed Location"),border:false,autoHeight:true,defaultType:"togglefield",labelWidth:1,fieldLabel:"",style:"padding-bottom: 5px; margin-bottom: 0px;"});var c=a.add({fieldLabel:"",name:"move_completed_path",width:425});this.optionsManager.bind("move_completed",c.toggle);this.optionsManager.bind("move_completed_path",c.input);var b=this.add({border:false,layout:"column",defaultType:"fieldset"});a=b.add({title:_("Allocation"),border:false,autoHeight:true,defaultType:"radio"});this.optionsManager.bind("compact_allocation",a.add({xtype:"radiogroup",columns:1,vertical:true,labelSeparator:"",width:80,items:[{name:"compact_allocation",value:false,inputValue:false,boxLabel:_("Full"),fieldLabel:"",labelSeparator:""},{name:"compact_allocation",value:true,inputValue:true,boxLabel:_("Compact"),fieldLabel:"",labelSeparator:""}]}));a=b.add({title:_("Bandwidth"),border:false,autoHeight:true,bodyStyle:"margin-left: 7px",labelWidth:105,width:200,defaultType:"spinnerfield"});this.optionsManager.bind("max_download_speed",a.add({fieldLabel:_("Max Down Speed"),name:"max_download_speed",width:60}));this.optionsManager.bind("max_upload_speed",a.add({fieldLabel:_("Max Up Speed"),name:"max_upload_speed",width:60}));this.optionsManager.bind("max_connections",a.add({fieldLabel:_("Max Connections"),name:"max_connections",width:60}));this.optionsManager.bind("max_upload_slots",a.add({fieldLabel:_("Max Upload Slots"),name:"max_upload_slots",width:60}));a=b.add({title:_("General"),border:false,autoHeight:true,defaultType:"checkbox"});this.optionsManager.bind("add_paused",a.add({name:"add_paused",boxLabel:_("Add In Paused State"),fieldLabel:"",labelSeparator:""}));this.optionsManager.bind("prioritize_first_last_pieces",a.add({name:"prioritize_first_last_pieces",boxLabel:_("Prioritize First/Last Pieces"),fieldLabel:"",labelSeparator:""}))},getDefaults:function(){var a=["add_paused","compact_allocation","download_location","max_connections_per_torrent","max_download_speed_per_torrent","move_completed","move_completed_path","max_upload_slots_per_torrent","max_upload_speed_per_torrent","prioritize_first_last_pieces"];deluge.client.core.get_config_values(a,{success:function(c){var b={file_priorities:[],add_paused:c.add_paused,compact_allocation:c.compact_allocation,download_location:c.download_location,move_completed:c.move_completed,move_completed_path:c.move_completed_path,max_connections:c.max_connections_per_torrent,max_download_speed:c.max_download_speed_per_torrent,max_upload_slots:c.max_upload_slots_per_torrent,max_upload_speed:c.max_upload_speed_per_torrent,prioritize_first_last_pieces:c.prioritize_first_last_pieces};this.optionsManager.options=b;this.optionsManager.resetAll()},scope:this})}});
/*
 * Deluge.add.UrlWindow.js
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
Ext.namespace("Deluge.add");Deluge.add.UrlWindow=Ext.extend(Deluge.add.Window,{title:_("Add from Url"),modal:true,plain:true,layout:"fit",width:350,height:155,buttonAlign:"center",closeAction:"hide",bodyStyle:"padding: 10px 5px;",iconCls:"x-deluge-add-url-window-icon",initComponent:function(){Deluge.add.UrlWindow.superclass.initComponent.call(this);this.addButton(_("Add"),this.onAddClick,this);var a=this.add({xtype:"form",defaultType:"textfield",baseCls:"x-plain",labelWidth:55});this.urlField=a.add({fieldLabel:_("Url"),id:"url",name:"url",width:"97%"});this.urlField.on("specialkey",this.onAdd,this);this.cookieField=a.add({fieldLabel:_("Cookies"),id:"cookies",name:"cookies",width:"97%"});this.cookieField.on("specialkey",this.onAdd,this)},onAddClick:function(f,d){if((f.id=="url"||f.id=="cookies")&&d.getKey()!=d.ENTER){return}var f=this.urlField;var b=f.getValue();var c=this.cookieField.getValue();var a=this.createTorrentId();if(b.indexOf("magnet:?")==0&&b.indexOf("xt=urn:btih")>-1){deluge.client.web.get_magnet_info(b,{success:this.onGotInfo,scope:this,filename:b,torrentId:a})}else{deluge.client.web.download_torrent_from_url(b,c,{success:this.onDownload,failure:this.onDownloadFailed,scope:this,torrentId:a})}this.hide();this.urlField.setValue("");this.fireEvent("beforeadd",a,b)},onDownload:function(a,c,d,b){deluge.client.web.get_torrent_info(a,{success:this.onGotInfo,scope:this,filename:a,torrentId:b.options.torrentId})},onDownloadFailed:function(b,c,a){Ext.MessageBox.show({title:_("Error"),msg:_("Failed to download torrent"),buttons:Ext.MessageBox.OK,modal:false,icon:Ext.MessageBox.ERROR,iconCls:"x-deluge-icon-error"});this.fireEvent("addfailed",a.options.torrentId)},onGotInfo:function(d,c,a,b){d.filename=b.options.filename;this.fireEvent("add",b.options.torrentId,d)}});
/*
 * Deluge.preferences.BandwidthPage.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.Bandwidth=Ext.extend(Ext.form.FormPanel,{constructor:function(a){a=Ext.apply({border:false,title:_("Bandwidth"),layout:"form",labelWidth:10},a);Deluge.preferences.Bandwidth.superclass.constructor.call(this,a)},initComponent:function(){Deluge.preferences.Bandwidth.superclass.initComponent.call(this);var b=deluge.preferences.getOptionsManager();var a=this.add({xtype:"fieldset",border:false,title:_("Global Bandwidth Usage"),labelWidth:200,defaultType:"spinnerfield",defaults:{minValue:-1,maxValue:99999},style:"margin-bottom: 0px; padding-bottom: 0px;",autoHeight:true});b.bind("max_connections_global",a.add({name:"max_connections_global",fieldLabel:_("Maximum Connections"),width:80,value:-1,decimalPrecision:0}));b.bind("max_upload_slots_global",a.add({name:"max_upload_slots_global",fieldLabel:_("Maximum Upload Slots"),width:80,value:-1,decimalPrecision:0}));b.bind("max_download_speed",a.add({name:"max_download_speed",fieldLabel:_("Maximum Download Speed (KiB/s)"),width:80,value:-1,decimalPrecision:1}));b.bind("max_upload_speed",a.add({name:"max_upload_speed",fieldLabel:_("Maximum Upload Speed (KiB/s)"),width:80,value:-1,decimalPrecision:1}));b.bind("max_half_open_connections",a.add({name:"max_half_open_connections",fieldLabel:_("Maximum Half-Open Connections"),width:80,value:-1,decimalPrecision:0}));b.bind("max_connections_per_second",a.add({name:"max_connections_per_second",fieldLabel:_("Maximum Connection Attempts per Second"),width:80,value:-1,decimalPrecision:0}));a=this.add({xtype:"fieldset",border:false,title:"",defaultType:"checkbox",style:"padding-top: 0px; padding-bottom: 5px; margin-top: 0px; margin-bottom: 0px;",autoHeight:true});b.bind("ignore_limits_on_local_network",a.add({name:"ignore_limits_on_local_network",height:22,fieldLabel:"",labelSeparator:"",boxLabel:_("Ignore limits on local network")}));b.bind("rate_limit_ip_overhead",a.add({name:"rate_limit_ip_overhead",height:22,fieldLabel:"",labelSeparator:"",boxLabel:_("Rate limit IP overhead")}));a=this.add({xtype:"fieldset",border:false,title:_("Per Torrent Bandwidth Usage"),style:"margin-bottom: 0px; padding-bottom: 0px;",defaultType:"spinnerfield",labelWidth:200,defaults:{minValue:-1,maxValue:99999},autoHeight:true});b.bind("max_connections_per_torrent",a.add({name:"max_connections_per_torrent",fieldLabel:_("Maximum Connections"),width:80,value:-1,decimalPrecision:0}));b.bind("max_upload_slots_per_torrent",a.add({name:"max_upload_slots_per_torrent",fieldLabel:_("Maximum Upload Slots"),width:80,value:-1,decimalPrecision:0}));b.bind("max_download_speed_per_torrent",a.add({name:"max_download_speed_per_torrent",fieldLabel:_("Maximum Download Speed (KiB/s)"),width:80,value:-1,decimalPrecision:0}));b.bind("max_upload_speed_per_torrent",a.add({name:"max_upload_speed_per_torrent",fieldLabel:_("Maximum Upload Speed (KiB/s)"),width:80,value:-1,decimalPrecision:0}))}});
/*
 * Deluge.preferences.CachePage.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.Cache=Ext.extend(Ext.form.FormPanel,{border:false,title:_("Cache"),layout:"form",initComponent:function(){Deluge.preferences.Cache.superclass.initComponent.call(this);var b=deluge.preferences.getOptionsManager();var a=this.add({xtype:"fieldset",border:false,title:_("Settings"),autoHeight:true,labelWidth:180,defaultType:"spinnerfield",defaults:{decimalPrecision:0,minValue:-1,maxValue:999999}});b.bind("cache_size",a.add({fieldLabel:_("Cache Size (16 KiB Blocks)"),name:"cache_size",width:60,value:512}));b.bind("cache_expiry",a.add({fieldLabel:_("Cache Expiry (seconds)"),name:"cache_expiry",width:60,value:60}))}});
/*
 * Deluge.preferences.DaemonPage.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.Daemon=Ext.extend(Ext.form.FormPanel,{border:false,title:_("Daemon"),layout:"form",initComponent:function(){Deluge.preferences.Daemon.superclass.initComponent.call(this);var b=deluge.preferences.getOptionsManager();var a=this.add({xtype:"fieldset",border:false,title:_("Port"),autoHeight:true,defaultType:"spinnerfield"});b.bind("daemon_port",a.add({fieldLabel:_("Daemon port"),name:"daemon_port",value:58846,decimalPrecision:0,minValue:-1,maxValue:99999}));a=this.add({xtype:"fieldset",border:false,title:_("Connections"),autoHeight:true,labelWidth:1,defaultType:"checkbox"});b.bind("allow_remote",a.add({fieldLabel:"",height:22,labelSeparator:"",boxLabel:_("Allow Remote Connections"),name:"allow_remote"}));a=this.add({xtype:"fieldset",border:false,title:_("Other"),autoHeight:true,labelWidth:1,defaultType:"checkbox"});b.bind("new_release_check",a.add({fieldLabel:"",labelSeparator:"",height:40,boxLabel:_("Periodically check the website for new releases"),id:"new_release_check"}))}});
/*
 * Deluge.preferences.DownloadsPage.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.Downloads=Ext.extend(Ext.FormPanel,{constructor:function(a){a=Ext.apply({border:false,title:_("Downloads"),layout:"form",autoHeight:true,width:320},a);Deluge.preferences.Downloads.superclass.constructor.call(this,a)},initComponent:function(){Deluge.preferences.Downloads.superclass.initComponent.call(this);var b=deluge.preferences.getOptionsManager();var a=this.add({xtype:"fieldset",border:false,title:_("Folders"),labelWidth:150,defaultType:"togglefield",autoHeight:true,labelAlign:"top",width:300,style:"margin-bottom: 5px; padding-bottom: 5px;"});b.bind("download_location",a.add({xtype:"textfield",name:"download_location",fieldLabel:_("Download to"),width:280}));var c=a.add({name:"move_completed_path",fieldLabel:_("Move completed to"),width:280});b.bind("move_completed",c.toggle);b.bind("move_completed_path",c.input);c=a.add({name:"torrentfiles_location",fieldLabel:_("Copy of .torrent files to"),width:280});b.bind("copy_torrent_file",c.toggle);b.bind("torrentfiles_location",c.input);c=a.add({name:"autoadd_location",fieldLabel:_("Autoadd .torrent files from"),width:280});b.bind("autoadd_enable",c.toggle);b.bind("autoadd_location",c.input);a=this.add({xtype:"fieldset",border:false,title:_("Allocation"),autoHeight:true,labelWidth:1,defaultType:"radiogroup",style:"margin-bottom: 5px; margin-top: 0; padding-bottom: 5px; padding-top: 0;",width:240});b.bind("compact_allocation",a.add({name:"compact_allocation",width:200,labelSeparator:"",defaults:{width:80,height:22,name:"compact_allocation"},items:[{boxLabel:_("Use Full"),inputValue:false},{boxLabel:_("Use Compact"),inputValue:true}]}));a=this.add({xtype:"fieldset",border:false,title:_("Options"),autoHeight:true,labelWidth:1,defaultType:"checkbox",style:"margin-bottom: 0; padding-bottom: 0;",width:280});b.bind("prioritize_first_last_pieces",a.add({name:"prioritize_first_last_pieces",labelSeparator:"",height:22,boxLabel:_("Prioritize first and last pieces of torrent")}));b.bind("add_paused",a.add({name:"add_paused",labelSeparator:"",height:22,boxLabel:_("Add torrents in Paused state")}))}});
/*
 * Deluge.preferences.EncryptionPage.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.Encryption=Ext.extend(Ext.form.FormPanel,{border:false,title:_("Encryption"),initComponent:function(){Deluge.preferences.Encryption.superclass.initComponent.call(this);var b=deluge.preferences.getOptionsManager();var a=this.add({xtype:"fieldset",border:false,title:_("Settings"),autoHeight:true,defaultType:"combo",width:300});b.bind("enc_in_policy",a.add({fieldLabel:_("Inbound"),mode:"local",width:150,store:new Ext.data.ArrayStore({fields:["id","text"],data:[[0,_("Forced")],[1,_("Enabled")],[2,_("Disabled")]]}),editable:false,triggerAction:"all",valueField:"id",displayField:"text"}));b.bind("enc_out_policy",a.add({fieldLabel:_("Outbound"),mode:"local",width:150,store:new Ext.data.SimpleStore({fields:["id","text"],data:[[0,_("Forced")],[1,_("Enabled")],[2,_("Disabled")]]}),editable:false,triggerAction:"all",valueField:"id",displayField:"text"}));b.bind("enc_level",a.add({fieldLabel:_("Level"),mode:"local",width:150,store:new Ext.data.SimpleStore({fields:["id","text"],data:[[0,_("Handshake")],[1,_("Full Stream")],[2,_("Either")]]}),editable:false,triggerAction:"all",valueField:"id",displayField:"text"}));b.bind("enc_prefer_rc4",a.add({xtype:"checkbox",name:"enc_prefer_rc4",height:40,hideLabel:true,boxLabel:_("Encrypt entire stream")}))}});
/*
 * Deluge.preferences.InstallPluginWindow.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.InstallPluginWindow=Ext.extend(Ext.Window,{title:_("Install Plugin"),layout:"fit",height:115,width:350,bodyStyle:"padding: 10px 5px;",buttonAlign:"center",closeAction:"hide",iconCls:"x-deluge-install-plugin",modal:true,plain:true,initComponent:function(){Deluge.add.FileWindow.superclass.initComponent.call(this);this.addButton(_("Install"),this.onInstall,this);this.form=this.add({xtype:"form",baseCls:"x-plain",labelWidth:70,autoHeight:true,fileUpload:true,items:[{xtype:"fileuploadfield",width:240,emptyText:_("Select an egg"),fieldLabel:_("Plugin Egg"),name:"file",buttonCfg:{text:_("Browse")+"..."}}]})},onInstall:function(b,a){this.form.getForm().submit({url:deluge.config.base+"upload",waitMsg:_("Uploading your plugin..."),success:this.onUploadSuccess,scope:this})},onUploadPlugin:function(d,c,a,b){this.fireEvent("pluginadded")},onUploadSuccess:function(c,b){this.hide();if(b.result.success){var a=this.form.getForm().getFieldValues().file;a=a.split("\\").slice(-1)[0];var d=b.result.files[0];this.form.getForm().setValues({file:""});deluge.client.web.upload_plugin(a,d,{success:this.onUploadPlugin,scope:this,filename:a})}}});
/*
 * Deluge.preferences.InterfacePage.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.Interface=Ext.extend(Ext.form.FormPanel,{border:false,title:_("Interface"),layout:"form",initComponent:function(){Deluge.preferences.Interface.superclass.initComponent.call(this);var c=this.optionsManager=new Deluge.OptionsManager();this.on("show",this.onPageShow,this);var a=this.add({xtype:"fieldset",border:false,title:_("Interface"),style:"margin-bottom: 0px; padding-bottom: 5px; padding-top: 5px",autoHeight:true,labelWidth:1,defaultType:"checkbox"});c.bind("show_session_speed",a.add({name:"show_session_speed",height:22,fieldLabel:"",labelSeparator:"",boxLabel:_("Show session speed in titlebar")}));c.bind("sidebar_show_zero",a.add({name:"sidebar_show_zero",height:22,fieldLabel:"",labelSeparator:"",boxLabel:_("Show filters with zero torrents")}));c.bind("sidebar_multiple_filters",a.add({name:"sidebar_multiple_filters",height:22,fieldLabel:"",labelSeparator:"",boxLabel:_("Allow the use of multiple filters at once")}));a=this.add({xtype:"fieldset",border:false,title:_("Password"),style:"margin-bottom: 0px; padding-bottom: 0px; padding-top: 5px",autoHeight:true,labelWidth:110,defaultType:"textfield",defaults:{width:180,inputType:"password"}});this.oldPassword=a.add({name:"old_password",fieldLabel:_("Old Password")});this.newPassword=a.add({name:"new_password",fieldLabel:_("New Password")});this.confirmPassword=a.add({name:"confirm_password",fieldLabel:_("Confirm Password")});var b=a.add({xtype:"panel",autoHeight:true,border:false,width:320,bodyStyle:"padding-left: 230px"});b.add({xtype:"button",text:_("Change"),listeners:{click:{fn:this.onPasswordChange,scope:this}}});a=this.add({xtype:"fieldset",border:false,title:_("Server"),style:"margin-top: 0px; padding-top: 0px; margin-bottom: 0px; padding-bottom: 0px",autoHeight:true,labelWidth:110,defaultType:"spinnerfield",defaults:{width:80}});c.bind("session_timeout",a.add({name:"session_timeout",fieldLabel:_("Session Timeout"),decimalPrecision:0,minValue:-1,maxValue:99999}));c.bind("port",a.add({name:"port",fieldLabel:_("Port"),decimalPrecision:0,minValue:-1,maxValue:99999}));this.httpsField=c.bind("https",a.add({xtype:"checkbox",name:"https",hideLabel:true,width:280,height:22,boxLabel:_("Use SSL (paths relative to Deluge config folder)")}));this.httpsField.on("check",this.onSSLCheck,this);this.pkeyField=c.bind("pkey",a.add({xtype:"textfield",disabled:true,name:"pkey",width:180,fieldLabel:_("Private Key")}));this.certField=c.bind("cert",a.add({xtype:"textfield",disabled:true,name:"cert",width:180,fieldLabel:_("Certificate")}))},onApply:function(){var b=this.optionsManager.getDirty();if(!Ext.isObjectEmpty(b)){deluge.client.web.set_config(b,{success:this.onSetConfig,scope:this});for(var a in deluge.config){deluge.config[a]=this.optionsManager.get(a)}}},onGotConfig:function(a){this.optionsManager.set(a)},onPasswordChange:function(){var b=this.newPassword.getValue();if(b!=this.confirmPassword.getValue()){Ext.MessageBox.show({title:_("Invalid Password"),msg:_("Your passwords don't match!"),buttons:Ext.MessageBox.OK,modal:false,icon:Ext.MessageBox.ERROR,iconCls:"x-deluge-icon-error"});return}var a=this.oldPassword.getValue();deluge.client.auth.change_password(a,b,{success:function(c){if(!c){Ext.MessageBox.show({title:_("Password"),msg:_("Your old password was incorrect!"),buttons:Ext.MessageBox.OK,modal:false,icon:Ext.MessageBox.ERROR,iconCls:"x-deluge-icon-error"});this.oldPassword.setValue("")}else{Ext.MessageBox.show({title:_("Change Successful"),msg:_("Your password was successfully changed!"),buttons:Ext.MessageBox.OK,modal:false,icon:Ext.MessageBox.INFO,iconCls:"x-deluge-icon-info"});this.oldPassword.setValue("");this.newPassword.setValue("");this.confirmPassword.setValue("")}},scope:this})},onSetConfig:function(){this.optionsManager.commit()},onPageShow:function(){deluge.client.web.get_config({success:this.onGotConfig,scope:this})},onSSLCheck:function(b,a){this.pkeyField.setDisabled(!a);this.certField.setDisabled(!a)}});
/*
 * Deluge.preferences.NetworkPage.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.Network=Ext.extend(Ext.form.FormPanel,{border:false,layout:"form",title:_("Network"),initComponent:function(){Deluge.preferences.Network.superclass.initComponent.call(this);var b=deluge.preferences.getOptionsManager();var a=this.add({xtype:"fieldset",border:false,title:_("Incoming Ports"),style:"margin-bottom: 5px; padding-bottom: 0px;",autoHeight:true,labelWidth:1,defaultType:"checkbox"});b.bind("random_port",a.add({fieldLabel:"",labelSeparator:"",boxLabel:_("Use Random Ports"),name:"random_port",height:22,listeners:{check:{fn:function(d,c){this.listenPorts.setDisabled(c)},scope:this}}}));this.listenPorts=a.add({xtype:"spinnergroup",name:"listen_ports",fieldLabel:"",labelSeparator:"",colCfg:{labelWidth:40,style:"margin-right: 10px;"},items:[{fieldLabel:"From",strategy:{xtype:"number",decimalPrecision:0,minValue:-1,maxValue:99999}},{fieldLabel:"To",strategy:{xtype:"number",decimalPrecision:0,minValue:-1,maxValue:99999}}]});b.bind("listen_ports",this.listenPorts);a=this.add({xtype:"fieldset",border:false,title:_("Outgoing Ports"),style:"margin-bottom: 5px; padding-bottom: 0px;",autoHeight:true,labelWidth:1,defaultType:"checkbox"});b.bind("random_outgoing_ports",a.add({fieldLabel:"",labelSeparator:"",boxLabel:_("Use Random Ports"),name:"random_outgoing_ports",height:22,listeners:{check:{fn:function(d,c){this.outgoingPorts.setDisabled(c)},scope:this}}}));this.outgoingPorts=a.add({xtype:"spinnergroup",name:"outgoing_ports",fieldLabel:"",labelSeparator:"",colCfg:{labelWidth:40,style:"margin-right: 10px;"},items:[{fieldLabel:"From",strategy:{xtype:"number",decimalPrecision:0,minValue:-1,maxValue:99999}},{fieldLabel:"To",strategy:{xtype:"number",decimalPrecision:0,minValue:-1,maxValue:99999}}]});b.bind("outgoing_ports",this.outgoingPorts);a=this.add({xtype:"fieldset",border:false,title:_("Network Interface"),style:"margin-bottom: 5px; padding-bottom: 0px;",autoHeight:true,labelWidth:1,defaultType:"textfield"});b.bind("listen_interface",a.add({name:"listen_interface",fieldLabel:"",labelSeparator:"",width:200}));a=this.add({xtype:"fieldset",border:false,title:_("TOS"),style:"margin-bottom: 5px; padding-bottom: 0px;",bodyStyle:"margin: 0px; padding: 0px",autoHeight:true,defaultType:"textfield"});b.bind("peer_tos",a.add({name:"peer_tos",fieldLabel:_("Peer TOS Byte"),width:80}));a=this.add({xtype:"fieldset",border:false,title:_("Network Extras"),autoHeight:true,layout:"table",layoutConfig:{columns:3},defaultType:"checkbox"});b.bind("upnp",a.add({fieldLabel:"",labelSeparator:"",boxLabel:_("UPnP"),name:"upnp"}));b.bind("natpmp",a.add({fieldLabel:"",labelSeparator:"",boxLabel:_("NAT-PMP"),ctCls:"x-deluge-indent-checkbox",name:"natpmp"}));b.bind("utpex",a.add({fieldLabel:"",labelSeparator:"",boxLabel:_("Peer Exchange"),ctCls:"x-deluge-indent-checkbox",name:"utpex"}));b.bind("lsd",a.add({fieldLabel:"",labelSeparator:"",boxLabel:_("LSD"),name:"lsd"}));b.bind("dht",a.add({fieldLabel:"",labelSeparator:"",boxLabel:_("DHT"),ctCls:"x-deluge-indent-checkbox",name:"dht"}))}});
/*
 * Deluge.preferences.OtherPage.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.Other=Ext.extend(Ext.form.FormPanel,{constructor:function(a){a=Ext.apply({border:false,title:_("Other"),layout:"form"},a);Deluge.preferences.Other.superclass.constructor.call(this,a)},initComponent:function(){Deluge.preferences.Other.superclass.initComponent.call(this);var b=deluge.preferences.getOptionsManager();var a=this.add({xtype:"fieldset",border:false,title:_("Updates"),autoHeight:true,labelWidth:1,defaultType:"checkbox"});b.bind("new_release_check",a.add({fieldLabel:"",labelSeparator:"",height:22,name:"new_release_check",boxLabel:_("Be alerted about new releases")}));a=this.add({xtype:"fieldset",border:false,title:_("System Information"),autoHeight:true,labelWidth:1,defaultType:"checkbox"});a.add({xtype:"panel",border:false,bodyCfg:{html:_("Help us improve Deluge by sending us your Python version, PyGTK version, OS and processor types. Absolutely no other information is sent.")}});b.bind("send_info",a.add({fieldLabel:"",labelSeparator:"",height:22,boxLabel:_("Yes, please send anonymous statistics"),name:"send_info"}));a=this.add({xtype:"fieldset",border:false,title:_("GeoIP Database"),autoHeight:true,labelWidth:80,defaultType:"textfield"});b.bind("geoip_db_location",a.add({name:"geoip_db_location",fieldLabel:_("Location"),width:200}))}});
/*
 * Deluge.preferences.PluginsPage.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.Plugins=Ext.extend(Ext.Panel,{layout:"border",title:_("Plugins"),border:false,height:400,cls:"x-deluge-plugins",pluginTemplate:new Ext.Template('<dl class="singleline"><dt>Author:</dt><dd>{author}</dd><dt>Version:</dt><dd>{version}</dd><dt>Author Email:</dt><dd>{email}</dd><dt>Homepage:</dt><dd>{homepage}</dd><dt>Details:</dt><dd>{details}</dd></dl>'),initComponent:function(){Deluge.preferences.Plugins.superclass.initComponent.call(this);this.defaultValues={version:"",email:"",homepage:"",details:""};this.pluginTemplate.compile();var c=function(e,f,d){f.css+=" x-grid3-check-col-td";return'<div class="x-grid3-check-col'+(e?"-on":"")+'"> </div>'};this.list=this.add({xtype:"listview",store:new Ext.data.ArrayStore({fields:[{name:"enabled",mapping:0},{name:"plugin",mapping:1}]}),columns:[{id:"enabled",header:_("Enabled"),width:0.2,sortable:true,tpl:new Ext.XTemplate("{enabled:this.getCheckbox}",{getCheckbox:function(d){return'<div class="x-grid3-check-col'+(d?"-on":"")+'" rel="chkbox"> </div>'}}),dataIndex:"enabled"},{id:"plugin",header:_("Plugin"),width:0.8,sortable:true,dataIndex:"plugin"}],singleSelect:true,autoExpandColumn:"plugin",listeners:{selectionchange:{fn:this.onPluginSelect,scope:this}}});this.panel=this.add({region:"center",autoScroll:true,margins:"5 5 5 5",items:[this.list],bbar:new Ext.Toolbar({items:[{cls:"x-btn-text-icon",iconCls:"x-deluge-install-plugin",text:_("Install"),handler:this.onInstallPluginWindow,scope:this},"->",{cls:"x-btn-text-icon",text:_("Find More"),iconCls:"x-deluge-find-more",handler:this.onFindMorePlugins,scope:this}]})});var b=this.pluginInfo=this.add({xtype:"panel",border:true,height:160,region:"south",margins:"0 5 5 5"});var a=b.add({xtype:"fieldset",title:_("Info"),border:false,autoHeight:true,labelWidth:1,style:"margin-top: 5px;"});this.pluginInfo=a.add({xtype:"panel",border:false,bodyCfg:{style:"margin-left: 10px"}});this.pluginInfo.on("render",this.onPluginInfoRender,this);this.list.on("click",this.onNodeClick,this);deluge.preferences.on("show",this.onPreferencesShow,this);deluge.events.on("PluginDisabledEvent",this.onPluginDisabled,this);deluge.events.on("PluginEnabledEvent",this.onPluginEnabled,this)},disablePlugin:function(a){deluge.client.core.disable_plugin(a)},enablePlugin:function(a){deluge.client.core.enable_plugin(a)},setInfo:function(b){if(!this.pluginInfo.rendered){return}var a=b||this.defaultValues;this.pluginInfo.body.dom.innerHTML=this.pluginTemplate.apply(a)},updatePlugins:function(){deluge.client.web.get_plugins({success:this.onGotPlugins,scope:this})},updatePluginsGrid:function(){var a=[];Ext.each(this.availablePlugins,function(b){if(this.enabledPlugins.indexOf(b)>-1){a.push([true,b])}else{a.push([false,b])}},this);this.list.getStore().loadData(a)},onNodeClick:function(b,a,f,g){var c=new Ext.Element(g.target);if(c.getAttribute("rel")!="chkbox"){return}var d=b.getStore().getAt(a);d.set("enabled",!d.get("enabled"));d.commit();if(d.get("enabled")){this.enablePlugin(d.get("plugin"))}else{this.disablePlugin(d.get("plugin"))}},onFindMorePlugins:function(){window.open("http://dev.deluge-torrent.org/wiki/Plugins")},onGotPlugins:function(a){this.enabledPlugins=a.enabled_plugins;this.availablePlugins=a.available_plugins;this.setInfo();this.updatePluginsGrid()},onGotPluginInfo:function(b){var a={author:b.Author,version:b.Version,email:b["Author-email"],homepage:b["Home-page"],details:b.Description};this.setInfo(a);delete b},onInstallPluginWindow:function(){if(!this.installWindow){this.installWindow=new Deluge.preferences.InstallPluginWindow();this.installWindow.on("pluginadded",this.onPluginInstall,this)}this.installWindow.show()},onPluginEnabled:function(c){var a=this.list.getStore().find("plugin",c);if(a==-1){return}var b=this.list.getStore().getAt(a);b.set("enabled",true);b.commit()},onPluginDisabled:function(c){var a=this.list.getStore().find("plugin",c);if(a==-1){return}var b=this.list.getStore().getAt(a);b.set("enabled",false);b.commit()},onPluginInstall:function(){this.updatePlugins()},onPluginSelect:function(a,b){if(b.length==0){return}var c=a.getRecords(b)[0];deluge.client.web.get_plugin_info(c.get("plugin"),{success:this.onGotPluginInfo,scope:this})},onPreferencesShow:function(){this.updatePlugins()},onPluginInfoRender:function(b,a){this.setInfo()}});
/*
 * Deluge.preferences.PreferencesWindow.js
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
Ext.namespace("Deluge.preferences");PreferencesRecord=Ext.data.Record.create([{name:"name",type:"string"}]);Deluge.preferences.PreferencesWindow=Ext.extend(Ext.Window,{currentPage:null,title:_("Preferences"),layout:"border",width:485,height:500,buttonAlign:"right",closeAction:"hide",closable:true,iconCls:"x-deluge-preferences",plain:true,resizable:false,pages:{},initComponent:function(){Deluge.preferences.PreferencesWindow.superclass.initComponent.call(this);this.list=new Ext.list.ListView({store:new Ext.data.Store(),columns:[{id:"name",renderer:fplain,dataIndex:"name"}],singleSelect:true,listeners:{selectionchange:{fn:this.onPageSelect,scope:this}},hideHeaders:true,autoExpandColumn:"name",deferredRender:false,autoScroll:true,collapsible:true});this.add({region:"west",title:_("Categories"),items:[this.list],width:120,margins:"5 0 5 5",cmargins:"5 0 5 5"});this.configPanel=this.add({type:"container",autoDestroy:false,region:"center",layout:"card",layoutConfig:{deferredRender:true},autoScroll:true,width:300,margins:"5 5 5 5",cmargins:"5 5 5 5"});this.addButton(_("Close"),this.onClose,this);this.addButton(_("Apply"),this.onApply,this);this.addButton(_("Ok"),this.onOk,this);this.optionsManager=new Deluge.OptionsManager();this.on("afterrender",this.onAfterRender,this);this.on("show",this.onShow,this);this.initPages()},initPages:function(){deluge.preferences=this;this.addPage(new Deluge.preferences.Downloads());this.addPage(new Deluge.preferences.Network());this.addPage(new Deluge.preferences.Encryption());this.addPage(new Deluge.preferences.Bandwidth());this.addPage(new Deluge.preferences.Interface());this.addPage(new Deluge.preferences.Other());this.addPage(new Deluge.preferences.Daemon());this.addPage(new Deluge.preferences.Queue());this.addPage(new Deluge.preferences.Proxy());this.addPage(new Deluge.preferences.Cache());this.addPage(new Deluge.preferences.Plugins())},onApply:function(b){var c=this.optionsManager.getDirty();if(!Ext.isObjectEmpty(c)){deluge.client.core.set_config(c,{success:this.onSetConfig,scope:this})}for(var a in this.pages){if(this.pages[a].onApply){this.pages[a].onApply()}}},getOptionsManager:function(){return this.optionsManager},addPage:function(c){var a=this.list.getStore();var b=c.title;a.add([new PreferencesRecord({name:b})]);c.bodyStyle="padding: 5px";c.preferences=this;this.pages[b]=this.configPanel.add(c);this.pages[b].index=-1;return this.pages[b]},removePage:function(c){var b=c.title;var a=this.list.getStore();a.removeAt(a.find("name",b));this.configPanel.remove(c);delete this.pages[c.title]},selectPage:function(a){if(this.pages[a].index<0){this.pages[a].index=this.configPanel.items.indexOf(this.pages[a])}this.list.select(this.pages[a].index)},doSelectPage:function(a){if(this.pages[a].index<0){this.pages[a].index=this.configPanel.items.indexOf(this.pages[a])}this.configPanel.getLayout().setActiveItem(this.pages[a].index);this.currentPage=a},onGotConfig:function(a){this.getOptionsManager().set(a)},onPageSelect:function(c,a){var b=c.getRecord(a[0]);this.doSelectPage(b.get("name"))},onSetConfig:function(){this.getOptionsManager().commit()},onAfterRender:function(){if(!this.list.getSelectionCount()){this.list.select(0)}this.configPanel.getLayout().setActiveItem(0)},onShow:function(){if(!deluge.client.core){return}deluge.client.core.get_config({success:this.onGotConfig,scope:this})},onClose:function(){this.hide()},onOk:function(){var b=this.optionsManager.getDirty();if(!Ext.isObjectEmpty(b)){deluge.client.core.set_config(b,{success:this.onSetConfig,scope:this})}for(var a in this.pages){if(this.pages[a].onOk){this.pages[a].onOk()}}this.hide()}});
/*
 * Deluge.preferences.ProxyField.js
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
 *	 The Free Software Foundation, Inc.,
 *	 51 Franklin Street, Fifth Floor
 *	 Boston, MA  02110-1301, USA.
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
Ext.ns("Deluge.preferences");Deluge.preferences.ProxyField=Ext.extend(Ext.form.FieldSet,{border:false,autoHeight:true,labelWidth:70,initComponent:function(){Deluge.preferences.ProxyField.superclass.initComponent.call(this);this.proxyType=this.add({xtype:"combo",fieldLabel:_("Type"),name:"proxytype",mode:"local",width:150,store:new Ext.data.ArrayStore({fields:["id","text"],data:[[0,_("None")],[1,_("Socksv4")],[2,_("Socksv5")],[3,_("Socksv5 with Auth")],[4,_("HTTP")],[5,_("HTTP with Auth")]]}),editable:false,triggerAction:"all",valueField:"id",displayField:"text"});this.proxyType.on("change",this.onFieldChange,this);this.proxyType.on("select",this.onTypeSelect,this);this.hostname=this.add({xtype:"textfield",name:"hostname",fieldLabel:_("Host"),width:220});this.hostname.on("change",this.onFieldChange,this);this.port=this.add({xtype:"spinnerfield",name:"port",fieldLabel:_("Port"),width:80,decimalPrecision:0,minValue:-1,maxValue:99999});this.port.on("change",this.onFieldChange,this);this.username=this.add({xtype:"textfield",name:"username",fieldLabel:_("Username"),width:220});this.username.on("change",this.onFieldChange,this);this.password=this.add({xtype:"textfield",name:"password",fieldLabel:_("Password"),inputType:"password",width:220});this.password.on("change",this.onFieldChange,this);this.setting=false},getName:function(){return this.initialConfig.name},getValue:function(){return{type:this.proxyType.getValue(),hostname:this.hostname.getValue(),port:Number(this.port.getValue()),username:this.username.getValue(),password:this.password.getValue()}},setValue:function(c){this.setting=true;this.proxyType.setValue(c.type);var b=this.proxyType.getStore().find("id",c.type);var a=this.proxyType.getStore().getAt(b);this.hostname.setValue(c.hostname);this.port.setValue(c.port);this.username.setValue(c.username);this.password.setValue(c.password);this.onTypeSelect(this.type,a,b);this.setting=false},onFieldChange:function(e,d,c){if(this.setting){return}var b=this.getValue();var a=Ext.apply({},b);a[e.getName()]=c;this.fireEvent("change",this,b,a)},onTypeSelect:function(d,a,b){var c=a.get("id");if(c>0){this.hostname.show();this.port.show()}else{this.hostname.hide();this.port.hide()}if(c==3||c==5){this.username.show();this.password.show()}else{this.username.hide();this.password.hide()}}});
/*
 * Deluge.preferences.ProxyPage.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.Proxy=Ext.extend(Ext.form.FormPanel,{constructor:function(a){a=Ext.apply({border:false,title:_("Proxy"),layout:"form",autoScroll:true},a);Deluge.preferences.Proxy.superclass.constructor.call(this,a)},initComponent:function(){Deluge.preferences.Proxy.superclass.initComponent.call(this);this.peer=this.add(new Deluge.preferences.ProxyField({title:_("Peer"),name:"peer"}));this.peer.on("change",this.onProxyChange,this);this.web_seed=this.add(new Deluge.preferences.ProxyField({title:_("Web Seed"),name:"web_seed"}));this.web_seed.on("change",this.onProxyChange,this);this.tracker=this.add(new Deluge.preferences.ProxyField({title:_("Tracker"),name:"tracker"}));this.tracker.on("change",this.onProxyChange,this);this.dht=this.add(new Deluge.preferences.ProxyField({title:_("DHT"),name:"dht"}));this.dht.on("change",this.onProxyChange,this);deluge.preferences.getOptionsManager().bind("proxies",this)},getValue:function(){return{dht:this.dht.getValue(),peer:this.peer.getValue(),tracker:this.tracker.getValue(),web_seed:this.web_seed.getValue()}},setValue:function(b){for(var a in b){this[a].setValue(b[a])}},onProxyChange:function(e,d,c){var b=this.getValue();var a=Ext.apply({},b);a[e.getName()]=c;this.fireEvent("change",this,b,a)}});
/*
 * Deluge.preferences.QueuePage.js
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
Ext.namespace("Deluge.preferences");Deluge.preferences.Queue=Ext.extend(Ext.form.FormPanel,{border:false,title:_("Queue"),layout:"form",initComponent:function(){Deluge.preferences.Queue.superclass.initComponent.call(this);var b=deluge.preferences.getOptionsManager();var a=this.add({xtype:"fieldset",border:false,title:_("General"),style:"padding-top: 5px;",autoHeight:true,labelWidth:1,defaultType:"checkbox"});b.bind("queue_new_to_top",a.add({fieldLabel:"",labelSeparator:"",height:22,boxLabel:_("Queue new torrents to top"),name:"queue_new_to_top"}));a=this.add({xtype:"fieldset",border:false,title:_("Active Torrents"),autoHeight:true,labelWidth:150,defaultType:"spinnerfield",style:"margin-bottom: 0px; padding-bottom: 0px;"});b.bind("max_active_limit",a.add({fieldLabel:_("Total Active"),name:"max_active_limit",value:8,width:80,decimalPrecision:0,minValue:-1,maxValue:99999}));b.bind("max_active_downloading",a.add({fieldLabel:_("Total Active Downloading"),name:"max_active_downloading",value:3,width:80,decimalPrecision:0,minValue:-1,maxValue:99999}));b.bind("max_active_seeding",a.add({fieldLabel:_("Total Active Seeding"),name:"max_active_seeding",value:5,width:80,decimalPrecision:0,minValue:-1,maxValue:99999}));b.bind("dont_count_slow_torrents",a.add({xtype:"checkbox",name:"dont_count_slow_torrents",height:40,hideLabel:true,boxLabel:_("Do not count slow torrents")}));a=this.add({xtype:"fieldset",border:false,title:_("Seeding"),autoHeight:true,labelWidth:150,defaultType:"spinnerfield",style:"margin-bottom: 0px; padding-bottom: 0px; margin-top: 0; padding-top: 0;"});b.bind("share_ratio_limit",a.add({fieldLabel:_("Share Ratio Limit"),name:"share_ratio_limit",value:8,width:80,incrementValue:0.1,minValue:-1,maxValue:99999,alternateIncrementValue:1,decimalPrecision:2}));b.bind("seed_time_ratio_limit",a.add({fieldLabel:_("Share Time Ratio"),name:"seed_time_ratio_limit",value:3,width:80,incrementValue:0.1,minValue:-1,maxValue:99999,alternateIncrementValue:1,decimalPrecision:2}));b.bind("seed_time_limit",a.add({fieldLabel:_("Seed Time (m)"),name:"seed_time_limit",value:5,width:80,decimalPrecision:0,minValue:-1,maxValue:99999}));a=this.add({xtype:"fieldset",border:false,autoHeight:true,layout:"table",layoutConfig:{columns:2},labelWidth:0,defaultType:"checkbox",defaults:{fieldLabel:"",labelSeparator:""}});this.stopAtRatio=a.add({name:"stop_seed_at_ratio",boxLabel:_("Stop seeding when share ratio reaches:")});this.stopAtRatio.on("check",this.onStopRatioCheck,this);b.bind("stop_seed_at_ratio",this.stopAtRatio);this.stopRatio=a.add({xtype:"spinnerfield",name:"stop_seed_ratio",ctCls:"x-deluge-indent-checkbox",disabled:true,value:"2.0",width:60,incrementValue:0.1,minValue:-1,maxValue:99999,alternateIncrementValue:1,decimalPrecision:2});b.bind("stop_seed_ratio",this.stopRatio);this.removeAtRatio=a.add({name:"remove_seed_at_ratio",ctCls:"x-deluge-indent-checkbox",boxLabel:_("Remove torrent when share ratio is reached"),disabled:true,colspan:2});b.bind("remove_seed_at_ratio",this.removeAtRatio)},onStopRatioCheck:function(b,a){this.stopRatio.setDisabled(!a);this.removeAtRatio.setDisabled(!a)}});
/*
 * Deluge.StatusbarMenu.js
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
Ext.ns("Deluge");Deluge.StatusbarMenu=Ext.extend(Ext.menu.Menu,{initComponent:function(){Deluge.StatusbarMenu.superclass.initComponent.call(this);this.otherWin=new Deluge.OtherLimitWindow(this.initialConfig.otherWin||{});this.items.each(function(a){if(a.getXType()!="menucheckitem"){return}if(a.value=="other"){a.on("click",this.onOtherClicked,this)}else{a.on("checkchange",this.onLimitChanged,this)}},this)},setValue:function(b){var c=false;this.value=b=(b==0)?-1:b;var a=null;this.items.each(function(d){if(d.setChecked){d.suspendEvents();if(d.value==b){d.setChecked(true);c=true}else{d.setChecked(false)}d.resumeEvents()}if(d.value=="other"){a=d}});if(c){return}a.suspendEvents();a.setChecked(true);a.resumeEvents()},onLimitChanged:function(c,b){if(!b||c.value=="other"){return}var a={};a[c.group]=c.value;deluge.client.core.set_config(a,{success:function(){deluge.ui.update()}})},onOtherClicked:function(a,b){this.otherWin.group=a.group;this.otherWin.setValue(this.value);this.otherWin.show()}});
/*
 * Deluge.OptionsManager.js
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
Ext.namespace("Deluge");Deluge.OptionsManager=Ext.extend(Ext.util.Observable,{constructor:function(a){a=a||{};this.binds={};this.changed={};this.options=(a&&a.options)||{};this.focused=null;this.addEvents({add:true,changed:true,reset:true});this.on("changed",this.onChange,this);Deluge.OptionsManager.superclass.constructor.call(this)},addOptions:function(a){this.options=Ext.applyIf(this.options,a)},bind:function(a,b){this.binds[a]=this.binds[a]||[];this.binds[a].push(b);b._doption=a;b.on("focus",this.onFieldFocus,this);b.on("blur",this.onFieldBlur,this);b.on("change",this.onFieldChange,this);b.on("check",this.onFieldChange,this);b.on("spin",this.onFieldChange,this);return b},commit:function(){this.options=Ext.apply(this.options,this.changed);this.reset()},convertValueType:function(a,b){if(Ext.type(a)!=Ext.type(b)){switch(Ext.type(a)){case"string":b=String(b);break;case"number":b=Number(b);break;case"boolean":if(Ext.type(b)=="string"){b=b.toLowerCase();b=(b=="true"||b=="1"||b=="on")?true:false}else{b=Boolean(b)}break}}return b},get:function(){if(arguments.length==1){var b=arguments[0];return(this.isDirty(b))?this.changed[b]:this.options[b]}else{var a={};Ext.each(arguments,function(c){if(!this.has(c)){return}a[c]=(this.isDirty(c))?this.changed[c]:this.options[c]},this);return a}},getDefault:function(a){return this.options[a]},getDirty:function(){return this.changed},isDirty:function(a){return !Ext.isEmpty(this.changed[a])},has:function(a){return(this.options[a])},reset:function(){this.changed={}},set:function(b,c){if(b===undefined){return}else{if(typeof b=="object"){var a=b;this.options=Ext.apply(this.options,a);for(var b in a){this.onChange(b,a[b])}}else{this.options[b]=c;this.onChange(b,c)}}},update:function(d,e){if(d===undefined){return}else{if(e===undefined){for(var c in d){this.update(c,d[c])}}else{var a=this.getDefault(d);e=this.convertValueType(a,e);var b=this.get(d);if(b==e){return}if(a==e){if(this.isDirty(d)){delete this.changed[d]}this.fireEvent("changed",d,e,b);return}this.changed[d]=e;this.fireEvent("changed",d,e,b)}}},onFieldBlur:function(b,a){if(this.focused==b){this.focused=null}},onFieldChange:function(b,a){if(b.field){b=b.field}this.update(b._doption,b.getValue())},onFieldFocus:function(b,a){this.focused=b},onChange:function(b,c,a){if(Ext.isEmpty(this.binds[b])){return}Ext.each(this.binds[b],function(d){if(d==this.focused){return}d.setValue(c)},this)}});
/*
 * Deluge.AddConnectionWindow.js
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
Ext.ns("Deluge");Deluge.AddConnectionWindow=Ext.extend(Ext.Window,{title:_("Add Connection"),iconCls:"x-deluge-add-window-icon",layout:"fit",width:300,height:195,bodyStyle:"padding: 10px 5px;",closeAction:"hide",initComponent:function(){Deluge.AddConnectionWindow.superclass.initComponent.call(this);this.addEvents("hostadded");this.addButton(_("Close"),this.hide,this);this.addButton(_("Add"),this.onAddClick,this);this.on("hide",this.onHide,this);this.form=this.add({xtype:"form",defaultType:"textfield",baseCls:"x-plain",labelWidth:60,items:[{fieldLabel:_("Host"),name:"host",anchor:"75%",value:""},{xtype:"spinnerfield",fieldLabel:_("Port"),name:"port",strategy:{xtype:"number",decimalPrecision:0,minValue:-1,maxValue:65535},value:"58846",anchor:"40%"},{fieldLabel:_("Username"),name:"username",anchor:"75%",value:""},{fieldLabel:_("Password"),anchor:"75%",name:"password",inputType:"password",value:""}]})},onAddClick:function(){var a=this.form.getForm().getValues();deluge.client.web.add_host(a.host,a.port,a.username,a.password,{success:function(b){if(!b[0]){Ext.MessageBox.show({title:_("Error"),msg:"Unable to add host: "+b[1],buttons:Ext.MessageBox.OK,modal:false,icon:Ext.MessageBox.ERROR,iconCls:"x-deluge-icon-error"})}else{this.fireEvent("hostadded")}this.hide()},scope:this})},onHide:function(){this.form.getForm().reset()}});
/*
 * Deluge.AddTrackerWindow.js
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
Ext.ns("Deluge");var trackerUrlTest=/(((^https?)|(^udp)):\/\/([\-\w]+\.)+\w{2,3}(\/[%\-\w]+(\.\w{2,})?)*(([\w\-\.\?\\\/+@&#;`~=%!]*)(\.\w{2,})?)*\/?)/i;Ext.apply(Ext.form.VTypes,{trackerUrl:function(b,a){return trackerUrlTest.test(b)},trackerUrlText:"Not a valid tracker url"});Deluge.AddTrackerWindow=Ext.extend(Ext.Window,{title:_("Add Tracker"),layout:"fit",width:375,height:150,plain:true,closable:true,resizable:false,bodyStyle:"padding: 5px",buttonAlign:"right",closeAction:"hide",iconCls:"x-deluge-edit-trackers",initComponent:function(){Deluge.AddTrackerWindow.superclass.initComponent.call(this);this.addButton(_("Cancel"),this.onCancelClick,this);this.addButton(_("Add"),this.onAddClick,this);this.addEvents("add");this.form=this.add({xtype:"form",defaultType:"textarea",baseCls:"x-plain",labelWidth:55,items:[{fieldLabel:_("Trackers"),name:"trackers",anchor:"100%"}]})},onAddClick:function(){var b=this.form.getForm().findField("trackers").getValue();b=b.split("\n");var a=[];Ext.each(b,function(c){if(Ext.form.VTypes.trackerUrl(c)){a.push(c)}},this);this.fireEvent("add",a);this.hide();this.form.getForm().findField("trackers").setValue("")},onCancelClick:function(){this.form.getForm().findField("trackers").setValue("");this.hide()}});
/*
 * Deluge.Client.js
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
Ext.namespace("Ext.ux.util");Ext.ux.util.RpcClient=Ext.extend(Ext.util.Observable,{_components:[],_methods:[],_requests:{},_url:null,_optionKeys:["scope","success","failure"],constructor:function(a){Ext.ux.util.RpcClient.superclass.constructor.call(this,a);this._url=a.url||null;this._id=0;this.addEvents("connected","error");this.reloadMethods()},reloadMethods:function(){this._execute("system.listMethods",{success:this._setMethods,scope:this})},_execute:function(c,a){a=a||{};a.params=a.params||[];a.id=this._id;var b=Ext.encode({method:c,params:a.params,id:a.id});this._id++;return Ext.Ajax.request({url:this._url,method:"POST",success:this._onSuccess,failure:this._onFailure,scope:this,jsonData:b,options:a})},_onFailure:function(b,a){var c=a.options;errorObj={id:c.id,result:null,error:{msg:"HTTP: "+b.status+" "+b.statusText,code:255}};this.fireEvent("error",errorObj,b,a);if(Ext.type(c.failure)!="function"){return}if(c.scope){c.failure.call(c.scope,errorObj,b,a)}else{c.failure(errorObj,b,a)}},_onSuccess:function(c,a){var b=Ext.decode(c.responseText);var d=a.options;if(b.error){this.fireEvent("error",b,c,a);if(Ext.type(d.failure)!="function"){return}if(d.scope){d.failure.call(d.scope,b,c,a)}else{d.failure(b,c,a)}}else{if(Ext.type(d.success)!="function"){return}if(d.scope){d.success.call(d.scope,b.result,b,c,a)}else{d.success(b.result,b,c,a)}}},_parseArgs:function(c){var e=[];Ext.each(c,function(f){e.push(f)});var b=e[e.length-1];if(Ext.type(b)=="object"){var d=Ext.keys(b),a=false;Ext.each(this._optionKeys,function(f){if(d.indexOf(f)>-1){a=true}});if(a){e.remove(b)}else{b={}}}else{b={}}b.params=e;return b},_setMethods:function(b){var d={},a=this;Ext.each(b,function(h){var g=h.split(".");var e=d[g[0]]||{};var f=function(){var i=a._parseArgs(arguments);return a._execute(h,i)};e[g[1]]=f;d[g[0]]=e});for(var c in d){a[c]=d[c]}Ext.each(this._components,function(e){if(!e in d){delete this[e]}},this);this._components=Ext.keys(d);this.fireEvent("connected",this)}});
/*
 * Deluge.ConnectionManager.js
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
Deluge.ConnectionManager=Ext.extend(Ext.Window,{layout:"fit",width:300,height:220,bodyStyle:"padding: 10px 5px;",buttonAlign:"right",closeAction:"hide",closable:true,plain:true,title:_("Connection Manager"),iconCls:"x-deluge-connect-window-icon",initComponent:function(){Deluge.ConnectionManager.superclass.initComponent.call(this);this.on("hide",this.onHide,this);this.on("show",this.onShow,this);deluge.events.on("login",this.onLogin,this);deluge.events.on("logout",this.onLogout,this);this.addButton(_("Close"),this.onClose,this);this.addButton(_("Connect"),this.onConnect,this);this.list=new Ext.list.ListView({store:new Ext.data.ArrayStore({fields:[{name:"status",mapping:3},{name:"host",mapping:1},{name:"port",mapping:2},{name:"version",mapping:4}],id:0}),columns:[{header:_("Status"),width:0.24,sortable:true,tpl:new Ext.XTemplate("<tpl if=\"status == 'Online'\">",_("Online"),"</tpl>","<tpl if=\"status == 'Offline'\">",_("Offline"),"</tpl>","<tpl if=\"status == 'Connected'\">",_("Connected"),"</tpl>"),dataIndex:"status"},{id:"host",header:_("Host"),width:0.51,sortable:true,tpl:"{host}:{port}",dataIndex:"host"},{header:_("Version"),width:0.25,sortable:true,tpl:'<tpl if="version">{version}</tpl>',dataIndex:"version"}],singleSelect:true,listeners:{selectionchange:{fn:this.onSelectionChanged,scope:this}}});this.panel=this.add({autoScroll:true,items:[this.list],bbar:new Ext.Toolbar({buttons:[{id:"cm-add",cls:"x-btn-text-icon",text:_("Add"),iconCls:"icon-add",handler:this.onAddClick,scope:this},{id:"cm-remove",cls:"x-btn-text-icon",text:_("Remove"),iconCls:"icon-remove",handler:this.onRemoveClick,disabled:true,scope:this},"->",{id:"cm-stop",cls:"x-btn-text-icon",text:_("Stop Daemon"),iconCls:"icon-error",handler:this.onStopClick,disabled:true,scope:this}]})});this.update=this.update.createDelegate(this)},checkConnected:function(){deluge.client.web.connected({success:function(a){if(a){deluge.events.fire("connect")}else{this.show()}},scope:this})},disconnect:function(a){deluge.events.fire("disconnect");if(a){if(this.isVisible()){return}this.show()}},loadHosts:function(){deluge.client.web.get_hosts({success:this.onGetHosts,scope:this})},update:function(){this.list.getStore().each(function(a){deluge.client.web.get_host_status(a.id,{success:this.onGetHostStatus,scope:this})},this)},updateButtons:function(b){var c=this.buttons[1],a=b.get("status");if(a=="Connected"){c.enable();c.setText(_("Disconnect"))}else{if(a=="Offline"){c.disable()}else{c.enable();c.setText(_("Connect"))}}if(a=="Offline"){if(b.get("host")=="127.0.0.1"||b.get("host")=="localhost"){this.stopHostButton.enable();this.stopHostButton.setText(_("Start Daemon"))}else{this.stopHostButton.disable()}}else{this.stopHostButton.enable();this.stopHostButton.setText(_("Stop Daemon"))}},onAddClick:function(a,b){if(!this.addWindow){this.addWindow=new Deluge.AddConnectionWindow();this.addWindow.on("hostadded",this.onHostAdded,this)}this.addWindow.show()},onHostAdded:function(){this.loadHosts()},onClose:function(a){this.hide()},onConnect:function(b){var a=this.list.getSelectedRecords()[0];if(!a){return}if(a.get("status")=="Connected"){deluge.client.web.disconnect({success:function(d){this.update(this);deluge.events.fire("disconnect")},scope:this})}else{var c=a.id;deluge.client.web.connect(c,{success:function(d){deluge.client.reloadMethods();deluge.client.on("connected",function(f){deluge.events.fire("connect")},this,{single:true})}});this.hide()}},onGetHosts:function(a){this.list.getStore().loadData(a);Ext.each(a,function(b){deluge.client.web.get_host_status(b[0],{success:this.onGetHostStatus,scope:this})},this)},onGetHostStatus:function(b){var a=this.list.getStore().getById(b[0]);a.set("status",b[3]);a.set("version",b[4]);a.commit();if(this.list.getSelectedRecords()[0]==a){this.updateButtons(a)}},onHide:function(){if(this.running){window.clearInterval(this.running)}},onLogin:function(){if(deluge.config.first_login){Ext.MessageBox.confirm(_("Change Default Password"),_("We recommend changing the default password.<br><br>Would you like to change it now?"),function(a){this.checkConnected();if(a=="yes"){deluge.preferences.show();deluge.preferences.selectPage("Interface")}deluge.client.web.set_config({first_login:false})},this)}else{this.checkConnected()}},onLogout:function(){this.disconnect();if(!this.hidden&&this.rendered){this.hide()}},onRemoveClick:function(b){var a=this.list.getSelectedRecords()[0];if(!a){return}deluge.client.web.remove_host(a.id,{success:function(c){if(!c){Ext.MessageBox.show({title:_("Error"),msg:c[1],buttons:Ext.MessageBox.OK,modal:false,icon:Ext.MessageBox.ERROR,iconCls:"x-deluge-icon-error"})}else{this.list.getStore().remove(a)}},scope:this})},onSelectionChanged:function(b,a){if(a[0]){this.removeHostButton.enable();this.stopHostButton.enable();this.stopHostButton.setText(_("Stop Daemon"));this.updateButtons(this.list.getRecord(a[0]))}else{this.removeHostButton.disable();this.stopHostButton.disable()}},onShow:function(){if(!this.addHostButton){var a=this.panel.getBottomToolbar();this.addHostButton=a.items.get("cm-add");this.removeHostButton=a.items.get("cm-remove");this.stopHostButton=a.items.get("cm-stop")}this.loadHosts();if(this.running){return}this.running=window.setInterval(this.update,2000,this)},onStopClick:function(b,c){var a=this.list.getSelectedRecords()[0];if(!a){return}if(a.get("status")=="Offline"){deluge.client.web.start_daemon(a.get("port"))}else{deluge.client.web.stop_daemon(a.id,{success:function(d){if(!d[0]){Ext.MessageBox.show({title:_("Error"),msg:d[1],buttons:Ext.MessageBox.OK,modal:false,icon:Ext.MessageBox.ERROR,iconCls:"x-deluge-icon-error"})}}})}}});
/*
 * Deluge.js
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
Ext.state.Manager.setProvider(new Ext.state.CookieProvider({expires:new Date(new Date().getTime()+(1000*60*60*24*365*10))}));Ext.apply(Ext,{escapeHTML:function(a){a=String(a).replace("<","&lt;").replace(">","&gt;");return a.replace("&","&amp;")},isObjectEmpty:function(b){for(var a in b){return false}return true},areObjectsEqual:function(d,c){var b=true;if(!d||!c){return false}for(var a in d){if(d[a]!=c[a]){b=false}}return b},keys:function(c){var b=[];for(var a in c){if(c.hasOwnProperty(a)){b.push(a)}}return b},values:function(c){var a=[];for(var b in c){if(c.hasOwnProperty(b)){a.push(c[b])}}return a},splat:function(b){var a=Ext.type(b);return(a)?((a!="array")?[b]:b):[]}});Ext.getKeys=Ext.keys;Ext.BLANK_IMAGE_URL=deluge.config.base+"images/s.gif";Ext.USE_NATIVE_JSON=true;Ext.apply(Deluge,{pluginStore:{},progressTpl:'<div class="x-progress-wrap x-progress-renderered"><div class="x-progress-inner"><div style="width: {2}px" class="x-progress-bar"><div style="z-index: 99; width: {3}px" class="x-progress-text"><div style="width: {1}px;">{0}</div></div></div><div class="x-progress-text x-progress-text-back"><div style="width: {1}px;">{0}</div></div></div></div>',progressBar:function(c,e,g,a){a=Ext.value(a,10);var b=((e/100)*c).toFixed(0);var d=b-1;var f=((b-a)>0?b-a:0);return String.format(Deluge.progressTpl,g,e,d,f)},createPlugin:function(a){return new Deluge.pluginStore[a]()},hasPlugin:function(a){return(Deluge.pluginStore[a])?true:false},registerPlugin:function(a,b){Deluge.pluginStore[a]=b}});deluge.plugins={};FILE_PRIORITY={9:"Mixed",0:"Do Not Download",1:"Normal Priority",2:"High Priority",5:"High Priority",7:"Highest Priority",Mixed:9,"Do Not Download":0,"Normal Priority":1,"High Priority":5,"Highest Priority":7};FILE_PRIORITY_CSS={9:"x-mixed-download",0:"x-no-download",1:"x-normal-download",2:"x-high-download",5:"x-high-download",7:"x-highest-download"}
/*
 * Deluge.EditTrackerWindow.js
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
;Ext.ns("Deluge");Deluge.EditTrackerWindow=Ext.extend(Ext.Window,{title:_("Edit Tracker"),layout:"fit",width:375,height:110,plain:true,closable:true,resizable:false,bodyStyle:"padding: 5px",buttonAlign:"right",closeAction:"hide",iconCls:"x-deluge-edit-trackers",initComponent:function(){Deluge.EditTrackerWindow.superclass.initComponent.call(this);this.addButton(_("Cancel"),this.onCancelClick,this);this.addButton(_("Save"),this.onSaveClick,this);this.on("hide",this.onHide,this);this.form=this.add({xtype:"form",defaultType:"textfield",baseCls:"x-plain",labelWidth:55,items:[{fieldLabel:_("Tracker"),name:"tracker",anchor:"100%"}]})},show:function(a){Deluge.EditTrackerWindow.superclass.show.call(this);this.record=a;this.form.getForm().findField("tracker").setValue(a.data.url)},onCancelClick:function(){this.hide()},onHide:function(){this.form.getForm().findField("tracker").setValue("")},onSaveClick:function(){var a=this.form.getForm().findField("tracker").getValue();this.record.set("url",a);this.record.commit();this.hide()}});
/*
 * Deluge.EditTrackers.js
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
Ext.ns("Deluge");Deluge.EditTrackersWindow=Ext.extend(Ext.Window,{title:_("Edit Trackers"),layout:"fit",width:350,height:220,plain:true,closable:true,resizable:true,bodyStyle:"padding: 5px",buttonAlign:"right",closeAction:"hide",iconCls:"x-deluge-edit-trackers",initComponent:function(){Deluge.EditTrackersWindow.superclass.initComponent.call(this);this.addButton(_("Cancel"),this.onCancelClick,this);this.addButton(_("Ok"),this.onOkClick,this);this.addEvents("save");this.on("show",this.onShow,this);this.on("save",this.onSave,this);this.addWindow=new Deluge.AddTrackerWindow();this.addWindow.on("add",this.onAddTrackers,this);this.editWindow=new Deluge.EditTrackerWindow();this.list=new Ext.list.ListView({store:new Ext.data.JsonStore({root:"trackers",fields:["tier","url"]}),columns:[{header:_("Tier"),width:0.1,dataIndex:"tier"},{header:_("Tracker"),width:0.9,dataIndex:"url"}],columnSort:{sortClasses:["",""]},stripeRows:true,singleSelect:true,listeners:{dblclick:{fn:this.onListNodeDblClicked,scope:this},selectionchange:{fn:this.onSelect,scope:this}}});this.panel=this.add({margins:"0 0 0 0",items:[this.list],autoScroll:true,bbar:new Ext.Toolbar({items:[{text:_("Up"),iconCls:"icon-up",handler:this.onUpClick,scope:this},{text:_("Down"),iconCls:"icon-down",handler:this.onDownClick,scope:this},"->",{text:_("Add"),iconCls:"icon-add",handler:this.onAddClick,scope:this},{text:_("Edit"),iconCls:"icon-edit-trackers",handler:this.onEditClick,scope:this},{text:_("Remove"),iconCls:"icon-remove",handler:this.onRemoveClick,scope:this}]})})},onAddClick:function(){this.addWindow.show()},onAddTrackers:function(b){var a=this.list.getStore();Ext.each(b,function(d){var e=false,c=-1;a.each(function(f){if(f.get("tier")>c){c=f.get("tier")}if(d==f.get("tracker")){e=true;return false}},this);if(e){return}a.add(new a.recordType({tier:c+1,url:d}))},this)},onCancelClick:function(){this.hide()},onEditClick:function(){this.editWindow.show(this.list.getSelectedRecords()[0])},onHide:function(){this.list.getStore().removeAll()},onListNodeDblClicked:function(c,a,b,d){this.editWindow.show(this.list.getRecord(b))},onOkClick:function(){var a=[];this.list.getStore().each(function(b){a.push({tier:b.get("tier"),url:b.get("url")})},this);deluge.client.core.set_torrent_trackers(this.torrentId,a,{failure:this.onSaveFail,scope:this});this.hide()},onRemoveClick:function(){this.list.getStore().remove(this.list.getSelectedRecords()[0])},onRequestComplete:function(a){this.list.getStore().loadData(a);this.list.getStore().sort("tier","ASC")},onSaveFail:function(){},onSelect:function(a){if(a.getSelectionCount()){this.panel.getBottomToolbar().items.get(4).enable()}},onShow:function(){this.panel.getBottomToolbar().items.get(4).disable();var a=deluge.torrents.getSelected();this.torrentId=a.id;deluge.client.core.get_torrent_status(a.id,["trackers"],{success:this.onRequestComplete,scope:this})},onDownClick:function(){var a=this.list.getSelectedRecords()[0];if(!a){return}a.set("tier",a.get("tier")+1);a.store.sort("tier","ASC");a.store.commitChanges();this.list.select(a.store.indexOf(a))},onUpClick:function(){var a=this.list.getSelectedRecords()[0];if(!a){return}if(a.get("tier")==0){return}a.set("tier",a.get("tier")-1);a.store.sort("tier","ASC");a.store.commitChanges();this.list.select(a.store.indexOf(a))}});
/*
 * Deluge.EventsManager.js
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
Deluge.EventsManager=Ext.extend(Ext.util.Observable,{constructor:function(){this.toRegister=[];this.on("login",this.onLogin,this);Deluge.EventsManager.superclass.constructor.call(this)},addListener:function(a,c,b,d){this.addEvents(a);if(/[A-Z]/.test(a.substring(0,1))){if(!deluge.client){this.toRegister.push(a)}else{deluge.client.web.register_event_listener(a)}}Deluge.EventsManager.superclass.addListener.call(this,a,c,b,d)},getEvents:function(){deluge.client.web.get_events({success:this.onGetEventsSuccess,failure:this.onGetEventsFailure,scope:this})},start:function(){Ext.each(this.toRegister,function(a){deluge.client.web.register_event_listener(a)});this.running=true;this.errorCount=0;this.getEvents()},stop:function(){this.running=false},onLogin:function(){this.start()},onGetEventsSuccess:function(a){if(!this.running){return}if(a){Ext.each(a,function(d){var c=d[0],b=d[1];b.splice(0,0,c);this.fireEvent.apply(this,b)},this)}this.getEvents()},onGetEventsFailure:function(a,b){if(!this.running){return}if(!b.isTimeout&&this.errorCount++>=3){this.stop();return}this.getEvents()}});Deluge.EventsManager.prototype.on=Deluge.EventsManager.prototype.addListener;Deluge.EventsManager.prototype.fire=Deluge.EventsManager.prototype.fireEvent;deluge.events=new Deluge.EventsManager();
/*
 * Deluge.FileBrowser.js
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
Ext.namespace("Deluge");Deluge.FileBrowser=Ext.extend(Ext.Window,{title:_("File Browser"),width:500,height:400,initComponent:function(){Deluge.FileBrowser.superclass.initComponent.call(this);this.add({xtype:"toolbar",items:[{text:_("Back"),iconCls:"icon-back"},{text:_("Forward"),iconCls:"icon-forward"},{text:_("Up"),iconCls:"icon-up"},{text:_("Home"),iconCls:"icon-home"}]})}});
/*
 * Deluge.FilterPanel.js
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
Ext.ns("Deluge");Deluge.FilterPanel=Ext.extend(Ext.Panel,{autoScroll:true,border:false,show_zero:null,initComponent:function(){Deluge.FilterPanel.superclass.initComponent.call(this);this.filterType=this.initialConfig.filter;var c=this.filterType.replace("_"," "),b=c.split(" "),c="";Ext.each(b,function(d){fl=d.substring(0,1).toUpperCase();c+=fl+d.substring(1)+" "});this.setTitle(_(c));if(Deluge.FilterPanel.templates[this.filterType]){var a=Deluge.FilterPanel.templates[this.filterType]}else{var a='<div class="x-deluge-filter x-deluge-{filter:lowercase}">{filter} ({count})</div>'}this.list=this.add({xtype:"listview",singleSelect:true,hideHeaders:true,reserveScrollOffset:true,store:new Ext.data.ArrayStore({idIndex:0,fields:["filter","count"]}),columns:[{id:"filter",sortable:false,tpl:a,dataIndex:"filter"}]});this.relayEvents(this.list,["selectionchange"])},getState:function(){if(!this.list.getSelectionCount()){return}var a=this.list.getSelectedRecords()[0];if(a.id=="All"){return}return a.id},getStates:function(){return this.states},getStore:function(){return this.list.getStore()},updateStates:function(b){this.states={};Ext.each(b,function(f){this.states[f[0]]=f[1]},this);var e=(this.show_zero==null)?deluge.config.sidebar_show_zero:this.show_zero;if(!e){var c=[];Ext.each(b,function(f){if(f[1]>0||f[0]==_("All")){c.push(f)}});b=c}var a=this.getStore();var d={};Ext.each(b,function(h,g){var f=a.getById(h[0]);if(!f){f=new a.recordType({filter:h[0],count:h[1]});f.id=h[0];a.insert(g,f)}f.beginEdit();f.set("filter",h[0]);f.set("count",h[1]);f.endEdit();d[h[0]]=true},this);a.each(function(f){if(d[f.id]){return}var g=this.list.getSelectedRecords()[0];a.remove(f);if(g.id==f.id){this.list.select(0)}},this);a.commitChanges();if(!this.list.getSelectionCount()){this.list.select(0)}}});Deluge.FilterPanel.templates={tracker_host:'<div class="x-deluge-filter" style="background-image: url('+deluge.config.base+'tracker/{filter});">{filter} ({count})</div>'}
/*
 * Deluge.Formatters.js
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
;Deluge.Formatters={date:function(c){function b(d,e){var f=d+"";while(f.length<e){f="0"+f}return f}c=c*1000;var a=new Date(c);return String.format("{0}/{1}/{2} {3}:{4}:{5}",b(a.getDate(),2),b(a.getMonth()+1,2),a.getFullYear(),b(a.getHours(),2),b(a.getMinutes(),2),b(a.getSeconds(),2))},size:function(b,a){if(!b&&!a){return""}b=b/1024;if(b<1024){return b.toFixed(1)+" KiB"}else{b=b/1024}if(b<1024){return b.toFixed(1)+" MiB"}else{b=b/1024}return b.toFixed(1)+" GiB"},sizeShort:function(b,a){if(!b&&!a){return""}b=b/1024;if(b<1024){return b.toFixed(1)+" K"}else{b=b/1024}if(b<1024){return b.toFixed(1)+" M"}else{b=b/1024}return b.toFixed(1)+" G"},speed:function(b,a){return(!b&&!a)?"":fsize(b,a)+"/s"},timeRemaining:function(c){if(c==0){return"&infin;"}c=c.toFixed(0);if(c<60){return c+"s"}else{c=c/60}if(c<60){var b=Math.floor(c);var d=Math.round(60*(c-b));if(d>0){return b+"m "+d+"s"}else{return b+"m"}}else{c=c/60}if(c<24){var a=Math.floor(c);var b=Math.round(60*(c-a));if(b>0){return a+"h "+b+"m"}else{return a+"h"}}else{c=c/24}var e=Math.floor(c);var a=Math.round(24*(c-e));if(a>0){return e+"d "+a+"h"}else{return e+"d"}},plain:function(a){return a},cssClassEscape:function(a){return a.toLowerCase().replace(".","_")}};var fsize=Deluge.Formatters.size;var fsize_short=Deluge.Formatters.sizeShort;var fspeed=Deluge.Formatters.speed;var ftime=Deluge.Formatters.timeRemaining;var fdate=Deluge.Formatters.date;var fplain=Deluge.Formatters.plain;Ext.util.Format.cssClassEscape=Deluge.Formatters.cssClassEscape;
/*
 * Deluge.Keys.js
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
Deluge.Keys={Grid:["queue","name","total_wanted","state","progress","num_seeds","total_seeds","num_peers","total_peers","download_payload_rate","upload_payload_rate","eta","ratio","distributed_copies","is_auto_managed","time_added","tracker_host","save_path","total_done","total_uploaded","max_download_speed","max_upload_speed","seeds_peers_ratio"],Status:["total_done","total_payload_download","total_uploaded","total_payload_upload","next_announce","tracker_status","num_pieces","piece_length","is_auto_managed","active_time","seeding_time","seed_rank"],Files:["files","file_progress","file_priorities"],Peers:["peers"],Details:["name","save_path","total_size","num_files","message","tracker","comment"],Options:["max_download_speed","max_upload_speed","max_connections","max_upload_slots","is_auto_managed","stop_at_ratio","stop_ratio","remove_at_ratio","private","prioritize_first_last","move_completed","move_completed_path"]};Ext.each(Deluge.Keys.Grid,function(a){Deluge.Keys.Status.push(a)});
/*
 * Deluge.LoginWindow.js
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
Deluge.LoginWindow=Ext.extend(Ext.Window,{firstShow:true,bodyStyle:"padding: 10px 5px;",buttonAlign:"center",closable:false,closeAction:"hide",iconCls:"x-deluge-login-window-icon",layout:"fit",modal:true,plain:true,resizable:false,title:_("Login"),width:300,height:120,initComponent:function(){Deluge.LoginWindow.superclass.initComponent.call(this);this.on("show",this.onShow,this);this.addButton({text:_("Login"),handler:this.onLogin,scope:this});this.form=this.add({xtype:"form",baseCls:"x-plain",labelWidth:120,labelAlign:"right",defaults:{width:110},defaultType:"textfield"});this.passwordField=this.form.add({xtype:"textfield",fieldLabel:_("Password"),grow:true,growMin:"110",growMax:"145",id:"_password",name:"password",inputType:"password"});this.passwordField.on("specialkey",this.onSpecialKey,this)},logout:function(){deluge.events.fire("logout");deluge.client.auth.delete_session({success:function(a){this.show(true)},scope:this})},show:function(a){if(this.firstShow){deluge.client.on("error",this.onClientError,this);this.firstShow=false}if(a){return Deluge.LoginWindow.superclass.show.call(this)}deluge.client.auth.check_session({success:function(b){if(b){deluge.events.fire("login")}else{this.show(true)}},failure:function(b){this.show(true)},scope:this})},onSpecialKey:function(b,a){if(a.getKey()==13){this.onLogin()}},onLogin:function(){var a=this.passwordField;deluge.client.auth.login(a.getValue(),{success:function(b){if(b){deluge.events.fire("login");this.hide();a.setRawValue("")}else{Ext.MessageBox.show({title:_("Login Failed"),msg:_("You entered an incorrect password"),buttons:Ext.MessageBox.OK,modal:false,fn:function(){a.focus(true,10)},icon:Ext.MessageBox.WARNING,iconCls:"x-deluge-icon-warning"})}},scope:this})},onClientError:function(c,b,a){if(c.error.code==1){deluge.events.fire("logout");this.show(true)}},onShow:function(){this.passwordField.focus(true,300)}});
/*
 * Deluge.Menus.js
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
deluge.menus={onTorrentActionSetOpt:function(c,f){var a=deluge.torrents.getSelectedIds();var d=c.initialConfig.torrentAction;var b={};b[d[0]]=d[1];deluge.client.core.set_torrent_options(a,b)},onTorrentActionMethod:function(b,d){var a=deluge.torrents.getSelectedIds();var c=b.initialConfig.torrentAction;deluge.client.core[c](a,{success:function(){deluge.ui.update()}})},onTorrentActionShow:function(b,d){var a=deluge.torrents.getSelectedIds();var c=b.initialConfig.torrentAction;switch(c){case"edit_trackers":deluge.editTrackers.show();break;case"remove":deluge.removeWindow.show(a);break;case"move":deluge.moveStorage.show(a);break}},};deluge.menus.torrent=new Ext.menu.Menu({id:"torrentMenu",items:[{torrentAction:"pause_torrent",text:_("Pause"),iconCls:"icon-pause",handler:deluge.menus.onTorrentActionMethod,scope:deluge.menus},{torrentAction:"resume_torrent",text:_("Resume"),iconCls:"icon-resume",handler:deluge.menus.onTorrentActionMethod,scope:deluge.menus},"-",{text:_("Options"),iconCls:"icon-options",hideOnClick:false,menu:new Ext.menu.Menu({items:[{text:_("D/L Speed Limit"),iconCls:"x-deluge-downloading",hideOnClick:false,menu:new Ext.menu.Menu({items:[{torrentAction:["max_download_speed",5],text:_("5 KiB/s"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_download_speed",10],text:_("10 KiB/s"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_download_speed",30],text:_("30 KiB/s"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_download_speed",80],text:_("80 KiB/s"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_download_speed",300],text:_("300 KiB/s"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_download_speed",-1],text:_("Unlimited"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus}]})},{text:_("U/L Speed Limit"),iconCls:"x-deluge-seeding",hideOnClick:false,menu:new Ext.menu.Menu({items:[{torrentAction:["max_upload_speed",5],text:_("5 KiB/s"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_upload_speed",10],text:_("10 KiB/s"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_upload_speed",30],text:_("30 KiB/s"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_upload_speed",80],text:_("80 KiB/s"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_upload_speed",300],text:_("300 KiB/s"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_upload_speed",-1],text:_("Unlimited"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus}]})},{text:_("Connection Limit"),iconCls:"x-deluge-connections",hideOnClick:false,menu:new Ext.menu.Menu({items:[{torrentAction:["max_connections",50],text:_("50"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_connections",100],text:_("100"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_connections",200],text:_("200"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_connections",300],text:_("300"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_connections",500],text:_("500"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_connections",-1],text:_("Unlimited"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus}]})},{text:_("Upload Slot Limit"),iconCls:"icon-upload-slots",hideOnClick:false,menu:new Ext.menu.Menu({items:[{torrentAction:["max_upload_slots",0],text:_("0"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_upload_slots",1],text:_("1"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_upload_slots",2],text:_("2"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_upload_slots",3],text:_("3"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_upload_slots",5],text:_("5"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["max_upload_slots",-1],text:_("Unlimited"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus}]})},{id:"auto_managed",text:_("Auto Managed"),hideOnClick:false,menu:new Ext.menu.Menu({items:[{torrentAction:["auto_managed",true],text:_("On"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus},{torrentAction:["auto_managed",false],text:_("Off"),handler:deluge.menus.onTorrentActionSetOpt,scope:deluge.menus}]})}]})},"-",{text:_("Queue"),iconCls:"icon-queue",hideOnClick:false,menu:new Ext.menu.Menu({items:[{torrentAction:"queue_top",text:_("Top"),iconCls:"icon-top",handler:deluge.menus.onTorrentActionMethod,scope:deluge.menus},{torrentAction:"queue_up",text:_("Up"),iconCls:"icon-up",handler:deluge.menus.onTorrentActionMethod,scope:deluge.menus},{torrentAction:"queue_down",text:_("Down"),iconCls:"icon-down",handler:deluge.menus.onTorrentActionMethod,scope:deluge.menus},{torrentAction:"queue_bottom",text:_("Bottom"),iconCls:"icon-bottom",handler:deluge.menus.onTorrentActionMethod,scope:deluge.menus}]})},"-",{torrentAction:"force_reannounce",text:_("Update Tracker"),iconCls:"icon-update-tracker",handler:deluge.menus.onTorrentActionMethod,scope:deluge.menus},{torrentAction:"edit_trackers",text:_("Edit Trackers"),iconCls:"icon-edit-trackers",handler:deluge.menus.onTorrentActionShow,scope:deluge.menus},"-",{torrentAction:"remove",text:_("Remove Torrent"),iconCls:"icon-remove",handler:deluge.menus.onTorrentActionShow,scope:deluge.menus},"-",{torrentAction:"force_recheck",text:_("Force Recheck"),iconCls:"icon-recheck",handler:deluge.menus.onTorrentActionMethod,scope:deluge.menus},{torrentAction:"move",text:_("Move Storage"),iconCls:"icon-move",handler:deluge.menus.onTorrentActionShow,scope:deluge.menus}]});deluge.menus.filePriorities=new Ext.menu.Menu({id:"filePrioritiesMenu",items:[{id:"expandAll",text:_("Expand All"),iconCls:"icon-expand-all"},"-",{id:"no_download",text:_("Do Not Download"),iconCls:"icon-do-not-download",filePriority:FILE_PRIORITY["Do Not Download"]},{id:"normal",text:_("Normal Priority"),iconCls:"icon-normal",filePriority:FILE_PRIORITY["Normal Priority"]},{id:"high",text:_("High Priority"),iconCls:"icon-high",filePriority:FILE_PRIORITY["High Priority"]},{id:"highest",text:_("Highest Priority"),iconCls:"icon-highest",filePriority:FILE_PRIORITY["Highest Priority"]}]});
/*
 * Deluge.MoveStorage.js
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
Ext.namespace("Deluge");Deluge.MoveStorage=Ext.extend(Ext.Window,{constructor:function(a){a=Ext.apply({title:_("Move Storage"),width:375,height:110,layout:"fit",buttonAlign:"right",closeAction:"hide",closable:true,iconCls:"x-deluge-move-storage",plain:true,resizable:false},a);Deluge.MoveStorage.superclass.constructor.call(this,a)},initComponent:function(){Deluge.MoveStorage.superclass.initComponent.call(this);this.addButton(_("Cancel"),this.onCancel,this);this.addButton(_("Move"),this.onMove,this);this.form=this.add({xtype:"form",border:false,defaultType:"textfield",width:300,bodyStyle:"padding: 5px"});this.moveLocation=this.form.add({fieldLabel:_("Location"),name:"location",width:240})},hide:function(){Deluge.MoveStorage.superclass.hide.call(this);this.torrentIds=null},show:function(a){Deluge.MoveStorage.superclass.show.call(this);this.torrentIds=a},onCancel:function(){this.hide()},onMove:function(){var a=this.moveLocation.getValue();deluge.client.core.move_storage(this.torrentIds,a);this.hide()}});deluge.moveStorage=new Deluge.MoveStorage();
/*
 * Deluge.MultiOptionsManager.js
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
Deluge.MultiOptionsManager=Ext.extend(Deluge.OptionsManager,{constructor:function(a){this.currentId=null;this.stored={};Deluge.MultiOptionsManager.superclass.constructor.call(this,a)},changeId:function(d,b){var c=this.currentId;this.currentId=d;if(!b){for(var a in this.options){if(!this.binds[a]){continue}Ext.each(this.binds[a],function(e){e.setValue(this.get(a))},this)}}return c},commit:function(){this.stored[this.currentId]=Ext.apply(this.stored[this.currentId],this.changed[this.currentId]);this.reset()},get:function(){if(arguments.length==1){var b=arguments[0];return(this.isDirty(b))?this.changed[this.currentId][b]:this.getDefault(b)}else{if(arguments.length==0){var a={};for(var b in this.options){a[b]=(this.isDirty(b))?this.changed[this.currentId][b]:this.getDefault(b)}return a}else{var a={};Ext.each(arguments,function(c){a[c]=(this.isDirty(c))?this.changed[this.currentId][c]:this.getDefault(c)},this);return a}}},getDefault:function(a){return(this.has(a))?this.stored[this.currentId][a]:this.options[a]},getDirty:function(){return(this.changed[this.currentId])?this.changed[this.currentId]:{}},isDirty:function(a){return(this.changed[this.currentId]&&!Ext.isEmpty(this.changed[this.currentId][a]))},has:function(a){return(this.stored[this.currentId]&&!Ext.isEmpty(this.stored[this.currentId][a]))},reset:function(){if(this.changed[this.currentId]){delete this.changed[this.currentId]}if(this.stored[this.currentId]){delete this.stored[this.currentId]}},resetAll:function(){this.changed={};this.stored={};this.changeId(null)},setDefault:function(c,d){if(c===undefined){return}else{if(d===undefined){for(var b in c){this.setDefault(b,c[b])}}else{var a=this.getDefault(c);d=this.convertValueType(a,d);if(a==d){return}if(!this.stored[this.currentId]){this.stored[this.currentId]={}}this.stored[this.currentId][c]=d;if(!this.isDirty(c)){this.fireEvent("changed",c,d,a)}}}},update:function(d,e){if(d===undefined){return}else{if(e===undefined){for(var c in d){this.update(c,d[c])}}else{if(!this.changed[this.currentId]){this.changed[this.currentId]={}}var a=this.getDefault(d);e=this.convertValueType(a,e);var b=this.get(d);if(b==e){return}if(a==e){if(this.isDirty(d)){delete this.changed[this.currentId][d]}this.fireEvent("changed",d,e,b);return}else{this.changed[this.currentId][d]=e;this.fireEvent("changed",d,e,b)}}}}});
/*
 * Deluge.OtherLimitWindow.js
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
Ext.ns("Deluge");Deluge.OtherLimitWindow=Ext.extend(Ext.Window,{layout:"fit",width:210,height:100,closeAction:"hide",initComponent:function(){Deluge.OtherLimitWindow.superclass.initComponent.call(this);this.form=this.add({xtype:"form",baseCls:"x-plain",bodyStyle:"padding: 5px",layout:"hbox",layoutConfig:{pack:"start"},items:[{xtype:"spinnerfield",name:"limit"}]});if(this.initialConfig.unit){this.form.add({border:false,baseCls:"x-plain",bodyStyle:"padding: 5px",html:this.initialConfig.unit})}else{this.setSize(180,100)}this.addButton(_("Cancel"),this.onCancelClick,this);this.addButton(_("Ok"),this.onOkClick,this);this.afterMethod("show",this.doFocusField,this)},setValue:function(a){this.form.getForm().setValues({limit:a})},onCancelClick:function(){this.form.getForm().reset();this.hide()},onOkClick:function(){var a={};a[this.group]=this.form.getForm().getValues().limit;deluge.client.core.set_config(a,{success:function(){deluge.ui.update()}});this.hide()},doFocusField:function(){this.form.getForm().findField("limit").focus(true,10)}});
/*
 * Deluge.Plugin.js
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
Ext.ns("Deluge");Deluge.Plugin=Ext.extend(Ext.util.Observable,{name:null,constructor:function(a){this.isDelugePlugin=true;this.addEvents({enabled:true,disabled:true});Deluge.Plugin.superclass.constructor.call(this,a)},disable:function(){this.fireEvent("disabled",this);if(this.onDisable){this.onDisable()}},enable:function(){deluge.client.reloadMethods();this.fireEvent("enable",this);if(this.onEnable){this.onEnable()}},registerTorrentStatus:function(b,f,a){a=a||{};var e=a.colCfg||{},d=a.storeCfg||{};d=Ext.apply(d,{name:b});deluge.torrents.meta.fields.push(d);deluge.torrents.getStore().reader.onMetaChange(deluge.torrents.meta);e=Ext.apply(e,{header:f,dataIndex:b});var c=deluge.torrents.columns.slice(0);c.push(e);deluge.torrents.colModel.setConfig(c);deluge.torrents.columns=c;Deluge.Keys.Grid.push(b);deluge.torrents.getView().refresh(true)},deregisterTorrentStatus:function(b){var a=[];Ext.each(deluge.torrents.meta.fields,function(e){if(e.name!=b){a.push(e)}});deluge.torrents.meta.fields=a;deluge.torrents.getStore().reader.onMetaChange(deluge.torrents.meta);var d=[];Ext.each(deluge.torrents.columns,function(e){if(e.dataIndex!=b){d.push(e)}});deluge.torrents.colModel.setConfig(d);deluge.torrents.columns=d;var c=[];Ext.each(Deluge.Keys.Grid,function(e){if(e==b){c.push(e)}});Deluge.Keys.Grid=c;deluge.torrents.getView().refresh(true)}});Ext.ns("Deluge.plugins");
/*
 * Deluge.RemoveWindow.js
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
Deluge.RemoveWindow=Ext.extend(Ext.Window,{title:_("Remove Torrent"),layout:"fit",width:350,height:100,buttonAlign:"right",closeAction:"hide",closable:true,iconCls:"x-deluge-remove-window-icon",plain:true,bodyStyle:"padding: 5px; padding-left: 10px;",html:"Are you sure you wish to remove the torrent (s)?",initComponent:function(){Deluge.RemoveWindow.superclass.initComponent.call(this);this.addButton(_("Cancel"),this.onCancel,this);this.addButton(_("Remove With Data"),this.onRemoveData,this);this.addButton(_("Remove Torrent"),this.onRemove,this)},remove:function(a){Ext.each(this.torrentIds,function(b){deluge.client.core.remove_torrent(b,a,{success:function(){this.onRemoved(b)},scope:this,torrentId:b})},this)},show:function(a){Deluge.RemoveWindow.superclass.show.call(this);this.torrentIds=a},onCancel:function(){this.hide();this.torrentIds=null},onRemove:function(){this.remove(false)},onRemoveData:function(){this.remove(true)},onRemoved:function(a){deluge.events.fire("torrentRemoved",a);this.hide();deluge.ui.update()}});deluge.removeWindow=new Deluge.RemoveWindow();
/*
 * Deluge.Sidebar.js
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
Deluge.Sidebar=Ext.extend(Ext.Panel,{panels:{},selected:null,constructor:function(a){a=Ext.apply({id:"sidebar",region:"west",cls:"deluge-sidebar",title:_("Filters"),layout:"accordion",split:true,width:200,minSize:100,collapsible:true,margins:"5 0 0 5",cmargins:"5 0 0 5"},a);Deluge.Sidebar.superclass.constructor.call(this,a)},initComponent:function(){Deluge.Sidebar.superclass.initComponent.call(this);deluge.events.on("disconnect",this.onDisconnect,this)},createFilter:function(c,b){var a=new Deluge.FilterPanel({filter:c});a.on("selectionchange",function(d,e){deluge.ui.update()});this.add(a);this.doLayout();this.panels[c]=a;a.header.on("click",function(d){if(!deluge.config.sidebar_multiple_filters){deluge.ui.update()}if(!a.list.getSelectionCount()){a.list.select(0)}});this.fireEvent("filtercreate",this,a);a.updateStates(b);this.fireEvent("afterfiltercreate",this,a)},getFilter:function(a){return this.panels[a]},getFilterStates:function(){var b={};if(deluge.config.sidebar_multiple_filters){this.items.each(function(d){var e=d.getState();if(e==null){return}b[d.filterType]=e},this)}else{var a=this.getLayout().activeItem;if(a){var c=a.getState();if(!c==null){return}b[a.filterType]=c}}return b},hasFilter:function(a){return(this.panels[a])?true:false},onDisconnect:function(){for(var a in this.panels){this.remove(this.panels[a])}this.panels={};this.selected=null},onFilterSelect:function(b,c,a){deluge.ui.update()},update:function(c){for(var b in c){var a=c[b];if(Ext.getKeys(this.panels).indexOf(b)>-1){this.panels[b].updateStates(a)}else{this.createFilter(b,a)}}Ext.each(Ext.keys(this.panels),function(d){if(Ext.keys(c).indexOf(d)==-1){this.remove(this.panels[d]);this.doLayout();delete this.panels[d]}},this)}});
/*
 * Deluge.Statusbar.js
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
Ext.namespace("Deluge");Deluge.Statusbar=Ext.extend(Ext.ux.StatusBar,{constructor:function(a){a=Ext.apply({id:"deluge-statusbar",defaultIconCls:"x-deluge-statusbar x-not-connected",defaultText:_("Not Connected")},a);Deluge.Statusbar.superclass.constructor.call(this,a)},initComponent:function(){Deluge.Statusbar.superclass.initComponent.call(this);deluge.events.on("connect",this.onConnect,this);deluge.events.on("disconnect",this.onDisconnect,this)},createButtons:function(){this.buttons=this.add({id:"statusbar-connections",text:" ",cls:"x-btn-text-icon",iconCls:"x-deluge-connections",tooltip:_("Connections"),menu:new Deluge.StatusbarMenu({items:[{text:"50",value:"50",group:"max_connections_global",checked:false},{text:"100",value:"100",group:"max_connections_global",checked:false},{text:"200",value:"200",group:"max_connections_global",checked:false},{text:"300",value:"300",group:"max_connections_global",checked:false},{text:"500",value:"500",group:"max_connections_global",checked:false},{text:_("Unlimited"),value:"-1",group:"max_connections_global",checked:false},"-",{text:_("Other"),value:"other",group:"max_connections_global",checked:false}],otherWin:{title:_("Set Maximum Connections")}})},"-",{id:"statusbar-downspeed",text:" ",cls:"x-btn-text-icon",iconCls:"x-deluge-downloading",tooltip:_("Download Speed"),menu:new Deluge.StatusbarMenu({items:[{value:"5",text:"5 KiB/s",group:"max_download_speed",checked:false},{value:"10",text:"10 KiB/s",group:"max_download_speed",checked:false},{value:"30",text:"30 KiB/s",group:"max_download_speed",checked:false},{value:"80",text:"80 KiB/s",group:"max_download_speed",checked:false},{value:"300",text:"300 KiB/s",group:"max_download_speed",checked:false},{value:"-1",text:_("Unlimited"),group:"max_download_speed",checked:false},"-",{value:"other",text:_("Other"),group:"max_download_speed",checked:false}],otherWin:{title:_("Set Maximum Download Speed"),unit:_("Kib/s")}})},"-",{id:"statusbar-upspeed",text:" ",cls:"x-btn-text-icon",iconCls:"x-deluge-seeding",tooltip:_("Upload Speed"),menu:new Deluge.StatusbarMenu({items:[{value:"5",text:"5 KiB/s",group:"max_upload_speed",checked:false},{value:"10",text:"10 KiB/s",group:"max_upload_speed",checked:false},{value:"30",text:"30 KiB/s",group:"max_upload_speed",checked:false},{value:"80",text:"80 KiB/s",group:"max_upload_speed",checked:false},{value:"300",text:"300 KiB/s",group:"max_upload_speed",checked:false},{value:"-1",text:_("Unlimited"),group:"max_upload_speed",checked:false},"-",{value:"other",text:_("Other"),group:"max_upload_speed",checked:false}],otherWin:{title:_("Set Maximum Upload Speed"),unit:_("Kib/s")}})},"-",{id:"statusbar-traffic",text:" ",cls:"x-btn-text-icon",iconCls:"x-deluge-traffic",tooltip:_("Protocol Traffic Download/Upload"),handler:function(){deluge.preferences.show();deluge.preferences.selectPage("Network")}},"-",{id:"statusbar-dht",text:" ",cls:"x-btn-text-icon",iconCls:"x-deluge-dht",tooltip:_("DHT Nodes")},"-",{id:"statusbar-freespace",text:" ",cls:"x-btn-text-icon",iconCls:"x-deluge-freespace",tooltip:_("Freespace in download location"),handler:function(){deluge.preferences.show();deluge.preferences.selectPage("Downloads")}});this.created=true},onConnect:function(){this.setStatus({iconCls:"x-connected",text:""});if(!this.created){this.createButtons()}else{Ext.each(this.buttons,function(a){a.show();a.enable()})}this.doLayout()},onDisconnect:function(){this.clearStatus({useDefaults:true});Ext.each(this.buttons,function(a){a.hide();a.disable()});this.doLayout()},update:function(b){if(!b){return}function c(d){return d+" KiB/s"}var a=function(f,e){var g=this.items.get("statusbar-"+f);if(e.limit.value>0){var h=(e.value.formatter)?e.value.formatter(e.value.value,true):e.value.value;var d=(e.limit.formatter)?e.limit.formatter(e.limit.value,true):e.limit.value;var i=String.format(e.format,h,d)}else{var i=(e.value.formatter)?e.value.formatter(e.value.value,true):e.value.value}g.setText(i);if(!g.menu){return}g.menu.setValue(e.limit.value)}.createDelegate(this);a("connections",{value:{value:b.num_connections},limit:{value:b.max_num_connections},format:"{0} ({1})"});a("downspeed",{value:{value:b.download_rate,formatter:Deluge.Formatters.speed},limit:{value:b.max_download,formatter:c},format:"{0} ({1})"});a("upspeed",{value:{value:b.upload_rate,formatter:Deluge.Formatters.speed},limit:{value:b.max_upload,formatter:c},format:"{0} ({1})"});a("traffic",{value:{value:b.download_protocol_rate,formatter:Deluge.Formatters.speed},limit:{value:b.upload_protocol_rate,formatter:Deluge.Formatters.speed},format:"{0}/{1}"});this.items.get("statusbar-dht").setText(b.dht_nodes);this.items.get("statusbar-freespace").setText(fsize(b.free_space))}});
/*
 * Deluge.Toolbar.js
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
Deluge.Toolbar=Ext.extend(Ext.Toolbar,{constructor:function(a){a=Ext.apply({items:[{id:"tbar-deluge-text",disabled:true,text:_("Deluge"),iconCls:"x-deluge-main-panel"},new Ext.Toolbar.Separator(),{id:"create",disabled:true,hidden:true,text:_("Create"),iconCls:"icon-create",handler:this.onTorrentAction},{id:"add",disabled:true,text:_("Add"),iconCls:"icon-add",handler:this.onTorrentAdd},{id:"remove",disabled:true,text:_("Remove"),iconCls:"icon-remove",handler:this.onTorrentAction},new Ext.Toolbar.Separator(),{id:"pause",disabled:true,text:_("Pause"),iconCls:"icon-pause",handler:this.onTorrentAction},{id:"resume",disabled:true,text:_("Resume"),iconCls:"icon-resume",handler:this.onTorrentAction},new Ext.Toolbar.Separator(),{id:"up",cls:"x-btn-text-icon",disabled:true,text:_("Up"),iconCls:"icon-up",handler:this.onTorrentAction},{id:"down",disabled:true,text:_("Down"),iconCls:"icon-down",handler:this.onTorrentAction},new Ext.Toolbar.Separator(),{id:"preferences",text:_("Preferences"),iconCls:"x-deluge-preferences",handler:this.onPreferencesClick,scope:this},{id:"connectionman",text:_("Connection Manager"),iconCls:"x-deluge-connection-manager",handler:this.onConnectionManagerClick,scope:this},"->",{id:"help",iconCls:"icon-help",text:_("Help"),handler:this.onHelpClick,scope:this},{id:"logout",iconCls:"icon-logout",disabled:true,text:_("Logout"),handler:this.onLogout,scope:this}]},a);Deluge.Toolbar.superclass.constructor.call(this,a)},connectedButtons:["add","remove","pause","resume","up","down"],initComponent:function(){Deluge.Toolbar.superclass.initComponent.call(this);deluge.events.on("connect",this.onConnect,this);deluge.events.on("login",this.onLogin,this)},onConnect:function(){Ext.each(this.connectedButtons,function(a){this.items.get(a).enable()},this)},onDisconnect:function(){Ext.each(this.connectedButtons,function(a){this.items.get(a).disable()},this)},onLogin:function(){this.items.get("logout").enable()},onLogout:function(){this.items.get("logout").disable();deluge.login.logout()},onConnectionManagerClick:function(){deluge.connectionManager.show()},onHelpClick:function(){window.open("http://dev.deluge-torrent.org/wiki/UserGuide")},onPreferencesClick:function(){deluge.preferences.show()},onTorrentAction:function(c){var b=deluge.torrents.getSelections();var a=[];Ext.each(b,function(d){a.push(d.id)});switch(c.id){case"remove":deluge.removeWindow.show(a);break;case"pause":case"resume":deluge.client.core[c.id+"_torrent"](a,{success:function(){deluge.ui.update()}});break;case"up":case"down":deluge.client.core["queue_"+c.id](a,{success:function(){deluge.ui.update()}});break}},onTorrentAdd:function(){deluge.add.show()}});
/*
 * Deluge.TorrentGrid.js
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
(function(){function c(k){return(k==-1)?"":k+1}function f(l,m,k){return String.format('<div class="torrent-name x-deluge-{0}">{1}</div>',k.data.state.toLowerCase(),l)}function g(k){if(!k){return}return fspeed(k)}function i(k){if(k==-1){return""}return fspeed(k*1024)}function j(o,q,n){o=new Number(o);var k=o;var s=n.data.state+" "+o.toFixed(2)+"%";if(this.style){var m=this.style}else{var m=q.style}var l=new Number(m.match(/\w+:\s*(\d+)\w+/)[1]);return Deluge.progressBar(o,l-8,s)}function a(l,m,k){if(k.data.total_seeds>-1){return String.format("{0} ({1})",l,k.data.total_seeds)}else{return l}}function e(l,m,k){if(k.data.total_peers>-1){return String.format("{0} ({1})",l,k.data.total_peers)}else{return l}}function b(l,m,k){return(l<0)?"&infin;":parseFloat(new Number(l).toFixed(3))}function d(l,m,k){return String.format('<div style="background: url('+deluge.config.base+'tracker/{0}) no-repeat; padding-left: 20px;">{0}</div>',l)}function h(k){return k*-1}Deluge.TorrentGrid=Ext.extend(Ext.grid.GridPanel,{torrents:{},columns:[{id:"queue",header:_("#"),width:30,sortable:true,renderer:c,dataIndex:"queue"},{id:"name",header:_("Name"),width:150,sortable:true,renderer:f,dataIndex:"name"},{header:_("Size"),width:75,sortable:true,renderer:fsize,dataIndex:"total_wanted"},{header:_("Progress"),width:150,sortable:true,renderer:j,dataIndex:"progress"},{header:_("Down Speed"),width:80,sortable:true,renderer:g,dataIndex:"download_payload_rate"},{header:_("Up Speed"),width:80,sortable:true,renderer:g,dataIndex:"upload_payload_rate"},{header:_("ETA"),width:60,sortable:true,renderer:ftime,dataIndex:"eta"},{header:_("Seeders"),hidden:true,width:60,sortable:true,renderer:a,dataIndex:"num_seeds"},{header:_("Peers"),hidden:true,width:60,sortable:true,renderer:e,dataIndex:"num_peers"},{header:_("Ratio"),hidden:true,width:60,sortable:true,renderer:b,dataIndex:"ratio"},{header:_("Avail"),hidden:true,width:60,sortable:true,renderer:b,dataIndex:"distributed_copies"},{header:_("Added"),hidden:true,width:80,sortable:true,renderer:fdate,dataIndex:"time_added"},{header:_("Tracker"),hidden:true,width:120,sortable:true,renderer:d,dataIndex:"tracker_host"},{header:_("Save Path"),hidden:true,width:120,sortable:true,renderer:fplain,dataIndex:"save_path"},{header:_("Downloaded"),hidden:true,width:75,sortable:true,renderer:fsize,dataIndex:"total_done"},{header:_("Uploaded"),hidden:true,width:75,sortable:true,renderer:fsize,dataIndex:"total_uploaded"},{header:_("Down Limit"),hidden:true,width:75,sortable:true,renderer:i,dataIndex:"max_download_speed"},{header:_("Up Limit"),hidden:true,width:75,sortable:true,renderer:i,dataIndex:"max_upload_speed"},{header:_("Seeders")+"/"+_("Peers"),hidden:true,width:75,sortable:true,renderer:b,dataIndex:"seeds_peers_ratio"}],meta:{root:"torrents",idProperty:"id",fields:[{name:"queue",sortType:Deluge.data.SortTypes.asQueuePosition},{name:"name",sortType:Deluge.data.SortTypes.asName},{name:"total_wanted",type:"int"},{name:"state"},{name:"progress",type:"float"},{name:"num_seeds",type:"int"},{name:"total_seeds",type:"int"},{name:"num_peers",type:"int"},{name:"total_peers",type:"int"},{name:"download_payload_rate",type:"int"},{name:"upload_payload_rate",type:"int"},{name:"eta",type:"int",sortType:h},{name:"ratio",type:"float"},{name:"distributed_copies",type:"float"},{name:"time_added",type:"int"},{name:"tracker_host"},{name:"save_path"},{name:"total_done",type:"int"},{name:"total_uploaded",type:"int"},{name:"max_download_speed",type:"int"},{name:"max_upload_speed",type:"int"},{name:"seeds_peers_ratio",type:"float"}]},keys:[{key:"a",ctrl:true,stopEvent:true,handler:function(){deluge.torrents.getSelectionModel().selectAll()}},{key:[46],stopEvent:true,handler:function(){ids=deluge.torrents.getSelectedIds();deluge.removeWindow.show(ids)}}],constructor:function(k){k=Ext.apply({id:"torrentGrid",store:new Ext.data.JsonStore(this.meta),columns:this.columns,keys:this.keys,region:"center",cls:"deluge-torrents",stripeRows:true,autoExpandColumn:"name",autoExpandMin:150,deferredRender:false,autoScroll:true,margins:"5 5 0 0",stateful:true,view:new Ext.ux.grid.BufferView({rowHeight:26,scrollDelay:false})},k);Deluge.TorrentGrid.superclass.constructor.call(this,k)},initComponent:function(){Deluge.TorrentGrid.superclass.initComponent.call(this);deluge.events.on("torrentRemoved",this.onTorrentRemoved,this);deluge.events.on("disconnect",this.onDisconnect,this);this.on("rowcontextmenu",function(k,n,m){m.stopEvent();var l=k.getSelectionModel();if(!l.isSelected(n)){l.selectRow(n)}deluge.menus.torrent.showAt(m.getPoint())})},getTorrent:function(k){return this.getStore().getAt(k)},getSelected:function(){return this.getSelectionModel().getSelected()},getSelections:function(){return this.getSelectionModel().getSelections()},getSelectedId:function(){return this.getSelectionModel().getSelected().id},getSelectedIds:function(){var k=[];Ext.each(this.getSelectionModel().getSelections(),function(l){k.push(l.id)});return k},update:function(o,m){var q=this.getStore();if(m){q.removeAll();this.torrents={}}var p=[];for(var r in o){var u=o[r];if(this.torrents[r]){var n=q.getById(r);n.beginEdit();for(var l in u){if(n.get(l)!=u[l]){n.set(l,u[l])}}n.endEdit()}else{var n=new Deluge.data.Torrent(u);n.id=r;this.torrents[r]=1;p.push(n)}}q.add(p);q.each(function(k){if(!o[k.id]){q.remove(k);delete this.torrents[k.id]}},this);q.commitChanges();var s=q.getSortState();if(!s){return}q.sort(s.field,s.direction)},onDisconnect:function(){this.getStore().removeAll();this.torrents={}},onTorrentRemoved:function(l){var k=this.getSelectionModel();Ext.each(l,function(n){var m=this.getStore().getById(n);if(k.isSelected(m)){k.deselectRow(this.getStore().indexOf(m))}this.getStore().remove(m);delete this.torrents[n]},this)}});deluge.torrents=new Deluge.TorrentGrid()})();
/*
 * Deluge.UI.js
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
deluge.ui={errorCount:0,filters:null,initialize:function(){deluge.add=new Deluge.add.AddWindow();deluge.details=new Deluge.details.DetailsPanel();deluge.connectionManager=new Deluge.ConnectionManager();deluge.editTrackers=new Deluge.EditTrackersWindow();deluge.login=new Deluge.LoginWindow();deluge.preferences=new Deluge.preferences.PreferencesWindow();deluge.sidebar=new Deluge.Sidebar();deluge.statusbar=new Deluge.Statusbar();deluge.toolbar=new Deluge.Toolbar();this.detailsPanel=new Ext.Panel({id:"detailsPanel",cls:"detailsPanel",region:"south",split:true,height:215,minSize:100,collapsible:true,margins:"0 5 5 5",cmargins:"0 5 5 5",layout:"fit",items:[deluge.details]});this.MainPanel=new Ext.Panel({id:"mainPanel",iconCls:"x-deluge-main-panel",layout:"border",border:false,tbar:deluge.toolbar,items:[deluge.sidebar,this.detailsPanel,deluge.torrents],bbar:deluge.statusbar});this.Viewport=new Ext.Viewport({layout:"fit",items:[this.MainPanel]});deluge.events.on("connect",this.onConnect,this);deluge.events.on("disconnect",this.onDisconnect,this);deluge.events.on("PluginDisabledEvent",this.onPluginDisabled,this);deluge.events.on("PluginEnabledEvent",this.onPluginEnabled,this);deluge.client=new Ext.ux.util.RpcClient({url:deluge.config.base+"json"});for(var a in Deluge.pluginStore){a=Deluge.createPlugin(a);a.enable();deluge.plugins[a.name]=a}Ext.QuickTips.init();deluge.client.on("connected",function(b){deluge.login.show()},this,{single:true});this.update=this.update.createDelegate(this);this.checkConnection=this.checkConnection.createDelegate(this);this.originalTitle=document.title},checkConnection:function(){deluge.client.web.connected({success:this.onConnectionSuccess,failure:this.onConnectionError,scope:this})},update:function(){var a=deluge.sidebar.getFilterStates();this.oldFilters=this.filters;this.filters=a;deluge.client.web.update_ui(Deluge.Keys.Grid,a,{success:this.onUpdate,failure:this.onUpdateError,scope:this});deluge.details.update()},onConnectionError:function(a){},onConnectionSuccess:function(a){deluge.statusbar.setStatus({iconCls:"x-deluge-statusbar icon-ok",text:_("Connection restored")});clearInterval(this.checking);if(!a){deluge.connectionManager.show()}},onUpdateError:function(a){if(this.errorCount==2){Ext.MessageBox.show({title:"Lost Connection",msg:"The connection to the webserver has been lost!",buttons:Ext.MessageBox.OK,icon:Ext.MessageBox.ERROR});deluge.events.fire("disconnect");deluge.statusbar.setStatus({text:"Lost connection to webserver"});this.checking=setInterval(this.checkConnection,2000)}this.errorCount++},onUpdate:function(a){if(!a.connected){deluge.connectionManager.disconnect(true);return}if(deluge.config.show_session_speed){document.title="D: "+fsize_short(a.stats.download_rate,true)+" U: "+fsize_short(a.stats.upload_rate,true)+" - "+this.originalTitle}if(Ext.areObjectsEqual(this.filters,this.oldFilters)){deluge.torrents.update(a.torrents)}else{deluge.torrents.update(a.torrents,true)}deluge.statusbar.update(a.stats);deluge.sidebar.update(a.filters);this.errorCount=0},onConnect:function(){if(!this.running){this.running=setInterval(this.update,2000);this.update()}deluge.client.web.get_plugins({success:this.onGotPlugins,scope:this})},onDisconnect:function(){this.stop()},onGotPlugins:function(a){Ext.each(a.enabled_plugins,function(b){if(deluge.plugins[b]){return}deluge.client.web.get_plugin_resources(b,{success:this.onGotPluginResources,scope:this})},this)},onPluginEnabled:function(a){if(deluge.plugins[a]){deluge.plugins[a].enable()}else{deluge.client.web.get_plugin_resources(a,{success:this.onGotPluginResources,scope:this})}},onGotPluginResources:function(b){var a=(Deluge.debug)?b.debug_scripts:b.scripts;Ext.each(a,function(c){Ext.ux.JSLoader({url:deluge.config.base+c,onLoad:this.onPluginLoaded,pluginName:b.name})},this)},onPluginDisabled:function(a){if(deluge.plugins[a]){deluge.plugins[a].disable()}},onPluginLoaded:function(a){if(!Deluge.hasPlugin(a.pluginName)){return}plugin=Deluge.createPlugin(a.pluginName);plugin.enable();deluge.plugins[plugin.name]=plugin},stop:function(){if(this.running){clearInterval(this.running);this.running=false;deluge.torrents.getStore().removeAll()}}};Ext.onReady(function(a){deluge.ui.initialize()});