import sys
from threading import Event

from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
)

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

        self.dialog = QMessageBox(self)
        self.dialog.setWindowTitle("Warning")
        self.dialog.setStyleSheet("color:rgb(255,255,255);")
        self.dialog.setFont(QFont('Trebuchet MS', 12))
        # image box ekleme
        self.image_box = QLabel(self)
        self.image_box.setGeometry(10, 10, 1600, 1200)
        self.image_box.setText("")
        # self.imageBox.setAutoFillBackground(True)
        color = QColor(0, 0, 0)
        alpha = 140
        values = "{r}, {g}, {b}, {a}".format(r=color.red(),
                                             g=color.green(),
                                             b=color.blue(),
                                             a=alpha
                                             )
        self.image_box.setStyleSheet("QLabel { background-color: rgba(" + values + "); }")
        self.image_box.show()

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

        self.direction_gb = QGroupBox(self)
        self.direction_gb.setObjectName("direction_gb")
        self.direction_gb.setTitle("Detected Direction")
        self.direction_gb.setStyleSheet("QGroupBox#direction_gb{font-size: 20px ;font-weight:bold;color:rgb(204, 204, 255)}")
        self.direction_gb.setGeometry(1630, 640, 275, 350)
        self.direction_gb.show()

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
        self.eye_tracking_stop_btn.setEnabled(False)

        # Detected direction textbox
        self.detected_direction_tbx = QLabel(self)
        self.detected_direction_tbx.setGeometry(1640, 700, 120, 20)
        self.detected_direction_tbx.setText("")
        self.detected_direction_tbx.setStyleSheet("color:rgb(255, 255, 255);")
        self.detected_direction_tbx.setFont(QFont('Trebuchet MS', 11, QFont.Bold))
        self.detected_direction_tbx.show()

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
        self.conn_stop_btn.setEnabled(False)

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
        self.port_tbx = QLineEdit(self)
        self.port_tbx.setGeometry(1700, 95, 180, 25)
        self.port_tbx.setStyleSheet("border: 2px solid rgb(255,214,216);color:rgb(255, 255, 255);")
        self.port_tbx.setText("")
        self.port_tbx.show()

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
        try:
            self.is_eye_tracking_stopped.clear()
            self.eye_tracking_thread = EyeTrackingThread(self.is_eye_tracking_stopped, self.image_box)
            self.eye_tracking_thread.daemon = True
            self.eye_tracking_thread.start()

            if self.send_position_thread is not None:
                self.eye_tracking_thread.position_counts = self.send_position_thread.position_counts

            self.eye_tracking_start_btn.setEnabled(False)
            self.eye_tracking_stop_btn.setEnabled(True)
        except Exception as ex:
            print(type(ex).__name__)
            print(ex)
            self.dialog.setText(str(ex))
            self.dialog.exec()

    def eye_tracking_stop(self):
        self.is_eye_tracking_stopped.set()
        self.eye_tracking_thread.video_capture.release()
        self.image_box.clear()
        self.eye_tracking_thread = None
        self.eye_tracking_stop_btn.setEnabled(False)
        self.eye_tracking_start_btn.setEnabled(True)

    def on_message(message):
        payload = message.payload.decode("utf-8")
        print(payload)

    def connection_start(self):
        class EmptyIpException(Exception):
            """Exception raised when IP field is left empty."""

            def __init__(self, *args: object) -> None:
                super().__init__(*args)

        class EmptyPortException(Exception):
            """Exception raised when port field is left empty."""

            def __init__(self, *args: object) -> None:
                super().__init__(*args)

        # Connect to mqtt broker first time button is pressed
        # and initialize send_position_thread
        try:
            ip_no = self.ip_tbx.text()
            port_no = self.port_tbx.text()
            if not(ip_no and ip_no.strip()):
                raise EmptyIpException("IP number cannot be empty.")
            if not(port_no and port_no.strip()):
                raise EmptyPortException("Port number cannot be empty.")
            port_no = int(port_no)
            client.connect(host=ip_no, port=port_no)  # connect to broker
            client.loop_start()  # start the loop
            client.subscribe("eye_tracking/pc")
            client.on_message = self.on_message
        except (EmptyIpException, EmptyPortException) as ex:
            self.dialog.setText(str(ex))
            self.dialog.exec()
        except ValueError:
            self.dialog.setText("""Port number is not an integer.""")
            self.dialog.exec()
        except Exception as ex:
            print(type(ex).__name__)
            print(ex)
            self.dialog.setText("Could not connect to the Raspberry Pi. Make sure the device is on and connection settings are correct.")
            self.dialog.exec()
        else:
            try:
                self.is_send_position_stopped.clear()
                self.send_position_thread = SendPositionThread(self.is_send_position_stopped,
                                                               self.detected_direction_tbx)
                # Share positiong_counts from send_position to eye_tracking for automatic update
                if self.eye_tracking_thread is not None:
                    self.eye_tracking_thread.position_counts = self.send_position_thread.position_counts
                self.send_position_thread.daemon = True
                self.send_position_thread.start()

                self.conn_start_btn.setEnabled(False)
                self.conn_stop_btn.setEnabled(True)
            except Exception as ex:
                print(type(ex).__name__)
                print(ex)
                self.dialog.setText(str(ex))
                self.dialog.exec()

    def connection_stop(self):
        self.is_send_position_stopped.set()
        client.loop_stop()
        self.detected_direction_tbx.setText("")
        self.send_position_thread = None
        self.conn_stop_btn.setEnabled(False)
        self.conn_start_btn.setEnabled(True)


app = QApplication(sys.argv)
main_GUI = main_GUI()
main_GUI.showMaximized()
main_GUI.setWindowTitle("Multi-Group-80-GUI")
main_GUI.setStyleSheet("background-color:rgb(47,79,79);")
main_GUI.show()
sys.exit(app.exec())
