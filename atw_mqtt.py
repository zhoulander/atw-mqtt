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

# ===============================
# Module import dependencies
# ===============================

import sys
import time
import socket
import json
import paho.mqtt.client as mqtt
import yaml
from datetime import datetime
from WavePlus import WavePlus
from Wave import Wave
from Wave2 import Wave2
from WaveMini import WaveMini

ATWMQTT_NAME           = 'airthings_mqtt'
ATWMQTT_VERSION        = '0.0.1'
ATWMQTT_MANUFACTURER   = 'Airthings'
ATWMQTT_MODEL_LIST     = ['Wave', 'Wave 2', 'Wave Plus', 'Wave Mini']
ATWMQTT_MQTT_TOPIC     = 'airthings'
ATWMQTT_MODEL_WAVE     = 0
ATWMQTT_MODEL_WAVE2    = 1
ATWMQTT_MODEL_WAVEPLUS = 2
ATWMQTT_MODEL_WAVEMINI = 3

# ===============================
# Script guards for correct usage
# ===============================
def print_usage():
    print ("USAGE: atw_mqtt.py YAMLFILE")

# homeassistant mqtt device discovery entity information payload
def ha_device(device_model, device_sn):
    device = dict()
    device['name']         = "{0}_{1}".format(ATWMQTT_MANUFACTURER.lower(), device_sn)
    device['model']        = ATWMQTT_MODEL_LIST[device_model]
    device['manufacturer'] = ATWMQTT_MANUFACTURER
    device['sw_version']   = "{0} {1}".format(ATWMQTT_NAME, ATWMQTT_VERSION)
    device['identifiers']  = ['{0}_{1}'.format(device['model'].lower().replace(' ',''), device_sn)]
    return device

# homeassistant mqtt device discovery configuration payload
def ha_device_config_payload(sensor_name, device_sn, sensor_unit, sensor_class, sensor_device):
    config_value = ['name', 'state_topic','unit_of_measurement','value_template','device', 'device_class', 'json_attributes_topic', 'unique_id']
    config_payload = dict()
    config_payload[config_value[0]] = sensor_name
    config_payload[config_value[1]] = "{0}/sensor/{1}".format(ATWMQTT_MQTT_TOPIC, device_sn)
    config_payload[config_value[2]] = sensor_unit
    config_payload[config_value[3]] = "{{{{ value_json.{0} }}}}".format(sensor_name)
    config_payload[config_value[4]] = sensor_device
    if sensor_class is not None:
        config_payload[config_value[5]] = sensor_class
    config_payload[config_value[6]] = "{0}/sensor/{1}".format(ATWMQTT_MQTT_TOPIC, device_sn)
    config_payload[config_value[7]] = "{0}_{1}_{2}".format(device_sn, sensor_name, ATWMQTT_NAME)
    return config_payload

# select airthings object
def airthings_select(device_model, device_sn):
    return {
        ATWMQTT_MODEL_WAVE     : Wave(device_sn),
        ATWMQTT_MODEL_WAVE2    : Wave2(device_sn),
        ATWMQTT_MODEL_WAVEPLUS : WavePlus(device_sn),
        ATWMQTT_MODEL_WAVEMINI : WaveMini(device_sn)
    }.get(device_model, None)

class Airthings_mqtt:
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            self.config = yaml.load(f)
        self.waves = list()
        self.devices = list()
        if self.check_config(self.config):
            self.mqtt_client = mqtt.Client()
            self.mqtt_connect(self.config)

    def check_config(self, conf):
        if "mqtt" not in conf:
            return False
        if "broker" not in conf["mqtt"]:
            return False
        if "port" not in conf["mqtt"]:
            return False
        if "waves" in conf:
            for wave in conf["waves"]:
                if "sn" in wave and "model" in wave:
                    # advertise to HA by default
                    if "advertise" not in wave:
                        wave["advertise"]=True
                    self.waves.append(wave)
                else:
                    print("Malformed config item: {0}".format(wave))
        return True

    def wave_init(self):
        for wave in self.config["waves"]:
            device_sn = wave["sn"]
            device_model = wave["model"]
            device_model_index = ATWMQTT_MODEL_LIST.index(device_model)
            self.devices.append(airthings_select(device_model_index, device_sn))

    def mqtt_connect(self, conf):
        self.mqtt_conf=self.config["mqtt"]
        if self.mqtt_conf["username"] is not None:
            self.mqtt_client.username_pw_set(self.mqtt_conf["username"], self.mqtt_conf["password"])
        self.mqtt_client.connect(self.mqtt_conf["broker"], self.mqtt_conf["port"])

if len(sys.argv) < 2:
    print ("ERROR: Missing input argument configuration.yaml.")
    print_usage()
    sys.exit(1)

config_file = sys.argv[1]

#---- Initialize ----#
now = datetime.now()
# dd/mm/YY H:M:S
dt_string = now.strftime("%Y/%m/%d %H:%M:%S")

print ("{0} {1} ".format(dt_string, config_file), end ='')

atw = Airthings_mqtt(config_file)
atw.wave_init()
device_count = len(atw.waves)
broker = atw.mqtt_conf["broker"]

try:
    socket.inet_aton(broker)
    # legal
except socket.error:
    # Not legal
    print ("ERROR: Invalid IP address: ", broker)
    print_usage()
    sys.exit(1)

print ("Devices configured: {0}".format(device_count))
print (json.dumps(atw.waves))

print ("\nReading devices...\n")

for w, d in zip(atw.waves, atw.devices):
    device_sn = w["sn"]
    device_name = w["name"]
    device_model = w["model"]
    device_model_index = ATWMQTT_MODEL_LIST.index(device_model)
    device_advertise = w["advertise"]

    if device_advertise:
        advertise_device = ha_device(device_model_index, device_sn)

    # show which device is being read
    print(json.dumps(w))

    # read device
    d.connect()
    d.read()
    d.disconnect()

    # package device sensor readings payload and advertise to HA
    payload = dict()
    for i in range(d.sensors.NUMBER_OF_SENSORS):
        sensor_name = d.sensors.sensor_names[i].replace(' ','_')
        payload[sensor_name] = d.sensors.getValue(i)

        if device_advertise:
            # publish device sensor HA configuration payload
            config_payload = ha_device_config_payload(sensor_name, device_sn, d.sensors.sensor_units[i], d.sensors.sensor_classes[i], advertise_device)

            topic = "homeassistant/sensor/{0}/{0}_{1}/config".format(device_sn, sensor_name)
            info = atw.mqtt_client.publish(topic, json.dumps(config_payload), retain=True)
            print("{0} / {1}".format(topic, info))

    # publish device sensors json
    topic = "{0}/sensor/{1}".format(ATWMQTT_MQTT_TOPIC, device_sn)
    info = atw.mqtt_client.publish(topic, json.dumps(payload), retain=False)
    print("{0} / {1} : {2}".format(topic, info, json.dumps(payload)))

    info.wait_for_publish()
    time.sleep(0.1)


atw.mqtt_client.disconnect()
