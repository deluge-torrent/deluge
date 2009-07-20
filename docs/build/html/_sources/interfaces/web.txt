Deluge Web UI
=============

The Deluge web interface is intended to be a full featured interface built using
the ExtJS framework, running on top of a Twisted webserver.


=================
SSL Configuration
=================
By default the web interface will use the same private key and certificate as
the Deluge daemon. If you wish to use a different certificate/key (see 
`How to Create a SSL Certificate <http://www.yatblog.com/2007/02/27/how-to-create-a-ssl-certificate/>`_
for information on creating one) you are able to specify which you want to use.

There are 2 ways to enable SSL encryption in the webserver, 1 is to specify it
in your configuration (accessible via the Preferences window). The other is to
add '--ssl' when running the webserver, which will override the configuration
value and enable SSL. 