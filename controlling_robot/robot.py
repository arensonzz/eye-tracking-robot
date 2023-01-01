from __future__ import annotations
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
        # _range_to_color is used to convert a distance value into corresponding color value. Array has 101 elements
        # and first 30%
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


class CurrentMove(Thread):
    def __init__(self, robot: Robot, direction: Direction, duration_sec: int, speed: float, is_stuck: Event,
                 daemon=False):
        super().__init__(daemon=daemon)
        self._robot = robot
        self._direction = direction
        self._duration_sec = duration_sec
        self._speed = speed
        self._is_stuck = is_stuck
        self.is_disabled = Event()

    def run(self):
        self._move_callback()

    def _move_callback(self):
        duration_sec = abs(self._duration_sec)
        if self._speed < 0 or self._speed > 1:
            raise RuntimeWarning("Speed must be a float number between 0 and 1.")
        match self._direction:
            case Direction.LEFT:
                self._robot._left_motors.backward(self._speed)
                self._robot._right_motors.forward(self._speed)
            case Direction.RIGHT:
                self._robot._left_motors.forward(self._speed)
                self._robot._right_motors.backward(self._speed)
            case Direction.FORWARD:
                if self._is_stuck.is_set():
                    return
                self._robot._left_motors.forward(self._speed)
                self._robot._right_motors.forward(self._speed)
            case Direction.BACKWARD:
                self._robot._left_motors.backward(self._speed)
                self._robot._right_motors.backward(self._speed)

        sleep(duration_sec)
        if not self.is_disabled.is_set():
            self._robot.stop()


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
        self._auto_stop_event = Event()  # _auto_stop continues to work until this is set
        self._is_stuck = Event()  # forward move is disabled if this is set

        self._current_move_thread: CurrentMove = None
        self._auto_stop_thread = None

    def _auto_stop(self):
        while not self._auto_stop_event.is_set():
            # If robot is in range of the obstacle then activate escape event and disable auto stop until escaped
            if self._distance_sensor.in_range:
                self._is_stuck.set()
                if self._current_move_thread is not None and self._current_move_thread._direction == Direction.FORWARD:
                    self._current_move_thread.is_disabled.set()
                    self.stop()
            else:
                self._is_stuck.clear()

            sleep(0.1)

    def enable_auto_stop(self):
        self._auto_stop_event.clear()
        self._is_stuck.clear()
        self._auto_stop_thread = Thread(target=self._auto_stop, args=())
        self._auto_stop_thread.daemon = True
        self._auto_stop_thread.start()

    def disable_auto_stop(self):
        self._auto_stop_event.set()
        self._is_stuck.clear()

    def stop(self):
        if self._current_move_thread is not None:
            self._current_move_thread.is_disabled.set()
        self._left_motors.stop()
        self._right_motors.stop()

    def move(self, direction: Direction, duration_sec: float, speed: float):
        if self._current_move_thread is not None:
            self._current_move_thread.is_disabled.set()

        self._current_move_thread = CurrentMove(self, direction, duration_sec, speed, self._is_stuck)
        self._current_move_thread.start()


if __name__ == "__main__":
    robot = Robot(left_motor_pins={"forward": 5, "backward": 6, "enable": 12},
                  right_motor_pins={"forward": 19, "backward": 26, "enable": 13},
                  distance_led_pins={"red": 18, "green": 15, "blue": 14},
                  distance_sensor_pins={"trigger": 16, "echo": 21})
