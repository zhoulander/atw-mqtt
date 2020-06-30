# ===============================
# Class WavePlus
# ===============================

import sys
import struct
from WaveGeneric import WaveGeneric
from bluepy.btle import UUID, Peripheral, Scanner, DefaultDelegate

class WavePlus(WaveGeneric):

    class Sensors(WaveGeneric.Sensors):

        NUMBER_OF_SENSORS               = 7
        SENSOR_IDX_HUMIDITY             = 0
        SENSOR_IDX_RADON_SHORT_TERM_AVG = 1
        SENSOR_IDX_RADON_LONG_TERM_AVG  = 2
        SENSOR_IDX_TEMPERATURE          = 3
        SENSOR_IDX_REL_ATM_PRESSURE     = 4
        SENSOR_IDX_CO2_LVL              = 5
        SENSOR_IDX_VOC_LVL              = 6
        SENSOR_UUID                     = "b42e2a68-ade7-11e4-89d3-123b93f75cba"

        def __init__(self):
            self.sensor_version = None
            self.sensor_data    = [None]*self.NUMBER_OF_SENSORS
            self.sensor_units   = ["%rH", "Bq/m3", "Bq/m3", "degC", "hPa", "ppm", "ppb"]
            self.sensor_names   = ['Humidity', 'Radon ST avg', 'Radon LT avg', 'Temperature', 'Pressure', 'CO2 level', 'VOC level']
            self.sensor_classes = ['humidity', None, None, 'temperature', 'pressure', None, None]
            self.sensor_format  = 'BBBBHHHHHHHH'
            self.sensor_uuid    = UUID(self.SENSOR_UUID)

        def set(self, rawData):
            self.sensor_version = rawData[0]
            if (self.sensor_version == 1):
                self.sensor_data[self.SENSOR_IDX_HUMIDITY]             = rawData[1]/2.0
                self.sensor_data[self.SENSOR_IDX_RADON_SHORT_TERM_AVG] = self.conv2radon(rawData[4])
                self.sensor_data[self.SENSOR_IDX_RADON_LONG_TERM_AVG]  = self.conv2radon(rawData[5])
                self.sensor_data[self.SENSOR_IDX_TEMPERATURE]          = rawData[6]/100.0
                self.sensor_data[self.SENSOR_IDX_REL_ATM_PRESSURE]     = rawData[7]/50.0
                self.sensor_data[self.SENSOR_IDX_CO2_LVL]              = rawData[8]*1.0
                self.sensor_data[self.SENSOR_IDX_VOC_LVL]              = rawData[9]*1.0
            else:
                print ("ERROR: Unknown sensor version.\n")
                print ("GUIDE: Contact Airthings for support.\n")
                sys.exit(1)

