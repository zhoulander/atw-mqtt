# ===============================
# Class WavePlus
# ===============================

import sys
import struct
from WaveGeneric import WaveGeneric
from bluepy.btle import UUID, Peripheral, Scanner, DefaultDelegate

class Wave(WaveGeneric):

    class Sensors(WaveGeneric.Sensors):

        NUMBER_OF_SENSORS               = 5

        SENSOR_IDX_DATETIME             = 0
        SENSOR_IDX_HUMIDITY             = 1
        SENSOR_IDX_TEMPERATURE          = 2
        SENSOR_IDX_RADON_SHORT_TERM_AVG = 3
        SENSOR_IDX_RADON_LONG_TERM_AVG  = 4

        SENSOR_UUID_DATETIME            = UUID(0x2A08)
        SENSOR_UUID_HUMIDITY            = UUID(0x2A6F)
        SENSOR_UUID_TEMPERATURE         = UUID(0x2A6E)
        SENSOR_UUID_RADON_STA           = UUID("b42e01aa-ade7-11e4-89d3-123b93f75cba")
        SENSOR_UUID_RADON_LTA           = UUID("b42e0a4c-ade7-11e4-89d3-123b93f75cba")


        def __init__(self):
            self.sensor_version = None
            self.sensor_data    = [None]*self.NUMBER_OF_SENSORS
            self.sensor_units   = ["", "%rH", "degC", "Bq/m3", "Bq/m3"]
            self.sensor_names   = ['Timestamp', 'Humidity', 'Temperature', 'Radon ST avg', 'Radon LT avg']
            self.sensor_classes = [None, 'humidity', 'temperature', None, None]
            self.sensor_format  = '<H5B4H'

        def set(self, rawData):
            timestamp = datetime.datetime(rawData[0], rawData[1], rawData[2], rawData[3], rawData[4], rawData[5])

            self.sensor_data[self.SENSOR_IDX_DATETIME]             = timestamp
            self.sensor_data[self.SENSOR_IDX_HUMIDITY]             = rawData[6]/100.0
            self.sensor_data[self.SENSOR_IDX_TEMPERATURE]          = rawData[7]/100.0
            self.sensor_data[self.SENSOR_IDX_RADON_SHORT_TERM_AVG] = self.conv2radon(rawData[8])
            self.sensor_data[self.SENSOR_IDX_RADON_LONG_TERM_AVG]  = self.conv2radon(rawData[9])

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
            self._datetime_char    = self.periph.getCharacteristics(uuid=self.SENSOR_UUID_DATETIME)[0]
            self._humidity_char    = self.periph.getCharacteristics(uuid=self.SENSOR_UUID_HUMIDITY)[0]
            self._temperature_char = self.periph.getCharacteristics(uuid=self.SENSOR_UUID_TEMPERATURE)[0]
            self._radon_sta_char   = self.periph.getCharacteristics(uuid=self.SENSOR_UUID_RADON_STA)[0]
            self._radon_lta_char   = self.periph.getCharacteristics(uuid=self.SENSOR_UUID_RADON_LTA)[0]


    def read(self):
        rawdata = self._datetime_char.read()
        rawdata += self._humidity_char.read()
        rawdata += self._temperature_char.read()
        rawdata += self._radon_sta_char.read()
        rawdata += self._radon_lta_char.read()
        rawdata = struct.unpack(self.sensors.sensor_format, rawdata)
        return self.sensors.set(rawdata)

