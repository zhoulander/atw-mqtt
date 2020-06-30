# ===============================
# Class WavePlus
# ===============================

import sys
import struct
from WaveGeneric import WaveGeneric
from bluepy.btle import UUID, Peripheral, Scanner, DefaultDelegate

class Wave2(WaveGeneric):

    class Sensors(WaveGeneric.Sensors):

        NUMBER_OF_SENSORS               = 4

        SENSOR_IDX_HUMIDITY             = 0
        SENSOR_IDX_RADON_SHORT_TERM_AVG = 1
        SENSOR_IDX_RADON_LONG_TERM_AVG  = 2
        SENSOR_IDX_TEMPERATURE          = 3
        SENSOR_UUID                     = 'b42e4dcc-ade7-11e4-89d3-123b93f75cba'

        def __init__(self):
            self.sensor_version = None
            self.sensor_data    = [None]*self.NUMBER_OF_SENSORS
            self.sensor_units   = ["%rH", "Bq/m3", "Bq/m3", "degC"]
            self.sensor_names   = ['Humidity', 'Radon ST avg', 'Radon LT avg', 'Temperature']
            self.sensor_classes = ['humidity', None, None, 'temperature']
            self.sensor_format  = '<4B8H'
            self.sensor_uuid    = UUID(self.SENSOR_UUID)

        def set(self, rawData):
            if rawData[0] != 1:
                raise ValueError("Incompatible current values version (Expected 1, got {})".format(rawData[0]))

            self.sensor_data[self.SENSOR_IDX_HUMIDITY]             = rawData[1]/2.0
            self.sensor_data[self.SENSOR_IDX_RADON_SHORT_TERM_AVG] = self.conv2radon(rawData[4])
            self.sensor_data[self.SENSOR_IDX_RADON_LONG_TERM_AVG]  = self.conv2radon(rawData[5])
            self.sensor_data[self.SENSOR_IDX_TEMPERATURE]          = rawData[6]/100.0

