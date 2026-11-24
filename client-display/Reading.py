from urllib.request import urlopen as uo
from http.client import HTTPException
import logging
import time
from datetime import datetime
from threading import Event, Lock, Thread
import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
from matplotlib import pyplot as plt

class Reading(object):

	def __init__(self, url: str = "http://192.168.0.12") -> None:
		self.base_url = url
		self.history = []
		self.history_lock = Lock()
		self.failed = False

	def readValue(self, path, label, minimum, maximum, suffix="") -> float:
		with uo(self.base_url + path, timeout=5) as response:
			if response.status != 200:
				raise ValueError(f"{path}: HTTP {response.status}")
			body = response.read().decode("utf-8").strip()

		prefix = label + ":"
		if not body.startswith(prefix) or not body.endswith(suffix):
			raise ValueError(f"{path}: unexpected response")
		payload = body[len(prefix):]
		if suffix:
			payload = payload[:-len(suffix)]
		try:
			value = float(payload)
		except ValueError as error:
			raise ValueError(f"{path}: invalid number") from error
		if not minimum <= value <= maximum:
			raise ValueError(f"{path}: reading outside sensor range")
		return value

	def getTemp(self) -> float:
		fahrenheit = self.readValue("/temp", "Temperature", -40.0, 176.0)
		return (fahrenheit - 32.0) * (5.0 / 9.0)

	def getTemp2(self) -> float:
		return self.readValue("/temp2", "Temperature 2", -55.0, 125.0)

	def getHumidity(self) -> float:
		return self.readValue("/humidity", "Humidity", 0.0, 100.0, "%")

	def fetchSample(self) -> tuple:
		temp = self.getTemp()
		temp2 = self.getTemp2()
		humidity = self.getHumidity()
		return datetime.now(), temp, temp2, humidity

	def getSamples(self, stop: Event) -> None:
		while not stop.is_set():
			try:
				sample = self.fetchSample()
				if stop.is_set():
					return
				timestamp, temp, temp2, humidity = sample
				with open("../data/readings.csv", mode="a") as csv_file:
					csv_file.write(f"{timestamp:%H:%M:%S},{temp:.1f},{temp2:.2f},{humidity:.2f}%\n")
			except (OSError, HTTPException, ValueError) as error:
				with self.history_lock:
					self.failed = True
				logging.warning("Reading failed: %s", error)
			else:
				with self.history_lock:
					self.history.append(sample)
					self.failed = False
			stop.wait(1)

class Display(object):
	
	def __init__(self, reading: Reading) -> None:
		self.sensor = reading
		lcd_columns = 16
		lcd_rows = 2
		i2c = busio.I2C(board.SCL, board.SDA)
		self.lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)
		self.figure = None
		self.up_pressed = False
		self.last_message = ""
	
	def refresh(self) -> None:
		with self.sensor.history_lock:
			sample = self.sensor.history[-1] if self.sensor.history else None
			failed = self.sensor.failed

		clock = datetime.now().strftime("%H:%M:%S")
		print(f"Time: {clock}")
		if sample is None:
			top = "No valid data" if failed else "Waiting for data"
			bottom = clock
			print(f"{top}")
		else:
			_, temp, temp2, humidity = sample
			top = f"{temp:.1f}C {temp2:.2f}C"
			humidity_text = f"{humidity:.2f}%"
			gap = ("*" if failed else " ").rjust(8 - len(humidity_text))
			bottom = f"{humidity_text}{gap}{clock}"
			print(f"Temperatures: {temp:.1f}C {temp2:.2f}C")
			print(f"Humidity: {humidity:.2f}")

		message = f"{top:<16}\n{bottom:<16}"
		if message != self.last_message:
			if sample is not None:
				temp = round(temp, 1)
				self.lcd.color = [1 + (temp > 20), 0, 1 + (temp < 25)]
			self.lcd.message = message
			self.last_message = message

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
		self.plot_count = 0
		self.updatePlot()
		plt.show(block=False)

	def updatePlot(self) -> None:
		with self.sensor.history_lock:
			if self.plot_count == len(self.sensor.history):
				return
			history = self.sensor.history.copy()
		self.plot_count = len(history)
		times, temp, temp2, humidity = zip(*history)
		elapsed = [(timestamp - times[0]).total_seconds() for timestamp in times]
		self.plot_lines[0].set_data(elapsed, temp)
		self.plot_lines[1].set_data(elapsed, temp2)
		self.plot_lines[2].set_data(elapsed, humidity)
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


if __name__ == "__main__":
	room = Reading()
	screen = Display(room)
	stop = Event()
	worker = Thread(target=room.getSamples, args=(stop,))
	worker.start()

	try:
		while worker.is_alive():
			screen.checkButtons()
			screen.refresh()
			if screen.figure is None:
				time.sleep(0.05)
			else:
				plt.pause(0.05)
	except KeyboardInterrupt:
		pass
	finally:
		stop.set()
		worker.join()
