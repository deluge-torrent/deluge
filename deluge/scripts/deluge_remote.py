<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
 <title>#382: deluge_config.py - Deluge - Trac</title><link rel="start" href="/wiki" /><link rel="search" href="/search" /><link rel="help" href="/wiki/TracGuide" /><link rel="stylesheet" href="/trac/css/trac.css" type="text/css" /><link rel="stylesheet" href="/trac/css/code.css" type="text/css" /><link rel="icon" href="/chrome/common/trac.ico" type="image/x-icon" /><link rel="shortcut icon" href="/chrome/common/trac.ico" type="image/x-icon" /><link rel="up" href="/ticket/382" title="Ticket #382" /><link rel="alternate" href="/attachment/ticket/382/deluge_config.py?format=raw" title="Original Format" type="text/x-python; charset=iso-8859-15" /><style type="text/css">
</style>
 <script type="text/javascript" src="/trac/js/trac.js"></script>
</head>
<body>

<head>
<link href="http://dev.deluge-torrent.org/chrome/common/deluge-specific.css" rel="stylesheet" type="text/css" />
</head>
<body>
<div id="headerd">
  <div id="headerd-inner">
    <div id="delugelogo">
      <h1 id="delugetext"><a href="http://deluge-torrent.org/">Deluge <span id="msg_to_news">(return to news &amp; home)</span></a></h1>
    </div>
    <ul id="navbar">
        <!--[if gte IE 6]>
        <li><img src="chrome/common/spacer.gif" width="20"></li>
        <![endif]-->
      <li><a href="http://deluge-torrent.org/about.php">About</a></li>
      <li><a href="http://deluge-torrent.org/downloads.php">Download</a></li>
      <li><a href="http://forum.deluge-torrent.org/">Community</a></li>
      <li><a href="http://dev.deluge-torrent.org/" class="currenttab">Development</a></li>
      <li><a href="http://deluge-torrent.org/faq.php">FAQ</a></li>
      <li><a href="http://deluge-torrent.org/screenshots.php">Screenshots</a></li>
      <li><a href="http://deluge-torrent.org/plugin-list.php">Plugins</a></li>
    </ul>
  </div>
</div>

<div id="banner">

<div id="header"><a id="logo" href="http://dev.deluge-torrent.org/"><img src="/chrome/common/trac_banner.png" alt="" /></a><hr /></div>

<form id="search" action="/search" method="get">
 <div>
  <label for="proj-search">Search:</label>
  <input type="text" id="proj-search" name="q" size="10" accesskey="f" value="" />
  <input type="submit" value="Search" />
  <input type="hidden" name="wiki" value="on" />
  <input type="hidden" name="changeset" value="on" />
  <input type="hidden" name="ticket" value="on" />
 </div>
</form>



<div id="metanav" class="nav"><ul><li class="first">logged in as mvoncken</li><li><a href="/logout">Logout</a></li><li><a href="/settings">Settings</a></li><li><a accesskey="6" href="/wiki/TracGuide">Help/Guide</a></li><li class="last"><a href="/about">About Trac</a></li></ul></div>
</div>

<div id="mainnav" class="nav"><ul><li class="first"><a accesskey="1" href="/wiki">Wiki</a></li><li><a accesskey="2" href="/timeline">Timeline</a></li><li><a accesskey="3" href="/roadmap">Roadmap</a></li><li><a href="/browser">Browse Source</a></li><li><a href="/report">View Tickets</a></li><li><a accesskey="7" href="/newticket">New Ticket</a></li><li class="last"><a accesskey="4" href="/search">Search</a></li></ul></div>
<div id="main">




<div id="ctxtnav" class="nav"></div>

<div id="content" class="attachment">


 <h1><a href="/ticket/382">Ticket #382</a>: deluge_config.py</h1>
 <table id="info" summary="Description"><tbody><tr>
   <th scope="col">
    File deluge_config.py, 3.8 kB 
    (added by garett@zy.ca,  2 days ago)
   </th></tr><tr>
   <td class="message"><p>
Script to alter configuration settings on the deluge backend
</p>
</td>
  </tr>
 </tbody></table>
 <div id="preview">
   <table class="code"><thead><tr><th class="lineno">Line</th><th class="content">&nbsp;</th></tr></thead><tbody><tr><th id="L1"><a href="#L1">1</a></th>
<td>#!/usr/bin/python</td>
</tr><tr><th id="L2"><a href="#L2">2</a></th>
<td>#</td>
</tr><tr><th id="L3"><a href="#L3">3</a></th>
<td># This software is in the public domain, furnished &#34;as is&#34;, without technical</td>
</tr><tr><th id="L4"><a href="#L4">4</a></th>
<td># support, and with no warranty, express or implied, as to its usefulness for</td>
</tr><tr><th id="L5"><a href="#L5">5</a></th>
<td># any purpose.</td>
</tr><tr><th id="L6"><a href="#L6">6</a></th>
<td>#</td>
</tr><tr><th id="L7"><a href="#L7">7</a></th>
<td># deluge_config.py</td>
</tr><tr><th id="L8"><a href="#L8">8</a></th>
<td># This code (at least in theory) allows one to alter configuration settings</td>
</tr><tr><th id="L9"><a href="#L9">9</a></th>
<td># on a deluge backend.&nbsp; &nbsp;At the moment, though, it only alters the parameters</td>
</tr><tr><th id="L10"><a href="#L10">10</a></th>
<td># that I've found useful to change.</td>
</tr><tr><th id="L11"><a href="#L11">11</a></th>
<td>#</td>
</tr><tr><th id="L12"><a href="#L12">12</a></th>
<td># Authour: Garett Harnish</td>
</tr><tr><th id="L13"><a href="#L13">13</a></th>
<td></td>
</tr><tr><th id="L14"><a href="#L14">14</a></th>
<td>from sys import argv, exit, stderr</td>
</tr><tr><th id="L15"><a href="#L15">15</a></th>
<td>from optparse import OptionParser</td>
</tr><tr><th id="L16"><a href="#L16">16</a></th>
<td></td>
</tr><tr><th id="L17"><a href="#L17">17</a></th>
<td>import logging</td>
</tr><tr><th id="L18"><a href="#L18">18</a></th>
<td></td>
</tr><tr><th id="L19"><a href="#L19">19</a></th>
<td>def isFloatDigit (string):</td>
</tr><tr><th id="L20"><a href="#L20">20</a></th>
<td>&nbsp; &nbsp; if string.isdigit():</td>
</tr><tr><th id="L21"><a href="#L21">21</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; return True</td>
</tr><tr><th id="L22"><a href="#L22">22</a></th>
<td>&nbsp; &nbsp; else:</td>
</tr><tr><th id="L23"><a href="#L23">23</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; try:</td>
</tr><tr><th id="L24"><a href="#L24">24</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; tmp = float(string)</td>
</tr><tr><th id="L25"><a href="#L25">25</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; return True</td>
</tr><tr><th id="L26"><a href="#L26">26</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; except: return False;</td>
</tr><tr><th id="L27"><a href="#L27">27</a></th>
<td></td>
</tr><tr><th id="L28"><a href="#L28">28</a></th>
<td># set up command-line options</td>
</tr><tr><th id="L29"><a href="#L29">29</a></th>
<td>parser = OptionParser()</td>
</tr><tr><th id="L30"><a href="#L30">30</a></th>
<td>parser.add_option(&#34;--port&#34;, help=&#34;port for deluge backend host (default: 58846)&#34;, default=&#34;58846&#34;, dest=&#34;port&#34;)</td>
</tr><tr><th id="L31"><a href="#L31">31</a></th>
<td>parser.add_option(&#34;--host&#34;, help=&#34;hostname of deluge backend to connect to (default: localhost)&#34;, default=&#34;localhost&#34;, dest=&#34;host&#34;)</td>
</tr><tr><th id="L32"><a href="#L32">32</a></th>
<td>parser.add_option(&#34;--max_active_limit&#34;, help=&#34;sets the absolute maximum number of active torrents on the deluge backend&#34;, dest=&#34;max_active_limit&#34;)</td>
</tr><tr><th id="L33"><a href="#L33">33</a></th>
<td>parser.add_option(&#34;--max_active_downloading&#34;, help=&#34;sets the maximum number of active downloading torrents on the deluge backend&#34;, dest=&#34;max_active_downloading&#34;)</td>
</tr><tr><th id="L34"><a href="#L34">34</a></th>
<td>parser.add_option(&#34;--max_active_seeding&#34;, help=&#34;sets the maximum number of active seeding torrents on the deluge backend&#34;, dest=&#34;max_active_seeding&#34;)</td>
</tr><tr><th id="L35"><a href="#L35">35</a></th>
<td>parser.add_option(&#34;--max_download_speed&#34;, help=&#34;sets the maximum global download speed on the deluge backend&#34;, dest=&#34;max_download_speed&#34;)</td>
</tr><tr><th id="L36"><a href="#L36">36</a></th>
<td>parser.add_option(&#34;--max_upload_speed&#34;, help=&#34;sets the maximum global upload speed on the deluge backend&#34;, dest=&#34;max_upload_speed&#34;)</td>
</tr><tr><th id="L37"><a href="#L37">37</a></th>
<td>parser.add_option(&#34;--debug&#34;, help=&#34;outputs debug information to the console&#34;, default=False, action=&#34;store_true&#34;, dest=&#34;debug&#34;)</td>
</tr><tr><th id="L38"><a href="#L38">38</a></th>
<td></td>
</tr><tr><th id="L39"><a href="#L39">39</a></th>
<td># grab command-line options</td>
</tr><tr><th id="L40"><a href="#L40">40</a></th>
<td>(options, args) = parser.parse_args()</td>
</tr><tr><th id="L41"><a href="#L41">41</a></th>
<td></td>
</tr><tr><th id="L42"><a href="#L42">42</a></th>
<td>if not options.debug:</td>
</tr><tr><th id="L43"><a href="#L43">43</a></th>
<td>&nbsp; &nbsp; logging.disable(logging.ERROR)</td>
</tr><tr><th id="L44"><a href="#L44">44</a></th>
<td></td>
</tr><tr><th id="L45"><a href="#L45">45</a></th>
<td>settings = {}</td>
</tr><tr><th id="L46"><a href="#L46">46</a></th>
<td></td>
</tr><tr><th id="L47"><a href="#L47">47</a></th>
<td># set values if set and valid</td>
</tr><tr><th id="L48"><a href="#L48">48</a></th>
<td>if options.max_active_limit:</td>
</tr><tr><th id="L49"><a href="#L49">49</a></th>
<td>&nbsp; &nbsp; if options.max_active_limit.isdigit() and int(options.max_active_limit) &gt;= 0:</td>
</tr><tr><th id="L50"><a href="#L50">50</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; settings['max_active_limit'] = int(options.max_active_limit)</td>
</tr><tr><th id="L51"><a href="#L51">51</a></th>
<td>&nbsp; &nbsp; else:</td>
</tr><tr><th id="L52"><a href="#L52">52</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; stderr.write (&#34;ERROR: Invalid max_active_limit parameter!\n&#34;)</td>
</tr><tr><th id="L53"><a href="#L53">53</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; exit (-1)</td>
</tr><tr><th id="L54"><a href="#L54">54</a></th>
<td></td>
</tr><tr><th id="L55"><a href="#L55">55</a></th>
<td>if options.max_active_downloading:</td>
</tr><tr><th id="L56"><a href="#L56">56</a></th>
<td>&nbsp; &nbsp; if options.max_active_downloading.isdigit() and int(options.max_active_downloading) &gt;= 0:</td>
</tr><tr><th id="L57"><a href="#L57">57</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; settings['max_active_downloading'] = int(options.max_active_downloading)</td>
</tr><tr><th id="L58"><a href="#L58">58</a></th>
<td>&nbsp; &nbsp; else:</td>
</tr><tr><th id="L59"><a href="#L59">59</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; stderr.write (&#34;ERROR: Invalid max_active_downloading parameter!\n&#34;)</td>
</tr><tr><th id="L60"><a href="#L60">60</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; exit (-1)</td>
</tr><tr><th id="L61"><a href="#L61">61</a></th>
<td></td>
</tr><tr><th id="L62"><a href="#L62">62</a></th>
<td>if options.max_active_seeding:</td>
</tr><tr><th id="L63"><a href="#L63">63</a></th>
<td>&nbsp; &nbsp; if options.max_active_seeding.isdigit() and int(options.max_active_seeding) &gt;= 0:</td>
</tr><tr><th id="L64"><a href="#L64">64</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; settings['max_active_seeding'] = int(options.max_active_seeding)</td>
</tr><tr><th id="L65"><a href="#L65">65</a></th>
<td>&nbsp; &nbsp; else:</td>
</tr><tr><th id="L66"><a href="#L66">66</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; stderr.write (&#34;ERROR: Invalid max_active_seeding parameter!\n&#34;)</td>
</tr><tr><th id="L67"><a href="#L67">67</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; exit (-1)</td>
</tr><tr><th id="L68"><a href="#L68">68</a></th>
<td></td>
</tr><tr><th id="L69"><a href="#L69">69</a></th>
<td>if options.max_download_speed:</td>
</tr><tr><th id="L70"><a href="#L70">70</a></th>
<td>&nbsp; &nbsp; if isFloatDigit(options.max_download_speed) and (float(options.max_download_speed) &gt;= 0.0 or float(options.max_download_speed) == -1.0):</td>
</tr><tr><th id="L71"><a href="#L71">71</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; settings['max_download_speed'] = float(options.max_download_speed)</td>
</tr><tr><th id="L72"><a href="#L72">72</a></th>
<td>&nbsp; &nbsp; else:</td>
</tr><tr><th id="L73"><a href="#L73">73</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; stderr.write (&#34;ERROR: Invalid max_download_speed parameter!\n&#34;)</td>
</tr><tr><th id="L74"><a href="#L74">74</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; exit (-1)</td>
</tr><tr><th id="L75"><a href="#L75">75</a></th>
<td></td>
</tr><tr><th id="L76"><a href="#L76">76</a></th>
<td>if options.max_upload_speed:</td>
</tr><tr><th id="L77"><a href="#L77">77</a></th>
<td>&nbsp; &nbsp; if isFloatDigit(options.max_upload_speed) and (float(options.max_upload_speed) &gt;= 0.0 or float(options.max_upload_speed) == -1.0):</td>
</tr><tr><th id="L78"><a href="#L78">78</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; settings['max_upload_speed'] = float(options.max_upload_speed)</td>
</tr><tr><th id="L79"><a href="#L79">79</a></th>
<td>&nbsp; &nbsp; else:</td>
</tr><tr><th id="L80"><a href="#L80">80</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; stderr.write (&#34;ERROR: Invalid max_upload_speed parameter!\n&#34;)</td>
</tr><tr><th id="L81"><a href="#L81">81</a></th>
<td>&nbsp; &nbsp; &nbsp; &nbsp; exit (-1)</td>
</tr><tr><th id="L82"><a href="#L82">82</a></th>
<td></td>
</tr><tr><th id="L83"><a href="#L83">83</a></th>
<td># If there is something to do ...</td>
</tr><tr><th id="L84"><a href="#L84">84</a></th>
<td>if settings:</td>
</tr><tr><th id="L85"><a href="#L85">85</a></th>
<td>&nbsp; &nbsp; # create connection to daemon</td>
</tr><tr><th id="L86"><a href="#L86">86</a></th>
<td>&nbsp; &nbsp; from deluge.ui.client import sclient as client</td>
</tr><tr><th id="L87"><a href="#L87">87</a></th>
<td>&nbsp; &nbsp; client.set_core_uri(&#34;http://&#34; + options.host + &#34;:&#34; + options.port)</td>
</tr><tr><th id="L88"><a href="#L88">88</a></th>
<td></td>
</tr><tr><th id="L89"><a href="#L89">89</a></th>
<td>&nbsp; &nbsp; # commit configurations changes</td>
</tr><tr><th id="L90"><a href="#L90">90</a></th>
<td>&nbsp; &nbsp; client.set_config(settings)</td>
</tr></tbody></table>
 </div>
 


</div>
<script type="text/javascript">searchHighlight()</script>
<div id="altlinks"><h3>Download in other formats:</h3><ul><li class="first last"><a href="/attachment/ticket/382/deluge_config.py?format=raw">Original Format</a></li></ul></div>

</div>

<div id="footer">
 <hr />
 <a id="tracpowered" href="http://trac.edgewall.org/"><img src="/trac/trac_logo_mini.png" height="30" width="107"
   alt="Trac Powered"/></a>
 <p class="left">
  Powered by <a href="/about"><strong>Trac 0.10.3.1</strong></a><br />
  By <a href="http://www.edgewall.org/">Edgewall Software</a>.
 </p>
 <p class="right">
  Visit the Trac open source project at<br /><a href="http://trac.edgewall.org/">http://trac.edgewall.org/</a>
 </p>
</div>



 </body>
</html>

