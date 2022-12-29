from robot import Robot, Direction
import curses


robot = Robot(left_motor_pins={"forward": 5, "backward": 6, "enable": 12},
              right_motor_pins={"forward": 19, "backward": 26, "enable": 13},
              distance_led_pins={"red": 18, "green": 15, "blue": 14},
              distance_sensor_pins={"trigger": 16, "echo": 21})

actions = {
    curses.KEY_UP: robot.move(Direction.FORWARD, 1, 0.8),
    curses.KEY_DOWN: robot.move(Direction.BACKWARD, 1, 0.8),
    curses.KEY_LEFT: robot.move(Direction.LEFT, 0.5, 0.6),
    curses.KEY_RIGHT: robot.move(Direction.RIGHT, 0.5, 0.6),
}


def main(window):
    robot.enable_auto_stop()
    robot.distance_led.on()
    next_key = None
    while True:
        curses.halfdelay(1)
        if next_key is None:
            key = window.getch()
        else:
            key = next_key
            next_key = None
        if key != -1:
            # KEY PRESSED
            curses.halfdelay(3)
            action = actions.get(key)
            if action is not None:
                action()
            next_key = key
            while next_key == key:
                next_key = window.getch()
            # KEY RELEASED
            robot.stop()


curses.wrapper(main)
