from urllib.request import urlopen as uo
import time
from datetime import datetime
import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
import asyncio

class Reading(object):
	
	temp = "Not read"
	temp2 = "Not read"
	hum = "Not read"
	
	def __init__(self, url: str = "http://192.168.0.7") -> None:
		self.base_url = url
	
	def getTemp(self) -> None:
		with uo(self.base_url + "/temp", timeout = 5) as response:
			self.temp = float(response.read().decode("utf-8").strip().split(" ")[-1])
	
	def getTemp2(self) -> None:
		with uo(self.base_url + "/temp2", timeout = 5) as response:
			self.temp2 = float(response.read().decode("utf-8").strip().split(" ")[-1])
	
	def getHumidity(self) -> None:
		with uo(self.base_url + "/humidity", timeout = 5) as response:
			self.hum = response.read().decode("utf-8").strip().split(" ")[-1]
			
	def grabTempF(self) -> str:
		return str(self.temp) + "F"
	
	def grabTempC(self) -> str:
		tempC = (self.temp - 32)*(5/9)
		return f"{tempC:.1f}"
		
	def grabTemp2(self) -> str:
		return f"{float(self.temp2):.2f}"
		
	def grabHumidity(self) -> str:
		return self.hum

class Display(object):
	
	def __init__(self, reading: Reading) -> None:
		self.sensor = reading
		lcd_columns = 16
		lcd_rows = 2
		i2c = busio.I2C(board.SCL, board.SDA)
		self.lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)
		self.counter = 0
	
	def refresh(self) -> None:
		self.sensor.getTemp()
		self.sensor.getTemp2()
		self.sensor.getHumidity()
		temp = self.sensor.grabTempC()
		temp2 = self.sensor.grabTemp2()
		humidity = self.sensor.grabHumidity()
		
		self.lcd.color = [1+(float(temp)>20),0,1+(float(temp)<25)]	 	
		self.lcd.message = f"{temp}C {temp2}C\n{humidity}  {datetime.now().strftime('%H:%M:%S')}"
		with open("heatgun_readings.csv", mode = 'a') as f:
			f.write(f"{datetime.now().strftime('%H:%M:%S')},{temp},{temp2},{humidity}\n")
		time.sleep(1)

room = Reading()
screen = Display(room)

while True:
	screen.refresh()
