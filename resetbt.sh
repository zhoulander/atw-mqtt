# resets ble adapter on rpi3b

#!/bin/sh
hciconfig hci0 down && hciconfig hci0 up
