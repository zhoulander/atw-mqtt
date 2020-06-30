# Airthings Wave 2 MQTT

This project allows you to read sensor values from [Airthings](http://airthings.com) BTLE Radon detector devices. It reads from Wave, Wave 2, Wave Plus, and Wave Mini devices and publishes data to a MQTT server. It also publishes [Home Assistant](https://www.home-assistant.io) configuration payloads for the [MQTT integration](https://www.home-assistant.io/integrations/mqtt/).

It has been tested with Wave Plus and Wave Mini devices.  Gen 1 and 2 devices should work, but please let me know if they do not.

**Table of contents**

* [Requirements](#requirements)
* [Usage](#usage)
  * [Configuration](#configuration)
  * [Example](#example)
  * [Posting regularly to MQTT Server](#posting-regularly-to-mqtt-server)
  * [Troubleshooting](#troubleshooting)
* [Sensor data description](#sensor-data-description)
* [Release notes](#release-notes)
* [Thanks](#thanks)

# Requirements

The following tables shows a compact overview of dependencies for this project.

**List of OS dependencies**

| OS | Device/model/version | Comments |
|-------------|-------------|-------------|
| Raspbian | Raspberry Pi 3 Model B | Used in this project.
| Linux    | x86 Debian             | Should work according to [bluepy](https://github.com/IanHarvey/bluepy)

**List of linux/raspberry dependencies**

| package | version | Comments |
|-------------|-------------|-------------|
| python3        | 3.7 | Tested with python 3.7.3
| python3-pip    |     | pip for python 3.7.3
| git            |     | To download this project
| libglib2.0-dev |     | For bluepy module

**List of Python dependencies**

| module | version | Comments |
|-------------|-------------|-------------|
| bluepy      | 1.3.0 | Newer versions have not been tested.
| paho-mqtt   | 1.5.0 | Newer versions have not been tested.
| pyyaml      | 3.13  | Newer versions have not been tested.

## Turn on the BLE interface

In the terminal window on your Raspberry Pi:

```
pi@raspberrypi:~$ bluetoothctl
[bluetooth]# power on
[bluetooth]# show
```

After issuing the command ```show```, a list of bluetooth settings will be printed
to the Raspberry Pi terminal window. Look for ```Powered: yes```.

# Usage

Use the ```find_wave.py``` script to scan for devices, or add the parameter ```read``` to  dump out sensor readings.  It will try to identify each device model. Match the 10-digit serial number to the one under the magnetic backplate of your Airthings Wave device.

If your device is paired and connected to e.g. a phone, you may need to turn off bluetooth on your phone while using this script.

```
pi@raspberrypi:~/atw-mqtt $ sudo python3 find_wave.py 
scanning for devices...
a4:da:30:b0:30:90 (public), RSSI=-56 dB, SN=1234567890, Model=WavePlus
done. 
```


```
pi@raspberrypi:~/atw-mqtt $ sudo python3 find_wave.py read
scanning for devices...
a4:da:30:b0:30:90 (public), RSSI=-64 dB, SN=2930000000, Model=WavePlus
80:6f:b0:40:00:30 (public), RSSI=-85 dB, SN=2920000001, Model=WaveMini
2 devices found.


{'model': 'WavePlus', 'sn': 2930000000, 'mac': 'a4:da:30:b0:30:90', 'Humidity': 49.5, 'Radon_ST_avg': 96, 'Radon_LT_avg': 51, 'Temperature': 23.57, 'Pressure': 991.3, 'CO2_level': 1778.0, 'VOC_level': 335.0}
{'model': 'WaveMini', 'sn': 2920000001, 'mac': '80:6f:b0:40:00:30', 'Temperature': 26.76, 'Humidity': 43.57, 'VOC_level': 46.0}
```

## Configuration

Edit the example configuration file ```config.yaml``` and populate it with the device serial number and model name:

```yaml
mqtt:
  broker: <IP address>
  port: 1883
  username: "username"
  password: "password"

waves:
  - name: "basement_radon"
    sn: 1234567890
    model: "Wave Plus"
    advertise: True
``` 

```advertise``` is optional.  If it does not exist it will advertise to HA MQTT on every run.  Change this to ```False``` to reduce MQTT traffic after your devices are setup.

## Example


```
pi@raspberrypi:~/atw-mqtt $ sudo python3 /home/pi/atw-mqtt/atw_mqtt.py /home/pi/atw-mqtt/config.yaml
2020/05/27 23:50:48 /home/pi/atw-mqtt/config.yaml Devices configured: 1
[{"name": "basement_radon", "sn": 1234567890, "addr": "a4:da:30:b0:30:90", "model": "Wave Plus", "advertise": true}]

Reading devices...

{"name": "basement_radon", "sn": 1234567890, "addr": "a4:da:30:b0:30:90", "model": "Wave Plus", "advertise": true}
homeassistant/sensor/1234567890/1234567890_Humidity/config / (0, 1)
homeassistant/sensor/1234567890/1234567890_Radon_ST_avg/config / (0, 2)
homeassistant/sensor/1234567890/1234567890_Radon_LT_avg/config / (0, 3)
homeassistant/sensor/1234567890/1234567890_Temperature/config / (0, 4)
homeassistant/sensor/1234567890/1234567890_Pressure/config / (0, 5)
homeassistant/sensor/1234567890/1234567890_CO2_level/config / (0, 6)
homeassistant/sensor/1234567890/1234567890_VOC_level/config / (0, 7)
airthings/sensor/1234567890 / (0, 8) : {"Humidity": 54.0, "Radon_ST_avg": 33, "Radon_LT_avg": 26, "Temperature": 22.72, "Pressure": 993.74, "CO2_level": 1349.0, "VOC_level": 797.0}
```


## Posting regularly to MQTT Server

The values will be posted as a json object to topic
```
airthings/sensor/SN
```
```SN``` is the configured device serial number
```json
{"Humidity": 53.5,
"Radon_ST_avg": 33,
"Radon_LT_avg": 26,
"Temperature": 22.53,
"Pressure": 993.76,
"CO2_level": 1337.0,
"VOC_level": 779.0}
```

Add a line to your cron table:
```
pi@raspberrypi:~ $ sudo crontab -e
```
Note the use of 'sudo': needed for the scripts access to the BTLE device.

The following line will make a read and post every 5 minutes:
 
```
*/5 * * * *   sudo python3 /home/pi/atw-mqtt/atw_mqtt.py /home/pi/atw-mqtt/config.yaml
```

> **Note on choosing a sample period:** 
Except for the radon measurements, the Wave Plus updates its current sensor values once every 5 minutes.
Radon measurements are updated once every hour.

## Troubleshooting
You can run ```sudo ./resetbt.sh``` to reset the Bluetooth controller if it starts throwing errors from polling too often.  Optionally add it into your crontab if it crashes out regularly.

# Sensor data description

| sensor | units | Comments |
|-------------|-------------|-------------|
| Humidity                      | %rH | 
| Temperature                   | &deg;C |
| Radon short term average      | Bq/m3 | First measurement available 1 hour after inserting batteries
| Radon long term average       | Bq/m3 | First measurement available 1 hour after inserting batteries
| Relative atmospheric pressure | hPa |
| CO2 level                     | ppm |
| TVOC level                    | ppb | Total volatile organic compounds level


# Release notes

* Initial release 30-Jun-2020

# Thanks

These resources helped me along the way:

* https://www.airthings.com/resources/raspberry-pi
* https://github.com/hpeyerl/airthingswave-mqtt
* https://github.com/stenjo/waveplus-reader
* https://github.com/Airthings/wave-reader
* https://github.com/Airthings/waveplus-reader
* https://github.com/Airthings/wavemini-reader