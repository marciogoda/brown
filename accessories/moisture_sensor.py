import RPi.GPIO as GPIO

from time import sleep
from datetime import datetime

from pyhap.const import CATEGORY_SENSOR
from pyhap.accessory import Accessory, Bridge

SENSOR_PIN = 17
RELAY_PIN = 26

class MoistureSensor(Accessory):

    category = CATEGORY_SENSOR

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)

        self._pin_number = SENSOR_PIN
        self._relay_pin_number = RELAY_PIN
        GPIO.setwarnings(False)

        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
        
        GPIO.setup(self._pin_number,GPIO.IN)
        if self._relay_pin_number != 0:
            GPIO.setup(self._relay_pin_number, 
                GPIO.OUT, 
                initial=GPIO.HIGH
            )

        serv_humidity = self.add_preload_service('HumiditySensor')
        self.char_humidity = serv_humidity.configure_char('CurrentRelativeHumidity')

    @Accessory.run_at_interval(360)
    async def run(self):
        if self._relay_pin_number != 0:
            GPIO.output(self._relay_pin_number, GPIO.LOW)
            sleep(2)

        dry = GPIO.input(self._pin_number)

        if self._relay_pin_number != 0:
            GPIO.output(self._relay_pin_number, GPIO.HIGH)

        self.char_humidity.set_value(0 if dry else 100)

        with open("/home/pi/brown/logs/log.txt", "a") as file_object:
            # Append 'hello' at the end of file
            date_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            text = ("DRY" if dry else "NOT DRY")
            file_object.write(f"{date_stamp}:{text}\n")