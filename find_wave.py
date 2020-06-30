# MIT License
#
# Copyright (c) 2020 Brian Zhou
# Portions Copyright (c) 2018 Airthings AS
#
# Portions of this code from https://airthings.com/raspberry-pi/ which is itself
# released under an MIT license with the following terms:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# https://airthings.com

from bluepy.btle import Scanner, DefaultDelegate
from bluepy import btle
import time
import struct
import sys
from Wave import Wave
from Wave2 import Wave2
from WavePlus import WavePlus
from WaveMini import WaveMini

class DecodeErrorException(Exception):
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return repr(self.value)

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

print ("scanning for devices...")
scanner = Scanner().withDelegate(ScanDelegate())

found = False

ATWMQTT_MODEL_WAVE     = 0
ATWMQTT_MODEL_WAVE2    = 1
ATWMQTT_MODEL_WAVEPLUS = 2
ATWMQTT_MODEL_WAVEMINI = 3
ATWMQTT_MODEL_LIST     = ['Wave', 'Wave2', 'WavePlus', 'WaveMini']

def airthings_select(device_model, device_sn, device_mac):
    return {
        ATWMQTT_MODEL_WAVE     : Wave(device_sn, device_mac),
        ATWMQTT_MODEL_WAVE2    : Wave2(device_sn, device_mac),
        ATWMQTT_MODEL_WAVEPLUS : WavePlus(device_sn, device_mac),
        ATWMQTT_MODEL_WAVEMINI : WaveMini(device_sn, device_mac)
    }.get(device_model, None)


if len(sys.argv) > 1:
     read = sys.argv[1] == 'read'
else:
     read = False

serials = []
models = []
macs = []

try:
    while (not found):
        devices = scanner.scan(10.0)
#        print ("{0} devices found".format(len(devices)))

        for dev in devices:
            ManuData = ""
            ManuDataHex = []
            for (adtype, desc, value) in dev.getScanData():
                serial_no = ""
                if (desc == "Manufacturer"):
                    ManuData = value

                if (ManuData == ""):
                    continue

                for i, j in zip (ManuData[::2], ManuData[1::2]):
                    ManuDataHex.append(int(i+j, 16))

                #Start decoding the raw Manufacturer data
                if ((ManuDataHex[0] == 0x34) and (ManuDataHex[1] == 0x03)):
                    serial_no = str(256*256*256*ManuDataHex[5] + 256*256*ManuDataHex[4] + 256*ManuDataHex[3] + ManuDataHex[2])
                    print ("{0} ({1}), RSSI={2} dB, SN={3}".format(dev.addr, dev.addrType, dev.rssi, serial_no), end ='')

                    sn = int(serial_no)

                    tries = 0
                    conn = False
                    skip = False

                    while (tries < 3 and conn is False):
                        try:
                            periph = btle.Peripheral(dev.addr)
                            try:
                                conn = periph.getState() == "conn"
                            except:
                                conn = False
                        except:
                            if tries == 3:
                                skip = True
                            else:
                                pass

                    model = "Unknown"
                    if (skip):
                        model = "Skip"

                    if (model == "Unknown"):
                        try:
                            char = periph.getCharacteristics(uuid=Wave2.Sensors.SENSOR_UUID)
                            model = "Wave2"
                        except:
                             pass

                    if (model == "Unknown"):
                        try:
                            char = periph.getCharacteristics(uuid=WavePlus.Sensors.SENSOR_UUID)
                            model = "WavePlus"
                        except:
                             pass

                    if (model == "Unknown"):
                        try:
                            char = periph.getCharacteristics(uuid=WaveMini.Sensors.SENSOR_UUID)
                            model = "WaveMini"
                        except:
                             pass

                    if (model == "Unknown"):
                        try:
                            char = periph.getCharacteristics(uuid='b42e01aa-ade7-11e4-89d3-123b93f75cba')
                            model = "Wave"
                        except:
                             pass

                    periph.disconnect()


                    if (skip):
                        model = 'Unknown'

                    print (", Model={0}".format(model))

                    if (model is not "Unknown"):
                        found = True
                        serials.append(sn)
                        models.append(model)
                        macs.append(dev.addr)

                else:
                    continue

        if (found):
            print ("{0} devices found.\n\n".format(len(serials)))

            if (read):
                time.sleep(5)

                for sn,model,mac in zip(serials,models,macs):
                    payload = dict()

                    device_model_index = ATWMQTT_MODEL_LIST.index(model)
                    device = airthings_select(device_model_index, sn, mac)

                    device.connect()
                    device.read()
                    device.disconnect()

                    payload['model'] = model
                    payload['sn']    = sn
                    payload['mac']   = mac

                    for i in range(device.sensors.NUMBER_OF_SENSORS):
                        sensor_name = device.sensors.sensor_names[i].replace(' ','_')
                        payload[sensor_name] = device.sensors.getValue(i)
                    print (payload)

                    device = None

        else:
            print ("scanning...")
except DecodeErrorException:
    pass
