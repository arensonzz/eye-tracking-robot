from gpiozero import Motor, OutputDevice, Device, RGBLED, DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
from threading import Thread, Event
from enum import Enum, auto


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


class Robot(object):
    """Controller for a robot with 2 sets of wheels (6V DC) and an ultrasonic sensor (HC-SR04)."""
    class Direction(Enum):
        """Available directions to move the car."""
        LEFT = auto()
        RIGHT = auto()
        FORWARD = auto()
        BACKWARD = auto()

    def __init__(self, left_motor_pins: dict, right_motor_pins: dict, distance_led_pins: dict,
                 distance_sensor_pins: dict):
        self._pwm_factory = PiGPIOFactory()
        self._left_motors = Motor(**left_motor_pins, pin_factory=self._pwm_factory)
        self._right_motors = Motor(**right_motor_pins, pin_factory=self._pwm_factory)
        self._distance_sensor = DistanceSensor(**distance_sensor_pins, max_distance=2, pin_factory=self._pwm_factory,
                                               threshold_distance=0.6)
        self._distance_led = DistanceLed(**distance_led_pins, max_distance=2, distance_sensor=self._distance_sensor)
        self._range_event = Event()
        self._range_thread = Thread(target=self._stop_when_in_range, args=(self._range_event,))

    def _stop_when_in_range(self):
        while not self._range_event.is_set():
            if self._distance_sensor.in_range():
                self.stop()
            sleep(0.1)

    def enable_auto_stop(self):
        self._range_thread.run()

    def disable_auto_stop(self):
        self._range_event.set()

    def close_devices(self):
        """Gracefully shutdown all GPIO devices."""
        self._left_motors.close()
        self._right_motors.close()
        self._distance_led.close()
        self._distance_sensor.close()

    def stop(self):
        self._left_motors.stop()
        self._right_motors.stop()

    def move(self, direction: Direction, duration_sec: float, speed: float):
        duration_sec = abs(duration_sec)
        if speed < 0 or speed > 1:
            raise RuntimeWarning("Speed must be a float number between 0 and 1.")
        match direction:
            case Robot.Direction.LEFT:
                self._left_motors.backward(speed)
                self._right_motors.forward(speed)
            case Robot.Direction.RIGHT:
                self._left_motors.forward(speed)
                self._right_motors.backward(speed)
            case Robot.Direction.FORWARD:
                self._left_motors.forward(speed)
                self._right_motors.forward(speed)
            case Robot.Direction.BACKWARD:
                self._left_motors.backward(speed)
                self._right_motors.backward(speed)

        Thread(target=sleep, args=(duration_sec,)).run()
        self.stop()


if __name__ == "__main__":
    robot = Robot(left_motor_pins={"forward": 5, "backward": 6, "enable": 12},
                  right_motor_pins={"forward": 19, "backward": 26, "enable": 13},
                  distance_led_pins={"red": 18, "green": 15, "blue": 14},
                  distance_sensor_pins={"trigger": 16, "echo": 21})
    try:
        robot._distance_led.on()
        #  robot.enable_auto_stop()
        sleep(3)
        robot.move(Robot.Direction.FORWARD, 10, 0.5)
        robot._distance_led.off()
        #  robot.disable_auto_stop()
        sleep()

    except KeyboardInterrupt:
        print("Goodbye my lover!")
    finally:
        robot.close_devices()
