/*
all javascript is optional, everything should work web 1.0
but javascript may/will enhance the experience.
i'm not a full time web-dev so don't expect beautifull patterns.
There's so much crap out there,i can't find good examples.
so i'd rather start from scratch,
Probably broken in an unexpected way , but worksforme.
*/
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
	}
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

function reselect_rows(){
	var selected_rows = getCookie('selected_rows').split(',');
 	for (i in getCookie('selected_rows')) {
	    select_row(selected_rows[i]);
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