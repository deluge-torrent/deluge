# Setting up Deluge with VPN

There are two basic options when using VPN.

1. Use the VPN as the primary connection with default routing passing through the VPN. This way all the traffic from the host uses the VPN.
2. Use the VPN connection only for specific traffic. All network traffic passes through the default interface except for the traffic you specifically want to route through the VPN interface.

Routing only specific traffic through the VPN interface can be useful, but is also the most tricky to configure.

## Linux

Directing only some traffic through the VPN interface can be achieved using iptables. There are two different solutions:

1. Route all traffic from a specific user (i.e. traffic from all processes owned by a specific user) through the VPN interface.
2. Route all traffic that matches specific ports or protocols

### Route all traffic from a specific user

By marking all packets produced by processes owned by a specific user, it is not necessary to add filters on the type of traffic that should be routed.

Scripts for a basic setup can be found at [the deluge-vpn repo](https://github.com/bendikro/deluge-vpn).


## FreeBSD with VPN

FreeBSD supports multiple routing tables (FIBs) in the kernel, which enables processes to be started with separate (non-default) routing table. This can be utilized to run deluge p2p traffic through a VPN tunnel.

### Setting up multiple routing tables (FIBs)

From FreeBSD 12, it's no longer necessary to recompile the kernel to enable multi-FIB support.
It can be enabled as follows:

Add this to /boot/loader.conf

```
 net.fibs=2
```

And this to /etc/sysctl.conf to prevent all your routing commands from affecting ALL fibs by default.

```
 net.add_addr_allfibs=0
```

Now reboot FreeBSD.

### OpenVPN
Using openvpn you can set up the alternate routing table automatically:

#### UP/DOWN scripts
Create /usr/local/etc/openvpn/link-up.sh with the following content:

```
 #!/bin/sh

 vpn_iface=$1
 vpn_ip=$4

 IFACE=em0
 FIB_NUM=1

 # If route_vpn_gateway=1.2.3.4 VPN_NETWORK_CIDR should be 1.2.3.0/24
 VPN_NETWORK_CIDR=$(echo ${route_vpn_gateway} | cut -d"." -f1-3).0/24
 LOCAL_NETWORK_CIDR=$(echo ${route_net_gateway} | cut -d"." -f1-3).0/24

 # Route all VPN traffic to tun0 interface
 /usr/sbin/setfib $FIB_NUM /sbin/route add ${VPN_NETWORK_CIDR} -iface ${vpn_iface}
 # Setup default route to VPN gateway
 /usr/sbin/setfib $FIB_NUM /sbin/route add default ${route_vpn_gateway}

 # Route all local traffic to em0 interface
 # Ensures local traffic. e.g. connections from deluge client from local network is routed
 # back to correct interface
 # This is also required if you have your router as DNS resolver in /etc/resolv.conf
 /usr/sbin/setfib $FIB_NUM /sbin/route add ${LOCAL_NETWORK_CIDR} -iface ${IFACE}
```

And Create /usr/local/etc/openvpn/link-down.sh with the following content:

```
 #!/bin/sh

 vpn_iface=$1
 vpn_ip=$4

 IFACE=em0
 FIB_NUM=1

 # If route_vpn_gateway=1.2.3.4 VPN_NETWORK_CIDR should be 1.2.3.0/24
 LOCAL_NETWORK_CIDR=$(echo ${route_net_gateway} | cut -d"." -f1-3).0/24

 # We only clean up routes we added to em0.
 # tun0 routes are removed automatically when interface goes down
 echo "Cleaning up routing table"

 # Remove rule that routes all local traffic to em0 interface
 /usr/sbin/setfib $FIB_NUM /sbin/route delete ${LOCAL_NETWORK_CIDR} -iface ${IFACE}
```

Make the scripts executable:

```
 chmod u+x /usr/local/etc/openvpn/link-up.sh
 chmod u+x /usr/local/etc/openvpn/link-down.sh
```

#### OpenVPN config
Add the following lines to the openvpn config file:

```
 script-security 2 # allow scripts to be run
 route-noexec # prevent default route being added to main routing table
 up-restart # up scripts are run on restart as well
 up "/usr/local/etc/openvpn/link-up.sh"
 down "/usr/local/etc/openvpn/link-down.sh"
```

Now test by running openvpn manually and see the output from the up/down scripts

```
 $ openvpn --config /usr/local/etc/openvpn/openvpn.conf
```

#### Verify and run====
Verify the routing table content:

```
$ setfib 1 netstat -rn
```

Test DNS resolution with traceroute:

```
$ setfib 1 traceroute www.google.com
```

### Run deluge on new FIB
Now you can run deluged on the new routing table with:

```
 $ setfib 1 deluged -L info -i tun0 -o tun0
```

## Windows 10

1. few openvpn clients can
2. bind to interface address
3. PRO and Enterprise versions


### Route traffic of specific programs

The least traumatic [lazy] way to achieve *Split Tunneling* is a branded OpenVPN client of a Tier1 paid provider. By my estimates fewer than 10% offer this feature reliably.

### Route traffic through TUN via program options

Alternatively use the Deluge UI:  options, network, address.  Find the [non routable] address of the TUN adapter to enter there.  It seems to accept wildcard character asterisk in lieu of a number for octet, i.e., 10.*.*.*

### Group Policy

https://www.reddit.com/r/HomeNetworking/comments/6wykcf/openvpn_split_tunnel_on_windows/dmc94ze/

Local Computer Policy -> Computer Configuration -> Windows Settings -> Policy-Based QoS

You can set Unique DSCP marks on a Per-User, Per-Application, Per-Source, Per-Destination or Per-Protocol | Port basis. These DSCP marks [can be specified in Deluge preferences: network: TOS].

