# Deluge Web UI

The Deluge web interface is a full featured interface built using the ExtJS framework,
running on top of a Twisted webserver.

## SSL Configuration

By default the web interface will use the same private key and certificate as
the Deluge daemon. You can use a different certificate/key and specify it in the Web UI
config, see below for details.

### Create SSL Certificate Examples

Sample guide: [How to Create a SSL Certificate][ssl cert]

#### Linux

    openssl req -new -x509 -nodes -out deluge.cert.pem -keyout deluge.key.pem

#### Windows

    C:\OpenSSL\bin\openssl.exe req -config C:\OpenSSL\bin\openssl.cnf -x509 -days 365 -newkey rsa:1024 -keyout hostkey.pem -nodes -out hostcert.pem

### Enable Web UI SSL

There are two ways to enable SSL encryption in the webserver:

- Specify in your config (accessible via the Preferences window).
- Use `--ssl` when running the webserver, overriding the configuration value to enable SSL.

## Enable Development mode

Add `?dev=true` to the webui url to enable development mode, uses the source js files
(if available) rather than compressed versions:

    http://127.0.0.1:8112/?dev=true

[ssl cert]: http://www.yatblog.com/2007/02/27/how-to-create-a-ssl-certificate/
