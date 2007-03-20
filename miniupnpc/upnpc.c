/* $Id: upnpc.c,v 1.49 2007/01/27 14:20:01 nanard Exp $ */
/* Project : miniupnp
 * Author : Thomas Bernard
 * Copyright (c) 2005 Thomas Bernard
 * This software is subject to the conditions detailed in the
 * LICENCE file provided in this distribution.
 * */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef WIN32
#include <winsock2.h>
#define snprintf _snprintf
#endif
#include "miniwget.h"
#include "miniupnpc.h"
#include "upnpcommands.h"

/* protofix() checks if protocol is "UDP" or "TCP" 
 * returns NULL if not */
const char * protofix(const char * proto)
{
	static const char proto_tcp[4] = { 'T', 'C', 'P', 0};
	static const char proto_udp[4] = { 'U', 'D', 'P', 0};
	int i, b;
	for(i=0, b=1; i<4; i++)
		b = b && (   (proto[i] == proto_tcp[i]) 
		          || (proto[i] == (proto_tcp[i] | 32)) );
	if(b)
		return proto_tcp;
	for(i=0, b=1; i<4; i++)
		b = b && (   (proto[i] == proto_udp[i])
		          || (proto[i] == (proto_udp[i] | 32)) );
	if(b)
		return proto_udp;
	return 0;
}

static void DisplayInfos(struct UPNPUrls * urls,
                         struct IGDdatas * data)
{
	char connectionType[64];
	char status[64];
	unsigned int uptime;
	unsigned int brUp, brDown;
	UPNP_GetConnectionTypeInfo(urls->controlURL,
	                           data->servicetype,
							   connectionType);
	if(connectionType[0])
		printf("Connection Type : %s\n", connectionType);
	else
		printf("GetConnectionTypeInfo failed.\n");
	UPNP_GetStatusInfo(urls->controlURL, data->servicetype, status, &uptime);
	printf("Status : %s, uptime=%u\n", status, uptime);
	UPNP_GetLinkLayerMaxBitRates(urls->controlURL_CIF, data->servicetype_CIF,
			&brDown, &brUp);
	printf("MaxBitRateDown : %u bps   MaxBitRateUp %u bps\n", brDown, brUp);
}

static void GetConnectionStatus(struct UPNPUrls * urls,
                               struct IGDdatas * data)
{
	unsigned int bytessent, bytesreceived, packetsreceived, packetssent;
	DisplayInfos(urls, data);
	bytessent = UPNP_GetTotalBytesSent(urls->controlURL_CIF, data->servicetype_CIF);
	bytesreceived = UPNP_GetTotalBytesReceived(urls->controlURL_CIF, data->servicetype_CIF);
	packetssent = UPNP_GetTotalPacketsSent(urls->controlURL_CIF, data->servicetype_CIF);
	packetsreceived = UPNP_GetTotalPacketsReceived(urls->controlURL_CIF, data->servicetype_CIF);
	printf("Bytes:   Sent: %8u\tRecv: %8u\n", bytessent, bytesreceived);
	printf("Packets: Sent: %8u\tRecv: %8u\n", packetssent, packetsreceived);
}

static void ListRedirections(struct UPNPUrls * urls,
                             struct IGDdatas * data)
{
	int r;
	int i = 0;
	char index[6];
	char intClient[16];
	char intPort[6];
	char extPort[6];
	char protocol[4];
	char desc[80];
	char enabled[6];
	char rHost[64];
	char duration[16];
	/*unsigned int num=0;
	UPNP_GetPortMappingNumberOfEntries(urls->controlURL, data->servicetype, &num);
	printf("PortMappingNumberOfEntries : %u\n", num);*/
	do {
		snprintf(index, 6, "%d", i);
		rHost[0] = '\0'; enabled[0] = '\0';
		duration[0] = '\0'; desc[0] = '\0';
		extPort[0] = '\0'; intPort[0] = '\0'; intClient[0] = '\0';
		r = UPNP_GetGenericPortMappingEntry(urls->controlURL, data->servicetype,
		                               index,
		                               extPort, intClient, intPort,
									   protocol, desc, enabled,
									   rHost, duration);
		if(r==0)
			printf("%02d - %s %s->%s:%s\tenabled=%s leaseDuration=%s\n"
			       "     desc='%s' rHost='%s'\n",
			       i, protocol, extPort, intClient, intPort,
				   enabled, duration,
				   desc, rHost);
		i++;
	} while(r==0);
}

/* Test function 
 * 1 - get connection type
 * 2 - get extenal ip address
 * 3 - Add port mapping
 * 4 - get this port mapping from the IGD */
static void SetRedirectAndTest(struct UPNPUrls * urls,
                               struct IGDdatas * data,
							   const char * iaddr,
							   const char * iport,
							   const char * eport,
                               const char * proto)
{
	char externalIPAddress[16];
	char intClient[16];
	char intPort[6];
	int r;

	if(!iaddr || !iport || !eport || !proto)
	{
		fprintf(stderr, "Wrong arguments\n");
		return;
	}
	proto = protofix(proto);
	if(!proto)
	{
		fprintf(stderr, "invalid protocol\n");
		return;
	}
	
	UPNP_GetExternalIPAddress(urls->controlURL,
	                          data->servicetype,
							  externalIPAddress);
	if(externalIPAddress[0])
		printf("ExternalIPAddress = %s\n", externalIPAddress);
	else
		printf("GetExternalIPAddress failed.\n");
	
	r = UPNP_AddPortMapping(urls->controlURL, data->servicetype,
	                        eport, iport, iaddr, 0, proto);
	if(r==0)
		printf("AddPortMapping(%s, %s, %s) failed\n", eport, iport, iaddr);

	UPNP_GetSpecificPortMappingEntry(urls->controlURL,
	                                 data->servicetype,
    	                             eport, proto,
									 intClient, intPort);
	if(intClient[0])
		printf("InternalIP:Port = %s:%s\n", intClient, intPort);
	else
		printf("GetSpecificPortMappingEntry failed.\n");

	printf("external %s:%s is redirected to internal %s:%s\n",
	       externalIPAddress, eport, intClient, intPort);
}

static void
RemoveRedirect(struct UPNPUrls * urls,
               struct IGDdatas * data,
			   const char * eport,
			   const char * proto)
{
	if(!proto || !eport)
	{
		fprintf(stderr, "invalid arguments\n");
		return;
	}
	proto = protofix(proto);
	if(!proto)
	{
		fprintf(stderr, "protocol invalid\n");
		return;
	}
	UPNP_DeletePortMapping(urls->controlURL, data->servicetype, eport, proto);
}


/* sample upnp client program */
int main(int argc, char ** argv)
{
	char command = 0;
	struct UPNPDev * devlist;
	char lanaddr[16];	/* my ip address on the LAN */
	int i;

#ifdef WIN32
	WSADATA wsaData;
	int nResult = WSAStartup(MAKEWORD(2,2), &wsaData);
	if(nResult != NO_ERROR)
	{
		fprintf(stderr, "WSAStartup() failed.\n");
		return -1;
	}
#endif
    printf("upnpc : miniupnp test client. (c) 2006 Thomas Bernard\n");
    printf("Go to http://miniupnp.free.fr/ or http://miniupnp.tuxfamily.org/\n"
	       "for more information.\n");
	if(argc>=2 && (argv[1][0] == '-'))
		command = argv[1][1];

	if(!command || argc<2 || (command == 'a' && argc<6)
	   || (command == 'd' && argc<4)
	   || (command == 'r' && argc<4))
	{
		fprintf(stderr, "Usage :\t%s -a ip port external_port protocol\tAdd port redirection\n", argv[0]);
		fprintf(stderr, "       \t%s -d external_port protocol\tDelete port redirection\n", argv[0]);
		fprintf(stderr, "       \t%s -s\t\t\t\tGet Connection status\n", argv[0]);
		fprintf(stderr, "       \t%s -l\t\t\t\tList redirections\n", argv[0]);
		fprintf(stderr, "       \t%s -r port1 protocol1 [port2 protocol2] [...]\n\t\t\t\tAdd all redirections to the current host\n", argv[0]);
		fprintf(stderr, "\nprotocol is UDP or TCP\n");
		return 1;
	}
	
	devlist = upnpDiscover(2000);
	if(devlist)
	{
		struct UPNPDev * device;
		struct UPNPUrls urls;
		struct IGDdatas data;
		printf("List of UPNP devices found on the network :\n");
		for(device = devlist; device; device = device->pNext)
		{
			printf("\n desc: %s\n st: %s\n",
				   device->descURL, device->st);
		}
		putchar('\n');
		if(UPNP_GetValidIGD(devlist, &urls, &data, lanaddr, sizeof(lanaddr)))
		{
			printf("Found valid IGD : %s\n", urls.controlURL);
			printf("Local LAN ip address : %s\n", lanaddr);
			#if 0
			printf("getting \"%s\"\n", urls.ipcondescURL);
			descXML = miniwget(urls.ipcondescURL, &descXMLsize);
			if(descXML)
			{
				/*fwrite(descXML, 1, descXMLsize, stdout);*/
				free(descXML); descXML = NULL;
			}
			#endif

			switch(command)
			{
			case 'l':
				DisplayInfos(&urls, &data);
				ListRedirections(&urls, &data);
				break;
			case 'a':
				SetRedirectAndTest(&urls, &data, argv[2], argv[3], argv[4], argv[5]);
				break;
			case 'd':
				RemoveRedirect(&urls, &data, argv[2], argv[3]);
				break;
			case 's':
				GetConnectionStatus(&urls, &data);
				break;
			case 'r':
				for(i=2; i<argc-1; i+=2)
				{
					/*printf("port %s protocol %s\n", argv[i], argv[i+1]);*/
					SetRedirectAndTest(&urls, &data,
					                   lanaddr, argv[i], argv[i], argv[i+1]);
				}
				break;
			default:
				fprintf(stderr, "Unknown switch -%c\n", command);
			}

			FreeUPNPUrls(&urls);
		}
		else
		{
			fprintf(stderr, "No valid UPNP Internet Gateway Device found.\n");
		}
		freeUPNPDevlist(devlist); devlist = 0;
	}
	else
	{
		fprintf(stderr, "No IGD UPnP Device found on the network !\n");
	}

	/*puts("************* HOP ***************");*/

	return 0;
}

