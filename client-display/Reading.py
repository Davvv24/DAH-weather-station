from urllib.request import urlopen as uo
import time
from datetime import datetime
import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
from matplotlib import pyplot as plt

class Reading(object):
	
	temp = "Not read"
	temp2 = "Not read"
	hum = "Not read"
	
	def __init__(self, url: str = "http://192.168.0.7") -> None:
		self.base_url = url
		self.history = []
	
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
		self.figure = None
		self.up_pressed = False
	
	def refresh(self) -> None:
		self.sensor.getTemp()
		self.sensor.getTemp2()
		self.sensor.getHumidity()
		temp = self.sensor.grabTempC()
		temp2 = self.sensor.grabTemp2()
		humidity = self.sensor.grabHumidity()
		timestamp = datetime.now()
		clock = timestamp.strftime('%H:%M:%S')
		self.sensor.history.append((timestamp, temp, temp2, humidity))
		
		self.lcd.color = [1+(float(temp)>20),0,1+(float(temp)<25)]	 	
		self.lcd.message = f"{temp}C {temp2}C\n{humidity}  {clock}"
		with open("heatgun_readings.csv", mode = 'a') as f:
			f.write(f"{clock},{temp},{temp2},{humidity}\n")

		if self.figure is not None:
			self.updatePlot()

	# Opens a live plot with two y axis for humidity and temperature and any reading up to now
	def openPlot(self) -> None:
		self.figure, (temperature_axis, humidity_axis) = plt.subplots(2, 1, sharex=True)
		dht_line, = temperature_axis.plot([], [], marker=".", label="DHT22")
		ds_line, = temperature_axis.plot([], [], marker=".", label="DS18B20")
		humidity_line, = humidity_axis.plot([], [], marker=".")
		self.plot_lines = dht_line, ds_line, humidity_line
		temperature_axis.set_ylabel("Temperature (C)")
		temperature_axis.legend()
		humidity_axis.set_ylabel("Humidity (%)")
		humidity_axis.set_xlabel("Elapsed time (s)")
		self.figure.tight_layout()
		self.updatePlot()
		plt.show(block=False)

	# Updates the existing plot when called
	def updatePlot(self) -> None:
		if not self.sensor.history:
			return
		times, temp, temp2, humidity = zip(*self.sensor.history)
		elapsed = [(timestamp - times[0]).total_seconds() for timestamp in times]
		self.plot_lines[0].set_data(elapsed, [float(value) for value in temp])
		self.plot_lines[1].set_data(elapsed, [float(value) for value in temp2])
		self.plot_lines[2].set_data(elapsed, [float(value.rstrip("%")) for value in humidity])
		for axis in self.figure.axes:
			axis.relim()
			axis.autoscale_view()
		self.figure.canvas.draw_idle()

	# Checks the buttons on the character lcd display and opens/closes the plot accordingly
	def checkButtons(self) -> None:
		if self.figure is not None and not plt.fignum_exists(self.figure.number):
			self.figure = None
		up = self.lcd.up_button			
		if self.lcd.down_button:									# down closes plot
			if self.figure is not None:
				plt.close(self.figure)
				self.figure = None
		elif up and not self.up_pressed and self.figure is None:	# up opens plot
			self.openPlot()
		self.up_pressed = up

	# Check the buttons constantly until it's time to update the readings again
	def waitNextReading(self) -> None:
		deadline = time.time() + 1
		while time.time() < deadline:
			self.checkButtons()
			delay = min(0.05, deadline - time.time()) # makes it wait the exact missing time 
			if delay <= 0:
				break
			if self.figure is None:
				time.sleep(delay)
			else:
				plt.pause(delay)


if __name__ == "__main__":
	room = Reading()
	screen = Display(room)

	while True:
		screen.refresh()
		screen.waitNextReading()
