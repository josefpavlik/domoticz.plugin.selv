# SELV
#
# Author: Jet 2020
# based on HTML.py example
#
#
"""
<plugin key="SELV" name="SELV" author="Jet" version="0.1" externallink="">
    <description>
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true"/>
        <param field="Port" label="Port" width="75px" default="80"/>
        <param field="Mode2" label="PIN" width="75px" default=""/>
        <param field="Mode3" label="Number of lights" width="75px" default="16"/>
        <param field="Mode4" label="Polling period [s]" width="75px" default="3"/>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Python" value="18"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import os
import re 

class BasePlugin:
    httpConn = None
    runAgain = 1
    disconnectCount = 0
   
    def __init__(self):
        return

    def connection(self):
        return Domoticz.Connection(Name="GetStatus", Transport="TCP/IP", Protocol="None", Address=Parameters["Address"], Port=Parameters["Port"])
      
    def onStart(self):        
        Domoticz.Log("onStart - Plugin is starting.")
        self.pin = Parameters["Mode2"]
        self.channels=int(Parameters["Mode3"])
        self.period=int(Parameters["Mode4"])
        Domoticz.Heartbeat(self.period)
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()
               
        for x in range(len(Devices), self.channels):
            Domoticz.Device(Name="Light_"+str(x+1), Unit=x+1, TypeName="Switch", Used=1).Create()
        for x in range(self.channels,len(Devices)):
            Devices[x+1].Delete()
        try:
            temp = Devices[1].TimedOut
        except AttributeError:
            self.timeoutversion = False
        else:
            self.timeoutversion = True


    def onStop(self):
        Domoticz.Log("onStop - Plugin is stopping.")

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Debug("selv connected successfully.")
            Connection.Send("GET /*s")
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Mode1"]+" with error: "+Description)

    def onMessage(self, Connection, Data):
        strData=Data.decode("utf-8");
        if (int(Parameters["Mode6"]) & 2):
          Domoticz.Log("ON MESSAGE CALLED = "+strData)
        Status = int(re.compile(r"HTTP/1.1 ([0-9]+)").search(strData)[1])

        if (Status == 200):
            if ((self.disconnectCount & 1) == 1):
#                Domoticz.Log("Good Response received from selv, Disconnecting.")
#                self.httpConn.Disconnect()
                unused=0
            else:
#                Domoticz.Log("Good Response received from selv, Dropping connection.")
                self.httpConn = None
            self.disconnectCount = self.disconnectCount + 1
# parse result                
            lights = re.compile(r"LIGHT='([01]+)';").search(strData)[1]
            if (int(Parameters["Mode6"]) & 2):
                Domoticz.Log("decoded lights="+lights)
            self.update_lights(lights)
        elif (Status == 400):
            Domoticz.Error("selv returned a Bad Request Error.")
        elif (Status == 500):
            Domoticz.Error("selv returned a Server Error.")
        else:
            Domoticz.Error("selv returned a status: "+str(Status))

    def update_lights(self, lights):
        for i in range(0,self.channels):
            self.update_light(i+1, lights[i]=='1')
            
    def update_light(self, Unit, state):
        val=state and "1" or "0"
        if (Unit in Devices): Devices[Unit].Update(int(val),val)
    
    def onCommand(self, Unit, Command, Level, Hue):
        cmd=Command=="On" and "G" or "g"
        command="curl http://"+Parameters["Address"]+":"+Parameters["Port"]+"/"+self.pin+"p"+str(Unit-1)+cmd+" &"
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level) + " exec "+command)
        os.system(command)
#        Domoticz.Debug("done")
        self.update_light(Unit, Command=="On")

    def onDisconnect(self, Connection):
        unused=0
#        Domoticz.Log("onDisconnect called for connection to: "+Connection.Address+":"+Connection.Port)

    def onHeartbeat(self):
        self.httpConn = self.connection()
        self.httpConn.Connect()
                 
global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def LogMessage(Message):
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"]+"http.html","w")
        f.write(Message)
        f.close()
        Domoticz.Log("File written")

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def DumpHTTPResponseToLog(httpDict):
    if isinstance(httpDict, dict):
        Domoticz.Debug("HTTP Details ("+str(len(httpDict))+"):")
        for x in httpDict:
            if isinstance(httpDict[x], dict):
                Domoticz.Debug("--->'"+x+" ("+str(len(httpDict[x]))+"):")
                for y in httpDict[x]:
                    Domoticz.Debug("------->'" + y + "':'" + str(httpDict[x][y]) + "'")
            else:
                Domoticz.Debug("--->'" + x + "':'" + str(httpDict[x]) + "'")
