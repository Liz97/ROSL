#! /usr/bin/python
import sys
import _thread
from bluetooth import *
import binascii
from PyQt4.QtGui import QApplication, QMainWindow
from PyQt4 import QtCore,QtGui
from ui_Car2b import Ui_MainWindow
from time import *

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        #A list of all the car objects that are currently connected
        self.listcars = []
        #Which car from the list is currently being controlled
        self.carindex = 0
        #the number of cars currently connected
        length = len(self.listcars)
        #The control state is whether all cars are being controlled (1) or only a single car(0)
        self.ControlState=0
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self, length)

        #Button Controls:
        #For example: connectPB is the name of a button created in the UI
        #self.tryToConnect is the function that happens when connectPB is pressed
        self.ui.connectPB.clicked.connect(self.tryToConnect)
        self.ui.quitPB.clicked.connect(self.quit)
        self.ui.RunPB.clicked.connect(self.Run) 
        self.ui.StopPB.clicked.connect(self.Stop)
        self.ui.CarSwitch.clicked.connect(self.carSwitch)
        self.ui.CarAll.clicked.connect(self.AllCars)
        self.ui.CarTest.clicked.connect(self.TestAll)

    #This cycles through the connected cars, changing which one is being controlled
    #It flashes the lights of the current car
    #It also sets the control state to a single car
    def carSwitch(self):
        print("CarPB clicked")
        self.carindex = (self.carindex + 1)%len(self.listcars)
        i = self.listcars[self.carindex]
        i.LightsOn()
        sleep(0.75)
        i.LightsOff()
        self.ControlState=0

    #Sets the control state all of the cars
    def AllCars(self):
        for x in self.listcars:
            x.LightsOn()
        sleep(1)
        for x in self.listcars:
            x.LightsOff()
        self.ControlState=1

    #Flashes the lights of all connected cars
    def TestAll(self):
        for x in self.listcars:
            x.LightsOn()
        sleep(1)
        for x in self.listcars:
            x.LightsOff()

    #The command for the quit button
    def quit(self):
        try:
            self.sock.close()
        except: AttributeError
        sys.exit()

    #Drives one or all cars forward        
    def Run(self):
        if self.ControlState:
            for i in self.listcars:
                i.run()
        else:
            i = self.listcars[self.carindex]
            i.run()

    #Stops one or all cars
    def Stop(self):
        if self.ControlState:
            for i in self.listcars:
                i.stop()
        else:
            i = self.listcars[self.carindex]
            i.stop()

    def tryToConnect(self):
        _thread.start_new_thread(self.updateText,())
        _thread.start_new_thread(self.connect,())

    def updateText(self):
        self.ui.lineEdit.setText("Searching all nearby bluetooth devices")

    def connect(self): 
        addr = None
        length = len(self.listcars)

        uuid = '00001101-0000-1000-8000-00805F9B34FB'
        service_matches = find_service( uuid = uuid, address = addr )

        if len(service_matches) == 0:
            self.ui.lineEdit.setText("Could not find device")
            return

        first_match = service_matches[0]
        port = first_match["port"]
        name = first_match["name"]
        host = first_match["host"]
        print(port, name, host)
        
        newcar = car(host, port, self.listcars)

        self.listcars.append(newcar)
        print("New car added")
        self.ui.lineEdit.setText("Connection established.")
        length=len(self.listcars)
        print(self.listcars)

#An object of the car class controls a specific car
#By calling functions within this class commands are sent to the car
class car:
    def __init__(self, host, port, listcars):
        self.action_dict = {'horn' : 0, 'lights' : 0, 'fault' : 0,}
        self.acceleration = 0
        self.steering = 0
        # List of available commands
        self.dict = {}
        self.dict['HORN_OFF'] = '8600'
        self.dict['HORN_ON'] = '8601'
        self.dict['LIGHTS_OFF'] = '8500'
        self.dict['LIGHTS_SOFT'] = '8501'
        self.dict['LIGHTS'] = '8502'
        self.dict['FAULT'] = ['8304',' 8404',' 8301',' 8401']
        self.dict['FAULT_OFF'] = ['8300',' 8400']
        self.dict['STEER_LEFT']=['817F','817E','817D','817C','817B','817A','8179','8178','8177','8176','8175','8174','8173','8172','8171','8170','816F','816E','816D','816C','816B','816A','8169','8168','8167','8166','8165','8164','8163','8162','8161','8160','815F','815E','815D','815C','815B','815A','8159','8158','8157','8156','8155','8154','8153','8152','8151','8150','814F','814E','814D','814C','814B','814A','8149','8148','8147','8146','8145','8144','8143','8142','8141']
        self.dict['STEER_RIGHT']=['8100','8101','8102','8103','8104','8105','8106','8107','8108','8109','810A','810B','810C','810D','810E','810F','8110','8111','8112','8113','8114','8115','8116','8117','8118','8119','811A','811B','811C','811D','811E','811F','8120','8121','8122','8123','8124','8125','8126','8127','8128','8129','812A','812B','812C','812D','812E','812F','8130','8131','8132','8133','8134','8135','8136','8137','8138','8139','813A','813B','813C','813D','813E','813F']
        self.dict['SPEED_BACK']=['827F','827E','827D','827C','827B','827A','8279','8278','8277','8276','8275','8274','8273','8272','8271','8270','826F','826E','826D','826C','826B','826A','8269','8268','8267','8266','8265','8264','8263','8262','8261','8260','825F','825E','825D','825C','825B','825A','8259','8258','8257','8256','8255','8254','8253','8252','8251','8250','824F','824E','824D','824C','824B','824A','8249','8248','8247','8246','8245','8244','8243','8242','8241']
        self.dict['SPEED_FRONT']=['8200','8201','8202','8203','8204','8205','8206','8207','8208','8209','820A','820B','820C','820D','820E','820F','8210','8211','8212','8213','8214','8215','8216','8217','8218','8219','821A','821B','821C','821D','821E','821F','8220','8221','8222','8223','8224','8225','8226','8227','8228','8229','822A','822B','822C','822D','822E','822F','8230','8231','8232','8233','8234','8235','8236','8237','8238','8239','823A','823B','823C','823D','823E','823F']
        self.dict['NO_SPEED']='8200'
        self.dict['NO_STEER'] = '8100'

        # Create the client socket
        self.sock=BluetoothSocket( RFCOMM )
        self.sock.connect((host, port))

        length = len(listcars)
        
    def horn(self):
        self.sock.send(binascii.a2b_hex(self.dict['HORN_ON']))
        sleep(0.5)
        self.sock.send(binascii.a2b_hex(self.dict['HORN_OFF']))
        
    def LightsOn(self):
        self.sock.send(binascii.a2b_hex(self.dict['LIGHTS']))
        
    def LightsOff(self):
        self.sock.send(binascii.a2b_hex(self.dict['LIGHTS_OFF']))

    def run(self):
        self.acceleration=20
        self.sock.send(binascii.a2b_hex(self.dict['SPEED_FRONT'][self.acceleration]))

    def stop(self):
        self.acceleration=0
        self.sock.send(binascii.a2b_hex(self.dict['NO_SPEED']))

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
