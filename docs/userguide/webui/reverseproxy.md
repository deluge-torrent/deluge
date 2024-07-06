# Reverse Proxy with Deluge WebUI

A reverse proxy is where there is an existing http web server (Apache, Nginx) that you wish Deluge WebUI to be served through. e.g. Site `http://example.net` serves the WebUI at `http://example.net/deluge`.

In the configurations below `deluge-web` is running on `localhost` with default port `8112` and reverse proxy url suffix `/deluge`.

 Apache Config: ::

 Enable the following apache modules:

 ```
 a2enmod proxy
 a2enmod proxy_html
 a2enmod proxy_http
 a2enmod headers
```

 And add the following to your `.conf` file:

 ```
 ProxyPass /deluge http://localhost:8112/
 
 <Location /deluge>
     ProxyPassReverse /
     ProxyPassReverseCookiePath / /deluge               
     RequestHeader set X-Deluge-Base "/deluge/"          
     Order allow,deny
     Allow from all
 </Location>
```

 Nginx Config: ::

```
location /deluge {
    proxy_pass http://localhost:8112/;
    proxy_set_header X-Deluge-Base "/deluge/";
    include proxy-control.conf;
    add_header X-Frame-Options SAMEORIGIN;
}
```

 *Note: Ensure the trailing slashes are maintained.*

 lighttpd Config: ::
You will need to install `lua` >= 5.1 and make sure `lighttpd` >= 1.4.12 is compiled with lua support. Lua will perform URL rewriting since lighty doesn't support it natively.

```
server.modules += ( "mod_proxy", "mod_magnet", "mod_setenv" )
$HTTP["url"] =~ "^/deluge/" {
    setenv.add-request-header = ( "X-Deluge-Base" => "/deluge/" )
    magnet.attract-raw-url-to = ( "/etc/lighttpd/lua/deluge.lua" )
    proxy.server = ( "" => ( "deluge" => ( "host" => "127.0.0.1", "port" => 8112 ) ) )
```

`/etc/lighttpd/lua/deluge.lua` contains:

```
lighty.env["request.uri"] = string.sub(lighty.env["request.uri"], string.len('/deluge/'))
return
```

 HAProxy Config: ::

```
frontend https
        bind *:443 ssl crt /etc/haproxy/certs/<YOUR-PEM-HERE>
        compression algo gzip
        default_backend <DEFAULT-BACKEND-HERE>
        use_backend Deluge if { path_beg /deluge }

backend Deluge
        server deluge localhost:8112
        reqrep ^([^\ ]*\ /)deluge[/]?(.*)     \1\2
        http-request add-header X-Deluge-Base /deluge
        http-request add-header X-Frame-Options SAMEORIGIN
```


 IIS Config: ::
Assuming IIS is already setup for reverse proxying (plenty of tutorials on this online).
Under site -> **URL Rewrite**, click on **View Server Variables...** and add a new variable name **HTTP_X_Deluge_Base**.
Then open your **web.config** file and add/edit your rule as follow (edit url to match your setup):

```
<rule name="Deluge" stopProcessing="true">
    <match url="deluge\/?(.*)" />
    <action type="Rewrite" url="http://1.1.1.1:8112/{R:1}" />
    <serverVariables>
        <set name="HTTP_X_Deluge_Base" value="/deluge/" />
    </serverVariables>
</rule>
```
