# Weather station #
This repo contains the server and client code for a simple remote weather station with temperature and humidity data.

The server provides a HTTP service accessed across a LAN within a given lab, while the client-display sends get requests, takes in the data, and displays it on a small backlit character LCD display with time information.

The firmware combines example code for a DHT22 weather/humidity sensor, a DS18B20 temperature sensor, and an ESP8266 Feather Huzzah dev board web server.

## Instructions ##
Git clone the repo.

### To run the web server: ### 
1. Install the required Arduino libraries:
    - DHT22 by dvarrell
    - DallasTemperature by Miles Burton
    - OneWire by Jim Studt
2. Add the ESP8266 board manager:
    - http://arduino.esp8266.com/stable/package_esp8266com_index.json
3. Power the board and connect the respective sensors
4. Change the hardcoded WiFi details inside `server.ino` to match the name and password for your setup
5. Compile and flash the Arduino code onto the dev board. 
6. Wait for it to connect to the local WiFi then optionally connect via serial


### To run the display ###
1. Install the required libraries listed in requirements.txt
2. Connect a raspberryPI to a backlit LCD character display
3. Add the local IP address of the board to `Reading.py`. If you can't find it, follow the instructions below
4. Run Reading.py with `python3 Reading.py`

### To find the local IP ###
Connect via USB serial to the server and open the serial monitor. This will print out the local IP on startup.

Alternatively, run the following Bash script from a RaspberryPI termninal:
```
for i in {1..254}; do
    ping -c 1 -W 1 192.168.0.$i >/dev/null 2>&1 && echo "192.168.1.$i" &
done
wait
```
This assumes the local netmask is 192.168.1.*. It pings every local network device and gives you a list of addresses you can send get requests to using your browser.