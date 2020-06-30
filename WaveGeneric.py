# ===============================
# Class WaveGeneric
# ===============================

import sys
import struct
from bluepy.btle import UUID, Peripheral, Scanner, DefaultDelegate

class WaveGeneric:

    class Sensors:

        NUMBER_OF_SENSORS               = 1


        def __init__(self):
            self.sensor_version = None
            self.sensor_data    = [None]*self.NUMBER_OF_SENSORS
            self.sensor_units   = [None]
            self.sensor_names   = [None]
            self.sensor_format  = None
            self.sensor_uuid    = None

        def getValue(self, sensor_index):
            return self.sensor_data[sensor_index]

        def getUnit(self, sensor_index):
            return self.sensor_units[sensor_index]

        def conv2radon(self, radon_raw):
            radon = "N/A" # Either invalid measurement, or not available
            if 0 <= radon_raw <= 16383:
                radon  = radon_raw
            return radon

    def __init__(self, SerialNumber, MAC = None):
        self.periph        = None
        self.curr_val_char = None
        self.MacAddr       = None
        self.SN            = SerialNumber
        self.sensors       = self.Sensors()
        self.MacAddr       = MAC

    def connect(self):
        # Auto-discover device on first connection
        if (self.MacAddr is None):
            scanner     = Scanner().withDelegate(DefaultDelegate())
            searchCount = 0
            timeout = 3
            scan_interval = 0.1
            for _count in range(int(timeout / scan_interval)):
                devices = scanner.scan(scan_interval)
                for dev in devices:
                    ManuData = dev.getValueText(255)
                    if ManuData != None:
                        SN = self.parseSerialNumber(ManuData)
                        if (SN == self.SN):
                            self.MacAddr = dev.addr # exits the while loop on next conditional check
                            break # exit for loop

            if (self.MacAddr is None):
                print ("ERROR: Could not find device. {0}".format(self.SN))
                print ("GUIDE: (1) Please verify the serial number.")
                print ("       (2) Ensure that the device is advertising.")
                print ("       (3) Retry connection.")
                sys.exit(1)

        # Connect to device
        if (self.periph is None):
            self.periph = Peripheral(self.MacAddr)
        if (self.curr_val_char is None):
            self.curr_val_char = self.periph.getCharacteristics(uuid=self.sensors.sensor_uuid)[0]

    def read(self):
        if (self.curr_val_char is None):
            print ("ERROR: Devices are not connected.")
            sys.exit(1)
        rawdata = self.curr_val_char.read()
        rawdata = struct.unpack(self.sensors.sensor_format, rawdata)
        return self.sensors.set(rawdata)

    def disconnect(self):
        if self.periph is not None:
            self.periph.disconnect()
            self.periph = None
            self.curr_val_char = None

    # =======================================
    # Utility functions for WaveGeneric class
    # =======================================

    def parseSerialNumber(self, ManuDataHexStr):
        if (ManuDataHexStr == "None"):
            SN = "Unknown"
        else:
            ManuData = bytearray.fromhex(ManuDataHexStr)

            if (((ManuData[1] << 8) | ManuData[0]) == 0x0334):
                SN  =  ManuData[2]
                SN |= (ManuData[3] << 8)
                SN |= (ManuData[4] << 16)
                SN |= (ManuData[5] << 24)
            else:
                SN = "Unknown"
        return SN

