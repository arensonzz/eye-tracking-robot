import math
from threading import Event, Thread

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel
import cv2 as cv
import mediapipe as mp
import numpy as np

from . import client

# CONSTANTS
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


class SendPositionThread(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event
        self.position_counts = {"left": 0, "right": 0, "up": 0, "down": 0, "center": 0}

    def run(self):
        while not self.stopped.wait(1.5):
            arr = list(self.position_counts.items())
            max = arr[0]
            for key, val in arr:
                if val > max[1]:
                    max = (key, val)
            if max[1] >= 10:
                print("Sending move: ", max)
                client.publish("eye_tracking/rpi", max[0])

            self.position_counts["left"] = 0
            self.position_counts["right"] = 0
            self.position_counts["up"] = 0
            self.position_counts["down"] = 0
            self.position_counts["center"] = 0


class EyeTrackingThread(Thread):
    def __init__(self, event: Event, image_box: QLabel = None):
        Thread.__init__(self)

        self.image_box = image_box
        self.stopped = event

        self.position_counts = None
        self.mp_face_mesh = mp.solutions.face_mesh
        self.ratio_list = []
        self.blink_counter = 0
        self.counter = 0
        self.video_capture = cv.VideoCapture(0)  # kamera görüntü açar
        self.mask = None
        self.frame = None

        #  self.fourrcc = cv.VideoWriter_fourcc(*'XVID')
        #  self.video = cv.VideoWriter('video.avi', self.fourrcc, 9.0, (640, 480))

    def distance(self, point1, point2):
        x1, y1 = point1.ravel()
        x2, y2 = point2.ravel()
        distance: float = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return distance

    def iris_position(self, iris_center, right_point, left_point, up_point, down_point):
        center_to_right_distance = self.distance(iris_center, right_point)
        center_to_up_distance = self.distance(iris_center, up_point)
        total_r2l_distance = self.distance(right_point, left_point)
        total_u2d_distance = self.distance(up_point, down_point)
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

    def run(self):
        # Start position thread
        with self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as face_mesh:
            while not self.stopped.wait(0.00001):
                ret, self.frame = self.video_capture.read()
                if not ret:
                    break
                self.frame = cv.flip(self.frame, 1)

                rgb_frame = cv.cvtColor(self.frame, cv.COLOR_BGR2RGB)
                img_h, img_w = self.frame.shape[:2]
                results = face_mesh.process(rgb_frame)
                self.mask = np.zeros((img_h, img_w), dtype=np.uint8)

                if results.multi_face_landmarks:
                    mesh_points = np.array([np.multiply([p.x, p.y], [img_w, img_h]).astype(int)
                                            for p in results.multi_face_landmarks[0].landmark])

                    (l_cx, l_cy), l_radius = cv.minEnclosingCircle(mesh_points[LEFT_IRIS])
                    (r_cx, r_cy), r_radius = cv.minEnclosingCircle(mesh_points[RIGHT_IRIS])
                    center_left = np.array([l_cx, l_cy], dtype=np.int32)
                    center_right = np.array([r_cx, r_cy], dtype=np.int32)
                    cv.circle(self.frame, center_left, int(l_radius), (0, 255, 0), 1, cv.LINE_AA)
                    cv.circle(self.frame, center_right, int(r_radius), (0, 255, 0), 1, cv.LINE_AA)

                    cv.circle(self.mask, center_left, int(l_radius), (255, 255, 255), -1, cv.LINE_AA)
                    cv.circle(self.mask, center_right, int(r_radius), (255, 255, 255), -1, cv.LINE_AA)

                    position_of_iris, ratio1, ratio2, total1, total2 = self.iris_position(center_right, mesh_points[R_H_RIGHT],
                                                                                          mesh_points[R_H_LEFT][0],
                                                                                          mesh_points[U_H_RIGHT],
                                                                                          mesh_points[D_H_RIGHT][0])
                    ratio = (total2 / total1) * 100
                    self.ratio_list.append(ratio)
                    if len(self.ratio_list) > 3:
                        self.ratio_list.pop(0)
                    ratio_avg = sum(self.ratio_list) / len(self.ratio_list)

                    if ratio_avg < 45 and self.counter == 0:
                        # Person blinked
                        self.blink_counter += 1
                        self.counter = 1
                        cv.putText(self.frame, "blink", (10, 70), cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 3)
                        if self.position_counts is not None:
                            self.position_counts["blink"] += 1
                    else:
                        # Person did not blink
                        if self.position_counts is not None:
                            self.position_counts[position_of_iris] += 1
                        #  print("Position: ", position_of_iris)
                        cv.putText(self.frame, position_of_iris, (10, 70), cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 3)

                    if self.counter != 0:
                        self.counter += 1
                        if self.counter >= 10:
                            self.counter = 0

                if self.blink_counter >= 2:
                    self.blink_counter = 0

                if self.image_box is not None:
                    # Display current frame in PyQt5 GUI
                    scale_percent = 250  # percent of original size
                    width = int(self.frame.shape[1] * scale_percent / 100)
                    height = int(self.frame.shape[0] * scale_percent / 100)
                    dim = (width, height)
                    resized_img = cv.resize(self.frame, dim, interpolation=cv.INTER_AREA)
                    q_image = QImage(resized_img.data, resized_img.shape[1], resized_img.shape[0],
                                     QImage.Format_RGB888).rgbSwapped()
                    self.image_box.setPixmap(QPixmap.fromImage(q_image))
                else:
                    # Display current frame in opencv GUI
                    cv.imshow('Mask', eye_tracking_thread.mask)
                    cv.imshow('img', eye_tracking_thread.frame)
                    key = cv.waitKey(1)
                    if key == ord('q'):
                        stop_tracking.set()
                # Save frames as video
                #  self.video.write(self.frame)


if __name__ == "__main__":
    stop_tracking = Event()
    position_counts = {"left": 0, "right": 0, "up": 0, "down": 0, "center": 0}
    eye_tracking_thread = EyeTrackingThread(stop_tracking)
    eye_tracking_thread.start()
    eye_tracking_thread.join()
    cv.destroyAllWindows()
