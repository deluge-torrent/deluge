/*
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

#


all javascript is optional, everything should work web 1.0
but javascript may/will enhance the experience.
i'm not a full time web-dev so don't expect beautifull patterns.
There's so much crap out there,i can't find good examples.
so i'd rather start from scratch,
Probably broken in an unexpected way , but worksforme.
*/

/*fix IE:*/
if(!Array.indexOf){
    Array.prototype.indexOf = function(obj){
	for(var i=0; i<this.length; i++){
	    if(this[i]==obj){
		return i;
	    }
	}
	return -1;
    }
}
/*/fix IE*/

state = {
	'row_js_continue':true,
	'selected_rows': new Array(),
	'base_url':''
};

function $(el_id){
	return document.getElementById(el_id)
}
function el(el_id){
	return document.getElementById(el_id)
}
function get_row(id){
	return $('torrent_' + id);
}

function on_click_row(e,id) {
	/*filter out web 1.0 events for detail-link and pause*/
	if (state.row_js_continue) {
	    on_click_action(e,id);
	}
	state.row_js_continue = true;
}

function on_click_row_js(e, id) {
	/*real onClick event*/
	if (!e.ctrlKey) {
		deselect_all_rows();
		select_row(id);
		open_inner_details(id);
	}
	else if (state.selected_rows.indexOf(id) != -1) {
		deselect_row(id);
	}
	else{
		select_row(id);
		open_inner_details(id);
	}
}

function select_row(id){
	var row = get_row(id);
	if (row) {
		if (!(row.default_class_name)) {
			row.default_class_name = row.className;
		}
		row.className = 'torrent_table_selected';
		state.selected_rows[state.selected_rows.length] = id;
		setCookie('selected_rows',state.selected_rows);
		return true;
	}
	return false;
}

function deselect_row(id){
	var row = get_row(id);
	if (row) {
	    row.className = row.default_class_name
	    /*remove from state.selected_rows*/
	    var idx = state.selected_rows.indexOf(id);
	    state.selected_rows.splice(idx,1);
	    setCookie('selected_rows',state.selected_rows);
	}
}

function deselect_all_rows(){
	/*unbind state.selected_rows from for..in:
	there must be a better way to do this*/
	var a = new Array()
	for (i in state.selected_rows) {
	    a[a.length] = state.selected_rows[i];
	}
	for (i in a){
		deselect_row(a[i]);
	}
}

function select_all_rows(){
    torrents = torrent_table.torrents
	for (i in torrents){
		select_row(torrents[i]);
	}
}


function reselect_rows(){
	var selected = false;
	var selected_rows = getCookie('selected_rows').split(',');
 	for (i in getCookie('selected_rows')) {
		if (select_row(selected_rows[i])) {
			selected = true;
		}
	}
	if (!selected) {
		/*select 1st*/
		select_row(torrent_table.torrents[0]);
	}
}

function open_details(e, id){
	alert(id);
	window.location.href = '/torrent/info/' + id;
}

function open_inner_details(id){
	/*probably broken for IE, use FF!*/
	$('torrent_info').src = state.base_url + '/torrent/info_inner/' + id;
}

function on_click_do_nothing(e, id){
}

on_click_action = on_click_do_nothing;

/*toobar buttons,  */
function toolbar_post(url, selected) {
	if ((!selected) || (state.selected_rows.length > 0)) {
		var ids = state.selected_rows.join(',');
		var ids = state.selected_rows.join(',');
		var form = $('toolbar_form');
		form.action = url  +ids;
		form.submit();
	}
	return false;
}

function toolbar_get(url , selected) {
	if (!selected) {
		window.location.href = url
	}
	else if (state.selected_rows.length > 0) {
		var ids = state.selected_rows.join(',');
		window.location.href = url  +ids;
	}
	return false;
}


/*arrow-navigation*/
torrent_table = {}
torrent_table.select_prev = function () {
	//torrent_tab
	var prev_id = state.selected_rows[0];
	var i = torrent_table.torrents.indexOf(prev_id);
	var id = torrent_table.torrents[i - 1];
	deselect_all_rows();
	select_row(id);
	open_inner_details(id);
}
torrent_table.select_next = function () {
	var prev_id = state.selected_rows[0];
	var i = torrent_table.torrents.indexOf(prev_id);
	var id = torrent_table.torrents[i + 1];
	deselect_all_rows();
	select_row(id);
	open_inner_details(id);
}
torrent_table.keydown = function (oEvent) {
    switch(oEvent.keyCode) {
        case 38: //up arrow
            torrent_table.select_prev();
            break;
        case 40: //down arrow
            torrent_table.select_next();
            break;
    }
};


/*stuff copied from various places:*/
/*http://www.w3schools.com/js/js_cookies.asp*/
function setCookie(c_name,value,expiredays)
{
	var exdate=new Date()
	exdate.setDate(exdate.getDate()+expiredays)
	document.cookie=c_name+ "=" +escape(value)+
	((expiredays==null) ? "" : ";expires="+exdate.toGMTString())
}

function getCookie(c_name)
{
if (document.cookie.length>0)
  {
  c_start=document.cookie.indexOf(c_name + "=")
  if (c_start!=-1)
    {
    c_start=c_start + c_name.length+1
    c_end=document.cookie.indexOf(";",c_start)
    if (c_end==-1) c_end=document.cookie.length
    return unescape(document.cookie.substring(c_start,c_end))
    }
  }
return ""
}
