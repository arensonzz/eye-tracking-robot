from enum import Enum, auto
from threading import Event, Thread
from time import sleep

from gpiozero import DistanceSensor, Motor, RGBLED
from gpiozero.pins.pigpio import PiGPIOFactory


class DistanceLed(RGBLED):
    """A RGBLED that changes color according to distance value coming from DistanceSensor."""

    def __init__(self, red=None, green=None, blue=None, active_high=True, initial_value=(0, 0, 0), pwm=True,
                 pin_factory=None, max_distance: int = 1, distance_sensor: DistanceSensor = None):
        super().__init__(red, green, blue, active_high, initial_value, pwm, pin_factory)
        self._is_active = False
        # _range_to_color is used to convert a distance value into corresponding color value. Array has 101 elements so
        #
        self._range_to_color = [(0.5, 0, 0)] * 30 + [(0.5, 0.5, 0)] * 36 + [(0, 0, 0.5)] * 35
        self._max_distance = max_distance
        self._distance_sensor = distance_sensor

    def _distance_generator(self):
        while self._is_active:
            color = self._range_to_color[int(self._distance_sensor.distance * 100 /
                                             self._max_distance)]
            yield color

    def on(self):
        self._is_active = True
        self.source = self._distance_generator()

    def off(self):
        self._is_active = False
        self.source = None
        self.value = (0, 0, 0)


class Direction(Enum):
    """Available directions to move the car."""
    LEFT = auto()
    RIGHT = auto()
    FORWARD = auto()
    BACKWARD = auto()


class Robot(object):
    """Controller for a robot with 2 sets of wheels (6V DC) and an ultrasonic sensor (HC-SR04)."""

    def __init__(self, left_motor_pins: dict, right_motor_pins: dict, distance_led_pins: dict,
                 distance_sensor_pins: dict):

        self._pwm_factory = PiGPIOFactory()
        self._left_motors = Motor(**left_motor_pins, pin_factory=self._pwm_factory)
        self._right_motors = Motor(**right_motor_pins, pin_factory=self._pwm_factory)
        self._distance_sensor = DistanceSensor(**distance_sensor_pins, max_distance=2, pin_factory=self._pwm_factory,
                                               threshold_distance=0.6)
        self.distance_led = DistanceLed(**distance_led_pins, max_distance=2, distance_sensor=self._distance_sensor)
        self._auto_stop_event = Event()  # _stop_when_in_range continues to work until this is set
        self.enable_auto_stop()
        self.distance_led.on()

        self._current_job_thread = None
        self._auto_stop_thread = Thread(target=self._auto_stop, args=())
        self._auto_stop_thread.daemon = True
        self._auto_stop_thread.start()

    def _auto_stop(self):
        while not self._auto_stop_event.is_set():
            if self._distance_sensor.in_range:
                self.stop()
                #  self.disable_auto_stop()
            sleep(0.1)

    def enable_auto_stop(self):
        #  self.distance_led.on()
        self._auto_stop_event.clear()

    def disable_auto_stop(self):
        # self.distance_led.off()
        self._auto_stop_event.set()

    def stop(self):
        self._left_motors.stop()
        self._right_motors.stop()

    def _move_callback(self, direction: Direction, duration_sec: float, speed: float):
        duration_sec = abs(duration_sec)
        if speed < 0 or speed > 1:
            raise RuntimeWarning("Speed must be a float number between 0 and 1.")
        match direction:
            case Direction.LEFT:
                self._left_motors.backward(speed)
                self._right_motors.forward(speed)
            case Direction.RIGHT:
                self._left_motors.forward(speed)
                self._right_motors.backward(speed)
            case Direction.FORWARD:
                self._left_motors.forward(speed)
                self._right_motors.forward(speed)
            case Direction.BACKWARD:
                self._left_motors.backward(speed)
                self._right_motors.backward(speed)

        sleep(duration_sec)
        #  Enable auto stop daemon if escaped from the obstacle
        #  if self._auto_stop_event.is_set():
        #      if not self._distance_sensor.in_range:
        #          self.enable_auto_stop()

        self.stop()

    def move(self, direction: Direction, duration_sec: float, speed: float):
        self._current_job_thread = Thread(target=self._move_callback, args=(direction, duration_sec, speed))
        self._current_job_thread.start()


if __name__ == "__main__":
    robot = Robot(left_motor_pins={"forward": 5, "backward": 6, "enable": 12},
                  right_motor_pins={"forward": 19, "backward": 26, "enable": 13},
                  distance_led_pins={"red": 18, "green": 15, "blue": 14},
                  distance_sensor_pins={"trigger": 16, "echo": 21})
