#include<stdlib.h>
#include<stdio.h>
#include"nodavesimple.h"
#include"openSocket.h"

int main(int argc) 
{
    int a,b,c,res;
    float d;
    daveInterface * di;
    daveConnection * dc;
    _daveOSserialType fds;
    
    daveSetDebug(daveDebugPrintErrors);
 
 if (argc<2) 
 {
	printf("Usage: testISO_TCP IP-Address of CP\n");
	exit(-1);
    }    
    
    fds.rfd=openSocket(102, "192.168.18.17");
    fds.wfd=fds.rfd;
    
    if (fds.rfd>0) 
	{ 
	di =daveNewInterface(fds,"IF1",0, daveProtoISOTCP, daveSpeed187k);
	daveSetTimeout(di,5000000);
	dc =daveNewConnection(di,2,0, 2);  // insert your rack and slot here
	
	if (0==daveConnectPLC(dc)) {
	    printf("Connected.\n");

	res=daveReadBytes(dc,daveFlags,0,0,16,NULL);
	if (0==res) { 
    	    a=daveGetU32(dc);
    	    b=daveGetU32(dc);
    	    c=daveGetU32(dc);
    	    d=daveGetFloat(dc);
	    printf("FD0: %d\n",a);
	    printf("FD4: %d\n",b);
	    printf("FD8: %d\n",c);
	    printf("FD12: %f\n",d);
	}  else 
	    printf("failed! (%d)\n",res);  

	printf("Finished.\n");
	return 0;
	} else {
	    printf("Couldn't connect to PLC.\n");	
	    return -2;
	}
    } else {
	printf("Couldn't open TCP port. \nPlease make sure a CP is connected and the IP address is ok. \n");	
    	return -1;
    }    
}
