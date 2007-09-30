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

//http://userscripts.org/scripts/show/12639
//This script is based on : "Add Torrents To utorrent" by Julien Couvreur
//Thanks Julian!
//modified by:
//mvoncken
//these 2 parameters need to be edited before using the script

// Server address
var host = "localhost";

// Server port
var port = "8112";

if (host == "") { alert('You need to configure the "Add Torrents To Deluge" user script with your uTorrent WebUI parameters before using it.'); }



function scanLinks() {
  var links = getLinks();

  for (var i=0; i < links.length; i++){
      var link = links[i];
      if (match(link.href)) {
          var uTorrentLink = makeUTorrentLink(link);

          link.parentNode.insertBefore(uTorrentLink, link.nextSibling);
      }
  }
}

function makeUTorrentLink(link) {
    var uTorrentLink = document.createElement('a');
    uTorrentLink.setAttribute("href", makeUTorrentUrl(link.href));
    uTorrentLink.setAttribute("target", "_blank");
    uTorrentLink.style.paddingLeft = "5px";
    uTorrentLink.innerHTML = "<img src=\"" + image + "\" style='border: 0px' />";

    return uTorrentLink;
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

function makeUTorrentUrl(url) {
   var uTorrentUrl = "http://"+host+":"+port+"/torrent/add?redir_after_login=1";
   return uTorrentUrl + "&url=" + escape(url);
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
