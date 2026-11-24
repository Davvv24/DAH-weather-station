/* 
  server - ESP8266 HTTP Webserver with a DHT sensor and a DS18B20 sensor as an input
  Based on ESP8266Webserver, DHT22 example, DS18B20 Single
*/

#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ESP8266WebServer.h>
#include <DHT22.h>
#include <math.h>

#include "OneWire.h"
#include "DallasTemperature.h"

#define DHTTYPE DHT22
#define DHTPIN  2
#define ONE_WIRE_BUS 5

const char* ssid     = "DAH-lab";         // Hotspot name
const char* password = "AbbeyRoadAlbum";  // Hotspot password
class WeatherSensors {
private:
  DHT22 dht_;
  OneWire one_wire_;
  DallasTemperature ds_sensor_;

public:
  // Initialise the DHT sensor with the DHTpin, the OneWire instance with the OneWire pin 
  // for the DS temperature sensor communication, and the DS sensor using the OneWire connection
  WeatherSensors(uint8_t dhtPin, uint8_t oneWirePin)
      : dht_(dhtPin), one_wire_(oneWirePin), ds_sensor_(&one_wire_) {}

  void begin() {
    ds_sensor_.begin();
  }

  float readTemperatureF() {
    float temp_f = dht_.getTemperature(false);
    if (dht_.getLastError() != dht_.OK) {
      Serial.print("DHT22 error: ");
      Serial.println(dht_.getLastError());
      return NAN;
    }
    Serial.print("t=");Serial.println(temp_f,1);Serial.println();
    return temp_f;
  }

  float readHumidity() {
    float humidity = dht_.getHumidity();
    if (dht_.getLastError() != dht_.OK) {
      Serial.print("DHT22 error: ");
      Serial.println(dht_.getLastError());
      return NAN;
    }
    Serial.print("h=");Serial.print(humidity,1);Serial.println();
    return humidity;
  }

  float readTemperatureC2() {
    ds_sensor_.requestTemperatures();
    float temp_c2 = ds_sensor_.getTempCByIndex(0);
    Serial.print("Temperature: ");Serial.print(temp_c2);Serial.print("deg C");Serial.println();
    return temp_c2;
  }
};


// Global HTTP server on port 80 and weather station instance
ESP8266WebServer server(80);
WeatherSensors weather_station(DHTPIN, ONE_WIRE_BUS);

void sendReading(float value, float minimum, float maximum, const char* label, const char* suffix) {
  if (!(value >= minimum && value <= maximum)) {
    server.send(503, "text/plain", "Sensor reading unavailable");
    return;
  }
  server.send(200, "text/plain", String(label) + String(value) + suffix);
}

void handle_root() {
  server.send(200, "text/plain", "Hello from the weather esp8266, read from /temp, /temp2, or /humidity");
  delay(100);
}
 
void setup(void)
{
  // You can open the Arduino IDE Serial Monitor window to see what the code is doing
  Serial.begin(115200);  // Serial connection from ESP-01 via 3.3v console cable

  // while(!Serial){delay(1);} // Uncomment to enforce serial
  
  // Connect to WiFi network
  WiFi.begin(ssid, password);
  Serial.print("\n\r \n\rWorking to connect");

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connection established. Weather station connected to: ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
   
  
  // Start up weather station
  weather_station.begin();
  Serial.println("Started weather station sensors");

  // Website response setup
  server.on("/", handle_root);
  
  server.on("/temp", [](){
    sendReading(weather_station.readTemperatureF(), -40.0f, 176.0f, "Temperature: ", "");
  });

  server.on("/humidity", [](){
    sendReading(weather_station.readHumidity(), 0.0f, 100.0f, "Humidity: ", "%");
  });

  server.on("/temp2", [](){
    sendReading(weather_station.readTemperatureC2(), -55.0f, 125.0f, "Temperature 2: ", "");
  });

  Serial.println("Website responses configured");
  
  server.begin();
  Serial.println("HTTP server started");
}
 
// Main loop
void loop(void)
{
  server.handleClient();
} 
