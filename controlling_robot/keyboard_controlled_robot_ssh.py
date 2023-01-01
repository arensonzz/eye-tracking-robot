import sys
from time import sleep

from sshkeyboard import listen_keyboard

from robot import Direction, Robot


robot = Robot(left_motor_pins={"forward": 5, "backward": 6, "enable": 12},
              right_motor_pins={"forward": 19, "backward": 26, "enable": 13},
              distance_led_pins={"red": 18, "green": 15, "blue": 14},
              distance_sensor_pins={"trigger": 16, "echo": 21})


def actions(key):
    match key:
        case "up":
            robot.move(Direction.FORWARD, 2, 0.7)
        case "down":
            robot.move(Direction.BACKWARD, 2, 0.7),
        case "left":
            robot.move(Direction.LEFT, 0.40, 0.7),
        case "right":
            robot.move(Direction.RIGHT, 0.40, 0.7),
        case "space":
            robot.stop()


try:
    robot.distance_led.on()
    #  robot.enable_auto_stop()
    sleep(2)
    listen_keyboard(on_press=actions)
except KeyboardInterrupt:
    print("Closing the program.")
    sys.exit()
