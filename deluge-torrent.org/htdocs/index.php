<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
"http://www.w3.org/TR/html4/strict.dtd">
<html> <head> <title>Deluge BitTorrent Client</title>
<meta http-equiv="Content-type" content="text/html; charset=utf-8">
<link rel="icon" type="image/png" href="images/deluge-icon.png">
<link id="mdgCss" rel="stylesheet" href="deluge_stormy_day.css" type="text/css">
<link rel="stylesheet" href="deluge_header_nav.css" type="text/css">
<script src="js/mootools.js"></script>
<script src="js/windows_dl.js"></script>
<style type="text/css">
      div#category_box_wrapper {
        display: none;
      }
      div#content-inner {
        padding: 0 0 10px 0;
      }
    </style> </head>
<body id='deluge-front-page'>

<!-- Header and Nav -->
<?php include 'deluge_header_nav.html'; ?>

<div id="content"> <div id="content-inner">
<div id="ajaxEditContainer">
<p>
<table border="0" width="100%"> 
<tr> 
<td style="width: 50%; border-right: 1px solid #485D73;"> 
<div style="white-space: nowrap;"> 
<span style="font-family: verdana, arial, helvetica, sans-serif; font-size: 34pt; font-weight: bold;"> 
Deluge  
<span style="font-size: 30pt;">
<?php echo file_get_contents('https://ftp.osuosl.org/pub/deluge/version'); ?>
<!-- <span style="font-weight: normal; font-style: italic; font-size: 50%; vertical-align: super;">
June '19
</span>-->
</span></span> 
</div> 
<div> 
<table border="0">
<tr><td style="padding-right: 10px;"><a href="/downloads.php"><img src="/images/deluge-download.gif" border="0"></a></td> <td id="deluge_download_box"><b><a style="font-size: 16pt;" href="/downloads.php">Download now</a></b><br> Available for Linux, macOS and Windows.</td> </tr>
</table> 
</div> </td> <td style="padding-left: 10px;"> <h2>What is Deluge?</h2> <p>Deluge is a lightweight, <b>Free Software</b>, <b>cross-platform</b> BitTorrent client.</p> <ul> <li>Full Encryption</li>
<li>WebUI</li> <li>Plugin System</li> <li>Much more...</li> </ul> <a href="http://dev.deluge-torrent.org">Learn More</a> </td> </tr> </table> </p>
</div><p>
</p>
</div> </div> </div>
<div id="copyright-container"> <div id="copyright">
<br>&copy; Deluge Team<br>Design by Dan Fuhry<br> <br></div>
</div>
<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write("\<script src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'>\<\/script>" );
</script>
<script type="text/javascript">
var pageTracker = _gat._getTracker("UA-8360366-2");
pageTracker._initData();
pageTracker._trackPageview();
</script>
</div>
</body>


 
</html>
