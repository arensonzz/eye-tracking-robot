from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui,QtWidgets
from PyQt5.QtNetwork import QUdpSocket, QHostAddress
import sys
import time
import cv2
import threading


class main_GUI(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        ## image box ekleme
        self.imageBox = QtWidgets.QLabel(self)
        self.imageBox.setGeometry(10, 10, 1600, 1000)
        self.imageBox.setText("")
        # self.imageBox.setAutoFillBackground(True)
        color = QtGui.QColor(0, 0, 0)
        alpha = 140
        values = "{r}, {g}, {b}, {a}".format(r=color.red(),
                                             g=color.green(),
                                             b=color.blue(),
                                             a=alpha
                                             )
        self.imageBox.setStyleSheet("QLabel { background-color: rgba(" + values + "); }")
        self.imageBox.show()

        ### Haberleşme ayar paneli
        self.comm_gb=QGroupBox(self)
        self.comm_gb.setObjectName("comm_gb")
        self.comm_gb.setTitle("Communication Settings")
        self.comm_gb.setStyleSheet("QGroupBox#comm_gb{font-size: 20px ;font-weight:bold;color:rgb(204, 204, 255)}")
        self.comm_gb.setGeometry(1630, 10, 275, 200)
        self.comm_gb.show()

        ### Görüntü ayar paneli
        self.video_gb=QGroupBox(self)
        self.video_gb.setObjectName("video_gb")
        self.video_gb.setTitle("Video Setting")
        self.video_gb.setStyleSheet("QGroupBox#video_gb{font-size: 22px ;font-weight:bold;color:rgb(204, 204, 255)}")
        self.video_gb.setGeometry(1630,220,275, 350)
        self.video_gb.show()
        ### Video Başlatma Butonu
        self.video_start_btn =QPushButton(self)
        self.video_start_btn.setGeometry(1640,250, 120, 35)
        self.video_start_btn.setText("Video Start")
        self.video_start_btn.setStyleSheet("color:rgb(255,255,255);")
        self.video_start_btn.setFont(QFont('Times',12))
        ### Video Durdurma Butonu
        self.video_stop_btn =QPushButton(self)
        self.video_stop_btn.setGeometry(1770, 250, 120, 35)
        self.video_stop_btn.setText("Video Stop")
        self.video_stop_btn.setStyleSheet("color:rgb(255,255,255);")
        self.video_stop_btn.setFont(QFont('Times', 12))
        
        ## Bağlantı kurma butonu
        self.conn_start_btn =QPushButton(self)
        self.conn_start_btn.setGeometry(1640, 140, 120, 35)
        self.conn_start_btn.setText("Bağlantı Kur")
        self.conn_start_btn.setStyleSheet("color:rgb(255,255,255);")
        self.conn_start_btn.setFont(QFont('Times', 12))

        ## Bağlantı kapatma butonu
        self.conn_stop_btn =QPushButton(self)
        self.conn_stop_btn.setGeometry(1770, 140, 120, 35)
        self.conn_stop_btn.setText("Bağlantı Kapat")
        self.conn_stop_btn.setStyleSheet("color:rgb(255,255,255);")
        self.conn_stop_btn.setFont(QFont('Times', 12))

        ## Görüntü işleme algoritma başlatma butonu
        self.algo_start_btn =QPushButton(self)
        self.algo_start_btn.setGeometry(1640, 300, 120, 35)
        self.algo_start_btn.setText("Proccess Start")
        self.algo_start_btn.setStyleSheet("color:rgb(255,255,255);")
        self.algo_start_btn.setFont(QFont('Times', 12))

        ## Görüntü işleme algoritma durdurma butonu
        self.algo_stop_btn =QPushButton(self)
        self.algo_stop_btn.setGeometry(1770, 300, 120, 35)
        self.algo_stop_btn.setText("Process Stop")
        self.algo_stop_btn.setStyleSheet("color:rgb(255,255,255);")
        self.algo_stop_btn.setFont(QFont('Times', 12))

        ## İp textbox
        self.ip_tbx = QtWidgets.QLineEdit(self)
        self.ip_tbx.setGeometry(1690, 50, 190, 25)
        self.ip_tbx.setStyleSheet("border: 2px solid rgb(255,214,216);color:rgb(255, 255, 255);")
        self.ip_tbx.setText("")
        self.ip_tbx.show()

        self.ip_label = QtWidgets.QLabel(self)
        self.ip_label.setGeometry(1650 , 50, 40, 20)
        self.ip_label.setText("IP: ")
        self.ip_label.setStyleSheet("color:rgb(255, 255, 255);")
        self.ip_label.setFont(QFont('Trebuchet MS', 11, QFont.Bold))
        self.ip_label.show()

        ## Port textbox
        self.port_txb = QtWidgets.QLineEdit(self)
        self.port_txb.setGeometry(1690, 95, 190, 25)
        self.port_txb.setStyleSheet("border: 2px solid rgb(255,214,216);color:rgb(255, 255, 255);")
        self.port_txb.setText("")
        self.port_txb.show()

        self.port_label = QtWidgets.QLabel(self)
        self.port_label.setGeometry(1650 , 95, 40, 20)
        self.port_label.setText("Port: ")
        self.port_label.setStyleSheet("color:rgb(255, 255, 255);")
        self.port_label.setFont(QFont('Trebuchet MS', 11, QFont.Bold))
        self.port_label.show()

        ## kamera başlatma butonu click
        self.video_start_btn.clicked.connect(self.video_show_setup)
        ## kameraa durdurma butonu click
        self.video_stop_btn.clicked.connect(self.video_stop)
            ## bağlntı kurma butonu click                                   #### buradaki yorum satırlarını açarsınız. arayüzü çalıştırıken sorun çıkmasın diye böyle kapattım.
        #self.conn_start_btn.clicked.connect(self.Connection_start)
            ## bağlantı kapatma butonu click
        #self.conn_stop_btn.clicked.connect(self.Connection_stop)
            ## görüntü işleme başlatma butonu click
        #self.algo_start_btn.clicked.connect(self.algo_start)
            ## görüntü işleme durduma butonu click
        #self.algo_stop_btn.clicked.connect(self.algo_stop)
    
    def video_show_setup(self):
        try:
            self.video_show_thread = threading.Thread(target = self.video_capture)
            self.video_show_thread.setDaemon(True)
            self.video_show_thread.start()
        except Exception as ex:
            print(ex)    

    def video_capture(self):
        #self.cap = cv2.VideoCapture('3.mp4')    ## video görüntüsü açar
        self.cap = cv2.VideoCapture(0)         ## kamera görüntü açar

        while True:
            try:
                success ,frame  = self.cap.read()
                if frame is not None:
                    height, width, channel = frame.shape
                    frame = cv2.resize(frame, None, fx=1, fy=1, interpolation = cv2.INTER_NEAREST)
                    #frame = cv2.resize(frame, (1600,900))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    bpl = channel * width
                    frame = QtGui.QImage(frame.data, width, height, bpl, QtGui.QImage.Format_RGB888)
                    self.imageBox.setPixmap(QPixmap(frame))
                    self.video_start_btn.setEnabled(False)
                    self.video_start_btn.setEnabled(True)
                time.sleep(0.007)
            except Exception as ex:
                print(ex)


    def video_stop(self):
        self.cap.release()
        self.imageBox.clear()
        self.video_start_btn.setEnabled(True)
        self.video_stop_btn.setEnabled(False)


    # def Connection_start(self):  ## Bağlantı burada sağlanacak, pyqt5 in kendi balantı classı var onları import ettim ben. bir sıkntı çıkarsa birlikte inceleriz.
    #     ip_no = self.ui.ip_tbx.text() 
    #     port_no = int(self.ui.port_tbx.text())

    # def Connection_stop(self):  ## Bağlantı burada bitecek
    #     ip_no = self.ui.ip_tbx.text() 
    #     port_no = int(self.ui.port_tbx.text())

    #def algo_start(self):                                      #### fonksiyonları açarsınız içlerini doldurursunuz.
                                                                
    #def algo_stop(self):                                       



app=QApplication(sys.argv)
main_GUI = main_GUI()
main_GUI.showMaximized()
main_GUI.setWindowTitle("Multi-Gruop-80-GUI")
main_GUI.setStyleSheet("background-color:rgb(47,79,79);")
main_GUI.show()
sys.exit(app.exec())
