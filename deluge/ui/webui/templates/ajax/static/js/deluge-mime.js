/*
Script: deluge-mime.js
    Library for converting mimetypes to extensions and vica versa.

 *
 * Copyright (C) Damien Churchill 2008 <damoxc@gmail.com>
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

 *


    Object: Deluge.Mime
        Object containing all mime related functions.

*/

Deluge.Mime = {
    types_map: new Hash({
        '.doc':      'application/msword',
        '.dot':      'application/msword',
        '.wiz':      'application/msword',
        '.a':        'application/octet-stream',
        '.bin':      'application/octet-stream',
        '.dll':      'application/octet-stream',
        '.exe':      'application/octet-stream',
        '.o':        'application/octet-stream',
        '.obj':      'application/octet-stream',
        '.so':       'application/octet-stream',
        '.oda':      'application/oda',
        '.pdf':      'application/pdf',
        '.p7c':      'application/pkcs7-mime',
        '.ai':       'application/postscript',
        '.eps':      'application/postscript',
        '.ps':       'application/postscript',
        '.xlb':      'application/vnd.ms-excel',
        '.xls':      'application/vnd.ms-excel',
        '.pot':      'application/vnd.ms-powerpoint',
        '.ppa':      'application/vnd.ms-powerpoint',
        '.pps':      'application/vnd.ms-powerpoint',
        '.ppt':      'application/vnd.ms-powerpoint',
        '.pwz':      'application/vnd.ms-powerpoint',
        '.bcpio':    'application/x-bcpio',
        '.cpio':     'application/x-cpio',
        '.csh':      'application/x-csh',
        '.dvi':      'application/x-dvi',
        '.gtar':     'application/x-gtar',
        '.hdf':      'application/x-hdf',
        '.js':       'application/x-javascript',
        '.latex':    'application/x-latex',
        '.mif':      'application/x-mif',
        '.cdf':      'application/x-netcdf',
        '.nc':       'application/x-netcdf',
        '.p12':      'application/x-pkcs12',
        '.pfx':      'application/x-pkcs12',
        '.ram':      'application/x-pn-realaudio',
        '.pyc':      'application/x-python-code',
        '.pyo':      'application/x-python-code',
        '.sh':       'application/x-sh',
        '.shar':     'application/x-shar',
        '.swf':      'application/x-shockwave-flash',
        '.sv4cpio':  'application/x-sv4cpio',
        '.sv4crc':   'application/x-sv4crc',
        '.tar':      'application/x-tar',
        '.tcl':      'application/x-tcl',
        '.tex':      'application/x-tex',
        '.texi':     'application/x-texinfo',
        '.texinfo':  'application/x-texinfo',
        '.roff':     'application/x-troff',
        '.t':        'application/x-troff',
        '.tr':       'application/x-troff',
        '.man':      'application/x-troff-man',
        '.me':       'application/x-troff-me',
        '.ms':       'application/x-troff-ms',
        '.ustar':    'application/x-ustar',
        '.src':      'application/x-wais-source',
        '.rdf':      'application/xml',
        '.wsdl':     'application/xml',
        '.xpdl':     'application/xml',
        '.xsl':      'application/xml',
        '.zip':      'application/zip',
        '.au':       'audio/basic',
        '.snd':      'audio/basic',
        '.mp2':      'audio/mpeg',
        '.mp3':      'audio/mpeg',
        '.aif':      'audio/x-aiff',
        '.aifc':     'audio/x-aiff',
        '.aiff':     'audio/x-aiff',
        '.ra':       'audio/x-pn-realaudio',
        '.wav':      'audio/x-wav',
        '.gif':      'image/gif',
        '.ief':      'image/ief',
        '.jpe':      'image/jpeg',
        '.jpeg':     'image/jpeg',
        '.jpg':      'image/jpeg',
        '.png':      'image/png',
        '.tif':      'image/tiff',
        '.tiff':     'image/tiff',
        '.ras':      'image/x-cmu-raster',
        '.bmp':      'image/x-ms-bmp',
        '.pnm':      'image/x-portable-anymap',
        '.pbm':      'image/x-portable-bitmap',
        '.pgm':      'image/x-portable-graymap',
        '.ppm':      'image/x-portable-pixmap',
        '.rgb':      'image/x-rgb',
        '.xbm':      'image/x-xbitmap',
        '.xpm':      'image/x-xpixmap',
        '.xwd':      'image/x-xwindowdump',
        '.eml':      'message/rfc822',
        '.mht':      'message/rfc822',
        '.mhtml':    'message/rfc822',
        '.nws':      'message/rfc822',
        '.css':      'text/css',
        '.htm':      'text/html',
        '.html':     'text/html',
        '.bat':      'text/plain',
        '.c':        'text/plain',
        '.h':        'text/plain',
        '.ksh':      'text/plain',
        '.pl':       'text/plain',
        '.txt':      'text/plain',
        '.rtx':      'text/richtext',
        '.tsv':      'text/tab-separated-values',
        '.py':       'text/x-python',
        '.etx':      'text/x-setext',
        '.sgm':      'text/x-sgml',
        '.sgml':     'text/x-sgml',
        '.vcf':      'text/x-vcard',
        '.xml':      'text/xml',
        '.m1v':      'video/mpeg',
        '.mpa':      'video/mpeg',
        '.mpe':      'video/mpeg',
        '.mpeg':     'video/mpeg',
        '.mpg':      'video/mpeg',
        '.mov':      'video/quicktime',
        '.qt':       'video/quicktime',
        '.avi':      'video/x-msvideo',
        '.movie':    'video/x-sgi-movie'
    }),

    getMimeType: function(filename) {
        var extension = filename.match(/^.*(\.\w+)$/)
        if (extension) extension = extension[1]
        else return null;

        if (this.types_map.has(extension)) return this.types_map[extension];
        else return null;
    }
}
