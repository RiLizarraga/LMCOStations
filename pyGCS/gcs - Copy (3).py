import sys
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,QCheckBox)
from PyQt5.QtCore import Qt, QTimer,pyqtSignal,QObject,QThread,QDate,QTime
from PyQt5.QtWidgets import QPushButton, QDialog, QGroupBox,QComboBox, QHBoxLayout, QVBoxLayout, QGridLayout, \
    QScrollArea, QTextEdit, QMessageBox, QLabel, QSizePolicy
from PyQt5.QtGui import QTextCursor, QFont,QColor, QPalette
import serial
import threading
import time
import os
auto = True
#RMODE = 99   #0=Terminal, 1=rssi,  3=rec, 99=idn,
port = 'COM17'#12/17
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
tower = 4
cmd ="idn?"
dly_cmd = 200
dly_comm = 2000

rssi = 0
station = "-"
idn = "-"
sync_flg = True
#delay_current   = 0.6 #0.35    #0.6 ,1,1.2
#delay_rssi      = 0.4 #0.155       #0.15,0.4,1.2      failed with 0.05
#delay_idn       = 1.0 #0.35            #0.6,1.1,2
filename = "GCS_data.csv" ####saving data to a file
def save_string_line(filename, line, append=True):
    # 1. Input Validation
    if not isinstance(filename, str):
        raise TypeError(f"filename must be a string, not {type(filename).__name__}")
    if not isinstance(line, str):
        raise TypeError(f"line must be a string, not {type(line).__name__}")
    if not isinstance(append, bool):
        raise TypeError(f"append must be a bool, not {type(append).__name__}")

    mode = "a" if append else "w"  # Determine the file open mode
    try:
        with open(filename, mode) as file:
            # 3. Write Line
            file.write(line + "\n")  # Add newline character
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")
        return

    print(f"Line saved to {filename} (append={append}): {line}")

def build_cmd():
    global cmd,tower,dly_cmd
    return cmd+","+ str(tower)+ ","+str(dly_cmd)
def build_cmd_line(msg):
    global tower,dly_cmd
    return msg+","+ str(tower)+ ","+str(dly_cmd)
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
        self.left = 200
        self.top = 100
        self.width = 2800
        self.height = 2000
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

        # ComboBox1
        self.combo1 = QComboBox(self)
        self.combo1.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.combo1.addItems(["Ground Control Station","Tower # 1", "Tower # 2", "Tower # 3", "Tower # 4"])
        self.combo1.setCurrentIndex(tower)
        self.layout.addWidget(self.combo1)
        self.combo1.currentIndexChanged.connect(self.on_combobox1_changed) # Connect event
        # ComboBox2
        self.combo2 = QComboBox(self)
        self.combo2.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.combo2.addItems(["idn?","rssi?", "dl?", "ul?", "rec?","adc?","rly?","dout?"])
        self.combo2.setCurrentIndex(0)
        self.layout.addWidget(self.combo2)
        self.combo2.currentIndexChanged.connect(self.on_combobox2_changed) # Connect event
        # ComboBox3
        self.combo3 = QComboBox(self)
        self.combo3.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.combo3.addItems(["0","50", "80", "150", "200", "250", "300", "400"])
        self.combo3.setCurrentIndex(4)
        self.layout.addWidget(self.combo3)
        self.combo3.currentIndexChanged.connect(self.on_combobox3_changed) # Connect event
        # ComboBox4
        self.combo4 = QComboBox(self)
        self.combo4.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.combo4.addItems(["0", "50", "250", "500", "650", "750", "1000", "2000", "10000"])
        self.combo4.setCurrentIndex(7)
        self.layout.addWidget(self.combo4)
        self.combo4.currentIndexChanged.connect(self.on_combobox4_changed)  # Connect event

        ##
        self.logOutput = QTextEdit()
        self.logOutput.setReadOnly(True)
        self.logOutput.setLineWrapMode(QTextEdit.NoWrap)
        self.font = QFont("Consolas", 18)
        self.font.setStyleHint(QFont.TypeWriter)
        self.logOutput.setCurrentFont(self.font)
        self.logOutput.setStyleSheet("background-color: black;")
        self.logOutput.setTextColor(QColor(255, 0, 0))  # Use QColor for RGB
        self.layout.addWidget(self.logOutput)
        ##
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
    def on_combobox1_changed(self, index):
        global tower
        selected_text = self.combo1.itemText(index)
        self.label.setText(f"Selected: {selected_text}")
        print(f"Combo box changed to index {index}: {selected_text}")
        tower = index
    def on_combobox2_changed(self, index):
        global cmd
        selected_text = self.combo2.itemText(index)
        self.label.setText(f"Selected: {selected_text}")
        print(f"Combo box changed to index {index}: {selected_text}")
        cmd = selected_text
    def on_combobox3_changed(self, index):
        global dly_cmd
        selected_text = self.combo3.itemText(index)
        self.label.setText(f"Selected: {selected_text}")
        print(f"Combo box changed to index {index}: {selected_text}")
        dly_cmd = int(selected_text)
    def on_combobox4_changed(self, index):
        global dly_comm
        selected_text = self.combo4.itemText(index)
        self.label.setText(f"Selected: {selected_text}")
        print(f"Combo box changed to index {index}: {selected_text}")
        dly_comm = int(selected_text)

    def checkbox_changed(self, state):
        global auto,sync_flg
        print("sync_flg = " + str(sync_flg))
        sync_flg = True
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
        global serial_connection, receive_thread, send_thread, rssi, station, RMODE,filename,sync_flg
        """Continuously reads data from the serial port and prints it."""
        while True:
            try:
                if serial_connection.in_waiting > 0:
                    received_bytes = serial_connection.readline()  # Read until newline (\n)
                    print("setting sync_flg!")
                    sync_flg = True
                    # received_bytes = serial_port.read(serial_port.in_waiting)
                    try:
                        received_text = received_bytes.decode('utf-8').strip()
                        print(f"{received_text}")
                        if len(received_text) > 0 and (is_number(received_text)):  # rssi = float(received_text) if (received_text.isnumeric()) else rssi #a if a > b else b
                            rssi = float(received_text)
                            self.logRow(received_text)
                        elif len(received_text) > 0:        # and RMODE == 2:
                            self.logRow(received_text)
                            try:
                                open(filename, 'a').close()
                            except Exception as e:
                                print(f"Error creating file: {e}")
                            num_fields = len(received_text.split(','))
                            if num_fields == 7:
                                save_string_line(filename, received_text, append=True)

                                # send "ACK"
                                #serial_connection.reset_output_buffer()
                                #serial_connection.reset_input_buffer()
                                #serial_connection.flushInput()
                                #serial_connection.flushOutput()
                                text_to_send = build_cmd_line("ack") + "\r\n"
                                serial_connection.write(text_to_send.encode('utf-8'))
                                serial_connection.flush()
                                print(f"Sent: {text_to_send}")


                    except UnicodeDecodeError:
                        print(f"Received non-UTF-8 data: {received_bytes}")
            except serial.SerialException as e:
                print(f"Error reading from serial port: {e}")
                break
            time.sleep(0.1)  # Small delay to avoid busy-waiting

    def send_data(self):
        global serial_connection, receive_thread, send_thread, rssi, station, RMODE,auto,sync_flg
        """Continuously prompts the user for input and sends it over the serial port."""
        while True:
            if auto:
                try:
                    if sync_flg:
                        serial_connection.reset_output_buffer()
                        serial_connection.reset_input_buffer()
                        serial_connection.flushInput()
                        serial_connection.flushOutput()
                        text_to_send = build_cmd() + "\r\n"
                        serial_connection.write(text_to_send.encode('utf-8'))
                        if text_to_send[:3]=="ack":
                            sync_flg = True
                        else:
                            sync_flg = False
                        serial_connection.flush()
                        print(f"Sent: {text_to_send}")
                        time.sleep(dly_comm/1000)
                        print("Clearing flag when cmd: "+ text_to_send)
                except serial.SerialException as e:
                    print(f"Error writing to serial port: {e}")
                    break
            else:
                time.sleep(1)

        print("Sending thread stopped.")

    def logRow(self, txt):
        self.eventlogStr.emit(txt)#strTS()

    def run(self):
        #global filename
        print("GCS ... started\n")

        print("\n--- File Contents ---")
        try:
            with open(filename, "r") as file:
                print(file.read())
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
        except Exception as e:
            print(f"An error occurred reading the file: {e}")
        ####

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