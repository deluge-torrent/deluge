document.addEvent('domready', function(e) {
    if (Browser.Platform.win) {
        var req = new Request({
            url: 'http://download.deluge-torrent.org/version',
            method: 'get'
        }).addEvent('onSuccess', function(version) {
            var link = $('deluge_download_box').getElement('a');
            link.set('href', 'http://download.deluge-torrent.org/windows/deluge-' + version + '-win32-py2.7-0.exe');
        }).send();
    }
});

