import sys
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,QCheckBox)
from PyQt5.QtCore import Qt, QTimer,pyqtSignal,QObject,QThread,QDate,QTime
from PyQt5.QtWidgets import QPushButton, QDialog, QGroupBox,QComboBox, QHBoxLayout, QVBoxLayout, QGridLayout, \
    QScrollArea, QTextEdit, QMessageBox, QLabel, QSizePolicy
from PyQt5.QtGui import QTextCursor, QFont

import serial
import threading
import time
auto = True
RMODE = 99   #0=Terminal, 1=rssi,  3=rec, 99=idn,
port = 'COM17'
baudrate = 115200
CMDs = ["idn?,0,0","idn?,0,222",
        "idn?,3,0","idn?,3,222",
        "rssi?,0,0","rssi?,0,222",
        "rssi?,3,0","rssi?,3,222","no command"]
TEST_SETUP_MSB_GCS = "Steps: \n\n" \
                  + "1.-???????:\n" \
                  + "   ????: ANT#4\n"\
                  + "   ????: ANT#1\n" \
                  + "???????,\n\n"
# Globals
serial_connection = None
receive_thread = None
send_thread = None
serial_port = None
tower = 3
rssi = 0
station = "-"
idn = "-"
delay_current   = 0.6 #0.35    #0.6 ,1,1.2
delay_rssi      = 0.4 #0.155       #0.15,0.4,1.2      failed with 0.05
delay_idn       = 1.0 #0.35            #0.6,1.1,2

def switch_mode(argument):
    global RMODE, delay_current,delay_rssi,delay_idn
    match argument:
        case 1:
            result = "rssi?,"+str(tower)+",111"
            delay_current = delay_rssi
        case 2:
            result = "rec?," + str(tower) + ",112"
            delay_current = delay_idn

        case 99:
            result = "idn?,"+str(tower)+",222"
            delay_current = delay_idn
            #RMODE = 2


        case _:
            result = "error mode"
    return result
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False



class VoltmeterDisplay(QWidget):
    eventlogInt = pyqtSignal(int)
    eventlogStr = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GCS")
        #self.setGeometry(100, 100, 300, 200)
        self.left = 500
        self.top = 200
        self.width = 1080
        self.height = 1000
        self.setGeometry(self.left, self.top, self.width, self.height)
        #####self.iconName = "???????????????????.PNG"

        self.layout = QVBoxLayout()

        self.voltage_label = QLabel("G r o u n d    C o n t r o l    S t a t i o n")
        self.voltage_label.setAlignment(Qt.AlignCenter)
        self.voltage_label.setStyleSheet("font-size: 64px;font-weight: bold;italic;")
        self.layout.addWidget(self.voltage_label)

        self.unit_label = QLabel("System configuration, verification, regression test, POST (Power On Self Test) and readiness")
        self.unit_label.setAlignment(Qt.AlignCenter)
        self.unit_label.setStyleSheet("font-size: 36px;")
        self.layout.addWidget(self.unit_label)

        self.value_label = QLabel("0.00 dBm")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 53px; font-weight: bold;")
        self.layout.addWidget(self.value_label)

        # Label
        self.label = QLabel("Select Tower:", self)
        self.label.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.layout.addWidget(self.label)

        # ComboBox
        self.combo = QComboBox(self)
        self.combo.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.combo.addItems(["# 0 - GCS","# 1 - Section A", "# 2- Section B", "# 3- Section C", "# 4- Section D"])
        self.combo.setCurrentIndex(3)
        self.layout.addWidget(self.combo)
        self.combo.currentIndexChanged.connect(self.on_combobox_changed) # Connect event
        ##
        self.logOutput = QTextEdit()
        self.logOutput.setReadOnly(True)
        self.logOutput.setLineWrapMode(QTextEdit.NoWrap)
        self.font = QFont("Consolas", 22)
        self.font.setStyleHint(QFont.TypeWriter)
        self.logOutput.setCurrentFont(self.font)
        self.layout.addWidget(self.logOutput)

        self.checkbox = QCheckBox("Auto/ manual")
        self.checkbox.setChecked(True)
        self.checkbox.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.checkbox.stateChanged.connect(self.checkbox_changed)
        self.layout.addWidget(self.checkbox)

        ####
        self.setLayout(self.layout)

        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.update_rssi)
        #self.timer1.start(2000)  # Update every 500 milliseconds

        # wrapup the layout
        #self.groupBox.setLayout((gridLayout))
        self.startSRThread_GCS()
    def logInt(self, val):
        self.logOutput.insertPlainText(str(val) + "\n")
    def startSRThread_GCS(self):
        self.srthread_GCS = SRThread_GCS()
        self.srthread_GCS.eventlogInt.connect(self.logInt)
        self.srthread_GCS.eventlogStr.connect(self.logStr)
        self.srthread_GCS.start()
    def logStr(self, val):  # self.logOutput.moveCursor(QTextCursor.End)
        # self.logOutput.moveCursor(QTextCursor.End)
        # self.logOutput.insertPlainText(str(val) + "\n")
        self.logOutput.append(str(val))
        print(val + '\n')
    def on_combobox_changed(self, index):
        global tower,RMODE
        selected_text = self.combo.itemText(index)
        self.label.setText(f"Selected: {selected_text}")
        print(f"Combo box changed to index {index}: {selected_text}")
        tower = index
        print("...Changed to idn mode\n")
        RMODE = 99 # idn mode

    def checkbox_changed(self, state):
        global auto
        if state == Qt.Checked:
            auto = True
        else:
            auto = False
    def update_rssi(self):
        global serial_port
        """Generates a random voltage value and updates the display."""
        #voltage = random.uniform(0.0, 15.0)  # Generate random voltage between 0.0 and 15.0
        self.value_label.setText(f"{rssi:.0f} dBm")


# GCS  ///////////////////////////////////////////////////////////////////////////////////
class SRThread_GCS(QThread):
    eventlogInt = pyqtSignal(int)
    eventlogStr = pyqtSignal(str)
    global serial_connection, receive_thread, send_thread, rssi, station, RMODE

    def receive_data(self):
        global serial_connection, receive_thread, send_thread, rssi, station, RMODE
        """Continuously reads data from the serial port and prints it."""
        while True:
            try:
                if serial_connection.in_waiting > 0:
                    received_bytes = serial_connection.readline()  # Read until newline (\n)
                    # received_bytes = serial_port.read(serial_port.in_waiting)
                    try:
                        received_text = received_bytes.decode('utf-8').strip()
                        print(f"{received_text}")
                        if len(received_text) > 0 and (is_number(received_text)):  # rssi = float(received_text) if (received_text.isnumeric()) else rssi #a if a > b else b
                            if RMODE == 1:
                                rssi = float(received_text)
                                self.logRow(received_text)
                        elif len(received_text) > 0:        # and RMODE == 2:
                            self.logRow(f"Received <{received_text}>\n")
                            #print("...Changed to rssi mode\n")
                            #RMODE = 1


                    except UnicodeDecodeError:
                        print(f"Received non-UTF-8 data: {received_bytes}")
            except serial.SerialException as e:
                print(f"Error reading from serial port: {e}")
                break
            time.sleep(0.1)  # Small delay to avoid busy-waiting

    def send_data(self):
        global serial_connection, receive_thread, send_thread, rssi, station, RMODE,auto
        """Continuously prompts the user for input and sends it over the serial port."""
        while True:
            if auto == True:
                try:
                    serial_connection.reset_output_buffer()
                    serial_connection.reset_input_buffer()
                    serial_connection.flushInput()
                    serial_connection.flushOutput()
                    switch_mode(RMODE)
                    if (RMODE == 0):
                        text_to_send = CMDs[int(input()) - 1]
                    else:
                        text_to_send = switch_mode(RMODE) + "\r\n"

                    if text_to_send.lower() == 'quit':
                        break

                    serial_connection.write(text_to_send.encode('utf-8'))
                    serial_connection.flush()
                    print(f"Sent: {text_to_send}")
                    time.sleep(delay_current)
                except serial.SerialException as e:
                    print(f"Error writing to serial port: {e}")
                    break
            else:
                time.sleep(1)

        print("Sending thread stopped.")

    def logRow(self, txt):
        self.eventlogStr.emit(txt)#strTS()

    def run(self):
        print("GCS ... started\n")
        global serial_connection,receive_thread,send_thread
        #datasheet = ""
        try:
            serial_connection = serial.Serial(port, baudrate, timeout=3)
            time.sleep(0.3)
            print(f"Connected to {port} at {baudrate} bps")

            # Create and start the receiver thread
            receive_thread = threading.Thread(target=self.receive_data)
            receive_thread.daemon = True  # Allow main thread to exit even if this is running
            receive_thread.start()
            print("Receive thread active\n")

            # Create and start the sender thread
            send_thread = threading.Thread(target=self.send_data, args=serial_connection)
            send_thread.start()
            print("Sending thread active\n")
            send_thread.join()  # Wait for the sending thread to finish (when user enters 'quit')

        except serial.SerialException as e:
            print(f"Error opening serial port {port}: {e}")
        finally:
            if serial_connection and serial_connection.is_open:
                # serial_connection.close();print(f"Closed serial port {port}")
                print(f"Keep serial port {port} open")

        print(f"Threads running")
        time.sleep(4)
        #**********************************************************
        self.logRow("test ... Ended\n")





# Wrap up ////////////////////////////////////////////////////////
if __name__ == '__main__':
    #global serial_connection, receive_thread, send_thread, serial_port, rssi, station
    app = QApplication(sys.argv)

    ###
    voltmeter = VoltmeterDisplay()
    voltmeter.show()
    ###

    print(f"... ...timer1 starting...")
    voltmeter.timer1.start(1200)
    unit_label = QLabel("idn here!!!!!")
    ###


    sys.exit(app.exec_())

    send_thread.join()  # Wait for the sending thread to finish (when user enters 'quit')