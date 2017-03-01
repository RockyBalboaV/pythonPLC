using System;
class Class1
{
	public static libnodave.daveOSserialType fds;
	public static libnodave.daveInterface di;
	public static libnodave.daveConnection dc;


	static void Main()
	{
		//int res;
		Console.WriteLine("ok!");
		fds.rfd = libnodave.openSocket(102, "192.168.18.17");
		fds.wfd = fds.rfd; 
		di = new libnodave.daveInterface(fds, "IF1", 0, libnodave.daveProtoISOTCP, libnodave.daveSpeed187k);//122Ò²¿ÉÒÔ
		//res = di.initAdapter(); 
		dc = new libnodave.daveConnection(di, 0, 0, 2);
		dc.connectPLC();

	}
}