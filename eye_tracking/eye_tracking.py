import math
from threading import Event, Thread

import paho.mqtt.client as mqtt

import cv2 as cv
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh

# left eyes indices
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
# right eyes indices
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]

# irises Indices list
RIGHT_IRIS = [474, 475, 476, 477]
LEFT_IRIS = [469, 470, 471, 472]
L_H_LEFT = [33]
L_H_RIGHT = [133]
R_H_LEFT = [362]
R_H_RIGHT = [263]
U_H_RIGHT = [159]
D_H_RIGHT = [145]
U_H_RIGHT = [387]
D_H_RIGHT = [374]

POSITION_COUNTS = {"left": 0, "right": 0, "up": 0, "down": 0, "center": 0}

# Connect to mqtt broker
# import the client1
broker_address = "10.42.0.109"
# broker_address="iot.eclipse.org" #use external broker
client = mqtt.Client("eye_tracking_pc")  # create new instance
client.connect(broker_address)  # connect to broker


def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8")
    print(payload)


class PositionThread(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event

    def run(self):
        global POSITION_COUNTS
        while not self.stopped.wait(2):
            arr = list(POSITION_COUNTS.items())
            max = arr[0]
            for key, val in arr:
                if val > max[1]:
                    max = (key, val)
            print(max)
            client.publish("eye_tracking/rpi", max[0])

            POSITION_COUNTS = {"left": 0, "right": 0, "up": 0, "down": 0, "center": 0}


def distance(point1, point2):
    x1, y1 = point1.ravel()
    x2, y2 = point2.ravel()
    distance: float = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance


def iris_position(iris_center, right_point, left_point, up_point, down_point):
    center_to_right_distance = distance(iris_center, right_point)
    center_to_up_distance = distance(iris_center, up_point)
    total_r2l_distance = distance(right_point, left_point)
    total_u2d_distance = distance(up_point, down_point)
    ratio_r2l = center_to_right_distance / total_r2l_distance
    ratio_u2d = center_to_up_distance / total_u2d_distance

    if ratio_r2l < 0.42:
        position_of_iris: str = "right"
    elif 0.42 <= ratio_r2l < 0.57:
        if ratio_u2d < 0.7:
            position_of_iris: str = "up"
        elif 0.70 <= ratio_u2d < 0.8:
            position_of_iris: str = "center"
        else:
            position_of_iris: str = "down"
    else:
        position_of_iris: str = "left"
    return position_of_iris, ratio_r2l, ratio_u2d, total_r2l_distance, total_u2d_distance


ratio_list = []
blink_counter = 0
counter = 0

cap = cv.VideoCapture(0)
fourrcc = cv.VideoWriter_fourcc(*'XVID')
video = cv.VideoWriter('video.avi', fourrcc, 9.0, (640, 480))

# Start position thread
stopFlag = Event()
send_position_thread = PositionThread(stopFlag)
send_position_thread.daemon = True
send_position_thread.start()

client.loop_start()  # start the loop
client.subscribe("eye_tracking/pc")
client.on_message = on_message

with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
) as face_mesh:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv.flip(frame, 1)

        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        img_h, img_w = frame.shape[:2]
        results = face_mesh.process(rgb_frame)
        mask = np.zeros((img_h, img_w), dtype=np.uint8)

        if results.multi_face_landmarks:
            mesh_points = np.array([np.multiply([p.x, p.y], [img_w, img_h]).astype(int)
                                    for p in results.multi_face_landmarks[0].landmark])

            (l_cx, l_cy), l_radius = cv.minEnclosingCircle(mesh_points[LEFT_IRIS])
            (r_cx, r_cy), r_radius = cv.minEnclosingCircle(mesh_points[RIGHT_IRIS])
            center_left = np.array([l_cx, l_cy], dtype=np.int32)
            center_right = np.array([r_cx, r_cy], dtype=np.int32)
            cv.circle(frame, center_left, int(l_radius), (0, 255, 0), 1, cv.LINE_AA)
            cv.circle(frame, center_right, int(r_radius), (0, 255, 0), 1, cv.LINE_AA)

            cv.circle(mask, center_left, int(l_radius), (255, 255, 255), -1, cv.LINE_AA)
            cv.circle(mask, center_right, int(r_radius), (255, 255, 255), -1, cv.LINE_AA)

            position_of_iris, ratio1, ratio2, total1, total2 = iris_position(center_right, mesh_points[R_H_RIGHT],
                                                                             mesh_points[R_H_LEFT][0],
                                                                             mesh_points[U_H_RIGHT],
                                                                             mesh_points[D_H_RIGHT][0])
            POSITION_COUNTS[position_of_iris] += 1
            ratio = (total2 / total1) * 100
            ratio_list.append(ratio)
            if len(ratio_list) > 3:
                ratio_list.pop(0)
            ratio_avg = sum(ratio_list) / len(ratio_list)

            if ratio_avg < 45 and counter == 0:
                blink_counter += 1
                counter = 1
                cv.putText(frame, "blink", (10, 70), cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 3)

            else:
                #  print(position_of_iris)
                #  print(ratio2)
                cv.putText(frame, position_of_iris, (10, 70), cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 3)

            if counter != 0:
                counter += 1
                if counter >= 10:
                    counter = 0

        if blink_counter >= 2:
            blink_counter = 0

        cv.imshow('Mask', mask)
        video.write(frame)
        cv.imshow('img', frame)
        key = cv.waitKey(1)
        if key == ord('q'):
            break

cap.release()
cv.destroyAllWindows()
client.loop_stop()
