import logging
import RPi.GPIO as GPIO

from time import sleep
from datetime import datetime
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_OUTLET

def _gpio_setup(pin):
    if GPIO.getmode() is None:
        GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)


def set_gpio_state(pin, state, reverse):
    if state:
        if reverse:
            GPIO.output(pin, 1)
        else:
            GPIO.output(pin, 0)
    else:
        if reverse:
            GPIO.output(pin, 0)
        else:
            GPIO.output(pin, 1)
    #logging.info("Setting pin: %s to state: %s", pin, state)


def get_gpio_state(pin, reverse):
    if GPIO.input(pin):
        if reverse:
            return int(1)
        else:
            return int(0)
    else:
        if reverse:
            return int(0)
        else:
            return int(1)


class WateringSwitch(Accessory):
    category = CATEGORY_OUTLET

    def __init__(self, 
        pin_number, 
        counter, 
        reverse, 
        startstate,
        *args, 
        **kwargs):

        super().__init__(*args, **kwargs)

        self.pin_number = pin_number
        self.counter = counter
        self.reverse = reverse
        self.startstate = startstate

        _gpio_setup(self.pin_number)

        serv_switch = self.add_preload_service('Outlet')
        self.relay_on = serv_switch.configure_char(
            'On', setter_callback=self.set_relay)

        self.relay_in_use = serv_switch.configure_char(
            'OutletInUse', setter_callback=self.get_relay_in_use)

        self.timer = 1

        self.set_relay(startstate)

    @Accessory.run_at_interval(1)
    def run(self):
        state = get_gpio_state(self.pin_number, self.reverse)

        if self.relay_on.value != state:
            self.relay_on.value = state
            self.relay_on.notify()
            self.relay_in_use.notify()

        oldstate = 1

        if state != oldstate:
            self.timer = 1
            oldstate == state

        if self.timer == self.counter:
            set_gpio_state(self.pin_number, 0, self.reverse)
            self.timer = 1

        self.timer = self.timer + 1
        #logging.info("counter %s state is %s", self.timer, state)


    def set_relay(self, state):
        if get_gpio_state(self.pin_number, self.reverse) != state:
            if state:
                set_gpio_state(self.pin_number, 1, self.reverse)
            else:
                set_gpio_state(self.pin_number, 0, self.reverse)

    def get_relay_in_use(self, state):
        return True

    # @Accessory.run_at_interval(60)
    # def checks_need_water(self):
    #     logging.info("checks_need_water")
    #     execution_date = datetime.now()
    #     date_stamp = execution_date.strftime("%Y%m%d-%H%M%S")
    #     if True:
    #     # if (execution_date.isoweekday() == 6 
    #     #     and execution_date.hour == 8
    #     #     and execution_date.min in range(0, 3600)):

    #         self._camera.start_record(f"/home/pi/brown/images/{date_stamp}.h264")
    #         self.set_relay(1)
    #         sleep(30)
    #         self._camera.stop_record()
    #     return