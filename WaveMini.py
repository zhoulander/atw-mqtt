# ===============================
# Class WaveMini
# ===============================

import sys
import struct
from WaveGeneric import WaveGeneric
from bluepy.btle import UUID, Peripheral, Scanner, DefaultDelegate

class WaveMini(WaveGeneric):

    class Sensors(WaveGeneric.Sensors):

        NUMBER_OF_SENSORS               = 3
        SENSOR_IDX_TEMPERATURE          = 0
        SENSOR_IDX_HUMIDITY             = 1
        SENSOR_IDX_VOC_LVL              = 2
        SENSOR_UUID                     = "b42e3b98-ade7-11e4-89d3-123b93f75cba"

        def __init__(self):
            self.sensor_version = None
            self.sensor_data    = [None]*self.NUMBER_OF_SENSORS
            self.sensor_units   = ["degC", "%rH", "ppb"]
            self.sensor_names   = ['Temperature', 'Humidity', 'VOC level']
            self.sensor_classes = ['temperature', 'humidity', None]
            self.sensor_classes = ['temperature', 'humidity', None]
            self.sensor_format  = '<HHHHHHLL'
            self.sensor_uuid    = UUID(self.SENSOR_UUID)

        def set(self, rawData):
            self.sensor_version = rawData[0]
            self.sensor_data[self.SENSOR_IDX_TEMPERATURE]          = round(rawData[1]/100.0 - 273.15, 2)
            self.sensor_data[self.SENSOR_IDX_HUMIDITY]             = rawData[3]/100.0
            self.sensor_data[self.SENSOR_IDX_VOC_LVL]              = rawData[4]*1.0

