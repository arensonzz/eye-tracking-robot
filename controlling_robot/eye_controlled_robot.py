from robot import Robot, Direction
from paho.mqtt.client import mqtt

robot = Robot(left_motor_pins={"forward": 5, "backward": 6, "enable": 12},
              right_motor_pins={"forward": 19, "backward": 26, "enable": 13},
              distance_led_pins={"red": 18, "green": 15, "blue": 14},
              distance_sensor_pins={"trigger": 16, "echo": 21})


def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8")
    match payload:
        case "left":
            robot.move(Direction.LEFT, 0.5, 0.6)
        case "right":
            robot.move(Direction.RIGHT, 0.5, 0.6)
        case "up":
            robot.move(Direction.FORWARD, 0.5, 0.8)
        case "down":
            robot.move(Direction.BACKWARD, 0.5, 0.8)
        case "center":
            robot.stop()


if __name__ == "__main__":

    # Connect to mqtt broker
    # import the client1
    broker_address = "10.42.0.109"
    # broker_address="iot.eclipse.org" #use external broker
    client = mqtt.Client("eye_tracking_rpi")  # create new instance
    client.connect(broker_address)  # connect to broker
    client.subscribe("eye_tracking/rpi")
    client.on_message = on_message
    client.loop_forever()
