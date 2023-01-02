import sys
import threading
from threading import Event, Thread
import time

from PyQt5.QtGui import QColor, QFont, QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
)
import cv2
import paho.mqtt.client as mqtt

from app import client
from app.eye_tracking import EyeTrackingThread, SendPositionThread


class main_GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # Eye tracking related threads
        self.send_position_thread: SendPositionThread = None
        self.is_send_position_stopped = Event()

        self.eye_tracking_thread: EyeTrackingThread = None
        self.is_eye_tracking_stopped = Event()

        # image box ekleme
        self.imageBox = QLabel(self)
        self.imageBox.setGeometry(10, 10, 1600, 1000)
        self.imageBox.setText("")
        # self.imageBox.setAutoFillBackground(True)
        color = QColor(0, 0, 0)
        alpha = 140
        values = "{r}, {g}, {b}, {a}".format(r=color.red(),
                                             g=color.green(),
                                             b=color.blue(),
                                             a=alpha
                                             )
        self.imageBox.setStyleSheet("QLabel { background-color: rgba(" + values + "); }")
        self.imageBox.show()

        # Haberleşme ayar paneli
        self.comm_gb = QGroupBox(self)
        self.comm_gb.setObjectName("comm_gb")
        self.comm_gb.setTitle("Car Communication Settings")
        self.comm_gb.setStyleSheet("QGroupBox#comm_gb{font-size: 20px ;font-weight:bold;color:rgb(204, 204, 255)}")
        self.comm_gb.setGeometry(1630, 10, 275, 250)
        self.comm_gb.show()

        # Görüntü işleme ayar paneli
        self.video_gb = QGroupBox(self)
        self.video_gb.setObjectName("video_gb")
        self.video_gb.setTitle("Eye Tracking Settings")
        self.video_gb.setStyleSheet("QGroupBox#video_gb{font-size: 20px ;font-weight:bold;color:rgb(204, 204, 255)}")
        self.video_gb.setGeometry(1630, 270, 275, 350)
        self.video_gb.show()

        # Görüntü İşleme Başlatma Butonu
        self.eye_tracking_start_btn = QPushButton(self)
        self.eye_tracking_start_btn.setGeometry(1640, 320, 240, 35)
        self.eye_tracking_start_btn.setText("Start Tracking")
        self.eye_tracking_start_btn.setStyleSheet("color:rgb(255,255,255);")
        self.eye_tracking_start_btn.setFont(QFont('Times', 12))
        # Görüntü İşleme Durdurma Butonu
        self.eye_tracking_stop_btn = QPushButton(self)
        self.eye_tracking_stop_btn.setGeometry(1640, 370, 240, 35)
        self.eye_tracking_stop_btn.setText("Stop Tracking")
        self.eye_tracking_stop_btn.setStyleSheet("color:rgb(255,255,255);")
        self.eye_tracking_stop_btn.setFont(QFont('Times', 12))

        # Bağlantı kurma butonu
        self.conn_start_btn = QPushButton(self)
        self.conn_start_btn.setGeometry(1640, 150, 240, 35)
        self.conn_start_btn.setText("Start Sending Commands")
        self.conn_start_btn.setStyleSheet("color:rgb(255,255,255);")
        self.conn_start_btn.setFont(QFont('Times', 12))

        # Bağlantı kapatma butonu
        self.conn_stop_btn = QPushButton(self)
        self.conn_stop_btn.setGeometry(1640, 200, 240, 35)
        self.conn_stop_btn.setText("Stop Sending Commands")
        self.conn_stop_btn.setStyleSheet("color:rgb(255,255,255);")
        self.conn_stop_btn.setFont(QFont('Times', 12))

        # IP textbox
        self.ip_tbx = QLineEdit(self)
        self.ip_tbx.setGeometry(1700, 50, 180, 25)
        self.ip_tbx.setStyleSheet("border: 2px solid rgb(255,214,216);color:rgb(255, 255, 255);")
        self.ip_tbx.setText("")
        self.ip_tbx.show()

        self.ip_label = QLabel(self)
        self.ip_label.setGeometry(1640, 50, 50, 20)
        self.ip_label.setText("IP: ")
        self.ip_label.setStyleSheet("color:rgb(255, 255, 255);")
        self.ip_label.setFont(QFont('Trebuchet MS', 11, QFont.Bold))
        self.ip_label.show()

        # Port textbox
        self.port_txb = QLineEdit(self)
        self.port_txb.setGeometry(1700, 95, 180, 25)
        self.port_txb.setStyleSheet("border: 2px solid rgb(255,214,216);color:rgb(255, 255, 255);")
        self.port_txb.setText("")
        self.port_txb.show()

        self.port_label = QLabel(self)
        self.port_label.setGeometry(1640, 95, 50, 20)
        self.port_label.setText("Port: ")
        self.port_label.setStyleSheet("color:rgb(255, 255, 255);")
        self.port_label.setFont(QFont('Trebuchet MS', 11, QFont.Bold))
        self.port_label.show()

        self.eye_tracking_start_btn.clicked.connect(self.eye_tracking_start)
        self.eye_tracking_stop_btn.clicked.connect(self.eye_tracking_stop)
        self.conn_start_btn.clicked.connect(self.connection_start)
        self.conn_stop_btn.clicked.connect(self.connection_stop)

    def eye_tracking_start(self):
        if self.eye_tracking_thread is None:
            self.eye_tracking_thread = EyeTrackingThread(self.is_eye_tracking_stopped)
            self.eye_tracking_thread.daemon = True
            self.eye_tracking_thread.start()

        if self.send_position_thread is not None:
            self.eye_tracking_thread.position_counts = self.send_position_thread.position_counts

        self.is_eye_tracking_stopped.clear()

        try:
            self.video_show_thread = Thread(target=self.video_capture)
            self.video_show_thread.daemon = True
            self.video_show_thread.start()
        except Exception as ex:
            print(ex)
        self.eye_tracking_start_btn.setEnabled(False)
        self.eye_tracking_start_btn.setEnabled(True)

    def video_capture(self):
        while not self.is_eye_tracking_stopped.is_set():
            try:
                frame = self.eye_tracking_thread.frame
                if frame is not None:
                    height, width, channel = frame.shape
                    frame = cv2.resize(frame, None, fx=1, fy=1, interpolation=cv2.INTER_NEAREST)
                    # frame = cv2.resize(frame, (1600,900))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    bpl = channel * width
                    frame = QImage(frame.data, width, height, bpl, QImage.Format_RGB888)
                    self.imageBox.setPixmap(QPixmap(frame))
                time.sleep(0.007)
            except Exception as ex:
                print("Warning: Eye tracking has not started!")
                print(ex)

    def eye_tracking_stop(self):
        #  self.cap.release()
        self.
        self.imageBox.clear()
        self.is_eye_tracking_stopped.set()
        self.eye_tracking_start_btn.setEnabled(True)
        self.eye_tracking_stop_btn.setEnabled(False)

    def on_message(message):
        payload = message.payload.decode("utf-8")
        print(payload)

    def connection_start(self):
        # Connect to mqtt broker first time button is pressed
        # and initialize send_position_thread
        if self.send_position_thread is None:
            ip_no = self.ui.ip_tbx.text()
            port_no = int(self.ui.port_tbx.text())
            client.connect(host=ip_no, port=port_no)  # connect to broker
            client.loop_start()  # start the loop
            client.subscribe("eye_tracking/pc")
            client.on_message = self.on_message
            self.send_position_thread = SendPositionThread(self.is_send_position_stopped)
            # Share positiong_counts from send_position to eye_tracking for automatic update
            if self.eye_tracking_thread is not None:
                self.eye_tracking_thread.position_counts = self.send_position_thread.position_counts
            self.send_position_thread.daemon = True
            self.send_position_thread.start()
        # Restart thread if stopped
        self.is_send_position_stopped.clear()

    def connection_stop(self):
        self.is_send_position_stopped.set()


app = QApplication(sys.argv)
main_GUI = main_GUI()
main_GUI.showMaximized()
main_GUI.setWindowTitle("Multi-Gruop-80-GUI")
main_GUI.setStyleSheet("background-color:rgb(47,79,79);")
main_GUI.show()
app.exec()
#  video_capture.release()
