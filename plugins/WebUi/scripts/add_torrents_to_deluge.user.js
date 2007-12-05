// ==UserScript==
// @name            Add Torrents To Deluge
// @namespace       http://blog.monstuff.com/archives/cat_greasemonkey.html
// @description     Let's you add torrents to the deluge WebUi
// @include         http://isohunt.com/torrent_details/*
// @include         http://thepiratebay.org/details.php?*
// @include         http://torrentreactor.net/view.php?*
// @include         http://www.mininova.org/*
// @include         http://www.torrentspy.com/*
// @include         http://ts.searching.com/*
// @include         *
// ==/UserScript==

//url-based submit and parsing based on : "Add Torrents To utorrent" by Julien Couvreur
//binary magic,contains from http://mgran.blogspot.com/2006/08/downloading-binary-streams-with.html

//these parameters need to be edited before using the script

// Server address
var host = "localhost";
// Server port
var port = "8112";
//open_page: "_blank" for a new window or "deluge_webui" for window re-use
//(not for private=1)
var open_page = "_blank"
//Private-trackers 0/1
//different behavior, gets torrent-data from (private) site and pops up a message.
var private_submit  = 1;
//deluge_password, only needed if private_submit = 1.
var deluge_password = 'deluge';
//========================


if (host == "") { alert('You need to configure the "Add Torrents To Deluge" user script with your WebUI parameters before using it.'); }



function scanLinks() {
  var links = getLinks();

  for (var i=0; i < links.length; i++){
      var link = links[i];
      if (match(link.href)) {
	if (private_submit) {
		makeUTorrentLink_private(link,i);
	}
	else {
		makeUTorrentLink(link);
	}
      }
  }
}

function makeUTorrentLink(link) {
    var uTorrentLink = document.createElement('a');
    uTorrentLink.setAttribute("href", makeUTorrentUrl(link.href));
    uTorrentLink.setAttribute("target", open_page);
    uTorrentLink.style.paddingLeft = "5px";
    uTorrentLink.innerHTML = "<img src=\"" + image + "\" style='border: 0px' />";
    link.parentNode.insertBefore(uTorrentLink, link.nextSibling);
    return uTorrentLink
}

function makeUTorrentUrl(url) {
   var uTorrentUrl = "http://"+host+":"+port+"/torrent/add?redir_after_login=1";
   return uTorrentUrl + "&url=" + escape(url);
}

function makeUTorrentLink_private(link,i) {
    var id = 'deluge_link' + i;
    var uTorrentLink = document.createElement('a');
    uTorrentLink.setAttribute("href", '#');
    uTorrentLink.setAttribute("id", id);
    uTorrentLink.style.paddingLeft = "5px";
    uTorrentLink.innerHTML = "<img src=\"" + image + "\" style='border: 0px' />";
    link.parentNode.insertBefore(uTorrentLink, link.nextSibling);

    ulink = document.getElementById(id)
    ulink.addEventListener("click", evt_private_submit_factory(link.href),false);

    return uTorrentLink
}

function evt_private_submit_factory(url) {
	//can this be done without magic?
	function evt_private_submit(evt) {
		GM_xmlhttpRequest({ method: 'GET', url: url,
			overrideMimeType: 'text/plain; charset=x-user-defined',
			onload: function(xhr)  {
				var stream = translateToBinaryString(xhr.responseText);
				var data_b64 = window.btoa(stream);
				post_to_webui(url, data_b64);
			},
			onerror:function(xhr) {
				alert('error fetching torrent file');
			}
		});
		return false;
	}
	return evt_private_submit;
}


function post_to_webui(url,data_b64){
	//alert('here1');
	//data contains the content of the .torrent-file.
	var POST_data = ('pwd=' + encodeURIComponent(deluge_password) +
		'&torrent_name=' + encodeURIComponent(url) +  '.torrent' +  //+.torrent is a clutch!
		'&data_b64=' + encodeURIComponent(data_b64) );
	//alert(POST_data);

	GM_xmlhttpRequest({ method: 'POST',
			url: "http://"+host+":"+port+"/remote/torrent/add",
			headers:{'Content-type':'application/x-www-form-urlencoded'},
			data: POST_data,
			onload: function(xhr)  {
				if (xhr.responseText == 'ok\n') {
					alert('Added torrent to webui : \n' + url);
				}
				else {
					alert('Error adding torrent to webui:\n"' + xhr.responseText + '"');
				}

			},
			onerror:function(xhr) {
				alert('error submitting torrent file');
			}

		});
}





function match(url) {

   // isohunt format
   if (url.match(/http:\/\/.*isohunt\.com\/download\//i)) {
       return true;
   }

   if (url.match(/\.torrent$/)) {
       return true;
   }

   if (url.match(/http:\/\/.*bt-chat\.com\/download\.php/)) {
       return true;
   }

   // TorrentReactor
   if (url.match(/http:\/\/dl\.torrentreactor\.net\/download.php\?/i)) {
       return true;
   }

   // Mininova
   if (url.match(/http:\/\/www\.mininova\.org\/get\//i)) {
       return true;
   }

   // Mininova
   if (url.match(/http:\/\/www\.mininova\.org\/get\//i)) {
       return true;
   }

   // TorrentSpy
   if (url.match(/http:\/\/ts\.searching\.com\/download\.asp\?/i)) {
       return true;
   }
   if (url.match(/http:\/\/www\.torrentspy\.com\/download.asp\?/i)) {
       return true;
   }

   // Seedler
   if (url.match(/http:\/\/.*seedler\.org\/download\.x\?/i)) {
       return true;
   }
   return false;
}


function getLinks() {
   var doc_links = document.links;
   var links = new Array();
   for (var i=0; i < doc_links.length; i++){
       links.push(doc_links[i]);
   }
   return links;
}

var image = "data:image/gif;base64,R0lGODlhEAAQAMZyAB1CdihAYx5CdiBEeCJGeSZJfChKfChLfSpPgTBRgThRdDRUgzRVhDVWhDZWhThYhjtbiD1ciD5diT5eiz9eikBeiUFeiT5fjT1gjkBfjERijkdjiUhljkVnlEdolUxokExqkk5qkU9rklBrklFtk1BullFulk5vmlZymFx3nE97rVZ5pUx8sl54nlt5oVl6pE5/tWJ6nVp9qFqArWOEq1uIuW6EpGCItl2Ku26Gp2KKuGuIrF+MvWaLtl+Nv3KJqG+KrGaOu2aQv2SRwnGOs2uQvGqSwICOpoCQqm6Ww3OVvHKWv3iWuoKWsn+XtnacxXaeynifyXigzICewn2gxnqizoqfunujzpWesX6l0IyivYijw4+jvpOiuoOp0puktY2x2I6y2Y+z2pG02pW43Ze42pa43Z/A4qjG56jH56nI6KzJ6a/M67nR67zW8sLa9cff+M/k+P///////////////////////////////////////////////////////yH+FUNyZWF0ZWQgd2l0aCBUaGUgR0lNUAAh+QQBCgB/ACwAAAAAEAAQAAAHkIB/goOEhYaCX1iHhkdIXU2LgzFARExbkYInCBcvRVSRHgQNEiYoPUmHGAkjO1FSSilBNYYQFTllY2BeSzJChg4iWmhpZ2JXOjgqhBMFH1xvbmtmWUMwM4QZBws/cXBsZFU+LCuFDwIhVm1qYVA8Nx2FEQQDHDZOU09GNIcWDAAGFEC0cBEpwAYNJUgowMQwEAA7";

scanLinks();

/*
binary magic,contains code taken from
http://mgran.blogspot.com/2006/08/downloading-binary-streams-with.html
*/
function translateToBinaryString(text){
	var out;
	out='';
	for(i=0;i<text.length;i++){
		//*bugfix* by Marcus Granado 2006 [http://mgran.blogspot.com] adapted by Thomas Belot
		out+=String.fromCharCode(text.charCodeAt(i) & 0xff);
	}
	return out;
}