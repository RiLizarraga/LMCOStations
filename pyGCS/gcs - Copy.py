import sys
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel)
from PyQt5.QtCore import Qt, QTimer

from PyQt5.QtWidgets import QPushButton, QDialog, QGroupBox, QHBoxLayout, QVBoxLayout, QGridLayout, \
    QScrollArea, QTextEdit, QMessageBox, QLabel, QSizePolicy

import serial
import threading
import time
MODE_TERMINAL = False
port = 'COM17'
baudrate = 115200
CMDs = ["idn?,0,0","idn?,0,222",
        "idn?,3,0","idn?,3,222",
        "rssi?,0,0","rssi?,0,222",
        "rssi?,3,0","rssi?,3,222","no command"]
TEST_SETUP_MSB_5GSA = "Steps: \n\n" \
                  + "1.-???????:\n" \
                  + "   ????: ANT#4\n"\
                  + "   ????: ANT#1\n" \
                  + "???????,\n\n"
# Globals
serial_connection = None
receive_thread = None
send_thread = None
serial_port = None
rssi = 0
station = "-"

def receive_data(serial_port):
    global serial_connection,receive_thread,send_thread,rssi,station
    """Continuously reads data from the serial port and prints it."""
    while True:
        try:
            if serial_port.in_waiting > 0:
                received_bytes = serial_port.readline()  # Read until newline (\n)
                #received_bytes = serial_port.read(serial_port.in_waiting)
                try:
                    received_text = received_bytes.decode('utf-8').strip()
                    print(f"{received_text}")
                    if len(received_text)>0:
                        rssi = float(received_text)
                    else:
                        rssi = 0
                except UnicodeDecodeError:
                    print(f"Received non-UTF-8 data: {received_bytes}")
        except serial.SerialException as e:
            print(f"Error reading from serial port: {e}")
            break
        time.sleep(0.1)  # Small delay to avoid busy-waiting

def send_data(serial_port):
    global serial_connection, receive_thread, send_thread, rssi, station
    """Continuously prompts the user for input and sends it over the serial port."""
    while True:
        try:
            serial_port.reset_output_buffer()
            serial_port.reset_input_buffer()
            serial_port.flushInput()
            serial_port.flushOutput()
            if (MODE_TERMINAL):
                text_to_send=CMDs[int(input())-1]
            else:
                text_to_send = CMDs[8 - 1]
                time.sleep(1.2)

            text_to_send = text_to_send + "\r\n"
            if len(text_to_send) == 1:
                text_to_send = "rssi?,3,222" + "\r\n"

            if text_to_send.lower() == 'quit':
                break

            serial_port.write(text_to_send.encode('utf-8'))
            serial_port.flush()
            print(f"Sent: {text_to_send}")
        except serial.SerialException as e:
            print(f"Error writing to serial port: {e}")
            break
    print("Sending thread stopped.")


class VoltmeterDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ground Control Station")
        self.setGeometry(100, 100, 300, 200)

        self.layout = QVBoxLayout()

        self.voltage_label = QLabel("RSSI Tower 3")
        self.voltage_label.setAlignment(Qt.AlignCenter)
        self.voltage_label.setStyleSheet("font-size: 24px;")
        self.layout.addWidget(self.voltage_label)

        self.value_label = QLabel("0.00 dBm")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.layout.addWidget(self.value_label)

        self.unit_label = QLabel("??????????????????")
        self.unit_label.setAlignment(Qt.AlignCenter)
        self.unit_label.setStyleSheet("font-size: 36px;")
        self.layout.addWidget(self.unit_label)

        self.setLayout(self.layout)

        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.update_rssi)
        #self.timer1.start(2000)  # Update every 500 milliseconds

    def update_rssi(self):
        global serial_port
        """Generates a random voltage value and updates the display."""
        #voltage = random.uniform(0.0, 15.0)  # Generate random voltage between 0.0 and 15.0
        self.value_label.setText(f"{rssi:.2f} dBm")

if __name__ == '__main__':
    #global serial_connection, receive_thread, send_thread, serial_port, rssi, station
    app = QApplication(sys.argv)



    ###
    voltmeter = VoltmeterDisplay()
    voltmeter.show()
    ###
    try:
        serial_connection = serial.Serial(port, baudrate, timeout=3)
        time.sleep(0.3)
        print(f"Connected to {port} at {baudrate} bps")

        # Create and start the receiver thread
        receive_thread = threading.Thread(target=receive_data, args=(serial_connection,))
        receive_thread.daemon = True  # Allow main thread to exit even if this is running
        receive_thread.start()

        # Create and start the sender thread
        send_thread = threading.Thread(target=send_data, args=(serial_connection,))
        send_thread.start()
        #send_thread.join()  # Wait for the sending thread to finish (when user enters 'quit')

    except serial.SerialException as e:
        print(f"Error opening serial port {port}: {e}")
    finally:
        if serial_connection and serial_connection.is_open:
            #serial_connection.close();print(f"Closed serial port {port}")
            print(f"Keep serial port {port} open")

    print(f"Threads running")
    time.sleep(4)
    print(f"... ...timer1 starting...")
    voltmeter.timer1.start(1200)
    ###
    sys.exit(app.exec_())

    send_thread.join()  # Wait for the sending thread to finish (when user enters 'quit')